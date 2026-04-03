"""
Core scraper engine — the main AIScraper class.

Orchestrates the browser engine and LLM extraction pipeline:
1. Fetch URL with headless Chrome (anti-bot bypass)
2. Clean the HTML (strip scripts, styles, nav, footer)
3. Send cleaned text to LLM with a schema
4. Return structured JSON results

Usage:
    from ai_scraper import AIScraper, Schema

    scraper = AIScraper(provider="openrouter", api_key="sk-...")
    results = scraper.scrape("https://example.com/listings", Schema.APARTMENTS)
"""

import json
import csv
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from bs4 import BeautifulSoup

from ai_scraper.browser import BrowserEngine
from ai_scraper.llm import LLMClient

logger = logging.getLogger(__name__)


class AIScraper:
    """
    AI-powered universal web scraper.

    Point at any URL → get structured data back.
    No custom CSS selectors, no brittle XPath — just AI.
    """

    def __init__(
        self,
        provider: str = "openrouter",
        api_key: str = "",
        model: Optional[str] = None,
        headless: bool = True,
        timeout: int = 30,
        wait_seconds: float = 2.0,
    ):
        """
        Initialize the AI scraper.

        Args:
            provider: LLM provider ('openrouter', 'openai', 'kilo', 'ollama').
            api_key: API key for the LLM provider.
            model: Specific model to use (or provider default).
            headless: Run Chrome in headless mode.
            timeout: Page load timeout in seconds.
            wait_seconds: How long to wait after page load for JS rendering.
        """
        self.wait_seconds = wait_seconds
        self._browser = BrowserEngine(headless=headless, timeout=timeout)
        self._llm = LLMClient(
            provider=provider,
            api_key=api_key,
            model=model,
        )
        logger.info(
            "AIScraper initialized (provider=%s, model=%s, headless=%s)",
            provider,
            self._llm.model,
            headless,
        )

    def scrape(
        self,
        url: str,
        schema: Union[Dict[str, Any], str],
        instructions: str = "",
        raw_html: Optional[str] = None,
    ) -> List[Dict]:
        """
        Scrape a URL and extract structured data.

        Args:
            url: The URL to scrape.
            schema: Extraction schema (dict or predefined name like 'apartments').
            instructions: Extra instructions for the LLM.
            raw_html: Optional pre-fetched HTML (skips browser fetch).

        Returns:
            List of dicts containing the extracted data.
        """
        # Resolve schema name to dict
        if isinstance(schema, str):
            from ai_scraper.schemas import Schema
            schema = Schema.get(schema)

        # Fetch page
        if raw_html:
            html = raw_html
            logger.info("Using provided HTML (%d chars)", len(html))
        else:
            html = self._browser.fetch(url, wait_seconds=self.wait_seconds)
            logger.info("Fetched %s (%d chars)", url, len(html))

        # Clean HTML → readable text
        cleaned = self._clean_html(html)
        logger.info("Cleaned content: %d chars", len(cleaned))

        if len(cleaned) < 50:
            logger.warning("Very little content extracted from %s", url)
            return []

        # Extract with LLM
        results = self._llm.extract(
            text=cleaned,
            schema=schema,
            instructions=instructions,
        )

        # Post-process: resolve relative URLs
        for item in results:
            for key in ("url", "image_url", "link"):
                if key in item and item[key] and not item[key].startswith("http"):
                    from urllib.parse import urljoin
                    item[key] = urljoin(url, item[key])

        return results

    def scrape_multiple(
        self,
        urls: List[str],
        schema: Union[Dict[str, Any], str],
        instructions: str = "",
    ) -> List[Dict]:
        """
        Scrape multiple URLs and combine results.

        Args:
            urls: List of URLs to scrape.
            schema: Extraction schema.
            instructions: Extra instructions for the LLM.

        Returns:
            Combined list of extracted data from all URLs.
        """
        all_results = []
        for i, url in enumerate(urls, 1):
            logger.info("Scraping URL %d/%d: %s", i, len(urls), url)
            try:
                results = self.scrape(url, schema, instructions)
                for item in results:
                    item["_source_url"] = url
                all_results.extend(results)
                logger.info("  → Got %d items", len(results))
            except Exception as e:
                logger.error("  → Failed: %s", e)
        return all_results

    def ask_page(self, url: str, question: str) -> str:
        """
        Fetch a page and ask the LLM a question about its content.

        Args:
            url: The page to fetch.
            question: Your question about the page content.

        Returns:
            LLM's text answer.
        """
        html = self._browser.fetch(url, wait_seconds=self.wait_seconds)
        cleaned = self._clean_html(html)
        full_question = (
            f"Based on the following web page content, answer this question:\n\n"
            f"Question: {question}\n\n"
            f"Page content:\n{cleaned[:30000]}"
        )
        return self._llm.ask(full_question)

    @staticmethod
    def _clean_html(html: str) -> str:
        """
        Strip scripts, styles, nav, footer, ads from HTML.
        Return readable text optimized for LLM consumption.
        """
        soup = BeautifulSoup(html, "lxml")

        # Remove non-content elements
        for tag_name in ["script", "style", "noscript", "svg", "iframe",
                         "nav", "footer", "header", "aside"]:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Remove hidden elements
        for tag in soup.find_all(attrs={"style": re.compile(r"display\s*:\s*none")}):
            tag.decompose()

        # Remove cookie banners, modals, popups
        for class_pattern in [r"cookie", r"consent", r"modal", r"popup",
                              r"overlay", r"banner", r"gdpr"]:
            for tag in soup.find_all(class_=re.compile(class_pattern, re.I)):
                tag.decompose()

        # Get text with reasonable spacing
        text = soup.get_text(separator="\n", strip=True)

        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def save_json(self, results: List[Dict], path: str):
        """Save results to a JSON file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info("Saved %d results to %s", len(results), path)

    def save_csv(self, results: List[Dict], path: str):
        """Save results to a CSV file."""
        if not results:
            logger.warning("No results to save")
            return

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(results[0].keys())
        # Ensure all fields from all rows are captured
        for row in results:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)

        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)
        logger.info("Saved %d results to %s", len(results), path)

    def close(self):
        """Close browser and clean up resources."""
        self._browser.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

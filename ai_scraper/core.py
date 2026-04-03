"""
Core scraper engine — the main AIScraper class.

Orchestrates the browser engine, LLM extraction, and self-learning pipeline:
1. Check memory for learned domain strategies
2. Fetch URL with headless Chrome (anti-bot bypass)
3. Apply learned cleaning rules + standard HTML stripping
4. Send cleaned text to LLM with evolved prompts
5. Score extraction quality automatically
6. If quality is poor → self-improve and retry
7. Store results and learnings in persistent memory
8. Return structured JSON results

Usage:
    from ai_scraper import AIScraper, Schema

    scraper = AIScraper(provider="openrouter", api_key="sk-...")
    results = scraper.scrape("https://example.com/listings", Schema.APARTMENTS)
"""

import json
import csv
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ai_scraper.browser import BrowserEngine
from ai_scraper.llm import LLMClient
from ai_scraper.memory import Memory
from ai_scraper.learner import Learner

logger = logging.getLogger(__name__)


class AIScraper:
    """
    AI-powered universal web scraper with self-learning capabilities.

    Point at any URL → get structured data back.
    Gets smarter with every scrape — learns what works,
    adapts to failures, evolves extraction prompts automatically.
    """

    def __init__(
        self,
        provider: str = "openrouter",
        api_key: str = "",
        model: Optional[str] = None,
        headless: bool = True,
        timeout: int = 30,
        wait_seconds: float = 2.0,
        learning: bool = True,
        memory_path: Optional[str] = None,
    ):
        """
        Initialize the AI scraper.

        Args:
            provider: LLM provider ('openrouter', 'openai', 'kilo', 'ollama').
            api_key: API key for the LLM provider.
            model: Specific model to use (or provider default).
            headless: Run Chrome in headless mode.
            timeout: Page load timeout in seconds.
            wait_seconds: Default wait after page load for JS rendering.
            learning: Enable self-learning (True by default).
            memory_path: Custom path for the learning database.
        """
        self.default_wait = wait_seconds
        self.learning_enabled = learning
        self._browser = BrowserEngine(headless=headless, timeout=timeout)
        self._llm = LLMClient(
            provider=provider,
            api_key=api_key,
            model=model,
        )

        # Initialize learning system
        if learning:
            mem_kwargs = {"db_path": memory_path} if memory_path else {}
            self._memory = Memory(**mem_kwargs)
            self._learner = Learner(memory=self._memory, llm_client=self._llm)
        else:
            self._memory = None
            self._learner = None

        logger.info(
            "AIScraper initialized (provider=%s, model=%s, learning=%s)",
            provider, self._llm.model, learning,
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
        Uses learned strategies and self-improves on poor results.

        Args:
            url: The URL to scrape.
            schema: Extraction schema (dict or predefined name like 'apartments').
            instructions: Extra instructions for the LLM.
            raw_html: Optional pre-fetched HTML (skips browser fetch).

        Returns:
            List of dicts containing the extracted data.
        """
        start_time = time.time()

        # Resolve schema name to dict
        schema_name = schema if isinstance(schema, str) else None
        if isinstance(schema, str):
            from ai_scraper.schemas import Schema
            schema = Schema.get(schema)

        domain = urlparse(url).netloc

        # ─── Phase 1: Get learned settings ───────────────────────
        wait = self.default_wait
        extra_instructions = instructions
        if self._learner:
            settings = self._learner.get_optimized_settings(url, schema)
            if settings["learned"]:
                wait = settings["wait_seconds"]
            if settings["extra_instructions"]:
                # Combine user instructions with learned ones
                extra_instructions = (
                    f"{instructions}\n\n"
                    f"[Learned from previous scrapes of this site]:\n"
                    f"{settings['extra_instructions']}"
                ).strip()

        # ─── Phase 2: Fetch page ─────────────────────────────────
        if raw_html:
            html = raw_html
            logger.info("Using provided HTML (%d chars)", len(html))
        else:
            html = self._browser.fetch(url, wait_seconds=wait)
            logger.info("Fetched %s (%d chars, wait=%.1fs)", url, len(html), wait)

        # ─── Phase 3: Clean HTML ─────────────────────────────────
        cleaned = self._clean_html(html, domain)
        logger.info("Cleaned content: %d chars", len(cleaned))

        if len(cleaned) < 50:
            logger.warning("Very little content extracted from %s", url)
            if self._learner:
                self._learner.learn_from_results(
                    url, schema, [], time.time() - start_time, self._llm.model
                )
                self._learner.learn_optimal_wait(domain, 0.0, wait)
            return []

        # ─── Phase 4: Extract with LLM ───────────────────────────
        results = self._llm.extract(
            text=cleaned,
            schema=schema,
            instructions=extra_instructions,
        )

        # Post-process: resolve relative URLs
        for item in results:
            for key in ("url", "image_url", "link"):
                if key in item and item[key] and not str(item[key]).startswith("http"):
                    from urllib.parse import urljoin
                    item[key] = urljoin(url, item[key])

        # ─── Phase 5: Learn & Self-Improve ───────────────────────
        if self._learner:
            duration = time.time() - start_time
            quality, diagnostics = self._learner.learn_from_results(
                url, schema, results, duration, self._llm.model
            )

            # Learn optimal wait time
            self._learner.learn_optimal_wait(domain, quality, wait)

            # Self-improvement: if quality is poor, try to do better
            if self._learner.should_retry(quality, attempt=0):
                logger.info("🔄 Quality below threshold — attempting self-improvement...")

                improved = self._self_improve(
                    url=url,
                    schema=schema,
                    results=results,
                    diagnostics=diagnostics,
                    cleaned_text=cleaned,
                    html=html,
                    domain=domain,
                    original_instructions=instructions,
                )

                if improved is not None:
                    # Re-score the improved results
                    new_quality, new_diag = self._learner.learn_from_results(
                        url, schema, improved,
                        time.time() - start_time, self._llm.model,
                    )
                    if new_quality > quality:
                        logger.info(
                            "✅ Self-improvement succeeded: %.0f%% → %.0f%%",
                            quality * 100, new_quality * 100,
                        )
                        return improved
                    else:
                        logger.info(
                            "⚠️ Self-improvement didn't help (%.0f%% → %.0f%%), keeping original",
                            quality * 100, new_quality * 100,
                        )

        return results

    def _self_improve(
        self,
        url: str,
        schema: Dict,
        results: List[Dict],
        diagnostics: Dict,
        cleaned_text: str,
        html: str,
        domain: str,
        original_instructions: str,
    ) -> Optional[List[Dict]]:
        """
        Attempt to improve extraction quality through adaptive strategies.
        """
        strategy = self._learner.generate_improvement_strategy(
            url=url,
            schema=schema,
            results=results,
            diagnostics=diagnostics,
            cleaned_text_sample=cleaned_text[:5000],
        )

        if not strategy.get("retry"):
            return None

        # Apply wait time adjustment
        if strategy["wait_seconds_adjust"] > 0:
            new_wait = self.default_wait + strategy["wait_seconds_adjust"]
            logger.info("⏱️ Retrying with longer wait: %.1fs", new_wait)
            html = self._browser.fetch(url, wait_seconds=new_wait)
            cleaned_text = self._clean_html(html, domain)

        # Retry extraction with improved instructions
        improved_instructions = (
            f"{original_instructions}\n\n"
            f"[Self-improvement instructions]:\n"
            f"{strategy['extra_instructions']}"
        ).strip()

        new_results = self._llm.extract(
            text=cleaned_text,
            schema=schema,
            instructions=improved_instructions,
        )

        # Resolve URLs
        for item in new_results:
            for key in ("url", "image_url", "link"):
                if key in item and item[key] and not str(item[key]).startswith("http"):
                    from urllib.parse import urljoin
                    item[key] = urljoin(url, item[key])

        return new_results if new_results else None

    def scrape_multiple(
        self,
        urls: List[str],
        schema: Union[Dict[str, Any], str],
        instructions: str = "",
    ) -> List[Dict]:
        """Scrape multiple URLs and combine results."""
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
        """Fetch a page and ask the LLM a question about its content."""
        html = self._browser.fetch(url, wait_seconds=self.default_wait)
        domain = urlparse(url).netloc
        cleaned = self._clean_html(html, domain)
        full_question = (
            f"Based on the following web page content, answer this question:\n\n"
            f"Question: {question}\n\n"
            f"Page content:\n{cleaned[:30000]}"
        )
        return self._llm.ask(full_question)

    def feedback(
        self, url: str, schema: Union[Dict, str], feedback_type: str, details: str = ""
    ):
        """
        Provide feedback on scraping results to help the learner improve.

        Args:
            url: The URL that was scraped.
            schema: The schema used.
            feedback_type: 'good', 'bad', or 'correction'.
            details: Additional details about what was wrong.
        """
        if not self._memory:
            logger.warning("Learning is disabled — feedback not recorded.")
            return

        schema_name = schema if isinstance(schema, str) else self._learner._schema_name(schema)
        self._memory.record_feedback(url, schema_name, feedback_type, details)
        logger.info("📝 Feedback recorded: %s for %s", feedback_type, url)

    def stats(self) -> Dict:
        """Get learning statistics."""
        if not self._memory:
            return {"learning": "disabled"}
        return self._memory.get_stats()

    def diagnose(self, domain: str) -> Dict:
        """Get a diagnostic report for a domain."""
        if not self._learner:
            return {"error": "Learning is disabled"}
        return self._learner.diagnose_domain(domain)

    def _clean_html(self, html: str, domain: str = "") -> str:
        """
        Strip scripts, styles, nav, footer, ads from HTML.
        Applies learned domain-specific cleaning rules.
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

        # Apply learned cleaning rules for this domain
        if domain and self._memory:
            rules = self._memory.get_cleaning_rules(domain)
            for rule in rules:
                try:
                    if rule["rule_type"] == "class":
                        for tag in soup.find_all(class_=re.compile(rule["selector"], re.I)):
                            tag.decompose()
                    elif rule["rule_type"] == "id":
                        tag = soup.find(id=rule["selector"])
                        if tag:
                            tag.decompose()
                    elif rule["rule_type"] == "tag":
                        for tag in soup.find_all(rule["selector"]):
                            tag.decompose()
                except Exception:
                    pass  # Silently skip bad rules

        # Get text with reasonable spacing
        text = soup.get_text(separator="\n", strip=True)
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
        if self._memory:
            self._memory.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

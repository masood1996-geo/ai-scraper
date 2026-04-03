"""
Browser engine — headless Chrome with anti-bot bypass.

Uses undetected_chromedriver to render JavaScript-heavy pages,
bypass WAF protections, and return clean HTML for LLM processing.
"""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class BrowserEngine:
    """Manages headless Chrome sessions for web scraping."""

    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout
        self._driver = None

    def _init_driver(self):
        """Initialize undetected Chrome with stealth settings."""
        import undetected_chromedriver as uc

        options = uc.ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )

        self._driver = uc.Chrome(options=options)
        self._driver.set_page_load_timeout(self.timeout)
        logger.info("Chrome WebDriver initialized (headless=%s)", self.headless)

    @property
    def driver(self):
        if self._driver is None:
            self._init_driver()
        return self._driver

    def fetch(self, url: str, wait_seconds: float = 2.0) -> str:
        """
        Navigate to URL, wait for JS to render, return page source.

        Args:
            url: Target URL to fetch.
            wait_seconds: Seconds to wait after page load for JS rendering.

        Returns:
            Full page HTML source after rendering.
        """
        logger.info("Fetching: %s", url)
        try:
            self.driver.get(url)
            time.sleep(wait_seconds)  # Let JS render

            # Check for common bot challenges
            source = self.driver.page_source
            if "awswaf-captcha" in source:
                logger.warning("AWS WAF captcha detected on %s", url)
            elif "challenge-platform" in source:
                logger.warning("Cloudflare challenge detected on %s", url)
                time.sleep(5)  # Extra wait for challenge resolution
                source = self.driver.page_source

            return source

        except Exception as e:
            logger.error("Failed to fetch %s: %s", url, e)
            raise

    def screenshot(self, path: str):
        """Save a screenshot of the current page."""
        if self._driver:
            self._driver.save_screenshot(path)
            logger.info("Screenshot saved to %s", path)

    def close(self):
        """Gracefully close the browser."""
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None
            logger.info("Browser closed")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

"""
AI Scraper — Universal AI-powered web data extraction engine.

Point at any website. Get structured data back. No custom parsers needed.
"""

__version__ = "1.0.0"
__author__ = "masood1996-geo"

from ai_scraper.core import AIScraper
from ai_scraper.schemas import Schema

__all__ = ["AIScraper", "Schema"]

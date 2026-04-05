"""
AI Scraper — Universal AI-powered web data extraction engine.

Point at any website. Get structured data back. No custom parsers needed.
Self-learning system that gets smarter with every scrape.
"""

__version__ = "1.1.0"
__author__ = "masood1996-geo"

from ai_scraper.core import AIScraper
from ai_scraper.schemas import Schema
from ai_scraper.memory import Memory
from ai_scraper.learner import Learner
from ai_scraper.recovery import RecoveryEngine, FailureScenario
from ai_scraper.command_safety import CommandSafety, PermissionMode

__all__ = [
    "AIScraper", "Schema", "Memory", "Learner",
    "RecoveryEngine", "FailureScenario",
    "CommandSafety", "PermissionMode",
]

"""
Self-Learning Engine — the neural core of AI Scraper.

This module makes the scraper get smarter with every run:

1. QUALITY SCORING — Automatically evaluates extraction results
   (field fill rate, data validity, consistency checks)

2. ADAPTIVE STRATEGIES — When quality is low, automatically:
   - Increases wait time for JS-heavy sites
   - Tries alternative HTML cleaning approaches
   - Generates refined LLM prompts based on what failed
   - Retries with domain-specific knowledge

3. PROMPT EVOLUTION — Uses the LLM itself to generate better
   extraction prompts based on past failures and successes

4. PATTERN LEARNING — Recognizes site structures it's seen before
   and pre-applies the best extraction strategy

5. SELF-DIAGNOSIS — Detects recurring failure patterns and
   reports actionable insights about what's going wrong
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from ai_scraper.memory import Memory

logger = logging.getLogger(__name__)


# Quality thresholds
QUALITY_EXCELLENT = 0.85
QUALITY_GOOD = 0.60
QUALITY_POOR = 0.35
QUALITY_FAILURE = 0.10

# Max retry attempts for self-improvement
MAX_IMPROVEMENT_ATTEMPTS = 2


class Learner:
    """
    Self-learning engine that improves scraping quality over time.

    Tracks what works, what fails, and evolves strategies automatically.
    """

    def __init__(self, memory: Memory, llm_client=None):
        self.memory = memory
        self._llm = llm_client  # Set later by AIScraper
        self._current_attempt = 0

    def set_llm(self, llm_client):
        """Inject the LLM client (called by AIScraper after init)."""
        self._llm = llm_client

    # ─── Quality Scoring ──────────────────────────────────────────

    def score_results(
        self,
        results: List[Dict],
        schema: Dict[str, Any],
        url: str = "",
    ) -> Tuple[float, Dict]:
        """
        Score extraction quality from 0.0 to 1.0.

        Checks:
        - Field fill rate (how many schema fields have values)
        - Data validity (non-empty, reasonable length)
        - Result count (at least some items found)
        - Uniqueness (no duplicate items)
        - Content quality (not just garbage/placeholder text)

        Returns:
            Tuple of (score, diagnostics_dict)
        """
        diagnostics = {
            "results_count": len(results),
            "fill_rate": 0.0,
            "validity_rate": 0.0,
            "uniqueness_rate": 0.0,
            "content_quality": 0.0,
            "issues": [],
        }

        if not results:
            diagnostics["issues"].append("NO_RESULTS")
            return 0.0, diagnostics

        schema_fields = list(schema.keys())
        total_fields = len(schema_fields) * len(results)

        # 1. Field fill rate — what percentage of fields have values?
        filled = 0
        for item in results:
            for field in schema_fields:
                val = item.get(field, "")
                if val and str(val).strip() and str(val).strip() != "N/A":
                    filled += 1
        fill_rate = filled / total_fields if total_fields > 0 else 0.0
        diagnostics["fill_rate"] = round(fill_rate, 3)

        # 2. Data validity — are values reasonable?
        valid_count = 0
        total_checks = 0
        for item in results:
            for field in schema_fields:
                val = str(item.get(field, "")).strip()
                total_checks += 1
                if val and len(val) > 1 and val not in ("N/A", "null", "undefined", "None", "-"):
                    # Check it's not just the field name repeated
                    if val.lower() != field.lower():
                        valid_count += 1
        validity_rate = valid_count / total_checks if total_checks > 0 else 0.0
        diagnostics["validity_rate"] = round(validity_rate, 3)

        # 3. Uniqueness — how many items are unique?
        seen_titles = set()
        unique_count = 0
        title_field = next(
            (f for f in schema_fields if f in ("title", "name", "headline")), None
        )
        if title_field:
            for item in results:
                title = str(item.get(title_field, "")).strip().lower()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    unique_count += 1
            uniqueness = unique_count / len(results) if results else 0.0
        else:
            uniqueness = 1.0  # Can't check without a title field
        diagnostics["uniqueness_rate"] = round(uniqueness, 3)

        # 4. Content quality — detect garbage/placeholder content
        garbage_patterns = [
            "lorem ipsum", "placeholder", "test data", "example.com",
            "click here", "read more", "loading...",
        ]
        garbage_count = 0
        for item in results:
            text = json.dumps(item).lower()
            if any(g in text for g in garbage_patterns):
                garbage_count += 1
        content_quality = 1.0 - (garbage_count / len(results)) if results else 0.0
        diagnostics["content_quality"] = round(content_quality, 3)

        # Weighted final score
        score = (
            fill_rate * 0.35 +
            validity_rate * 0.30 +
            uniqueness * 0.15 +
            content_quality * 0.10 +
            min(len(results) / 5.0, 1.0) * 0.10  # Bonus for finding multiple items
        )
        score = round(min(score, 1.0), 3)

        # Add issue flags
        if fill_rate < 0.3:
            diagnostics["issues"].append("LOW_FILL_RATE")
        if validity_rate < 0.3:
            diagnostics["issues"].append("LOW_VALIDITY")
        if uniqueness < 0.5:
            diagnostics["issues"].append("MANY_DUPLICATES")
        if content_quality < 0.5:
            diagnostics["issues"].append("GARBAGE_CONTENT")
        if len(results) == 1:
            diagnostics["issues"].append("ONLY_ONE_RESULT")

        return score, diagnostics

    # ─── Pre-Scrape Intelligence ──────────────────────────────────

    def get_optimized_settings(self, url: str, schema: Dict) -> Dict:
        """
        Get optimized scrape settings based on past learning.

        Returns a dict with:
        - wait_seconds: optimal page load wait
        - extra_instructions: learned prompt additions
        - cleaning_hints: domain-specific HTML cleaning rules
        """
        domain = urlparse(url).netloc
        schema_name = self._schema_name(schema)

        settings = {
            "wait_seconds": 2.0,
            "extra_instructions": "",
            "cleaning_rules": [],
            "learned": False,
        }

        # Check if we have a domain profile
        profile = self.memory.get_domain_profile(domain)
        if profile:
            settings["wait_seconds"] = profile["wait_seconds"]
            settings["learned"] = True
            logger.info(
                "🧠 Using learned settings for %s "
                "(quality: %.0f%%, scrapes: %d, wait: %.1fs)",
                domain,
                profile["avg_quality"] * 100,
                profile["total_scrapes"],
                profile["wait_seconds"],
            )

        # Check for refined prompts
        best_prompt = self.memory.get_best_prompt(domain, schema_name)
        if best_prompt:
            settings["extra_instructions"] = best_prompt
            self.memory.increment_prompt_usage(domain, schema_name)
            logger.info("🧠 Using evolved prompt for %s/%s", domain, schema_name)

        # Check for cleaning rules
        rules = self.memory.get_cleaning_rules(domain)
        if rules:
            settings["cleaning_rules"] = rules
            logger.info("🧠 Applying %d learned cleaning rules for %s", len(rules), domain)

        return settings

    # ─── Post-Scrape Learning ─────────────────────────────────────

    def learn_from_results(
        self,
        url: str,
        schema: Dict,
        results: List[Dict],
        duration: float,
        model_used: str = "",
    ) -> Tuple[float, Dict]:
        """
        Evaluate results and update the learning memory.

        Returns:
            Tuple of (quality_score, diagnostics)
        """
        domain = urlparse(url).netloc
        schema_name = self._schema_name(schema)

        # Score the results
        quality, diagnostics = self.score_results(results, schema, url)

        # Log to extraction history
        self.memory.log_extraction(
            url=url,
            schema_name=schema_name,
            results_count=len(results),
            quality_score=quality,
            fill_rate=diagnostics["fill_rate"],
            duration_secs=duration,
            model_used=model_used,
            error=", ".join(diagnostics["issues"]),
        )

        # Update domain profile
        self.memory.update_domain_profile(
            domain=domain,
            success=quality >= QUALITY_POOR,
            quality_score=quality,
        )

        # Log quality assessment
        quality_label = self._quality_label(quality)
        logger.info(
            "📊 Quality: %.0f%% (%s) | Items: %d | Fill: %.0f%% | "
            "Valid: %.0f%% | Issues: %s",
            quality * 100,
            quality_label,
            len(results),
            diagnostics["fill_rate"] * 100,
            diagnostics["validity_rate"] * 100,
            diagnostics["issues"] or "none",
        )

        return quality, diagnostics

    # ─── Self-Improvement ─────────────────────────────────────────

    def should_retry(self, quality: float, attempt: int) -> bool:
        """Decide whether to retry with improved strategy."""
        return quality < QUALITY_GOOD and attempt < MAX_IMPROVEMENT_ATTEMPTS

    def generate_improvement_strategy(
        self,
        url: str,
        schema: Dict,
        results: List[Dict],
        diagnostics: Dict,
        cleaned_text_sample: str = "",
    ) -> Dict:
        """
        Use the LLM to analyze why extraction was poor and generate
        an improved strategy.

        Returns:
            Dict with improved settings (extra_instructions, wait_seconds, etc.)
        """
        domain = urlparse(url).netloc
        schema_name = self._schema_name(schema)
        issues = diagnostics.get("issues", [])

        strategy = {
            "extra_instructions": "",
            "wait_seconds_adjust": 0,
            "retry": True,
        }

        # Rule-based improvements (fast, no LLM needed)
        if "NO_RESULTS" in issues:
            # Site might need more JS render time
            strategy["wait_seconds_adjust"] = 3.0
            strategy["extra_instructions"] = (
                "The page may use heavy JavaScript loading. "
                "Look very carefully for ANY content that resembles listings, items, or data entries. "
                "Check for dynamically loaded content regions."
            )
            logger.info("🔧 Strategy: Increasing wait time + broadening search")

        elif "LOW_FILL_RATE" in issues:
            # LLM is finding items but can't fill fields
            strategy["extra_instructions"] = (
                "Previous extraction had low field fill rate. "
                "Look more carefully for each field — they might use different labels: "
                "price could be 'rent', 'cost', 'Miete'; "
                "size could be 'area', 'sqm', 'Fläche', 'm²'; "
                "rooms could be 'Zimmer', 'Zi.', 'bedrooms'. "
                "If a field truly isn't present, use null instead of empty string."
            )
            logger.info("🔧 Strategy: Expanded field recognition hints")

        elif "GARBAGE_CONTENT" in issues:
            # Extracting nav items, footer content, etc.
            strategy["extra_instructions"] = (
                "Previous extraction picked up non-listing content like navigation items, "
                "news articles, or corporate pages. "
                "ONLY extract actual data listings/items — ignore menus, headers, footers, "
                "press releases, blog posts, and corporate information."
            )
            logger.info("🔧 Strategy: Stricter content discrimination")

        elif "MANY_DUPLICATES" in issues:
            strategy["extra_instructions"] = (
                "Previous extraction had many duplicate entries. "
                "Each item should be unique. Skip any repeated content."
            )
            logger.info("🔧 Strategy: De-duplication hints")

        # LLM-powered improvement (slower but smarter)
        if self._llm and cleaned_text_sample and diagnostics["fill_rate"] < 0.5:
            try:
                refined = self._generate_prompt_refinement(
                    domain, schema, results, diagnostics, cleaned_text_sample
                )
                if refined:
                    strategy["extra_instructions"] = refined
                    logger.info("🧠 LLM generated refined extraction prompt")
            except Exception as e:
                logger.warning("LLM prompt refinement failed: %s", e)

        return strategy

    def _generate_prompt_refinement(
        self,
        domain: str,
        schema: Dict,
        results: List[Dict],
        diagnostics: Dict,
        text_sample: str,
    ) -> Optional[str]:
        """
        Ask the LLM to analyze why extraction was poor and generate
        a better extraction prompt.
        """
        if not self._llm:
            return None

        # Prepare context for the meta-prompt
        sample_results = json.dumps(results[:3], indent=2) if results else "[]"
        schema_desc = json.dumps(schema, indent=2)

        meta_prompt = f"""You are analyzing a web scraping extraction that performed poorly.

SCHEMA (what we wanted to extract):
{schema_desc}

WHAT WE GOT (sample of {len(results)} total results):
{sample_results}

QUALITY DIAGNOSTICS:
- Fill rate: {diagnostics['fill_rate']:.0%} (how many fields had values)
- Validity: {diagnostics['validity_rate']:.0%} (how many values were meaningful)
- Issues: {diagnostics['issues']}

PAGE CONTENT SAMPLE (first 3000 chars):
{text_sample[:3000]}

Based on this analysis, generate IMPROVED extraction instructions.
The instructions should be specific to this website's content structure.
Tell the AI exactly where to find each field and what patterns to look for.

Output ONLY the improved instructions text, no other commentary."""

        response = self._llm.ask(meta_prompt)

        if response and len(response) > 20 and not response.startswith("Error"):
            # Save the refinement
            schema_name = self._schema_name(schema)
            self.memory.save_prompt_refinement(
                domain=domain,
                schema_name=schema_name,
                extra_instructions=response,
                quality_score=diagnostics["fill_rate"],
            )
            return response

        return None

    # ─── Adaptive Wait Time ───────────────────────────────────────

    def learn_optimal_wait(self, domain: str, quality: float, current_wait: float):
        """
        Learn the optimal wait time for a domain.

        If quality is low, increase wait time (site might need more JS rendering).
        If quality is high, gradually decrease (save time on fast sites).
        """
        profile = self.memory.get_domain_profile(domain)
        if not profile:
            return

        if quality < QUALITY_POOR and current_wait < 10.0:
            new_wait = min(current_wait + 2.0, 15.0)
            logger.info(
                "⏱️ Increasing wait for %s: %.1f → %.1fs (quality was low)",
                domain, current_wait, new_wait,
            )
            self.memory.update_domain_profile(
                domain, success=False, quality_score=quality, wait_seconds=new_wait,
            )
        elif quality >= QUALITY_EXCELLENT and current_wait > 1.5:
            new_wait = max(current_wait - 0.5, 1.0)
            self.memory.update_domain_profile(
                domain, success=True, quality_score=quality, wait_seconds=new_wait,
            )

    # ─── Self-Diagnosis ───────────────────────────────────────────

    def diagnose_domain(self, domain: str) -> Dict:
        """
        Generate a diagnostic report for a domain.

        Analyzes patterns in past scrape attempts to identify
        recurring issues and suggest fixes.
        """
        history = self.memory.get_domain_history(domain, limit=50)
        profile = self.memory.get_domain_profile(domain)

        report = {
            "domain": domain,
            "total_attempts": len(history),
            "success_rate": 0.0,
            "avg_quality": 0.0,
            "common_issues": [],
            "recommendations": [],
            "trend": "unknown",
        }

        if not history:
            report["recommendations"].append("No data yet — run at least one scrape.")
            return report

        # Calculate averages
        qualities = [h["quality_score"] for h in history]
        report["avg_quality"] = sum(qualities) / len(qualities)
        report["success_rate"] = self.memory.get_success_rate(domain)

        # Analyze issues
        issue_counts = {}
        for h in history:
            for issue in (h.get("error", "") or "").split(", "):
                if issue:
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1

        report["common_issues"] = sorted(
            issue_counts.items(), key=lambda x: x[1], reverse=True
        )

        # Trend analysis (last 5 vs previous 5)
        if len(qualities) >= 10:
            recent = sum(qualities[:5]) / 5
            older = sum(qualities[5:10]) / 5
            if recent > older + 0.1:
                report["trend"] = "improving ↑"
            elif recent < older - 0.1:
                report["trend"] = "declining ↓"
            else:
                report["trend"] = "stable →"

        # Recommendations
        if report["success_rate"] < 0.5:
            report["recommendations"].append(
                "High failure rate — this site may have anti-bot protection. "
                "Try running with --no-headless to debug visually."
            )
        if "LOW_FILL_RATE" in dict(report["common_issues"]):
            report["recommendations"].append(
                "Consistently low field fill rate — the LLM may need "
                "domain-specific field mapping hints."
            )
        if "NO_RESULTS" in dict(report["common_issues"]):
            report["recommendations"].append(
                "Site frequently returns no results — it may require "
                "authentication, or the content loads via API calls."
            )

        return report

    # ─── Utilities ────────────────────────────────────────────────

    @staticmethod
    def _schema_name(schema: Dict) -> str:
        """Generate a stable name for a schema based on its fields."""
        fields = sorted(schema.keys())
        return "_".join(fields[:4])

    @staticmethod
    def _quality_label(score: float) -> str:
        if score >= QUALITY_EXCELLENT:
            return "EXCELLENT ⭐"
        elif score >= QUALITY_GOOD:
            return "GOOD ✅"
        elif score >= QUALITY_POOR:
            return "POOR ⚠️"
        else:
            return "FAILURE ❌"

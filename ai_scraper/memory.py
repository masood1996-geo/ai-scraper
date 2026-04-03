"""
Persistent learning memory — SQLite-backed knowledge base.

Stores everything the scraper learns:
- Domain profiles (what worked, optimal settings per site)
- Extraction history (success/failure/quality scores)
- Evolved prompts (refined per domain+schema combination)
- User feedback (corrections, validations)

The memory persists across runs, so the scraper gets smarter over time.
"""

import json
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.path.join(
    os.path.expanduser("~"), ".ai_scraper", "memory.db"
)


class Memory:
    """
    Persistent learning memory for the AI Scraper.

    Tracks per-domain extraction strategies, quality scores,
    prompt refinements, and user feedback to improve over time.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info("Learning Memory initialized at %s", db_path)

    def _create_tables(self):
        """Create all memory tables if they don't exist."""
        self._conn.executescript("""
            -- Per-domain learned profiles
            CREATE TABLE IF NOT EXISTS domain_profiles (
                domain          TEXT PRIMARY KEY,
                wait_seconds    REAL DEFAULT 2.0,
                clean_strategy  TEXT DEFAULT 'standard',
                avg_quality     REAL DEFAULT 0.0,
                total_scrapes   INTEGER DEFAULT 0,
                total_successes INTEGER DEFAULT 0,
                total_failures  INTEGER DEFAULT 0,
                last_scraped    REAL DEFAULT 0,
                notes           TEXT DEFAULT '',
                created_at      REAL DEFAULT 0,
                updated_at      REAL DEFAULT 0
            );

            -- Every scrape attempt
            CREATE TABLE IF NOT EXISTS extraction_history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                url             TEXT NOT NULL,
                domain          TEXT NOT NULL,
                schema_name     TEXT NOT NULL,
                results_count   INTEGER DEFAULT 0,
                quality_score   REAL DEFAULT 0.0,
                fill_rate       REAL DEFAULT 0.0,
                duration_secs   REAL DEFAULT 0.0,
                prompt_version  INTEGER DEFAULT 0,
                model_used      TEXT DEFAULT '',
                error           TEXT DEFAULT '',
                timestamp       REAL DEFAULT 0
            );

            -- Evolved prompts — refined per domain+schema
            CREATE TABLE IF NOT EXISTS prompt_refinements (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                domain          TEXT NOT NULL,
                schema_name     TEXT NOT NULL,
                version         INTEGER DEFAULT 1,
                extra_instructions TEXT DEFAULT '',
                quality_score   REAL DEFAULT 0.0,
                times_used      INTEGER DEFAULT 0,
                created_at      REAL DEFAULT 0,
                UNIQUE(domain, schema_name, version)
            );

            -- Learned cleaning rules per domain
            CREATE TABLE IF NOT EXISTS cleaning_rules (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                domain          TEXT NOT NULL,
                rule_type       TEXT NOT NULL,
                selector        TEXT NOT NULL,
                action          TEXT DEFAULT 'remove',
                confidence      REAL DEFAULT 1.0,
                times_applied   INTEGER DEFAULT 0,
                created_at      REAL DEFAULT 0
            );

            -- User feedback on results
            CREATE TABLE IF NOT EXISTS feedback (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                url             TEXT NOT NULL,
                domain          TEXT NOT NULL,
                schema_name     TEXT NOT NULL,
                feedback_type   TEXT NOT NULL,
                details         TEXT DEFAULT '',
                timestamp       REAL DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_history_domain
                ON extraction_history(domain);
            CREATE INDEX IF NOT EXISTS idx_history_url
                ON extraction_history(url);
            CREATE INDEX IF NOT EXISTS idx_prompts_domain_schema
                ON prompt_refinements(domain, schema_name);
        """)
        self._conn.commit()

    # ─── Domain Profile Operations ────────────────────────────────

    def get_domain_profile(self, domain: str) -> Optional[Dict]:
        """Get learned profile for a domain."""
        row = self._conn.execute(
            "SELECT * FROM domain_profiles WHERE domain = ?", (domain,)
        ).fetchone()
        return dict(row) if row else None

    def update_domain_profile(
        self,
        domain: str,
        success: bool,
        quality_score: float,
        wait_seconds: Optional[float] = None,
    ):
        """Update a domain's profile after a scrape attempt."""
        now = time.time()
        existing = self.get_domain_profile(domain)

        if existing:
            new_total = existing["total_scrapes"] + 1
            new_successes = existing["total_successes"] + (1 if success else 0)
            new_failures = existing["total_failures"] + (0 if success else 1)
            # Exponential moving average for quality
            alpha = 0.3
            new_avg = alpha * quality_score + (1 - alpha) * existing["avg_quality"]

            update_fields = {
                "total_scrapes": new_total,
                "total_successes": new_successes,
                "total_failures": new_failures,
                "avg_quality": round(new_avg, 3),
                "last_scraped": now,
                "updated_at": now,
            }
            if wait_seconds is not None:
                update_fields["wait_seconds"] = wait_seconds

            set_clause = ", ".join(f"{k} = ?" for k in update_fields)
            self._conn.execute(
                f"UPDATE domain_profiles SET {set_clause} WHERE domain = ?",
                (*update_fields.values(), domain),
            )
        else:
            self._conn.execute(
                """INSERT INTO domain_profiles
                   (domain, wait_seconds, avg_quality, total_scrapes,
                    total_successes, total_failures, last_scraped,
                    created_at, updated_at)
                   VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?)""",
                (
                    domain,
                    wait_seconds or 2.0,
                    quality_score,
                    1 if success else 0,
                    0 if success else 1,
                    now, now, now,
                ),
            )
        self._conn.commit()

    def get_learned_wait_seconds(self, domain: str) -> float:
        """Get the optimal wait time learned for a domain."""
        profile = self.get_domain_profile(domain)
        return profile["wait_seconds"] if profile else 2.0

    # ─── Extraction History ───────────────────────────────────────

    def log_extraction(
        self,
        url: str,
        schema_name: str,
        results_count: int,
        quality_score: float,
        fill_rate: float,
        duration_secs: float,
        model_used: str = "",
        prompt_version: int = 0,
        error: str = "",
    ):
        """Record a scrape attempt in history."""
        domain = urlparse(url).netloc
        self._conn.execute(
            """INSERT INTO extraction_history
               (url, domain, schema_name, results_count, quality_score,
                fill_rate, duration_secs, model_used, prompt_version,
                error, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                url, domain, schema_name, results_count,
                quality_score, fill_rate, duration_secs,
                model_used, prompt_version, error, time.time(),
            ),
        )
        self._conn.commit()

    def get_domain_history(
        self, domain: str, limit: int = 20
    ) -> List[Dict]:
        """Get recent extraction history for a domain."""
        rows = self._conn.execute(
            """SELECT * FROM extraction_history
               WHERE domain = ? ORDER BY timestamp DESC LIMIT ?""",
            (domain, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_success_rate(self, domain: str) -> float:
        """Get the success rate for a domain (0.0 to 1.0)."""
        profile = self.get_domain_profile(domain)
        if not profile or profile["total_scrapes"] == 0:
            return 0.0
        return profile["total_successes"] / profile["total_scrapes"]

    # ─── Prompt Refinement ────────────────────────────────────────

    def get_best_prompt(self, domain: str, schema_name: str) -> Optional[str]:
        """Get the highest-quality refined prompt for a domain+schema."""
        row = self._conn.execute(
            """SELECT extra_instructions FROM prompt_refinements
               WHERE domain = ? AND schema_name = ?
               ORDER BY quality_score DESC, version DESC LIMIT 1""",
            (domain, schema_name),
        ).fetchone()
        return row["extra_instructions"] if row else None

    def save_prompt_refinement(
        self,
        domain: str,
        schema_name: str,
        extra_instructions: str,
        quality_score: float,
    ):
        """Save a refined prompt version."""
        # Get next version number
        row = self._conn.execute(
            """SELECT MAX(version) as max_v FROM prompt_refinements
               WHERE domain = ? AND schema_name = ?""",
            (domain, schema_name),
        ).fetchone()
        next_version = (row["max_v"] or 0) + 1

        self._conn.execute(
            """INSERT INTO prompt_refinements
               (domain, schema_name, version, extra_instructions,
                quality_score, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (domain, schema_name, next_version, extra_instructions,
             quality_score, time.time()),
        )
        self._conn.commit()
        logger.info(
            "Saved prompt refinement v%d for %s/%s (quality: %.2f)",
            next_version, domain, schema_name, quality_score,
        )

    def increment_prompt_usage(self, domain: str, schema_name: str):
        """Track that a refined prompt was used."""
        self._conn.execute(
            """UPDATE prompt_refinements SET times_used = times_used + 1
               WHERE domain = ? AND schema_name = ?
               AND version = (
                   SELECT MAX(version) FROM prompt_refinements
                   WHERE domain = ? AND schema_name = ?
               )""",
            (domain, schema_name, domain, schema_name),
        )
        self._conn.commit()

    # ─── Cleaning Rules ───────────────────────────────────────────

    def save_cleaning_rule(
        self, domain: str, rule_type: str, selector: str, action: str = "remove"
    ):
        """Save a learned HTML cleaning rule for a domain."""
        self._conn.execute(
            """INSERT OR IGNORE INTO cleaning_rules
               (domain, rule_type, selector, action, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (domain, rule_type, selector, action, time.time()),
        )
        self._conn.commit()

    def get_cleaning_rules(self, domain: str) -> List[Dict]:
        """Get all learned cleaning rules for a domain."""
        rows = self._conn.execute(
            "SELECT * FROM cleaning_rules WHERE domain = ?", (domain,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ─── User Feedback ────────────────────────────────────────────

    def record_feedback(
        self,
        url: str,
        schema_name: str,
        feedback_type: str,
        details: str = "",
    ):
        """Record user feedback (good/bad/correction)."""
        domain = urlparse(url).netloc
        self._conn.execute(
            """INSERT INTO feedback
               (url, domain, schema_name, feedback_type, details, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (url, domain, schema_name, feedback_type, details, time.time()),
        )
        self._conn.commit()

    # ─── Analytics ────────────────────────────────────────────────

    def get_stats(self) -> Dict:
        """Get overall learning statistics."""
        stats = {}
        stats["total_scrapes"] = self._conn.execute(
            "SELECT COUNT(*) FROM extraction_history"
        ).fetchone()[0]
        stats["unique_domains"] = self._conn.execute(
            "SELECT COUNT(DISTINCT domain) FROM extraction_history"
        ).fetchone()[0]
        stats["avg_quality"] = self._conn.execute(
            "SELECT AVG(quality_score) FROM extraction_history"
        ).fetchone()[0] or 0.0
        stats["total_refinements"] = self._conn.execute(
            "SELECT COUNT(*) FROM prompt_refinements"
        ).fetchone()[0]
        stats["total_feedback"] = self._conn.execute(
            "SELECT COUNT(*) FROM feedback"
        ).fetchone()[0]

        # Top domains by scrape count
        top = self._conn.execute(
            """SELECT domain, total_scrapes, avg_quality, total_successes, total_failures
               FROM domain_profiles ORDER BY total_scrapes DESC LIMIT 10"""
        ).fetchall()
        stats["top_domains"] = [dict(r) for r in top]

        return stats

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

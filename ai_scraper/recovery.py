"""
Recovery engine — codified self-healing for scraping failures.

Adapted from the recovery_recipes pattern in claw-code-parity.
Instead of crashing on known failure scenarios, we define recovery
steps with automatic retry and escalation policies.

Architecture:
    FailureScenario → RecoveryRecipe (steps + max_attempts + escalation)
    RecoveryContext  → tracks attempts per scenario, emits structured events
    attempt_recovery → executes recipe steps, returns typed RecoveryResult

Usage:
    from ai_scraper.recovery import RecoveryEngine, FailureScenario

    engine = RecoveryEngine()
    result = engine.attempt(FailureScenario.NETWORK_TIMEOUT, context={"url": "..."})
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ─── Failure Scenarios ────────────────────────────────────────────────

class FailureScenario(Enum):
    """Known failure scenarios with coded recovery recipes."""

    NETWORK_TIMEOUT = "network_timeout"
    RATE_LIMITED = "rate_limited"
    CAPTCHA_BLOCKED = "captcha_blocked"
    LLM_EXTRACTION_FAILED = "llm_extraction_failed"
    LLM_PROVIDER_ERROR = "llm_provider_error"
    STALE_SELECTOR = "stale_selector"
    EMPTY_PAGE = "empty_page"
    BROWSER_CRASH = "browser_crash"
    CLOUDFLARE_CHALLENGE = "cloudflare_challenge"
    JSON_PARSE_ERROR = "json_parse_error"


# ─── Escalation Policies ─────────────────────────────────────────────

class EscalationPolicy(Enum):
    """What happens when automatic recovery is exhausted."""

    ALERT_HUMAN = "alert_human"
    LOG_AND_CONTINUE = "log_and_continue"
    ABORT = "abort"


# ─── Recovery Steps ──────────────────────────────────────────────────

class RecoveryStepType(Enum):
    """Individual step types that can be part of a recovery recipe."""

    RETRY_WITH_BACKOFF = "retry_with_backoff"
    WAIT_COOLDOWN = "wait_cooldown"
    RETRY_REQUEST = "retry_request"
    RESTART_BROWSER = "restart_browser"
    INCREASE_WAIT = "increase_wait"
    REDUCE_CONTENT = "reduce_content"
    RETRY_WITH_FALLBACK_MODEL = "retry_with_fallback_model"
    CLEAR_COOKIES = "clear_cookies"
    ROTATE_USER_AGENT = "rotate_user_agent"
    WAIT_FOR_CHALLENGE = "wait_for_challenge"
    SKIP_AND_LOG = "skip_and_log"


@dataclass
class RecoveryStep:
    """A single step in a recovery recipe."""

    step_type: RecoveryStepType
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def __repr__(self) -> str:
        return f"RecoveryStep({self.step_type.value}, {self.params})"


# ─── Recovery Recipe ─────────────────────────────────────────────────

@dataclass
class RecoveryRecipe:
    """
    Encodes the recovery strategy for a specific failure scenario.

    Attributes:
        scenario: The failure scenario this recipe handles.
        steps: Ordered list of recovery steps to execute.
        max_attempts: Maximum automatic recovery attempts before escalation.
        escalation_policy: What to do when max_attempts is exceeded.
    """

    scenario: FailureScenario
    steps: List[RecoveryStep]
    max_attempts: int
    escalation_policy: EscalationPolicy


# ─── Recovery Results ─────────────────────────────────────────────────

class RecoveryResultType(Enum):
    """Outcome classification for a recovery attempt."""

    RECOVERED = "recovered"
    PARTIAL_RECOVERY = "partial_recovery"
    ESCALATION_REQUIRED = "escalation_required"


@dataclass
class RecoveryResult:
    """Typed outcome of a recovery attempt."""

    result_type: RecoveryResultType
    steps_taken: int = 0
    recovered_steps: List[RecoveryStep] = field(default_factory=list)
    remaining_steps: List[RecoveryStep] = field(default_factory=list)
    reason: str = ""

    @property
    def success(self) -> bool:
        return self.result_type == RecoveryResultType.RECOVERED


# ─── Recovery Events ─────────────────────────────────────────────────

class RecoveryEventType(Enum):
    """Structured event types emitted during recovery."""

    RECOVERY_ATTEMPTED = "recovery.attempted"
    RECOVERY_SUCCEEDED = "recovery.succeeded"
    RECOVERY_FAILED = "recovery.failed"
    RECOVERY_ESCALATED = "recovery.escalated"
    STEP_EXECUTED = "recovery.step.executed"
    STEP_FAILED = "recovery.step.failed"


@dataclass
class RecoveryEvent:
    """Structured event emitted during recovery operations."""

    event_type: RecoveryEventType
    scenario: Optional[FailureScenario] = None
    step: Optional[RecoveryStep] = None
    result: Optional[RecoveryResult] = None
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a structured dict for logging/telemetry."""
        return {
            "event": self.event_type.value,
            "scenario": self.scenario.value if self.scenario else None,
            "step": self.step.step_type.value if self.step else None,
            "detail": self.detail,
            "timestamp": self.timestamp,
            "success": self.result.success if self.result else None,
        }


# ─── Recipe Registry ─────────────────────────────────────────────────

def _build_recipes() -> Dict[FailureScenario, RecoveryRecipe]:
    """Build the default recipe registry for all known failure scenarios."""
    return {
        FailureScenario.NETWORK_TIMEOUT: RecoveryRecipe(
            scenario=FailureScenario.NETWORK_TIMEOUT,
            steps=[
                RecoveryStep(
                    RecoveryStepType.RETRY_WITH_BACKOFF,
                    params={"max_wait": 30, "base_delay": 2},
                    description="Retry with exponential backoff up to 30s",
                ),
            ],
            max_attempts=3,
            escalation_policy=EscalationPolicy.LOG_AND_CONTINUE,
        ),
        FailureScenario.RATE_LIMITED: RecoveryRecipe(
            scenario=FailureScenario.RATE_LIMITED,
            steps=[
                RecoveryStep(
                    RecoveryStepType.WAIT_COOLDOWN,
                    params={"duration": 60},
                    description="Wait 60s for rate limit to reset",
                ),
                RecoveryStep(
                    RecoveryStepType.RETRY_REQUEST,
                    description="Retry the original request",
                ),
            ],
            max_attempts=2,
            escalation_policy=EscalationPolicy.ALERT_HUMAN,
        ),
        FailureScenario.CAPTCHA_BLOCKED: RecoveryRecipe(
            scenario=FailureScenario.CAPTCHA_BLOCKED,
            steps=[
                RecoveryStep(
                    RecoveryStepType.WAIT_FOR_CHALLENGE,
                    params={"timeout": 10},
                    description="Wait for CAPTCHA/challenge to auto-resolve",
                ),
                RecoveryStep(
                    RecoveryStepType.RETRY_REQUEST,
                    description="Retry after challenge wait",
                ),
            ],
            max_attempts=2,
            escalation_policy=EscalationPolicy.ALERT_HUMAN,
        ),
        FailureScenario.LLM_EXTRACTION_FAILED: RecoveryRecipe(
            scenario=FailureScenario.LLM_EXTRACTION_FAILED,
            steps=[
                RecoveryStep(
                    RecoveryStepType.REDUCE_CONTENT,
                    params={"max_chars": 25000},
                    description="Reduce input content size for cleaner extraction",
                ),
                RecoveryStep(
                    RecoveryStepType.RETRY_REQUEST,
                    description="Retry extraction with reduced content",
                ),
            ],
            max_attempts=2,
            escalation_policy=EscalationPolicy.LOG_AND_CONTINUE,
        ),
        FailureScenario.LLM_PROVIDER_ERROR: RecoveryRecipe(
            scenario=FailureScenario.LLM_PROVIDER_ERROR,
            steps=[
                RecoveryStep(
                    RecoveryStepType.RETRY_WITH_BACKOFF,
                    params={"max_wait": 15, "base_delay": 3},
                    description="Retry with backoff — provider may be temporarily down",
                ),
            ],
            max_attempts=3,
            escalation_policy=EscalationPolicy.ABORT,
        ),
        FailureScenario.STALE_SELECTOR: RecoveryRecipe(
            scenario=FailureScenario.STALE_SELECTOR,
            steps=[
                RecoveryStep(
                    RecoveryStepType.INCREASE_WAIT,
                    params={"additional_seconds": 3},
                    description="Wait longer for dynamic content to load",
                ),
                RecoveryStep(
                    RecoveryStepType.RETRY_REQUEST,
                    description="Retry with extended wait time",
                ),
            ],
            max_attempts=2,
            escalation_policy=EscalationPolicy.LOG_AND_CONTINUE,
        ),
        FailureScenario.EMPTY_PAGE: RecoveryRecipe(
            scenario=FailureScenario.EMPTY_PAGE,
            steps=[
                RecoveryStep(
                    RecoveryStepType.INCREASE_WAIT,
                    params={"additional_seconds": 5},
                    description="Wait longer for JS-heavy pages to render",
                ),
                RecoveryStep(
                    RecoveryStepType.RESTART_BROWSER,
                    description="Restart browser with fresh session",
                ),
                RecoveryStep(
                    RecoveryStepType.RETRY_REQUEST,
                    description="Retry from scratch",
                ),
            ],
            max_attempts=2,
            escalation_policy=EscalationPolicy.ALERT_HUMAN,
        ),
        FailureScenario.BROWSER_CRASH: RecoveryRecipe(
            scenario=FailureScenario.BROWSER_CRASH,
            steps=[
                RecoveryStep(
                    RecoveryStepType.RESTART_BROWSER,
                    description="Restart crashed browser instance",
                ),
                RecoveryStep(
                    RecoveryStepType.RETRY_REQUEST,
                    description="Retry the scrape",
                ),
            ],
            max_attempts=2,
            escalation_policy=EscalationPolicy.ABORT,
        ),
        FailureScenario.CLOUDFLARE_CHALLENGE: RecoveryRecipe(
            scenario=FailureScenario.CLOUDFLARE_CHALLENGE,
            steps=[
                RecoveryStep(
                    RecoveryStepType.WAIT_FOR_CHALLENGE,
                    params={"timeout": 8},
                    description="Wait for Cloudflare challenge resolution",
                ),
                RecoveryStep(
                    RecoveryStepType.ROTATE_USER_AGENT,
                    description="Switch to a different browser user-agent",
                ),
                RecoveryStep(
                    RecoveryStepType.RETRY_REQUEST,
                    description="Retry with new identity",
                ),
            ],
            max_attempts=2,
            escalation_policy=EscalationPolicy.ALERT_HUMAN,
        ),
        FailureScenario.JSON_PARSE_ERROR: RecoveryRecipe(
            scenario=FailureScenario.JSON_PARSE_ERROR,
            steps=[
                RecoveryStep(
                    RecoveryStepType.RETRY_REQUEST,
                    description="Retry LLM extraction — model may produce valid JSON",
                ),
            ],
            max_attempts=2,
            escalation_policy=EscalationPolicy.LOG_AND_CONTINUE,
        ),
    }


DEFAULT_RECIPES = _build_recipes()


# ─── Recovery Context ────────────────────────────────────────────────

class RecoveryContext:
    """
    Tracks recovery state across attempts and emits structured events.

    Holds per-scenario attempt counts and a structured event log,
    mirroring the RecoveryContext pattern from claw-code-parity.
    """

    def __init__(self):
        self._attempts: Dict[FailureScenario, int] = {}
        self._events: List[RecoveryEvent] = []

    @property
    def events(self) -> List[RecoveryEvent]:
        """The structured event log."""
        return list(self._events)

    def attempt_count(self, scenario: FailureScenario) -> int:
        """Returns the number of recovery attempts made for a scenario."""
        return self._attempts.get(scenario, 0)

    def reset(self, scenario: Optional[FailureScenario] = None):
        """Reset attempt counters. If scenario is None, reset all."""
        if scenario:
            self._attempts.pop(scenario, None)
        else:
            self._attempts.clear()

    def _emit(self, event: RecoveryEvent):
        """Record a structured recovery event."""
        self._events.append(event)
        log_msg = f"[{event.event_type.value}] {event.detail}"
        if event.scenario:
            log_msg = f"[{event.scenario.value}] {log_msg}"
        logger.info(log_msg)

    def _increment(self, scenario: FailureScenario) -> int:
        """Increment and return the attempt count for a scenario."""
        count = self._attempts.get(scenario, 0) + 1
        self._attempts[scenario] = count
        return count


# ─── Recovery Engine ─────────────────────────────────────────────────

class RecoveryEngine:
    """
    Main recovery engine — classifies failures and executes recovery recipes.

    This is the primary integration point for the ai-scraper:

        engine = RecoveryEngine()
        result = engine.attempt(FailureScenario.NETWORK_TIMEOUT)

    Custom step handlers can be registered to execute actual side effects:

        engine.register_handler(
            RecoveryStepType.RESTART_BROWSER,
            lambda step, ctx: browser.restart()
        )
    """

    def __init__(
        self,
        recipes: Optional[Dict[FailureScenario, RecoveryRecipe]] = None,
    ):
        self._recipes = recipes or DEFAULT_RECIPES
        self._context = RecoveryContext()
        self._handlers: Dict[RecoveryStepType, Callable] = {}

    @property
    def context(self) -> RecoveryContext:
        """Access the recovery context for inspection."""
        return self._context

    def register_handler(
        self,
        step_type: RecoveryStepType,
        handler: Callable[[RecoveryStep, Dict[str, Any]], bool],
    ):
        """
        Register a handler function for a recovery step type.

        The handler receives (step, context_dict) and should return True
        if the step succeeded, False otherwise.

        Args:
            step_type: The step type to handle.
            handler: Callable that executes the step. Returns bool.
        """
        self._handlers[step_type] = handler

    def recipe_for(self, scenario: FailureScenario) -> RecoveryRecipe:
        """Get the recovery recipe for a given failure scenario."""
        if scenario not in self._recipes:
            raise ValueError(f"No recovery recipe for scenario: {scenario.value}")
        return self._recipes[scenario]

    def classify_error(self, error: Exception, context: Dict[str, Any] = None) -> FailureScenario:
        """
        Classify an exception into a FailureScenario.

        This provides automatic failure detection — pass any exception
        and get back the appropriate recovery scenario.
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Network / timeout errors
        if any(kw in error_str for kw in ["timeout", "timed out", "connection"]):
            return FailureScenario.NETWORK_TIMEOUT

        # Rate limiting
        if any(kw in error_str for kw in ["429", "rate limit", "too many requests"]):
            return FailureScenario.RATE_LIMITED

        # CAPTCHA / bot detection
        if any(kw in error_str for kw in ["captcha", "waf", "bot detected"]):
            return FailureScenario.CAPTCHA_BLOCKED

        # Cloudflare
        if any(kw in error_str for kw in ["cloudflare", "challenge-platform", "cf-"]):
            return FailureScenario.CLOUDFLARE_CHALLENGE

        # LLM/API errors
        if any(kw in error_str for kw in ["api", "openai", "provider", "500", "503"]):
            return FailureScenario.LLM_PROVIDER_ERROR

        # JSON parsing
        if "json" in error_type.lower() or "json" in error_str:
            return FailureScenario.JSON_PARSE_ERROR

        # Browser crashes
        if any(kw in error_str for kw in ["webdriver", "session", "chrome", "browser"]):
            return FailureScenario.BROWSER_CRASH

        # Default to network timeout as safest fallback
        return FailureScenario.NETWORK_TIMEOUT

    def attempt(
        self,
        scenario: FailureScenario,
        context: Optional[Dict[str, Any]] = None,
    ) -> RecoveryResult:
        """
        Attempt automatic recovery for a given failure scenario.

        Looks up the recipe, enforces max-attempts-before-escalation policy,
        executes step handlers, and emits structured events.

        Args:
            scenario: The classified failure scenario.
            context: Optional dict with contextual info (url, error, etc.).

        Returns:
            RecoveryResult with the outcome.
        """
        context = context or {}
        recipe = self.recipe_for(scenario)
        current_attempts = self._context.attempt_count(scenario)

        # ── Enforce max attempts before escalation ──
        if current_attempts >= recipe.max_attempts:
            result = RecoveryResult(
                result_type=RecoveryResultType.ESCALATION_REQUIRED,
                reason=(
                    f"Max recovery attempts ({recipe.max_attempts}) exceeded "
                    f"for {scenario.value}"
                ),
            )
            self._context._emit(RecoveryEvent(
                event_type=RecoveryEventType.RECOVERY_ATTEMPTED,
                scenario=scenario,
                result=result,
                detail=result.reason,
            ))
            self._context._emit(RecoveryEvent(
                event_type=RecoveryEventType.RECOVERY_ESCALATED,
                scenario=scenario,
                detail=f"Escalation policy: {recipe.escalation_policy.value}",
            ))
            return result

        # ── Increment attempt counter ──
        attempt_num = self._context._increment(scenario)

        # ── Execute recovery steps ──
        executed: List[RecoveryStep] = []
        failed = False

        for step in recipe.steps:
            handler = self._handlers.get(step.step_type)
            step_success = True

            if handler:
                try:
                    step_success = handler(step, context)
                except Exception as e:
                    logger.warning(
                        "Recovery step %s failed: %s",
                        step.step_type.value, e,
                    )
                    step_success = False
            else:
                # No handler registered — execute built-in defaults
                step_success = self._execute_default(step, context)

            if step_success:
                executed.append(step)
                self._context._emit(RecoveryEvent(
                    event_type=RecoveryEventType.STEP_EXECUTED,
                    scenario=scenario,
                    step=step,
                    detail=step.description or step.step_type.value,
                ))
            else:
                self._context._emit(RecoveryEvent(
                    event_type=RecoveryEventType.STEP_FAILED,
                    scenario=scenario,
                    step=step,
                    detail=f"Step failed: {step.step_type.value}",
                ))
                failed = True
                break

        # ── Build result ──
        if failed:
            remaining = recipe.steps[len(executed):]
            if not executed:
                result = RecoveryResult(
                    result_type=RecoveryResultType.ESCALATION_REQUIRED,
                    reason=f"Recovery failed at first step for {scenario.value}",
                )
            else:
                result = RecoveryResult(
                    result_type=RecoveryResultType.PARTIAL_RECOVERY,
                    steps_taken=len(executed),
                    recovered_steps=executed,
                    remaining_steps=remaining,
                )
        else:
            result = RecoveryResult(
                result_type=RecoveryResultType.RECOVERED,
                steps_taken=len(executed),
                recovered_steps=executed,
            )

        # ── Emit result events ──
        self._context._emit(RecoveryEvent(
            event_type=RecoveryEventType.RECOVERY_ATTEMPTED,
            scenario=scenario,
            result=result,
            detail=f"Attempt {attempt_num}/{recipe.max_attempts}: {result.result_type.value}",
        ))

        if result.success:
            self._context._emit(RecoveryEvent(
                event_type=RecoveryEventType.RECOVERY_SUCCEEDED,
                scenario=scenario,
                detail=f"Recovered in {result.steps_taken} steps",
            ))
        elif result.result_type == RecoveryResultType.PARTIAL_RECOVERY:
            self._context._emit(RecoveryEvent(
                event_type=RecoveryEventType.RECOVERY_FAILED,
                scenario=scenario,
                detail=f"Partial: {len(result.recovered_steps)} of {len(recipe.steps)} steps",
            ))
        else:
            self._context._emit(RecoveryEvent(
                event_type=RecoveryEventType.RECOVERY_ESCALATED,
                scenario=scenario,
                detail=f"Escalation policy: {recipe.escalation_policy.value}",
            ))

        return result

    def attempt_from_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> RecoveryResult:
        """
        Convenience method — classify an error and attempt recovery.

        Args:
            error: The exception that occurred.
            context: Optional dict with contextual info.

        Returns:
            RecoveryResult with the outcome.
        """
        scenario = self.classify_error(error, context)
        logger.info(
            "🔍 Classified error '%s' as %s",
            type(error).__name__, scenario.value,
        )
        return self.attempt(scenario, context)

    def should_retry(self, scenario: FailureScenario) -> bool:
        """Check if a retry is possible for the given scenario."""
        recipe = self._recipes.get(scenario)
        if not recipe:
            return False
        return self._context.attempt_count(scenario) < recipe.max_attempts

    def _execute_default(self, step: RecoveryStep, context: Dict[str, Any]) -> bool:
        """Execute built-in default behavior for a step type."""
        if step.step_type == RecoveryStepType.RETRY_WITH_BACKOFF:
            base_delay = step.params.get("base_delay", 2)
            max_wait = step.params.get("max_wait", 30)
            # Calculate delay based on attempt count
            attempt = max(1, sum(self._context._attempts.values()))
            delay = min(base_delay * (2 ** (attempt - 1)), max_wait)
            logger.info("⏳ Backing off for %.1fs...", delay)
            time.sleep(delay)
            return True

        elif step.step_type == RecoveryStepType.WAIT_COOLDOWN:
            duration = step.params.get("duration", 30)
            logger.info("⏳ Cooling down for %ds...", duration)
            time.sleep(duration)
            return True

        elif step.step_type == RecoveryStepType.WAIT_FOR_CHALLENGE:
            timeout = step.params.get("timeout", 10)
            logger.info("⏳ Waiting %ds for challenge resolution...", timeout)
            time.sleep(timeout)
            return True

        elif step.step_type == RecoveryStepType.INCREASE_WAIT:
            additional = step.params.get("additional_seconds", 3)
            context["wait_increase"] = additional
            logger.info("⏱️ Will increase wait by %ds on next fetch", additional)
            return True

        elif step.step_type == RecoveryStepType.REDUCE_CONTENT:
            max_chars = step.params.get("max_chars", 25000)
            context["max_chars"] = max_chars
            logger.info("📄 Content limit set to %d chars", max_chars)
            return True

        elif step.step_type in (
            RecoveryStepType.RETRY_REQUEST,
            RecoveryStepType.SKIP_AND_LOG,
        ):
            # These are signals — the caller checks the result
            return True

        elif step.step_type in (
            RecoveryStepType.RESTART_BROWSER,
            RecoveryStepType.ROTATE_USER_AGENT,
            RecoveryStepType.CLEAR_COOKIES,
            RecoveryStepType.RETRY_WITH_FALLBACK_MODEL,
        ):
            # These require registered handlers — no default action
            logger.warning(
                "No handler registered for %s — step skipped",
                step.step_type.value,
            )
            return True

        return True

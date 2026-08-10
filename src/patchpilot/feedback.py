"""Deterministic validation feedback for the PatchPilot repair loop.

This module deliberately relies only on the standard library.  It turns noisy
command results into compact, repeatable facts that an agent loop can safely
put into its next prompt.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import re


class FailureCategory(str, Enum):
    """The finite set of failure signals understood by the repair loop."""

    SYNTAX = "syntax"
    TEST_ASSERTION = "test_assertion"
    MISSING_DEPENDENCY = "missing_dependency"
    TIMEOUT = "timeout"
    POLICY = "policy"
    UNKNOWN = "unknown"


_ANSI_ESCAPE = re.compile(
    r"(?:\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]|\x1b[@-_][ -/]*[@-~])"
)
_SYNTAX = re.compile(r"\b(?:SyntaxError|IndentationError|TabError)\b|\binvalid syntax\b", re.I)
_ASSERTION = re.compile(r"\bAssertionError\b|\bFAILED\b|\b(?:expected|actual)\b.*\b(?:!=|==)\b", re.I)
_DEPENDENCY = re.compile(r"\b(?:ModuleNotFoundError|ImportError)\b|\bNo module named\b|\bcannot import name\b", re.I)
_TIMEOUT = re.compile(r"\b(?:TimeoutExpired|timed out|timeout)\b", re.I)
_POLICY = re.compile(r"\b(?:policy|guardrail|approval)\b.*\b(?:deny|denied|required|block|blocked|violation)\b", re.I)


def clean_ansi(text: str) -> str:
    """Remove terminal escape sequences without altering meaningful output."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return _ANSI_ESCAPE.sub("", text)


def _utf8_prefix(text: str, max_bytes: int) -> str:
    """Return the longest character-aligned UTF-8 prefix within ``max_bytes``."""
    if max_bytes <= 0:
        return ""
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def truncate_output(text: str, max_bytes: int) -> str:
    """Bound output by bytes, retaining an explicit marker when it was clipped."""
    if not isinstance(max_bytes, int):
        raise TypeError("max_bytes must be an integer")
    cleaned = clean_ansi(text)
    if max_bytes <= 0:
        return ""
    if len(cleaned.encode("utf-8")) <= max_bytes:
        return cleaned
    marker = "...[truncated]"
    marker_bytes = len(marker.encode("utf-8"))
    if max_bytes <= marker_bytes:
        return _utf8_prefix(marker, max_bytes)
    return _utf8_prefix(cleaned, max_bytes - marker_bytes) + marker


class FailureClassifier:
    """Classify command failure output using fixed, auditable rules."""

    def classify(
        self,
        output: str,
        *,
        timed_out: bool = False,
        policy_blocked: bool = False,
    ) -> FailureCategory:
        message = clean_ansi(output)
        if policy_blocked or _POLICY.search(message):
            return FailureCategory.POLICY
        if timed_out or _TIMEOUT.search(message):
            return FailureCategory.TIMEOUT
        if _SYNTAX.search(message):
            return FailureCategory.SYNTAX
        if _ASSERTION.search(message):
            return FailureCategory.TEST_ASSERTION
        if _DEPENDENCY.search(message):
            return FailureCategory.MISSING_DEPENDENCY
        return FailureCategory.UNKNOWN


def classify_failure(
    output: str, *, timed_out: bool = False, policy_blocked: bool = False
) -> FailureCategory:
    """Convenience function for callers which do not need a classifier instance."""
    return FailureClassifier().classify(
        output, timed_out=timed_out, policy_blocked=policy_blocked
    )


def failure_fingerprint(category: FailureCategory | str, output: str) -> str:
    """Create a stable SHA-256 identifier for a normalized failure."""
    category_value = category.value if isinstance(category, FailureCategory) else str(category)
    normalized = clean_ansi(output).replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\b\d+(?:\.\d+)?s\b", "<duration>", normalized)
    payload = f"{category_value}\n{normalized}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class Feedback:
    """Compact result supplied to the next repair decision."""

    passed: bool
    category: FailureCategory | None
    output: str
    fingerprint: str | None
    consecutive_failures: int
    stalled: bool
    exit_code: int
    timed_out: bool = False
    policy_blocked: bool = False


class FeedbackLoop:
    """Track repeated failures and trip after a configured consecutive limit."""

    def __init__(self, repeat_failure_limit: int = 2, max_output_bytes: int = 16_384):
        if not isinstance(repeat_failure_limit, int) or repeat_failure_limit < 1:
            raise ValueError("repeat_failure_limit must be at least 1")
        if not isinstance(max_output_bytes, int) or max_output_bytes < 0:
            raise ValueError("max_output_bytes must be non-negative")
        self.repeat_failure_limit = repeat_failure_limit
        self.max_output_bytes = max_output_bytes
        self._last_fingerprint: str | None = None
        self._consecutive_failures = 0
        self._classifier = FailureClassifier()

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    def record(
        self,
        *,
        exit_code: int,
        stdout: str = "",
        stderr: str = "",
        timed_out: bool = False,
        policy_blocked: bool = False,
    ) -> Feedback:
        """Record one validation result and reset state immediately on success."""
        if not isinstance(exit_code, int):
            raise TypeError("exit_code must be an integer")
        combined = "\n".join(part for part in (stdout, stderr) if part)
        passed = exit_code == 0 and not timed_out and not policy_blocked
        compact = truncate_output(combined, self.max_output_bytes)
        if passed:
            self._last_fingerprint = None
            self._consecutive_failures = 0
            return Feedback(True, None, compact, None, 0, False, exit_code)

        category = self._classifier.classify(
            combined, timed_out=timed_out, policy_blocked=policy_blocked
        )
        fingerprint = failure_fingerprint(category, combined)
        if fingerprint == self._last_fingerprint:
            self._consecutive_failures += 1
        else:
            self._last_fingerprint = fingerprint
            self._consecutive_failures = 1
        stalled = self._consecutive_failures >= self.repeat_failure_limit
        return Feedback(
            False,
            category,
            compact,
            fingerprint,
            self._consecutive_failures,
            stalled,
            exit_code,
            timed_out,
            policy_blocked,
        )

    observe = record


__all__ = [
    "FailureCategory",
    "FailureClassifier",
    "Feedback",
    "FeedbackLoop",
    "clean_ansi",
    "classify_failure",
    "failure_fingerprint",
    "truncate_output",
]

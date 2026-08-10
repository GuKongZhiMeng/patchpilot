import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from patchpilot.feedback import (
    FailureCategory,
    FeedbackLoop,
    FailureClassifier,
    clean_ansi,
    failure_fingerprint,
    truncate_output,
)


class FailureClassifierTests(unittest.TestCase):
    def test_classifies_deterministic_failure_signals(self):
        classifier = FailureClassifier()
        self.assertEqual(classifier.classify("SyntaxError: invalid syntax"), FailureCategory.SYNTAX)
        self.assertEqual(classifier.classify("AssertionError: expected 2"), FailureCategory.TEST_ASSERTION)
        self.assertEqual(classifier.classify("ModuleNotFoundError: No module named 'demo'"), FailureCategory.MISSING_DEPENDENCY)
        self.assertEqual(classifier.classify("anything", timed_out=True), FailureCategory.TIMEOUT)
        self.assertEqual(classifier.classify("policy denied this action"), FailureCategory.POLICY)
        self.assertEqual(classifier.classify("unrecognised failure"), FailureCategory.UNKNOWN)


class OutputNormalisationTests(unittest.TestCase):
    def test_removes_ansi_and_truncates_on_utf8_boundaries(self):
        self.assertEqual(clean_ansi("\x1b[31mFAILED\x1b[0m"), "FAILED")
        value = "错误" * 20
        shortened = truncate_output(value, 20)
        self.assertLessEqual(len(shortened.encode("utf-8")), 20)
        self.assertTrue(shortened.endswith("...[truncated]"))

    def test_fingerprint_is_stable_and_ignores_ansi(self):
        plain = failure_fingerprint(FailureCategory.TEST_ASSERTION, "AssertionError: x")
        coloured = failure_fingerprint(FailureCategory.TEST_ASSERTION, "\x1b[31mAssertionError: x\x1b[0m")
        self.assertEqual(plain, coloured)
        self.assertEqual(plain, failure_fingerprint(FailureCategory.TEST_ASSERTION, "AssertionError: x"))


class FeedbackLoopTests(unittest.TestCase):
    def test_repeated_failure_trips_circuit_breaker(self):
        loop = FeedbackLoop(repeat_failure_limit=2, max_output_bytes=200)
        first = loop.record(exit_code=1, stdout="", stderr="AssertionError: x")
        second = loop.record(exit_code=1, stdout="", stderr="AssertionError: x")
        self.assertFalse(first.stalled)
        self.assertEqual(second.consecutive_failures, 2)
        self.assertTrue(second.stalled)

    def test_success_resets_consecutive_failure_state(self):
        loop = FeedbackLoop(repeat_failure_limit=2)
        loop.record(exit_code=1, stdout="", stderr="AssertionError: x")
        passed = loop.record(exit_code=0, stdout="ok", stderr="")
        later = loop.record(exit_code=1, stdout="", stderr="AssertionError: x")
        self.assertTrue(passed.passed)
        self.assertEqual(passed.consecutive_failures, 0)
        self.assertEqual(later.consecutive_failures, 1)
        self.assertFalse(later.stalled)


if __name__ == "__main__":
    unittest.main()

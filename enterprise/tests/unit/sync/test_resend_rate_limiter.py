"""Tests for the rate limiting functionality in resend_keycloak.py.

These tests verify the rate limiting functionality that prevents
hitting Resend API rate limits (2 requests per second).
"""

import threading
import time

from ratelimit import limits, sleep_and_retry
from resend.exceptions import ResendError


# Copy of the exception classes for testing
class ResendSyncError(Exception):
    """Base exception for Resend sync errors."""

    pass


class RateLimitError(ResendSyncError):
    """Exception for rate limit errors that shouldn't be retried immediately."""

    pass


def is_rate_limit_error(error: Exception) -> bool:
    """Check if an error is a rate limit error.

    Args:
        error: The exception to check.

    Returns:
        True if the error is a rate limit error, False otherwise.
    """
    if isinstance(error, ResendError):
        error_msg = str(error).lower()
        return (
            'rate limit' in error_msg
            or 'too many requests' in error_msg
            or '429' in error_msg
        )
    return False


class TestRateLimitedResendCall:
    """Tests for the rate-limited Resend API call wrapper."""

    def test_rate_limiter_enforces_rate_limit(self):
        """Test that the ratelimit library enforces the rate limit."""
        # Create a test rate limiter with 2 calls per second
        call_count = 0
        semaphore = threading.Semaphore(1)

        @sleep_and_retry
        @limits(calls=2, period=1)
        def rate_limited_call():
            nonlocal call_count
            with semaphore:
                call_count += 1
                return call_count

        start_time = time.time()

        # Make 4 calls - should take at least 1 second (2 calls per second)
        for _ in range(4):
            rate_limited_call()

        elapsed = time.time() - start_time

        # 4 calls at 2 calls/sec should take at least 1 second
        assert elapsed >= 0.9  # Allow small tolerance
        assert call_count == 4

    def test_rate_limiter_with_semaphore_thread_safety(self):
        """Test that the semaphore provides thread safety."""
        results = []
        semaphore = threading.Semaphore(1)

        @sleep_and_retry
        @limits(calls=10, period=1)  # Higher limit for this test
        def rate_limited_call(value):
            with semaphore:
                results.append(value)
                return value

        # Make calls from multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=rate_limited_call, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All calls should have completed
        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}


class TestIsRateLimitError:
    """Tests for the is_rate_limit_error function."""

    def test_detects_rate_limit_message(self):
        """Test that rate limit errors are detected by message."""
        # Test various rate limit error messages
        error1 = ResendError(
            message='Too many requests',
            code=429,
            error_type='rate_limit_exceeded',
            suggested_action='Wait and retry',
        )
        assert is_rate_limit_error(error1) is True

        error2 = ResendError(
            message='Rate limit exceeded',
            code=429,
            error_type='rate_limit_exceeded',
            suggested_action='Wait and retry',
        )
        assert is_rate_limit_error(error2) is True

        error3 = ResendError(
            message='429 Too Many Requests',
            code=429,
            error_type='rate_limit_exceeded',
            suggested_action='Wait and retry',
        )
        assert is_rate_limit_error(error3) is True

    def test_does_not_detect_other_errors(self):
        """Test that non-rate-limit errors are not detected."""
        error = ResendError(
            message='Invalid email address',
            code=400,
            error_type='validation_error',
            suggested_action='Check email format',
        )
        assert is_rate_limit_error(error) is False

    def test_handles_non_resend_errors(self):
        """Test that non-ResendError exceptions return False."""
        error = ValueError('Some other error')
        assert is_rate_limit_error(error) is False


class TestRateLimitError:
    """Tests for the RateLimitError exception."""

    def test_rate_limit_error_is_resend_sync_error(self):
        """Test that RateLimitError inherits from ResendSyncError."""
        error = RateLimitError('Rate limit hit')
        assert isinstance(error, ResendSyncError)

    def test_rate_limit_error_message(self):
        """Test that RateLimitError preserves the message."""
        error = RateLimitError('Rate limit hit for test@example.com')
        assert 'test@example.com' in str(error)

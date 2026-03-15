"""Unit tests for T-022: retry utility."""
from __future__ import annotations

import pytest

from app.utils.retry import retry


class _Transient(Exception):
    pass


class _Fatal(Exception):
    pass


class TestRetrySucceedsImmediately:
    def test_succeeds_on_first_attempt(self):
        calls = []

        def fn():
            calls.append(1)
            return "ok"

        result = retry(fn, retryable=(_Transient,), max_attempts=3, initial_delay_sec=0)
        assert result == "ok"
        assert len(calls) == 1

    def test_returns_value_on_success(self):
        result = retry(lambda: 42, retryable=(_Transient,), max_attempts=3, initial_delay_sec=0)
        assert result == 42


class TestRetryRetriesOnTransientError:
    def test_retries_and_succeeds_on_second_attempt(self, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda _: None)
        call_count = [0]

        def fn():
            call_count[0] += 1
            if call_count[0] < 2:
                raise _Transient("transient")
            return "ok"

        result = retry(fn, retryable=(_Transient,), max_attempts=3, initial_delay_sec=0.001)
        assert result == "ok"
        assert call_count[0] == 2

    def test_retries_up_to_max_attempts(self, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda _: None)
        call_count = [0]

        def fn():
            call_count[0] += 1
            raise _Transient("always fails")

        with pytest.raises(_Transient):
            retry(fn, retryable=(_Transient,), max_attempts=3, initial_delay_sec=0.001)
        assert call_count[0] == 3

    def test_raises_last_exception_after_exhaustion(self, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda _: None)
        attempt_errors = [_Transient(f"error_{i}") for i in range(3)]
        idx = [0]

        def fn():
            exc = attempt_errors[idx[0]]
            idx[0] += 1
            raise exc

        with pytest.raises(_Transient, match="error_2"):
            retry(fn, retryable=(_Transient,), max_attempts=3, initial_delay_sec=0.001)

    def test_single_attempt_raises_immediately(self, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda _: None)
        call_count = [0]

        def fn():
            call_count[0] += 1
            raise _Transient("fail")

        with pytest.raises(_Transient):
            retry(fn, retryable=(_Transient,), max_attempts=1, initial_delay_sec=0)
        assert call_count[0] == 1


class TestRetryDoesNotRetryFatalErrors:
    def test_non_retryable_exception_propagates_immediately(self, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda _: None)
        call_count = [0]

        def fn():
            call_count[0] += 1
            raise _Fatal("fatal")

        with pytest.raises(_Fatal):
            retry(fn, retryable=(_Transient,), max_attempts=3, initial_delay_sec=0.001)
        assert call_count[0] == 1

    def test_non_retryable_does_not_sleep(self, monkeypatch):
        sleep_calls = []
        monkeypatch.setattr("time.sleep", lambda d: sleep_calls.append(d))

        def fn():
            raise _Fatal("fatal")

        with pytest.raises(_Fatal):
            retry(fn, retryable=(_Transient,), max_attempts=3, initial_delay_sec=1.0)
        assert sleep_calls == []


class TestRetryExponentialBackoff:
    def test_sleep_delays_double_each_attempt(self, monkeypatch):
        delays = []
        monkeypatch.setattr("time.sleep", lambda d: delays.append(d))
        call_count = [0]

        def fn():
            call_count[0] += 1
            raise _Transient("fail")

        with pytest.raises(_Transient):
            retry(fn, retryable=(_Transient,), max_attempts=4, initial_delay_sec=1.0)

        # 3 sleeps for 4 attempts: 1.0, 2.0, 4.0
        assert len(delays) == 3
        assert delays == [1.0, 2.0, 4.0]

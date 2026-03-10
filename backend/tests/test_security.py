# Tests for CPX-SEC Security Features (Rate Limiter & Audit Logger)

import pytest
import time
from app.services.rate_limiter import RateLimiter, RateLimitConfig, get_rate_limiter, reset_rate_limiter
from app.services.audit_logger import (
    AuditLogger, AuditEventType, AuditSeverity, get_audit_logger, reset_audit_logger
)


class TestRateLimiter:
    """Test rate limiting functionality"""

    def setup_method(self):
        """Reset rate limiter before each test"""
        reset_rate_limiter()

    def test_rate_limiter_allows_requests_within_limit(self):
        """Test that requests within limit are allowed"""
        limiter = RateLimiter()
        client_id = "test_client"
        endpoint = "/api/test"

        # Should allow requests up to limit
        for i in range(5):
            is_allowed, info = limiter.check_rate_limit(client_id, endpoint)
            assert is_allowed is True
            assert info["remaining"] >= 0

    def test_rate_limiter_blocks_requests_over_limit(self):
        """Test that requests over limit are blocked"""
        limiter = RateLimiter({
            "/api/test": RateLimitConfig(requests_per_window=3, window_seconds=60)
        })
        client_id = "test_client"
        endpoint = "/api/test"

        # Fill up the limit
        for i in range(3):
            limiter.check_rate_limit(client_id, endpoint)

        # Next request should be blocked
        is_allowed, info = limiter.check_rate_limit(client_id, endpoint)
        assert is_allowed is False
        assert info["remaining"] == 0
        assert info["retry_after"] is not None

    def test_rate_limiter_different_clients(self):
        """Test that different clients have separate limits"""
        limiter = RateLimiter({
            "/api/test": RateLimitConfig(requests_per_window=2, window_seconds=60)
        })
        endpoint = "/api/test"

        # Client 1 hits limit
        limiter.check_rate_limit("client1", endpoint)
        limiter.check_rate_limit("client1", endpoint)
        is_allowed, _ = limiter.check_rate_limit("client1", endpoint)
        assert is_allowed is False

        # Client 2 should still be allowed
        is_allowed, _ = limiter.check_rate_limit("client2", endpoint)
        assert is_allowed is True

    def test_rate_limiter_different_endpoints(self):
        """Test that different endpoints have separate limits"""
        limiter = RateLimiter({
            "/api/endpoint1": RateLimitConfig(requests_per_window=1, window_seconds=60),
            "/api/endpoint2": RateLimitConfig(requests_per_window=2, window_seconds=60),
        })

        # Hit limit on endpoint1
        limiter.check_rate_limit("client", "/api/endpoint1")
        is_allowed, _ = limiter.check_rate_limit("client", "/api/endpoint1")
        assert is_allowed is False

        # endpoint2 should still be allowed
        limiter.check_rate_limit("client", "/api/endpoint2")
        is_allowed, _ = limiter.check_rate_limit("client", "/api/endpoint2")
        assert is_allowed is True

    def test_rate_limiter_reset_client(self):
        """Test client reset functionality"""
        limiter = RateLimiter({
            "/api/test": RateLimitConfig(requests_per_window=1, window_seconds=60)
        })
        client_id = "test_client"
        endpoint = "/api/test"

        # Hit limit
        limiter.check_rate_limit(client_id, endpoint)
        is_allowed, _ = limiter.check_rate_limit(client_id, endpoint)
        assert is_allowed is False

        # Reset and try again
        limiter.reset_client(client_id)
        is_allowed, _ = limiter.check_rate_limit(client_id, endpoint)
        assert is_allowed is True

    def test_rate_limiter_get_stats(self):
        """Test getting rate limit stats"""
        limiter = RateLimiter({
            "/api/test": RateLimitConfig(requests_per_window=10, window_seconds=60, burst_allowance=2)
        })

        limiter.check_rate_limit("client", "/api/test")
        limiter.check_rate_limit("client", "/api/test")

        stats = limiter.get_stats("client", "/api/test")
        assert stats["current"] == 2
        assert stats["limit"] == 10
        assert stats["burst"] == 2
        # remaining = (limit + burst) - current = 12 - 2 = 10
        assert stats["remaining"] == 10


class TestAuditLogger:
    """Test audit logging functionality"""

    def setup_method(self):
        """Reset audit logger before each test"""
        reset_audit_logger()

    def test_audit_logger_creates_event(self):
        """Test that audit events are created"""
        logger = AuditLogger()

        event_id = logger.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            action="user_login",
            result="success",
            user_id="user123",
            username="testuser",
            ip_address="192.168.1.1"
        )

        assert event_id is not None
        assert len(event_id) > 0

    def test_audit_logger_stores_events(self):
        """Test that events are stored"""
        logger = AuditLogger()

        logger.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            action="login",
            result="success",
            user_id="user1"
        )

        logger.log_event(
            event_type=AuditEventType.GAME_CREATED,
            action="create_game",
            result="success",
            user_id="user1"
        )

        events = logger.get_events(user_id="user1")
        assert len(events) == 2

    def test_audit_logger_filters_by_event_type(self):
        """Test filtering by event type"""
        logger = AuditLogger()

        logger.log_event(event_type=AuditEventType.LOGIN_SUCCESS, action="login", result="success")
        logger.log_event(event_type=AuditEventType.LOGOUT, action="logout", result="success")
        logger.log_event(event_type=AuditEventType.LOGIN_FAILED, action="login", result="failure")

        login_events = logger.get_events(event_type=AuditEventType.LOGIN_SUCCESS)
        assert len(login_events) == 1

    def test_audit_logger_security_events(self):
        """Test getting security events"""
        logger = AuditLogger()

        # Add normal events
        logger.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            action="login",
            result="success",
            severity=AuditSeverity.INFO
        )

        # Add security events
        logger.log_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            action="rate_limit",
            result="blocked",
            severity=AuditSeverity.WARNING
        )

        logger.log_event(
            event_type=AuditEventType.INVALID_REQUEST,
            action="invalid_request",
            result="error",
            severity=AuditSeverity.ERROR
        )

        security_events = logger.get_security_events()
        assert len(security_events) == 2

    def test_audit_logger_clear(self):
        """Test clearing audit events"""
        logger = AuditLogger()

        logger.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            action="login",
            result="success"
        )

        assert len(logger.get_events()) == 1

        logger.clear()
        assert len(logger.get_events()) == 0


class TestRateLimiterDefaults:
    """Test default rate limit configurations"""

    def test_default_limits_exist(self):
        """Test that default limits are defined"""
        limiter = RateLimiter()

        # Check some expected endpoints have limits
        assert "/api/auth/login" in limiter.limits
        assert "/api/games" in limiter.limits
        assert "/api/orders/" in limiter.limits
        assert "/api/turn/commit" in limiter.limits
        assert "/api/internal/" in limiter.limits

    def test_auth_endpoints_have_strict_limits(self):
        """Test that auth endpoints have stricter limits"""
        limiter = RateLimiter()

        login_limit = limiter.limits["/api/auth/login"]
        games_limit = limiter.limits["/api/games"]

        # Auth should have lower limits than game endpoints
        assert login_limit.requests_per_window <= games_limit.requests_per_window

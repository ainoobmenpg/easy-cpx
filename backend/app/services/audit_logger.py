# Audit Logging Service - CPX-SEC
# Provides structured audit logging for security events

import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading


class AuditEventType(Enum):
    """Types of audit events"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"

    # Authorization events
    ACCESS_DENIED = "access_denied"
    ROLE_CHANGED = "role_changed"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"

    # Game events
    GAME_CREATED = "game_created"
    GAME_JOINED = "game_joined"
    GAME_LEFT = "game_left"
    GAME_ENDED = "game_ended"

    # Order events
    ORDER_SUBMITTED = "order_submitted"
    ORDER_MODIFIED = "order_modified"
    ORDER_CANCELLED = "order_cancelled"
    TURN_COMMITTED = "turn_committed"

    # Admin events
    CONFIG_CHANGED = "config_changed"
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"

    # Security events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_REQUEST = "invalid_request"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # Data events
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit log entry"""
    event_id: str
    timestamp: str
    event_type: str
    severity: str
    user_id: Optional[str]
    username: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    status_code: Optional[int]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    result: str
    details: Dict[str, Any]
    session_id: Optional[str]
    request_id: Optional[str]


class AuditLogger:
    """
    Structured audit logger for security and compliance.
    Thread-safe for concurrent access.
    """

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file
        self._events: List[AuditEvent] = []
        self._lock = threading.Lock()
        self._max_memory_events = 10000  # Keep last 10000 in memory

    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        result: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> str:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            action: Action performed
            result: Result of action (success, failure, etc.)
            severity: Severity level
            user_id: User ID (if authenticated)
            username: Username
            ip_address: Client IP address
            user_agent: Client user agent
            endpoint: API endpoint
            method: HTTP method
            status_code: HTTP status code
            resource_type: Type of resource accessed
            resource_id: ID of resource
            details: Additional details
            session_id: Session ID
            request_id: Request ID for tracing

        Returns:
            Event ID for reference
        """
        event = AuditEvent(
            event_id=str(uuid.uuid4())[:12],
            timestamp=datetime.utcnow().isoformat() + "Z",
            event_type=event_type.value,
            severity=severity.value,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            details=details or {},
            session_id=session_id,
            request_id=request_id,
        )

        with self._lock:
            self._events.append(event)

            # Trim old events if exceeding max
            if len(self._events) > self._max_memory_events:
                self._events = self._events[-self._max_memory_events:]

        # Write to file if configured
        if self.log_file:
            self._write_to_file(event)

        return event.event_id

    def _write_to_file(self, event: AuditEvent) -> None:
        """Write event to log file"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(asdict(event)) + '\n')
        except Exception:
            pass  # Fail silently for file writes

    def get_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Query audit events with filters"""
        with self._lock:
            filtered = self._events.copy()

        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]

        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type.value]

        if start_time:
            start_iso = start_time.isoformat()
            filtered = [e for e in filtered if e.timestamp >= start_iso]

        if end_time:
            end_iso = end_time.isoformat()
            filtered = [e for e in filtered if e.timestamp <= end_iso]

        return filtered[-limit:]

    def get_security_events(
        self,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Get security-related events (warnings, errors, critical)"""
        with self._lock:
            filtered = self._events.copy()

        severity_levels = {AuditSeverity.WARNING.value, AuditSeverity.ERROR.value, AuditSeverity.CRITICAL.value}
        filtered = [e for e in filtered if e.severity in severity_levels]

        if since:
            since_iso = since.isoformat()
            filtered = [e for e in filtered if e.timestamp >= since_iso]

        return filtered[-limit:]

    def clear(self) -> None:
        """Clear in-memory events (for testing)"""
        with self._lock:
            self._events.clear()


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(log_file: Optional[str] = None) -> AuditLogger:
    """Get the global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(log_file)
    return _audit_logger


def reset_audit_logger() -> None:
    """Reset the global audit logger (for testing)"""
    global _audit_logger
    _audit_logger = None

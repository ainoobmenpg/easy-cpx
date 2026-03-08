# Reporting Requirement System for Operational CPX
# Tracks and enforces commander reporting requirements
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ReportingEvent:
    """An event that should be reported"""
    event_type: str
    timestamp: datetime
    details: dict
    reported: bool = False
    report_text: Optional[str] = None


@dataclass
class CommanderInquiry:
    """An inquiry from the commander when reporting requirements are not met"""
    inquiry_id: int
    timestamp: datetime
    subject: str
    question: str
    urgency: str  # low, normal, high, critical
    response_required: bool = True
    response_text: Optional[str] = None
    responded_at: Optional[datetime] = None


class ReportingSystem:
    """
    Manages reporting requirements from commander

    If the player does not report required events, the commander
    will send inquiries, potentially leading to distrust events.
    """

    DEFAULT_REPORTING_REQUIREMENTS = [
        "enemy_contact",      # Contact with enemy forces
        "border_incursion",   # Border crossing detected
        "civilian_casualties", # Civilian casualties
        "command_breakdown",   # Loss of command connectivity
        "unexpected_resistance", # Unexpected enemy resistance
        "supply_line_cut",     # Supply lines interrupted
        "unit_destroyed",      # Unit destroyed
        "objective_lost",      # Lost an objective
    ]

    def __init__(self):
        self._events: list[ReportingEvent] = []
        self._inquiries: list[CommanderInquiry] = []
        self._reporting_requirements = self.DEFAULT_REPORTING_REQUIREMENTS.copy()
        self._unreported_count = 0
        self._inquiry_counter = 0
        self._distrust_level = 0  # 0-100
        self._last_report_turn = 0

    def set_reporting_requirements(self, requirements: list[str]):
        """Set the list of events that must be reported"""
        self._reporting_requirements = requirements.copy()

    def add_event(self, event_type: str, details: dict = None):
        """Add an event that may need reporting"""
        event = ReportingEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            details=details or {}
        )
        self._events.append(event)

        # Check if this event requires reporting
        if self._requires_reporting(event_type):
            self._unreported_count += 1

    def _requires_reporting(self, event_type: str) -> bool:
        """Check if an event type requires reporting"""
        event_type_lower = event_type.lower()
        for req in self._reporting_requirements:
            if req.lower() in event_type_lower:
                return True
        return False

    def report_event(self, event_index: int, report_text: str, turn: int) -> bool:
        """Player reports an event"""
        if 0 <= event_index < len(self._events):
            self._events[event_index].reported = True
            self._events[event_index].report_text = report_text
            self._unreported_count = max(0, self._unreported_count - 1)
            self._last_report_turn = turn
            return True
        return False

    def check_reporting_compliance(self, current_turn: int) -> list[CommanderInquiry]:
        """
        Check if reporting requirements are being met

        Returns list of inquiries if there are compliance issues
        """
        inquiries = []

        # Check if too many unreported events
        if self._unreported_count >= 3:
            inquiry = self._create_inquiry(
                subject="未報告の重要事項について",
                question=f"{-self._unreported_count}件の重要事項が報告されていません。状況を説明してください。",
                urgency="high"
            )
            inquiries.append(inquiry)
            self._distrust_level += 10

        # Check if no reports for too long
        turns_since_report = current_turn - self._last_report_turn
        if turns_since_report >= 2 and self._unreported_count > 0:
            inquiry = self._create_inquiry(
                subject="報告の遅延",
                question="久しく報告がありません。現在の状況は？",
                urgency="normal"
            )
            inquiries.append(inquiry)
            self._distrust_level += 5

        # Check specific high-priority events
        for event in self._events:
            if not event.reported and self._requires_reporting(event.event_type):
                # Check if event is old (more than 1 turn)
                # For simplicity, we'll just track high-priority events
                if event.details.get("priority") == "high":
                    inquiry = self._create_inquiry(
                        subject=f"{event.event_type}について",
                        question="この件についてまだ報告がありません。",
                        urgency="critical"
                    )
                    inquiries.append(inquiry)
                    self._distrust_level += 15

        self._inquiries.extend(inquiries)
        return inquiries

    def _create_inquiry(
        self,
        subject: str,
        question: str,
        urgency: str
    ) -> CommanderInquiry:
        """Create a new commander inquiry"""
        self._inquiry_counter += 1
        return CommanderInquiry(
            inquiry_id=self._inquiry_counter,
            timestamp=datetime.utcnow(),
            subject=subject,
            question=question,
            urgency=urgency
        )

    def respond_to_inquiry(self, inquiry_id: int, response: str) -> bool:
        """Player responds to a commander inquiry"""
        for inquiry in self._inquiries:
            if inquiry.inquiry_id == inquiry_id:
                inquiry.response_text = response
                inquiry.responded_at = datetime.utcnow()
                inquiry.response_required = False

                # Reduce distrust if responded appropriately
                if inquiry.urgency in ["normal", "low"]:
                    self._distrust_level = max(0, self._distrust_level - 5)
                elif inquiry.urgency == "high":
                    self._distrust_level = max(0, self._distrust_level - 10)
                elif inquiry.urgency == "critical":
                    self._distrust_level = max(0, self._distrust_level - 15)

                return True
        return False

    def get_pending_inquiries(self) -> list[CommanderInquiry]:
        """Get all inquiries that need a response"""
        return [i for i in self._inquiries if i.response_required]

    def get_distrust_level(self) -> int:
        """Get current commander distrust level (0-100)"""
        return self._distrust_level

    def get_distrust_description(self) -> str:
        """Get human-readable description of distrust level"""
        if self._distrust_level < 20:
            return "信頼厚く任務を委ねられている"
        elif self._distrust_level < 40:
            return "特に問題はない"
        elif self._distrust_level < 60:
            return "若干の不信感がある"
        elif self._distrust_level < 80:
            return "信頼が揺らいでいる"
        else:
            return "信頼危机 - 任務の続行が疑问视される"

    def get_unreported_events(self) -> list[ReportingEvent]:
        """Get list of unreported events"""
        return [e for e in self._events if not e.reported]

    def get_reported_events(self) -> list[ReportingEvent]:
        """Get list of reported events"""
        return [e for e in self._events if e.reported]

    def get_reporting_summary(self) -> dict:
        """Get a summary of reporting status"""
        return {
            "total_events": len(self._events),
            "reported": len(self.get_reported_events()),
            "unreported": len(self.get_unreported_events()),
            "pending_inquiries": len(self.get_pending_inquiries()),
            "distrust_level": self._distrust_level,
            "distrust_description": self.get_distrust_description()
        }

    def format_pending_inquiries(self) -> str:
        """Format pending inquiries for display"""
        inquiries = self.get_pending_inquiries()
        if not inquiries:
            return "未回答の質疑なし"

        lines = ["【上官からの質疑】"]
        for inquiry in inquiries:
            urgency_icon = {
                "low": "○",
                "normal": "△",
                "high": "◐",
                "critical": "⚠"
            }.get(inquiry.urgency, "?")

            lines.append(f"{urgency_icon} {inquiry.subject}")
            lines.append(f"   {inquiry.question}")

        return "\n".join(lines)


# Global instance
_reporting_system = ReportingSystem()


def get_reporting_system() -> ReportingSystem:
    """Get the global reporting system"""
    return _reporting_system

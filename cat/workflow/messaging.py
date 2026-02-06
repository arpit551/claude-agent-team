"""Agent communication and messaging protocols."""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from cat.agent.models import AgentRole

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of inter-agent messages."""

    FINDING = "finding"  # Share a finding/discovery
    QUESTION = "question"  # Ask another agent a question
    ANSWER = "answer"  # Answer a question
    COORDINATE = "coordinate"  # Coordination request
    STATUS = "status"  # Status update
    CLAIM = "claim"  # Claim a task
    PROGRESS = "progress"  # Progress update
    BLOCKED = "blocked"  # Report blocking issue
    COMPLETE = "complete"  # Report completion
    ERROR = "error"  # Report error


class Severity(Enum):
    """Message severity levels."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Message:
    """Inter-agent message."""

    from_role: AgentRole
    to_role: Optional[AgentRole]  # None = broadcast
    msg_type: MessageType
    content: str
    severity: Severity = Severity.INFO
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    message_id: Optional[str] = None

    def __post_init__(self):
        """Generate message ID if not provided."""
        if self.message_id is None:
            self.message_id = f"{self.from_role.value}_{self.timestamp.timestamp()}"

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "from_role": self.from_role.value,
            "to_role": self.to_role.value if self.to_role else None,
            "msg_type": self.msg_type.value,
            "content": self.content,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "message_id": self.message_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create from dictionary.

        Args:
            data: Dictionary data

        Returns:
            Message instance
        """
        return cls(
            from_role=AgentRole(data["from_role"]),
            to_role=AgentRole(data["to_role"]) if data.get("to_role") else None,
            msg_type=MessageType(data["msg_type"]),
            content=data["content"],
            severity=Severity(data.get("severity", "info")),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            message_id=data.get("message_id"),
        )

    def format_cli(self) -> str:
        """Format for CLI display.

        Returns:
            Formatted string
        """
        severity_symbols = {
            Severity.INFO: "ℹ",
            Severity.LOW: "◉",
            Severity.MEDIUM: "⚠",
            Severity.HIGH: "⚠",
            Severity.CRITICAL: "⚠",
        }

        type_symbols = {
            MessageType.FINDING: "[FINDING]",
            MessageType.QUESTION: "[QUESTION]",
            MessageType.ANSWER: "[ANSWER]",
            MessageType.COORDINATE: "[COORD]",
            MessageType.STATUS: "[STATUS]",
            MessageType.CLAIM: "[CLAIM]",
            MessageType.PROGRESS: "[PROGRESS]",
            MessageType.BLOCKED: "[BLOCKED]",
            MessageType.COMPLETE: "[COMPLETE]",
            MessageType.ERROR: "[ERROR]",
        }

        symbol = severity_symbols.get(self.severity, "◦")
        type_tag = type_symbols.get(self.msg_type, "")

        to_str = f"→ {self.to_role.display_name}" if self.to_role else "→ ALL"

        return f"{symbol} {type_tag} {self.from_role.display_name} {to_str}: {self.content}"


class MessageBus:
    """Central message bus for agent communication."""

    def __init__(self, message_dir: Path):
        """Initialize message bus.

        Args:
            message_dir: Directory for storing messages
        """
        self.message_dir = message_dir
        self.message_dir.mkdir(parents=True, exist_ok=True)

        # Message files
        self.messages_file = message_dir / "messages.jsonl"
        self.inbox_dir = message_dir / "inbox"
        self.inbox_dir.mkdir(exist_ok=True)

        # In-memory message tracking
        self._messages: list[Message] = []
        self._load_messages()

    def _load_messages(self) -> None:
        """Load existing messages from file."""
        if not self.messages_file.exists():
            return

        try:
            with open(self.messages_file) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        msg = Message.from_dict(data)
                        self._messages.append(msg)

            logger.info(f"Loaded {len(self._messages)} messages")

        except Exception as e:
            logger.error(f"Error loading messages: {e}", exc_info=True)

    def send(self, message: Message) -> None:
        """Send a message.

        Args:
            message: Message to send
        """
        # Add to in-memory list
        self._messages.append(message)

        # Persist to file (append-only)
        try:
            with open(self.messages_file, "a") as f:
                f.write(json.dumps(message.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Error saving message: {e}")

        # Write to recipient's inbox
        if message.to_role:
            self._write_to_inbox(message.to_role, message)
        else:
            # Broadcast - write to all inboxes
            for role in AgentRole:
                if role != message.from_role:
                    self._write_to_inbox(role, message)

        logger.debug(f"Message sent: {message.format_cli()}")

    def _write_to_inbox(self, role: AgentRole, message: Message) -> None:
        """Write message to agent's inbox.

        Args:
            role: Recipient role
            message: Message to deliver
        """
        inbox_file = self.inbox_dir / f"{role.value}.jsonl"

        try:
            with open(inbox_file, "a") as f:
                f.write(json.dumps(message.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Error writing to inbox for {role.display_name}: {e}")

    def get_messages(
        self,
        from_role: Optional[AgentRole] = None,
        to_role: Optional[AgentRole] = None,
        msg_type: Optional[MessageType] = None,
        since: Optional[datetime] = None,
    ) -> list[Message]:
        """Get messages matching filters.

        Args:
            from_role: Filter by sender
            to_role: Filter by recipient
            msg_type: Filter by message type
            since: Filter by timestamp (after this time)

        Returns:
            List of matching messages
        """
        messages = self._messages.copy()

        if from_role:
            messages = [m for m in messages if m.from_role == from_role]

        if to_role:
            messages = [
                m for m in messages if m.to_role == to_role or m.to_role is None
            ]

        if msg_type:
            messages = [m for m in messages if m.msg_type == msg_type]

        if since:
            messages = [m for m in messages if m.timestamp > since]

        return messages

    def get_inbox(self, role: AgentRole, unread_only: bool = False) -> list[Message]:
        """Get messages for an agent.

        Args:
            role: Agent role
            unread_only: Return only unread messages

        Returns:
            List of messages
        """
        # For simplicity, return all messages to this role
        # In production, would track read/unread status
        return self.get_messages(to_role=role)

    def clear_inbox(self, role: AgentRole) -> None:
        """Clear an agent's inbox.

        Args:
            role: Agent role
        """
        inbox_file = self.inbox_dir / f"{role.value}.jsonl"
        if inbox_file.exists():
            inbox_file.unlink()
            logger.debug(f"Cleared inbox for {role.display_name}")

    def get_recent_messages(self, limit: int = 50) -> list[Message]:
        """Get most recent messages.

        Args:
            limit: Maximum number of messages

        Returns:
            List of recent messages
        """
        return self._messages[-limit:] if len(self._messages) > limit else self._messages

    def count_messages(self) -> int:
        """Get total message count.

        Returns:
            Number of messages
        """
        return len(self._messages)


# Helper functions for creating common message types

def finding_message(
    from_role: AgentRole,
    finding: str,
    severity: Severity = Severity.MEDIUM,
    file: Optional[str] = None,
    line: Optional[int] = None,
) -> Message:
    """Create a finding message.

    Args:
        from_role: Sender role
        finding: Finding description
        severity: Finding severity
        file: File where finding was discovered
        line: Line number

    Returns:
        Message instance
    """
    metadata = {}
    if file:
        metadata["file"] = file
    if line:
        metadata["line"] = line

    return Message(
        from_role=from_role,
        to_role=None,  # Broadcast
        msg_type=MessageType.FINDING,
        content=finding,
        severity=severity,
        metadata=metadata,
    )


def coordinate_message(
    from_role: AgentRole,
    to_role: AgentRole,
    request: str,
) -> Message:
    """Create a coordination message.

    Args:
        from_role: Sender role
        to_role: Recipient role
        request: Coordination request

    Returns:
        Message instance
    """
    return Message(
        from_role=from_role,
        to_role=to_role,
        msg_type=MessageType.COORDINATE,
        content=request,
        severity=Severity.INFO,
    )


def progress_message(
    from_role: AgentRole,
    status: str,
    percent: Optional[int] = None,
) -> Message:
    """Create a progress message.

    Args:
        from_role: Sender role
        status: Status description
        percent: Progress percentage

    Returns:
        Message instance
    """
    metadata = {}
    if percent is not None:
        metadata["percent"] = percent

    return Message(
        from_role=from_role,
        to_role=None,  # Broadcast
        msg_type=MessageType.PROGRESS,
        content=status,
        severity=Severity.INFO,
        metadata=metadata,
    )


def blocked_message(
    from_role: AgentRole,
    reason: str,
    severity: Severity = Severity.HIGH,
) -> Message:
    """Create a blocked message.

    Args:
        from_role: Sender role
        reason: Blocking reason
        severity: Severity level

    Returns:
        Message instance
    """
    return Message(
        from_role=from_role,
        to_role=None,  # Broadcast
        msg_type=MessageType.BLOCKED,
        content=reason,
        severity=severity,
    )

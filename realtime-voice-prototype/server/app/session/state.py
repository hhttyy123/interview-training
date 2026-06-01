from dataclasses import dataclass, field
from enum import Enum


class SessionStatus(str, Enum):
    READY = "ready"
    ENDED = "ended"


@dataclass
class ConversationMessage:
    role: str
    text: str


@dataclass
class VoiceSession:
    session_id: str
    status: SessionStatus = SessionStatus.READY
    messages: list[ConversationMessage] = field(default_factory=list)

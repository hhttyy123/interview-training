from uuid import uuid4

from app.session.state import ConversationMessage, SessionStatus, VoiceSession


class VoiceSessionManager:
    """Maintains only the active transient session for one socket."""

    def __init__(self) -> None:
        self.active_session: VoiceSession | None = None

    def start(self) -> VoiceSession:
        self.active_session = VoiceSession(session_id=str(uuid4()))
        return self.active_session

    def stop(self) -> str | None:
        if self.active_session is None:
            return None
        self.active_session.status = SessionStatus.ENDED
        session_id = self.active_session.session_id
        self.active_session = None
        return session_id

    def is_active(self) -> bool:
        return self.active_session is not None

    def add_user_message(self, text: str) -> None:
        if self.active_session is not None and text:
            self.active_session.messages.append(ConversationMessage(role="user", text=text))

    def add_assistant_message(self, text: str) -> None:
        if self.active_session is not None and text:
            self.active_session.messages.append(ConversationMessage(role="assistant", text=text))

    def messages(self) -> list[ConversationMessage]:
        if self.active_session is None:
            return []
        return list(self.active_session.messages)

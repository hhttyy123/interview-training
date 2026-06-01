from enum import Enum
from typing import Any


class ClientEvent(str, Enum):
    START = "session.start"
    STOP = "session.stop"
    AUDIO_BEGIN = "audio.begin"
    AUDIO_END = "audio.end"


def parse_client_event(payload: dict[str, Any]) -> ClientEvent | None:
    try:
        return ClientEvent(payload.get("type"))
    except ValueError:
        return None

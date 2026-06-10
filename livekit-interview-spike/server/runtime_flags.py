from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FLAGS_PATH = ROOT / ".runtime-flags.json"


def env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def pro_followup_rag_enabled() -> bool:
    flags = _read_flags()
    value = flags.get("proFollowupRagEnabled")
    if isinstance(value, bool):
        return value
    return env_bool("PRO_FOLLOWUP_RAG_ENABLED", True)


def set_pro_followup_rag_enabled(enabled: bool) -> dict[str, Any]:
    flags = _read_flags()
    flags["proFollowupRagEnabled"] = enabled
    RUNTIME_FLAGS_PATH.write_text(json.dumps(flags, ensure_ascii=False, indent=2), encoding="utf-8")
    return flags


def _read_flags() -> dict[str, Any]:
    if not RUNTIME_FLAGS_PATH.exists():
        return {}
    try:
        payload = json.loads(RUNTIME_FLAGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}

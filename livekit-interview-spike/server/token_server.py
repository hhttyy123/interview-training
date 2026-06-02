import os
import time
import logging
from datetime import timedelta
from importlib.util import find_spec
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from pydantic import BaseModel

from interview.configs import TRAINING_OPTIONS
from local_providers import synthesize_edge_tts


load_dotenv(Path(__file__).resolve().parents[1] / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("interview_spike.token")

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
AGENT_NAME = os.getenv("LIVEKIT_AGENT_NAME", "interview-coach")
ROOM_NAME = os.getenv("LIVEKIT_ROOM", "interview-spike-room")
TOKEN_TTL_SECONDS = int(os.getenv("LIVEKIT_TOKEN_TTL_SECONDS", "3600"))
TTS_MAX_TEXT_CHARS = int(os.getenv("TTS_MAX_TEXT_CHARS", "900"))

app = FastAPI(title="LiveKit Interview Spike Token Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class TokenRequest(BaseModel):
    room: str = ROOM_NAME
    name: str = "candidate"


class TtsRequest(BaseModel):
    text: str
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+18%"


def normalize_identity_name(raw_name: str) -> str:
    candidate = raw_name.strip()[:40] or "candidate"
    safe = "".join(ch for ch in candidate if ch.isalnum() or ch in ("-", "_"))
    return safe or "candidate"


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "livekit-interview-spike-token-server",
        "status": "ok",
        "health": "/health",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "livekitUrl": LIVEKIT_URL,
        "room": ROOM_NAME,
        "deepseekConfigured": bool(os.getenv("DEEPSEEK_API_KEY", "")),
        "deepseekModel": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        "edgeTtsInstalled": find_spec("edge_tts") is not None,
    }


@app.get("/training-options")
async def training_options() -> dict[str, object]:
    return TRAINING_OPTIONS


@app.post("/token")
async def create_token(request: TokenRequest) -> dict[str, str]:
    if not LIVEKIT_URL or not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=500, detail="LiveKit credentials are missing in .env")
    if request.room != ROOM_NAME:
        raise HTTPException(status_code=400, detail="Only the configured interview room can be joined")

    name = normalize_identity_name(request.name)
    identity = f"{name}-{int(time.time())}"
    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(name)
        .with_ttl(timedelta(seconds=TOKEN_TTL_SECONDS))
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=ROOM_NAME,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .to_jwt()
    )
    logger.info("issued token room=%s identity=%s livekit_url=%s", ROOM_NAME, identity, LIVEKIT_URL)
    return {
        "url": LIVEKIT_URL,
        "token": token,
        "room": ROOM_NAME,
        "identity": identity,
        "agentName": AGENT_NAME,
    }


@app.post("/tts")
async def create_tts(request: TtsRequest) -> Response:
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="TTS text is empty")
    if len(text) > TTS_MAX_TEXT_CHARS:
        raise HTTPException(status_code=413, detail=f"TTS text is too long, max {TTS_MAX_TEXT_CHARS} characters")

    started_at = time.perf_counter()
    audio = await synthesize_edge_tts(text, voice=request.voice, rate=request.rate)
    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info("created tts bytes=%s elapsed_ms=%s", len(audio), elapsed_ms)
    return Response(content=audio, media_type="audio/mpeg", headers={"Cache-Control": "no-store"})

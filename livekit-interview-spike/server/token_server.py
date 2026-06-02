import os
import time
import logging
from importlib.util import find_spec
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from pydantic import BaseModel

from local_providers import synthesize_edge_tts


load_dotenv(Path(__file__).resolve().parents[1] / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("interview_spike.token")

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
AGENT_NAME = os.getenv("LIVEKIT_AGENT_NAME", "interview-coach")
ROOM_NAME = os.getenv("LIVEKIT_ROOM", "interview-spike-room")

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


@app.post("/token")
async def create_token(request: TokenRequest) -> dict[str, str]:
    if not LIVEKIT_URL or not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=500, detail="LiveKit credentials are missing in .env")

    identity = f"{request.name}-{int(time.time())}"
    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(request.name)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=request.room,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .to_jwt()
    )
    logger.info("issued token room=%s identity=%s livekit_url=%s", request.room, identity, LIVEKIT_URL)
    return {
        "url": LIVEKIT_URL,
        "token": token,
        "room": request.room,
        "identity": identity,
        "agentName": AGENT_NAME,
    }


@app.post("/tts")
async def create_tts(request: TtsRequest) -> Response:
    started_at = time.perf_counter()
    audio = await synthesize_edge_tts(request.text.strip(), voice=request.voice, rate=request.rate)
    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info("created tts bytes=%s elapsed_ms=%s", len(audio), elapsed_ms)
    return Response(content=audio, media_type="audio/mpeg", headers={"Cache-Control": "no-store"})

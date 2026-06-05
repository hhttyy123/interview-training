import os
import time
import logging
from datetime import timedelta
from importlib.util import find_spec
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from pydantic import BaseModel

from interview.company_intel import build_company_card_from_source, company_card_to_payload, search_company_profiles_payload
from interview.company_research import research_company_source_text
from interview.configs import TRAINING_OPTIONS, VOICE_PROFILES, interview_options_payload, voice_profile_by_id
from interview.jd_analyzer import analyze_jd_with_llm
from interview.resume_parser import extract_pdf_text, summarize_resume_text
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
    voice: str | None = None
    voiceProfileId: str = "gentle_female_young"
    rate: str | None = None
    pitch: str | None = None
    volume: str | None = None


class CompanyCardRequest(BaseModel):
    companyName: str
    targetRole: str = "目标岗位"
    sourceText: str = ""
    sourceUrl: str = ""
    businessLine: str = ""
    useWebSearch: bool = True


class JdAnalysisRequest(BaseModel):
    roleId: str = ""
    roleLabel: str = ""
    modeId: str = "standard"
    jdText: str = ""
    companyCard: dict[str, object] | None = None


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
    search_provider = os.getenv("COMPANY_SEARCH_PROVIDER", "brave")
    return {
        "livekitUrl": LIVEKIT_URL,
        "room": ROOM_NAME,
        "deepseekConfigured": bool(os.getenv("DEEPSEEK_API_KEY", "")),
        "deepseekModel": os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        "edgeTtsInstalled": find_spec("edge_tts") is not None,
        "companySearchProvider": search_provider,
        "companySearchConfigured": bool(
            os.getenv("BRAVE_SEARCH_API_KEY", "")
            or os.getenv("SERPER_API_KEY", "")
            or os.getenv("TAVILY_API_KEY", "")
            or os.getenv("BOCHA_API_KEY", "")
        ),
    }


@app.get("/training-options")
async def training_options() -> dict[str, object]:
    return TRAINING_OPTIONS


@app.get("/interview-options")
async def interview_options() -> dict[str, object]:
    return interview_options_payload()


@app.get("/tts-options")
async def tts_options() -> dict[str, object]:
    return {
        "voiceProfiles": [
            {
                "id": profile.id,
                "label": profile.label,
                "gender": profile.gender,
                "ageStyle": profile.age_style,
                "voiceName": profile.voice_name,
                "rate": profile.rate,
                "pitch": profile.pitch,
                "volume": profile.volume,
                "tone": profile.tone,
            }
            for profile in VOICE_PROFILES
        ]
    }


@app.post("/company-card")
async def company_card(request: CompanyCardRequest) -> dict[str, object]:
    source_text = request.sourceText.strip()
    source_note = "用户提供资料"
    source_url = request.sourceUrl.strip()

    if not source_text and request.useWebSearch:
        try:
            source_text, urls = await research_company_source_text(
                company_name=request.companyName,
                target_role=request.targetRole,
            )
            if source_text:
                source_note = "全网搜索资料"
                source_url = urls[0] if urls else ""
        except Exception as error:
            logger.warning("company web research failed company=%s error=%s", request.companyName, error)

    card = await build_company_card_from_source(
        company_name=request.companyName,
        target_role=request.targetRole,
        source_text=source_text,
        business_line=request.businessLine,
        source_note=source_note,
        source_url=source_url,
    )
    return company_card_to_payload(card)


@app.post("/analyze-jd")
async def analyze_jd_endpoint(request: JdAnalysisRequest) -> dict[str, object]:
    try:
        # 如果没有预设 roleId 但有自定义岗位名，视为动态岗位
        role_id = request.roleId.strip()
        role_label = request.roleLabel.strip()
        if not role_id and role_label:
            role_id = "dynamic"
        elif not role_id:
            role_id = "product_manager"
        return await analyze_jd_with_llm(
            role_id=role_id,
            role_label=role_label,
            mode_id=request.modeId,
            jd_text=request.jdText,
            company_card=request.companyCard,
        )
    except RuntimeError as error:
        logger.warning("jd analysis failed role=%s mode=%s error=%s", request.roleLabel or request.roleId, request.modeId, error)
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)) -> dict[str, object]:
    data = await file.read()
    filename = file.filename or ""
    if filename.lower().endswith(".pdf"):
        text = extract_pdf_text(data)
    else:
        text = data.decode("utf-8", errors="ignore")
    return summarize_resume_text(text)


@app.get("/company-search")
async def company_search(q: str = "") -> dict[str, object]:
    return {"companies": search_company_profiles_payload(q)}


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
    profile = voice_profile_by_id(request.voiceProfileId)
    audio = await synthesize_edge_tts(
        text,
        voice=request.voice or profile.voice_name,
        rate=request.rate or profile.rate,
        pitch=request.pitch or profile.pitch,
        volume=request.volume or profile.volume,
    )
    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info("created tts bytes=%s elapsed_ms=%s", len(audio), elapsed_ms)
    return Response(content=audio, media_type="audio/mpeg", headers={"Cache-Control": "no-store"})

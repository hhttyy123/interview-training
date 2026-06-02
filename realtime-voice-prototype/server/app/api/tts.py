from pydantic import BaseModel, Field
from fastapi import APIRouter, Response

from app.providers.tts.edge import EdgeTextToSpeechProvider


router = APIRouter(prefix="/api")


class TtsRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1200)
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+18%"


@router.post("/tts")
async def synthesize_speech(request: TtsRequest) -> Response:
    provider = EdgeTextToSpeechProvider(voice=request.voice, rate=request.rate)
    audio = await provider.synthesize(request.text.strip())
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-store"},
    )

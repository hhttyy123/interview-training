import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.config import load_local_env
from app.api.voice_ws import router as voice_router
from app.providers.asr.funasr_streaming import preload_shared_funasr_model


load_local_env()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if os.getenv("REALTIME_VOICE_PRELOAD_ASR", "1") != "0":
        await preload_shared_funasr_model()
    yield


app = FastAPI(title="Realtime Voice Prototype", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(voice_router)

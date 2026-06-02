from fastapi import HTTPException


class EdgeTextToSpeechProvider:
    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural", rate: str = "+18%") -> None:
        self.voice = voice
        self.rate = rate

    async def synthesize(self, text: str) -> bytes:
        try:
            import edge_tts
        except ImportError as error:
            raise HTTPException(
                status_code=503,
                detail="Edge TTS is not installed. Run: python -m pip install edge-tts",
            ) from error

        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
        audio = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
        if not audio:
            raise HTTPException(status_code=502, detail="TTS provider returned empty audio.")
        return bytes(audio)

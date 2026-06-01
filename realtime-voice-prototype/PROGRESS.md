# Progress Snapshot

## What is finished

Slice `01-scaffold-local-realtime-session` is complete.

Verified previously:

- Local project scaffold exists for `web/`, `server/`, `models/`, `scripts`, and `evaluation`.
- FastAPI exposes `/health` and `/ws/voice`.
- WebSocket session flow supports `session.start`, `session.ready`, `session.stop`, `session.ended`, and `session.error`.
- Frontend page renders status, event feed, start button, and stop button.
- No audio or transcript persistence has been added.

## What is working locally

Slice `02-stream-browser-speech-to-funasr-transcript` is usable in the browser.

Working:

- Browser microphone capture via `AudioWorklet`.
- PCM downsampling to 16 kHz 16-bit audio.
- WebSocket binary audio upload to the server.
- `FunAsrStreamingProvider` buffering browser PCM into FunASR-sized chunks.
- Partial and final transcript events on the server.
- Frontend transcript panel for in-progress and confirmed text.
- Assistant text delta/done events and frontend AI reply display.
- `DeepSeekStreamingTextProvider` for real streaming text replies.

## Current development

Automatic turn completion has been implemented in code and still needs hands-on browser validation.

Implemented:

- Starting a session now opens the microphone and keeps it active until the session ends.
- The manual per-turn button is now a fallback `I'm done` action, with `Enter` as a shortcut.
- Backend turn control combines lightweight voice activity detection, ASR transcript stability, rule-based completion checks, and a DeepSeek-backed completion judge for ambiguous pauses.
- Uncertain or incomplete turns enter a dynamic wait state and show a final-window UI hint before the backend automatically ends the turn.
- If the user starts speaking while an assistant text reply is streaming, the backend cancels the current assistant generation and returns to listening.

Needs verification:

- Real noisy-room behavior of the lightweight voice activity detector.
- Whether the DeepSeek completion judge returns valid JSON consistently in the configured account/model.
- Whether the default wait windows feel natural during interview-style answers.

## Current behavior

- FunASR model files are cached under the local ModelScope cache after the first download.
- The server preloads the shared FunASR model during startup by default.
- Startup may still be slow because the Python process loads the cached model weights into memory.
- Running with `--reload` restarts the Python process after code changes, so the model is loaded again.

## Standard commands

Install or refresh dependencies:

```powershell
cd server
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python scripts\check_asr_environment.py
```

Start the server for interactive testing:

```powershell
cd server
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

Start the server with DeepSeek text replies and turn-completion judging:

```powershell
cd server
$env:DEEPSEEK_API_KEY='<your-deepseek-api-key>'
$env:DEEPSEEK_MODEL='deepseek-v4-flash'
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

Alternatively, create `server/.env` from `server/.env.example`. The server loads it automatically and `.gitignore` excludes it.

Start the web app:

```powershell
cd web
npm run dev
```

## Manual acceptance path

1. Start the server.
2. Start the web app.
3. Open the browser page.
4. Start a session.
5. Confirm the browser requests microphone permission and then stays in listening mode.
6. Speak one short Chinese sentence and stop naturally.
7. Confirm partial transcripts appear while speaking.
8. Confirm the backend either waits for more speech or automatically finalizes the turn.
9. Confirm an AI text reply streams after the final transcript.
10. While the AI text reply is streaming, start speaking again and confirm the reply is cancelled.
11. Use `I'm done` or `Enter` once as a fallback and confirm it immediately finalizes the current turn.

## Next step

Verify automatic turn completion end-to-end, tune VAD/wait windows, then continue to streaming TTS.

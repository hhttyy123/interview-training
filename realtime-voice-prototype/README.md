# Realtime Voice Prototype

Local V0 workspace for a browser-based real-time voice conversation experience.

## Current slice

Implemented and verified:

- A browser page with start and end controls.
- A FastAPI WebSocket endpoint for transient session events.
- Visible connection state and event activity.
- No persisted audio or transcript data.

Implemented in code, not yet verified end-to-end:

- Browser microphone capture streamed as 16 kHz PCM.
- `FunASR Paraformer-zh-streaming` incremental and final transcript display.
- Deterministic streaming AI text replies after each final user transcript.

## Prerequisites

- Node.js 20+
- Python 3.11

## Run locally

Install and start the server:

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python scripts\check_asr_environment.py
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

To use DeepSeek for streaming text replies, set the API key in the terminal before starting the server:

```powershell
cd server
$env:DEEPSEEK_API_KEY='<your-deepseek-api-key>'
$env:DEEPSEEK_MODEL='deepseek-v4-flash'
.\.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

Or create `server/.env` from `server/.env.example`; the server loads it automatically on startup. Do not commit `server/.env`.

In a second terminal, install and start the web app:

```powershell
cd web
npm install
npm run dev
```

Open the Vite URL shown in the terminal, usually `http://localhost:5173`. The web app connects to `ws://localhost:8000/ws/voice`.

## Current status

What we know is working:

- Server tests for health and WebSocket session lifecycle passed.
- Web state-store test passed.
- TypeScript compile and Vite production build passed.

What still needs verification:

- Installing `funasr`, `modelscope`, `numpy`, `torch`, and `torchaudio` into `server/.venv`.
- Passing `scripts/check_asr_environment.py`.
- Loading the `paraformer-zh-streaming` model successfully.
- Real browser microphone capture flowing through to visible partial and final transcripts.

If you are resuming work from here, the next command to revisit is:

```powershell
cd server
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python scripts\check_asr_environment.py
```

## Session protocol

| Direction | Event | Purpose |
| --- | --- | --- |
| Web -> Server | `session.start` | Begin an in-memory session |
| Web -> Server | `session.stop` | End and clear the session |
| Server -> Web | `session.ready` | Confirm session is ready |
| Server -> Web | `session.ended` | Confirm session was cleared |
| Server -> Web | `session.error` | Report invalid or failed interaction |

| Web -> Server | `audio.begin` | Start microphone input for one utterance |
| Web -> Server | binary PCM chunks | Stream 16 kHz microphone input |
| Web -> Server | `audio.end` | Flush the final transcript for the utterance |
| Server -> Web | `transcript.partial` | Show in-progress user speech recognition |
| Server -> Web | `transcript.final` | Confirm the completed user utterance |
| Server -> Web | `assistant.text.delta` | Stream one AI text reply chunk |
| Server -> Web | `assistant.text.done` | Confirm the completed AI text reply |

## Text reply provider

The first real text provider is DeepSeek's OpenAI-compatible chat completions endpoint. Runtime configuration:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | unset | Enables real DeepSeek replies when present |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | Model name sent to DeepSeek |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | API base URL |

## FunASR model

The server preloads `paraformer-zh-streaming` during startup so the first microphone turn does not pay the model-load cost. Startup can still take a while because the process loads the cached model weights into memory. Set `REALTIME_VOICE_PRELOAD_ASR=0` before starting the server if you want to skip startup preload and load lazily on first speech.

The stream uses the FunASR reference chunk profile of approximately 600 ms at 16 kHz. During interactive testing, prefer running the server without `--reload`; hot reload restarts the Python process and reloads the ASR model.

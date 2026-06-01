# Realtime Voice Technical Debt

Status: `active`
Last updated: 2026-06-01

## Context

The current V0 is moving from button-driven recording to a more natural realtime interview room:

```text
Start session
-> keep microphone active
-> detect user speech and pauses
-> judge whether the turn is complete
-> wait when the user may still be thinking
-> automatically finalize the turn
-> stream the assistant reply
-> cancel the assistant reply if the user starts speaking again
```

This document records technical debt found during the automatic turn-completion implementation and the remediation status.

## Fixed In Current Patch

### Turn timing was driven by incoming audio

Risk:

The backend previously checked `TurnController.next_action()` only after receiving an audio chunk. If the user stopped speaking and no more chunks arrived, waiting windows, final hints, and automatic turn ending could stall indefinitely.

Fix:

- Added a backend turn monitor task that wakes periodically while the session is active.
- Audio handling now updates voice/transcript state.
- The monitor owns time-based progression: wait, hint, and automatic finalization.
- Added controller revision tracking so stale LLM judge results are ignored when the user starts speaking or the transcript changes during a judge call.

Files:

- `realtime-voice-prototype/server/app/api/voice_ws.py`
- `realtime-voice-prototype/server/app/session/turn_controller.py`
- `realtime-voice-prototype/server/tests/test_turn_controller.py`

### WebSocket accepted browser origins without checking

Risk:

`CORSMiddleware` does not protect WebSocket handshakes. A random browser page could try to connect to the local voice service and consume local ASR/LLM resources.

Fix:

- Added an explicit WebSocket origin allowlist for the Vite dev origins:
  `http://localhost:5173` and `http://127.0.0.1:5173`.
- Non-browser clients without an `Origin` header are still allowed for local scripts/tests.

File:

- `realtime-voice-prototype/server/app/api/voice_ws.py`

### Malformed WebSocket JSON could break the session handler

Risk:

Bad text payloads could raise `JSONDecodeError` and terminate the socket handler instead of producing a controlled error response.

Fix:

- Malformed JSON now returns `session.error`.
- Non-object JSON now returns `session.error`.
- Added a protocol test for malformed JSON.

Files:

- `realtime-voice-prototype/server/app/api/voice_ws.py`
- `realtime-voice-prototype/server/tests/test_protocol.py`

### Enter shortcut could be registered repeatedly

Risk:

The frontend `Enter` shortcut for `I'm done` was registered on `document` inside `render()`. Re-rendering/remounting could leave multiple handlers attached.

Fix:

- Store the active keydown handler at class level.
- Remove the previous handler before registering a new one.

File:

- `realtime-voice-prototype/web/src/ui/controls.ts`

## Remaining Technical Debt

### Lightweight VAD is still heuristic

Risk:

`VoiceActivityDetector` uses RMS thresholding with a simple adaptive noise floor. It can still misclassify keyboard noise, fan noise, quiet speech, or far-field microphone input.

Recommended next step:

- Record measured behavior in quiet, noisy, and mixed environments.
- Consider a real VAD model or WebRTC VAD if the heuristic causes frequent false positives/false negatives.

### Turn-completion judge depends on provider JSON behavior

Risk:

The DeepSeek completion judge asks for JSON output, but provider behavior should be validated with the actual account/model. Invalid JSON currently falls back to rule-based behavior, which is safe but may reduce intelligence.

Recommended next step:

- Add logging for judge fallback reasons.
- Track completion, confidence, suggested wait, and final controller action during manual evaluation.

### Frontend status language is mixed and not yet product-quality Chinese

Risk:

Recent frontend copy uses English for the new realtime-room flow, while older UI copy still contains Chinese mojibake in some components. This affects trust and manual testing clarity.

Recommended next step:

- Normalize UI copy after the realtime behavior is validated.
- Keep privacy and listening states especially clear.

### No automated end-to-end browser audio test

Risk:

Unit tests cover controller and event behavior, but the full browser microphone -> WebSocket -> ASR -> turn monitor -> assistant cancellation flow still needs manual validation.

Recommended next step:

- Keep the manual acceptance checklist in `realtime-voice-prototype/PROGRESS.md` current.
- Add an injectable fake ASR provider before attempting browser automation.

## Verification Commands

Per the project development habit, these are provided for manual execution.

Backend:

```powershell
cd D:\面试训练\realtime-voice-prototype\server
.\.venv\Scripts\python -m pytest
```

Frontend:

```powershell
cd D:\面试训练\realtime-voice-prototype\web
npm test
npm exec -- tsc
npm exec -- vite build
```

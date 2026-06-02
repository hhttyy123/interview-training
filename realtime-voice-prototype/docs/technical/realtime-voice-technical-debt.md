# Realtime Voice Technical Debt

Status: active
Date: 2026-06-01

## Context

The realtime voice prototype is moving toward a hands-free interview flow: the user starts a session once, speaks naturally, pauses when thinking, and the system decides whether to wait, show a final-countdown hint, or continue the interview. The implementation should avoid forcing the user to click "end turn" after every answer.

## Fixed In This Pass

### Turn timing was coupled to incoming audio

Risk: the previous turn-completion check only ran while audio frames were arriving. If the browser stopped sending frames during silence, the backend might never reach the final wait window or hint state.

Fix: added a backend turn monitor task that evaluates the turn controller every 250 ms while the session is active. Audio handling now only updates voice/transcript state; the monitor owns waiting, hint, and auto-finalization.

### Stale LLM judge results could finalize a newer turn

Risk: if the completion judge was still running while the user started speaking again, its old result could end the turn after the conversation state had already changed.

Fix: added a revision counter to the turn controller. Speech, transcript changes, and turn resets advance the revision; judge results are ignored if the revision changed during the request.

### WebSocket accepted any browser origin

Risk: another local web page could attempt to connect to the voice WebSocket from a browser.

Fix: added a local development origin allowlist for `http://localhost:5173` and `http://127.0.0.1:5173`. Non-browser test clients without an `Origin` header are still allowed.

### Malformed WebSocket JSON could break the session loop

Risk: invalid client text frames could raise during JSON parsing instead of returning a protocol-level error.

Fix: malformed JSON and non-object payloads now return `session.error`.

### Frontend Enter shortcut could be registered repeatedly

Risk: if controls are re-rendered, multiple `keydown` listeners could stack up and trigger duplicate actions.

Fix: the controls renderer now removes the previous static keydown handler before registering a new one.

### Assistant interruption was too sensitive in noisy rooms

Risk: after the user manually ended a turn, background speech could be treated as a fresh user interruption while the assistant was starting its reply. That cancelled the assistant stream and made the session feel stuck in listening mode.

Fix: added a short manual-end lock window and a stricter assistant barge-in gate. During assistant replies, interruption now requires sustained strong voice above the current noise floor. Candidate interruption audio is buffered and forwarded only after the interruption is confirmed.

### Turn completion felt inconsistent and hard to debug

Risk: when the system waited too long or ended quickly, there was no compact record showing whether the delay came from VAD, transcript stability, the LLM judge, or the wait policy.

Fix: turn decisions now include structured backend traces. The wait policy also shortens ambiguous waits for longer answers instead of blindly applying the default uncertain window.

### Background speech could still extend the user's turn

Risk: a nearby voice could pass the basic VAD gate, refresh the user's last-voice timestamp, and delay turn completion even when the candidate had stopped.

Fix: regular answer capture now uses a stricter near-voice check before refreshing the turn timer or sending audio to ASR. The basic VAD signal is still retained for noise-floor tracking.

## Remaining Debt

### Voice activity detection is still lightweight

Current behavior uses a simple audio-energy heuristic. It is useful for a local prototype, but noisy rooms may still produce false positives or false negatives.

Suggested next step: keep the current heuristic as a baseline, then add adaptive noise-floor calibration and a small VAD state machine before considering a heavier model.

### Turn-completion judge depends on JSON discipline from the LLM

The DeepSeek judge has fallback parsing, but malformed or vague responses still reduce confidence.

Suggested next step: add structured-output hardening and more tests around incomplete, uncertain, and interrupted answers.

### Browser audio flow lacks an end-to-end test

Unit tests cover the turn controller and protocol pieces, but not a full browser microphone session with ASR and streaming assistant cancellation.

Suggested next step: add a manual smoke checklist first, then automate only the stable parts once the local audio pipeline stops changing quickly.

### User-facing text still needs one localization pass

Some backend fallback messages are English to keep encoding safe. The UI also mixes prototype wording and production-facing wording.

Suggested next step: centralize user-facing strings and decide whether V0 should be fully Chinese, bilingual, or intentionally developer-facing.

## Manual Verification

Backend:

```powershell
cd .\server
.\.venv\Scripts\python -m pytest
```

Frontend:

```powershell
cd .\web
npm test
npm exec -- tsc
npm exec -- vite build
```

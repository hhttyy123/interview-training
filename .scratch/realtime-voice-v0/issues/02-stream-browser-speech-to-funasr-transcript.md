# 在网页中实时显示 FunASR 转写

Status: `in-progress`
Type: `AFK`

## What to build

在本地会话页面中开启麦克风，将用户音频流发送到后端并接入 `FunASR Paraformer-zh-streaming`，让用户在讲话过程中看到增量转写，并在一轮讲话结束后看到确认文本。

## Acceptance criteria

- [ ] 用户授权麦克风后，页面能够开始和停止音频采集。
- [ ] 用户音频以适配 `FunASR Paraformer-zh-streaming` 的格式传递并实时识别。
- [ ] 页面区分识别中的增量转写与已确认的一轮文本。
- [ ] 用户停止讲话后，可形成最终转写结果。
- [ ] 可以观察或记录“开口到首次显示识别文本”的延迟。
- [ ] 音频与转写仅用于当前页面会话，不持久化保存。

## Blocked by

- `01-scaffold-local-realtime-session.md`

## Progress notes

- Browser microphone capture, PCM downsampling, WebSocket audio upload, and transcript UI have been coded.
- Server-side `FunAsrStreamingProvider` and transcript events have been coded.
- End-to-end verification is still pending because `funasr`, `modelscope`, and `numpy` are not yet installed in `server/.venv`.
- Resume from `.\.venv\Scripts\python -m pip install -e ".[dev,asr]"`, then run the browser flow.

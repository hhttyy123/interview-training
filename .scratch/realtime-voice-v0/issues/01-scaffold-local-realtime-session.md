# 搭建本地实时会话骨架

Status: `completed`
Type: `AFK`

## What to build

创建 `realtime-voice-prototype` 本地原型工程，让电脑浏览器能够打开对话页面、连接本地后端实时通道，并通过开始与结束操作看到明确的会话状态变化。本切片不接入语音模型，也不保存任何对话数据。

## Acceptance criteria

- [x] 前端网页和本地后端均可通过明确命令启动。
- [x] 页面提供开始与结束操作，并展示未连接、已连接、已结束和异常状态。
- [x] 浏览器与后端通过实时会话通道完成 `session.start`、`session.ready`、`session.stop` 和 `session.error` 事件交互。
- [x] 原型工程包含后续接入音频、模型服务和体验评估的基础目录与使用说明。
- [x] 当前实现不保存音频或转写内容。

## Blocked by

None - can start immediately.

## Verification

- `server/.venv/Scripts/python.exe -m pytest`: 2 passed.
- `npm test`: 1 passed.
- `npm exec -- tsc`: passed.
- `npm exec -- vite build`: passed.

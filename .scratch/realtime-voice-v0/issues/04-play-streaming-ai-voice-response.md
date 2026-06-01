# 播放 AI 流式语音回答

Status: `ready-for-human`
Type: `HITL`

## What to build

在已有实时识别和文字回复基础上接入流式 `TTS`，使 AI 的回复能够尽快以语音在网页中播出。用户需要选择或批准首轮 `TTS` 方案，以低首包延迟为优先。

## Acceptance criteria

- [ ] 明确并记录首轮流式 `TTS` 实现：本地运行方案或国内云端服务。
- [ ] `TTS` 通过独立适配器接入，后续可替换而无需修改会话控制。
- [ ] AI 回复文本能够转为连续音频并在浏览器播放。
- [ ] 多轮对话播放顺序正确，不重叠、不遗留上一轮音频。
- [ ] 页面仍可同步看到 AI 的临时文字回复。
- [ ] 可以测量用户说完到听见 AI 首段声音的延迟。

## Blocked by

- `03-add-controlled-streaming-text-response.md`

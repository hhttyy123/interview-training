# AI 面试训练实时语音版

这是当前项目的实时语音主线版本。它用 LiveKit 负责音频房间，用本地 FunASR 做转写，用 DeepSeek 生成面试追问，用 Edge TTS 播放 AI 语音。

当前目标不是做通用聊天机器人，而是验证“公司岗位级 AI 面试训练教练”的核心体验：候选人自然说话，系统自动判断一轮回答是否结束，AI 以面试官方式继续追问，并在调试台保留可观察日志。

## 当前能力

- 本地 LiveKit 房间：浏览器进入同一个语音房间，麦克风音频交给本地 agent。
- 本地 ASR：FunASR 流式识别候选人回答。
- 自动轮次判断：结合音量门控、转写稳定时间、规则式结束判断和手动兜底按钮。
- LLM 面试官：DeepSeek 根据对话历史生成下一句中文追问。
- TTS 播放：前端请求 token server 的 `/tts`，用 Edge TTS 生成并播放 AI 语音。
- 双界面：主界面像语音通话，只保留 AI 动态球和用户音浪；调试台展示转写、AI 文本、事件日志和服务状态。

## 技术结构

```text
livekit-interview-spike/
  bin/                    # 本地 LiveKit server，可本机运行
  docs/                   # 项目技术债和后续规划
  scripts/start-dev.ps1   # Windows 本地四服务启动脚本
  server/
    agent.py              # LiveKit agent，处理音频、转写、轮次和 LLM
    local_providers.py    # FunASR、DeepSeek、Edge TTS provider
    token_server.py       # token、health、tts HTTP 服务
    turn_completion.py    # 回答结束判断
    turn_controller.py    # 轮次状态机
  web/
    src/main.tsx          # React 前端
    src/styles.css        # 主通话界面和调试台样式
```

## 环境准备

项目需要 Python 3.11、Node.js 20+、本地 LiveKit server，以及 DeepSeek API Key。

复制环境变量：

```powershell
cd D:\面试训练\livekit-interview-spike
Copy-Item .env.example .env
```

本地开发默认 LiveKit 配置：

```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
LIVEKIT_ROOM=interview-spike-room
```

还需要在 `.env` 里配置：

```env
DEEPSEEK_API_KEY=你的 DeepSeek Key
```

## 启动方式

一键启动四个窗口：

```powershell
cd D:\面试训练\livekit-interview-spike
.\scripts\start-dev.ps1
```

也可以手动分四步启动：

```powershell
cd D:\面试训练\livekit-interview-spike
.\bin\livekit-server.exe --dev --bind 0.0.0.0
```

```powershell
cd D:\面试训练\livekit-interview-spike\server
.\.venv\Scripts\python -m uvicorn token_server:app --host 127.0.0.1 --port 8787
```

```powershell
cd D:\面试训练\livekit-interview-spike\server
.\.venv\Scripts\python agent.py
```

```powershell
cd D:\面试训练\livekit-interview-spike\web
npm run dev
```

打开 Vite 显示的地址，通常是 `http://localhost:5173`。

## 判断是否正常

- LiveKit server 看到 `starting LiveKit server`。
- Agent 看到 `agent connected`，并且有人进入房间后看到 `track subscribed`。
- Token server 的 `http://127.0.0.1:8787/health` 返回 JSON。
- 前端首页服务状态为可用，进入房间后点“开始”能听到 AI 开场。
- 调试台能看到 `transcript.partial`、`transcript.final`、`assistant.text.done` 和 TTS 耗时日志。

## 边界

- 现在还没有接入主项目的岗位/JD/简历/RAG/评分闭环。
- TTS 目前是前端本地播放，不是作为 LiveKit audio track 发布到房间。
- 回答结束判断仍是启发式逻辑，适合继续打磨，但还不是最终工业级方案。
- 本地 `devkey/secret` 只能用于开发，不适合公网部署。

后续优化见 [技术债文档](docs/technical-debt.md)。

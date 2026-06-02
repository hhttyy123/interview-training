# LiveKit Interview Spike

独立 LiveKit 测试项目，不依赖也不修改 `realtime-voice-prototype`。

目标是快速验证：

- 浏览器进入一个 LiveKit 语音面试房间。
- AI 面试官用语音提问。
- 用户持续语音回答。
- LiveKit Agents 负责 STT -> LLM -> TTS 管线、VAD、turn detection 和打断。
- 当前只做语音面试体验 spike，不做简历/JD/评分/持久化。

## 当前技术组合

- LiveKit 本地：音频房间与浏览器麦克风连接。
- FunASR 本地：用户语音转写。
- DeepSeek API：AI 面试官追问。
- Edge TTS：AI 文字回复转语音。

这个版本不使用 OpenAI Realtime，也不使用 LiveKit Inference、Deepgram、Cartesia。

## 你需要准备

- 本地 LiveKit server。Windows 没有 Docker 也可以直接用 `livekit-server.exe`。
- Python 3.11+。
- Node.js 20+。
- DeepSeek API Key。

如果暂时没有 DeepSeek Key，也能启动，但 AI 会提示你缺少 `DEEPSEEK_API_KEY`。

## 启动步骤

复制环境变量：

```powershell
cd D:\面试训练\livekit-interview-spike
Copy-Item .env.example .env
```

编辑 `.env`，填入真实 LiveKit 配置。

本地 LiveKit 默认可以先保持：

```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

同时填入：

```env
DEEPSEEK_API_KEY=你的 DeepSeek Key
```

### 启动本地 LiveKit server

推荐 Windows 方式：下载 `livekit-server.exe` 后直接运行。

1. 打开 LiveKit releases：

```text
https://github.com/livekit/livekit/releases
```

2. 下载 Windows amd64 版本，解压后把 `livekit-server.exe` 放到：

```text
D:\面试训练\livekit-interview-spike\bin\livekit-server.exe
```

3. 启动本地 LiveKit：

```powershell
cd D:\面试训练\livekit-interview-spike
.\bin\livekit-server.exe --dev --bind 0.0.0.0
```

看到类似 `listening on :7880` 后，再启动 token server 和 agent。

如果你有可用 Docker，也可以用：

```powershell
cd D:\面试训练\livekit-interview-spike
docker compose up
```

如果 Docker 拉镜像失败，优先使用上面的 `livekit-server.exe` 方式。

安装 Python 依赖：

```powershell
cd D:\面试训练\livekit-interview-spike\server
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m livekit.agents download-files
```

启动 token server：

```powershell
cd D:\面试训练\livekit-interview-spike\server
.\.venv\Scripts\python -m uvicorn token_server:app --host 127.0.0.1 --port 8787
```

再开一个终端，启动本地 AI Agent：

```powershell
cd D:\面试训练\livekit-interview-spike\server
.\.venv\Scripts\python agent.py
```

再开一个终端，启动前端：

```powershell
cd D:\面试训练\livekit-interview-spike\web
npm install
npm run dev
```

打开 Vite 显示的地址，通常是：

```text
http://localhost:5173
```

如果你已经安装过依赖，也可以用一键启动脚本分别拉起 4 个窗口：

```powershell
cd D:\面试训练\livekit-interview-spike
.\scripts\start-dev.ps1
```

## 预期体验

- 点击“进入面试室”后，浏览器请求本地 token server。
- 前端连接本地 LiveKit 房间并打开麦克风。
- 本地 Agent 主动加入固定房间 `interview-spike-room`，订阅用户音频，用 FunASR 做转写。
- Agent 用 DeepSeek 生成面试官追问。
- Agent 通过 LiveKit data channel 把转写和 AI 文本发给前端。
- 前端请求本地 token server 的 `/tts`，用 Edge TTS 播放 AI 语音。

## 当前边界

- 这是 LiveKit spike，不是正式产品代码。
- 当前没有使用 LiveKit Inference。
- 面试官 prompt 已按“公司岗位级 AI 求职训练教练”方向写入。
- 没有接入当前项目的能力图谱、JD、简历、结构化反馈。
- 后续如果体验 OK，再把业务层抽成 `Interview Orchestrator` 接进去。
- AI 语音目前由浏览器本地播放，不是以 LiveKit audio track 发布给房间。
- 当前 turn detection 是 spike 级静音阈值，后续还需要接入更稳的 VAD/turn controller。

## 验收重点

- 停止说话后，AI 是否比旧链路更快接话。
- AI 说话时插话，是否能更自然中断。
- 尾字转写是否比旧链路稳定。
- 语音播放是否仍有明显卡顿。
- 浏览器麦克风状态是否比旧链路更稳定。

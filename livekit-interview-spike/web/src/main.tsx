import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BarVisualizer,
  ControlBar,
  LiveKitRoom,
  RoomAudioRenderer,
  useRoomContext,
  useVoiceAssistant,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { RoomEvent } from "livekit-client";
import "./styles.css";

const API_BASE = "http://127.0.0.1:8787";
const DEFAULT_ROOM = "interview-spike-room";

interface TokenPayload {
  url: string;
  token: string;
  room: string;
  identity: string;
  agentName: string;
}

interface HealthPayload {
  livekitUrl: string;
  room: string;
  deepseekConfigured: boolean;
  deepseekModel: string;
  edgeTtsInstalled: boolean;
}

interface TrainingConfig {
  jobId: string;
  modeId: string;
  competencyId: string;
  strategyId: string;
}

interface TrainingOptions {
  jobs: Array<{ id: string; label: string }>;
  modes: Array<{ id: string; label: string }>;
  competencies: Array<{ id: string; label: string }>;
  strategies: Array<{ id: string; label: string }>;
}

interface ConversationEntry {
  role: "candidate" | "assistant";
  text: string;
  time: string;
}

interface InterviewReport {
  summary?: string;
  dimensions?: Array<{
    id: string;
    name: string;
    score: number;
    reason: string;
    evidence: string;
    improvement: string;
  }>;
  main_weakness?: string;
  training_plan?: {
    theme?: string;
    goal?: string;
    exercise?: string;
    method?: string;
    duration_minutes?: number;
  };
}

type SessionPhase = "idle" | "listening" | "thinking" | "speaking" | "ended";

const DEFAULT_TRAINING_CONFIG: TrainingConfig = {
  jobId: "product_manager",
  modeId: "standard",
  competencyId: "requirement_analysis",
  strategyId: "evidence_probe",
};

const FALLBACK_TRAINING_OPTIONS: TrainingOptions = {
  jobs: [{ id: "product_manager", label: "产品经理" }],
  modes: [
    { id: "standard", label: "标准训练" },
    { id: "guided", label: "引导训练" },
    { id: "challenge", label: "压力追问" },
  ],
  competencies: [
    { id: "requirement_analysis", label: "需求分析" },
    { id: "project_delivery", label: "项目推进" },
    { id: "impact_expression", label: "结果表达" },
  ],
  strategies: [
    { id: "clarification_probe", label: "澄清追问" },
    { id: "evidence_probe", label: "证据追问" },
    { id: "result_probe", label: "结果追问" },
    { id: "reflection_probe", label: "复盘追问" },
  ],
};

function App() {
  const [session, setSession] = useState<TokenPayload | null>(null);
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [healthError, setHealthError] = useState("");
  const [trainingOptions, setTrainingOptions] = useState<TrainingOptions>(FALLBACK_TRAINING_OPTIONS);
  const [trainingConfig, setTrainingConfig] = useState<TrainingConfig>(DEFAULT_TRAINING_CONFIG);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function refreshHealth(): Promise<HealthPayload | null> {
    try {
      const response = await fetch(`${API_BASE}/health`, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as HealthPayload;
      setHealth(payload);
      setHealthError("");
      return payload;
    } catch (cause) {
      setHealth(null);
      setHealthError(cause instanceof Error ? cause.message : "无法连接 token server");
      return null;
    }
  }

  async function refreshTrainingOptions() {
    try {
      const response = await fetch(`${API_BASE}/training-options`, { cache: "no-store" });
      if (response.ok) setTrainingOptions((await response.json()) as TrainingOptions);
    } catch {
      setTrainingOptions(FALLBACK_TRAINING_OPTIONS);
    }
  }

  useEffect(() => {
    void refreshHealth();
    void refreshTrainingOptions();
    const timer = window.setInterval(() => void refreshHealth(), 3000);
    return () => window.clearInterval(timer);
  }, []);

  async function joinRoom() {
    setLoading(true);
    setError("");
    await refreshHealth();
    try {
      const response = await fetch(`${API_BASE}/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ room: DEFAULT_ROOM, name: "candidate" }),
      });
      if (!response.ok) throw new Error(await response.text());
      setSession((await response.json()) as TokenPayload);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "无法进入面试室");
    } finally {
      setLoading(false);
    }
  }

  if (!session) {
    return (
      <main className="landing">
        <section className="hero-card">
          <p className="eyebrow">AI INTERVIEW CALL</p>
          <h1>实时语音面试室</h1>
          <p className="intro">
            选择训练条件后进入语音面试。主界面保持安静，调试台保留转写、评分报告和训练建议。
          </p>
          <TrainingDock
            config={trainingConfig}
            options={trainingOptions}
            disabled={loading}
            onChange={setTrainingConfig}
          />
          <HealthPanel health={health} healthError={healthError} />
          <button type="button" onClick={joinRoom} disabled={loading}>
            {loading ? "正在进入..." : "进入面试室"}
          </button>
          {error && <p className="error">{error}</p>}
        </section>
      </main>
    );
  }

  return (
    <LiveKitRoom
      serverUrl={session.url}
      token={session.token}
      connect
      audio={false}
      video={false}
      onDisconnected={() => setSession(null)}
      className="room"
    >
      <InterviewRoom
        room={session.room}
        health={health}
        healthError={healthError}
        trainingConfig={trainingConfig}
        trainingOptions={trainingOptions}
        onTrainingConfigChange={setTrainingConfig}
      />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}

function TrainingDock({
  config,
  options,
  disabled,
  onChange,
}: {
  config: TrainingConfig;
  options: TrainingOptions;
  disabled: boolean;
  onChange: (config: TrainingConfig) => void;
}) {
  function update(key: keyof TrainingConfig, value: string) {
    onChange({ ...config, [key]: value });
  }

  return (
    <section className="training-dock" aria-label="训练条件">
      <SelectField label="岗位" value={config.jobId} options={options.jobs} disabled={disabled} onChange={(value) => update("jobId", value)} />
      <SelectField label="模式" value={config.modeId} options={options.modes} disabled={disabled} onChange={(value) => update("modeId", value)} />
      <SelectField
        label="能力"
        value={config.competencyId}
        options={options.competencies}
        disabled={disabled}
        onChange={(value) => update("competencyId", value)}
      />
      <SelectField
        label="追问"
        value={config.strategyId}
        options={options.strategies}
        disabled={disabled}
        onChange={(value) => update("strategyId", value)}
      />
    </section>
  );
}

function SelectField({
  label,
  value,
  options,
  disabled,
  onChange,
}: {
  label: string;
  value: string;
  options: Array<{ id: string; label: string }>;
  disabled: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <label className="config-field">
      <span>{label}</span>
      <select value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function HealthPanel({ health, healthError }: { health: HealthPayload | null; healthError: string }) {
  return (
    <div className="health-panel">
      <div>
        <span className="health-dot" data-ok={Boolean(health)} />
        <strong>Token 服务</strong>
        <p>{health ? "可访问" : `未检测到：${healthError || "请启动 token_server.py"}`}</p>
      </div>
      <div>
        <span className="health-dot" data-ok={Boolean(health?.deepseekConfigured)} />
        <strong>DeepSeek 配置</strong>
        <p>{health?.deepseekConfigured ? `已读取 Key，模型：${health.deepseekModel}` : "未读取到 DEEPSEEK_API_KEY"}</p>
      </div>
      <div>
        <span className="health-dot" data-ok={Boolean(health?.edgeTtsInstalled)} />
        <strong>Edge TTS 依赖</strong>
        <p>{health?.edgeTtsInstalled ? "已安装 edge-tts" : "未检测到 edge-tts"}</p>
      </div>
      <div>
        <strong>LiveKit 房间</strong>
        <p>{health?.room || DEFAULT_ROOM}</p>
      </div>
    </div>
  );
}

function InterviewRoom({
  room,
  health,
  healthError,
  trainingConfig,
  trainingOptions,
  onTrainingConfigChange,
}: {
  room: string;
  health: HealthPayload | null;
  healthError: string;
  trainingConfig: TrainingConfig;
  trainingOptions: TrainingOptions;
  onTrainingConfigChange: (config: TrainingConfig) => void;
}) {
  const assistant = useVoiceAssistant();
  const livekitRoom = useRoomContext();
  const stateText = assistant.state || "connecting";
  const phaseRef = useRef<SessionPhase>("idle");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const [partialTranscript, setPartialTranscript] = useState("");
  const [finalTranscript, setFinalTranscript] = useState("");
  const [assistantText, setAssistantText] = useState("");
  const [assistantState, setAssistantState] = useState("已进入房间，点击开始会话");
  const [debugEvents, setDebugEvents] = useState<string[]>([]);
  const [conversation, setConversation] = useState<ConversationEntry[]>([]);
  const [livekitConnected, setLivekitConnected] = useState(false);
  const [phase, setPhaseState] = useState<SessionPhase>("idle");
  const [showDebug, setShowDebug] = useState(false);
  const [lastVoiceLevel, setLastVoiceLevel] = useState(0);
  const [interviewReport, setInterviewReport] = useState<InterviewReport | null>(null);

  function setPhase(next: SessionPhase) {
    phaseRef.current = next;
    setPhaseState(next);
    if (next !== "listening") setLastVoiceLevel(0);
  }

  function addDebugEvent(event: string) {
    setDebugEvents((current) => [`${new Date().toLocaleTimeString()} ${event}`, ...current].slice(0, 12));
  }

  function addConversationEntry(role: ConversationEntry["role"], text: string) {
    const cleanText = text.trim();
    if (!cleanText) return;
    setConversation((current) =>
      [{ role, text: cleanText, time: new Date().toLocaleTimeString() }, ...current].slice(0, 12),
    );
  }

  async function setMicEnabled(enabled: boolean) {
    try {
      await livekitRoom.localParticipant.setMicrophoneEnabled(enabled);
      addDebugEvent(enabled ? "麦克风已打开" : "麦克风已关闭");
    } catch (cause) {
      addDebugEvent(`麦克风切换失败：${cause instanceof Error ? cause.message : "unknown"}`);
    }
  }

  async function sendControl(type: string, extra: Record<string, unknown> = {}) {
    const payload = new TextEncoder().encode(JSON.stringify({ type, ...extra }));
    await livekitRoom.localParticipant.publishData(payload, { reliable: true, topic: "control" });
    addDebugEvent(`发送控制消息：${type}`);
  }

  async function startSession() {
    setAssistantText("");
    setPartialTranscript("");
    setFinalTranscript("");
    setInterviewReport(null);
    setConversation([]);
    setPhase("thinking");
    setAssistantState("正在开始会话");
    await setMicEnabled(false);
    await sendControl("start_session", { config: trainingConfig });
  }

  async function finishTurn() {
    if (phaseRef.current !== "listening") return;
    setPhase("thinking");
    setAssistantState("已提交回答，AI 正在思考");
    await sendControl("end_turn");
    window.setTimeout(() => void setMicEnabled(false), 150);
  }

  async function endSession() {
    setPhase("thinking");
    setAssistantState("正在结束本轮并生成评分");
    await setMicEnabled(false);
    await sendControl("end_session");
  }

  async function resumeListening(reason: string) {
    if (phaseRef.current === "ended") return;
    setPhase("listening");
    setAssistantState(reason);
    await setMicEnabled(true);
  }

  async function playTts(text: string) {
    await setMicEnabled(false);
    await sendControl("assistant_speaking");
    audioRef.current?.pause();
    if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);

    try {
      const ttsStartedAt = performance.now();
      setAssistantState("正在准备 AI 语音");
      const response = await fetch(`${API_BASE}/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      objectUrlRef.current = URL.createObjectURL(await response.blob());
      addDebugEvent(`TTS 音频已返回：${Math.round(performance.now() - ttsStartedAt)}ms`);
      audioRef.current = new Audio(objectUrlRef.current);
      setPhase("speaking");
      setAssistantState("AI 正在说话，麦克风已暂时关闭");
      addDebugEvent("TTS 音频已开始播放");
      audioRef.current.addEventListener(
        "ended",
        () => {
          void sendControl("assistant_done");
          void resumeListening("AI 说完了，现在可以回答");
        },
        { once: true },
      );
      audioRef.current.addEventListener(
        "error",
        () => {
          addDebugEvent("TTS 音频播放出错");
          void sendControl("assistant_done");
          void resumeListening("TTS 播放失败，已恢复麦克风");
        },
        { once: true },
      );
      await audioRef.current.play();
    } catch (cause) {
      addDebugEvent(`TTS 失败：${cause instanceof Error ? cause.message : "unknown"}`);
      await sendControl("assistant_done");
      await resumeListening("TTS 失败，已恢复麦克风，你可以继续回答");
    }
  }

  useEffect(() => {
    const decoder = new TextDecoder();

    function onData(payload: Uint8Array, _participant?: unknown, _kind?: unknown, topic?: string) {
      const raw = decoder.decode(payload);
      addDebugEvent(`收到 data topic=${topic || "(none)"} bytes=${payload.byteLength}`);
      let event: {
        type: string;
        text?: string;
        state?: string;
        reason?: string;
        rms?: number;
        report?: InterviewReport;
      };
      try {
        event = JSON.parse(raw) as typeof event;
      } catch {
        addDebugEvent(`data 不是 JSON：${raw.slice(0, 40)}`);
        return;
      }
      if (topic && topic !== "interview") {
        addDebugEvent(`忽略非 interview topic：${topic}`);
        return;
      }

      if (event.type === "session.ready") setAssistantState("AI 面试官已准备好，点击开始会话");
      if (event.type === "session.ended") {
        setPhase("ended");
        setAssistantState(event.text || "本轮面试已结束");
      }
      if (event.type === "transcript.partial") {
        if (phaseRef.current !== "listening") return;
        setPartialTranscript(event.text || "");
        setAssistantState("正在听你回答");
      }
      if (event.type === "transcript.cancelled") {
        setPartialTranscript("");
        setAssistantState(event.reason === "mic_muted" ? "麦克风已关闭，已丢弃未完成转写" : "已取消当前转写");
        addDebugEvent(`转写已取消：${event.reason || "unknown"}`);
      }
      if (event.type === "transcript.empty") void resumeListening("没有检测到有效回答，麦克风已恢复");
      if (event.type === "turn.waiting" && phaseRef.current === "listening") {
        setAssistantState("我判断你可能还没说完，正在继续等待");
      }
      if (event.type === "turn.hint" && phaseRef.current === "listening") {
        setAssistantState(event.text || "如果没有更多补充，我将继续追问");
      }
      if (event.type === "transcript.final") {
        const text = event.text || "";
        setFinalTranscript(text);
        setPartialTranscript("");
        setPhase("thinking");
        setAssistantState("AI 正在思考追问");
        addConversationEntry("candidate", text);
      }
      if (event.type === "interview.evaluating") {
        setPhase("thinking");
        setAssistantState("正在生成评分和下一轮训练建议");
        addDebugEvent("开始生成面试评分报告");
      }
      if (event.type === "interview.report") {
        setInterviewReport(event.report || null);
        setShowDebug(false);
        setAssistantState("评分和训练建议已生成");
        addDebugEvent("已收到面试评分报告");
      }
      if (event.type === "assistant.text.delta") setAssistantText((current) => current + (event.text || ""));
      if (event.type === "assistant.text.done") {
        const text = event.text || "";
        setAssistantText(text);
        setAssistantState("正在准备 AI 语音");
        addConversationEntry("assistant", text);
        void playTts(text);
      }
      if (event.type === "assistant.state" && event.state === "thinking") {
        setPhase("thinking");
        setAssistantState("AI 正在思考追问");
      }
      if (event.type === "assistant.state" && event.state === "connected") setAssistantState("AI 面试官已进入房间");
      if (event.type === "audio.state" && event.state === "voice" && phaseRef.current === "listening") {
        const rms = typeof event.rms === "number" ? event.rms : 0;
        setLastVoiceLevel(Math.max(0, Math.min(1, rms * 18)));
        setAssistantState("检测到你的声音");
      }
      if (event.type === "audio.state" && event.state === "muted" && phaseRef.current !== "speaking") {
        setAssistantState("麦克风已关闭");
      }
      if (event.type === "audio.state" && event.state === "unmuted" && phaseRef.current === "listening") {
        setAssistantState("麦克风已打开，正在听你回答");
      }
    }

    function onConnected() {
      addDebugEvent("LiveKit 已连接");
      setLivekitConnected(true);
      setAssistantState("已进入房间，点击开始会话");
      void setMicEnabled(false);
    }

    function onDisconnected() {
      addDebugEvent("LiveKit 已断开");
      setLivekitConnected(false);
    }

    function onParticipantConnected(participant: { identity?: string }) {
      addDebugEvent(`参与者进入：${participant.identity || "unknown"}`);
    }

    function onTrackSubscribed() {
      addDebugEvent("订阅到远端音轨");
    }

    livekitRoom.on(RoomEvent.DataReceived, onData);
    livekitRoom.on(RoomEvent.Connected, onConnected);
    livekitRoom.on(RoomEvent.Disconnected, onDisconnected);
    livekitRoom.on(RoomEvent.ParticipantConnected, onParticipantConnected);
    livekitRoom.on(RoomEvent.TrackSubscribed, onTrackSubscribed);
    if (livekitRoom.state === "connected") onConnected();
    return () => {
      livekitRoom.off(RoomEvent.DataReceived, onData);
      livekitRoom.off(RoomEvent.Connected, onConnected);
      livekitRoom.off(RoomEvent.Disconnected, onDisconnected);
      livekitRoom.off(RoomEvent.ParticipantConnected, onParticipantConnected);
      livekitRoom.off(RoomEvent.TrackSubscribed, onTrackSubscribed);
      audioRef.current?.pause();
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    };
  }, [livekitRoom, trainingConfig]);

  const controlsDisabled = phase === "listening" || phase === "thinking" || phase === "speaking";

  return (
    <main className={showDebug ? "room-shell debug-layout" : "room-shell call-layout"}>
      <header className="room-header call-header">
        <div>
          <p className="eyebrow">AI INTERVIEW CALL</p>
          <h1>产品经理模拟面试</h1>
        </div>
        <div className="header-actions">
          <span className="pill">{livekitConnected ? "房间已连接" : "正在连接"}</span>
          <button type="button" className="ghost-button" onClick={() => setShowDebug((current) => !current)}>
            {showDebug ? "返回通话" : "调试台"}
          </button>
        </div>
      </header>

      {!showDebug && (
        <section className="call-stage" data-phase={phase}>
          <div className="call-backdrop" />
          <TrainingDock
            config={trainingConfig}
            options={trainingOptions}
            disabled={controlsDisabled}
            onChange={onTrainingConfigChange}
          />
          <div className="call-persona">
            <div className="call-avatar" data-phase={phase}>
              <div className="avatar-core">
                <span>AI</span>
              </div>
              <div className="avatar-ring ring-one" />
              <div className="avatar-ring ring-two" />
            </div>
            <p className="call-status-minimal">{minimalStatus(phase, assistantState || statusText(stateText))}</p>
          </div>

          {!interviewReport && (
            <div className="user-wave" data-active={phase === "listening"} style={{ "--voice-level": lastVoiceLevel } as React.CSSProperties}>
              {Array.from({ length: 18 }, (_, index) => (
                <span key={index} />
              ))}
            </div>
          )}

          {interviewReport && <InterviewReportPanel report={interviewReport} compact />}

          <div className="call-controls">
            <button
              type="button"
              className="call-control primary-call"
              onClick={startSession}
              disabled={!livekitConnected || controlsDisabled}
            >
              <span>{interviewReport ? "再练一轮" : "开始"}</span>
            </button>
            <button type="button" className="call-control" onClick={finishTurn} disabled={phase !== "listening"}>
              <span>说完了</span>
            </button>
            <button type="button" className="call-control end-call" onClick={endSession} disabled={phase === "ended" || phase === "idle"}>
              <span>结束</span>
            </button>
          </div>
        </section>
      )}

      {showDebug && (
        <section className="voice-stage" data-state={stateText}>
          <HealthPanel health={health} healthError={healthError} />
          <div className="connection-row">
            <span className="health-dot" data-ok={livekitConnected} />
            <strong>LiveKit 房间：</strong>
            <p>
              {livekitConnected ? "已连接" : "未连接"} · {room}
            </p>
          </div>
          <div className="orb">
            {assistant.audioTrack && (
              <BarVisualizer
                state={assistant.state}
                trackRef={assistant.audioTrack}
                barCount={7}
                options={{ minHeight: 16, maxHeight: 92 }}
              />
            )}
          </div>
          <p className="status">{assistantState || statusText(stateText)}</p>
          <p className="hint">自动轮次模式：AI 说话时不转写；你自然说完后系统自动判断是否提交；“我说完了”只是兜底按钮。</p>

          <div className="action-row">
            <button type="button" onClick={startSession} disabled={!livekitConnected || controlsDisabled}>
              开始会话
            </button>
            <button type="button" className="secondary-button" onClick={finishTurn} disabled={phase !== "listening"}>
              我说完了（兜底）
            </button>
            <button type="button" className="danger-button" onClick={endSession} disabled={phase === "ended" || phase === "idle"}>
              结束会话
            </button>
          </div>

          <div className="transcript-grid">
            <div className="transcript-card">
              <p className="label">实时转写</p>
              <p>{partialTranscript || finalTranscript || "等待你开始回答。"}</p>
            </div>
            <div className="transcript-card">
              <p className="label">AI 面试官</p>
              <p>{assistantText || "面试官准备中。"}</p>
            </div>
          </div>

          <section className="history-card">
            <div className="history-title">
              <p className="label">对话记录</p>
              <span>{conversation.length} 条</span>
            </div>
            {conversation.length === 0 ? (
              <p className="empty">还没有完整转写。你说完一句后，这里会保留你的回答和 AI 追问。</p>
            ) : (
              <ul>
                {conversation.map((item) => (
                  <li key={`${item.time}-${item.role}-${item.text}`}>
                    <span>{item.role === "candidate" ? "你" : "AI"}</span>
                    <p>{item.text}</p>
                    <time>{item.time}</time>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {interviewReport && <InterviewReportPanel report={interviewReport} />}

          <details className="debug-card" open>
            <summary>调试事件</summary>
            {debugEvents.length === 0 ? (
              <p>暂无事件。如果一直为空，说明前端还没连上 LiveKit 或没有收到 agent 数据。</p>
            ) : (
              <ul>
                {debugEvents.map((event) => (
                  <li key={event}>{event}</li>
                ))}
              </ul>
            )}
          </details>
        </section>
      )}

      <footer className={showDebug ? "controls" : "controls compact-controls"}>
        <ControlBar variation="minimal" controls={{ camera: false, screenShare: false }} />
      </footer>
    </main>
  );
}

function InterviewReportPanel({ report, compact = false }: { report: InterviewReport; compact?: boolean }) {
  return (
    <section className={compact ? "report-card compact-report" : "report-card"}>
      <div className="history-title">
        <p className="label">评分报告</p>
        <span>训练建议</span>
      </div>
      <p className="report-summary">{report.summary || "本轮评分已生成。"}</p>
      {!compact && report.dimensions && report.dimensions.length > 0 && (
        <div className="score-grid">
          {report.dimensions.map((item) => (
            <article key={item.id} className="score-card">
              <div className="score-head">
                <strong>{item.name}</strong>
                <span>{item.score}/5</span>
              </div>
              <p>{item.reason}</p>
              <p>
                <b>依据：</b>
                {item.evidence}
              </p>
              <p>
                <b>改进：</b>
                {item.improvement}
              </p>
            </article>
          ))}
        </div>
      )}
      <div className="plan-card">
        <p>
          <b>主要短板：</b>
          {report.main_weakness || "暂无"}
        </p>
        <p>
          <b>下一轮主题：</b>
          {report.training_plan?.theme || "暂无"}
        </p>
        <p>
          <b>练习题：</b>
          {report.training_plan?.exercise || "暂无"}
        </p>
        {!compact && (
          <p>
            <b>方法：</b>
            {report.training_plan?.method || "暂无"}
            {report.training_plan?.duration_minutes ? ` · ${report.training_plan.duration_minutes} 分钟` : ""}
          </p>
        )}
      </div>
    </section>
  );
}

function minimalStatus(phase: SessionPhase, fallback: string): string {
  if (phase === "speaking") return "AI 正在说话";
  if (phase === "thinking") return "思考中";
  if (phase === "listening") return "请回答";
  if (phase === "ended") return "已结束";
  return fallback;
}

function statusText(state: string): string {
  if (state.includes("speaking")) return "AI 正在说话";
  if (state.includes("listening")) return "正在听你回答";
  if (state.includes("thinking")) return "AI 正在思考追问";
  return "正在连接面试官";
}

createRoot(document.getElementById("root")!).render(<App />);

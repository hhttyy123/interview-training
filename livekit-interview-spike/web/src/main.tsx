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

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8787";
const DEFAULT_ROOM = "interview-spike-room";

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string") return payload.detail;
    return JSON.stringify(payload);
  } catch {
    return response.text();
  }
}

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
  companySearchProvider?: string;
  companySearchConfigured?: boolean;
  proFollowupRagEnabled?: boolean;
}

interface TrainingConfig {
  jobId: string;
  customJobTitle: string;
  modeId: string;
  followupMode: "fast" | "balanced" | "professional";
  competencyId: string;
  strategyId: string;
  companyName: string;
  companyCard: CompanyCard | null;
  jdText: string;
  resumeText: string;
  voiceProfileId: string;
  voiceRate: string;
  voicePitch: string;
  voiceVolume: string;
  interviewerTone: string;
  competencyWeights: Record<string, number>;
  questionStyleWeights: Record<string, number>;
  dynamicModel?: DynamicModelPayload | null;
}

interface CompanyCard {
  companyName: string;
  targetRole: string;
  summary: string;
  businessLines?: string[];
  productsOrServices?: string[];
  marketPosition?: string[];
  financialStrength?: string[];
  recentContext?: string[];
  cultureAndValues?: string[];
  roleRelevantPoints: string[];
  interviewTalkingPoints: string[];
  companyUnderstandingQuestions?: string[];
  sourceNotes: string[];
  sourceUrls?: string[];
  verificationStatus: "verified" | "partial" | "unverified" | string;
  confidence: number;
}

interface JdAnalysisResult {
  jdSummary?: string;
  coreRequirements?: string[];
  interviewFocus?: string[];
  competencyWeights?: Record<string, number>;
  questionStyleWeights?: Record<string, number>;
  focusCompetencyId?: string;
  recommendedVoice?: Partial<TrainingConfig>;
  analysisNotes?: string[];
  analysisSource?: string;
  dynamicModel?: DynamicModelPayload;
}

interface DynamicCompetencyPayload {
  id: string;
  name: string;
  description: string;
  weight: number;
  observableSignals: string[];
  weakSignals: string[];
}

interface DynamicEvidenceReqPayload {
  id: string;
  name: string;
  description: string;
  keywords: string[];
}

interface DynamicRubricDimPayload {
  id: string;
  name: string;
  description: string;
  weakAnchor: string;
  normalAnchor: string;
  strongAnchor: string;
}

interface DynamicModelPayload {
  jobTitle: string;
  jobSummary: string;
  coreRequirements: string[];
  interviewFocus: string[];
  competencies: DynamicCompetencyPayload[];
  questionSeeds: string[];
  competencyWeights: Record<string, number>;
  questionStyleWeights: Record<string, number>;
  focusCompetencyId: string;
  evidenceRequirements: Array<{
    competencyId: string;
    requirements: DynamicEvidenceReqPayload[];
  }>;
  rubricDimensions: DynamicRubricDimPayload[];
  recommendedVoice: Record<string, string>;
  analysisNotes: string[];
  analysisSource: string;
  openingQuestion: string;
}

interface TrainingOptions {
  jobs: Array<{ id: string; label: string }>;
  modes: Array<{ id: string; label: string }>;
  competencies: Array<{ id: string; label: string; description?: string; defaultWeight?: number }>;
  strategies: Array<{ id: string; label: string }>;
  questionStyles?: Array<{ id: string; label: string; defaultWeight: number }>;
  roles?: Array<{
    id: string;
    label: string;
    genericJd: string;
    competencies: Array<{ id: string; label: string; description?: string; defaultWeight?: number }>;
  }>;
  voiceProfiles?: VoiceProfile[];
}

interface VoiceProfile {
  id: string;
  label: string;
  gender: string;
  ageStyle: string;
  voiceName: string;
  rate: string;
  pitch: string;
  volume: string;
  tone: string;
}

interface ConversationEntry {
  role: "candidate" | "assistant";
  text: string;
  time: string;
}

interface DebugEvent {
  id: string;
  text: string;
}

interface PlannerTrace {
  id: string;
  time: string;
  mode?: string;
  followupMode?: TrainingConfig["followupMode"];
  gapTypes: string[];
  strategyId?: string;
  strategyTitle?: string;
  target?: string;
  timings?: { gapMs?: number; ragMs?: number; totalMs?: number };
  ragEnabled?: boolean;
  ragUsed?: boolean;
  ragRawCount?: number;
  ragFilteredCount?: number;
  ragMinScore?: number;
  ragTimeoutMs?: number;
  ragEmbeddingMs?: number;
  ragSearchMs?: number;
  ragRerankMs?: number;
  ragCacheHit?: boolean;
  ragError?: string;
  ragSources: string[];
  ragMatches: Array<{ title?: string; score?: number; ordinal?: number; preview?: string }>;
  ragQuery?: {
    text?: string;
    strategyCategory?: string;
    roleFamily?: string;
    competencyArchetypes?: string[];
    evidenceCategories?: string[];
    limit?: number;
  };
  error?: string;
}

interface InterviewReport {
  report_quality?: "full" | "fallback" | "insufficient_sample" | string;
  summary?: string;
  turn_count?: number;
  coverage_ratio?: number;
  ability_model?: Record<string, number>;
  evidence_gaps?: string[];
  dimensions?: Array<{
    id: string;
    name: string;
    score?: number | null;
    level?: string;
    reason: string;
    evidence: string;
    risk?: string;
    improvement: string;
  }>;
  company_fit_bonus?: {
    score?: number | null;
    reason?: string;
    verification_note?: string;
    talking_points?: string[];
  };
  role_fit?: {
    score?: number | null;
    reason?: string;
    focus_dimensions?: string[];
    risk?: string;
  };
  main_weakness?: string;
  training_plan?: {
    theme?: string;
    goal?: string;
    exercise?: string;
    method?: string;
    duration_minutes?: number;
    seven_day_plan?: string[];
    fourteen_day_plan?: string[];
    thirty_day_plan?: string[];
    tasks?: Array<{
      name?: string;
      exercise?: string;
      method?: string;
      success_criteria?: string;
    }>;
    next_interview_focus?: string;
  };
}

type SessionPhase = "idle" | "listening" | "thinking" | "speaking" | "ended";
type AppView = "home" | "setup" | "report" | "debug";
type DisconnectIntent = "manual" | "report" | null;

interface InterviewHistoryRecord {
  id: string;
  createdAt: string;
  companyName: string;
  jobLabel: string;
  modeLabel: string;
  summary: string;
  report: InterviewReport;
  conversation: ConversationEntry[];
  config: TrainingConfig;
}

interface AppDraft {
  view: AppView;
  trainingConfig: TrainingConfig;
  setupStep: number;
  analysisResult: JdAnalysisResult | null;
}

const HISTORY_STORAGE_KEY = "interview-training-history-v1";
const APP_DRAFT_STORAGE_KEY = "interview-training-app-draft-v1";

const DEFAULT_TRAINING_CONFIG: TrainingConfig = {
  jobId: "product_manager",
  customJobTitle: "",
  modeId: "standard",
  followupMode: "fast",
  competencyId: "requirement_analysis",
  strategyId: "evidence_probe",
  companyName: "",
  companyCard: null,
  jdText: "",
  resumeText: "",
  voiceProfileId: "gentle_female_young",
  voiceRate: "",
  voicePitch: "",
  voiceVolume: "",
  interviewerTone: "encouraging",
  competencyWeights: {},
  questionStyleWeights: {
    open: 30,
    evidence: 30,
    pressure: 15,
    relaxed: 15,
    reflection: 10,
  },
};

const FOLLOWUP_MODES: Array<{
  id: TrainingConfig["followupMode"];
  label: string;
  badge: string;
}> = [
  {
    id: "fast",
    label: "极速稳定",
    badge: "推荐上线",
  },
  {
    id: "balanced",
    label: "平衡策略",
    badge: "开发中",
  },
  {
    id: "professional",
    label: "专业增强",
    badge: "效果待优化",
  },
];

const FALLBACK_TRAINING_OPTIONS: TrainingOptions = {
  jobs: [{ id: "product_manager", label: "产品经理" }],
  modes: [
    { id: "standard", label: "标准训练" },
    { id: "guided", label: "引导训练" },
    { id: "challenge", label: "压力追问" },
  ],
  competencies: [
    { id: "requirement_analysis", label: "需求分析", defaultWeight: 5 },
    { id: "project_delivery", label: "项目推进", defaultWeight: 5 },
    { id: "impact_expression", label: "结果表达", defaultWeight: 5 },
  ],
  strategies: [
    { id: "clarification_probe", label: "澄清追问" },
    { id: "evidence_probe", label: "证据追问" },
    { id: "result_probe", label: "结果追问" },
    { id: "reflection_probe", label: "复盘追问" },
  ],
  questionStyles: [
    { id: "open", label: "开放提问", defaultWeight: 30 },
    { id: "evidence", label: "证据追问", defaultWeight: 30 },
    { id: "pressure", label: "压力追问", defaultWeight: 15 },
    { id: "relaxed", label: "轻松提问", defaultWeight: 15 },
    { id: "reflection", label: "复盘提问", defaultWeight: 10 },
  ],
  voiceProfiles: [
    {
      id: "gentle_female_young",
      label: "温和年轻女面试官",
      gender: "female",
      ageStyle: "young",
      voiceName: "zh-CN-XiaoxiaoNeural",
      rate: "+12%",
      pitch: "+4Hz",
      volume: "+0%",
      tone: "encouraging",
    },
  ],
};

function App() {
  const [session, setSession] = useState<TokenPayload | null>(null);
  const expectedDisconnectRef = useRef<DisconnectIntent>(null);
  const reconnectingRef = useRef(false);
  const reconnectRunRef = useRef(0);
  const [savedDraft] = useState(() => loadAppDraft());
  const [view, setView] = useState<AppView>(savedDraft?.view ?? "home");
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [healthError, setHealthError] = useState("");
  const [trainingOptions, setTrainingOptions] = useState<TrainingOptions>(FALLBACK_TRAINING_OPTIONS);
  const [trainingConfig, setTrainingConfig] = useState<TrainingConfig>(savedDraft?.trainingConfig ?? DEFAULT_TRAINING_CONFIG);
  const [setupStep, setSetupStep] = useState(savedDraft?.setupStep ?? 0);
  const [analysisResult, setAnalysisResult] = useState<JdAnalysisResult | null>(savedDraft?.analysisResult ?? null);
  const [history, setHistory] = useState<InterviewHistoryRecord[]>(() => loadHistoryRecords());
  const [activeReport, setActiveReport] = useState<InterviewHistoryRecord | null>(() => loadHistoryRecords()[0] ?? null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [reconnectNotice, setReconnectNotice] = useState("");

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
      const response = await fetch(`${API_BASE}/interview-options`, { cache: "no-store" });
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

  useEffect(() => {
    saveAppDraft({ view, trainingConfig, setupStep, analysisResult });
  }, [view, trainingConfig, setupStep, analysisResult]);

  async function requestRoomToken(): Promise<TokenPayload> {
    const response = await fetch(`${API_BASE}/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ room: DEFAULT_ROOM, name: "candidate" }),
    });
    if (!response.ok) throw new Error(await response.text());
    return (await response.json()) as TokenPayload;
  }

  async function joinRoom() {
    setLoading(true);
    setError("");
    expectedDisconnectRef.current = null;
    setReconnectNotice("");
    await refreshHealth();
    try {
      setSession(await requestRoomToken());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "无法进入面试室");
    } finally {
      setLoading(false);
    }
  }

  async function recoverRoomConnection() {
    if (reconnectingRef.current) return;
    reconnectingRef.current = true;
    const runId = reconnectRunRef.current + 1;
    reconnectRunRef.current = runId;
    setSession(null);
    setReconnectNotice("网络连接已断开，正在重新进入面试房间...");
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        await new Promise((resolve) => window.setTimeout(resolve, attempt * 900));
        if (reconnectRunRef.current !== runId) return;
        await refreshHealth();
        const nextSession = await requestRoomToken();
        if (reconnectRunRef.current !== runId) return;
        expectedDisconnectRef.current = null;
        setSession(nextSession);
        setReconnectNotice("");
        setError("");
        reconnectingRef.current = false;
        return;
      } catch (cause) {
        if (reconnectRunRef.current !== runId) return;
        setReconnectNotice(`正在尝试恢复连接 (${attempt}/3)...`);
        if (attempt === 3) {
          setError(cause instanceof Error ? cause.message : "网络恢复失败，请重新进入面试室");
        }
      }
    }
    reconnectingRef.current = false;
    setReconnectNotice("");
  }

  function handleRoomDisconnected() {
    if (expectedDisconnectRef.current) {
      reconnectRunRef.current += 1;
      expectedDisconnectRef.current = null;
      setReconnectNotice("");
      setSession(null);
      return;
    }
    void recoverRoomConnection();
  }

  function saveReport(report: InterviewReport, conversation: ConversationEntry[]) {
    const record: InterviewHistoryRecord = {
      id: `${Date.now()}`,
      createdAt: new Date().toLocaleString(),
      companyName: trainingConfig.companyCard?.companyName || trainingConfig.companyName || "未选择公司",
      jobLabel: trainingConfig.customJobTitle || trainingOptions.jobs.find((item) => item.id === trainingConfig.jobId)?.label || "目标岗位",
      modeLabel: trainingOptions.modes.find((item) => item.id === trainingConfig.modeId)?.label || trainingConfig.modeId,
      summary: report.summary || "本轮报告已生成。",
      report,
      conversation,
      config: trainingConfig,
    };
    const nextHistory = [record, ...history].slice(0, 12);
    setHistory(nextHistory);
    setActiveReport(record);
    saveHistoryRecords(nextHistory);
    setView("report");
  }

  if (!session) {
    if (reconnectNotice) {
      return (
        <main className="product-shell">
          <section className="reconnect-screen">
            <p className="eyebrow">CONNECTION RECOVERY</p>
            <h1>正在恢复面试连接</h1>
            <p>{reconnectNotice}</p>
            <button type="button" className="ghost-button" onClick={() => {
              reconnectingRef.current = false;
              reconnectRunRef.current += 1;
              expectedDisconnectRef.current = null;
              setReconnectNotice("");
              setView("setup");
            }}>
              返回配置
            </button>
          </section>
        </main>
      );
    }

    if (view === "setup") {
      return (
        <main className="product-shell">
          <SetupWizard
            config={trainingConfig}
            options={trainingOptions}
            loading={loading}
            error={error}
            onChange={setTrainingConfig}
            onBackHome={() => setView("home")}
            onStart={joinRoom}
            step={setupStep}
            onStepChange={setSetupStep}
            analysisResult={analysisResult}
            onAnalysisResultChange={setAnalysisResult}
          />
        </main>
      );
    }

    if (view === "debug") {
      return (
        <LegacySetupDebug
          trainingConfig={trainingConfig}
          trainingOptions={trainingOptions}
          loading={loading}
          error={error}
          health={health}
          healthError={healthError}
          joinRoom={joinRoom}
          setTrainingConfig={setTrainingConfig}
          onBackHome={() => setView("home")}
        />
      );
    }

    if (view === "report" && activeReport) {
      return (
        <main className="product-shell">
          <ReportPage
            record={activeReport}
            onHome={() => setView("home")}
            onRestart={() => {
              setTrainingConfig(activeReport.config);
              setView("setup");
            }}
          />
        </main>
      );
    }

    return (
      <main className="product-shell">
        <HomePage
          history={history}
          onStart={() => {
            setTrainingConfig(DEFAULT_TRAINING_CONFIG);
            setSetupStep(0);
            setAnalysisResult(null);
            setView("setup");
          }}
          onOpenRecord={(record) => {
            setActiveReport(record);
            setView("report");
          }}
        />
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
      onDisconnected={handleRoomDisconnected}
      key={session.identity}
      className="room"
    >
      <InterviewRoom
        room={session.room}
        health={health}
        healthError={healthError}
        trainingConfig={trainingConfig}
        trainingOptions={trainingOptions}
        onTrainingConfigChange={setTrainingConfig}
        onReportComplete={saveReport}
        onDisconnectIntent={(intent) => {
          expectedDisconnectRef.current = intent;
        }}
      />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}

function loadHistoryRecords(): InterviewHistoryRecord[] {
  try {
    const raw = window.localStorage.getItem(HISTORY_STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.slice(0, 12) : [];
  } catch {
    return [];
  }
}

function saveHistoryRecords(records: InterviewHistoryRecord[]) {
  window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(records.slice(0, 12)));
}

function loadAppDraft(): AppDraft | null {
  try {
    const raw = window.localStorage.getItem(APP_DRAFT_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<AppDraft>;
    const view: AppView = parsed.view === "setup" || parsed.view === "report" || parsed.view === "debug" ? parsed.view : "home";
    return {
      view,
        trainingConfig: { ...DEFAULT_TRAINING_CONFIG, ...(parsed.trainingConfig ?? {}) },
        setupStep: Math.max(0, Math.min(6, Number(parsed.setupStep ?? 0))),
        analysisResult: parsed.analysisResult ?? null,
      };
  } catch {
    return null;
  }
}

function saveAppDraft(draft: AppDraft) {
  try {
    window.localStorage.setItem(APP_DRAFT_STORAGE_KEY, JSON.stringify(draft));
  } catch {
    // 草稿只影响刷新恢复；存储失败时不阻塞主流程。
  }
}

function LegacySetupDebug({
  trainingConfig,
  trainingOptions,
  loading,
  error,
  health,
  healthError,
  joinRoom,
  setTrainingConfig,
  onBackHome,
}: {
  trainingConfig: TrainingConfig;
  trainingOptions: TrainingOptions;
  loading: boolean;
  error: string;
  health: HealthPayload | null;
  healthError: string;
  joinRoom: () => void;
  setTrainingConfig: (config: TrainingConfig) => void;
  onBackHome: () => void;
}) {
  return (
    <main className="landing setup-page">
      <button type="button" className="ghost-button debug-back-button" onClick={onBackHome}>返回主页</button>
      <TrainingDock
          config={trainingConfig}
          options={trainingOptions}
          disabled={loading}
          loading={loading}
          error={error}
          health={health}
          healthError={healthError}
          onStart={joinRoom}
          onChange={setTrainingConfig}
        />
    </main>
  );
}

function HomePage({
  history,
  onStart,
  onOpenRecord,
}: {
  history: InterviewHistoryRecord[];
  onStart: () => void;
  onOpenRecord: (record: InterviewHistoryRecord) => void;
}) {
  const latest = history[0];
  const [historyExpanded, setHistoryExpanded] = useState(false);
  const [activePanel, setActivePanel] = useState<"start" | "report" | "history">("start");
  const visibleHistory = historyExpanded ? history : history.slice(0, 3);
  return (
    <section className="home-dashboard">
      <section className="home-workspace">
        <aside className="home-nav-card" aria-label="首页功能">
          <div className="home-nav-brand">面试训练</div>
          <nav className="home-nav-list">
            <button type="button" data-active={activePanel === "start"} onClick={() => setActivePanel("start")}>
              <strong>开始训练</strong>
              <span>新建或继续配置</span>
            </button>
            <button type="button" data-active={activePanel === "report"} onClick={() => setActivePanel("report")}>
              <strong>最近报告</strong>
              <span>{latest ? latest.jobLabel : "暂无报告"}</span>
            </button>
            <button type="button" data-active={activePanel === "history"} onClick={() => setActivePanel("history")}>
              <strong>历史记录</strong>
              <span>{history.length} 条本地记录</span>
            </button>
          </nav>
        </aside>

        <section className="home-stage">
          {activePanel === "start" && (
            <article className="home-card home-focus-card">
              <p className="eyebrow">NEXT STEP</p>
              <h2>{latest ? "继续打磨下一轮面试表现" : "开始第一轮模拟面试"}</h2>
              <p className="intro">
                {latest
                  ? `最近一次是 ${latest.companyName} · ${latest.jobLabel}，你可以基于新的公司和岗位重新配置。`
                  : "先输入目标公司，再配置岗位和训练风格，系统会生成一轮可复盘的模拟面试。"}
              </p>
              <div className="home-primary-actions">
                <button type="button" onClick={onStart}>开始新的模拟面试</button>
                {latest && <button type="button" className="ghost-button" onClick={() => onOpenRecord(latest)}>查看最近报告</button>}
              </div>
              <div className="home-status-row">
                <span>累计训练 {history.length} 次</span>
                <span>{latest ? latest.jobLabel : "等待第一轮训练"}</span>
                <span>{latest?.createdAt || "暂无训练记录"}</span>
              </div>
            </article>
          )}

          {activePanel === "report" && (
            <article className="home-card">
              <div className="section-title">
                <strong>最近报告</strong>
                {latest && <button type="button" className="text-button" onClick={() => onOpenRecord(latest)}>查看完整报告</button>}
              </div>
              {latest ? (
                <>
                  <p className="report-summary">{latest.summary}</p>
                  <div className="mini-tags">
                    <span>{latest.companyName}</span>
                    <span>{latest.jobLabel}</span>
                    <span>{latest.createdAt}</span>
                  </div>
                  {latest.report.training_plan ? <PhaseTrainingPlan plan={latest.report.training_plan} /> : null}
                </>
              ) : (
                <p className="empty">还没有报告。完成一轮面试后，这里会显示最新结果。</p>
              )}
            </article>
          )}

          {activePanel === "history" && (
            <article className="home-card history-card">
              <div className="section-title">
                <strong>历史记录</strong>
                {history.length > 3 ? (
                  <button type="button" className="text-button" onClick={() => setHistoryExpanded((current) => !current)}>
                    {historyExpanded ? "收起" : `查看全部 ${history.length} 条`}
                  </button>
                ) : (
                  <span>{history.length} 条</span>
                )}
              </div>
              {history.length === 0 ? (
                <p className="empty">暂无历史。开始第一轮模拟面试吧。</p>
              ) : (
                <div className="history-list compact-history-list">
                  {visibleHistory.map((record) => (
                    <button type="button" key={record.id} onClick={() => onOpenRecord(record)}>
                      <strong>{record.jobLabel}</strong>
                      <span>{record.companyName} · {record.modeLabel}</span>
                      <time>{record.createdAt}</time>
                    </button>
                  ))}
                </div>
              )}
            </article>
          )}
        </section>
      </section>
    </section>
  );
}

function SetupWizard({
  config,
  options,
  loading,
  error,
  onChange,
  onBackHome,
  onStart,
  step,
  onStepChange,
  analysisResult,
  onAnalysisResultChange,
}: {
  config: TrainingConfig;
  options: TrainingOptions;
  loading: boolean;
  error: string;
  onChange: (config: TrainingConfig) => void;
  onBackHome: () => void;
  onStart: () => void;
  step: number;
  onStepChange: React.Dispatch<React.SetStateAction<number>>;
  analysisResult: JdAnalysisResult | null;
  onAnalysisResultChange: (result: JdAnalysisResult | null) => void;
}) {
  const [companyLoading, setCompanyLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useSimulatedProgress(analysisLoading);
  const [resumeLoading, setResumeLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState("");
  const [companyError, setCompanyError] = useState("");
  const [jobFocused, setJobFocused] = useState(false);
  const [companyDetailOpen, setCompanyDetailOpen] = useState(false);
  const [resumeModalOpen, setResumeModalOpen] = useState(false);
  const [resumePdfUrl, setResumePdfUrl] = useState<string | null>(() => {
    try { return window.localStorage.getItem("resume-pdf-data"); } catch { return null; }
  });
  const selectedRole = options.roles?.find((role) => role.id === config.jobId);
  // 优先使用动态模型的能力维度，否则用预设岗位的
  const dynamicCompetencies: Array<{ id: string; label: string; description?: string; defaultWeight?: number }> =
    analysisResult?.dynamicModel?.competencies?.map((c) => ({
      id: c.id,
      label: c.name,
      description: c.description,
      defaultWeight: c.weight,
    })) ?? [];
  const competencies = dynamicCompetencies.length > 0
    ? dynamicCompetencies
    : (selectedRole?.competencies?.length ? selectedRole.competencies : options.competencies);
  const questionStyles = options.questionStyles ?? FALLBACK_TRAINING_OPTIONS.questionStyles ?? [];
  const voiceProfiles = options.voiceProfiles?.length ? options.voiceProfiles : FALLBACK_TRAINING_OPTIONS.voiceProfiles ?? [];
  const [jobDraft, setJobDraft] = useState(config.customJobTitle || selectedRole?.label || "");
  const visibleJobs = options.jobs
    .filter((item) => !jobDraft.trim() || item.label.includes(jobDraft) || item.id.includes(jobDraft.toLowerCase()))
    .slice(0, 6);
  const steps = ["目标公司", "目标岗位", "JD 分析", "面试风格", "声音氛围", "个人材料", "最终确认"];
  const jobInputReady = Boolean(roleLabel().trim());

  function patch(next: Partial<TrainingConfig>) {
    onChange({ ...config, ...next });
  }

  function commitJobDraft(value = jobDraft) {
    const clean = value.trim();
    const matched = options.jobs.find((item) => item.label === clean || item.id === clean);
    patch({
      jobId: matched?.id || "",
      customJobTitle: matched ? "" : clean,
      jdText: "",
    });
    return matched?.id || "";
  }

  function selectPresetJob(item: { id: string; label: string }) {
    setJobDraft(item.label);
    onAnalysisResultChange(null);
    setAnalysisError("");
    patch({ jobId: item.id, customJobTitle: "", jdText: "" });
    setJobFocused(false);
  }

  function updateJobDraft(value: string) {
    const matched = options.jobs.find((item) => item.label === value.trim() || item.id === value.trim());
    setJobDraft(value);
    onAnalysisResultChange(null);
    setAnalysisError("");
    patch({
      jobId: matched?.id || "",
      customJobTitle: matched ? "" : value.trim(),
      jdText: "",
      dynamicModel: null,
    });
  }

  function roleLabel() {
    return jobDraft.trim() || config.customJobTitle.trim() || "";
  }

  async function generateCompanyCard() {
    if (!config.companyName.trim()) {
      setCompanyError("请输入公司名称后再生成公司资料。");
      return;
    }
    setCompanyError("");
    setCompanyLoading(true);
    try {
      const response = await fetch(`${API_BASE}/company-card`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ companyName: config.companyName.trim(), targetRole: roleLabel(), useWebSearch: true }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      patch({ companyCard: (await response.json()) as CompanyCard });
      setCompanyDetailOpen(false);
    } finally {
      setCompanyLoading(false);
    }
  }

  async function analyzeJob() {
    const cleanRoleLabel = roleLabel().trim();
    if (!cleanRoleLabel) {
      setAnalysisError("请先输入或选择目标岗位，再生成岗位 JD 分析。");
      return;
    }
    setAnalysisLoading(true);
    setAnalysisError("");
    try {
      const committedJobId = commitJobDraft();
      const committedRole = options.roles?.find((role) => role.id === committedJobId);
      const isCustomJob = Boolean(jobDraft.trim()) && !options.jobs.some((item) => item.label === jobDraft.trim() || item.id === jobDraft.trim());
      const sourceJdText = isCustomJob ? "" : committedRole?.genericJd || config.jdText;
      const companyCard =
        config.companyCard && roleLabel() !== config.companyCard.targetRole
          ? { ...config.companyCard, targetRole: roleLabel() }
          : config.companyCard;
      const response = await fetch(`${API_BASE}/analyze-jd`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          roleId: committedJobId,
          roleLabel: cleanRoleLabel,
          modeId: config.modeId,
          jdText: sourceJdText,
          companyCard,
        }),
      });
      if (!response.ok) {
        const detail = await readErrorDetail(response);
        throw new Error(detail || `HTTP ${response.status}`);
      }
      const payload = (await response.json()) as JdAnalysisResult;
      setAnalysisProgress(96);
      onAnalysisResultChange(payload);
      patch({
        jobId: committedJobId,
        customJobTitle: options.jobs.find((item) => item.id === committedJobId)?.label === cleanRoleLabel ? "" : cleanRoleLabel,
        jdText: payload.jdSummary || sourceJdText,
        companyCard,
        competencyId: payload.focusCompetencyId || config.competencyId,
        competencyWeights: payload.competencyWeights || (payload.dynamicModel?.competencyWeights || config.competencyWeights),
        questionStyleWeights: payload.questionStyleWeights || (payload.dynamicModel?.questionStyleWeights || config.questionStyleWeights),
        dynamicModel: payload.dynamicModel || null,
        voiceProfileId: payload.recommendedVoice?.voiceProfileId || config.voiceProfileId,
        interviewerTone: payload.recommendedVoice?.interviewerTone || config.interviewerTone,
        voiceRate: payload.recommendedVoice?.voiceRate || config.voiceRate,
        voicePitch: payload.recommendedVoice?.voicePitch || config.voicePitch,
        voiceVolume: payload.recommendedVoice?.voiceVolume || config.voiceVolume,
      });
      onStepChange(2);
    } catch (error) {
      setAnalysisError(error instanceof Error ? error.message : "岗位 JD 分析失败，请检查 DeepSeek 配置和网络。");
    } finally {
      setAnalysisProgress(100);
      setAnalysisLoading(false);
      window.setTimeout(() => setAnalysisProgress(0), 500);
    }
  }

  async function parseResumeFile(file: File | null) {
    if (!file) return;
    setResumeLoading(true);
    // 将 PDF 存为 base64，持久化到 localStorage，刷新不丢
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      setResumePdfUrl(dataUrl);
      try { window.localStorage.setItem("resume-pdf-data", dataUrl); } catch {}
    };
    reader.readAsDataURL(file);
    try {
      const form = new FormData();
      form.append("file", file);
      const response = await fetch(`${API_BASE}/parse-resume`, { method: "POST", body: form });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as { text?: string; summary?: string };
      patch({ resumeText: payload.text || payload.summary || config.resumeText });
    } finally {
      setResumeLoading(false);
    }
  }

  function updateCompetencyWeight(id: string, value: number) {
    patch({ competencyWeights: { ...defaultCompetencyWeights(competencies), ...config.competencyWeights, [id]: value } });
  }

  function updateQuestionStyleWeight(id: string, value: number) {
    patch({ questionStyleWeights: { ...config.questionStyleWeights, [id]: value } });
  }

  function resetAnalysisDefaults() {
    patch({
      competencyWeights: analysisResult?.competencyWeights || defaultCompetencyWeights(competencies),
      questionStyleWeights: analysisResult?.questionStyleWeights || config.questionStyleWeights,
    });
  }

  function applyModePreset(modeId: string) {
    const presets: Record<string, Record<string, number>> = {
      standard: { open: 25, evidence: 35, pressure: 15, relaxed: 10, reflection: 15 },
      guided: { open: 35, evidence: 25, pressure: 5, relaxed: 20, reflection: 15 },
      challenge: { open: 15, evidence: 30, pressure: 35, relaxed: 5, reflection: 15 },
    };
    patch({
      modeId,
      questionStyleWeights: presets[modeId] || config.questionStyleWeights,
    });
  }

  async function nextStep() {
    if (step === 1) {
      await analyzeJob();
      return;
    }
    onStepChange((current) => Math.min(steps.length - 1, current + 1));
  }

  return (
    <section className="wizard-shell">
      <header className="wizard-topbar">
        <button type="button" className="wizard-home-button" onClick={onBackHome}>返回主页</button>
        <span>{steps[step]}</span>
      </header>
      <section className="wizard-panel">
        <div className="wizard-progress" aria-label={`第 ${step + 1} 步，共 ${steps.length} 步`}>
          <i style={{ width: `${((step + 1) / steps.length) * 100}%` }} />
        </div>
        {step === 0 && (
          <WizardCard title="选择目标公司">
            <div className="inline-action-field">
              <input value={config.companyName} placeholder="输入公司名，例如腾讯、字节跳动" onChange={(event) => {
                setCompanyError("");
                patch({ companyName: event.target.value });
              }} />
              <button type="button" className="secondary-button" disabled={companyLoading || !config.companyName.trim()} onClick={generateCompanyCard}>
                {companyLoading ? "生成中" : "生成情报"}
              </button>
            </div>
            {!config.companyName.trim() && <p className="empty">输入公司名称后，才可以搜索并生成公司资料。</p>}
            {companyError && <p className="error-text">{companyError}</p>}
            {config.companyCard ? (
              <>
                <button type="button" className="company-summary-strip" onClick={() => setCompanyDetailOpen(true)}>
                  <span>
                    <strong>{config.companyCard.companyName}</strong>
                    <small>{verificationLabel(config.companyCard.verificationStatus)}</small>
                  </span>
                  <em>{config.companyCard.summary}</em>
                  <b>查看</b>
                </button>
                {companyDetailOpen && (
                  <CompanyInsightModal card={config.companyCard} onClose={() => setCompanyDetailOpen(false)} />
                )}
              </>
            ) : config.companyName.trim() ? <p className="empty">点击“生成情报”后会显示公司资料。</p> : <p className="empty">也可以直接下一步，做通用岗位面试。</p>}
          </WizardCard>
        )}

        {step === 1 && (
          <WizardCard title="选择目标岗位">
            <div className="job-picker">
              <input value={jobDraft} placeholder="输入或选择岗位，例如销售" onFocus={() => setJobFocused(true)} onBlur={() => window.setTimeout(() => setJobFocused(false), 120)} onChange={(event) => updateJobDraft(event.target.value)} />
              <button type="button" className="job-picker-toggle" tabIndex={-1} onMouseDown={(event) => { event.preventDefault(); setJobFocused((current) => !current); }}>▾</button>
              {jobFocused && visibleJobs.length > 0 && (
                <div className="job-picker-menu">
                  {visibleJobs.map((item) => (
                    <button type="button" key={item.id} onMouseDown={(event) => event.preventDefault()} onClick={() => selectPresetJob(item)}>
                      {item.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {(analysisLoading || analysisProgress > 0) && <JdAnalysisProgress active={analysisLoading} progress={analysisLoading ? analysisProgress : 100} />}
            {analysisError && <p className="error-text">{analysisError}</p>}
            <p className="empty">{jobInputReady ? "点击下一步后，系统会分析该岗位的通用 JD 和训练能力模型。" : "请先输入或选择目标岗位，岗位为空时不会生成默认 JD。"}</p>
          </WizardCard>
        )}

        {step === 2 && (
          <WizardCard title="岗位 JD 分析">
            <p className="analysis-summary">{analysisLoading ? "正在分析岗位 JD..." : analysisResult?.jdSummary || "还没有分析结果，请返回岗位页重新分析。"}</p>
            {analysisError && <p className="error-text">{analysisError}</p>}
            <div className="analysis-mini-grid">
              <MiniList title="核心要求" items={analysisResult?.coreRequirements} />
              <MiniList title="面试重点" items={analysisResult?.interviewFocus} />
            </div>
            <button type="button" className="ghost-button" onClick={resetAnalysisDefaults}>恢复岗位默认</button>
            <div className="config-radar-grid single-radar-grid">
              <ConfigRadarPanel
                title="能力重要性评分"
                subtitle="每个能力独立评分 1-10，不影响其他维度"
                disabled={false}
                maxValue={10}
                entries={competencies.map((item) => ({
                  id: item.id,
                  label: item.label,
                  value: config.competencyWeights[item.id] ?? item.defaultWeight ?? 5,
                  defaultValue: analysisResult?.competencyWeights?.[item.id] ?? item.defaultWeight ?? 5,
                }))}
                onChange={updateCompetencyWeight}
              />
            </div>
            {analysisResult?.analysisNotes && analysisResult.analysisNotes.length > 0 && (
              <div className="analysis-notes-card">
                <strong>分析依据</strong>
                <ul>
                  {analysisResult.analysisNotes.map((note) => (
                    <li key={note.slice(0, 20)}>{note}</li>
                  ))}
                </ul>
                {analysisResult?.dynamicModel?.competencies && (
                  <details>
                    <summary>各能力维度说明</summary>
                    <div className="competency-detail-grid">
                      {analysisResult.dynamicModel.competencies.map((comp) => (
                        <div key={comp.id} className="competency-detail-item">
                          <strong>{comp.name}</strong>
                          <span>重要性 {comp.weight}/10</span>
                          <p>{comp.description}</p>
                          <small>正面信号：{comp.observableSignals.join("、")}</small>
                          <small>不足信号：{comp.weakSignals.join("、")}</small>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            )}
          </WizardCard>
        )}

        {step === 3 && (
          <WizardCard title="选择面试风格">
            <div className="followup-mode-grid" aria-label="追问运行模式">
              {FOLLOWUP_MODES.map((mode) => (
                <button
                  type="button"
                  key={mode.id}
                  data-active={config.followupMode === mode.id}
                  onClick={() => patch({ followupMode: mode.id })}
                >
                  <span className="mode-card-topline">
                    <strong>{mode.label}</strong>
                    <em>{mode.badge}</em>
                  </span>
                </button>
              ))}
            </div>
            <div className="choice-grid">
              {options.modes.map((mode) => (
                <button type="button" key={mode.id} data-active={config.modeId === mode.id} onClick={() => applyModePreset(mode.id)}>
                  <strong>{mode.label}</strong>
                  <span>{mode.id === "challenge" ? "更直接、更重证据" : mode.id === "guided" ? "更温和，会给方向" : "接近真实结构化面试"}</span>
                </button>
              ))}
            </div>
            <ConfigRadarPanel
              title="追问雷达"
              subtitle="选择模式会套用预设，也可以拖动自定义"
              disabled={false}
              entries={questionStyles.map((item) => ({
                id: item.id,
                label: item.label,
                value: config.questionStyleWeights[item.id] ?? item.defaultWeight,
                defaultValue: analysisResult?.questionStyleWeights?.[item.id] ?? config.questionStyleWeights[item.id] ?? item.defaultWeight,
              }))}
              onChange={updateQuestionStyleWeight}
            />
            <button type="button" className="ghost-button" onClick={() => applyModePreset(config.modeId)}>恢复当前风格预设</button>
          </WizardCard>
        )}

        {step === 4 && (
          <WizardCard title="声音与氛围">
            <div className="choice-grid">
              {voiceProfiles.map((profile) => (
                <button type="button" key={profile.id} data-active={config.voiceProfileId === profile.id} onClick={() => patch({ voiceProfileId: profile.id, voiceRate: profile.rate, voicePitch: profile.pitch, voiceVolume: profile.volume, interviewerTone: profile.tone })}>
                  <strong>{profile.label}</strong>
                  <span>{profile.gender} · {profile.ageStyle} · {profile.tone}</span>
                </button>
              ))}
            </div>
            <details className="advanced-card">
              <summary>高级 TTS 设置</summary>
              <div className="voice-control-grid">
                <SelectField label="语气" value={config.interviewerTone} options={[{ id: "encouraging", label: "鼓励" }, { id: "formal", label: "正式" }, { id: "pressure", label: "压力" }, { id: "relaxed", label: "轻松" }, { id: "calm", label: "沉稳" }]} disabled={false} onChange={(value) => patch({ interviewerTone: value })} />
                <SelectField label="语速" value={config.voiceRate} options={[{ id: "", label: "跟随档位" }, { id: "-10%", label: "偏慢" }, { id: "+0%", label: "正常" }, { id: "+10%", label: "偏快" }, { id: "+18%", label: "很快" }]} disabled={false} onChange={(value) => patch({ voiceRate: value })} />
              </div>
            </details>
          </WizardCard>
        )}

        {step === 5 && (
          <WizardCard title="上传个人材料">
            <label className="file-upload-field">
              <span>{resumeLoading ? "正在解析简历..." : config.resumeText ? "PDF 简历已解析，可重新上传" : "上传 PDF 简历"}</span>
              <input type="file" accept=".pdf,application/pdf" disabled={resumeLoading} onChange={(event) => void parseResumeFile(event.target.files?.[0] || null)} />
            </label>
            {config.resumeText && (
              <button type="button" className="company-summary-strip" onClick={() => setResumeModalOpen(true)}>
                <span><strong>个人简历</strong><small>{config.resumeText.length} 字</small></span>
                <em>{config.resumeText.slice(0, 80)}{config.resumeText.length > 80 ? "…" : ""}</em>
                <b>查看</b>
              </button>
            )}
            {resumeModalOpen && config.resumeText && (
              <ResumeModal text={config.resumeText} pdfUrl={resumePdfUrl} onClose={() => setResumeModalOpen(false)} />
            )}
          </WizardCard>
        )}

        {step === 6 && (
          <WizardCard title="确认面试设置">
            <div className="confirm-grid">
              <MiniList title="公司" items={[config.companyCard?.companyName || config.companyName || "已跳过"]} />
              <MiniList title="岗位" items={[roleLabel()]} />
              <MiniList title="风格" items={[options.modes.find((item) => item.id === config.modeId)?.label || config.modeId]} />
              <MiniList title="追问档位" items={[FOLLOWUP_MODES.find((item) => item.id === config.followupMode)?.label || config.followupMode]} />
              <MiniList title="声音" items={[voiceProfiles.find((item) => item.id === config.voiceProfileId)?.label || config.voiceProfileId]} />
              <MiniList title="简历" items={[config.resumeText ? "已上传并解析" : "未上传"]} />
              <MiniList title="配置" items={[analysisResult ? "已生成 JD 和雷达配置" : "请先完成 AI 岗位分析"]} />
            </div>
          </WizardCard>
        )}

        <footer className="wizard-actions">
          <span>第 {step + 1} 步，共 {steps.length} 步</span>
          <button type="button" className="ghost-button" disabled={step === 0 || loading || analysisLoading} onClick={() => onStepChange((current) => Math.max(0, current - 1))}>上一步</button>
          {step < steps.length - 1 ? (
            <button type="button" disabled={loading || analysisLoading || (step === 1 && !jobInputReady)} onClick={() => void nextStep()}>{analysisLoading ? "分析中..." : "下一步"}</button>
          ) : (
            <button type="button" disabled={loading} onClick={onStart}>{loading ? "正在进入..." : "开始面试"}</button>
          )}
          {error && <p className="error">{error}</p>}
        </footer>
      </section>
    </section>
  );
}

function WizardCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <article className="wizard-card">
      <div className="section-title">
        <div>
          <strong>{title}</strong>
        </div>
      </div>
      {children}
    </article>
  );
}

function CompanyInsightCard({ card }: { card: CompanyCard }) {
  return (
    <div className="compact-company-card">
      <strong>{card.companyName}</strong>
      <span>{verificationLabel(card.verificationStatus)}</span>
      <p>{card.summary}</p>
      <div className="company-detail-grid">
        <MiniList title="基本现状" items={[...(card.businessLines ?? []), ...(card.productsOrServices ?? [])]} />
        <MiniList title="行业位置" items={card.marketPosition} />
        <MiniList title="企业特色" items={card.cultureAndValues} />
        <MiniList title="面试注意点" items={card.roleRelevantPoints} />
        <MiniList title="公司理解话题" items={card.interviewTalkingPoints} />
        <MiniList title="资料来源" items={card.sourceNotes} />
      </div>
    </div>
  );
}

function CompanyInsightModal({ card, onClose }: { card: CompanyCard; onClose: () => void }) {
  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  return (
    <div className="company-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="company-modal" role="dialog" aria-modal="true" aria-label={`${card.companyName}公司资料`} onMouseDown={(event) => event.stopPropagation()}>
        <header>
          <div>
            <span>公司资料</span>
            <h2>{card.companyName}</h2>
            <p>公司理解用于面试加分项，不包含岗位 JD 与财务搜索。</p>
          </div>
          <button type="button" aria-label="关闭公司资料" onClick={onClose}>×</button>
        </header>
        <div className="company-modal-meta">
          <span>{verificationLabel(card.verificationStatus)}</span>
        </div>
        <div className="company-modal-layout">
          <div className="company-modal-summary-card">
            <strong>简介</strong>
            <p>{card.summary}</p>
          </div>
          <MiniList title="基本现状" items={[...(card.businessLines ?? []), ...(card.productsOrServices ?? [])]} />
          <MiniList title="行业位置" items={card.marketPosition} />
          <MiniList title="企业特色/文化" items={card.cultureAndValues} />
          <MiniList title="面试注意点" items={card.roleRelevantPoints} />
          <MiniList title="公司理解话题" items={card.interviewTalkingPoints} />
          <MiniList title="准备问题" items={card.companyUnderstandingQuestions} />
          <SourceNotesDetails items={card.sourceNotes} />
        </div>
      </section>
    </div>
  );
}

function ResumeModal({ text, pdfUrl, onClose }: { text: string; pdfUrl?: string | null; onClose: () => void }) {
  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  return (
    <div className="company-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="company-modal" role="dialog" aria-modal="true" aria-label="简历全文" onMouseDown={(event) => event.stopPropagation()} style={{ maxWidth: "56rem", height: "min(95vh, 52rem)", display: "flex", flexDirection: "column" }}>
        <header style={{ flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.7rem 1rem", borderBottom: "1px solid rgba(33,79,64,0.1)" }}>
          <span style={{ fontWeight: 850, color: "#214f40", fontSize: "0.95rem" }}>个人简历{pdfUrl ? "（原始 PDF）" : `（${text.length} 字）`}</span>
          <button type="button" aria-label="关闭简历" onClick={onClose} style={{ width: "1.8rem", height: "1.8rem", border: "1px solid rgba(33,79,64,0.12)", borderRadius: "50%", background: "rgba(255,255,255,0.72)", color: "#214f40", fontSize: "1rem", cursor: "pointer", display: "grid", placeItems: "center" }}>×</button>
        </header>
        <div style={{ flex: 1, minHeight: 0, padding: 0 }}>
          {pdfUrl ? (
            <iframe src={pdfUrl} style={{ width: "100%", height: "100%", border: "none", display: "block" }} title="PDF 简历预览" />
          ) : (
            <div style={{ padding: "1.2rem", whiteSpace: "pre-wrap", wordBreak: "break-word", fontFamily: "'PingFang SC', 'Microsoft YaHei UI', sans-serif", fontSize: "0.95rem", lineHeight: 1.85, color: "#1a2e1a", height: "100%", overflow: "auto" }}>
              {text}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function SourceNotesDetails({ items }: { items?: string[] }) {
  const safeItems = items?.filter(Boolean).slice(0, 5) ?? [];
  return (
    <details className="company-source-details">
      <summary>资料来源</summary>
      {safeItems.length > 0 ? (
        safeItems.map((item) => <span key={item}>{item}</span>)
      ) : (
        <span>等待分析</span>
      )}
    </details>
  );
}

function ReportPage({ record, onHome, onRestart }: { record: InterviewHistoryRecord; onHome: () => void; onRestart: () => void }) {
  const [reportModalOpen, setReportModalOpen] = useState(false);

  return (
    <section className="report-page">
      <header className="home-hero">
        <div>
          <p className="eyebrow">INTERVIEW REPORT</p>
          <h1>面试报告</h1>
          <p className="intro">{record.companyName} · {record.jobLabel} · {record.createdAt}</p>
        </div>
        <div className="home-actions">
          <button type="button" onClick={onHome}>返回主页</button>
          <button type="button" className="ghost-button" onClick={onRestart}>再练一轮</button>
        </div>
      </header>
      <InterviewReportSummaryCard report={record.report} onOpen={() => setReportModalOpen(true)} />
      {reportModalOpen && (
        <InterviewReportModal
          report={record.report}
          title={`${record.companyName} · ${record.jobLabel}`}
          subtitle={record.createdAt}
          onClose={() => setReportModalOpen(false)}
        />
      )}
      <details className="home-card">
        <summary>完整对话记录</summary>
        <div className="history-list transcript-history">
          {record.conversation.map((item, index) => (
            <div key={`${item.time}-${index}`}>
              <strong>{item.role === "candidate" ? "你" : "AI"}</strong>
              <p>{item.text}</p>
              <time>{item.time}</time>
            </div>
          ))}
        </div>
      </details>
    </section>
  );
}

function TrainingDock({
  config,
  options,
  disabled,
  loading = false,
  error = "",
  health,
  healthError = "",
  onStart,
  onChange,
}: {
  config: TrainingConfig;
  options: TrainingOptions;
  disabled: boolean;
  loading?: boolean;
  error?: string;
  health?: HealthPayload | null;
  healthError?: string;
  onStart?: () => void;
  onChange: (config: TrainingConfig) => void;
}) {
  const [jdLoading, setJdLoading] = useState(false);
  const [resumeLoading, setResumeLoading] = useState(false);
  const [companyLoading, setCompanyLoading] = useState(false);
  const [companyDetailOpen, setCompanyDetailOpen] = useState(false);
  const [resumeModalOpen, setResumeModalOpen] = useState(false);
  const [resumePdfUrl, setResumePdfUrl] = useState<string | null>(() => {
    try { return window.localStorage.getItem("resume-pdf-data"); } catch { return null; }
  });
  const [analysisResult, setAnalysisResult] = useState<JdAnalysisResult | null>(null);
  const [jobInputFocused, setJobInputFocused] = useState(false);
  const selectedRole = options.roles?.find((role) => role.id === config.jobId);
  const dynamicCompetencies: Array<{ id: string; label: string; description?: string; defaultWeight?: number }> =
    analysisResult?.dynamicModel?.competencies?.map((c) => ({
      id: c.id,
      label: c.name,
      description: c.description,
      defaultWeight: c.weight,
    })) ?? [];
  const competencies = dynamicCompetencies.length > 0
    ? dynamicCompetencies
    : (selectedRole?.competencies?.length ? selectedRole.competencies : options.competencies);
  const voiceProfiles = options.voiceProfiles?.length ? options.voiceProfiles : FALLBACK_TRAINING_OPTIONS.voiceProfiles ?? [];
  const questionStyles = options.questionStyles ?? FALLBACK_TRAINING_OPTIONS.questionStyles ?? [];
  const jobInputValue = config.customJobTitle || selectedRole?.label || "";
  const visibleJobOptions = options.jobs
    .filter((item) => {
      const keyword = jobInputValue.trim().toLowerCase();
      if (!keyword || !config.customJobTitle) return true;
      return item.label.toLowerCase().includes(keyword) || item.id.toLowerCase().includes(keyword);
    })
    .slice(0, 6);

  function update(key: keyof TrainingConfig, value: string) {
    onChange({ ...config, [key]: value });
  }

  function updateJobInput(value: string) {
    const matchedRole = options.jobs.find((item) => item.label === value || item.id === value);
    onChange({
      ...config,
      jobId: matchedRole?.id || config.jobId,
      customJobTitle: matchedRole ? "" : value,
    });
  }

  function selectJobOption(option: { id: string; label: string }) {
    onChange({
      ...config,
      jobId: option.id,
      customJobTitle: "",
    });
    setJobInputFocused(false);
  }

  function displayRoleLabel(): string {
    return config.customJobTitle.trim() || selectedRole?.label || options.jobs.find((item) => item.id === config.jobId)?.label || "目标岗位";
  }

  async function generateCompanyCard() {
    if (!config.companyName.trim()) return;
    setCompanyLoading(true);
    try {
      const response = await fetch(`${API_BASE}/company-card`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          companyName: config.companyName.trim(),
          targetRole: displayRoleLabel(),
          useWebSearch: true,
        }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as CompanyCard;
      onChange({ ...config, companyCard: payload });
      setCompanyDetailOpen(false);
    } finally {
      setCompanyLoading(false);
    }
  }

  function updateQuestionStyleWeight(styleId: string, value: string) {
    onChange({
      ...config,
      questionStyleWeights: {
        ...config.questionStyleWeights,
        [styleId]: Number(value),
      },
    });
  }

  function updateCompetencyWeight(competencyId: string, value: string) {
    onChange({
      ...config,
      competencyWeights: {
        ...defaultCompetencyWeights(competencies),
        ...config.competencyWeights,
        [competencyId]: Number(value),
      },
    });
  }

  async function analyzeJd() {
    setJdLoading(true);
    try {
      const response = await fetch(`${API_BASE}/analyze-jd`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          roleId: config.jobId,
          roleLabel: displayRoleLabel(),
          modeId: config.modeId,
          jdText: selectedRole?.genericJd || config.jdText,
          companyCard: config.companyCard,
        }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as JdAnalysisResult;
      setAnalysisResult(payload);
      onChange({
        ...config,
        jdText: selectedRole?.genericJd || config.jdText,
        competencyId: payload.focusCompetencyId || config.competencyId,
        competencyWeights: payload.competencyWeights || (payload.dynamicModel?.competencyWeights || config.competencyWeights),
        questionStyleWeights: payload.questionStyleWeights || (payload.dynamicModel?.questionStyleWeights || config.questionStyleWeights),
        dynamicModel: payload.dynamicModel || config.dynamicModel || null,
        voiceProfileId: payload.recommendedVoice?.voiceProfileId || config.voiceProfileId,
        interviewerTone: payload.recommendedVoice?.interviewerTone || config.interviewerTone,
        voiceRate: payload.recommendedVoice?.voiceRate || config.voiceRate,
        voicePitch: payload.recommendedVoice?.voicePitch || config.voicePitch,
        voiceVolume: payload.recommendedVoice?.voiceVolume || config.voiceVolume,
      });
    } finally {
      setJdLoading(false);
    }
  }

  async function parseResumeFile(file: File | null) {
    if (!file) return;
    setResumeLoading(true);
    // 将 PDF 存为 base64，持久化到 localStorage，刷新不丢
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      setResumePdfUrl(dataUrl);
      try { window.localStorage.setItem("resume-pdf-data", dataUrl); } catch {}
    };
    reader.readAsDataURL(file);
    try {
      const form = new FormData();
      form.append("file", file);
      const response = await fetch(`${API_BASE}/parse-resume`, {
        method: "POST",
        body: form,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = (await response.json()) as { text?: string; summary?: string };
      onChange({ ...config, resumeText: payload.text || payload.summary || config.resumeText });
    } finally {
      setResumeLoading(false);
    }
  }

  return (
    <section className="training-dock" aria-label="训练条件">
      <aside className="setup-sidebar">
        <p className="eyebrow">AI INTERVIEW AGENT</p>
        <h1>面试训练</h1>
        <p className="intro compact-intro">选公司、岗位、风格和声音，再点击分析生成本轮配置。</p>

        <article className="setup-card sidebar-card">
          <div className="setup-card-head">
            <span>01</span>
            <div>
              <strong>面试对象</strong>
            </div>
          </div>
          <div className="setup-grid">
            <label className="config-field">
              <span>目标公司</span>
              <div className="inline-action-field">
                <input
                  value={config.companyName}
                  disabled={disabled || companyLoading}
                  placeholder="例如：腾讯、字节跳动"
                  onChange={(event) => onChange({ ...config, companyName: event.target.value })}
                />
                <button type="button" className="secondary-button" disabled={disabled || companyLoading || !config.companyName.trim()} onClick={generateCompanyCard}>
                  {companyLoading ? "搜索中" : "生成"}
                </button>
              </div>
            </label>
            <label className="config-field">
              <span>岗位</span>
              <div className="job-picker">
                <input
                  value={jobInputValue}
                  disabled={disabled}
                  placeholder="输入或选择岗位，例如增长产品经理"
                  onFocus={() => setJobInputFocused(true)}
                  onBlur={() => window.setTimeout(() => setJobInputFocused(false), 120)}
                  onChange={(event) => updateJobInput(event.target.value)}
                />
                <button
                  type="button"
                  className="job-picker-toggle"
                  disabled={disabled}
                  tabIndex={-1}
                  onMouseDown={(event) => {
                    event.preventDefault();
                    setJobInputFocused((current) => !current);
                  }}
                >
                  ▾
                </button>
                {jobInputFocused && visibleJobOptions.length > 0 && (
                  <div className="job-picker-menu">
                    {visibleJobOptions.map((option) => (
                      <button type="button" key={option.id} onMouseDown={(event) => event.preventDefault()} onClick={() => selectJobOption(option)}>
                        {option.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </label>
            <SelectField label="模式" value={config.modeId} options={options.modes} disabled={disabled} onChange={(value) => update("modeId", value)} />
            <SelectField
              label="声音"
              value={config.voiceProfileId}
              options={voiceProfiles}
              disabled={disabled}
              onChange={(value) => update("voiceProfileId", value)}
            />
          </div>
        </article>

        <div className="setup-flow" aria-label="面试链路">
          <span>选择</span>
          <span>分析</span>
          <span>雷达</span>
          <span>面试</span>
          <span>报告</span>
        </div>

        {onStart && (
          <div className="setup-actions">
            <button type="button" onClick={onStart} disabled={loading}>
              {loading ? "正在进入..." : "进入面试室"}
            </button>
            <details className="setup-health">
              <summary>系统状态</summary>
              <HealthPanel health={health ?? null} healthError={healthError} />
            </details>
            {error && <p className="error">{error}</p>}
          </div>
        )}
      </aside>

      <section className="setup-main">
      <article className="setup-card full-field">
        <div className="setup-card-head">
          <span>02</span>
          <div>
            <strong>岗位分析与简历</strong>
            <p>点击分析后才会更新雷达图、提问占比和推荐声音。</p>
          </div>
        </div>
        <div className="analysis-row">
          <button type="button" className="secondary-button" disabled={disabled || jdLoading} onClick={analyzeJd}>
            {jdLoading ? "正在分析岗位 JD 并生成配置..." : "开始分析岗位并生成面试配置"}
          </button>
          <label className="file-upload-field">
            <span>{resumeLoading ? "正在解析简历..." : config.resumeText ? "PDF 简历已解析，可重新上传" : "上传 PDF 简历"}</span>
            <input
              type="file"
              accept=".pdf,application/pdf"
              disabled={disabled || resumeLoading}
              onChange={(event) => void parseResumeFile(event.target.files?.[0] || null)}
            />
          </label>
        </div>
        {config.companyCard && (
          <>
            <button type="button" className="company-summary-strip" onClick={() => setCompanyDetailOpen(true)}>
              <span>
                <strong>{config.companyCard.companyName}</strong>
                <small>{verificationLabel(config.companyCard.verificationStatus)}</small>
              </span>
              <em>{config.companyCard.summary}</em>
              <b>查看</b>
            </button>
            {companyDetailOpen && (
              <CompanyInsightModal card={config.companyCard} onClose={() => setCompanyDetailOpen(false)} />
            )}
          </>
        )}
        {config.resumeText && (
          <button type="button" className="company-summary-strip" onClick={() => setResumeModalOpen(true)}>
            <span><strong>个人简历</strong><small>{config.resumeText.length} 字</small></span>
            <em>{config.resumeText.slice(0, 80)}{config.resumeText.length > 80 ? "…" : ""}</em>
            <b>查看</b>
          </button>
        )}
        {resumeModalOpen && config.resumeText && (
          <ResumeModal text={config.resumeText} pdfUrl={resumePdfUrl} onClose={() => setResumeModalOpen(false)} />
        )}
      </article>

      <article className="setup-card analysis-result-card">
        <div className="setup-card-head">
          <span>03</span>
          <div>
            <strong>JD 与配置分析</strong>
            <p>{analysisResult?.analysisSource === "deepseek" ? "已由 DeepSeek 生成配置建议。" : "未完成 AI 分析。"}</p>
          </div>
        </div>
        <p className="analysis-summary">{analysisResult?.jdSummary || "选择公司、岗位和模式后，点击上方按钮生成岗位 JD 摘要、能力权重和提问策略。"}</p>
        <div className="analysis-mini-grid">
          <MiniList title="核心要求" items={analysisResult?.coreRequirements} />
          <MiniList title="面试重点" items={analysisResult?.interviewFocus} />
          <MiniList title="调整依据" items={analysisResult?.analysisNotes} />
        </div>
      </article>

      <article className="setup-card full-field">
        <div className="setup-card-head">
          <span>04</span>
          <div>
            <strong>训练策略</strong>
            <p>拖动绿色圆点调整本轮重点；淡蓝色区域是岗位默认模型。</p>
          </div>
        </div>
        <div className="config-radar-grid">
          <ConfigRadarPanel
            title="能力重要性评分"
            subtitle="每个能力独立评分 1-10，不影响其他维度"
            disabled={disabled}
            maxValue={10}
            entries={competencies.map((item) => ({
              id: item.id,
              label: item.label,
              value: config.competencyWeights[item.id] ?? item.defaultWeight ?? 5,
              defaultValue: item.defaultWeight ?? 5,
            }))}
            onChange={(id, value) => updateCompetencyWeight(id, String(value))}
          />
          <ConfigRadarPanel
            title="提问方式占比"
            subtitle="决定面试官用什么方式追问"
            disabled={disabled}
            entries={questionStyles.map((item) => ({
              id: item.id,
              label: item.label,
              value: config.questionStyleWeights[item.id] ?? item.defaultWeight,
              defaultValue: item.defaultWeight,
            }))}
            onChange={(id, value) => updateQuestionStyleWeight(id, String(value))}
          />
        </div>
      </article>

      <article className="setup-card full-field">
        <div className="setup-card-head">
          <span>05</span>
          <div>
            <strong>面试官声音</strong>
            <p>基础音色、语气、语速、音调和音量会同时影响播报与提问措辞。</p>
          </div>
        </div>
        <div className="voice-control-grid">
        <SelectField
          label="语气"
          value={config.interviewerTone}
          options={[
            { id: "encouraging", label: "鼓励" },
            { id: "formal", label: "正式" },
            { id: "pressure", label: "压力" },
            { id: "relaxed", label: "轻松" },
            { id: "calm", label: "沉稳" },
          ]}
          disabled={disabled}
          onChange={(value) => update("interviewerTone", value)}
        />
        <label className="config-field">
          <span>语速</span>
          <select value={config.voiceRate} disabled={disabled} onChange={(event) => update("voiceRate", event.target.value)}>
            <option value="">跟随声音档位</option>
            <option value="-10%">偏慢</option>
            <option value="+0%">正常</option>
            <option value="+10%">偏快</option>
            <option value="+18%">很快</option>
          </select>
        </label>
        <label className="config-field">
          <span>音调</span>
          <select value={config.voicePitch} disabled={disabled} onChange={(event) => update("voicePitch", event.target.value)}>
            <option value="">跟随声音档位</option>
            <option value="-8Hz">偏低</option>
            <option value="+0Hz">正常</option>
            <option value="+4Hz">偏高</option>
            <option value="+8Hz">更高</option>
          </select>
        </label>
        <label className="config-field">
          <span>音量</span>
          <select value={config.voiceVolume} disabled={disabled} onChange={(event) => update("voiceVolume", event.target.value)}>
            <option value="">跟随声音档位</option>
            <option value="-20%">偏低</option>
            <option value="+0%">正常</option>
            <option value="+15%">偏高</option>
          </select>
        </label>
      </div>
      </article>
      </section>
    </section>
  );
}

function defaultCompetencyWeights(competencies: Array<{ id: string; defaultWeight?: number }>): Record<string, number> {
  // defaultWeight 现在是 1-10 的重要性评分
  return Object.fromEntries(competencies.map((item) => [item.id, item.defaultWeight ?? 5]));
}

function scoresToWeights(scores: Record<string, number>): Record<string, number> {
  const total = Object.values(scores).reduce((a, b) => a + b, 0) || 1;
  return Object.fromEntries(
    Object.entries(scores).map(([id, score]) => [id, Math.max(3, Math.min(60, Math.round(score / total * 100)))]),
  );
}

function primaryIdFromWeights(weights: Record<string, number>): string {
  return Object.entries(weights).sort((a, b) => b[1] - a[1])[0]?.[0] || "";
}

function verificationLabel(status: string): string {
  if (status === "verified") return "已核验";
  if (status === "partial") return "部分来源";
  return "待核验";
}

function MiniList({ title, items }: { title: string; items?: string[] }) {
  const safeItems = items?.filter(Boolean).slice(0, 5) ?? [];
  return (
    <div className="mini-list">
      <strong>{title}</strong>
      {safeItems.length > 0 ? (
        safeItems.map((item) => <span key={item}>{item}</span>)
      ) : (
        <span>等待分析</span>
      )}
    </div>
  );
}

function ConfigRadarPanel({
  title,
  subtitle,
  entries,
  disabled,
  onChange,
  maxValue = 50,
}: {
  title: string;
  subtitle: string;
  entries: Array<{ id: string; label: string; value: number; defaultValue: number }>;
  disabled: boolean;
  onChange: (id: string, value: number) => void;
  maxValue?: number;
}) {
  return (
    <article className="config-radar-card">
      <div className="radar-title">
        <strong>{title}</strong>
        <span>{subtitle}</span>
      </div>
      <RadarSvg
        entries={entries.map((item) => [item.id, item.label, item.value])}
        baselineEntries={entries.map((item) => [item.id, item.label, item.defaultValue])}
        maxValue={maxValue}
        className="config-radar-svg"
        disabled={disabled}
        onValueChange={onChange}
      />
      <div className="radar-legend">
        <span className="legend-default">默认模型</span>
        <span className="legend-current">你的选择，拖动圆点调整</span>
      </div>
    </article>
  );
}

function RadarSvg({
  entries,
  baselineEntries,
  maxValue,
  className = "",
  disabled = true,
  onValueChange,
}: {
  entries: Array<[string, string, number]>;
  baselineEntries?: Array<[string, string, number]>;
  maxValue: number;
  className?: string;
  disabled?: boolean;
  onValueChange?: (id: string, value: number) => void;
}) {
  const size = 260;
  const center = size / 2;
  const radius = 86;
  const safeEntries = entries.slice(0, 8);
  const points = radarPoints(safeEntries, center, radius, maxValue);
  const baselinePoints = baselineEntries ? radarPoints(baselineEntries.slice(0, 8), center, radius, maxValue) : [];
  const polygon = points.map((point) => `${point.x},${point.y}`).join(" ");
  const baselinePolygon = baselinePoints.map((point) => `${point.x},${point.y}`).join(" ");
  const gridLevels = [0.25, 0.5, 0.75, 1];

  function updateFromPointer(event: React.PointerEvent<SVGCircleElement>, index: number) {
    if (disabled || !onValueChange) return;
    const svg = event.currentTarget.ownerSVGElement;
    if (!svg) return;
    const point = svg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;
    const transformed = point.matrixTransform(svg.getScreenCTM()?.inverse());
    const angle = -Math.PI / 2 + (index / safeEntries.length) * Math.PI * 2;
    const axisX = Math.cos(angle);
    const axisY = Math.sin(angle);
    const dx = transformed.x - center;
    const dy = transformed.y - center;
    const projected = Math.max(0, Math.min(radius, dx * axisX + dy * axisY));
    const value = Math.round((projected / radius) * maxValue);
    onValueChange(safeEntries[index][0], Math.max(0, Math.min(maxValue, value)));
  }

  return (
    <svg className={className} viewBox={`0 0 ${size} ${size}`} role="img">
      {gridLevels.map((level) => {
        const gridPoints = safeEntries
          .map((_, index) => {
            const angle = -Math.PI / 2 + (index / safeEntries.length) * Math.PI * 2;
            return `${center + Math.cos(angle) * radius * level},${center + Math.sin(angle) * radius * level}`;
          })
          .join(" ");
        return <polygon key={level} points={gridPoints} className="radar-grid" />;
      })}
      {baselinePolygon && <polygon points={baselinePolygon} className="radar-baseline" />}
      {points.map((point, index) => (
        <line key={`${safeEntries[index][0]}-axis`} x1={center} y1={center} x2={point.axisX} y2={point.axisY} className="radar-axis" />
      ))}
      <polygon points={polygon} className="radar-area" />
      {points.map((point, index) => (
        <circle
          key={`${safeEntries[index][0]}-dot`}
          cx={point.x}
          cy={point.y}
          r={disabled ? 4 : 7}
          className={disabled ? "radar-dot" : "radar-dot draggable-dot"}
          onPointerDown={(event) => {
            event.currentTarget.setPointerCapture(event.pointerId);
            updateFromPointer(event, index);
          }}
          onPointerMove={(event) => {
            if (event.buttons) updateFromPointer(event, index);
          }}
        />
      ))}
      {points.map((point, index) => (
        <text
          key={`${safeEntries[index][0]}-label`}
          x={point.labelX}
          y={point.labelY}
          textAnchor={Math.cos(point.angle) > 0.2 ? "start" : Math.cos(point.angle) < -0.2 ? "end" : "middle"}
          dominantBaseline="middle"
          className="radar-label"
        >
          {safeEntries[index][1]}
        </text>
      ))}
    </svg>
  );
}

function radarPoints(entries: Array<[string, string, number]>, center: number, radius: number, maxValue: number) {
  return entries.map(([, , value], index) => {
    const angle = -Math.PI / 2 + (index / entries.length) * Math.PI * 2;
    const ratio = Math.max(0, Math.min(1, Number(value) / Math.max(1, maxValue)));
    return {
      x: center + Math.cos(angle) * radius * ratio,
      y: center + Math.sin(angle) * radius * ratio,
      axisX: center + Math.cos(angle) * radius,
      axisY: center + Math.sin(angle) * radius,
      labelX: center + Math.cos(angle) * (radius + 28),
      labelY: center + Math.sin(angle) * (radius + 28),
      angle,
    };
  });
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
  onReportComplete,
  onDisconnectIntent,
}: {
  room: string;
  health: HealthPayload | null;
  healthError: string;
  trainingConfig: TrainingConfig;
  trainingOptions: TrainingOptions;
  onTrainingConfigChange: (config: TrainingConfig) => void;
  onReportComplete: (report: InterviewReport, conversation: ConversationEntry[]) => void;
  onDisconnectIntent: (intent: DisconnectIntent) => void;
}) {
  const assistant = useVoiceAssistant();
  const livekitRoom = useRoomContext();
  const stateText = assistant.state || "connecting";
  const phaseRef = useRef<SessionPhase>("idle");
  const debugEventSeqRef = useRef(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const trainingConfigRef = useRef(trainingConfig);
  const interviewReportRef = useRef<InterviewReport | null>(null);
  const conversationRef = useRef<ConversationEntry[]>([]);
  const onReportCompleteRef = useRef(onReportComplete);
  const onDisconnectIntentRef = useRef(onDisconnectIntent);
  const [partialTranscript, setPartialTranscript] = useState("");
  const [finalTranscript, setFinalTranscript] = useState("");
  const [assistantText, setAssistantText] = useState("");
  const [assistantState, setAssistantState] = useState("已进入房间，点击开始会话");
  const [debugEvents, setDebugEvents] = useState<DebugEvent[]>([]);
  const [plannerTraces, setPlannerTraces] = useState<PlannerTrace[]>([]);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [conversation, setConversation] = useState<ConversationEntry[]>([]);
  const [livekitConnected, setLivekitConnected] = useState(false);
  const [phase, setPhaseState] = useState<SessionPhase>("idle");
  const [showDebug, setShowDebug] = useState(false);
  const [lastVoiceLevel, setLastVoiceLevel] = useState(0);
  const [interviewReport, setInterviewReport] = useState<InterviewReport | null>(null);
  const [ragEnabled, setRagEnabled] = useState(Boolean(health?.proFollowupRagEnabled));
  const [ragSwitching, setRagSwitching] = useState(false);
  const activeJobLabel =
    trainingConfig.customJobTitle ||
    trainingOptions.jobs.find((item) => item.id === trainingConfig.jobId)?.label ||
    "目标岗位";

  useEffect(() => {
    trainingConfigRef.current = trainingConfig;
  }, [trainingConfig]);

  useEffect(() => {
    if (typeof health?.proFollowupRagEnabled === "boolean") {
      setRagEnabled(health.proFollowupRagEnabled);
    }
  }, [health?.proFollowupRagEnabled]);

  useEffect(() => {
    interviewReportRef.current = interviewReport;
  }, [interviewReport]);

  useEffect(() => {
    conversationRef.current = conversation;
  }, [conversation]);

  useEffect(() => {
    onReportCompleteRef.current = onReportComplete;
  }, [onReportComplete]);

  useEffect(() => {
    onDisconnectIntentRef.current = onDisconnectIntent;
  }, [onDisconnectIntent]);

  function setPhase(next: SessionPhase) {
    phaseRef.current = next;
    setPhaseState(next);
    if (next !== "listening") setLastVoiceLevel(0);
  }

  function addDebugEvent(event: string) {
    debugEventSeqRef.current += 1;
    const id = `${Date.now()}-${debugEventSeqRef.current}`;
    setDebugEvents((current) =>
      [
        {
          id,
          text: `${new Date().toLocaleTimeString()} ${event}`,
        },
        ...current,
      ].slice(0, 80),
    );
  }

  function addPlannerTrace(event: {
    plannerMode?: string;
    followupMode?: TrainingConfig["followupMode"];
    answerGapTypes?: string[];
    bestNextProbeTarget?: string;
    selectedStrategyId?: string;
    selectedStrategyTitle?: string;
    plannerTimings?: PlannerTrace["timings"];
    ragEnabled?: boolean;
    ragUsed?: boolean;
    ragRawCount?: number;
    ragFilteredCount?: number;
    ragMinScore?: number;
    ragTimeoutMs?: number;
    ragEmbeddingMs?: number;
    ragSearchMs?: number;
    ragRerankMs?: number;
    ragCacheHit?: boolean;
    ragError?: string;
    ragSourceTitles?: string[];
    ragMatches?: PlannerTrace["ragMatches"];
    ragQuery?: PlannerTrace["ragQuery"];
    plannerError?: string;
  }) {
    debugEventSeqRef.current += 1;
    const time = new Date().toLocaleTimeString();
    const id = `planner-${Date.now()}-${debugEventSeqRef.current}`;
    setPlannerTraces((current) =>
      [
        {
          id,
          time,
          mode: event.plannerMode,
          followupMode: event.followupMode,
          gapTypes: event.answerGapTypes || [],
          strategyId: event.selectedStrategyId,
          strategyTitle: event.selectedStrategyTitle,
          target: event.bestNextProbeTarget,
          timings: event.plannerTimings,
          ragEnabled: event.ragEnabled,
          ragUsed: event.ragUsed,
          ragRawCount: event.ragRawCount,
          ragFilteredCount: event.ragFilteredCount,
          ragMinScore: event.ragMinScore,
          ragTimeoutMs: event.ragTimeoutMs,
          ragEmbeddingMs: event.ragEmbeddingMs,
          ragSearchMs: event.ragSearchMs,
          ragRerankMs: event.ragRerankMs,
          ragCacheHit: event.ragCacheHit,
          ragError: event.ragError,
          ragSources: event.ragSourceTitles || [],
          ragMatches: event.ragMatches || [],
          ragQuery: event.ragQuery,
          error: event.plannerError,
        },
        ...current,
      ].slice(0, 20),
    );
  }

  async function toggleRagEnabled() {
    const nextEnabled = !ragEnabled;
    setRagSwitching(true);
    try {
      const response = await fetch(`${API_BASE}/debug/rag`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: nextEnabled }),
      });
      if (!response.ok) throw new Error(await readErrorDetail(response));
      const payload = (await response.json()) as { proFollowupRagEnabled?: boolean };
      const enabled = Boolean(payload.proFollowupRagEnabled);
      setRagEnabled(enabled);
      addDebugEvent(`RAG 总开关已${enabled ? "开启" : "关闭"}，下一轮追问生效`);
    } catch (error) {
      addDebugEvent(`RAG 总开关切换失败：${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setRagSwitching(false);
    }
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
    const primaryCompetencyId = primaryIdFromWeights(trainingConfig.competencyWeights) || trainingConfig.competencyId;
    // 将前端 1-10 评分转为后端调度用的百分比权重
    const normalizedWeights = scoresToWeights(trainingConfig.competencyWeights);
    await sendControl("start_session", {
      config: {
        ...trainingConfig,
        competencyId: primaryCompetencyId,
        competencyWeights: normalizedWeights,
        companyCard: trainingConfig.companyCard,
      },
    });
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
    audioRef.current?.pause();
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
    await setMicEnabled(false);
    await sendControl("assistant_done");
    await sendControl("end_session");
  }

  async function resumeListening(reason: string) {
    if (phaseRef.current === "ended") return;
    if (interviewReportRef.current) return;
    setPhase("listening");
    setAssistantState(reason);
    await setMicEnabled(true);
  }

  async function playTts(text: string) {
    const currentConfig = trainingConfigRef.current;
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
        body: JSON.stringify({
          text,
          voiceProfileId: currentConfig.voiceProfileId,
          rate: currentConfig.voiceRate || undefined,
          pitch: currentConfig.voicePitch || undefined,
          volume: currentConfig.voiceVolume || undefined,
        }),
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
        traceReason?: string;
        modeId?: string;
        modeLabel?: string;
        competencyId?: string;
        competencyLabel?: string;
        strategyId?: string;
        strategyLabel?: string;
        companyVerificationStatus?: string;
        voiceProfileId?: string;
        interviewerTone?: string;
        capabilityId?: string;
        capabilityName?: string;
        capabilityWeight?: number;
        questionStyleId?: string;
        questionStyleName?: string;
        questionStyleWeight?: number;
        coverageRatio?: number;
        missingEvidence?: string[];
        reason?: string;
        plannerMode?: string;
        followupMode?: TrainingConfig["followupMode"];
        professionalEnabled?: boolean;
        answerGapTypes?: string[];
        answerGapConfidence?: number;
        answerGapFallback?: boolean;
        answerQualitySummary?: string;
        bestNextProbeTarget?: string;
        selectedStrategyId?: string;
        selectedStrategyTitle?: string;
        ragEnabled?: boolean;
        ragUsed?: boolean;
        ragRawCount?: number;
        ragFilteredCount?: number;
        ragMinScore?: number;
        ragTimeoutMs?: number;
        ragEmbeddingMs?: number;
        ragSearchMs?: number;
        ragRerankMs?: number;
        ragCacheHit?: boolean;
        ragError?: string;
        ragSourceTitles?: string[];
        plannerTimings?: { gapMs?: number; ragMs?: number; totalMs?: number };
        ragQuery?: {
          text?: string;
          strategyCategory?: string;
          roleFamily?: string;
          competencyArchetypes?: string[];
          evidenceCategories?: string[];
          limit?: number;
        };
        ragMatches?: Array<{ title?: string; score?: number; ordinal?: number; sourceId?: string; preview?: string }>;
        plannerError?: string;
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
      if (event.type === "session.configured") {
        addDebugEvent(
          `配置已应用：${event.modeLabel || event.modeId} / ${event.competencyLabel || event.competencyId} / ${
            event.strategyLabel || event.strategyId
          } / 追问档位=${FOLLOWUP_MODES.find((item) => item.id === event.followupMode)?.label || event.followupMode || "极速稳定"} / ${event.voiceProfileId || "默认声音"} / ${event.interviewerTone || "默认语气"}`,
        );
      }
      if (event.type === "question.plan") {
        addDebugEvent(
          `下一问计划：${event.capabilityName || event.capabilityId || "unknown"}(${event.capabilityWeight ?? 0}%) / ${
            event.questionStyleName || event.questionStyleId || "unknown"
          }(${event.questionStyleWeight ?? 0}%) / 覆盖率=${Math.round((event.coverageRatio ?? 0) * 100)}% / 缺口=${
            event.missingEvidence?.slice(0, 2).join("、") || "暂无"
          } / ${event.traceReason || ""}`,
        );
        if (event.plannerMode) {
          addDebugEvent(
            `专业追问：mode=${event.plannerMode} / followup=${event.followupMode || "-"} / gap=${event.answerGapTypes?.join(",") || "none"} / strategy=${
              event.selectedStrategyId || "none"
            } / ragEnabled=${event.ragEnabled === false ? "off" : "on"} / rag=${
              event.ragUsed ? event.ragSourceTitles?.slice(0, 2).join("、") || "命中" : "未使用"
            } / raw=${
              event.ragRawCount ?? "-"
            } / filtered=${event.ragFilteredCount ?? "-"} / cache=${event.ragCacheHit ? "hit" : "miss"}${
              event.ragError ? ` / ragError=${event.ragError}` : event.plannerError ? ` / error=${event.plannerError}` : ""
            }`,
          );
        }
      }
      if (event.type === "planner.trace") {
        addPlannerTrace(event);
        const timings = event.plannerTimings;
        addDebugEvent(
          `Planner耗时：total=${timings?.totalMs ?? "-"}ms / gap=${timings?.gapMs ?? "-"}ms / rag=${
            timings?.ragMs ?? "-"
          }ms / embed=${event.ragEmbeddingMs ?? "-"}ms / search=${event.ragSearchMs ?? "-"}ms / mode=${event.plannerMode || "unknown"}`,
        );
        addDebugEvent(
          `Planner决策：gap=${event.answerGapTypes?.join(",") || "none"} / strategy=${
            event.selectedStrategyId || "none"
          } / target=${event.bestNextProbeTarget || "无"}`,
        );
        if (event.ragQuery) {
          addDebugEvent(
            `RAG查询：category=${event.ragQuery.strategyCategory || "none"} / evidence=${
              event.ragQuery.evidenceCategories?.join(",") || "none"
            } / limit=${event.ragQuery.limit ?? "-"} / minScore=${event.ragMinScore ?? "-"} / timeout=${event.ragTimeoutMs ?? "-"}ms`,
          );
        }
        if (event.ragMatches?.length) {
          addDebugEvent(
            `RAG命中：${event.ragMatches
              .slice(0, 3)
              .map((item) => `${item.title || "unknown"}(${item.score ?? 0})`)
              .join(" / ")}`,
          );
        } else if (event.professionalEnabled) {
          addDebugEvent(
            `RAG命中：无 / raw=${event.ragRawCount ?? "-"} / filtered=${event.ragFilteredCount ?? "-"}${
              event.ragError ? ` / ${event.ragError}` : event.plannerError ? ` / ${event.plannerError}` : ""
            }`,
          );
        }
      }
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
        setPhase("ended");
        void setMicEnabled(false);
        setAssistantState("评分和训练建议已生成");
        addDebugEvent("已收到面试评分报告");
        if (event.report) {
          onDisconnectIntentRef.current("report");
          onReportCompleteRef.current(event.report, conversationRef.current);
          window.setTimeout(() => void livekitRoom.disconnect(), 80);
        }
      }
      if (event.type === "assistant.text.delta") setAssistantText((current) => current + (event.text || ""));
      if (event.type === "assistant.text.done") {
        const text = event.text || "";
        setAssistantText(text);
        if (phaseRef.current === "ended" || interviewReportRef.current) {
          addConversationEntry("assistant", text);
          return;
        }
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

    function onReconnecting() {
      addDebugEvent("LiveKit 正在自动重连");
      setLivekitConnected(false);
      setAssistantState("网络波动，正在恢复连接...");
    }

    function onReconnected() {
      addDebugEvent("LiveKit 已自动恢复连接");
      setLivekitConnected(true);
      setAssistantState("连接已恢复，可以继续面试");
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
    livekitRoom.on(RoomEvent.Reconnecting, onReconnecting);
    livekitRoom.on(RoomEvent.Reconnected, onReconnected);
    livekitRoom.on(RoomEvent.Disconnected, onDisconnected);
    livekitRoom.on(RoomEvent.ParticipantConnected, onParticipantConnected);
    livekitRoom.on(RoomEvent.TrackSubscribed, onTrackSubscribed);
    if (livekitRoom.state === "connected") onConnected();
    return () => {
      livekitRoom.off(RoomEvent.DataReceived, onData);
      livekitRoom.off(RoomEvent.Connected, onConnected);
      livekitRoom.off(RoomEvent.Reconnecting, onReconnecting);
      livekitRoom.off(RoomEvent.Reconnected, onReconnected);
      livekitRoom.off(RoomEvent.Disconnected, onDisconnected);
      livekitRoom.off(RoomEvent.ParticipantConnected, onParticipantConnected);
      livekitRoom.off(RoomEvent.TrackSubscribed, onTrackSubscribed);
      audioRef.current?.pause();
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    };
  }, [livekitRoom]);

  const controlsDisabled = phase === "listening" || phase === "thinking" || phase === "speaking";

  return (
    <main className={showDebug ? "room-shell debug-layout" : "room-shell call-layout"}>
      <header className="room-header call-header">
        <div>
          <p className="eyebrow">AI INTERVIEW CALL</p>
          <h1>模拟面试系统</h1>
        </div>
        <div className="header-actions">
          <span className="pill">{livekitConnected ? "房间已连接" : "正在连接"}</span>
          <button type="button" className="ghost-button" onClick={() => {
            onDisconnectIntentRef.current("manual");
            void livekitRoom.disconnect();
          }}>
            返回配置
          </button>
          <button type="button" className="ghost-button" onClick={() => setShowDebug((current) => !current)}>
            {showDebug ? "返回通话" : "调试台"}
          </button>
        </div>
      </header>

      {!showDebug && (
        <section className="call-stage" data-phase={phase}>
          <div className="call-backdrop" />
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

          {interviewReport && <InterviewReportSummaryCard report={interviewReport} onOpen={() => setReportModalOpen(true)} compact />}

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
          <TrainingDock
            config={trainingConfig}
            options={trainingOptions}
            disabled={controlsDisabled}
            onChange={onTrainingConfigChange}
          />
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
                {conversation.map((item, index) => (
                  <li key={`${item.time}-${item.role}-${index}`}>
                    <span>{item.role === "candidate" ? "你" : "AI"}</span>
                    <p>{item.text}</p>
                    <time>{item.time}</time>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {interviewReport && <InterviewReportSummaryCard report={interviewReport} onOpen={() => setReportModalOpen(true)} />}

          <details className="debug-card" open>
            <summary>Planner / RAG 追问调试（保留最近 {plannerTraces.length} 条）</summary>
            <div className="debug-toolbar">
              <div>
                <strong>RAG 总开关</strong>
                <span>{ragEnabled ? "已开启：追问会检索方法论库" : "已关闭：追问只使用策略卡和 answer_gap"}</span>
              </div>
              <button type="button" className={ragEnabled ? "secondary-button" : ""} disabled={ragSwitching} onClick={toggleRagEnabled}>
                {ragSwitching ? "切换中" : ragEnabled ? "关闭 RAG" : "开启 RAG"}
              </button>
            </div>
            {plannerTraces.length === 0 ? (
              <p>暂无 planner trace。完成一轮回答后，这里会显示 answer_gap、策略卡、RAG 查询和命中资料。</p>
            ) : (
              <div className="planner-trace-list">
                {plannerTraces.map((trace) => (
                  <article key={trace.id} className="planner-trace-item">
                    <div className="planner-trace-head">
                      <strong>{trace.time}</strong>
                      <span>{trace.mode || "unknown"}</span>
                      <span>followup={trace.followupMode || "-"}</span>
                      <span>{trace.timings?.totalMs ?? "-"}ms</span>
                    </div>
                    <p>
                      <b>gap</b>：{trace.gapTypes.join(", ") || "none"}
                    </p>
                    <p>
                      <b>strategy</b>：{trace.strategyId || "none"}
                      {trace.strategyTitle ? ` / ${trace.strategyTitle}` : ""}
                    </p>
                    <p>
                      <b>target</b>：{trace.target || "无"}
                    </p>
                    <p>
                      <b>timing</b>：gap={trace.timings?.gapMs ?? "-"}ms / rag={trace.timings?.ragMs ?? "-"}ms / total=
                      {trace.timings?.totalMs ?? "-"}ms
                    </p>
                    <p>
                      <b>rag stats</b>：raw={trace.ragRawCount ?? "-"} / filtered={trace.ragFilteredCount ?? "-"} / minScore=
                      {trace.ragMinScore ?? "-"} / timeout={trace.ragTimeoutMs ?? "-"}ms / enabled=
                      {trace.ragEnabled === false ? "off" : "on"} / cache={trace.ragCacheHit ? "hit" : "miss"}
                    </p>
                    <p>
                      <b>rag split</b>：embedding={trace.ragEmbeddingMs ?? "-"}ms / search={trace.ragSearchMs ?? "-"}ms / rerank=
                      {trace.ragRerankMs ?? "-"}ms
                    </p>
                    <p>
                      <b>rag query</b>：category={trace.ragQuery?.strategyCategory || "none"} / evidence=
                      {trace.ragQuery?.evidenceCategories?.join(",") || "none"} / limit={trace.ragQuery?.limit ?? "-"}
                    </p>
                    <p>
                      <b>rag used</b>：{trace.ragUsed ? "是" : "否"}
                      {trace.ragSources.length ? ` / ${trace.ragSources.join(" / ")}` : ""}
                    </p>
                    {trace.ragMatches.length ? (
                      <ul className="planner-rag-matches">
                        {trace.ragMatches.slice(0, 4).map((match, index) => (
                          <li key={`${trace.id}-match-${index}`}>
                            {match.title || "unknown"} score={match.score ?? "-"} ordinal={match.ordinal ?? "-"}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                    {trace.ragError ? <p className="planner-trace-error">rag error：{trace.ragError}</p> : null}
                    {trace.error ? <p className="planner-trace-error">error：{trace.error}</p> : null}
                  </article>
                ))}
              </div>
            )}
          </details>

          <details className="debug-card" open>
            <summary>调试事件</summary>
            {debugEvents.length === 0 ? (
              <p>暂无事件。如果一直为空，说明前端还没连上 LiveKit 或没有收到 agent 数据。</p>
            ) : (
              <ul>
                {debugEvents.map((event, index) => (
                  <li key={`${event.id}-${index}`}>{event.text}</li>
                ))}
              </ul>
            )}
          </details>
        </section>
      )}

      {interviewReport && reportModalOpen && (
        <InterviewReportModal
          report={interviewReport}
          title={`${trainingConfig.companyCard?.companyName || trainingConfig.companyName || "模拟面试"} · ${activeJobLabel}`}
          subtitle={`回答 ${interviewReport.turn_count ?? 0} 轮 · 证据覆盖 ${Math.round((interviewReport.coverage_ratio ?? 0) * 100)}%`}
          onClose={() => setReportModalOpen(false)}
        />
      )}

      <footer className={showDebug ? "controls" : "controls compact-controls"}>
        <ControlBar variation="minimal" controls={{ camera: false, screenShare: false }} />
      </footer>
    </main>
  );
}

const ABILITY_LABELS: Record<string, string> = {
  answer_structure: "回答结构",
  experience_evidence: "经历证据",
  job_understanding: "岗位理解",
  project_delivery: "项目推进",
  expression_clarity: "表达清晰",
};

type AbilityRadarEntry = {
  id: string;
  label: string;
  score: number;
};

function reportQualityText(report: InterviewReport): string {
  if (report.report_quality === "insufficient_sample") return "样本不足，暂不生成正式评分";
  if (report.report_quality === "evaluation_unavailable") return "评分模型不可用";
  if (report.report_quality === "fallback") return "非正式报告，可信度较低";
  return "正式评分报告";
}

function scoreText(score: number | null | undefined): string {
  return typeof score === "number" ? `${score}/10` : "暂不评分";
}

function useSimulatedProgress(active: boolean) {
  const [progress, setProgress] = useState(0);
  useEffect(() => {
    if (!active) {
      return;
    }
    setProgress(8);
    const startedAt = Date.now();
    const interval = window.setInterval(() => {
      const elapsed = Date.now() - startedAt;
      const next = Math.min(88, 8 + Math.round(elapsed / 260));
      setProgress((current) => Math.max(current, next));
    }, 280);
    return () => window.clearInterval(interval);
  }, [active]);
  return [progress, setProgress] as const;
}

function JdAnalysisProgress({ active, progress }: { active: boolean; progress: number }) {
  const safeProgress = Math.max(0, Math.min(100, progress));
  return (
    <div className="jd-progress-card compact-jd-progress" aria-live="polite" data-active={active} aria-label="岗位 JD 分析进度">
      <div className="jd-progress-track">
        <i style={{ width: `${safeProgress}%` }} />
      </div>
    </div>
  );
}

function InterviewReportSummaryCard({
  report,
  onOpen,
  compact = false,
}: {
  report: InterviewReport;
  onOpen: () => void;
  compact?: boolean;
}) {
  const scoredDimensions = (report.dimensions ?? []).filter((item) => typeof item.score === "number");
  const averageScore =
    scoredDimensions.length > 0
      ? Math.round((scoredDimensions.reduce((sum, item) => sum + Number(item.score), 0) / scoredDimensions.length) * 10) / 10
      : null;
  const strongest = scoredDimensions.reduce<(typeof scoredDimensions)[number] | null>(
    (best, item) => (best && Number(best.score) >= Number(item.score) ? best : item),
    null,
  );
  const weakest = scoredDimensions.reduce<(typeof scoredDimensions)[number] | null>(
    (worst, item) => (worst && Number(worst.score) <= Number(item.score) ? worst : item),
    null,
  );

  return (
    <article className={compact ? "report-summary-strip compact-report-summary-strip" : "report-summary-strip"}>
      <div className="report-summary-copy">
        <p className="label">面试报告</p>
        <h3>{reportQualityText(report)}</h3>
        <p>{report.summary || "报告已生成，点击查看完整岗位能力雷达图、评分维度和训练计划。"}</p>
        <div className="report-summary-meta">
          <span>平均 {averageScore ? `${averageScore}/10` : "暂不评分"}</span>
          <span>岗位匹配 {scoreText(report.role_fit?.score)}</span>
          <span>覆盖 {Math.round((report.coverage_ratio ?? 0) * 100)}%</span>
        </div>
      </div>
      {!compact && (
        <div className="report-summary-insights">
          <span>优势：{strongest?.name || "等待更多样本"}</span>
          <span>优先补强：{weakest?.name || report.main_weakness || "等待更多样本"}</span>
        </div>
      )}
      <button type="button" onClick={onOpen}>查看完整报告</button>
    </article>
  );
}

function InterviewReportModal({
  report,
  title,
  subtitle,
  onClose,
}: {
  report: InterviewReport;
  title: string;
  subtitle?: string;
  onClose: () => void;
}) {
  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  return (
    <div className="company-modal-backdrop report-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="company-modal report-modal" role="dialog" aria-modal="true" aria-label="完整面试报告" onMouseDown={(event) => event.stopPropagation()}>
        <header>
          <div>
            <span>INTERVIEW REPORT</span>
            <h2>{title}</h2>
            <p>{subtitle || "完整评价报告包含岗位能力雷达、分项证据、岗位匹配和后续训练计划。"}</p>
          </div>
          <button type="button" aria-label="关闭面试报告" onClick={onClose}>×</button>
        </header>
        <div className="company-modal-meta">
          <span>{reportQualityText(report)}</span>
          <span>回答 {report.turn_count ?? 0} 轮</span>
          <span>证据覆盖 {Math.round((report.coverage_ratio ?? 0) * 100)}%</span>
        </div>
        <div className="report-modal-body">
          <InterviewReportPanel report={report} />
        </div>
      </section>
    </div>
  );
}

function InterviewReportPanel({ report, compact = false }: { report: InterviewReport; compact?: boolean }) {
  const dimensionAbilityEntries: AbilityRadarEntry[] = (report.dimensions ?? [])
    .filter((item) => typeof item.score === "number")
    .map((item) => ({
      id: item.id || item.name,
      label: item.name || ABILITY_LABELS[item.id] || item.id,
      score: Math.max(1, Math.min(10, Number(item.score))),
    }));
  const abilityEntries: AbilityRadarEntry[] =
    dimensionAbilityEntries.length > 0
      ? dimensionAbilityEntries
      : Object.entries(report.ability_model ?? {}).map(([id, score]) => ({
          id,
          label: ABILITY_LABELS[id] ?? id,
          score: Math.max(1, Math.min(10, Number(score))),
        }));
  const tasks = report.training_plan?.tasks ?? [];

  return (
    <section className={compact ? "report-card compact-report" : "report-card"}>
      <div className="history-title">
        <p className="label">评分报告</p>
        <span>{reportQualityText(report)}</span>
      </div>
      <div className="report-meta">
        <span>回答轮次：{report.turn_count ?? 0}</span>
        <span>证据覆盖：{Math.round((report.coverage_ratio ?? 0) * 100)}%</span>
      </div>
      <p className="report-summary">{report.summary || "本轮评分已生成。"}</p>

      <div className="fit-grid">
        {report.company_fit_bonus && (
          <article className="fit-card">
            <div className="fit-head">
              <strong>公司理解加分项</strong>
              <span>{scoreText(report.company_fit_bonus.score)}</span>
            </div>
            <p>{report.company_fit_bonus.reason || "暂无公司理解评价。"}</p>
            {!compact && report.company_fit_bonus.verification_note && <small>{report.company_fit_bonus.verification_note}</small>}
            {!compact && report.company_fit_bonus.talking_points && report.company_fit_bonus.talking_points.length > 0 && (
              <div className="mini-tags">
                {report.company_fit_bonus.talking_points.slice(0, 6).map((point) => (
                  <span key={point}>{point}</span>
                ))}
              </div>
            )}
          </article>
        )}
        {report.role_fit && (
          <article className="fit-card">
            <div className="fit-head">
              <strong>岗位匹配度</strong>
              <span>{scoreText(report.role_fit.score)}</span>
            </div>
            <p>{report.role_fit.reason || "暂无岗位匹配评价。"}</p>
            {!compact && report.role_fit.risk && <small>风险：{report.role_fit.risk}</small>}
            {!compact && report.role_fit.focus_dimensions && report.role_fit.focus_dimensions.length > 0 && (
              <div className="mini-tags">
                {report.role_fit.focus_dimensions.slice(0, 6).map((item) => (
                  <span key={item}>{item}</span>
                ))}
              </div>
            )}
          </article>
        )}
      </div>

      {abilityEntries.length > 0 && (
        <>
          <AbilityRadar entries={abilityEntries} />
          <div className="ability-bars" aria-label="能力模型">
            {abilityEntries.map(({ id, label, score }, index) => (
              <div key={`${id}-${index}`} className="ability-row">
                <span>{label}</span>
                <div className="ability-track">
                  <i style={{ width: `${Math.max(8, Math.min(100, (score / 10) * 100))}%` }} />
                </div>
                <b>{score}/10</b>
              </div>
            ))}
          </div>
        </>
      )}

      {!compact && report.evidence_gaps && report.evidence_gaps.length > 0 && (
        <div className="gap-card">
          <b>证据缺口</b>
          <ul>
            {report.evidence_gaps.map((gap) => (
              <li key={gap}>{gap}</li>
            ))}
          </ul>
        </div>
      )}

      {!compact && report.dimensions && report.dimensions.length > 0 && (
        <div className="score-grid">
          {report.dimensions.map((item) => (
            <article key={item.id} className="score-card">
              <div className="score-head">
                <strong>{item.name}</strong>
                <span>{scoreText(item.score)}{item.level ? ` · ${item.level}` : ""}</span>
              </div>
              <p>{item.reason}</p>
              <p>
                <b>依据：</b>
                {item.evidence}
              </p>
              {item.risk && (
                <p>
                  <b>风险：</b>
                  {item.risk}
                </p>
              )}
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
          <b>训练主题：</b>
          {report.training_plan?.theme || "暂无"}
        </p>
        {report.training_plan?.goal && (
          <p>
            <b>训练目标：</b>
            {report.training_plan.goal}
          </p>
        )}
        {tasks.length > 0 ? (
          <div className="task-list">
            {tasks.map((task, index) => (
              <article key={`${task.name ?? "task"}-${index}`}>
                <strong>{task.name || `训练任务 ${index + 1}`}</strong>
                <p>{task.exercise || "暂无练习题"}</p>
                {!compact && <p>{task.method || "暂无训练方法"}</p>}
                {!compact && task.success_criteria && <small>达标：{task.success_criteria}</small>}
              </article>
            ))}
          </div>
        ) : (
          <p>
            <b>练习题：</b>
            {report.training_plan?.exercise || "暂无"}
          </p>
        )}
        {!compact && <PhaseTrainingPlan plan={report.training_plan} />}
        {!compact && report.training_plan?.next_interview_focus && (
          <p>
            <b>下一轮重点：</b>
            {report.training_plan.next_interview_focus}
          </p>
        )}
        {!compact && report.training_plan?.duration_minutes ? <p>建议训练时长：{report.training_plan.duration_minutes} 分钟</p> : null}
      </div>
    </section>
  );
}

function AbilityRadar({ entries }: { entries: AbilityRadarEntry[] }) {
  const size = 260;
  const center = size / 2;
  const radius = 86;
  const normalizedEntries = entries.slice(0, 8);
  if (normalizedEntries.length < 3) {
    return (
      <div className="radar-card" aria-label="岗位能力雷达图">
        <div className="radar-title">
          <strong>岗位能力雷达图</strong>
          <span>10 分制</span>
        </div>
        <p className="report-summary">当前可评分维度不足，雷达图暂不绘制；下方能力条仍会展示已有岗位维度评分。</p>
      </div>
    );
  }
  const points = normalizedEntries.map(({ score }, index) => {
    const angle = -Math.PI / 2 + (index / normalizedEntries.length) * Math.PI * 2;
    const value = Math.max(0, Math.min(10, Number(score))) / 10;
    return {
      x: center + Math.cos(angle) * radius * value,
      y: center + Math.sin(angle) * radius * value,
      axisX: center + Math.cos(angle) * radius,
      axisY: center + Math.sin(angle) * radius,
      labelX: center + Math.cos(angle) * (radius + 28),
      labelY: center + Math.sin(angle) * (radius + 28),
      angle,
    };
  });
  const polygon = points.map((point) => `${point.x},${point.y}`).join(" ");
  const gridLevels = [0.25, 0.5, 0.75, 1];

  return (
    <div className="radar-card" aria-label="能力雷达图">
      <div className="radar-title">
        <strong>能力模型雷达图</strong>
        <span>10 分制</span>
      </div>
      <svg viewBox={`0 0 ${size} ${size}`} role="img">
        {gridLevels.map((level) => {
          const gridPoints = normalizedEntries
            .map((_, index) => {
              const angle = -Math.PI / 2 + (index / normalizedEntries.length) * Math.PI * 2;
              return `${center + Math.cos(angle) * radius * level},${center + Math.sin(angle) * radius * level}`;
            })
            .join(" ");
          return <polygon key={level} points={gridPoints} className="radar-grid" />;
        })}
        {points.map((point, index) => (
          <line key={`${normalizedEntries[index].id}-${index}-axis`} x1={center} y1={center} x2={point.axisX} y2={point.axisY} className="radar-axis" />
        ))}
        <polygon points={polygon} className="radar-area" />
        {points.map((point, index) => (
          <circle key={`${normalizedEntries[index].id}-${index}-dot`} cx={point.x} cy={point.y} r="4" className="radar-dot" />
        ))}
        {points.map((point, index) => (
          <text
            key={`${normalizedEntries[index].id}-${index}-label`}
            x={point.labelX}
            y={point.labelY}
            textAnchor={Math.cos(point.angle) > 0.2 ? "start" : Math.cos(point.angle) < -0.2 ? "end" : "middle"}
            dominantBaseline="middle"
            className="radar-label"
          >
            {normalizedEntries[index].label}
          </text>
        ))}
      </svg>
    </div>
  );
}

function PhaseTrainingPlan({ plan }: { plan?: InterviewReport["training_plan"] }) {
  const phases = [
    { title: "7 天", items: plan?.seven_day_plan ?? [] },
    { title: "14 天", items: plan?.fourteen_day_plan ?? [] },
    { title: "30 天", items: plan?.thirty_day_plan ?? [] },
  ];
  if (!phases.some((phase) => phase.items.length > 0)) return null;
  return (
    <div className="phase-plan">
      {phases.map((phase) => (
        <article key={phase.title}>
          <strong>{phase.title}</strong>
          <ul>
            {phase.items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      ))}
    </div>
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

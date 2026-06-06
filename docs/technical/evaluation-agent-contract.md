# 评价 Agent 对接契约与当前项目数据流

本文档只描述与“评价 Agent”相关的对接内容，目标读者是评价 Agent 的实现者、后端编排方、以及负责把评价结果接回报告页的开发者。

文档回答这些问题：

- 当前项目已经实现了哪些和评价相关的工作流。
- 这些现场生成的数据如何沉淀到 `SessionState`。
- 公司资料、岗位模型、追问记录、问答记录、证据快照分别怎么传给评价 Agent。
- `EvaluationRequest` / `EvaluationResponse` 的 TypeScript 数据结构。
- 为什么 `questionTrace` 是追问 Agent 和评价 Agent 之间的关键桥梁。
- 当前项目已有字段如何映射到这套契约。

## 1. 评价 Agent 的职责边界

评价 Agent 的职责是：**基于主流程沉淀下来的证据包，生成面试复盘报告**。

评价 Agent 应该做：

- 根据岗位模型和评分 Rubric 判断候选人表现。
- 根据追问记录判断系统问了什么、为什么问、候选人是否有机会补证据。
- 根据问答记录提取可引用证据。
- 根据证据快照判断哪些能力已经被覆盖，哪些仍缺证据。
- 输出维度评分、证据依据、风险、改进建议、训练计划。
- 样本不足时返回 `insufficient_sample`，不要硬打低分。

评价 Agent 不应该做：

- 不重新搜索公司资料。
- 不重新生成岗位模型。
- 不决定下一题问什么。
- 不决定面试是否结束。
- 不编造用户经历、简历项目、数据指标、公司事实。
- 不把 ASR 漏字、断网、中断等技术问题直接判断成用户能力差。

核心边界：

```text
追问逻辑负责采证。
评价 Agent 负责基于采证结果评分。
评价 Agent 不控制追问，但必须读取追问 trace，否则评分不可信。
```

## 2. 当前项目已经实现的相关工作流

当前项目在 `livekit-interview-spike` 中已经具备一条完整的模拟面试链路。

### 2.1 配置阶段：公司资料生成

入口：

- 前端：`/company-card`
- 后端：`server/token_server.py` 的 `company_card`
- 公司搜索：`server/interview/company_search.py`
- 公司资料抽取：`server/interview/company_intel.py`

当前行为：

1. 用户在配置页输入公司名称。
2. 前端请求 `/company-card`。
3. 后端根据公司名称做网页搜索和来源抽取。
4. 生成结构化 `CompanyCard`。
5. 前端写入 `trainingConfig.companyCard`。
6. 当前 App 草稿会持久化 `trainingConfig`，因此刷新后公司卡片应保留。

评价 Agent 使用方式：

- 评价 Agent 只读取 `companyCard`。
- 不允许评价 Agent 自己重新搜索公司。
- 公司资料只作为“公司理解/岗位连接”的上下文，不作为用户能力本身。
- 如果 `verificationStatus` 不是 verified，评价 Agent 只能评价用户是否有准备意识，不能判断公司事实真假。

### 2.2 配置阶段：岗位模型生成

入口：

- 前端：`/analyze-jd`
- 后端：`server/token_server.py` 的 `analyze_jd_endpoint`
- 岗位模型生成：`server/interview/jd_analyzer.py`

当前行为：

1. 用户输入或选择岗位。
2. 前端请求 `/analyze-jd`。
3. 后端根据岗位名、JD、公司资料生成 JD 分析结果。
4. 结果中包含：
   - `jdSummary`
   - `coreRequirements`
   - `interviewFocus`
   - `competencyWeights`
   - `questionStyleWeights`
   - `focusCompetencyId`
   - `dynamicModel`
5. 前端将 `dynamicModel` 写入 `trainingConfig.dynamicModel`。
6. 前端将完整 `analysisResult` 写入 App 层草稿，刷新后 JD 分析页内容应保留。

评价 Agent 使用方式：

- `dynamicModel` 是评价 Agent 的主要岗位模型来源。
- 其中 `competencies` 定义要考察哪些能力。
- 其中 `rubricDimensions` 定义评分维度和行为锚点。
- 评价 Agent 不能重新生成一套岗位模型，否则报告和追问逻辑会脱节。

### 2.3 面试阶段：追问计划生成

入口：

- 后端：`server/interview/orchestrator.py`
- 当前函数：`InterviewOrchestrator.build_question_trace()`
- 前端事件：`question.plan`

当前行为：

1. 每轮追问前，orchestrator 会根据当前能力维度、证据缺口、提问方式生成问题计划。
2. 后端通过 LiveKit data channel 发出 `question.plan` 事件。
3. 前端目前主要用于 debug 展示。
4. 当前项目已经能生成“这一题为什么问”的信息，但还需要进一步沉淀为完整 `questionTrace[]`。

当前 `question.plan` 已有近似字段：

- `capabilityId`
- `capabilityName`
- `capabilityDescription`
- `questionStyleId`
- `questionStyleName`
- `coverageRatio`
- `missingEvidence`
- `traceReason`
- `turnIndex`

评价 Agent 使用方式：

- 这些字段应该沉淀为 `questionTrace[]`，随最终评价请求一起传给评价 Agent。
- 评价 Agent 不能只看问答文本，否则不知道追问 Agent 当时为什么问这道题。

### 2.4 面试阶段：问答记录

入口：

- 后端：`InterviewOrchestrator.record_candidate_answer()`
- 当前状态：`orchestrator.turns`
- 前端历史：`conversation`

当前行为：

1. 用户回答经 ASR 转写成文本。
2. 后端记录当前问题和用户回答。
3. orchestrator 将其存为 `InterviewTurn`：
   - `question`
   - `answer`
   - `capabilityId`
   - `questionStyleId`
4. 前端也维护一份 conversation 用于报告历史展示。

评价 Agent 使用方式：

- 最终评价应以结构化 `transcript[]` 为准。
- 每一轮必须带上对应能力维度和提问方式。
- 如果回答过短、转写失败、中断，应该在 `answerMeta` 中标记。

### 2.5 面试阶段：证据覆盖状态

入口：

- 后端：`InterviewOrchestrator.evidence_snapshot_text()`
- 后端：`InterviewOrchestrator.coverage_ratio()`

当前行为：

1. orchestrator 根据能力要求中的关键词检查用户回答是否覆盖关键证据。
2. 当前已经能生成文本版 evidence snapshot。
3. 当前已经能计算 `coverageRatio`。

评价 Agent 使用方式：

- 评价 Agent 需要 `coverageRatio` 判断报告可信度。
- 评价 Agent 需要每个能力维度的 covered/missing，判断是“能力弱”还是“证据没采到”。
- 当前项目应逐步把文本版 `evidence_snapshot_text()` 升级成结构化 `EvidenceSnapshot`。

### 2.6 评价阶段：当前内置评价器

入口：

- 后端：`server/interview/evaluator.py`
- 当前类：`InterviewEvaluator`
- 当前调用：`server/agent.py` 中 `evaluate_interview`
- 前端接收事件：`interview.report`

当前行为：

1. 面试结束后，后端调用 `InterviewEvaluator.evaluate()`。
2. evaluator 从 orchestrator 读取问答、证据覆盖、岗位模型、公司资料。
3. evaluator 调用 LLM 生成 JSON 报告。
4. 后端通过 `interview.report` 事件发给前端。
5. 前端 `InterviewReportPanel` 展示报告。

评价 Agent 分离后的目标：

- 当前 `InterviewEvaluator` 的输入来源要显式整理为 `EvaluationRequest`。
- 评价 Agent 返回的数据应保持与当前前端报告结构兼容，或通过 adapter 转换。

## 3. 现场生成数据如何沉淀到 SessionState

建议主流程维护一个统一 `SessionState`。现场生成的数据不是临时变量，而是每一步写入该状态。

```ts
type SessionState = {
  sessionId: string;
  userId?: string;

  status: "configuring" | "interviewing" | "evaluating" | "completed" | "failed";

  companyCard: CompanyCard | null;
  jobModel: JobModel | null;
  interviewConfig: InterviewConfig;

  questionTrace: QuestionTraceItem[];
  transcript: TranscriptTurn[];
  evidenceSnapshot: EvidenceSnapshot;

  sessionMeta: SessionMeta;
  evaluationReport?: EvaluationResponse;
};
```

写入时机：

| 数据 | 写入时机 | 写入方 |
| --- | --- | --- |
| `companyCard` | 公司资料生成成功后 | 公司资料流程 |
| `jobModel` | JD 分析/岗位模型生成成功后 | 岗位模型流程 |
| `interviewConfig` | 用户开始面试前 | 配置页 / Session Controller |
| `questionTrace[]` | 每次生成问题计划时 | 追问逻辑 |
| `transcript[]` | 每次用户回答完成后 | ASR / Orchestrator |
| `evidenceSnapshot` | 每次用户回答后更新 | Evidence Tracker / Orchestrator |
| `sessionMeta` | 开始、结束、异常时更新 | Session Controller |
| `evaluationReport` | 评价 Agent 返回后 | 评价流程 |

## 4. 公司资料如何传给评价 Agent

评价 Agent 需要公司资料，是为了判断候选人是否能把回答和目标公司连接起来。

不需要传完整网页原文。应传结构化公司卡片。

```ts
type CompanyCard = {
  companyName: string;
  targetRole?: string;

  summary: string;
  businessLines?: string[];
  productsOrServices?: string[];
  marketPosition?: string[];
  cultureAndValues?: string[];

  // 面试准备相关信息，不是岗位 JD
  interviewNotes?: string[];
  interviewTalkingPoints?: string[];
  companyUnderstandingQuestions?: string[];

  sourceNotes?: string[];
  sourceUrls?: string[];
  verificationStatus: "verified" | "partial" | "unverified" | string;
  confidence?: number;
};
```

评价规则：

- `verified`：可以较正常地评价公司理解。
- `partial`：可以评价候选人是否尝试连接公司业务，但要提醒来源有限。
- `unverified`：只评价准备意识，不评价事实准确性。
- 如果没有 `companyCard`，公司理解项应返回 `score: null` 或说明“未配置公司资料”。

当前项目映射：

| 当前字段 | EvaluationRequest 字段 |
| --- | --- |
| `trainingConfig.companyCard.companyName` | `companyCard.companyName` |
| `companyCard.summary` | `companyCard.summary` |
| `businessLines` / `productsOrServices` | `companyCard.businessLines` / `productsOrServices` |
| `marketPosition` | `companyCard.marketPosition` |
| `cultureAndValues` | `companyCard.cultureAndValues` |
| `roleRelevantPoints` | 可映射为 `interviewNotes` |
| `interviewTalkingPoints` | `interviewTalkingPoints` |
| `companyUnderstandingQuestions` | `companyUnderstandingQuestions` |
| `sourceNotes` / `sourceUrls` | `sourceNotes` / `sourceUrls` |
| `verificationStatus` / `confidence` | 同名字段 |

## 5. 岗位模型如何传给评价 Agent

岗位模型是评价 Agent 的评分标准来源。评价 Agent 不应该自己重建岗位标准。

```ts
type JobModel = {
  jobTitle: string;
  jdSummary: string;
  coreRequirements: string[];
  interviewFocus: string[];

  competencies: Array<{
    id: string;
    name: string;
    description: string;
    weight: number;
    observableSignals: string[];
    weakSignals: string[];
  }>;

  rubricDimensions: Array<{
    id: string;
    name: string;
    description: string;
    weakAnchor: string;
    normalAnchor: string;
    strongAnchor: string;
  }>;

  questionSeeds?: string[];
  focusCompetencyId?: string;
  openingQuestion?: string;
  modelVersion?: string;
};
```

当前项目映射：

| 当前字段 | EvaluationRequest 字段 |
| --- | --- |
| `analysisResult.dynamicModel.jobTitle` | `jobModel.jobTitle` |
| `analysisResult.dynamicModel.jobSummary` | `jobModel.jdSummary` |
| `analysisResult.dynamicModel.coreRequirements` | `jobModel.coreRequirements` |
| `analysisResult.dynamicModel.interviewFocus` | `jobModel.interviewFocus` |
| `analysisResult.dynamicModel.competencies` | `jobModel.competencies` |
| `analysisResult.dynamicModel.rubricDimensions` | `jobModel.rubricDimensions` |
| `analysisResult.dynamicModel.questionSeeds` | `jobModel.questionSeeds` |
| `analysisResult.dynamicModel.openingQuestion` | `jobModel.openingQuestion` |
| `trainingConfig.dynamicModel` | 面试开始后的 `jobModel` 来源 |

注意：

- `competencyWeights` 是训练/追问调度权重，不是用户评分。
- `rubricDimensions` 是评价维度，应优先用于最终报告。
- 如果没有动态模型，才使用预设岗位模板作为 fallback。

## 6. 追问记录 questionTrace 如何传给评价 Agent

`questionTrace` 是评价 Agent 最容易缺失、但最关键的数据。

它解决的问题是：评价 Agent 需要知道系统到底有没有给用户补证据的机会。

如果只传 transcript，评价 Agent 只能看到：

```text
Q: 你这个项目最终有什么结果？
A: 结果还可以，大家反馈不错。
```

但它不知道：

- 这题对应哪个能力维度？
- 问之前缺什么证据？
- 这是开放问题、证据追问还是压力追问？
- 这一题是核心考察还是顺带问？
- 用户没有答结果指标，是因为系统没提示，还是已经被追问后仍没补？

因此每一轮问题都应该沉淀：

```ts
type QuestionTraceItem = {
  turnIndex: number;
  questionId: string;
  question: string;

  competencyId: string;
  competencyName?: string;
  competencyDescription?: string;

  questionStyleId: "open" | "evidence" | "pressure" | "relaxed" | "reflection" | string;
  questionStyleName?: string;

  coverageRatioBeforeQuestion?: number;
  missingEvidenceBeforeQuestion: string[];
  coveredEvidenceBeforeQuestion?: string[];

  askedBecause: string;
  expectedEvidence?: string[];

  createdAt?: string;
};
```

示例：

```json
{
  "turnIndex": 2,
  "questionId": "q_002",
  "question": "你刚才说推动了需求落地，能具体讲讲你负责了哪些关键动作，以及最后结果怎么验证的吗？",
  "competencyId": "project_delivery",
  "competencyName": "项目推进",
  "competencyDescription": "识别个人角色、关键动作、协作对象和交付结果。",
  "questionStyleId": "evidence",
  "questionStyleName": "证据追问",
  "coverageRatioBeforeQuestion": 0.28,
  "missingEvidenceBeforeQuestion": ["个人角色", "关键动作", "结果指标"],
  "coveredEvidenceBeforeQuestion": ["项目背景"],
  "askedBecause": "项目推进维度缺少个人贡献和结果证据，需要补齐可验证动作。",
  "expectedEvidence": ["个人负责内容", "协作对象", "结果指标或用户反馈"],
  "createdAt": "2026-06-06T10:20:00+08:00"
}
```

当前项目映射：

| 当前字段 | QuestionTraceItem 字段 |
| --- | --- |
| `build_question_trace().turnIndex` | `turnIndex` |
| 可由 turnIndex 生成 | `questionId` |
| 实际发给用户的问题 | `question` |
| `capabilityId` | `competencyId` |
| `capabilityName` | `competencyName` |
| `capabilityDescription` | `competencyDescription` |
| `questionStyleId` | `questionStyleId` |
| `questionStyleName` | `questionStyleName` |
| `coverageRatio` | `coverageRatioBeforeQuestion` |
| `missingEvidence` | `missingEvidenceBeforeQuestion` |
| `traceReason` | `askedBecause` |

当前差距：

- 项目现在会通过 `question.plan` 事件发出 trace 信息。
- 但它更多是调试/前端展示事件。
- 后续需要在后端 SessionState 中持久化为 `questionTrace[]`。

## 7. 问答记录 transcript 如何传给评价 Agent

评价 Agent 需要结构化问答，不应只收到一整段对话文本。

```ts
type TranscriptTurn = {
  turnIndex: number;
  questionId: string;
  question: string;
  answer: string;

  competencyId: string;
  competencyName?: string;
  questionStyleId: string;
  questionStyleName?: string;

  answerMeta?: {
    asrConfidence?: number;
    wasInterrupted?: boolean;
    wasTooShort?: boolean;
    userSkipped?: boolean;
    networkInterrupted?: boolean;
    startedAt?: string;
    endedAt?: string;
    answerCharCount?: number;
  };
};
```

当前项目映射：

| 当前字段 | TranscriptTurn 字段 |
| --- | --- |
| `InterviewTurn.question` | `question` |
| `InterviewTurn.answer` | `answer` |
| `InterviewTurn.capability_id` | `competencyId` |
| `InterviewTurn.question_style_id` | `questionStyleId` |
| turn 数组 index | `turnIndex` |
| 对应 questionTrace 的 id | `questionId` |
| ASR/中断状态 | `answerMeta`，当前需要补强 |

注意：

- 如果用户没说完整，`wasTooShort` 应标记。
- 如果麦克风关闭或转写取消，`wasInterrupted` 应标记。
- 如果断网重连导致该轮不完整，`networkInterrupted` 应标记。
- 评价 Agent 应把这些作为报告可信度信息，不应直接给低分。

## 8. 证据快照 evidenceSnapshot 如何传给评价 Agent

证据快照告诉评价 Agent：

- 当前已经采到哪些证据。
- 每个能力维度还缺哪些证据。
- 证据来自第几轮回答。
- 整体覆盖率是多少。

推荐结构：

```ts
type EvidenceSnapshot = {
  coverageRatio: number;
  coveredEvidence: string[];
  missingEvidence: string[];

  perCompetency: Array<{
    competencyId: string;
    competencyName?: string;
    covered: string[];
    missing: string[];
    evidenceRefs?: Array<{
      requirement: string;
      turnIndex: number;
      answerExcerpt: string;
    }>;
  }>;

  textSnapshot?: string; // 兼容当前 prompt 的文本版
};
```

当前项目映射：

| 当前字段 | EvidenceSnapshot 字段 |
| --- | --- |
| `orchestrator.coverage_ratio()` | `coverageRatio` |
| `orchestrator.evidence_snapshot_text()` | `textSnapshot` |
| 每个 track requirement 的命中情况 | `perCompetency.covered/missing`，当前需要结构化补强 |
| 命中的回答片段 | `evidenceRefs`，当前需要补强 |

当前项目已经有文本版：

```text
需求分析:
- 需求来源: 已出现
- 用户问题: 缺失
项目推进:
- 个人角色: 已出现
- 关键行动: 缺失
```

建议后续升级成结构化对象，同时保留 `textSnapshot` 兼容旧 prompt。

## 9. EvaluationRequest TypeScript 结构

面试结束时，Session Controller 应从 `SessionState` 组装以下请求给评价 Agent。

```ts
type EvaluationRequest = {
  sessionId: string;
  userId?: string;

  reportSchemaVersion: string;
  rubricVersion: string;
  jobModelVersion?: string;

  companyCard: CompanyCard | null;
  jobModel: JobModel;
  interviewConfig: InterviewConfig;

  questionTrace: QuestionTraceItem[];
  transcript: TranscriptTurn[];
  evidenceSnapshot: EvidenceSnapshot;

  resume?: {
    rawText?: string;
    summary?: string;
    projects?: string[];
    skills?: string[];
  };

  sessionMeta: SessionMeta;
};

type InterviewConfig = {
  modeId: string;
  competencyWeights: Record<string, number>;
  questionStyleWeights: Record<string, number>;
  interviewerTone: string;
  voiceProfileId?: string;
  strategyId?: string;
};

type SessionMeta = {
  startedAt: string;
  endedAt?: string;
  candidateTurnCount: number;
  totalAnswerChars: number;
  endedReason: "normal" | "user_stopped" | "timeout" | "network_error" | "agent_error";
  locale?: string;
  clientVersion?: string;
};
```

MVP 最小必传：

```ts
type MinimumEvaluationRequest = {
  sessionId: string;
  companyCard: CompanyCard | null;
  jobModel: JobModel;
  interviewConfig: InterviewConfig;
  questionTrace: QuestionTraceItem[];
  transcript: TranscriptTurn[];
  evidenceSnapshot: EvidenceSnapshot;
  sessionMeta: SessionMeta;
};
```

如果 MVP 阶段还没有结构化 `EvidenceSnapshot`，可以先传：

```ts
evidenceSnapshot: {
  coverageRatio: number;
  coveredEvidence: [];
  missingEvidence: [];
  perCompetency: [];
  textSnapshot: string;
}
```

但要明确这是过渡方案。

## 10. EvaluationResponse TypeScript 结构

评价 Agent 返回结构建议尽量兼容当前前端 `InterviewReport`。

```ts
type EvaluationResponse = {
  reportQuality: "full" | "insufficient_sample" | "evaluation_unavailable";
  summary: string;

  turnCount: number;
  coverageRatio: number;

  abilityModel: Record<string, number>;

  dimensions: Array<{
    id: string;
    name: string;
    score: number | null;
    level: "暂不评分" | "待补强" | "基础可用" | "较好" | "优秀" | string;
    reason: string;
    evidence: string;
    risk?: string;
    improvement: string;
  }>;

  evidenceGaps: string[];

  companyFitBonus?: {
    score: number | null;
    reason: string;
    verificationNote?: string;
    talkingPoints?: string[];
  };

  roleFit?: {
    score: number | null;
    reason: string;
    focusDimensions?: string[];
    risk?: string;
  };

  answerCards?: Array<{
    issue: string;
    relatedTurnIndex?: number;
    dangerousAnswer: string;
    passableAnswer: string;
    strongAnswer: string;
    evidenceNeeded?: string[];
  }>;

  trainingPlan: {
    theme: string;
    goal: string;
    durationMinutes?: number;
    sevenDayPlan?: string[];
    fourteenDayPlan?: string[];
    thirtyDayPlan?: string[];
    tasks?: Array<{
      name: string;
      exercise: string;
      method: string;
      successCriteria?: string;
    }>;
    nextInterviewFocus?: string;
  };
};
```

当前前端 `InterviewReport` 字段是 snake_case 风格，例如：

- `report_quality`
- `turn_count`
- `coverage_ratio`
- `ability_model`
- `company_fit_bonus`
- `role_fit`
- `main_weakness`
- `training_plan`

因此可以二选一：

1. 评价 Agent 直接返回当前前端兼容的 snake_case。
2. 评价 Agent 返回 camelCase，由 adapter 转成当前前端结构。

推荐短期用 snake_case 兼容现有前端，长期定义正式 schema 后再统一。

## 11. reportQuality 规则

评价 Agent 必须显式返回报告质量：

```ts
type ReportQuality = "full" | "insufficient_sample" | "evaluation_unavailable";
```

### full

适用条件：

- 至少有足够问答轮次。
- transcript 可读。
- 有岗位模型和评分维度。
- 能找到足够证据做维度判断。

### insufficient_sample

适用条件：

- 回答轮次太少。
- 回答总字数太少。
- 用户中途停止。
- 大量回答为空。
- 关键维度完全没有机会被问到。

要求：

- 不打硬分，或多数维度 `score: null`。
- 说明“暂不能稳定判断”，不要写成“能力差”。
- 训练计划应聚焦补全素材，而不是能力否定。

### evaluation_unavailable

适用条件：

- 评价 Agent 调用失败。
- 返回格式无法解析。
- 必要字段缺失。

要求：

- 不生成伪报告。
- 保留 transcript。
- 允许稍后重新生成。

## 12. questionTrace 为什么是关键桥梁

评价 Agent 的公平性依赖三类信息：

1. 标准是什么：`jobModel.rubricDimensions`
2. 系统问了什么、为什么问：`questionTrace`
3. 用户答了什么、证据覆盖到哪里：`transcript` + `evidenceSnapshot`

如果缺少 `questionTrace`，评价 Agent 无法区分：

- 用户没提供某证据。
- 系统从来没问过某证据。
- 该能力不是本轮重点。
- 追问 Agent 已经给过补充机会但用户仍没回答。
- 用户回答被 ASR 或网络问题截断。

示例：

如果 transcript 里只有：

```text
Q: 这个项目最终效果怎么样？
A: 效果还不错，后来团队也继续用了。
```

评价 Agent 可能会粗暴判断“结果表达弱”。

但如果有 questionTrace：

```json
{
  "questionStyleId": "evidence",
  "missingEvidenceBeforeQuestion": ["结果指标", "用户反馈", "前后对比"],
  "askedBecause": "结果表达维度缺少可验证结果。"
}
```

评价 Agent 就可以更准确地写：

```text
结果表达维度：基础可用。
已看到候选人知道要说明项目结果，但在被明确追问结果指标后，仍未给出量化指标、用户反馈或前后对比，因此目前证据不足，下一步应补充一个可验证结果。
```

这比单纯低分更公平，也更适合训练产品。

## 13. 当前项目已有字段映射总表

| 当前实现位置 | 当前字段/函数 | 目标契约字段 |
| --- | --- | --- |
| `web/src/main.tsx` | `trainingConfig.companyCard` | `EvaluationRequest.companyCard` |
| `web/src/main.tsx` | `trainingConfig.dynamicModel` | `EvaluationRequest.jobModel` |
| `web/src/main.tsx` | `analysisResult.dynamicModel` | 配置阶段的 `jobModel` 来源 |
| `web/src/main.tsx` | `trainingConfig.competencyWeights` | `interviewConfig.competencyWeights` |
| `web/src/main.tsx` | `trainingConfig.questionStyleWeights` | `interviewConfig.questionStyleWeights` |
| `web/src/main.tsx` | `trainingConfig.interviewerTone` | `interviewConfig.interviewerTone` |
| `server/agent.py` | `training_config_from_event()` | 面试开始时构建 `interviewConfig` |
| `server/agent.py` | `_deserialize_dynamic_model()` | 将前端 `dynamicModel` 转为后端 `DynamicJobModel` |
| `server/interview/orchestrator.py` | `build_question_trace()` | `questionTrace[]` 单项来源 |
| `server/interview/orchestrator.py` | `record_candidate_answer()` | `transcript[]` 单项来源 |
| `server/interview/orchestrator.py` | `turns` | `transcript[]` |
| `server/interview/orchestrator.py` | `evidence_snapshot_text()` | `evidenceSnapshot.textSnapshot` |
| `server/interview/orchestrator.py` | `coverage_ratio()` | `evidenceSnapshot.coverageRatio` |
| `server/interview/evaluator.py` | `InterviewEvaluator.evaluate()` | 未来替换为评价 Agent 调用点 |
| `server/agent.py` | `interview.report` event | `EvaluationResponse` 回传前端 |
| `web/src/main.tsx` | `InterviewReportPanel` | `EvaluationResponse` 展示组件 |

## 14. 当前项目需要补的点

### 14.1 持久化 questionTrace[]

当前 `question.plan` 已经能发给前端，但更像调试事件。评价 Agent 对接前，应在后端 SessionState 中保存：

```ts
questionTrace.push(questionPlan)
```

并确保每个 `TranscriptTurn` 能通过 `questionId` 或 `turnIndex` 对回对应 trace。

### 14.2 结构化 evidenceSnapshot

当前只有文本版 evidence snapshot。建议新增结构化输出：

```ts
{
  coverageRatio,
  coveredEvidence,
  missingEvidence,
  perCompetency,
  textSnapshot
}
```

短期可以先让评价 Agent 读 `textSnapshot`，但长期必须结构化。

### 14.3 增加 answerMeta

目前评价 Agent 很难知道某轮回答是否受技术问题影响。建议在 ASR/转写链路补充：

- `wasTooShort`
- `wasInterrupted`
- `networkInterrupted`
- `answerCharCount`
- `asrConfidence`，如果 ASR 支持

### 14.4 版本化

建议新增：

- `reportSchemaVersion`
- `rubricVersion`
- `jobModelVersion`

否则后续评分标准变化后，历史报告很难解释。

### 14.5 评价结果 adapter

如果评价 Agent 返回 camelCase，应在后端 adapter 转为当前前端兼容的 snake_case。

当前前端报告组件已经支持：

- `report_quality`
- `summary`
- `turn_count`
- `coverage_ratio`
- `ability_model`
- `dimensions`
- `evidence_gaps`
- `company_fit_bonus`
- `role_fit`
- `main_weakness`
- `training_plan`

## 15. 给评价 Agent 的最小系统提示词

```text
你是 AI 面试训练产品的评价 Agent。
你只能基于 EvaluationRequest 中的信息评分。
不要自行搜索公司信息。
不要重新生成岗位模型。
不要编造用户经历、项目、指标、公司事实。
每个分数必须引用 transcript、questionTrace 或 evidenceSnapshot 中的证据。
如果样本不足，返回 reportQuality=insufficient_sample，不要硬打低分。
如果某轮回答受 ASR、断网、中断影响，要降低判断确定性，不要直接归因于候选人能力差。
你是训练教练，不是淘汰面试官。报告要真实指出问题，但必须给出可执行的下一步。
```

## 16. 推荐对接顺序

1. 先约定 `EvaluationRequest` / `EvaluationResponse` 字段名和版本。
2. 当前项目先组装 MVP 版 `EvaluationRequest`。
3. 把 `build_question_trace()` 的结果沉淀为 `questionTrace[]`。
4. 把 `orchestrator.turns` 转成结构化 `transcript[]`。
5. 先用 `evidence_snapshot_text()` 填 `evidenceSnapshot.textSnapshot`。
6. 评价 Agent 先返回当前前端兼容的报告结构。
7. 后续再补结构化 `perCompetency`、`answerMeta`、`answerCards`。

## 17. 一句话总结

```text
当前项目已经能生成公司资料、岗位模型、追问计划、问答记录和证据覆盖文本。
评价 Agent 对接时，不要让它重新找事实，而是把这些现场生成的数据沉淀成 SessionState，
最终组装成 EvaluationRequest。
其中 questionTrace 是追问逻辑和评价逻辑之间的关键桥梁：
它告诉评价 Agent 每一道题为什么问、缺什么证据、用户是否有机会补证据。
```

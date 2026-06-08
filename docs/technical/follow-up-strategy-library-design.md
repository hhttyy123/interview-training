# 面试追问策略库设计文档

更新日期：2026-06-08

本文档定义“面试追问策略库”的正式设计。目标不是做一个 demo 级 prompt 集合，而是把当前项目里偏粗糙的追问逻辑升级为可扩展、可解释、可测试、可与评价 Agent 对齐的专业面试采证系统。

## 1. 背景与问题

当前项目已经有追问调度雏形：

- `InterviewOrchestrator` 会根据能力权重选择下一轮考察能力。
- 系统会根据提问方式权重选择 `open`、`evidence`、`pressure`、`relaxed`、`reflection` 等问题类型。
- `build_question_trace()` 会生成能力维度、证据缺口、提问方式和追问原因。
- `build_followup_prompt()` 会把这些上下文塞给 LLM，让模型生成下一句追问。

但实际体验中存在明显问题：

- 不同面试风格主要只是 prompt 语气不同，追问路径没有本质区别。
- 证据判断主要依赖关键词命中，无法判断回答是否真正有质量。
- 缺失证据类型太粗，经常都落到“个人动作、结果指标、复盘”这几类。
- 没有专业面试方法论库，导致问题像泛化追问，而不是成熟面试官。
- `question.plan` 还不是完整策略决策结果，评价 Agent 很难复盘“为什么这样问”。
- 压力面、轻松面、结构化面、终面风格没有真正变成不同的问题路径。

因此需要新增一层：**Follow-up Strategy Library**。

新的追问链路应该是：

```text
岗位模型
-> 能力维度
-> 证据状态
-> 候选人上一轮回答
-> 面试阶段
-> 面试风格
-> 选择追问策略
-> 生成 QuestionPlan
-> LLM 只负责自然语言表达
-> 写入 questionTrace
```

核心变化是：LLM 不再自由决定“怎么追问”，而是被策略库约束在一个专业追问动作里。

## 2. 设计目标

追问策略库必须满足以下目标：

- 专业：内置结构化行为面试、岗位面试、压力面、复盘面、公司匹配面等成熟方法论。
- 可用：每个策略都能直接生成下一轮问题计划，不只是写原则。
- 可解释：每次追问都能说明使用了哪个策略、为什么使用、期待采集什么证据。
- 可配置：用户选择的面试风格、提问方式占比、能力重点会明显影响问题。
- 可测试：给定相同 SessionState，策略选择结果应该可预测、可断言。
- 可评价：`questionTrace` 能被评价 Agent 用来判断追问是否充分、公平。
- 可扩展：未来可以按岗位、公司、面试阶段、候选人水平扩展策略。

## 3. 非目标

本设计不做以下事情：

- 不把追问策略库做成固定题库。
- 不让策略库替代岗位模型。
- 不让策略库替代评价 Agent。
- 不让 LLM 自己临场发明面试方法论。
- 不在策略库中写具体公司的不可核验事实。
- 不为了“压力感”攻击、羞辱或否定候选人。

策略库的定位是：**决定专业追问动作，而不是生成最终报告，也不是背诵题库。**

## 4. 总体架构

建议新增以下模块：

```text
livekit-interview-spike/server/interview/
  followup/
    __init__.py
    models.py
    methodology.py
    strategy_library.py
    strategy_selector.py
    evidence_state.py
    question_plan_builder.py
    prompt_renderer.py
```

职责划分：

- `models.py`：定义策略、证据状态、问题计划、策略选择结果。
- `methodology.py`：沉淀 STAR/CAR/SOAR、行为面试、压力面、案例面等方法论。
- `strategy_library.py`：维护可用追问策略清单。
- `strategy_selector.py`：根据 SessionState 选择最合适策略。
- `evidence_state.py`：把回答从“关键词命中”升级为结构化证据状态。
- `question_plan_builder.py`：将策略选择结果组装成 `QuestionPlan`。
- `prompt_renderer.py`：把 `QuestionPlan` 渲染为 LLM prompt，让 LLM 只做自然语言表达。

当前 `InterviewOrchestrator` 后续应逐步收口为：

```python
class InterviewOrchestrator:
    def record_candidate_answer(...)
    def build_next_question_plan(...) -> QuestionPlan
    def build_followup_prompt(plan: QuestionPlan) -> str
    def record_assistant_question(...)
```

## 5. 核心概念

### 5.1 QuestionPlan

`QuestionPlan` 是每一轮追问的正式决策结果。

```ts
type QuestionPlan = {
  questionId: string;
  turnIndex: number;

  stage: InterviewStage;
  competencyId: string;
  competencyName: string;

  evidenceTarget: EvidenceTarget;
  strategyId: string;
  strategyName: string;
  methodologyIds: string[];

  interviewStyleId: InterviewStyleId;
  questionStyleId: QuestionStyleId;
  pressureLevel: 0 | 1 | 2 | 3;

  anchor: QuestionAnchor;
  expectedEvidence: ExpectedEvidence[];
  missingEvidenceBeforeQuestion: EvidenceGap[];
  coveredEvidenceBeforeQuestion: EvidenceItem[];

  askIntent: string;
  questionShape: QuestionShape;
  constraints: QuestionConstraints;

  promptHints: string[];
  disallowedMoves: string[];
};
```

### 5.2 QuestionAnchor

每一轮追问必须锚定真实上下文，不能凭空问。

```ts
type QuestionAnchor = {
  source: "last_answer" | "resume" | "job_model" | "company_card" | "previous_gap" | "interview_stage";
  quote?: string;
  summary: string;
  turnIndex?: number;
  confidence: "high" | "medium" | "low";
};
```

规则：

- 优先锚定上一轮回答。
- 如果上一轮回答太短，锚定简历或岗位模型。
- 如果公司资料未核验，只能锚定用户表达或准备思路，不能锚定公司事实。
- 如果没有任何可用锚点，策略应生成澄清问题，而不是假装理解。

### 5.3 EvidenceTarget

证据目标不是一句“缺结果指标”就结束，而要拆成可采集的结构。

```ts
type EvidenceTarget = {
  id: string;
  label: string;
  category:
    | "context"
    | "task"
    | "action"
    | "decision"
    | "tradeoff"
    | "collaboration"
    | "result"
    | "metric"
    | "learning"
    | "company_fit"
    | "role_fit"
    | "technical_depth"
    | "business_judgment";
  qualityBar: EvidenceQualityBar;
};
```

### 5.4 EvidenceQualityBar

每个证据目标都要有质量标准。

```ts
type EvidenceQualityBar = {
  unacceptable: string;
  weak: string;
  acceptable: string;
  strong: string;
};
```

示例：

```json
{
  "unacceptable": "只说结果不错，没有任何可验证信息",
  "weak": "有主观评价，但缺少数据、反馈或前后对比",
  "acceptable": "能给出至少一个数据、用户反馈或业务变化",
  "strong": "能说明指标口径、变化幅度、归因边界和自己贡献"
}
```

## 6. 面试方法论层

策略库需要内置稳定的方法论。方法论不是直接问题，而是追问动作的依据。

### 6.1 STAR 行为面试

用途：

- 项目经历
- 实习经历
- 校园经历
- 行为面试

采证顺序：

```text
Situation -> Task -> Action -> Result
```

要替换当前粗糙点：

- 不再笼统问“具体讲讲项目”。
- 改为判断用户当前缺的是 S/T/A/R 哪一段，再针对性追问。

策略示例：

- 缺 S：追问背景、问题来源、业务/用户场景。
- 缺 T：追问目标、约束、个人职责。
- 缺 A：追问个人动作、关键决策、协作推进。
- 缺 R：追问结果、指标、反馈、影响。

### 6.2 CAR / PAR 结构

用途：

- 用户回答很散时快速收束。
- 适合低年级、应届生、表达训练。

结构：

```text
Challenge / Problem -> Action -> Result
```

优势：

- 比 STAR 更短，适合语音实时训练。
- 当用户表达太长时，用 CAR 帮他回到主线。

### 6.3 SOAR 成就表达

用途：

- 用户讲成功案例，但亮点不突出。
- 用于训练“经历如何变成竞争力”。

结构：

```text
Situation -> Obstacle -> Action -> Result
```

重点：

- 追问困难、阻力和复杂度。
- 防止用户把普通执行讲成高价值成果。

### 6.4 Behavioral Event Interview

用途：

- 判断真实行为，而不是听理念。

规则：

- 少问“你会怎么做”。
- 多问“你当时怎么做”。
- 追问具体时间、对象、动作、反馈。

典型追问：

```text
你当时具体先找了谁确认？对方怎么反馈？
```

### 6.5 Funnel Interview 漏斗追问

用途：

- 从泛回答逐步追到细节。

路径：

```text
开放问题 -> 澄清问题 -> 证据问题 -> 反事实/压力问题 -> 复盘问题
```

这应成为默认多轮追问节奏，而不是每轮都直接问证据。

### 6.6 Case Interview 业务拆解

用途：

- 产品、运营、数据、商业分析、策略类岗位。

追问维度：

- 目标定义
- 用户/客户分层
- 约束和资源
- 方案选项
- 优先级
- 指标体系
- 风险和验证

### 6.7 Technical Deep Dive

用途：

- 前端、后端、算法、数据、工程类岗位。

追问维度：

- 架构选择
- 边界条件
- 复杂度
- 性能
- 稳定性
- 测试
- 故障处理
- 技术取舍

### 6.8 Bar Raiser / 压力面

用途：

- 检查证据真实性、归因边界、逻辑漏洞。

规则：

- 压力来自问题难度，不来自攻击语气。
- 必须基于用户已经说过的话挑战。
- 不允许人身否定。

典型动作：

- 追问“你如何证明是你的动作导致结果？”
- 追问“如果没有这个条件，方案还成立吗？”
- 追问“这个数据口径是否可能误导？”

### 6.9 Company Fit / Motivation Fit

用途：

- 公司理解
- 岗位动机
- 业务连接

注意：

- 公司资料未核验时，只评价准备思路和连接能力。
- 不判断用户说的公司事实真假。

追问路径：

- 用户知道公司做什么吗？
- 用户能把岗位和公司业务连接起来吗？
- 用户能解释自己为什么匹配吗？
- 用户是否有具体准备动作？

## 7. 证据状态机

当前项目的证据覆盖主要靠关键词命中。这个设计太粗，必须替换为结构化证据状态机。

### 7.1 EvidenceSlot

每个能力维度下维护若干证据槽。

```ts
type EvidenceSlot = {
  id: string;
  competencyId: string;
  label: string;
  category: EvidenceCategory;
  required: boolean;
  priority: number;

  status: "missing" | "mentioned" | "partial" | "supported" | "strong" | "contradictory";
  confidence: number;

  refs: EvidenceRef[];
  lastAskedTurn?: number;
  askCount: number;
};
```

状态含义：

- `missing`：完全没有出现。
- `mentioned`：提到了相关词，但没有有效信息。
- `partial`：有一些事实，但不完整。
- `supported`：有可用证据。
- `strong`：有具体、可验证、能支撑评价的证据。
- `contradictory`：前后说法冲突，需要澄清。

### 7.2 EvidenceRef

```ts
type EvidenceRef = {
  turnIndex: number;
  source: "answer" | "resume" | "company_card" | "jd";
  excerpt: string;
  interpretedAs: string;
  confidence: number;
};
```

### 7.3 证据质量判断

证据质量不能只看关键词，也不应该把规则写死。正式方案应采用 **LLM 主导 + 规则轻护栏**。

LLM 判断层是主判断，占主要权重：

- 回答是否真正支持该证据槽。
- 回答是否有具体场景、角色、动作、决策、结果或反思。
- 回答里的证据强度属于 `mentioned`、`partial`、`supported` 还是 `strong`。
- 是否需要继续澄清。
- 是否存在归因过度、逻辑跳跃、前后矛盾或责任边界不清。
- 回答是否和岗位模型、简历锚点、公司上下文存在有效连接。

规则层只做轻量辅助和安全护栏，不能替代判断：

- 检测是否包含数字、时间、对象、角色、动作等显性信号。
- 检测是否有前后对比、用户反馈、业务影响等强证据线索。
- 检测是否出现“我们”很多但“我”的个人贡献不足。
- 检测是否出现“效果不错”“提升很多”等空泛表达。
- 检测回答是否过短、疑似 ASR 截断、疑似网络中断。

权重建议：

```text
LLM evidence judge: 70%-80%
规则信号: 20%-30%
```

规则只能影响置信度和候选证据提示，不能单独决定 `EvidenceSlot` 已经 covered。真正决定证据状态的，应是 LLM 对回答语义、岗位语境和证据质量的综合判断。

LLM 判断必须返回结构化结果：

```ts
type EvidenceUpdate = {
  slotId: string;
  status: EvidenceSlotStatus;
  confidence: number;
  excerpt: string;
  rationale: string;
  nextBestProbe?: string;
};
```

## 8. 策略库分类

追问策略库分为 9 大类。

### 8.1 Opening Strategy

用于开场。

子策略：

- `company_understanding_opening`
- `role_motivation_opening`
- `resume_project_opening`
- `self_intro_opening`

使用规则：

- 有公司资料：优先公司理解开场。
- 有简历且公司资料缺失：用简历核心项目开场。
- 用户只配置岗位：用岗位动机和项目经历开场。

### 8.2 Clarification Strategy

用于回答含糊、不完整、代词过多时。

触发条件：

- 用户说“这个”“那个”“一部分”“很多”“还可以”等模糊词。
- 没有明确项目背景。
- 没有说明个人角色。
- 回答短于阈值。

问题形态：

```text
你刚才说“{模糊表达}”，这里具体指的是哪类用户、场景或问题？
```

### 8.3 Evidence Probe Strategy

用于补齐事实证据。

触发条件：

- 有经历，但缺个人动作。
- 有结论，但缺数据。
- 有过程，但缺角色。
- 有结果，但缺验证方式。

问题形态：

```text
你刚才提到{anchor}，你个人负责的关键动作是哪两个？
```

### 8.4 Depth Probe Strategy

用于判断深度，不满足于表面描述。

触发条件：

- 用户给出流程，但没有解释为什么。
- 用户给出方案，但没有取舍。
- 用户给出工具，但没有边界。

问题形态：

```text
当时为什么选这个方案，而不是另一个更简单的做法？
```

### 8.5 Pressure / Challenge Strategy

用于挑战证据真实性和逻辑边界。

触发条件：

- 用户声称结果很好，但没有归因。
- 用户把团队成果完全归于自己。
- 用户前后说法不一致。
- 用户给出明显空泛结论。

问题形态：

```text
如果去掉你做的这个动作，结果还会发生吗？你怎么证明差异？
```

### 8.6 Reflection Strategy

用于复盘、成长、失败、重做。

触发条件：

- 核心 S/T/A/R 已基本采齐。
- 用户已经讲完完整经历。
- 需要考察学习能力和成熟度。

问题形态：

```text
如果重做一次，你会最先改哪个判断？为什么？
```

### 8.7 Role Fit Strategy

用于岗位匹配。

触发条件：

- 用户回答中出现岗位能力信号。
- 需要连接 JD 或岗位模型。
- 面试进入中后段。

问题形态：

```text
这段经历里，哪一部分最能证明你适合{targetRole}？
```

### 8.8 Company Fit Strategy

用于公司理解加分项。

触发条件：

- 有公司卡片。
- 用户主动提到公司业务、文化、产品、岗位动机。
- 面试开场或中后段需要连接公司。

问题形态：

```text
你提到关注{companyTopic}，这和你刚才的项目经验有什么对应关系？
```

### 8.9 Recovery Strategy

用于兜底和体验恢复。

触发条件：

- 用户回答太短。
- ASR 质量差。
- 用户明显卡住。
- 网络中断后恢复。
- 连续两轮没有采到有效证据。

问题形态：

```text
没关系，我们先收窄一点。这个项目里你最确定是自己完成的一件事是什么？
```

## 9. 面试风格如何真正生效

当前风格差异太弱，是因为风格只进入 prompt。新的设计中，风格必须影响三个层面：

- 策略选择权重。
- 问题形态。
- 允许的压力等级。

### 9.1 InterviewStyleProfile

```ts
type InterviewStyleProfile = {
  id: "supportive" | "standard" | "formal" | "pressure" | "senior" | "final_round";
  label: string;
  strategyWeights: Record<string, number>;
  pressureLevelRange: [number, number];
  preferredQuestionShapes: QuestionShape[];
  wordingRules: string[];
  disallowedMoves: string[];
};
```

### 9.2 轻松引导型 supportive

特点：

- 更多澄清和引导。
- 少用压力追问。
- 问题允许带一点方向提示，但不能替用户作答。

策略权重：

```json
{
  "clarification": 25,
  "evidence_probe": 25,
  "depth_probe": 15,
  "reflection": 15,
  "role_fit": 10,
  "company_fit": 5,
  "pressure": 5
}
```

同样缺“结果指标”时：

```text
你刚才说效果不错，可以回忆一个最能说明变化的数据、反馈或前后对比吗？
```

### 9.3 标准结构化 standard

特点：

- 按 STAR/CAR 稳定采证。
- 语气中性。
- 优先补齐关键证据。

策略权重：

```json
{
  "clarification": 15,
  "evidence_probe": 30,
  "depth_probe": 20,
  "reflection": 15,
  "role_fit": 10,
  "company_fit": 5,
  "pressure": 5
}
```

问题示例：

```text
你刚才说效果不错，最终用了哪个指标或反馈来验证这个结果？
```

### 9.4 正式克制 formal

特点：

- 更像真实一面。
- 问题简洁、克制、职业化。
- 少用安抚词。

问题示例：

```text
这个结果的验证口径是什么？请说明数据来源和变化幅度。
```

### 9.5 压力挑战型 pressure

特点：

- 更高比例挑战策略。
- 追问归因、边界、矛盾。
- 不允许攻击候选人。

策略权重：

```json
{
  "clarification": 10,
  "evidence_probe": 20,
  "depth_probe": 20,
  "reflection": 10,
  "role_fit": 10,
  "company_fit": 5,
  "pressure": 25
}
```

同样缺“结果指标”时：

```text
你说效果不错，但没有指标支撑。怎么证明这不是主观判断？
```

### 9.6 资深面试官 senior

特点：

- 更重视结构、边界、取舍、复杂度。
- 不急着追指标，会先看判断质量。

问题示例：

```text
这个方案当时最大的约束是什么？你做取舍时放弃了什么？
```

### 9.7 终面风格 final_round

特点：

- 更关注动机、潜力、成熟度、岗位匹配。
- 追问价值观和长期判断，但仍需基于具体经历。

问题示例：

```text
这段经历里最能代表你工作方式的一点是什么？和目标岗位有什么关系？
```

## 10. 职业通用化策略

策略库不能只盯着预置岗位。产品经理、运营、数据分析、前端工程只能作为验证样例，不能成为系统能力边界。

正式方案必须支持任意职业，方式是：**动态岗位模型 + 职业族画像 + 能力原型 + 策略组合**。

### 10.1 设计原则

- 不为少数岗位写死策略分支。
- 不把预置岗位当成产品能力上限。
- 任何用户输入的岗位，都必须能生成可用的追问策略。
- 预置模板只能作为 seed/fallback，用于冷启动和稳定兜底。
- 真正的追问策略应来自岗位职责、能力模型、证据槽和职业场景，而不是岗位名称字符串。

### 10.2 CareerProfile

每个岗位在面试开始前都应被转成 `CareerProfile`。

```ts
type CareerProfile = {
  roleTitle: string;
  roleFamily: RoleFamily;
  seniority?: "intern" | "junior" | "mid" | "senior" | "lead" | "unknown";
  workMode?: "individual_contributor" | "collaborative" | "managerial" | "research" | "sales" | "service" | "creative" | "unknown";

  coreWorkObjects: string[];
  typicalTasks: string[];
  commonDeliverables: string[];
  successMetrics: string[];
  collaborationObjects: string[];
  riskTypes: string[];

  competencyArchetypes: CompetencyArchetype[];
  evidenceSlots: EvidenceSlot[];
  strategyHints: StrategyHint[];

  source: "dynamic_jd" | "user_input" | "role_template" | "hybrid";
  confidence: number;
};
```

### 10.3 RoleFamily

`RoleFamily` 不是硬编码岗位，而是职业工作形态分类。一个岗位可以命中多个职业族。

```ts
type RoleFamily =
  | "product_business"
  | "operations_growth"
  | "engineering"
  | "data_analytics"
  | "design_creative"
  | "marketing_brand"
  | "sales_customer"
  | "consulting_strategy"
  | "finance_risk"
  | "hr_admin"
  | "research_academic"
  | "education_training"
  | "medical_healthcare"
  | "legal_compliance"
  | "supply_chain_manufacturing"
  | "public_service"
  | "general";
```

如果模型无法稳定判断职业族，使用 `general`，但仍然基于岗位文本生成能力和证据槽。

### 10.4 CompetencyArchetype

能力原型用于跨职业复用，避免为每个岗位写一套逻辑。

```ts
type CompetencyArchetype =
  | "problem_framing"
  | "domain_knowledge"
  | "execution_delivery"
  | "collaboration_influence"
  | "analytical_reasoning"
  | "technical_depth"
  | "customer_user_understanding"
  | "commercial_judgment"
  | "creative_solution"
  | "communication_expression"
  | "ownership_resilience"
  | "learning_reflection"
  | "compliance_risk_awareness"
  | "leadership_planning";
```

任意岗位的能力模型都应映射到这些能力原型，再叠加岗位自身的动态能力描述。

### 10.5 通用策略如何适配任意职业

策略库不问“这是产品经理还是前端”，而问：

- 这个岗位的核心工作对象是什么？
- 这个岗位交付什么结果？
- 这个岗位如何衡量成功？
- 这个岗位常见风险是什么？
- 这个岗位需要和谁协作？
- 这个岗位最需要证明哪些能力原型？

示例：

```text
用户输入：供应链计划专员
系统生成：
- roleFamily: supply_chain_manufacturing
- coreWorkObjects: 需求预测、库存、供应商、交付周期
- successMetrics: 缺货率、库存周转、准时交付率、预测准确率
- competencyArchetypes: analytical_reasoning, execution_delivery, collaboration_influence, risk_awareness

追问就不再问泛泛的“你做了什么”，而是问：
“你当时如何判断预测偏差来自需求变化、供应延迟还是库存策略问题？”
```

```text
用户输入：新媒体编导
系统生成：
- roleFamily: design_creative / marketing_brand
- coreWorkObjects: 选题、脚本、拍摄、剪辑、传播效果
- successMetrics: 完播率、互动率、转化、涨粉、品牌一致性
- competencyArchetypes: creative_solution, customer_user_understanding, execution_delivery, analytical_reasoning

追问：
“这个选题最后效果好，你怎么判断是脚本结构、渠道分发还是热点本身带来的？”
```

### 10.6 职业族策略包

职业族策略包只提供倾向，不写死具体岗位。

```ts
type RoleFamilyStrategyPack = {
  roleFamily: RoleFamily;
  preferredEvidenceCategories: EvidenceCategory[];
  commonQuestionShapes: QuestionShape[];
  commonRiskProbes: string[];
  metricHints: string[];
  collaborationHints: string[];
};
```

职业族策略包可以帮助系统更快生成追问，但不能阻止动态岗位模型覆盖它。

优先级：

```text
用户提供 JD / 岗位描述
> 动态岗位模型
> 职业族策略包
> 通用能力原型
> fallback 通用行为面试
```

### 10.7 扩展原则

新增职业时，不应该新增大量 if/else，而应该：

1. 从岗位文本生成 `CareerProfile`。
2. 映射 `RoleFamily` 和 `CompetencyArchetype`。
3. 生成岗位专属 `EvidenceSlot`。
4. 复用通用策略库。
5. 必要时增加一个职业族策略包，而不是写死单个岗位。

验收标准：

- 输入任意岗位名称，系统都能生成基本可用的 `CareerProfile`。
- 输入任意 JD，系统能提取工作对象、任务、交付物、指标和风险。
- 策略选择不能依赖固定岗位枚举。
- 预置岗位删除后，系统仍能基于用户输入岗位运行。
- 文档和代码不得把“产品/运营/数据/前端”写成唯一支持范围。

## 11. 策略选择算法

策略选择不能随机，也不能只按用户选择的比例。

建议使用打分式选择：

```text
strategy_score =
  evidence_gap_score
  + competency_priority_score
  + style_preference_score
  + stage_fit_score
  + anchor_quality_score
  + freshness_score
  - repetition_penalty
  - risk_penalty
```

### 11.1 evidence_gap_score

证据缺口越关键，分越高。

规则：

- 必填 EvidenceSlot 缺失：高分。
- 只 mentioned，没有 supported：中高分。
- 已 strong：低分。
- contradictory：优先澄清或压力追问。

### 11.2 competency_priority_score

来自岗位模型和用户配置。

规则：

- 用户加权能力提高优先级。
- JD 强调能力提高优先级。
- 已经连续问过 2 轮的能力降权。

### 11.3 style_preference_score

来自用户选择的面试风格和问题类型占比。

规则：

- 当前问题类型使用不足，提高对应策略。
- 当前问题类型已超额，降低对应策略。
- 压力型风格提高 challenge 策略，但仍受安全上限约束。

### 11.4 stage_fit_score

面试阶段影响策略：

- 开场：公司理解、动机、项目概览。
- 前段：澄清、STAR 补齐。
- 中段：证据、深度、岗位匹配。
- 后段：压力、复盘、终面风格。
- 收尾：反思、下一步、补缺口。

### 11.5 freshness_score

避免反复问同一种问题。

规则：

- 同一 strategy 连续使用降权。
- 同一 EvidenceSlot askCount 超过 2 降权。
- 同一问题形态近 3 轮使用过降权。

## 12. QuestionShape 问题形态

问题形态是把策略变成问题的模板骨架。

```ts
type QuestionShape =
  | "open_expand"
  | "clarify_reference"
  | "ask_specific_action"
  | "ask_metric"
  | "ask_tradeoff"
  | "ask_counterfactual"
  | "challenge_attribution"
  | "ask_reflection"
  | "connect_company"
  | "connect_role"
  | "recover_narrow";
```

每种形态都有不同表达规则。

示例：`ask_metric`

```text
输入：
- anchor: "上线后大家反馈不错"
- target: "结果指标"
- style: standard

输出倾向：
你刚才说上线后反馈不错，具体用哪个数据或反馈验证这个结果？
```

示例：`challenge_attribution`

```text
输入：
- anchor: "转化率提升了"
- target: "归因边界"
- style: pressure

输出倾向：
转化率提升可能有多种原因，你怎么证明主要来自你的动作？
```

## 13. Prompt 渲染方式

LLM prompt 不再直接塞一堆原则，而是塞结构化 `QuestionPlan`。

### 13.1 Prompt 输入

```text
你是实时语音面试官。请根据 QuestionPlan 生成一条中文追问。

QuestionPlan:
- strategyId: pressure_attribution_probe
- methodology: Bar Raiser / Behavioral Event Interview
- competency: 数据结果
- evidenceTarget: 结果归因
- anchor: 用户刚才说“上线后反馈不错”
- askIntent: 检查结果是否有可验证指标和归因边界
- questionShape: challenge_attribution
- pressureLevel: 2
- style: pressure

约束：
- 只输出一个问题。
- 不超过 70 个汉字。
- 必须指向 anchor。
- 不输出分析。
- 不攻击候选人。
```

### 13.2 Prompt 输出

```text
你说上线后反馈不错，怎么证明这个结果主要来自你的动作？
```

## 14. questionTrace 升级

`questionTrace` 需要扩展为正式追问决策记录。

```ts
type QuestionTraceItem = {
  questionId: string;
  turnIndex: number;
  question: string;

  stage: InterviewStage;
  competencyId: string;
  competencyName: string;

  strategyId: string;
  strategyName: string;
  methodologyIds: string[];
  questionStyleId: string;
  interviewStyleId: string;
  pressureLevel: number;

  anchor: QuestionAnchor;
  evidenceTarget: EvidenceTarget;
  expectedEvidence: ExpectedEvidence[];

  missingEvidenceBeforeQuestion: EvidenceGap[];
  coveredEvidenceBeforeQuestion: EvidenceItem[];

  selectedBecause: string;
  alternativesConsidered?: Array<{
    strategyId: string;
    reasonNotSelected: string;
  }>;

  createdAt: string;
};
```

评价 Agent 应使用这些字段判断：

- 系统是否给过补证据机会。
- 是否过早压力追问。
- 是否只追一个维度导致不公平。
- 用户低分是能力不足，还是系统采证不足。

## 15. 替换当前粗糙设计

### 15.1 替换关键词覆盖

当前：

```text
关键词命中 -> requirement covered
```

替换为：

```text
回答文本
-> EvidenceExtractor
-> EvidenceSlot 状态更新
-> EvidenceSnapshot
-> StrategySelector
```

### 15.2 替换简单提问方式权重

当前：

```text
open/evidence/pressure 按占比调度
```

替换为：

```text
面试风格 + 阶段 + 证据状态 + 能力权重 + 近几轮重复情况
-> 策略打分
-> 选择专业策略
```

### 15.3 替换泛 prompt 原则

当前：

```text
请基于上一轮回答追问，优先补齐证据
```

替换为：

```text
QuestionPlan 指定：
- 方法论
- 策略
- 证据目标
- 锚点
- 问题形态
- 风格
- 禁止动作
LLM 只负责自然表达
```

### 15.4 替换单一公司匹配

当前：

```text
公司资料进入上下文，偶尔追问公司理解
```

替换为：

```text
company_fit 作为独立 EvidenceSlot 和 Strategy
只评价准备意识、业务连接和岗位动机
未核验资料不做事实判断
```

## 16. 数据结构建议

### 16.1 FollowUpStrategy

```ts
type FollowUpStrategy = {
  id: string;
  name: string;
  category: StrategyCategory;
  methodologyIds: string[];

  applicableStages: InterviewStage[];
  applicableRoles?: string[];
  applicableCompetencyCategories?: string[];
  applicableEvidenceCategories: EvidenceCategory[];

  preferredStyles: InterviewStyleId[];
  questionStyleId: QuestionStyleId;
  pressureLevel: 0 | 1 | 2 | 3;

  triggerConditions: StrategyCondition[];
  suppressConditions: StrategyCondition[];

  questionShapes: QuestionShape[];
  expectedEvidence: ExpectedEvidence[];

  promptHints: string[];
  disallowedMoves: string[];
};
```

### 16.2 StrategyCondition

```ts
type StrategyCondition = {
  type:
    | "evidence_status"
    | "answer_length"
    | "has_metric"
    | "has_role_contribution"
    | "has_contradiction"
    | "company_card_available"
    | "resume_anchor_available"
    | "recent_strategy_used"
    | "stage";
  operator: "eq" | "neq" | "gt" | "lt" | "includes" | "missing";
  value: unknown;
  weight?: number;
};
```

### 16.3 StrategySelectionResult

```ts
type StrategySelectionResult = {
  selected: FollowUpStrategy;
  score: number;
  scoreBreakdown: Record<string, number>;
  selectedBecause: string;
  alternatives: Array<{
    strategyId: string;
    score: number;
    reasonNotSelected: string;
  }>;
};
```

## 17. 内置策略清单

第一版正式策略库建议至少包含以下策略，不低于 30 个。

通用行为面试：

- `star_situation_clarify`
- `star_task_clarify`
- `star_action_probe`
- `star_result_probe`
- `soar_obstacle_probe`
- `car_problem_reframe`
- `behavioral_specific_event_probe`

证据追问：

- `personal_contribution_probe`
- `metric_validation_probe`
- `user_feedback_probe`
- `before_after_comparison_probe`
- `decision_basis_probe`
- `collaboration_detail_probe`
- `risk_handling_probe`

深度追问：

- `tradeoff_probe`
- `alternative_solution_probe`
- `constraint_probe`
- `root_cause_probe`
- `boundary_condition_probe`

压力追问：

- `attribution_challenge`
- `data_source_challenge`
- `role_ownership_challenge`
- `logic_gap_challenge`
- `counterfactual_challenge`

复盘追问：

- `failure_reflection_probe`
- `redo_decision_probe`
- `learning_transfer_probe`
- `next_iteration_probe`

公司与岗位匹配：

- `company_business_connection_probe`
- `company_motivation_probe`
- `role_fit_evidence_probe`
- `jd_requirement_match_probe`

恢复策略：

- `short_answer_recovery`
- `asr_unclear_recovery`
- `candidate_stuck_recovery`
- `network_resume_recovery`

岗位专属策略另行扩展，不能混在通用策略里。

## 18. 验收标准

功能验收：

- 用户选择不同面试风格后，同一证据缺口会生成明显不同的问题路径。
- 压力风格不只是语气更硬，而是更常触发归因、边界、矛盾挑战。
- 轻松风格不只是语气更温和，而是更常触发澄清、收窄、引导策略。
- 同一 EvidenceSlot 不会被连续追问超过 2 次，除非存在矛盾。
- 每轮 `questionTrace` 都包含 `strategyId`、`methodologyIds`、`evidenceTarget`、`anchor`、`selectedBecause`。
- 报告可以引用 `questionTrace` 判断用户是否已经被追问过某个证据。

质量验收：

- 至少覆盖 30 个通用策略。
- 至少覆盖 10 个职业族策略包，但职业族策略包只能作为倾向，不能成为硬编码岗位分支。
- 任意用户输入岗位都能生成 `CareerProfile`、`EvidenceSlot` 和可用 `QuestionPlan`。
- 每个策略有触发条件、抑制条件、期望证据、问题形态和禁用动作。
- 至少有 20 个可回放测试样本验证策略选择。

体验验收：

- 面试中不再连续出现“你能具体讲讲吗”这类泛问题。
- 问题必须能听出当前风格差异。
- 问题必须指向上一轮回答、简历、公司或岗位中的具体锚点。
- 用户回答短或卡住时，系统能恢复，而不是继续压力追问。

## 19. 推荐实施顺序

第一阶段：策略库骨架

1. 新增 `followup/models.py`。
2. 定义 `QuestionPlan`、`FollowUpStrategy`、`EvidenceSlot`、`StrategySelectionResult`。
3. 新增 `strategy_library.py`，先录入 30 个通用策略。
4. 新增 `strategy_selector.py`，实现打分选择。

第二阶段：证据状态机

1. 新增 `EvidenceSlot` 状态更新。
2. 将关键词命中降级为弱信号。
3. 增加规则判断：数字、角色、动作、结果、前后对比、归因。
4. 后续再加 LLM evidence judge。

第三阶段：Orchestrator 接入

1. `build_question_trace()` 升级为基于 `QuestionPlan`。
2. `build_followup_prompt()` 改为渲染 `QuestionPlan`。
3. 每轮保存完整 `questionTrace[]`。
4. 保持前端现有 `question.plan` 事件兼容。

第四阶段：职业通用化策略

1. 实现 `CareerProfile` 动态生成。
2. 实现 `RoleFamily` 与 `CompetencyArchetype` 映射。
3. 实现职业族策略包。
4. 用任意岗位输入验证策略选择，而不是只测预置岗位。

第五阶段：测试和调优

1. 建立 20 个可回放回答样本。
2. 测试不同风格下策略差异。
3. 测试证据覆盖变化。
4. 测试评价 Agent 能读取 `questionTrace`。

## 20. 方法论知识库与 RAG

追问策略库可以先用结构化策略配置落地，但如果目标是长期专业化，建议建设一个“面试方法论知识库”。

这里的知识库不应该是把书籍或论文全文直接塞进 RAG，而应该沉淀为可引用、可维护、可授权的 Methodology Cards。

### 20.1 是否必须做 RAG

短期不是必须。

第一阶段可以先把成熟方法论人工整理为结构化策略，例如 STAR、CAR、SOAR、行为面试、漏斗追问、压力面、案例面、技术深挖、公司匹配面。

但中长期建议做 RAG，因为它能解决三个问题：

- 策略来源可追溯，不是模型临场编。
- 新职业、新面试类型可以持续扩展。
- 后续可以针对不同行业、岗位层级、公司面试风格做更专业的策略选择。

### 20.2 用户需要提供什么

如果用户愿意提供材料，最有价值的不是整本书，而是以下内容：

- 合法可使用的面试方法论资料。
- 读书笔记和摘要。
- 公开课程笔记。
- 真实面试复盘。
- 招聘官访谈整理。
- 岗位面试题分析。
- 公司面经中总结出的追问模式。
- 学术论文或公开报告中的评价框架。

不建议直接上传未授权的整本版权书全文作为 RAG 语料。更合适的方式是：用户整理读书笔记、章节摘要、方法论卡片，或提供自己拥有使用权的资料。

### 20.3 Methodology Card

知识库的最小单元应是 `MethodologyCard`。

```ts
type MethodologyCard = {
  id: string;
  title: string;
  sourceType: "book_note" | "paper" | "article" | "interview_review" | "internal_note" | "public_framework";
  sourceTitle?: string;
  sourceUrl?: string;
  licenseNote?: string;

  applicableScenarios: string[];
  applicableRoleFamilies: RoleFamily[];
  applicableCompetencyArchetypes: CompetencyArchetype[];

  corePrinciple: string;
  interviewMoves: Array<{
    name: string;
    purpose: string;
    whenToUse: string;
    questionShapes: string[];
    expectedEvidence: string[];
    risks: string[];
  }>;

  antiPatterns: string[];
  examples: Array<{
    context: string;
    weakQuestion: string;
    strongQuestion: string;
  }>;
};
```

### 20.4 RAG 使用方式

RAG 不应该每轮直接让 LLM 从资料里自由生成问题。正确方式是：

```text
SessionState
-> StrategySelector 先选策略类别
-> MethodologyRetriever 检索相关 Methodology Cards
-> QuestionPlanBuilder 将方法论卡片转成结构化 QuestionPlan
-> PromptRenderer 让 LLM 生成自然问题
```

也就是说，RAG 是给策略库补充专业依据，不是绕过策略库。

### 20.5 优先建设资料类型

建议优先整理这些方向：

- 结构化行为面试：STAR、CAR、SOAR、BEI。
- 咨询和商业分析面：Case Interview、假设驱动、MECE、指标拆解。
- 技术面：系统设计、代码评审、故障排查、性能优化、测试质量。
- 产品面：用户问题、需求验证、优先级、指标、增长、商业化。
- 数据面：指标口径、数据质量、归因、实验、决策影响。
- 压力面：归因挑战、边界条件、反事实、矛盾澄清。
- 终面：动机、成熟度、价值观、长期潜力。

这些资料整理成卡片后，系统可以用于全部职业，而不是只服务某几个预置岗位。

### 20.6 验收标准

- 每条策略能追溯到一个或多个 `MethodologyCard`，或明确标记为 internal heuristic。
- RAG 检索结果只影响 `QuestionPlan`，不能直接跳过策略选择。
- 资料来源必须有来源类型和授权说明。
- 用户删除某个资料源后，系统仍能降级到通用策略库。
- 不允许把未经授权的书籍全文作为默认知识库。

## 21. 一句话结论

```text
追问策略库不是题库，也不是更长的 prompt。
它应该是一个专业采证决策层：
先判断当前缺什么证据，再选择合适的面试方法论和追问策略，
最后让 LLM 只负责把这个策略自然地问出来。
```

# 面试系统 Agent 正式版技术方案与执行规划

Status: `ready-for-implementation`

## 0. 真实可用原则

本版本不再按“能演示的 demo”作为标准，而是按“真实可用的面试系统 Agent”设计和验收。所谓真实可用，不是所有外部 Agent 都已经接入，而是当前面试系统内部已经具备完整闭环、来源透明、可配置、可解释、可扩展，并且不能用硬编码样例伪装成产品能力。

硬性原则：

- 公司信息不能主要依赖用户手工填写。用户最多输入公司名称、目标岗位方向、可选官网/JD 链接或补充资料；系统负责生成公司情报卡，并标明来源和可信度。
- 没有来源支撑的公司事实不能当作确定事实使用。DeepSeek 可以帮助整理和生成“待核验公司情报卡”，但必须在 UI 和面试上下文中标记为待确认；真正可用版本要优先接官方资料、招聘页、用户上传材料或后续联网检索/RAG。
- 岗位 JD 默认走通用岗位模型，不绑定某一家公司的 JD。用户如果提供具体 JD，则作为覆盖项合并到通用岗位能力模型中。
- TTS 声音控制不是调试参数，而是正式产品能力。至少要支持性别、年龄风格、音色、语速、音调、音量、语气/面试官风格，并让这些配置影响语音和提问措辞。
- 降级可以存在，但必须透明。比如无法获取公司来源时，系统进入“待核验公司准备模式”，不能假装已经掌握真实公司信息。
- 面试报告必须引用本轮真实回答、简历证据和配置目标，不能生成泛泛而谈的模板化评价。

## 1. 背景与目标

当前项目已经有一条可运行的实时语音面试链路：

```text
LiveKit 音频房间
-> 本地 FunASR 转写
-> 回答结束判断
-> DeepSeek 生成追问
-> Edge TTS 播放
-> 结构化报告
```

接下来开发安排发生变化：整体产品拆成四个 Agent，但短期内其他 Agent 不会接入，因此面试系统 Agent 需要先独立承担“正式可用面试训练”的完整闭环。

四个 Agent 的长期分工是：

- 公司岗位推荐 Agent：公司、岗位、路径推荐。
- 简历智能生成 Agent：简历解析、简历优化、经历结构化。
- 能力评估与训练建议 Agent：能力画像、训练计划、进步跟踪。
- 面试系统 Agent：面试配置、实时语音训练、追问、面试报告。

短期因为其他 Agent 接不进来，面试系统 Agent 需要先独立承接公司情报、通用岗位模型、简历解析、能力评估和训练建议的最小闭环。这里不能用假数据模拟上游输入，而是要用当前可获得的真实来源、用户提供材料和明确标记的待核验内容，形成一个可以独立使用的产品版本。

## 2. 两天半内的交付目标

本轮目标不是做“玩具原型”，而是做一个能真实跑通的正式版 MVP：

用户进入系统后，可以配置目标公司、目标岗位、JD、简历、能力训练重点、提问方式占比、面试氛围和面试官声音；配置完成后开始实时语音面试。AI 面试官先考察用户对公司的了解，再基于岗位能力模型、简历内容和提问策略进行多轮追问。结束后生成结构化报告，包含能力模型评分、公司了解加分项、简历证据引用、问题诊断和训练建议。

必须完成的功能：

- 目标公司情报卡生成、来源标记与“公司了解”开场问题。
- 岗位能力模型与能力训练重点选择。
- 提问方式占比配置。
- 面试氛围与面试官声音/语速配置。
- 简历文本解析，并基于简历内容追问。
- 面试前配置页。
- 面试执行逻辑接入配置。
- 结构化报告升级。

暂不做但保留接口的功能：

- 账号体系。
- 数据库持久化。
- 多用户历史训练中心。
- 全自动联网抓取和多源交叉核验公司信息。
- 复杂 PDF 简历高精度解析。
- 与其他 Agent 的真实服务调用。

## 3. 产品流程

正式版面试系统 Agent 的用户流程：

```text
进入页面
-> 填写/选择目标公司
-> 填写/选择目标岗位与 JD
-> 粘贴/上传简历
-> 查看岗位能力模型
-> 选择加强训练能力
-> 设置提问方式占比
-> 设置面试氛围与声音
-> 开始面试
-> 公司了解开场问题
-> 简历驱动 + 能力模型驱动追问
-> 结束面试
-> 生成能力报告与训练建议
```

关键体验原则：

- 面试不是泛聊，所有问题都要能追溯到公司、岗位、简历或能力模型。
- 用户选择的训练重点必须明显影响问题分布。
- 提问方式占比必须可观测，调试台要显示每轮问题类型。
- 简历内容必须进入追问，而不是只作为装饰字段。
- 报告必须引用用户回答和简历证据，不能泛泛而谈。

## 4. 系统架构

现有架构保留，不大改实时语音链路：

```text
web/src/main.tsx
  - 面试前配置页
  - 语音面试页
  - 报告页
  - 调试台

server/token_server.py
  - /token
  - /health
  - /tts
  - /interview-options
  - /parse-resume

server/agent.py
  - LiveKit Agent
  - 接收 start_session 配置
  - 音频处理
  - 转写
  - 回答结束判断
  - 调用 InterviewOrchestrator

server/interview/
  - models.py
  - configs.py
  - profile_builder.py
  - resume_parser.py
  - question_scheduler.py
  - orchestrator.py
  - evaluator.py
```

新增核心模块：

- `profile_builder.py`：把前端配置、公司信息、岗位模型、JD、简历解析结果合成为 `InterviewProfile`。
- `resume_parser.py`：把用户简历文本解析成项目、经历、技能、教育、证据点。
- `question_scheduler.py`：根据能力权重和提问方式占比决定下一轮问什么。
- `configs.py`：维护岗位模板、能力模型、提问方式、氛围配置。

## 5. 核心数据模型

### 5.1 InterviewSetup

前端传给后端的面试配置。

```python
@dataclass
class InterviewSetup:
    company: CompanyInput
    job: JobInput
    resume_text: str
    selected_capabilities: dict[str, float]
    question_style_mix: dict[str, float]
    atmosphere_id: str
    voice_id: str
    tts_rate: str
```

### 5.2 CompanyInput

```python
@dataclass
class CompanyInput:
    name: str
    industry: str = ""
    business: str = ""
    products: str = ""
    culture: str = ""
    recent_info: str = ""
```

用途：

- 开场先问用户对公司的了解。
- 报告中生成 `company_fit_bonus`。
- 追问中加入公司业务语境。

### 5.3 JobInput

```python
@dataclass
class JobInput:
    job_id: str
    title: str
    jd_text: str = ""
```

用途：

- 选择内置岗位模板。
- 从 JD 中提取关键词和岗位任务。
- 覆盖默认能力权重。

### 5.4 ResumeProfile

```python
@dataclass
class ResumeProfile:
    raw_text: str
    education: list[str]
    experiences: list[ResumeExperience]
    projects: list[ResumeProject]
    skills: list[str]
    achievements: list[str]
```

### 5.5 ResumeProject

```python
@dataclass
class ResumeProject:
    name: str
    role: str
    description: str
    actions: list[str]
    results: list[str]
    keywords: list[str]
```

短期解析方式：

- 不追求 100% 准确。
- 用规则 + LLM 轻量解析。
- 如果解析失败，保留原文并让 LLM 基于原文追问。

### 5.6 CapabilityModel

岗位能力模型。

```python
@dataclass
class CapabilityDimension:
    id: str
    name: str
    description: str
    default_weight: float
    evidence_requirements: list[EvidenceRequirement]
    rubric: Rubric
```

前端展示为雷达图或能力条。

短期实现：

- 雷达图可以先用 SVG。
- 如果时间紧，先用能力条 + 权重滑块，后续再替换为雷达图。

### 5.7 QuestionStyleMix

提问方式占比。

```python
QUESTION_STYLES = {
    "open": "开放提问",
    "clarification": "澄清追问",
    "evidence": "证据追问",
    "pressure": "压力追问",
    "reflection": "复盘追问",
    "company_fit": "公司匹配追问",
}
```

默认占比：

```json
{
  "open": 0.20,
  "clarification": 0.15,
  "evidence": 0.30,
  "pressure": 0.15,
  "reflection": 0.15,
  "company_fit": 0.05
}
```

## 6. 面试前配置页设计

配置页分成 6 个区域。

### 6.1 目标公司

字段：

- 公司名称，必填。
- 行业，可选。
- 主营业务，可选。
- 主要产品，可选。
- 公司文化，可选。
- 近期信息，可选。

默认样例：

- 公司：字节跳动。
- 岗位：产品经理实习生。
- 业务：内容平台、推荐系统、商业化、AI 产品。

### 6.2 目标岗位与 JD

字段：

- 岗位下拉。
- 岗位名称。
- JD 文本。

内置岗位：

- 产品经理。
- 前端开发。
- 数据分析。
- 运营。
- UI/UX 设计。

### 6.3 简历

短期支持：

- 粘贴简历文本。
- 上传 `.txt` 或 `.md`。

PDF 上传如果当前依赖缺失，可以先不做或只做最佳努力。

### 6.4 能力训练重点

展示岗位能力模型：

- 默认显示 5-6 个能力维度。
- 每个能力有默认权重。
- 用户可以勾选“本轮加强”。
- 勾选后该能力权重提高。

实现方式：

- 初版使用能力条和开关。
- 正式展示可以做 SVG 雷达图。

### 6.5 提问方式占比

展示 6 种问题类型：

- 开放提问。
- 澄清追问。
- 证据追问。
- 压力追问。
- 复盘追问。
- 公司匹配追问。

交互：

- 提供默认配置。
- 用户可用滑块调整。
- 前端自动归一化为 100%。

### 6.6 面试氛围与声音

氛围：

- 轻松引导。
- 标准正式。
- 压力挑战。
- 终面风格。

声音：

- 语音角色。
- 语速。
- 语气提示词。

短期 Edge TTS 能做：

- voice。
- rate。

不能稳定做：

- 真实情绪语调。
- 多维度语气控制。

因此短期做成“语音 + 语速 + 面试官风格 prompt”。

## 7. 面试执行逻辑

### 7.1 开场阶段

第一轮固定为公司理解问题：

```text
我们先从目标公司开始。你对 {company_name} 的业务、产品或文化有什么了解？为什么你想投这个岗位？
```

该问题用于：

- 判断用户是否做过公司准备。
- 生成 `company_fit_bonus`。
- 后续追问可结合用户回答里的公司信息。

如果公司信息为空，则降级：

```text
你可以先说说你为什么想投这个岗位，以及你对目标公司的了解程度。
```

### 7.2 主面试阶段

从第二轮开始进入岗位能力追问。

每一轮问题选择流程：

```text
获取当前 InterviewState
-> 计算各能力证据覆盖度
-> 根据用户选择权重得到能力优先级
-> 根据提问方式占比选择 question_style
-> 结合简历项目和上一轮回答生成追问
-> 记录 question_trace
```

### 7.3 QuestionScheduler

核心逻辑：

```python
class QuestionScheduler:
    def next_question_plan(state, profile) -> QuestionPlan:
        capability = choose_capability(state, profile)
        style = choose_question_style(state, profile)
        resume_anchor = choose_resume_anchor(state, profile, capability)
        return QuestionPlan(capability, style, resume_anchor)
```

能力选择：

- 用户加强训练的能力优先。
- 证据缺失最多的能力优先。
- 太久没问过的能力补问。
- 已连续追问 2-3 次的能力降权，避免卡死。

提问方式选择：

- 根据目标占比和当前已使用次数做“欠账调度”。
- 例如压力追问目标 20%，当前只用了 5%，后续提高概率。

### 7.4 简历驱动追问

简历内容进入问题生成：

- 开放问题优先选择简历里的核心项目。
- 证据追问要求补充项目细节、数据、个人贡献。
- 压力追问质疑结果归因、数据来源、取舍依据。
- 复盘追问要求说明不足、改进和重做方案。

示例：

```text
你简历里提到“校园二手交易小程序”，刚才也提到了发布流程优化。你能具体说说你当时如何判断哪些字段应该必填，哪些可以选填吗？
```

## 8. Prompt 约束设计

### 8.1 追问 Prompt 必须包含

- 当前岗位。
- 公司信息。
- JD 摘要。
- 简历摘要。
- 当前能力维度。
- 当前提问方式。
- 上一轮回答。
- 已问问题摘要。
- 证据缺口。

### 8.2 追问输出约束

- 只输出一句中文问题。
- 不输出解释。
- 不输出评分。
- 不超过 70 个汉字。
- 必须引用或指向用户上一轮回答、简历或公司信息。
- 必须符合当前提问方式。

### 8.3 提问方式示例

开放提问：

```text
你可以展开讲讲这个项目的背景和你负责的核心部分吗？
```

澄清追问：

```text
你刚才说“用户反馈很多”，这些反馈具体来自哪里？
```

证据追问：

```text
这个优化最终带来了哪些可验证的数据变化？
```

压力追问：

```text
如果没有你做的动作，这个结果还会发生吗？你怎么证明？
```

复盘追问：

```text
如果让你重新做一次，你会优先改哪一个决策？
```

公司匹配追问：

```text
你提到了解这家公司重视效率，这和你这个项目经历有什么对应关系？
```

## 9. 报告设计

报告结构：

```json
{
  "summary": "",
  "company_fit_bonus": {
    "score": 0,
    "reason": "",
    "evidence": ""
  },
  "ability_model": {
    "capability_id": 0
  },
  "question_style_usage": {
    "open": 0,
    "pressure": 0
  },
  "dimensions": [],
  "resume_evidence": [],
  "evidence_gaps": [],
  "main_weakness": "",
  "training_plan": {
    "theme": "",
    "goal": "",
    "tasks": [],
    "next_interview_focus": ""
  }
}
```

前端展示：

- 总结。
- 公司了解加分项。
- 能力雷达图或能力条。
- 提问方式实际占比。
- 维度评分。
- 简历证据引用。
- 证据缺口。
- 训练计划。

## 10. 前端实现规划

### 10.1 页面状态

新增页面阶段：

```ts
type AppView = "setup" | "interview" | "report";
```

### 10.2 配置数据

```ts
interface InterviewSetup {
  company: CompanyInput;
  job: JobInput;
  resumeText: string;
  selectedCapabilities: Record<string, number>;
  questionStyleMix: Record<string, number>;
  atmosphereId: string;
  voiceId: string;
  ttsRate: string;
}
```

### 10.3 UI 组件

建议拆分：

- `SetupPanel`
- `CompanyForm`
- `JobForm`
- `ResumeInput`
- `CapabilityWeights`
- `QuestionStyleMixer`
- `AtmosphereSettings`
- `InterviewRoom`
- `ReportPanel`

当前项目如果时间紧，可以先在 `main.tsx` 内实现，完成后再拆文件。

## 11. 后端实现规划

### 11.1 models.py

新增：

- `CompanyProfile`
- `ResumeProfile`
- `JobProfile`
- `CapabilityDimension`
- `QuestionPlan`
- `QuestionTrace`
- `InterviewProfile`

### 11.2 configs.py

新增：

- `JOB_PROFILES`
- `QUESTION_STYLES`
- `ATMOSPHERE_PROFILES`
- `VOICE_PROFILES`
- `DEFAULT_INTERVIEW_SETUP`

### 11.3 resume_parser.py

短期能力：

- 从文本提取项目、经历、技能、结果数字。
- LLM 解析失败时返回规则解析结果。

### 11.4 profile_builder.py

职责：

- 合并用户配置。
- 生成能力权重。
- 生成 JD 摘要。
- 生成简历摘要。
- 生成最终 `InterviewProfile`。

### 11.5 question_scheduler.py

职责：

- 根据能力权重和证据缺口选能力。
- 根据提问方式占比选问题类型。
- 选择简历锚点。

### 11.6 orchestrator.py

职责：

- 管理面试状态。
- 记录每轮问题和回答。
- 生成追问 prompt。
- 判断是否进入报告。

### 11.7 evaluator.py

职责：

- 生成报告 prompt。
- 处理样本不足。
- 解析 JSON。
- 兜底报告。

## 12. 执行排期

### Day 1 上午：配置页与数据模型

目标：

- 前端能配置完整面试画像。
- 后端能接收配置。

任务：

- 新增 `InterviewSetup` 前端状态。
- 做公司信息表单。
- 做岗位/JD 表单。
- 做简历文本输入。
- 做能力训练重点选择。
- 做提问方式占比配置。
- 做氛围和声音配置。
- 后端新增对应 dataclass。

验收：

- 点击开始面试时，调试台能看到完整配置。
- 配置能传到 agent。

### Day 1 下午：ProfileBuilder 与简历解析

目标：

- 配置能转成面试画像。
- 简历内容能被结构化使用。

任务：

- 实现 `resume_parser.py`。
- 实现 `profile_builder.py`。
- 内置岗位能力模型。
- 支持 JD 文本摘要。
- `token_server.py` 提供 `/interview-options` 和 `/parse-resume`。

验收：

- 输入简历文本后能解析出项目、技能、结果。
- 不输入简历时有合理降级。

### Day 1 晚上：公司了解开场

目标：

- 面试第一问围绕公司了解。

任务：

- `orchestrator` 加入 `stage = company_intro`。
- 第一问固定为公司理解。
- 第一轮回答记录为 `company_fit_evidence`。
- 后续报告能使用该证据。

验收：

- 开始面试第一问一定是公司了解。
- 回答后第二问进入岗位/简历追问。

### Day 2 上午：动态追问调度器

目标：

- 问题分布受能力重点和提问方式占比控制。

任务：

- 实现 `QuestionScheduler`。
- 记录 `QuestionTrace`。
- 每轮问题带上能力、问题类型、简历锚点。
- 调试台展示 trace。

验收：

- 改能力权重后，追问明显偏向对应能力。
- 改提问方式占比后，问题类型分布变化。

### Day 2 下午：报告升级

目标：

- 报告包含公司、能力、简历和训练建议。

任务：

- 升级 `evaluator.py` prompt。
- 增加 `company_fit_bonus`。
- 增加 `question_style_usage`。
- 增加 `resume_evidence`。
- 前端报告页展示新字段。

验收：

- 结束面试后生成完整报告。
- 报告引用用户回答或简历信息。
- 样本不足时不生成假评分。

### Day 2 晚上：声音和氛围

目标：

- 用户选择的氛围和声音生效。

任务：

- 面试氛围进入追问 prompt。
- 声音和语速进入 TTS 请求。
- 前端可选 voice/rate。

验收：

- 切换语速后 TTS 明显变化。
- 切换压力/轻松后追问语气变化。

### Day 3 上午：演示打磨与测试

目标：

- 可稳定演示。

任务：

- 写默认公司、JD、简历样例。
- 写演示话术。
- 跑 6-10 轮面试。
- 修复配置传输、报告展示、结束状态问题。
- 更新 README。

验收：

- 一键启动后可完成完整面试。
- 面试结束后报告稳定生成。
- 调试台能解释每轮问题为什么这样问。

## 13. 验收标准

功能验收：

- 用户能完成面试前配置。
- 第一问能考察公司了解。
- 简历内容能进入至少 2 个追问。
- 能力重点能影响问题分布。
- 提问方式占比能影响问题类型。
- 面试氛围能影响语气。
- TTS 语速/声音能调整。
- 报告包含公司了解、能力评分、证据缺口和训练计划。

稳定性验收：

- 不输入公司信息也能开始。
- 不输入 JD 也能开始。
- 不输入简历也能开始。
- DeepSeek 失败有兜底提示。
- 简历解析失败不阻塞面试。
- 报告 JSON 解析失败有兜底报告。

体验验收：

- 配置页不显得像调试工具。
- 主面试页保持干净。
- 调试台保留详细日志。
- 结束报告不触发语音播报。

## 14. 技术风险与处理

### 14.1 两天半内范围过大

处理：

- 雷达图先用能力条替代。
- 简历解析先支持文本。
- 公司信息走公司情报卡生成；无来源时必须标记待核验，不能伪装成已核验事实。
- 不做数据库。

### 14.2 追问仍然泛化

处理：

- 每轮问题强制绑定 `QuestionPlan`。
- Prompt 中明确当前能力、问题类型、简历锚点。
- 调试台展示 trace，方便检查。

### 14.3 报告水

处理：

- 报告必须引用回答或简历证据。
- 样本不足直接标记不足。
- 每个评分维度必须有 reason/evidence/improvement。

### 14.4 前端改动过大

处理：

- 先在单文件内完成。
- 功能稳定后再拆组件。

### 14.5 Edge TTS 对细腻语气控制有限

处理：

- 正式数据模型保留 voice/rate/pitch/volume/tone/interviewer_style。
- 当前 Edge TTS 优先落地可用参数；不可用参数必须在调试台记录降级原因。
- 氛围同时控制面试官文本语气和 TTS 声音配置，不能只改文字。

## 15. 推荐实现顺序

优先级从高到低：

1. 面试配置数据结构。
2. 配置页。
3. 公司了解开场问题。
4. 简历文本解析。
5. 能力模型与权重。
6. 提问方式占比。
7. QuestionScheduler。
8. 报告升级。
9. 氛围和声音设置。
10. 演示样例和文档。

## 16. 最终判断

这次升级的关键不是继续优化语音底层，而是把面试系统从“能语音对话”升级成“能围绕公司、岗位、简历和训练目标进行结构化面试”。

如果两天半内只完成一件最重要的事，应该是：

> 建立 InterviewProfile，并让追问和报告都基于它运行。

只要这条主线成立，后续接公司岗位推荐 Agent、简历 Agent、能力评估 Agent 都会自然变成替换输入源，而不是重写面试系统。

## 17. 修订后的公司信息方案

公司信息不能让用户自己承担主要录入责任。这个模块的真实产品形态是“公司情报卡”，用户只给最小目标，系统负责整理、核验和转化为面试上下文。

用户侧只需要提供：

- 公司名称。
- 目标岗位方向。
- 可选的官网、招聘页、JD 链接或用户已有资料。
- 可选的业务线偏好，比如“增长”“商业化”“AI 产品”“ToB SaaS”。

系统侧生成 `CompanyIntelligenceCard`：

```python
class CompanyIntelligenceCard:
    company_name: str
    target_role: str
    summary: str
    business_lines: list[str]
    products_or_services: list[str]
    recent_context: list[str]
    culture_and_values: list[str]
    role_relevant_points: list[str]
    interview_talking_points: list[str]
    company_understanding_questions: list[str]
    source_notes: list[str]
    verification_status: str  # verified | partial | unverified
    confidence: float
```

来源优先级：

- 第一优先级：用户提供的官网、招聘页、JD、公司介绍材料、截图转文字内容。
- 第二优先级：后续接入联网检索或公司岗位推荐 Agent 后，由外部服务返回带来源的公司资料。
- 第三优先级：DeepSeek 根据公司名称生成待核验情报卡，只能用于准备提纲，不能当作确定事实。

面试使用方式：

- 第一问固定考察“你对这家公司/业务的理解”，但问题要来自 `CompanyIntelligenceCard`。
- 报告中单独给出“公司理解加分项”，只评价用户是否表达了业务理解、岗位匹配和动机，不评价无法核验的公司事实。
- 如果公司情报卡是 `unverified`，报告必须提示“公司资料待核验”，并把建议写成准备方向，而不是事实判断。

这样做的原因很简单：真实可用的产品不能让用户自己填公司知识，也不能让模型凭空编公司事实。我们要做的是“系统帮用户准备公司理解”，但所有事实都要有来源或有待核验标记。

## 18. 修订后的通用 JD 与岗位模型方案

岗位 JD 默认通用化，不为某家公司硬编码。每个岗位维护一个通用岗位模板，包含能力模型、典型职责、常见追问方向和评分标准。

核心结构：

```python
class RoleTemplate:
    role_id: str
    display_name: str
    generic_jd: str
    competency_model: list[CompetencyDimension]
    question_bank_seeds: list[str]
    scoring_rubric: dict

class CompetencyDimension:
    key: str
    name: str
    description: str
    default_weight: float
    observable_signals: list[str]
    weak_signals: list[str]
```

如果用户粘贴具体 JD，系统不替换岗位模型，而是做覆盖合并：

- 从 JD 中提取额外职责、技能关键词、业务关键词。
- 调整能力权重，比如 JD 强调数据分析，就提高数据分析维度权重。
- 增加针对 JD 的追问点。
- 报告中标记哪些评分来自通用岗位模型，哪些来自用户提供 JD。

这能保证两个目标同时成立：没有 JD 也能开始真实训练，有 JD 时又能明显变得更贴合。

## 19. 修订后的 TTS 声音控制方案

TTS 声音控制是正式能力，不是调试项。当前技术栈先使用 Edge TTS，但要按产品级 `VoiceProfile` 设计，后续可以无痛切换 Azure Speech、CosyVoice、MiniMax、火山或其它更强的语音服务。

前端必须提供的配置：

- 性别：男声、女声、不强调性别。
- 年龄风格：年轻、成熟、资深。
- 音色：温和、清晰、沉稳、锐利、亲和。
- 语速：慢、正常、快，以及细粒度百分比。
- 音调：低、正常、高。
- 音量：低、正常、高。
- 语气/面试官风格：轻松、正式、压力、鼓励、克制。

后端统一成 `VoiceProfile`：

```python
class VoiceProfile:
    id: str
    label: str
    gender: str
    age_style: str
    voice_name: str
    rate: str
    pitch: str
    volume: str
    tone: str
    interviewer_style_prompt: str
```

实现策略：

- `voice_name` 控制基础音色和性别。
- `rate` 控制语速。
- `pitch` 控制音调。
- `volume` 控制音量。
- `tone` 同时影响 TTS 参数和面试官文本风格。
- 年龄不是一个真实声学参数，要通过音色、语速、音调和措辞组合模拟。
- Edge TTS 如果某些 prosody 参数在本地版本不可用，接口仍然保留字段，并在服务端降级到可用参数，同时在调试台记录降级原因。

必须提供的内置声音档位：

- 温和年轻女面试官：适合默认训练，语气鼓励，语速略快。
- 正式成熟男面试官：适合标准面试，语气克制，语速正常。
- 资深沉稳男面试官：适合高阶岗位，语速略慢，追问更重视结构。
- 清晰压力女面试官：适合压力面试，问题更短更直接，但不能攻击用户。
- 亲和轻松面试官：适合破冰和表达训练，降低压迫感。

验收标准：

- 用户切换声音档位后，下一轮 AI 播报必须明显变化。
- 用户调整语速后，TTS 请求参数必须变化。
- 用户选择压力/轻松/正式语气后，问题文本风格和播报风格都要变化。
- 报告页不触发 TTS 播报。
- AI 播报期间默认不收音、不转写、不追问，避免自问自答。

## 20. 修订后的两天半执行口径

两天半内不做“阉割版”，但要控制实现顺序，先把正式产品骨架打通。

第一阶段：配置闭环真实可用。

- 建立 `InterviewSetup`、`CompanyIntelligenceCard`、`RoleTemplate`、`VoiceProfile` 数据结构。
- 前端做正式配置页：公司目标、岗位模板、JD 覆盖、简历文本、能力权重、提问方式占比、面试氛围、声音档位。
- 后端提供 `/interview-options`、`/company-card`、`/parse-resume`、`/tts-options`。

第二阶段：面试过程真实可用。

- 面试开场绑定公司情报卡。
- QuestionScheduler 同时读取岗位能力、JD 覆盖、简历证据、提问方式占比和历史回答。
- 每轮问题生成都输出 trace，调试台能看到为什么问这个问题。
- AI 播报期间锁定收音，播报结束后自动进入用户回答阶段。

第三阶段：报告真实可用。

- 报告按 10 分制评分。
- 每个能力维度必须包含分数、证据、问题、改进建议。
- 训练计划按 7 天/14 天/30 天给出，不写空泛鸡汤。
- 公司理解、岗位匹配、简历表达、沟通结构分别评价。

最终判断：我们不是把 demo 做厚一点，而是把面试系统 Agent 先做成一个独立可用的产品单元。其它 Agent 未来接入时，只是替换公司资料、简历资料、能力画像和训练建议来源，不改变面试系统的主流程。

# 项目优化路线图

更新日期：2026-06-06

本文档记录当前项目下一阶段最值得做的优化方向。它不是功能愿望清单，而是基于当前代码和产品状态整理出的执行优先级。

当前主线项目是 `livekit-interview-spike`。它已经具备公司资料搜索、岗位模型生成、配置页、LiveKit 实时面试、追问、内置评价和报告展示能力。下一阶段的重点不应该继续堆零散功能，而应该先把现场生成的数据、追问链路、评价输入输出和前端结构稳定下来。

## 1. 当前判断

项目已经从“能演示的实时语音原型”进入“需要产品化收口”的阶段。

目前最有价值的资产是：

- 公司资料可以通过搜索现场生成，并沉淀到配置状态。
- 岗位 JD/岗位模型可以现场生成，并影响后续面试配置。
- 面试过程中已经能生成问题计划、追问原因、能力维度和证据缺口。
- 面试结束后已经能生成报告。
- 前端已经有配置流程、公司资料弹层、实时房间和报告页。

目前最主要的风险是：

- 现场生成的数据还没有统一沉淀成稳定的后端 `SessionState`。
- `questionTrace` 还更像调试事件，没有成为评价 Agent 的正式输入。
- 评价 Agent 分离后，如果没有统一的 `EvaluationRequest`，报告会和追问逻辑脱节。
- 前端 `main.tsx` 过大，新旧组件并存，后续改 UI 容易改错位置。
- 实时语音链路能跑，但断网、重连、TTS、VAD、轮次结束判断还不是生产级。
- 缺少自动化测试和可回放的面试样本，后续每次改动都容易引入体验回归。

## 2. 第一优先级：评价数据闭环

下一步最建议先做：**EvaluationRequest Builder + SessionState Recorder**。

原因是评价 Agent 已经从整体架构里分离出去。只要评价 Agent 是独立模块，当前面试系统就必须提供稳定、完整、可解释的证据包，而不是让评价 Agent 自己重新理解面试过程。

目标链路：

```text
配置页生成数据
-> 面试 SessionState 持续记录
-> 面试结束组装 EvaluationRequest
-> 内置评价器或外部评价 Agent 消费
-> 返回 EvaluationResponse
-> 前端报告展示
```

短期 MVP 要做的事情：

- 在后端维护统一 `SessionState`，至少包含 `companyCard`、`jobModel`、`interviewConfig`、`questionTrace`、`transcript`、`evidenceSnapshot`、`sessionMeta`。
- 每次生成问题计划时，把当前 `build_question_trace()` 的结果写入 `questionTrace[]`。
- 每次用户回答完成时，把问题、回答、能力维度、追问类型和回答元信息写入 `transcript[]`。
- 面试结束时，从 `SessionState` 组装 `EvaluationRequest`。
- 当前内置 `InterviewEvaluator` 先消费这套 `EvaluationRequest`，以后再替换成外部评价 Agent。
- 评价结果通过 adapter 转成当前前端兼容的报告结构。

相关详细契约见：

- `docs/technical/evaluation-agent-contract.md`
- `livekit-interview-spike/server/interview/orchestrator.py`
- `livekit-interview-spike/server/interview/evaluator.py`
- `livekit-interview-spike/server/agent.py`

## 3. questionTrace 是关键桥梁

`questionTrace` 不只是日志，它是追问 Agent 和评价 Agent 之间的关键桥梁。

它要回答的问题是：

- 这一题为什么问？
- 对应哪个能力维度？
- 提问前缺哪些证据？
- 这是开放提问、证据追问、压力追问还是复盘提问？
- 用户是否已经被给过补证据的机会？
- 某个能力低分到底是用户没答出来，还是系统没有采到证据？

如果评价 Agent 只看 transcript，它只能看到用户说了什么，却不知道系统有没有问到位。这样会导致评分过严、误判，或者把采证不足当成能力不足。

因此后续实现时，`questionTrace[]` 必须和 `transcript[]` 通过 `turnIndex` 或 `questionId` 对齐。

### 3.1 追问策略库升级

当前追问逻辑仍然偏“调度器 + prompt”，不同面试风格的差异主要体现在措辞上，问题路径还不够专业。

下一步需要把追问升级为“策略库驱动”：

```text
岗位模型
-> 能力维度
-> 证据状态
-> 面试阶段
-> 面试风格
-> 选择追问策略
-> 生成 QuestionPlan
-> LLM 只负责自然语言表达
```

这部分详细方案见 `follow-up-strategy-library-design.md`。该文档定义了 STAR/CAR/SOAR、行为面试、压力面、公司匹配面、岗位专属追问、证据状态机和 `QuestionPlan` / `FollowUpStrategy` 等结构。

## 4. 第二优先级：前端结构收口

当前 `livekit-interview-spike/web/src/main.tsx` 承载了太多职责，包括首页、配置页、公司资料弹层、实时房间、报告页和旧版配置组件。

下一步建议拆分：

```text
web/src/
  api/
    client.ts
  components/
    home/HomePage.tsx
    setup/SetupWizard.tsx
    setup/CompanyInsightModal.tsx
    room/InterviewRoom.tsx
    report/InterviewReportPanel.tsx
  state/
    appDraft.ts
    trainingConfig.ts
```

拆分原则：

- 不先做大重构，先按现有组件边界搬文件。
- 保留当前行为，不顺手改业务逻辑。
- 先移除或明确标记旧版 `TrainingDock`，避免以后改错组件。
- API 请求集中到 `api/client.ts`，避免多个组件散落请求细节。
- 本地草稿持久化集中到 `state/appDraft.ts`。

这个优化的收益很直接：以后改公司资料页、配置流程、报告页，不会再出现“看起来改了但页面没变化”的问题。

## 5. 第三优先级：实时语音稳定性

实时链路目前可以作为主线继续推进，但还不是稳定产品形态。

建议按风险顺序做：

- 增加每轮耗时指标：ASR 首段、ASR 最终文本、LLM 首 token、TTS 首音频、整轮耗时。
- 为断网、切网、LiveKit 重连失败记录明确 session event。
- 轮次结束判断增加可回放测试，避免“说完等太久”和“思考时被误判结束”。
- TTS 后续优先考虑稳定低延迟方案，或让 AI 声音作为 LiveKit audio track 进入房间。
- VAD 从 RMS 规则逐步升级到 WebRTC VAD / Silero VAD，并结合环境噪声基线。

短期不建议直接把主线替换成 Fun-Audio-Chat-8B、Step-Audio 2 mini 或其他端到端音频模型。可以开实验分支验证，但主线应先把状态机、日志、评价数据闭环做稳。

## 6. 第四优先级：报告体验升级

报告体验的重点不是把分数做得更花，而是让用户知道：

- 为什么这么评？
- 证据来自哪一轮回答？
- 哪些是能力问题，哪些只是证据没采到？
- 下一次应该怎么补？

建议报告逐步增加：

- 能力雷达或能力条形图。
- 每个维度的证据引用。
- 回答卡片：危险回答、及格回答、强回答。
- 证据缺口清单。
- 下一轮训练建议。

这部分要依赖 `EvaluationResponse` 稳定下来之后再做，否则 UI 会被后端字段牵着反复改。

## 7. 第五优先级：搜索与岗位模型缓存

公司资料和岗位模型目前都是现场生成，这是对的，但需要缓存和版本意识。

建议：

- 公司资料缓存到 session，并保留来源 URL、来源摘要、生成时间。
- JD 分析结果缓存到 session，并保留 `jobModelVersion`。
- 评价时只使用本轮 session 中的公司资料和岗位模型，不重新搜索、不重新生成。
- 如果搜索失败，返回明确的 `verificationStatus`，不要用内置样例伪装真实数据。

这能保证配置页、追问、评价报告使用同一份事实基础。

## 8. 工程质量与测试

当前主项目缺少自动化测试。旁边的 `realtime-voice-prototype` 反而有更清晰的测试结构，可以借鉴。

短期建议补：

- `turn_completion` 单元测试。
- `turn_controller` 单元测试。
- `EvaluationRequest` builder 测试。
- `questionTrace` 与 `transcript` 对齐测试。
- `/company-card` 和 `/analyze-jd` 的基础 API 测试。
- 一个可回放的面试 fixture，用于验证评价结果不会突然变得过严或失真。

同时建议增加统一检查命令：

```text
npm run build
python -m compileall livekit-interview-spike/server
pytest
```

如果暂时不引入完整 pytest，也至少保留 compile 和 TypeScript build 作为最低门槛。

## 9. 不建议现在做的事

以下事情可以研究，但不建议作为下一步主线：

- 立刻大换实时语音模型。
- 继续重做首页视觉，而不处理数据闭环。
- 让评价 Agent 自己重新搜索公司资料。
- 让评价 Agent 自己重新生成岗位模型。
- 先做大量样例数据或假 demo。
- 把公司推荐、简历生成、能力评估、面试系统四个 Agent 一次性全部接上。

这些动作都会扩大不确定性。当前更应该把面试系统 Agent 自身的数据契约和闭环做扎实。

## 10. 推荐执行顺序

第一阶段：评价数据闭环

1. 定义后端 `SessionState`。
2. 持久化 `questionTrace[]`。
3. 持久化结构化 `transcript[]`。
4. 生成 MVP 版 `EvaluationRequest`。
5. 让当前内置评价器消费 `EvaluationRequest`。
6. 保持前端报告兼容。

第二阶段：前端收口

1. 拆分 `main.tsx`。
2. 移除或隔离旧版配置组件。
3. 集中 API client。
4. 集中本地草稿状态。

第三阶段：可观测和测试

1. 增加每轮语音链路耗时指标。
2. 增加断网、重连、中断事件记录。
3. 增加 EvaluationRequest fixture。
4. 增加 turn controller / turn completion 测试。

第四阶段：报告体验升级

1. 增加证据引用。
2. 增加回答卡片。
3. 增加训练计划可视化。
4. 增加下一轮训练重点。

## 11. 一句话结论

```text
下一步最应该做的不是继续堆功能，而是先把面试过程中现场生成的数据沉淀为 SessionState，
再组装成稳定的 EvaluationRequest。
只要这条链路成立，外部评价 Agent、报告页优化、追问策略升级、历史复盘和训练计划都会自然接上。
```

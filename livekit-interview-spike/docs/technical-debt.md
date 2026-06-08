# 技术债与后续优化

更新日期：2026-06-02

这个版本已经可以作为实时语音主线继续推进，但它仍然是“可体验的主线原型”，不是最终生产架构。下面按风险优先级记录当前技术债。

## 高优先级

- TTS 仍然不是稳定的流式语音。当前 Edge TTS 是请求完整音频后播放，网络和服务状态会导致首字延迟波动；长期应迁到更稳定的流式 TTS，或把 AI 语音作为 LiveKit audio track 发布进房间。
- 轮次结束判断还是启发式规则。现在依赖音量门控、转写稳定时间、中文短语规则和等待窗口；下一步应补充 LLM/小模型结束判断、统计日志和回放测试，避免“说完等太久”和“思考被误判结束”反复拉扯。
- ASR 抗噪和准确率还不够工业级。当前用 RMS 自适应门限挡环境声，但没有做人声模型 VAD、说话人识别、回声消除质量评估和领域词热词增强。
- 面试业务逻辑仍然偏硬编码。agent 里暂时写死产品经理面试 prompt 和开场白，还没有接入主项目的岗位、JD、简历、能力图谱、训练模式和评分反馈。

## 中优先级

- 观测能力不足。调试台能看到事件，但缺少统一延迟指标，例如首段转写耗时、最终转写耗时、DeepSeek 首 token、TTS 首音频、整轮耗时。
- 本地启动仍然偏重。现在需要 LiveKit server、token server、agent、web 四个进程；`start-dev.ps1` 能辅助启动，但后续应做健康检查、端口占用检测和更清晰的失败提示。
- LiveKit dev key 只能本地使用。当前 `.env.example` 保留 `devkey/secret` 是为了开发方便；公网部署必须换成强 secret、HTTPS/WSS、严格 CORS 和更短 token TTL。
- Data channel 控制消息缺少更严格的身份校验。本地单人房间风险较低，但如果未来多参与者或公网化，需要只允许候选人身份发送控制指令。

## 低优先级

- 前端 API 地址写死为 `http://127.0.0.1:8787`。本地开发方便，但部署时应抽成环境变量。
- FunASR 音频缓存使用 `np.concatenate`，长时间会话下可以优化为 ring buffer，减少频繁内存复制。
- 当前没有自动化测试。至少应补 `turn_completion`、`turn_controller` 的单元测试，以及 token server 的基础 API 测试。
- README 已经精简，但产品文档和技术路线还分散在主项目 `docs/`，后续应把 LiveKit 主线和原型主线的关系再合并一次。

## 推荐下一步

1. 接入主项目面试业务层：把岗位、能力项、追问策略、评分规则抽成 `Interview Orchestrator`，替换 agent 里的硬编码 prompt。
2. 增加实时链路指标：每轮回答记录 ASR、LLM、TTS、轮次判断耗时，先让问题可被量化。
3. 优化 TTS：优先尝试稳定的低延迟中文 TTS；如果继续用 LiveKit，最好让 AI 语音进入房间音轨，而不只是前端本地播放。
4. 升级 VAD：从 RMS 门限升级到 WebRTC VAD/Silero VAD + 环境基线，再评估是否需要说话人识别。

## 2026-06-06 补充：下一阶段收口重点

当前最应该优先处理的不是继续堆功能，而是把面试过程中现场生成的数据沉淀成稳定的 `SessionState`，并在面试结束时组装成标准 `EvaluationRequest`。

推荐新增一条评价数据闭环主线：

1. 在后端维护统一 `SessionState`，保存 `companyCard`、`jobModel`、`interviewConfig`、`questionTrace`、`transcript`、`evidenceSnapshot` 和 `sessionMeta`。
2. 将当前 `question.plan` / `build_question_trace()` 从调试事件升级为正式 `questionTrace[]` 记录。
3. 将 `orchestrator.turns` 转为结构化 `transcript[]`，并补充 `answerMeta`，记录过短回答、中断、断网、ASR 质量等信息。
4. 面试结束时从 `SessionState` 组装 MVP 版 `EvaluationRequest`。
5. 当前内置评价器先消费 `EvaluationRequest`，后续外部评价 Agent 也消费同一契约。
6. 评价结果通过 adapter 转成当前前端兼容的报告结构。

这条主线的详细方案见 `../../docs/technical/project-optimization-roadmap.md` 和 `../../docs/technical/evaluation-agent-contract.md`。

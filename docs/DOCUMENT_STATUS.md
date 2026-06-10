# 文档状态清单

更新时间：2026-06-08

这个文件用于避免文档越积越多后不知道该看哪一份。

## Active：当前有效

- `docs/README.md`
- `docs/technical/README.md`
- `docs/technical/project-optimization-roadmap.md`
- `docs/technical/server-deployment-runbook.md`
- `docs/technical/rag-service-runbook.md`
- `docs/technical/follow-up-strategy-library-design.md`
- `docs/technical/evaluation-agent-contract.md`
- `docs/technical/realtime-voice-technical-debt.md`
- `docs/technical/livekit-interview-spike-technical-debt.md`
- `docs/product/AI求职训练产品PRD.md`
- `docs/agents/个人开发习惯文档.md`

## Reference：可参考但不是第一入口

- `docs/product/AI求职训练.md`
- `docs/product/产品的想法.pptx`
- `docs/research/AI求职训练产品调研问卷核心摘要.md`
- `docs/research/AI 求职训练产品调研问卷-AI-报告.md`
- `docs/technical/面试系统Agent正式版技术方案与执行规划.md`

## Archived：历史稿

- 历史稿已清理；如需回溯早期方案，请查看 Git 历史。

## 整理原则

- 新增长期文档时，必须同步更新 `docs/README.md` 和本文件。
- 临时阶段记录不应长期散落在 `docs/technical/`，阶段结束后要合并到对应 active 文档；没有长期价值的历史稿直接删除，通过 Git 历史回溯。
- 运行命令、部署步骤、故障处理优先写进 runbook，不要散落在设计文档里。
- 架构设计写进 design/contract 类文档，操作步骤写进 runbook，产品判断写进 product 文档。

# 文档总入口

更新时间：2026-06-08

这个目录按“当前是否还作为决策依据”来读，不要从文件数量判断重要性。

## 1. 当前优先阅读

如果你要继续开发当前项目，优先看这些：

- [文档状态清单](DOCUMENT_STATUS.md)：哪些文档当前有效，哪些只是参考或历史稿。
- [技术文档索引](technical/README.md)：当前技术文档的阅读顺序。
- [RAG 服务测试与运维手册](technical/rag-service-runbook.md)：Qdrant、BGE-M3、资料入库、检索评测、删除数据。
- [追问策略库设计](technical/follow-up-strategy-library-design.md)：追问策略、RAG 方法论库、证据槽、评价对齐的总设计。
- [评价 Agent 对接契约](technical/evaluation-agent-contract.md)：评价 Agent 需要接收什么数据、如何使用 questionTrace。
- [项目优化路线图](technical/project-optimization-roadmap.md)：下一步优先级和暂不建议做的事项。
- [个人开发习惯文档](agents/个人开发习惯文档.md)：你的协作偏好、上线商用优先原则、不要硬编码少数岗位等约束。

## 2. 产品与需求

- [AI 求职训练产品 PRD](product/AI求职训练产品PRD.md)：当前产品需求主文档。
- [AI 求职训练](product/AI求职训练.md)：产品方向说明。
- `product/产品的想法.pptx`：早期产品想法演示材料。

## 3. 用户调研

- [调研问卷核心摘要](research/AI求职训练产品调研问卷核心摘要.md)：建议优先看摘要。
- [调研问卷 AI 报告](research/AI 求职训练产品调研问卷-AI-报告.md)：完整调研报告，内容较长。

## 4. Agent 与协作规则

- [领域说明](agents/domain.md)：当前项目的领域上下文。
- [Issue tracker 说明](agents/issue-tracker.md)：本地 issue 文件管理方式。
- [Triage 标签](agents/triage-labels.md)：默认 triage 标签约定。
- [个人开发习惯文档](agents/个人开发习惯文档.md)：协作和工程偏好。

## 5. 历史与归档

- [归档说明](archive/README.md)：已被替代的历史稿说明。
- `archive/technical/`：早期技术方案历史稿，只作背景参考，不作为当前实现依据。

## 6. 阅读建议

常见场景：

- 要启动/测试 RAG：读 [RAG 服务测试与运维手册](technical/rag-service-runbook.md)。
- 要接追问策略库：读 [追问策略库设计](technical/follow-up-strategy-library-design.md)。
- 要和评价 Agent 对接：读 [评价 Agent 对接契约](technical/evaluation-agent-contract.md)。
- 要判断下一步做什么：读 [项目优化路线图](technical/project-optimization-roadmap.md)。
- 要确认做事风格：读 [个人开发习惯文档](agents/个人开发习惯文档.md)。

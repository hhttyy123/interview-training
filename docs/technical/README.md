# 技术文档索引

更新时间：2026-06-08

## 1. 当前权威文档

这些文档是当前开发和决策优先依据：

1. [project-optimization-roadmap.md](project-optimization-roadmap.md)
   当前项目下一步优化路线图，包含优先级、执行顺序和暂不建议做的事项。

2. [rag-service-runbook.md](rag-service-runbook.md)
   RAG 服务测试与运维手册，包含 Qdrant、BGE-M3、TEI、资料入库、检索评测、删除数据、常见错误处理。

3. [server-deployment-runbook.md](server-deployment-runbook.md)
   服务器部署思路与上线检查，按阿里云 ACR、Xshell、Docker Compose 的发布方式整理。

4. [follow-up-strategy-library-design.md](follow-up-strategy-library-design.md)
   面试追问策略库完整设计，覆盖六阶段：追问策略骨架、RAG 方法论库、职业通用化、证据质量判断、RAG 接入追问、评价 Agent 对齐。

5. [evaluation-agent-contract.md](evaluation-agent-contract.md)
   评价 Agent 对接契约，说明 `EvaluationRequest`、`EvaluationResponse`、`questionTrace`、`evidenceSnapshot` 等字段。

## 2. 实时语音与 LiveKit

这些文档和实时语音主链路相关：

- [realtime-voice-technical-debt.md](realtime-voice-technical-debt.md)
  当前实时语音链路的技术债和稳定性风险。

- [livekit-interview-spike-technical-debt.md](livekit-interview-spike-technical-debt.md)
  `livekit-interview-spike` 落地项目的技术债、后续优化和评价数据闭环记录。

## 3. Agent 系统长期方案

- [面试系统Agent正式版技术方案与执行规划.md](面试系统Agent正式版技术方案与执行规划.md)
  面试系统多 Agent 正式版长期方案。当前实现以 `livekit-interview-spike` 为落地入口，这份文档更多用于长期架构对齐。

## 4. 当前不要优先看的内容

这些不是当前第一优先级：

- 根目录的产品讨论总结：更偏产品背景，不作为当前工程落地依据。

## 5. 推荐阅读路径

### 做 RAG

1. [rag-service-runbook.md](rag-service-runbook.md)
2. [follow-up-strategy-library-design.md](follow-up-strategy-library-design.md) 的 RAG 阶段
3. [evaluation-agent-contract.md](evaluation-agent-contract.md) 里的 methodology 字段映射

### 做服务器部署

1. [server-deployment-runbook.md](server-deployment-runbook.md)
2. [rag-service-runbook.md](rag-service-runbook.md) 的服务器 RAG 服务部分
3. [livekit-interview-spike-technical-debt.md](livekit-interview-spike-technical-debt.md)

### 做追问策略

1. [follow-up-strategy-library-design.md](follow-up-strategy-library-design.md)
2. [project-optimization-roadmap.md](project-optimization-roadmap.md)
3. [evaluation-agent-contract.md](evaluation-agent-contract.md)

### 做评价 Agent 对接

1. [evaluation-agent-contract.md](evaluation-agent-contract.md)
2. [follow-up-strategy-library-design.md](follow-up-strategy-library-design.md) 的 questionTrace / Evaluation 对齐部分

### 做实时语音稳定性

1. [realtime-voice-technical-debt.md](realtime-voice-technical-debt.md)
2. [livekit-interview-spike-technical-debt.md](livekit-interview-spike-technical-debt.md)

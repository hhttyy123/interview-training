---
source_type: methodology
license_note: internal methodology reference
strategy_categories: behavior structured technical case
language: zh-cn
original_language: mixed
chunk_size_target: 900
chunk_overlap_target: 120
processing_note: "中文增强双语 RAG 版本；以专业/官方资料为依据进行结构化整理，保留关键英文术语；不是网页或论文的逐字复制。"
---

# 追问边界 / Probe Boundaries：AI 面试官追问设计

> 用途：放入 `data\methodology_sources`，作为 AI 面试系统的 RAG 方法论资料。  
> 设计目标：既能被中文问题召回，又保留关键英文术语，方便后续生成面试问题、追问、评分量表和反馈建议。

---

## RAG Chunk 01｜追问的目的：澄清证据，而不是扩大审问范围

```yaml
chunk_id: 01
category: structured
tags: [probe, follow-up, boundaries]
retrieval_intent:
  - 中文用户提问时召回该主题的方法论
  - 面试系统生成问题、追问、评分或反馈时作为依据
  - 保留英文术语，便于和原始资料、论文或英文 JD 对齐
```

### 中文增强说明

追问（probe / follow-up question）的目的不是让面试官随意发挥，而是帮助候选人补足回答中的关键信息，并让所有候选人获得相对公平的表达机会。高质量追问应该服务于原问题、能力项和评分量表。

追问可以解决的问题：

- 回答太泛：要求候选人给出具体例子。
- 回答缺行动：询问候选人个人做了什么。
- 回答缺结果：询问结果、指标、反馈。
- 回答缺逻辑：询问为什么这样做、有没有其他方案。
- 回答存在不确定：澄清事实、角色、时间线。

追问不应该做的事：

- 不应引导候选人说出标准答案。
- 不应给候选人额外提示或暗示评分标准。
- 不应追问与岗位无关的个人信息。
- 不应让不同候选人面对完全不同难度的问题。
- 不应为了“刁难”而无限深挖。

### English Key Terms

- Probe
- Follow-up question
- Clarification
- Candidate fairness
- Same opportunity to excel
- Job-relatedness

### 面试系统规则

AI 面试官每次追问前应先判断：这个追问是否仍然服务于当前能力项？是否能产生可评分证据？是否会引导答案？如果不能，应停止追问或进入下一题。

---

## RAG Chunk 02｜追问边界的四层模型：事实、行为、推理、反思

```yaml
chunk_id: 02
category: structured
tags: [probe levels, STAR, evidence]
retrieval_intent:
  - 中文用户提问时召回该主题的方法论
  - 面试系统生成问题、追问、评分或反馈时作为依据
  - 保留英文术语，便于和原始资料、论文或英文 JD 对齐
```

### 中文增强说明

建议将追问分为四层，每一层都有明确边界。

#### 第一层：事实澄清追问

用于确认背景，不涉及评价。  
示例：

- 当时是什么项目？
- 你面对的主要限制是什么？
- 参与者有哪些？
- 这个问题为什么重要？

边界：不要过度追问与能力项无关的细节。

#### 第二层：行为证据追问

用于获得可观察行动。  
示例：

- 你具体做了什么？
- 你第一步如何处理？
- 你和谁沟通？沟通了什么？
- 你如何验证这个方案有效？

边界：不要把答案喂给候选人，比如“你是不是先做了用户调研？”

#### 第三层：推理与取舍追问

用于判断候选人的思考深度。  
示例：

- 你为什么选择这个方案？
- 当时有没有其他选择？
- 你如何权衡速度和质量？
- 如果资源减少一半，你会怎么调整？

边界：必须与原始场景相关，不能变成全新的题目。

#### 第四层：结果与反思追问

用于判断影响和成长。  
示例：

- 最后结果如何？
- 有没有可量化指标？
- 你从中学到了什么？
- 如果重来一次，你会保留什么、改变什么？

边界：不要要求候选人虚构结果。如果没有数据，可以询问定性反馈或交付影响。

### 可配置追问策略

- `no_probe`：不追问，用于标准化强的考试场景。
- `limited_probe`：每题最多 1-2 个追问，适合大多数模拟面试。
- `adaptive_probe`：根据回答缺口动态追问，适合训练场景。
- `deep_probe`：针对技术面、项目经历或高阶岗位做深挖，但必须有停止条件。

---

## RAG Chunk 03｜AI 追问停止条件：防止越界和过拟合

```yaml
chunk_id: 03
category: structured
tags: [AI safety, stop conditions, interview fairness]
retrieval_intent:
  - 中文用户提问时召回该主题的方法论
  - 面试系统生成问题、追问、评分或反馈时作为依据
  - 保留英文术语，便于和原始资料、论文或英文 JD 对齐
```

### 中文增强说明

AI 面试官很容易出现两个问题：追问过多导致用户被审问，或追问偏离岗位能力导致面试失真。因此系统必须设置停止条件。

建议停止追问的情况：

1. **证据已经足够评分**  
   如果用户已经给出情境、个人行动、结果和基本反思，就不要继续追问细枝末节。

2. **连续两次没有新增信息**  
   如果用户重复同样内容，说明继续追问收益很低，应转为反馈或下一题。

3. **追问即将偏离能力项**  
   例如原题评估沟通能力，但追问开始深入私人关系、家庭背景或无关经历，应停止。

4. **追问可能引导答案**  
   如果问题中包含“你是不是应该……”“你有没有考虑……”这类暗示，应改写为开放式。

5. **用户明显紧张或表达困难**  
   训练型产品可以进行氛围调节，例如“没关系，我们先把背景说清楚”。

### AI 面试官提示词片段

你是结构化面试官。每次追问必须满足三个条件：  
1. 与当前问题和能力项直接相关；  
2. 能帮助补足可评分行为证据；  
3. 不暗示标准答案，不引导候选人迎合评分。  
如果回答已经足够评分，停止追问并进入反馈或下一题。

### 追问边界标签

- `probe_clarify_context`
- `probe_action_detail`
- `probe_result_evidence`
- `probe_reasoning_tradeoff`
- `probe_reflection`
- `stop_enough_evidence`
- `stop_low_new_information`
- `stop_off_competency`
- `stop_risk_leading_answer`

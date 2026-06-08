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

# Interview Methodology RAG Pack v2 索引

> 用途：放入 `data\methodology_sources`，作为 AI 面试系统的 RAG 方法论资料。  
> 设计目标：既能被中文问题召回，又保留关键英文术语，方便后续生成面试问题、追问、评分量表和反馈建议。

## 资料包说明

这一版不是简单摘要，而是面向你的 AI 面试训练系统重新整理的“可召回、可评分、可落地”的方法论资料包。每个文件都采用：

- 中文增强说明
- 英文关键术语
- RAG chunk 元数据
- 可用于系统提示词的规则
- 可用于评分/追问/反馈的标签
- 可直接落地的评分量表或流程

## 文件列表

1. `star_behavioral_answering_rag_zh_bilingual_v2.md`
   - STAR / PAR 行为面试回答结构
   - 用于回答诊断、结构完整性评分、个人贡献识别

2. `bars_rating_scales_rag_zh_bilingual_v2.md`
   - BARS / 行为锚定评分量表
   - 用于设计 5 分评分、能力项锚点、可解释评分

3. `probing_boundaries_rag_zh_bilingual_v2.md`
   - 追问边界 / Probe Boundaries
   - 用于 AI 面试官追问策略、停止条件和越界控制

4. `interviewer_bias_control_rag_zh_bilingual_v2.md`
   - 面试官偏差控制
   - 用于评分一致性、抗偏差提示词、审核标签

5. `technical_interview_deep_dive_rag_zh_bilingual_v2.md`
   - 技术面深挖
   - 用于编码题、项目深挖、系统设计追问和评分

## 建议导入命令

```powershell
python scripts\ingest_documents.py `
  --path data\methodology_sources `
  --source-type methodology `
  --license-note "internal methodology reference" `
  --strategy-categories behavior structured technical case `
  --chunk-size 900 `
  --chunk-overlap 120
```

## 主要参考来源

- U.S. Office of Personnel Management, Structured Interviews: A Practical Guide.
- OPM Structured Interviews official topic page and example question PDFs.
- Google re:Work, A guide to structured interviewing for better hiring practices.
- MIT CAPD, The STAR method for behavioral interviews.
- VA Careers, Performance-Based Interview / STAR technique resources.
- ETS research on developing BARS for structured interview performance.
- Levashina, Hartwell, Morgeson & Campion, The Structured Employment Interview.
- Karat, structured rubric for technical interviews.
- Microsoft Careers, Technical interviewing guidance.

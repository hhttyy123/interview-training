---
title: "结构化面试：实践指南（RAG 中文增强双语版）"
source_file: "guide.pdf"
source_type: "methodology"
license_note: "internal methodology reference"
strategy_categories: [behavior, structured, technical, case]
language: "zh-cn + en"
original_language: "en"
chunk_size: 900
chunk_overlap: 120
preprocessing_note: "Bilingual RAG preparation. Chinese translation/semantic layer added before each original English chunk; original extracted English text is preserved unchanged under each chunk."
---

# 结构化面试：实践指南（RAG 中文增强双语版）

> 来源：U.S. Office of Personnel Management, September 2008。  
> 用途：用于 `python scripts\ingest_documents.py --path data\methodology_sources --source-type methodology --license-note "internal methodology reference" --strategy-categories behavior structured technical case --chunk-size 900 --chunk-overlap 120` 的 RAG 预处理文档。

## 术语对照表

| English | 中文建议译法 | RAG 检索关键词 |
|---|---|---|
| Structured Interview | 结构化面试 | 标准化问题、统一评分、可比性 |
| Unstructured Interview | 非结构化面试 | 主观性、低可靠性、法律风险 |
| Behavioral Interview | 行为面试 / 行为描述面试 | 过去行为、STAR、行为证据 |
| Situational Interview | 情景面试 | 假设情境、岗位场景、应对策略 |
| Competency | 胜任力 / 能力项 | 岗位能力模型、评估维度 |
| Rating Scale | 评分量表 | 评分标准、量化等级、BARS |
| Proficiency Level | 熟练度等级 | Level 1-5、能力水平 |
| Behavioral Examples | 行为示例 | 评分锚点、行为证据 |
| Representative Responses | 代表性回答 | 情景题评分参考 |
| Probe | 追问 / 探询问题 | 澄清、深入追问、边界 |
| Subject Matter Expert / SME | 主题专家 / 领域专家 | 专家共识、岗位专家 |
| Job Analysis | 工作分析 / 岗位分析 | 岗位任务、职责、胜任力来源 |
| Critical Incident | 关键事件 | 有效行为、无效行为、案例收集 |

---
## RAG Chunk 001

<!-- source_type: methodology | category: structured | pages: 1-5 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 865 -->

### 中文译文 / 中文检索层

本文件为美国人事管理办公室（U.S. Office of Personnel Management）2008 年 9 月发布的《结构化面试：实践指南》。导言指出，招聘质量会显著影响联邦机构完成使命的能力，而面试能够评估书面测试不容易测量的特征，例如口头沟通能力和人际技能。文件区分了结构化面试与非结构化面试：结构化面试要求所有候选人以相同顺序回答相同问题，并使用共同评分量表；非结构化面试则问题不一致、评分标准不统一、面试官不必对可接受答案达成一致。指南强调，非结构化面试虽然看似灵活、对话感强，但主观性高，可靠性和效度较低，也更容易引发法律挑战。相比之下，结构化面试在可靠性、效度和法律防御性方面表现更好，因此建议用于正式雇佣决策。本指南的目的，是说明为什么面试需要结构化、结构化包含哪些要素，以及如何设计和实施结构化面试。

### Original English Text

September 2008
Structured IntervIewS:
A PrActicAl Guide

STRUCTURED INTERVIEWS:

A PRACTICAL GUIDE

U.S. Office of Personnel Management
Theodore Roosevelt Building
1900 E Street, NW
Washington, DC 20415-0001

September 2008

TABLE OF CONTENTS

Introduction..................................................................................................................................... 3
Overview.................................................................................................................................. 3
Structured vs. Unstructured Interviews ................................................................................... 3
The Purpose of this Guide ....................................................................................................... 4
Section I: Developing a Structured Interview................................................................................ 5
1. Conduct a Job Analysis ...................................................................................................... 5
2. Determine the Competencies to Be Assessed by the Interview ......................................... 5
3. Choose the Interview Format and Develop Questions ....................................................... 6
Behavioral Interview Format and Questions.................................................................... 6
Writing Behavioral Interview Questions.......................................................................... 7
Situational Interview Format and Questions.................................................................... 7
Writing Situational Interview Questions.......................................................................... 7
4. Developing Rating Scales to Evaluate Candidates............................................................. 8
Rating Scale and Behavioral Examples for a Behavioral Interview ................................ 8
Rating Scale and Behavioral Responses for a Situational Interview ............................. 11
5. Create Interview Probes.................................................................................................... 12
6. Pilot Test the Interview Questions and Evaluate the Interview Process .......................... 14
7. Create the Interviewer’s Guide......................................................................................... 14
8. Document the Development Process................................................................................ 14
Section II: Administering a Structured Interview......................................................................... 15
Interviewers ........................................................................................................................... 15
Training Your Interviewer..................................................................................................... 15
Note-Taking.................................................................................................................... 15
Interviewer’s Non-Verbal Behavior............................................................................... 15
Interpersonal Bias and Rating Errors ............................................................................. 16
The Interview Setting ............................................................................................................ 16
Conducting the Interview ...................................................................................................... 16
Supplemental Materials.................................................................................................. 16
Arrival of the Candidate................................................................................................. 16
Rating Each Candidate ................................................................................................... 17
Documenting the Interview Process......................................................................................17
Appendix A: Structured Interview Implementation Checklist ..................................................... 21
Appendix B: Structured Interview Development Checklist ......................................................... 22
Appendix C: Sample Critical Incident Forms............................................................................... 23
Appendix D: Panel Interviews...................................................................................................... 25
Appendix E: Sample Lesson Plan for an Interviewer Training Course........................................ 27
Appendix F: Common Rating Errors and Interviewing Mistakes ................................................ 28
Appendix G: Sample Structured Interview Individual Rating Form............................................ 30
Appendix H: Sample Structured Interview Group Rating Form .................................................. 35

September 2008
U.S. Office of Personnel Management
2

Introduction

Overview

Federal Agency mission accomplishment is substantially affected by who gets hired. Agencies
must select people who possess characteristics required for the job. The employment interview
is an effective way of determining who has these attributes and therefore, who is right for a job.

The interview is popular because it is more personal than traditional selection assessments (e.g.,
written tests) and because it can be used to evaluate job characteristics not easily measured with
other procedures (e.g., Oral Communication and Interpersonal Skills).

Interviews are typically used for one of two purposes in the Federal Government. First, the
interview may be used as part of the formal selection process in which candidates are screened or
ranked based on their scores. Second, a “selecting official's interview” may be used to verify
candidates’ qualifications for a job after they have been rated using other assessment methods,
but prior to making a hiring decision. In a selecting official’s interview, candidates’ responses
are typically not scored.

Structured vs. Unstructured Interviews

Employment interviews can be either structured or unstructured. Generally speaking, structured
interviews ensure candidates have equal opportunities to provide information and are assessed
accurately and consistently.

Structured Interview
Unstructured Interview

• All candidates are asked the same
questions in the same order.
• Candidates may be asked different
questions.
• All candidates are evaluated using a
common rating scale.
• A standardized rating scale is not
required.
• Interviewers are in agreement on
acceptable answers.
• Interviewers do not need to agree on
acceptable answers.

At first glance, the unstructured interview appears attractive due to its loose framework,
discretionary content, and conversational flow. Yet, these same features make this type of
interview very subjective, which reduces its accuracy and invites legal challenges.

Research consistently indicates unstructured interviews have little value in predicting job
performance. Unstructured interviews typically demonstrate:
• Low levels of reliability (rating consistency among interviewers).
• Low to moderate levels of validity (the extent to which the assessment method measures
what it is intended to measure, e.g., job performance).
September 2008
U.S. Office of Personnel Management
3

Besides adversely affecting the reliability and validity of the unstructured interview, the lack of
standardization in interview procedure and questions also makes the unstructured interview
susceptible to legal challenges (Terpstra, Mohamed, and Kethley 19991; U.S. Merit Systems
Protection Board, 20032).

In comparison, structured interviews have demonstrated a high degree of reliability, validity, and
legal defensibility. Therefore, because interviews used to make employment decisions are
subject to the same legal and psychometric requirements as any written employment test or other
assessment method, agencies are encouraged to use structured interviews. The benefits of
consistently selecting quality candidates and reducing the risk of legal challenges far outweigh
any costs of adding structure (e.g., additional time and expertise).

The selecting official’s interview is likely to fall somewhere between structured and
unstructured, as it may incorporate a consistent set of questions but is unlikely to be rated.

The Purpose of this Guide

This guide provides practical information on designing structured interviews. The guide
discusses why interviews should have structure, what structure consists of, and how to conduct a
structured interview. It also addresses the pros and cons of different types of interview questions
and helpful/harmful interviewing techniques. Additionally, the guide provides practical tools for
developing and implementing a structured interview. For step-by-step checklists for
implementing and developing a structured interview, refer to Appendix A and Appendix B,
respectively.

---

---

## RAG Chunk 002

<!-- source_type: methodology | category: technical | pages: 5-7 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 888 -->

### 中文译文 / 中文检索层

第一部分介绍开发结构化面试的八个关键步骤：进行工作分析；确定面试要评估的胜任力；选择面试形式并开发问题；开发候选人评分量表；设计追问；试测面试问题；创建面试官指南；记录开发过程。工作分析的目的是识别岗位要求以及完成这些要求所需的胜任力，包括岗位任务、职责、成功完成任务所需能力，以及入职时必须具备的能力。可参考绩效考核关键要素、职位说明书、分类标准、任务陈述、主题专家访谈和组织结构图等来源。确定胜任力后，应判断哪些能力适合在选拔过程中评估，以及用何种方法评估。结构化面试通常评估四到六项胜任力，尤其适合评估口头沟通、人际技能等能力。

### Original English Text

In comparison, structured interviews have demonstrated a high degree of reliability, validity, and
legal defensibility. Therefore, because interviews used to make employment decisions are
subject to the same legal and psychometric requirements as any written employment test or other
assessment method, agencies are encouraged to use structured interviews. The benefits of
consistently selecting quality candidates and reducing the risk of legal challenges far outweigh
any costs of adding structure (e.g., additional time and expertise).

The selecting official’s interview is likely to fall somewhere between structured and
unstructured, as it may incorporate a consistent set of questions but is unlikely to be rated.

The Purpose of this Guide

This guide provides practical information on designing structured interviews. The guide
discusses why interviews should have structure, what structure consists of, and how to conduct a
structured interview. It also addresses the pros and cons of different types of interview questions
and helpful/harmful interviewing techniques. Additionally, the guide provides practical tools for
developing and implementing a structured interview. For step-by-step checklists for
implementing and developing a structured interview, refer to Appendix A and Appendix B,
respectively.

The guidance on developing and administering structured interviews applies to interviews
formally rated as part of the assessment process, as well as those used by the selection official to
verify a candidate’s qualifications after he/she has been rated by other assessment procedures.
However, since responses are typically not scored in a selecting official’s interview, the
information in this document related to developing and using rating scales may be of limited use
for the selecting official’s interview.

This guide is not intended to be exhaustive of the possible approaches to developing a structured
interview, but to provide one effective method. Additional information on assessment methods
is available in OPM’s Assessment and Selection Policy website. Please see
also The Uniform Guidelines on Employee Selection Procedures and the Delegated Examining
Operations Handbook.

1 Terpstra, D. E., Mohamed, A. A., & Kethley, R. B. (1999). An analysis of Federal court cases involving nine
selection devices. International Journal of Selection and Assessment, 7, 26-34.

2 U. S. Merit Systems Protection Board. (2003). The federal selection interview: Unrealized potential.
Washington, DC: Office of Policy and Evaluation.

September 2008
U.S. Office of Personnel Management
 4

Section I: Developing a Structured Interview

There are 8 key steps in developing a structured interview. Appendix B provides a checklist
based on these steps.

1.
Conduct a Job Analysis
2.
Determine the Competencies to be Assessed by the Interview
3.
Choose the Interview Format and Develop Questions
4.
Develop Rating Scales to Evaluate Candidates
5.
Create Interview Probes
6.
Pilot-Test the Interview Questions
7.
Create the Interviewer’s Guide
8.
Document the Development Process

1. Conduct a Job Analysis

The purpose of a job analysis is to identify the requirements of the job and the competencies
necessary to perform them. In many instances, a new job analysis will not need to be conducted;
however, the critical requirements and competencies should be re-confirmed by subject matter
experts. A thorough job analysis will:

• Identify the job tasks and responsibilities.
• Identify the competencies required to successfully perform the job tasks and
responsibilities.
• Identify which of those competencies are required upon entry to the job.

To gather this information about a job, consider sources such as:

• Performance appraisal critical elements
• Position descriptions
• Classification standards
• Task statements
• Interviews with subject matter experts (e.g., high-performing employees, supervisors)
• Organizational charts

Chapter 2 and Appendix G of the Delegated Examining Operations Handbook provide additional
information and tools for conducting a job analysis.

2. Determine the Competencies to be Assessed by the Interview

After identifying the critical competencies, determine which will be assessed in the selection
process and how each competency will be measured (e.g., using a written test or interview).
OPM’s interactive Assessment Decision Tool provides suggested methods for assessing a range
of competencies and also provides evaluation criteria for each assessment method.
September 2008
U.S. Office of Personnel Management
 5

The structured interview is typically used to assess between four and six competencies, unless
the job is unique or at a high level. Some competencies (e.g., Oral Communication,
Interpersonal Skills) are particularly well-suited to assessment through an interview.

3. Choose the Interview Format and Develop Questions

The format of the interview can focus on candidates’ past behavior, their anticipated behavior in
hypothetical situations, or a combination of the two approaches. An interview based on
questions about past behaviors is a behavioral description interview, also known as a behavioral
event interview. An interview based on questions about hypothetical behavior is a situational
interview. In the remainder of this document, “behavioral interview” will refer to both the
behavioral description interview and the behavioral event interview.

The interview format will determine how the interview questions are developed. The two
interview formats measure different aspects of job performance. Therefore, deciding which
format to use depends upon the needs and resources of the agency and on the other assessments
used. The agency may elect to include questions derived from both the behavioral- and
situational-interview formats.

Regardless of the format, the interview questions should be:

• Reflective of competencies derived from a job analysis
• Realistic of the responsibilities of the job
• Open-ended
• Clear and concise
• At a reading level appropriate for the candidates
• Free of jargon

---

---

## RAG Chunk 003

<!-- source_type: methodology | category: behavior | pages: 7-9 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 877 -->

### 中文译文 / 中文检索层

本部分说明面试问题的两种主要形式：行为面试和情景面试。行为面试要求候选人描述过去经历中的实际行为，其基本假设是：相似情境下的过去行为是未来工作行为的较好预测因素。情景面试则给候选人一个真实岗位情境或两难问题，询问其将如何处理，基本假设是人的意图与实际行为密切相关。无论采用哪种形式，面试问题都应来自工作分析中的胜任力，与岗位责任真实相关，开放式、清晰、简洁，阅读难度适合候选人，并避免行话。文件以“人际技能”为例展示行为问题：描述一次你处理困难、敌对或情绪低落人员的情境，涉及谁，你采取了哪些具体行动，结果如何。

### Original English Text

The format of the interview can focus on candidates’ past behavior, their anticipated behavior in
hypothetical situations, or a combination of the two approaches. An interview based on
questions about past behaviors is a behavioral description interview, also known as a behavioral
event interview. An interview based on questions about hypothetical behavior is a situational
interview. In the remainder of this document, “behavioral interview” will refer to both the
behavioral description interview and the behavioral event interview.

The interview format will determine how the interview questions are developed. The two
interview formats measure different aspects of job performance. Therefore, deciding which
format to use depends upon the needs and resources of the agency and on the other assessments
used. The agency may elect to include questions derived from both the behavioral- and
situational-interview formats.

Regardless of the format, the interview questions should be:

• Reflective of competencies derived from a job analysis
• Realistic of the responsibilities of the job
• Open-ended
• Clear and concise
• At a reading level appropriate for the candidates
• Free of jargon

Behavioral Interview Format and Questions. The primary purpose of the behavioral interview
is to gather information from job candidates about their actual behavior during past experiences
which demonstrates competencies required for the job. The underlying premise is the best
predictor of future behavior on the job is past behavior under similar circumstances.

For example, consider the competency, Interpersonal Skills, defined as: “shows understanding,
friendliness, courtesy, tact, empathy, concern, and politeness to others; develops and maintains
effective relationships with others; may include effectively dealing with individuals who are
difficult, hostile, or distressed; relates well to people from varied backgrounds and different
situations; is sensitive to cultural diversity, race, gender, disabilities, and other individual
differences.” This definition could lead to a behavioral interview question focused on a
candidate’s past behavior such as:

Describe a situation in which you dealt with individuals who were difficult,
hostile, or distressed. Who was involved? What specific actions did you take and
what was the result?

September 2008
U.S. Office of Personnel Management
 6

Writing Behavioral Interview Questions. Convene a group of approximately six or seven
subject matter experts (SMEs). These SMEs should be experienced, high-performing employees
or supervisors who possess knowledge of the job at the level of the position to be filled.
Typically, SMEs are at the journey level or higher.

• Have SMEs familiarize themselves with the competencies (and their definitions) to be
measured by the interview.
• Have SMEs work together to write interview questions.
o Each question should measure at least one of the specified competencies.
o Each question should be written to elicit specific details about a situation, task, or
context, the actions the person took or did not take, and the impact of these
actions.
• SMEs should use superlative adjectives in the questions (e.g., most, last, worst, least) to
help the candidate focus on specific incidents.
• SMEs should develop more questions than are actually needed to allow for subsequent
discarding of questions during review and tryout.

Situational Interview Format and Questions. In contrast to the behavioral interview, the
questions in a situational interview are based on future-oriented behavior. Situational interview
questions give the candidate realistic job scenarios or dilemmas and ask how he/she would
respond. The underlying premise is a person’s intentions are closely tied to his/her actual
behavior.

An example situational interview question for the competency Interpersonal Skills is:

A very angry client walks up to your desk. She says she was told your office sent
her an overdue check five days ago. She claims she has not received the check.
She says she has bills to pay, and no one will help her. How would you handle
this situation?

Writing Situational Interview Questions. Typically, the critical incident method, outlined
below, is used to write situational interview questions (Flanagan, 1954)3.

• Assemble a group of subject matter experts (SMEs) who have extensive knowledge about
the job.
• Have the SMEs review the competencies (and their definitions) to be measured by the
interview and the job tasks linked to the competencies.
• Have SMEs write examples of effective and ineffective behaviors (i.e., critical incidents)
which reflect the competencies and associated tasks.
• Arrange for a separate group of SMEs to read each critical incident and identify the
competency they believe the incident best illustrates.
o This will confirm whether the critical incidents can be clearly linked to the
specific competencies to which they are supposed to be linked.

3 Flanagan, J. C. (1954). The critical incident technique. Psychological Bulletin, 51, 327-358.
September 2008
U.S. Office of Personnel Management
 7

o Eliminate critical incidents not clearly linked to a competency and those
associated with multiple competencies.
• Have SMEs rewrite the retained critical incidents in the form of hypothetical situations.
o These hypothetical situations should still demonstrate the correct competency.
o The hypothetical situations should be as real as possible and reflective of the job.
• As with the behavioral interview, have SMEs develop more questions than are actually
needed to allow for future elimination.

Appendix C provides example forms for writing critical incidents describing effective and
ineffective behavior.

4. Developing Rating Scales to Evaluate Candidates
NOTE: This step is not applicable to a selecting official’s interview.

---

---

## RAG Chunk 004

<!-- source_type: methodology | category: technical | pages: 8-10 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 768 -->

### 中文译文 / 中文检索层

文件接着说明如何编写行为面试和情景面试问题。行为问题应由约六到七名主题专家共同开发，这些专家应是经验丰富、表现优秀、熟悉岗位的员工或主管。专家需要熟悉待测胜任力及定义，共同编写能引出具体情境、任务或背景、候选人采取或未采取的行动，以及行动影响的问题。问题中可使用“最、最近、最糟、最少”等最高级形容词，帮助候选人聚焦具体事件。情景问题通常使用关键事件法开发：主题专家先围绕胜任力和任务写出有效与无效行为案例，再由另一组专家判断每个事件最能体现哪项胜任力；不能清晰对应单一胜任力的事件应删除，保留事件再改写为真实、岗位相关的假设情境。

### Original English Text

3 Flanagan, J. C. (1954). The critical incident technique. Psychological Bulletin, 51, 327-358.
September 2008
U.S. Office of Personnel Management
 7

o Eliminate critical incidents not clearly linked to a competency and those
associated with multiple competencies.
• Have SMEs rewrite the retained critical incidents in the form of hypothetical situations.
o These hypothetical situations should still demonstrate the correct competency.
o The hypothetical situations should be as real as possible and reflective of the job.
• As with the behavioral interview, have SMEs develop more questions than are actually
needed to allow for future elimination.

Appendix C provides example forms for writing critical incidents describing effective and
ineffective behavior.

4. Developing Rating Scales to Evaluate Candidates
NOTE: This step is not applicable to a selecting official’s interview.

The use of a common rating scale for all candidates is a key component of the structured
interview procedure. A standardized rating scale can be developed for either behavioral- or
situational-interview questions; however, the process is slightly different.

Rating Scale and Behavioral Examples for a Behavioral Interview. The first step in the
development of a standardized rating scale for a behavioral interview is specifying the range of
proficiency for each competency.

• Decide on one proficiency-level range for all competencies (e.g., a range of 1-5 with
5 being the most proficient and 1 being the least proficient).
• Create at least three proficiency levels, but aim for five to seven levels.
• Label at least three proficiency levels (e.g., unsatisfactory, satisfactory, and superior).

Table 1 provides a 5-level proficiency rating scale developed by OPM. Labels are provided for
each of the five levels.

Table 1: Rating Scale
Proficiency
Level
General Competencies
Technical Competencies
Level 5 -
Expert
• Applies the competency in
exceptionally difficult situations.
• Serves as a key resource and
advises others.

• Applies the competency in
exceptionally difficult situations.
• Serves as a key resource and
advises others.
• Demonstrates comprehensive,
expert understanding of concepts
and processes.
Level 4 -
Advanced
• Applies the competency in
considerably difficult situations.
• Generally requires little or no
guidance.
• Applies the competency in
considerably difficult situations.
• Generally requires little or no
guidance.
• Demonstrates broad understanding
of concepts and processes.
September 2008
U.S. Office of Personnel Management
 8

Proficiency
Level
General Competencies
Technical Competencies
Level 3 -
Intermediate
• Applies the competency in difficult
situations.
• Requires occasional guidance.

• Applies the competency in difficult
situations.
• Requires occasional guidance.
• Demonstrates understanding of
concepts and processes.
Level 2 -
Basic
• Applies the competency in
somewhat difficult situations.
• Requires frequent guidance.

• Applies the competency in
somewhat difficult situations.
• Requires frequent guidance.
• Demonstrates familiarity with
concepts and processes.
Level 1 -
Awareness
• Applies the competency in the
simplest situations.
• Requires close and extensive
guidance.

• Applies the competency in the
simplest situations.
• Requires close and extensive
guidance.
• Demonstrates awareness of
concepts and processes.

For a behavioral interview, develop example behaviors for each proficiency level of each
competency. The purpose of these example behaviors is to clearly differentiate between
proficiency levels for each competency. This will ease the rating process by giving interviewers
concrete behaviors to refer to as they are considering how proficient each candidate is on each
competency. The example behaviors will provide a common framework for assessing
candidates’ responses in a consistent manner.

Subject matter experts (SMEs) should assist in developing the behavioral examples for each
behavioral interview question.

• Reconvene the panel of SMEs who developed the behavioral interview questions.
• For each question, have SMEs individually determine how actual employees at each
proficiency level would respond (i.e., what their answers would be).
o These hypothetical responses are behavioral examples for the proficiency levels.
• Have the SMEs discuss their behavioral examples.
• For each proficiency level, retain behavioral examples which the SMEs agree best reflect
the competency at that level.
• Instruct interviewers to use these behavioral examples as a general guide (not an
absolute) in making their ratings, as candidate’s responses may differ depending on their
unique experiences (Feild and Gatewood, 1989)4.

Table 2 presents an example behavioral interview rating scale for a question based on the
competency Interpersonal Skills. This rating scale has been supplemented with behavioral
examples to illustrate differences between the proficiency levels.

4 Feild, H. S., & Gatewood, R. D. (1989). Development of a selection interview: A job content strategy. In Eder,
R. W. & Ferris, G. R. (Eds.), The employment interview: Theory, research, and practice (pp. 145-157). Newbury
Park, California: Sage Publications.
September 2008
U.S. Office of Personnel Management
 9

---

---

## RAG Chunk 005

<!-- source_type: methodology | category: technical | pages: 10-12 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 875 -->

### 中文译文 / 中文检索层

第四步是开发用于评价候选人的评分量表。文件指出，统一评分量表是结构化面试的重要组成部分。对行为面试而言，首先要为每项胜任力确定熟练度等级范围，例如 1 到 5 分，其中 5 代表最高熟练度，1 代表最低熟练度。评分等级至少应有三个，理想情况下为五到七个，并应为至少三个等级提供标签，如不满意、满意、优秀。OPM 给出了五级量表：Level 5 Expert、Level 4 Advanced、Level 3 Intermediate、Level 2 Basic、Level 1 Awareness。通用能力与技术能力都按照情境难度、所需指导程度，以及对概念和流程的理解水平区分。

### Original English Text

• Reconvene the panel of SMEs who developed the behavioral interview questions.
• For each question, have SMEs individually determine how actual employees at each
proficiency level would respond (i.e., what their answers would be).
o These hypothetical responses are behavioral examples for the proficiency levels.
• Have the SMEs discuss their behavioral examples.
• For each proficiency level, retain behavioral examples which the SMEs agree best reflect
the competency at that level.
• Instruct interviewers to use these behavioral examples as a general guide (not an
absolute) in making their ratings, as candidate’s responses may differ depending on their
unique experiences (Feild and Gatewood, 1989)4.

Table 2 presents an example behavioral interview rating scale for a question based on the
competency Interpersonal Skills. This rating scale has been supplemented with behavioral
examples to illustrate differences between the proficiency levels.

4 Feild, H. S., & Gatewood, R. D. (1989). Development of a selection interview: A job content strategy. In Eder,
R. W. & Ferris, G. R. (Eds.), The employment interview: Theory, research, and practice (pp. 145-157). Newbury
Park, California: Sage Publications.
September 2008
U.S. Office of Personnel Management
 9

Table 2: Example of a Behavioral Interview Question and Rating Scale
Competency: Interpersonal Skills
Definition: Shows understanding, friendliness, courtesy, tact, empathy, concern, and politeness to others;
develops and maintains effective relationships with others; may include effectively dealing with
individuals who are difficult, hostile, or distressed; relates well to people from varied backgrounds and
different situations; is sensitive to cultural diversity, race, gender, disabilities, and other individual
differences.
Question: Describe a situation in which you had to deal with individuals who were difficult, hostile,
or distressed. Who was involved? What specific actions did you take and what was the result?
Proficiency
Level
Definition
Question-Specific Behavioral Examples
Level 5
Expert
•
Applies the
competency in
exceptionally difficult
situations.
•
Serves as a key
resource and advises
others.
•
Presents shortcomings of a newly installed HR
automation system in a tactful manner to irate senior
management officials.
•
Explains the benefits of controversial policy changes
to a group of upset individuals at a public hearing.
•
Diffuses an emotionally charged meeting with external
stakeholders by expressing empathy for their concerns.
Level 4
Advanced
•
Applies the
competency in
considerably difficult
situations.
•
Generally requires
little or no guidance.
•
Facilitates an open forum to discuss employee
concerns about a new compensation system.
•
Builds on the ideas of others to foster cooperation
during bargaining agreement negotiations.
•
Identifies and emphasizes common goals to promote
cooperation between HR and line staff.
•
Identifies and alleviates sources of stress among a
team developing a new automated HR system.
Level 3
Intermediate
•
Applies the
competency in difficult
situations.
•
Requires occasional
guidance.
•
Restores a working relationship between angry co-
workers who have opposing views.
•
Remains courteous and tactful when confronted by an
employee who is frustrated by a payroll problem.
•
Establishes cooperative working relationships with
managers, so they are comfortable asking for advice
on HR issues.
Level 2
Basic
•
Applies the
competency in
somewhat difficult
situations.
•
Requires frequent
guidance.
•
Offers to assist employees in resolving problems with
their benefits election.
•
Works with other HR staff on a cross-functional team
to improve coordination of activities.
•
Works with others to minimize disruptions to an
employee working under tight deadlines.
Level 1
Awareness
•
Applies the
competency in the
simplest situations.
•
Requires close and
extensive guidance.
•
Refers employees to the appropriate staff member to
resolve their issues.
•
Works with others in the HR office to organize
information for employee intervention sessions on
controversial issues.
•
Works with others to obtain employee concerns about
controversial policy changes.

September 2008
U.S. Office of Personnel Management

10

Rating Scale and Behavioral Responses for a Situational Interview. As with behavioral
interview questions, the first step in the development of a rating scale for each situational
interview question is specifying the range of proficiency for each competency being assessed.

• Decide on one proficiency-level range for all competencies.
• Have at least three proficiency levels, but aim for five to seven levels.
• Provide labels for at least three proficiency levels (e.g., unsatisfactory, satisfactory,
and superior).

Next, develop a representative response for each competency proficiency-level for each
hypothetical job-scenario question. A representative response illustrates how someone with the
given proficiency level on the given competency might behave. To develop the representative
responses for proficiency levels of each situational interview question, follow these steps:

• Reconvene the panel of subject matter experts (SMEs) who developed the interview
questions.
• For each hypothetical scenario, have each SME individually determine how actual
employees at each proficiency level might behave (i.e., what their answers would be).
o These answers are representative responses for the proficiency-level ratings.
• Have the SMEs discuss their representative responses.
• For each proficiency level, retain the representative responses which the SMEs agree are
the best.

Table 3 shows an example proficiency-level rating scale for a situational interview question with
representative responses for each proficiency level. The situational interview question is derived
from a job task and reflects a particular competency. This linkage needs to be present for all
questions.

September 2008
U.S. Office of Personnel Management

11

---

---

## RAG Chunk 006

<!-- source_type: methodology | category: behavior | pages: 12-15 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 899 -->

### 中文译文 / 中文检索层

对行为面试，还应为每个问题、每项胜任力的每个熟练度等级开发行为示例。行为示例的作用是清楚区分不同熟练度层级，让面试官在评分时有具体行为参照，从而以一致方式评估候选人。主题专家应重新聚集，针对每个问题分别判断不同熟练度员工可能如何回答，并讨论保留最能代表该层级胜任力的行为示例。文件提醒，行为示例应作为一般指南，而不是绝对标准，因为候选人的回答会因个人经历不同而有所差异。随后给出“人际技能”问题的评分表，展示从 Awareness 到 Expert 各等级的定义和具体行为例子。

### Original English Text

• Reconvene the panel of subject matter experts (SMEs) who developed the interview
questions.
• For each hypothetical scenario, have each SME individually determine how actual
employees at each proficiency level might behave (i.e., what their answers would be).
o These answers are representative responses for the proficiency-level ratings.
• Have the SMEs discuss their representative responses.
• For each proficiency level, retain the representative responses which the SMEs agree are
the best.

Table 3 shows an example proficiency-level rating scale for a situational interview question with
representative responses for each proficiency level. The situational interview question is derived
from a job task and reflects a particular competency. This linkage needs to be present for all
questions.

September 2008
U.S. Office of Personnel Management

11

Table 3: Example of a Situational Interview Question and Rating Scale
Job Task
Competency
Interview Question
Proficiency Level &
Representative
Response
Performs
investigative work to
obtain information,
gather evidence, or
verify facts.
Integrity/ Honesty:
Contributes to
maintaining the
integrity of the
organization; displays
high standards of
ethical conduct and
understands the
impact violating these
standards would have
on an organization,
self, and others; is
trustworthy.

You are investigating
a group of auto
dealership managers
suspected of money-
laundering activities.
During the course of
an interview with one
suspect, the suspect
offers to help you buy
a car at a price you
know is well below
market value. What
would you do?

Unsatisfactory:
Accept the offer.

Satisfactory:
Say no to the offer and
continue the
investigation; document
the incident in your
report.

Superior:
Probe the dealership
managers to determine
how they are able to
offer a car at such a
reduced price; attempt to
get contact information
of others involved; say
no to the offer; and
document the details of
the incident.

5. Create Interview Probes

A probe is a question asked by the interviewer to help clarify a candidate’s response or ensure
the candidate has provided enough information. When probes are necessary, interviewers should
use very similar probes for all candidates to ensure candidates are given the same opportunities
to excel. While probes may need to be tailored to address each candidate’s specific response, the
general meaning of the probes should not change.

• Prior to the interview, establish the desired range of probing (for example, no probes, a
limited number of probes, unlimited probes).
• If probes will be used, determine the specific probes for each question the interviewer is
allowed to use.

Example probes for behavioral- and situational-interview questions are presented in Table 4.

September 2008
U.S. Office of Personnel Management

12

Table 4: Example Probes for Behavioral- and Situational-Interview Questions
Competency: Interpersonal Skills
Behavioral Interview Question:
Describe a situation in which you had
to deal with individuals who were
difficult, hostile, or distressed. Who
was involved? What specific actions
did you take and what was the result?
Behavioral Interview Probes:
Situation
• What factors led up to the situation?
• Could you or anyone else have done something
to prevent the situation?
• What did you determine as the most critical issue
to address in this situation?

Action
• How did you respond?
• What was the most important factor you
considered in taking action?
• What is the first thing you did?

Outcome
• What was the outcome?
• Is there anything you would have said and/or
done differently?
• Were there any benefits from the situation?

Situational Interview Question:
A very angry client walks up to your
desk. She says she was told your
office sent her an overdue check five
days ago. She claims she has not
received the check. She says she has
bills to pay, and no one will help her.
How would you handle this
situation?
Situational Interview Probes:
Situation
• Why do you believe this situation occurred?
• What do you consider the most critical issue in
this situation?
• What other issues are of concern?

Action
• What would you say?
• What is the first thing you would do?
• What factors would affect your course of action?
• What other actions could you take?

Outcome
• How do you think your action would be
received?
• What would you do if your action was not
received well?
• What do you consider as benefits of your action?

September 2008
U.S. Office of Personnel Management

13

6. Pilot Test the Interview Questions and Evaluate the Interview Process

Prior to using the newly developed behavioral interview and/or situational interview questions in
an actual interview, give the questions to colleagues for a trial run. This trial run (i.e., pilot test)
will ensure questions are clearly worded and draw an appropriate range of responses. The pilot
test will indicate if and where revisions need to be made. To the extent possible, the pilot test
should mirror the actual structured interview.

7. Create the Interviewer’s Guide

After finalizing the questions and rating scales, create an interviewer’s guide. The interviewer’s
guide should provide general instructions about the interview process, a summary of common
rating biases and rating mistakes to avoid, and general tips for good interviewing (see Section II).
The guide should also provide information specific to the particular interview, including:

• Definitions of each competency being assessed
• Proficiency levels of each competency
• Interview questions
• Rating scale (with behavioral examples and/or representative responses) for each
question
• Example probes

8. Document the Development Process

---

---

## RAG Chunk 007

<!-- source_type: methodology | category: behavior | pages: 15-17 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 811 -->

### 中文译文 / 中文检索层

情景面试的评分量表也需要先确定胜任力熟练度范围，并为各等级提供标签。然后，针对每个假设岗位情境，为每个熟练度等级设计代表性回答。代表性回答说明具备某一能力水平的人在该情境中可能如何行动。开发方式是让原先编写面试问题的主题专家分别写出不同等级员工可能的回答，再集体讨论并保留最合适的代表性回答。文件给出诚信/正直能力的情景题示例：调查汽车经销商洗钱活动时，嫌疑人提出以低于市场价帮助你买车，你会怎么做。评分示例中，不满意回答是接受报价；满意回答是拒绝并继续调查、记录事件；优秀回答还会进一步追问低价来源、获取相关人员信息，并完整记录。

### Original English Text

Prior to using the newly developed behavioral interview and/or situational interview questions in
an actual interview, give the questions to colleagues for a trial run. This trial run (i.e., pilot test)
will ensure questions are clearly worded and draw an appropriate range of responses. The pilot
test will indicate if and where revisions need to be made. To the extent possible, the pilot test
should mirror the actual structured interview.

7. Create the Interviewer’s Guide

After finalizing the questions and rating scales, create an interviewer’s guide. The interviewer’s
guide should provide general instructions about the interview process, a summary of common
rating biases and rating mistakes to avoid, and general tips for good interviewing (see Section II).
The guide should also provide information specific to the particular interview, including:

• Definitions of each competency being assessed
• Proficiency levels of each competency
• Interview questions
• Rating scale (with behavioral examples and/or representative responses) for each
question
• Example probes

8. Document the Development Process

You should maintain records of the entire interview development process, in accordance with the
Delegated Examining Operations Handbook. The documentation should include:

• Descriptions of all participants, including subject matter experts and those in the pilot
study (e.g., name, job title, race, national origin, sex, and level of expertise).
• Interview development materials (e.g., reference materials, previous manuals).
• A description of the development of the interview, including the job analysis, the
question and rating scale development process, and the pilot test.
September 2008
U.S. Office of Personnel Management

14

Section II: Administering a Structured Interview

Interviewers

In Federal Agencies, interviews are typically conducted by one person, namely the selecting
official (i.e., supervisor) for the position being filled. While the following sections are directed
toward the use of one interviewer, a structured interview may also be administered by a panel of
interviewers. A typical panel consists of two or more persons who have extensive knowledge of
the job and are trained in administering interviews.

For information on using a panel to conduct the structured interview, please refer to Appendix D.

Training Your Interviewer

It is essential to train the person who will administer the structured interview. Interviewer
training increases the accuracy of the interview. Before or during the training, the interviewer
should receive a guide describing the interview process in detail.

Appendix E provides a sample lesson plan for an interviewer training course. The training
should emphasize the importance of note-taking, discuss the impact of the interviewer’s non-
verbal behavior, and review common rating biases and errors.

Note-Taking. Taking regular and detailed notes of observable behaviors and verbal responses
during each interview is crucial. Notes will reduce the burden on the interviewer to remember
details about multiple candidates. Additionally, these notes should:

• Summarize the content and delivery of respondents’ answers.
• Document the candidate’s grammar, body language, and other non-verbal factors.
• Help interviewers focus on pertinent information during the interview.
• Be of sufficient quality and quantity to document the interviewer’s reasoning for each
rating on each competency.
• Serve as documentation to support the employment decision.

Interviewer’s Non-Verbal Behavior. An interviewer’s body language such as facial expressions
and body movements (e.g., nodding, raising eyebrows, frowning) communicates a lot to the
candidate. For example, the interviewer communicates disinterest by slouching, regularly
looking at the clock, leaning back, or doodling with a pen.

Interviewers need be aware of their body language to avoid communicating negative
impressions. Additionally, while taking notes, interviewers should make periodic eye contact
with the candidate to show their interest and to provide opportunities to observe the candidate’s
non-verbal behavior.

September 2008
U.S. Office of Personnel Management

15

Interpersonal Bias and Rating Errors. Bias and rating errors are inconsistent with the purpose
of the structured interview process, namely, ensuring candidates are evaluated fairly,
consistently, and have equal opportunities to excel. The interviewer should not be influenced by
personal biases or fall prey to common rating errors.

Biases can take a variety of forms. For example, an interviewer might give higher ratings to
candidates who appear outwardly similar to him/her. Rating errors might include giving all high
ratings or all low ratings to candidates. Appendix F describes common rating errors and
interviewing mistakes.

The Interview Setting

The interview should take place in a comfortable environment.

• Interviews should be held in a quiet, non-threatening, and private place.
• Seating arrangements should be the same for all candidates.
• The interview room and facilities must be accessible to candidates with disabilities.
• There should be a separate area for those waiting to be interviewed.
• Individuals who have been interviewed should not be allowed to communicate with those
waiting to be interviewed.
• Interviews should be scheduled far enough in advance to provide adequate preparation
time for the interviewer.
• All candidates should be allotted the same amount of interview time.

Conducting the Interview

---

---

## RAG Chunk 008

<!-- source_type: methodology | category: case | pages: 17-19 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 885 -->

### 中文译文 / 中文检索层

第五步是创建面试追问。追问是面试官为澄清候选人回答或确保信息充分而提出的问题。为了保证公平，若使用追问，不同候选人应获得类似的追问机会；追问可以根据具体回答稍作调整，但总体含义不应改变。面试前应确定允许追问的范围，例如不追问、有限追问或无限追问；如果允许追问，应为每个问题预先确定面试官可以使用的具体追问。文件展示了行为面试和情景面试的追问示例，并按 Situation、Action、Outcome 三类组织。行为追问包括情境如何形成、最关键问题是什么、你如何回应、第一步做了什么、结果如何、是否会采取不同做法等。

### Original English Text

Biases can take a variety of forms. For example, an interviewer might give higher ratings to
candidates who appear outwardly similar to him/her. Rating errors might include giving all high
ratings or all low ratings to candidates. Appendix F describes common rating errors and
interviewing mistakes.

The Interview Setting

The interview should take place in a comfortable environment.

• Interviews should be held in a quiet, non-threatening, and private place.
• Seating arrangements should be the same for all candidates.
• The interview room and facilities must be accessible to candidates with disabilities.
• There should be a separate area for those waiting to be interviewed.
• Individuals who have been interviewed should not be allowed to communicate with those
waiting to be interviewed.
• Interviews should be scheduled far enough in advance to provide adequate preparation
time for the interviewer.
• All candidates should be allotted the same amount of interview time.

Conducting the Interview

Supplemental Materials. While candidates may be permitted to bring supplemental documents
to the interview (e.g., references, transcripts, or a resume), this information is for the candidate’s
reference only and should not be looked at by the interviewer during the interview. Allowing
interviewers to look at these documents during the interview may bias the interviewer’s
perceptions of the candidates (e.g., interviewers might rate the responses of candidates with
strong resumes more favorably then those of candidates with weak resumes). If interviewers
look at supplemental information during the interview and this supplemental information is not
provided by all candidates, candidates may be evaluated inconsistently.

Arrival of the Candidate.

• Welcome the candidate in a warm and friendly manner.
• Thank the candidate for his/her interest in the position and for coming to the interview.
• Briefly describe the job and relevant organizational characteristics to allow candidates to
become comfortable in the interview setting.
• Explain the interview process in a standardized way. You may also provide this
information in writing to each candidate.
• Inform the candidate that notes will be taken throughout the interview.
• Ask the candidate if he/she has any questions before beginning.

September 2008
U.S. Office of Personnel Management

16

At the end of the interview, the interviewer should ask, “Is there anything else you would like us
to know?” and provide the candidate with an opportunity to ask questions. The interviewer
should then thank and excuse the candidate.

Rating Each Candidate. Immediately after the candidate leaves the room, the interviewer
should review his or her notes and, if the interview is being rated, rate the candidate. Notes
should include actual behavioral examples and ratings should be defensible and supported by the
notes. Examples of actual answers given should be included along with explanations of how
these answers apply to the competency being rated and why they merit the given rating.
Examples of rating forms for use by one interviewer or a panel of interviewers can be found in
Appendix G and Appendix H, respectively.

After all candidates have been rated, the interviewer should:

• Review the ratings given to each candidate.
• Ensure the total performance of each candidate has been considered thoroughly and
objectively.
• Ensure the ratings are tied to specific behavioral examples.
• Sign and date each rating form.

Documenting the Interview Process

In addition to the documentation mentioned above, the following information should be recorded
and retained:
• Date, time, place, and length of the interview
• Name, job title, race, national origin, and sex of the interviewer
• Interview questions, scores, and notes for each candidate
• Training provided to the interviewer
• Interview guides, rating scales, and other materials used

September 2008
U.S. Office of Personnel Management

17

References

Campion, J. E., & Arvey, R. D. (1989). Unfair discrimination in the employment interview.

In Eder, R. W. & Ferris, G. R. (Eds.), The employment interview: Theory, research and

practice (pp. 61-73). Newbury Park, California: Sage Publications.

Campion, M. A., Campion, J. E., & Hudson, J. P. Jr. (1994). Structured interviewing: A note on

incremental validity and alternative question types. Journal of Applied Psychology, 79,

998-1002.

Campion, M. A., Palmer, D. K., & Campion, J. E. (1997). A review of structure in the

selection interview. Personnel Psychology, 50, 655-702.
Campion, M., Pursell, E., & Brown, B. (1988). Structured interviewing: Raising the
psychometric properties of the employment interview. Personnel Psychology, 41, 25-42.
Cascio, W. F., & Aguinis, H. (2005). Applied Psychology in Human Resource Management, 6th

Edition. New Jersey: Pearson Prentice Hall.

Conway, J. M., & Peneno, G. M. (1999). Comparing structured interview question types:

Construct validity and candidate reactions. Journal of Business and Psychology, 13,

485-506.

Day, A. L., & Carroll, S. A. (2003). Situational and patterned behavior description interviews:

A comparison of their validity, correlates, and perceived fairness. Human Performance,

16, 25-47.

Feild, H. S., & Gatewood, R. D. (1989). Development of a selection interview: A job content
strategy. In Eder, R. W. & Ferris, G. R. (Eds.), The employment interview: Theory,
research, and practice (pp. 145-157). Newbury Park, California: Sage Publications.

Flanagan, J. C. (1954). The critical incident technique. Psychological Bulletin, 51, 327-358.

Gael, S. (1984). Job analysis: A guide to assessing work activities. San Francisco:

Jossey-Bass.

Harris, M. M. (1989). Reconsidering the employment interview: A review of recent literature

and suggestions for future research. Personnel Psychology, 42, 691-726.

---

---

## RAG Chunk 009

<!-- source_type: methodology | category: structured | pages: 19-23 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 886 -->

### 中文译文 / 中文检索层

第六到第八步分别是试测问题、创建面试官指南、记录开发过程。正式使用新开发的行为或情景问题前，应先让同事试运行，以检查问题是否清晰，是否能引出合适范围的回答；试测应尽量模拟真实结构化面试。问题和评分量表最终确定后，应创建面试官指南，内容包括面试流程说明、常见评分偏差和错误、良好面试技巧，以及本次面试的具体信息，如胜任力定义、熟练度等级、面试问题、评分量表、行为示例或代表性回答、追问示例。开发过程也应完整留档，包括参与者信息、开发材料、工作分析、问题和量表开发过程以及试测情况。

### Original English Text

Construct validity and candidate reactions. Journal of Business and Psychology, 13,

485-506.

Day, A. L., & Carroll, S. A. (2003). Situational and patterned behavior description interviews:

A comparison of their validity, correlates, and perceived fairness. Human Performance,

16, 25-47.

Feild, H. S., & Gatewood, R. D. (1989). Development of a selection interview: A job content
strategy. In Eder, R. W. & Ferris, G. R. (Eds.), The employment interview: Theory,
research, and practice (pp. 145-157). Newbury Park, California: Sage Publications.

Flanagan, J. C. (1954). The critical incident technique. Psychological Bulletin, 51, 327-358.

Gael, S. (1984). Job analysis: A guide to assessing work activities. San Francisco:

Jossey-Bass.

Harris, M. M. (1989). Reconsidering the employment interview: A review of recent literature

and suggestions for future research. Personnel Psychology, 42, 691-726.

Huffcutt, A. I., Weekley, J. A., Wiesner, W. H., Degroot, T. G., & Jones, C. (2001).
Comparison of situational and behavior description interview questions for higher-level
positions. Personnel Psychology, 54, 619-644.

Janz, T. (1982). Initial comparisons of patterned behavior description interviews versus

unstructured interviews. Journal of Applied Psychology, 67, 557-580.
September 2008
U.S. Office of Personnel Management

18

Latham, G. P. & Saari, L. M. (1984). Do people do what they say? Further studies on the

situational interview. Journal of Applied Psychology, 69, 569-573.

Latham, G. P., Saari, L. M., Pursell, E. D., & Campion, M. A. (1980). The situational interview.

Journal of Applied Psychology, 65, 422-427.

Latham, G. P., & Sue-Chan, C. (1999). A meta-analysis of the situational interview: An

enumerative review of reasons for its validity. Canadian Psychology, 40, 56-67.

Locke, E. A. (1968). Towards a theory of task motivation and incentives. Organizational

Behavior and Human Performance, 3, 157-189.

McDaniel, M. A., Whetzel, D. L., Schmidt, F. L., & Maurer, S. D. (1994). The validity of

employment interviews: A comprehensive review and meta-analysis. Journal of Applied

Psychology, 79, 599-616.

Mento, A. J. (1980). Suggestions for structuring and conducting the selection interview

(Professional Paper 80-1). Washington, DC: U. S. Office of Personnel Management,

Personnel Research and Development Center.

Motowildo, S. J., Carter, G. W., Dunnett, M. D., Tippins, N., Werner, S., Burnett, J. R., &

Vaughn, M. J. (1992). Studies of the structured behavioral interview. Journal of

Applied Psychology, 77, 571-587.

Muldrow, T. W. (1987). Developing and conducting interviews: Some general guidance.

Washington, DC: U. S. Office of Personnel Management.

Orpen, C. (1985). Patterned behavior description interviews versus unstructured interviews: A

comparative validity study. Journal of Applied Psychology, 70, 774-776.

Outerbridge, A. N. (1994). Developing and conducting the structured situational interview: A
practical guide. Washington, DC: U.S. Office of Personnel Management, Office of
Personnel Research and Development, PRD-94-01.

Pulakos, E. D., & Schmitt, N. (1995). Experience-based and situational interview questions:

Studies of validity. Personnel Psychology, 48, 289-308.

Schmidt, F. L., & Hunter, J. E. (1998). The validity and utility of selection methods in

personnel psychology: Practical and theoretical implications of 85 years of research

findings. Psychological Bulletin, 124, 262-274.

Terpstra, D. E., Mohamed, A. A., & Kethley, R. B. (1999). An analysis of Federal court cases

involving nine selection devices. International Journal of Selection and Assessment, 7,

26-34.

September 2008
U.S. Office of Personnel Management

19

U. S. Merit Systems Protection Board. (2003). The federal selection interview: Unrealized

potential. Washington, DC: Office of Policy and Evaluation.

Whitley, B. E. (2002). Principles of Research in Behavioral Science, 2nd Edition. New York:

McGraw-Hill.

September 2008
U.S. Office of Personnel Management

20

Appendix A: Structured Interview Implementation
Checklist

Assess the Current Selection Situation. Discuss the need for developing a structured
interview and the specific goals for the structured interview. Also determine which job or
jobs will use the structured interview.

Determine Where the Structured Interview Fits within the Selection Process.
Determine where to place the structured interview in the selection of job candidates (e.g.,
after a written test, as the last selection procedure). Federal Agencies typically use the
interview after candidates have been determined eligible for a given job and rated/ranked
on the basis of other assessment tools (e.g., a written test or resume). The interview is then
used to verify a candidate's qualifications.

Create a Development and Implementation Plan with Timelines. Plan the major steps
for developing the structured interview, including updating or conducting a job analysis,
convening subject matter experts to develop the interview questions and rating scale, and
training interviewers on how to evaluate candidates.

Ensure Compliance of the Plan with Established Guidelines. Make sure the structured
interview process complies with the requirements in The Uniform Guidelines on
Employee Selection Procedures and the Delegated Examining Operations Handbook.

Create a Communication Plan and Obtain Commitment to the Plan. Ensure managers
are aware of the intent of the structured interview.

Establish Structured Interview Development Team(s). Identify the development and
implementation team, which may include human resources specialists, selecting officials,
supervisors, and/or employees.

Develop the Structured Interview. (See Appendix B: Structured Interview Development
Checklist)

Administer the Structured Interview.

Evaluate the Results. Monitor the implementation of the structured interview on a
periodic basis to ensure the plan is followed and the intended results are achieved. Adjust
the structured interview procedure as necessary.

September 2008
U.S. Office of Personnel Management

21

Appendix B: Structured Interview Development
Checklist

1. Conduct a Job Analysis. Identify the job characteristics (i.e., job tasks, duties, and
responsibilities) and the competencies/knowledge, skills, abilities required to perform the
job successfully.

---

---

## RAG Chunk 010

<!-- source_type: methodology | category: structured | pages: 22-26 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 891 -->

### 中文译文 / 中文检索层

第二部分讨论如何实施结构化面试。面试可由单名面试官或面试小组完成；小组通常由两名以上熟悉岗位且接受过面试培训的人组成。培训面试官非常重要，因为培训可以提高面试准确性。培训应强调做笔记的重要性、非语言行为对候选人的影响，以及常见评分偏差和错误。面试笔记应定期、详细记录候选人的可观察行为和口头回答，总结回答内容与表达方式，记录语法、肢体语言等非语言因素，并足以支持每项胜任力评分的理由。面试官还应注意自身非语言行为，避免通过身体姿态、表情或动作传递消极印象，同时在做笔记时保持适当眼神交流。

### Original English Text

Create a Communication Plan and Obtain Commitment to the Plan. Ensure managers
are aware of the intent of the structured interview.

Establish Structured Interview Development Team(s). Identify the development and
implementation team, which may include human resources specialists, selecting officials,
supervisors, and/or employees.

Develop the Structured Interview. (See Appendix B: Structured Interview Development
Checklist)

Administer the Structured Interview.

Evaluate the Results. Monitor the implementation of the structured interview on a
periodic basis to ensure the plan is followed and the intended results are achieved. Adjust
the structured interview procedure as necessary.

September 2008
U.S. Office of Personnel Management

21

Appendix B: Structured Interview Development
Checklist

1. Conduct a Job Analysis. Identify the job characteristics (i.e., job tasks, duties, and
responsibilities) and the competencies/knowledge, skills, abilities required to perform the
job successfully.

2. Determine the Competencies to be Assessed by the Interview. Consider which
competencies are measured most effectively with an interview.

3. Choose the Interview Format and Develop Questions. Determine if you will use a
behavioral interview or situational interview. Work with subject matter experts to
develop questions.

4. Develop Rating Scales to Evaluate Candidates. Determine the proficiency scale
and develop accompanying proficiency level examples. (NOTE: May not be applicable
to a selecting official’s interview.)

5. Create Interview Probes. Establish if probes may be used. If probes will be used,
draft specific probes for each question.

6. Pilot-Test the Interview Questions. Pilot test the interview questions on persons
similar to the anticipated candidates. Check for clarity and appropriateness.

7. Create the Interviewer’s Guide. Prepare an interviewer's guide, question booklet,
and rating form.

8. Document the Development Process. Document all stages of the interview
development.

September 2008
U.S. Office of Personnel Management

22

Appendix C: Sample Critical Incident Forms

Effective Incident Form
Job Title:
Competency:
Instructions:
Think of an incident during the past year in which you were particularly proud of your
performance, or the performance of a coworker, and share it with us. The incident must be
related to performance on the job. The incident may have involved people, facilities,
information, or another item relevant to performance on the job.

Recalling this incident, please answer the following questions:
1. What circumstances led to the incident? (Situation)
2. What did you or your co-worker do that was very effective at the time? (Action)
3. Why was this incident very helpful in getting the job done? (Outcome)

September 2008
U.S. Office of Personnel Management

23

Ineffective Incident Form
Job Title:
Competency:
Instructions:
Think back over the past year and describe an incident that should have been handled differently.
The incident must be related to your performance or the performance of a coworker on the job.
The incident may have involved people, facilities, information, or another item relevant to
performance on the job.

Recalling the incident, please answer the following questions:
1. What circumstances led to the incident? (Situation)
2. What did you or your co-worker do that was ineffective at that time? (Action)
3. What were the effects of the actions? (Outcome)
4. What should have been done differently?
September 2008
U.S. Office of Personnel Management

24

Appendix D: Panel Interviews

During the interview process, an abundance of information is exchanged between the candidate
and the interviewer. A panel of two or three interviewers may be better able to document and
interpret the information. A panel also reduces the risk of biases in ratings and allows for a
diverse (e.g., race and sex) range of interviewers, indicating to the candidate that the organization
values diversity and fair treatment.

Interviewers may conduct the interview together at one time or individually in a serial fashion in
which the candidate progresses through multiple interviews. When feasible, the same
interviewers should be used (either in a panel or serially) across all candidates, to ensure
consistency in ratings.

In a panel interview, each panel member should individually observe, record, and evaluate the
responses of the candidates. After each candidate, panel members should discuss their individual
ratings. Final scores or ratings should be based on the consensus of the panel. This process is
described in more detail below.

Although the interview panel works as a team, one panel member is typically designated as the
chairperson or coordinator and he/she is responsible for the administrative and logistical
arrangements of the interview and for documenting the process.

Conducting a Panel Interview

Before the candidate enters the interview room, the panel coordinator should verify all panel
members understand the procedures to be followed and have all necessary materials. The
interview process should be described in detail in the interviewer's guide and the guide should be
provided to each panel member.

Upon each candidate’s arrival, the panel coordinator should:

• Welcome the candidate and introduce each panel member.
• Thank the candidate for his/her interest in the position and for coming to the interview.
• Briefly describe the job and relevant organizational characteristics as to allow candidates
to become comfortable in the interview setting.
• Explain the interview process in a standardized way. This explanation may also be
provided to applicants in writing.
• Inform the candidate that notes will be taken throughout the interview.
• Ask if the candidate has any questions before beginning.

At the end of the interview, the coordinator should thank the candidate, answer any general
questions, and excuse the candidate.

September 2008
U.S. Office of Personnel Management

25

---

---

## RAG Chunk 011

<!-- source_type: methodology | category: case | pages: 26-30 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 859 -->

### 中文译文 / 中文检索层

文件指出，偏见和评分错误会破坏结构化面试的目标，即保证候选人被公平、一致地评价，并拥有同等表现机会。面试官不应受个人偏见影响，例如因候选人与自己外表相似而给出更高分，也不应出现所有候选人都打高分或低分等评分错误。面试环境应安静、私密、不具威胁性，座位安排对所有候选人一致，房间和设施应方便残障候选人使用。候选人等待区应与已面试人员隔开，防止信息交流。所有候选人应获得相同面试时间。候选人可带简历、成绩单等补充材料作为自己参考，但面试官不应在面试中查看，以免形成对回答评分的偏差。

### Original English Text

Upon each candidate’s arrival, the panel coordinator should:

• Welcome the candidate and introduce each panel member.
• Thank the candidate for his/her interest in the position and for coming to the interview.
• Briefly describe the job and relevant organizational characteristics as to allow candidates
to become comfortable in the interview setting.
• Explain the interview process in a standardized way. This explanation may also be
provided to applicants in writing.
• Inform the candidate that notes will be taken throughout the interview.
• Ask if the candidate has any questions before beginning.

At the end of the interview, the coordinator should thank the candidate, answer any general
questions, and excuse the candidate.

September 2008
U.S. Office of Personnel Management

25

Making Candidate Ratings. Each panel member should independently review his/her notes
immediately after the candidate leaves the room and, if the interview is not a selecting official’s
interview, rate the candidate. At this stage, each panelist is forming an independent evaluation
without discussion with other panel members. Ratings should be specific, defensible, and
supported by behavioral examples. Interviewers should include actual examples of answers
given, explanations of how these answers apply to the competency being rated, and why they
merit the given rating.

After panel members have independently rated all candidates, they should compare notes,
ratings, and supporting observations. Panel members should thoroughly explore the basis for
discrepancies in their ratings, and then reach a consensus on each candidate. Statements made
by the candidate should be recorded to support specific ratings. Panelists should record the
consensus rating for each candidate on a group rating form. Appendix H provides a sample
group rating form.

After the last candidate has been rated, panelists should review the group ratings given to all
candidates. This exchange will ensure the performance of each candidate has been considered
thoroughly and objectively. This also ensures the final ratings represent the consensus judgment
of the panel. After all ratings have been meticuously reviewed, they should be declared final and
each member should attest to the final ratings by signing the group rating form.

September 2008
U.S. Office of Personnel Management

26

Appendix E: Sample Lesson Plan for an Interviewer
Training Course

Lesson 1: Introduction
• Interview Reliability and Validity
• Court Challenges and the Importance of adding Structure to the Interview Process
• Relationship of the Interview to the Total Hiring Process

Lesson 2: Interview Material
• General Interview Guidelines
• Awareness of Interviewer Biases and Mistakes
• Competency Definitions and Job Information
• Interview Questions (Behavior Interview or Situational Interview)
• Behavioral examples Responses
• Rating Forms and Procedures
• Sample Rating Forms

Lesson 3: Interview Process and Practice Exercises
• Interview Procedures
• Checklist of “Do’s and Don’ts” for Conducting the Interview
• Critiqued Practice Using a Videotaped Interview
• Security of Interview Materials
September 2008
U.S. Office of Personnel Management

27

Appendix F: Common Rating Errors and
Interviewing Mistakes

Common Rating Errors

One way to minimize rating errors is to make interviewers aware of the most common types of
error, which are summarized below.

1. Rater Bias: Allowing prejudices about certain groups of people or personalities to interfere
with being able to fairly evaluate a candidate’s performance. Interviewers should refrain
from considering any non-performance related factors when making judgments.

2. Halo Effect: Allowing ratings of performance in one competency to influence ratings for
other competencies. For example, allowing a high rating on Oral Communication to bias the
rating on Problem Solving, irrespective of the candidate’s performance on Problem Solving.

3. Central Tendency: A tendency to rate all competencies at the middle of the rating scale (for
example, giving all “3s” on a 5-point scale). When hesitating over making a high rating,
interviewers should realize such a rating does not indicate perfect performance; it means
demonstrating more of the competency than is generally exhibited. Similarly, when
hesitating over a low rating, interviewers should realize it does not mean the candidate does
not possess the competency; it means he/she did not demonstrate much of the competency in
his/her interview responses.

4. Leniency: A tendency to give high ratings to all candidates, irrespective of their actual
performance. There may be candidates who could benefit from further development in
certain areas. Interviewers should allow their ratings to reflect these intra- and inter-
individual differences.

5. Strictness: A tendency to give low ratings to all candidates, irrespective of their actual
performance. There may be outstanding candidates whose demonstration of competencies
warrants high ratings. Interviewers should allow their ratings to reflect these intra- and inter-
individual differences.

6. Similar to Me: Giving higher than deserved ratings to candidates who appear similar to you.
People have a natural tendency to prefer others who are similar in various ways to
themselves. Interviewers should concentrate on the responses given by the candidate in
making evaluations, rather than on the outward characteristics and personality of the
candidate.

Interviewers can minimize these rating errors by thoroughly understanding the competencies
being assessed and by learning to compare the behaviors exhibited in the interview with the
behaviors anchoring the proficiency-level ratings for each competency.

September 2008
U.S. Office of Personnel Management

28

Common Interviewing Mistakes

---

---

## RAG Chunk 012

<!-- source_type: methodology | category: case | pages: 29-32 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 885 -->

### 中文译文 / 中文检索层

候选人到达时，面试官应以温暖友好的方式欢迎，感谢其参加面试，简要介绍岗位和组织特征，使用标准化方式解释面试流程，并告知面试期间会做笔记。开始前可询问候选人是否有问题。面试结束时，应询问“还有什么希望我们了解的吗？”并给候选人提问机会，随后感谢并结束面试。候选人离开后，面试官应立即回顾笔记并评分。笔记应包含真实行为例子，评分应可辩护并由笔记支持。所有候选人评分后，面试官应复核评分，确保每名候选人的整体表现被客观充分考虑，评分与具体行为例子相连，并在评分表上签名和注明日期。

### Original English Text

5. Strictness: A tendency to give low ratings to all candidates, irrespective of their actual
performance. There may be outstanding candidates whose demonstration of competencies
warrants high ratings. Interviewers should allow their ratings to reflect these intra- and inter-
individual differences.

6. Similar to Me: Giving higher than deserved ratings to candidates who appear similar to you.
People have a natural tendency to prefer others who are similar in various ways to
themselves. Interviewers should concentrate on the responses given by the candidate in
making evaluations, rather than on the outward characteristics and personality of the
candidate.

Interviewers can minimize these rating errors by thoroughly understanding the competencies
being assessed and by learning to compare the behaviors exhibited in the interview with the
behaviors anchoring the proficiency-level ratings for each competency.

September 2008
U.S. Office of Personnel Management

28

Common Interviewing Mistakes

1. Relying on First Impressions: Interviewers tend to make rapid decisions about the
qualifications of a candidate within the first few minutes of the interview based on minimal
information. Interviewers should reserve their judgment until sufficient information on the
candidate has been gathered.

2. Negative Emphasis: Unfavorable information tends to be more influential and memorable
than favorable information. Interviewers should avoid focusing on negative information to
the exclusion of positive information.

3. Not Knowing the Job: Interviewers who do not have a comprehensive understanding of the
skills needed for the job often form their own opinion about what constitutes the best
candidate. They use this personal impression to evaluate candidates. Therefore, it is
important to make sure interviewers fully understand the requirements of the job.

4. Pressure to Hire: When interviewers believe they need to make a decision quickly, they
tend to make decisions based on a limited sample of information, or on a small number of
candidate interviews. Interviewers should adhere to the established interview procedure and
timeline with each candidate to avoid making erroneous decisions.

5. Contrast Effects: The order in which the candidates are interviewed can affect the ratings
given to candidates. While making ratings, interviewers should refrain from comparing and
contrasting candidates to those who have been previously interviewed.

6. Nonverbal Behavior: Interviewers should base their evaluation of the candidate on the
candidate’s past performance and current behavior as it relates to the competency being
evaluated and not just on how the candidate acts during the interview. Questions and probes
relating to the competencies of interest will usually direct the interviewer to the important
information.

September 2008
U.S. Office of Personnel Management

29

Appendix G: Sample Structured Interview
Individual Rating Form

GENERAL COMPETENCIES:
The proficiency-level behavioral examples illustrate the types of behavior associated with each
proficiency level, across the full range of HR functions. They are only examples, and candidates
may demonstrate proficiency through behaviors not listed.

Writing: Recognizes or uses correct English grammar, punctuation, and spelling; communicates
information (e.g., facts, ideas, or messages) in a succinct and organized manner; produces written
information, which may include technical material that is appropriate for the intended audience.

Proficiency
Rating
 (choose
only one)
Proficiency Level Behavioral Examples for Typical
HR Positions
Proficiency Level Definition

 1

The candidate can apply the
competency in the simplest situations.
The candidate requires close and
extensive guidance.
• Accurately copies information from one source to
another.
• Composes basic memos and emails.
• Completes standard forms such as training forms and
travel orders.
 2

The candidate can apply the
competency in somewhat difficult
situations. The candidate will require
frequent guidance.

• Assists in developing training materials for managers
and employees.
• Writes responses to non-selected job applicants.
• Writes congratulatory letter to award recipients.
 3

The candidate can apply the
competency in difficult situations.
The candidate may require occasional
guidance.

• Proofreads internal memos for format and grammatical,
spelling, and typographical errors.
• Prepares informational material to communicate a new
leave policy to employees.
• Prepares a flowchart of the organization’s hiring
process.
• Develops recruitment materials for a job fair.
 4

The candidate can apply the
competency in considerably difficult
situations. The candidate requires no
guidance.

• Writes a handbook for employees to describe HR
procedures.
• Prepares correspondence on a sensitive discipline case.
• Prepares a position paper to defend a controversial HR
program.
• Prepares organization’s written comments on proposed
classification standards.
 5

The candidate can apply the
competency in exceptionally difficult
situations. The candidate has served
as a key resource and advised others.

• Writes the organization’s strategic human capital plan.
• Authors an article about the organization’s innovative
HR practices.
• Develops legislative proposals to resolve critical HR
issues affecting the organization’s ability to achieve its
mission.
September 2008
U.S. Office of Personnel Management

30

Oral Communication: Expresses information (e.g., ideas or facts) to individuals or groups
effectively, taking into account the audience and nature of the information (e.g., technical,
sensitive, controversial); makes clear and convincing oral presentations; listens to others, attends
to nonverbal cues, and responds appropriately.

Proficiency
Rating
 (choose
only one)
Proficiency Level Definition
Proficiency Level Behavioral Examples for Typical
HR Positions

 1

The candidate can apply the
competency in the simplest
situations. The candidate requires
close and extensive guidance.
• Explains procedures for changing a beneficiary.
• Refers prospective applicants to organization’s
website.
• Responds to customer inquiries about pay
schedules.
 2

---

---

## RAG Chunk 013

<!-- source_type: methodology | category: technical | pages: 31-34 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 867 -->

### 中文译文 / 中文检索层

文件的参考文献部分列出了结构化面试、情景面试、行为描述面试、选拔效度、面试公平性、工作分析和人事测评等相关研究。引用包括 Campion、Latham、McDaniel、Schmidt 与 Hunter、Huffcutt、Pulakos、Motowidlo 等学者的研究，以及美国 Merit Systems Protection Board 和 OPM 的相关报告。这些文献为结构化面试相对于非结构化面试在可靠性、效度、公平性和法律防御性上的优势提供了理论与实证背景。对你的面试训练系统而言，这部分可作为方法论背书来源，用于解释为什么需要统一问题、统一评分标准、行为证据、胜任力模型、追问边界和评分记录。

### Original English Text

• Writes the organization’s strategic human capital plan.
• Authors an article about the organization’s innovative
HR practices.
• Develops legislative proposals to resolve critical HR
issues affecting the organization’s ability to achieve its
mission.
September 2008
U.S. Office of Personnel Management

30

Oral Communication: Expresses information (e.g., ideas or facts) to individuals or groups
effectively, taking into account the audience and nature of the information (e.g., technical,
sensitive, controversial); makes clear and convincing oral presentations; listens to others, attends
to nonverbal cues, and responds appropriately.

Proficiency
Rating
 (choose
only one)
Proficiency Level Definition
Proficiency Level Behavioral Examples for Typical
HR Positions

 1

The candidate can apply the
competency in the simplest
situations. The candidate requires
close and extensive guidance.
• Explains procedures for changing a beneficiary.
• Refers prospective applicants to organization’s
website.
• Responds to customer inquiries about pay
schedules.
 2

The candidate can apply the
competency in somewhat difficult
situations. The candidate will
require frequent guidance.

• Reports on project status during weekly team
meetings.
• Explains special pay rate eligibility criteria to
employees.
• Presents information about flexible work schedules
at new employee orientation.
• Conducts exit interviews.
 3

The candidate can apply the
competency in difficult situations.
The candidate may require
occasional guidance.

• Describes the organization’s employee assistance
program to groups within the HR community.
• Presents a summary of new regulations affecting
the organization’s mission at a staff meeting.
• Responds to position classification inquiries from
managers who are posting vacancies.
• Describes new HR services to managers.
 4

The candidate can apply the
competency in considerably
difficult situations. The candidate
requires no guidance.

• Facilitates focus groups to elicit feedback on
proposed performance management system.
• Presents controversial decisions about
organizational restructuring to employee groups.
• Explains complicated new pay regulations to a lay
group.
• Explains to recruiters the impact of a legal decision
on application procedures.
 5

The candidate can apply the
competency in exceptionally
difficult situations. The candidate
has served as a key resource and
advised others.

• Presents controversial workforce diversity findings
and recommendations to management.
• Testifies about the organization’s selection
procedures at administrative proceedings.
• Informs management of their misinterpretation of
the Americans with Disabilities Act and
recommends corrective action.

September 2008
U.S. Office of Personnel Management

31

Problem Solving: Identifies problems; determines accuracy and relevance of information; uses
sound judgment to generate and evaluate alternatives, and to make recommendations.

Proficiency
Rating
 (choose
only one)
Proficiency Level Definition
Proficiency Level Behavioral Examples for Typical
HR Positions

 1

The candidate can apply the
competency in the simplest
situations. The candidate requires
close and extensive guidance.
• Corrects simple problems with Health Benefits
Election forms.
• Identifies missing training forms from personnel
files.
• Reviews information justifying employee award
nominations for completeness.
 2

The candidate can apply the
competency in somewhat difficult
situations. The candidate will
require frequent guidance.

• Determines the appropriate changes to employees’
official personnel folders in cases of marriage or
divorce.
• Recommends options for an employee who has no
accrued annual or sick leave and is adopting a
child.
• Suggests review process for vacancy
announcements to improve accuracy and clarity.
 3

The candidate can apply the
competency in difficult situations.
The candidate may require
occasional guidance.

• Resolves classification issues by researching
precedent-setting case decisions.
• Analyzes relevant information to identify barriers
preventing participation in a mentoring program.
• Applies pay rules and regulations to resolve a pay-
setting dispute for a new employee.
 4

The candidate can apply the
competency in considerably
difficult situations. The candidate
requires no guidance.

• Integrates a variety of strategic hiring flexibilities
to address recruitment and retention problems.
• Identifies the immediate training needs of
employees to address customer complaints.
• Resolves union concerns about inconsistent
performance ratings across the organization by
implementing mandatory supervisory training.
 5

The candidate can apply the
competency in exceptionally
difficult situations. The candidate
has served as a key resource and
advised others.

• Analyzes and solves complex labor-management
disagreements involving vague and untested areas
of case law regarding working conditions.
• Resolves logistical problems associated with hiring
several thousand employees to meet a temporary
staffing need.
• Resolves projected shortages in critical occupations
by developing a comprehensive recruitment
program to include outreach, mentoring,
internships, and financial incentives.

September 2008
U.S. Office of Personnel Management

32

Interpersonal Skills: Shows understanding, friendliness, courtesy, tact, empathy, concern, and
politeness to others; develops and maintains effective relationships with others; may include
effectively dealing with individuals who are difficult, hostile, or distressed; relates well to people
from varied backgrounds and different situations; is sensitive to cultural diversity, race, gender,
disabilities, and other individual differences.

Proficiency
Rating
 (choose
only one)
Proficiency Level Definition
Proficiency Level Behavioral Examples for Typical
HR Positions

 1

The candidate can apply the
competency in the simplest
situations. The candidate requires
close and extensive guidance.
• Greets job applicants when they arrive for
interviews.
• Works with others in the HR office to organize
information materials for employee orientation
sessions.
 2

The candidate can apply the
competency in somewhat difficult
situations. The candidate will
require frequent guidance.

---

---

## RAG Chunk 014

<!-- source_type: methodology | category: case | pages: 34-36 | chunk_size_target: 900 | chunk_overlap_target: 120 | words: 554 -->

### 中文译文 / 中文检索层

附录提供了可直接转化为产品流程和后台配置的清单与表单。附录 A 是结构化面试实施清单，包含评估当前选拔情况、确定结构化面试在选拔流程中的位置、制定开发和实施计划、确保合规、制定沟通计划、建立开发团队、开发并实施面试、评估结果。附录 B 是开发清单，对应八个开发步骤。附录 C 提供有效和无效关键事件表单，用 Situation、Action、Outcome 帮助收集行为证据。附录 D 说明小组面试：小组可降低偏见风险，每位成员应独立观察、记录和评价，随后讨论并形成共识评分。后续附录还包括面试官培训课程样例、常见评分错误、个人评分表和小组评分表。

### Original English Text

Interpersonal Skills: Shows understanding, friendliness, courtesy, tact, empathy, concern, and
politeness to others; develops and maintains effective relationships with others; may include
effectively dealing with individuals who are difficult, hostile, or distressed; relates well to people
from varied backgrounds and different situations; is sensitive to cultural diversity, race, gender,
disabilities, and other individual differences.

Proficiency
Rating
 (choose
only one)
Proficiency Level Definition
Proficiency Level Behavioral Examples for Typical
HR Positions

 1

The candidate can apply the
competency in the simplest
situations. The candidate requires
close and extensive guidance.
• Greets job applicants when they arrive for
interviews.
• Works with others in the HR office to organize
information materials for employee orientation
sessions.
 2

The candidate can apply the
competency in somewhat difficult
situations. The candidate will
require frequent guidance.

• Offers to assist employees in resolving problems
with their benefits election.
• Works with other HR staff on a cross-functional
team to improve coordination of activities.
• Works with others to minimize disruptions to an
employee working under tight deadlines.
 3

The candidate can apply the
competency in difficult situations.
The candidate may require
occasional guidance.

• Restores a working relationship between angry co-
workers who have opposing views.
• Acts courteous and tactful when confronted by an
employee who is frustrated by a payroll problem.
• Establishes cooperative working relationships with
managers, so they are comfortable asking for advice
on HR issues.
 4

The candidate can apply the
competency in considerably
difficult situations. The candidate
requires no guidance.

• Facilitates an open forum to discuss employee
concerns regarding new compensation system.
• Maintains contact with stakeholder groups when
implementing new employee development program.
• Builds on the ideas of others to foster cooperation
during bargaining agreement negotiations.
• Identifies and emphasizes common goals to
promote cooperation between HR and line staff.
• Identifies and alleviates sources of stress among a
team developing a new automated HR system.
 5

The candidate can apply the
competency in exceptionally
difficult situations. The candidate
has served as a key resource and
advised others.

• Presents shortcomings of a newly installed HR
automation system in a tactful manner to irate
senior management officials.
• Explains the benefits of controversial policy
changes to upset individuals at a public hearing.
• Diffuses an emotionally charged meeting with
external stakeholders by expressing empathy for
their concerns.

September 2008
U.S. Office of Personnel Management

33

FINAL RATING

Candidate:_______________________________ Rater:_____________________________

General Competencies:

Proficiency Level
1. Writing

2. Oral Communication

3. Problem Solving

4. Interpersonal Skills

ACTION:

Highly Recommended for Position

Recommended for Position

Not Recommended for Position

Interviewer’s Signature:

Date:

September 2008
U.S. Office of Personnel Management

34

Appendix H: Sample Structured Interview
Group Rating Form

Candidate Name: _____________________________ Date of Interview: __________________

Instructions: Transfer each interviewer’s competency ratings onto this form. A consensus discussion
must occur with each panel member justifying his or her rating. Any changes to the individual ratings
during consensus discussion should be initialed by the panel members. A final group consensus rating
must be entered for each competency.

Panelists’ Individual Ratings

Competency

(1)

(2)

(3)

Consensus
Group Rating
Writing

Oral Communication

Problem Solving

Interpersonal Skills

COMMENTS:

Name of Panel Chairperson #1 :

N ame of Panel Member #2:

N ame of Panel Member #3:

September 2008
U.S. Office of Personnel Management

35

---


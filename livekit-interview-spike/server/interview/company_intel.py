from __future__ import annotations

import json
import re
from typing import Any

from interview.company_profiles import search_seed_company_profiles
from interview.models import CompanyIntelligenceCard
from local_providers import ConversationMessage, DeepSeekStreamingTextProvider


COMPANY_CARD_SYSTEM_PROMPT = """\
你是公司岗位级模拟面试的信息抽取器。只输出合法 JSON，不输出 Markdown。

你要从搜索材料中生成一张用于面试训练的公司情报卡。它不是百科页面，而是服务于：
1. 面试开场时让候选人用一两句话说明公司理解；
2. 把公司理解作为加分项；
3. 帮助后续岗位/JD 分析理解公司背景。

来源规则：
- official / authoritative 可以作为公司事实。
- job_board 不参与本步骤抽取；岗位职责、任职要求、JD 留到后续岗位分析步骤处理。
- weak_reference / unknown 只能作为弱参考，不能写成确定公司事实。
- 本步骤不要抽取财务、融资、营收、利润、岗位职责、任职要求。
- 不要在 roleRelevantPoints、interviewTalkingPoints、companyUnderstandingQuestions 中出现目标岗位名。
- 市场份额、排名等高风险信息，没有 official / authoritative 来源就留空或写“待核验”，不要编造。

输出 JSON 结构：
{
  "summary": "120字以内公司基本现状和简介，说明公司做什么、主要服务谁、核心特点是什么",
  "businessLines": ["业务线，尽量3-6条，具体到业务方向"],
  "productsOrServices": ["产品或服务，尽量4-8条，写具体产品/平台/服务名"],
  "marketPosition": ["行业位置或竞争环境，尽量2-5条，必须可被来源支持；不确定就写待核验"],
  "financialStrength": [],
  "recentContext": [],
  "cultureAndValues": ["企业特色/文化/价值观，尽量2-5条"],
  "roleRelevantPoints": ["面试注意点，尽量3-5条，只写公司理解加分项，不写岗位职责"],
  "interviewTalkingPoints": ["面试中谈公司理解时可准备的话题，尽量4-8条"],
  "companyUnderstandingQuestions": ["最多3个问题，每个问题一句话，围绕公司理解"],
  "sourceNotes": ["来源说明，格式尽量为：来源：URL 或 来源等级：说明"],
  "verificationStatus": "verified|partial|unverified",
  "confidence": 0.0
}
"""


async def build_company_card_from_source(
    *,
    company_name: str,
    target_role: str,
    source_text: str = "",
    business_line: str = "",
    source_note: str = "用户提供资料",
    source_url: str = "",
) -> CompanyIntelligenceCard:
    clean_source = source_text.strip()
    if not clean_source:
        return build_company_card(
            company_name=company_name,
            target_role=target_role,
            source_text=source_text,
            business_line=business_line,
            source_note=source_note,
            source_url=source_url,
        )

    provider = DeepSeekStreamingTextProvider()
    if not provider.api_key:
        return build_company_card(
            company_name=company_name,
            target_role=target_role,
            source_text=source_text,
            business_line=business_line,
            source_note=source_note,
            source_url=source_url,
        )

    clean_company = company_name.strip() or "目标公司"
    clean_role = target_role.strip() or "目标岗位"
    prompt = f"""
目标公司：{clean_company}
当前用户选择的岗位：{clean_role}（本步骤不要搜索或抽取该岗位 JD，仅用于措辞）
用户指定业务线：{business_line.strip() or "无"}
资料入口说明：{source_note}
资料入口 URL：{source_url or "无"}

搜索材料：
{clean_source[:18000]}

请按系统要求输出 JSON。
""".strip()
    try:
        raw = await provider.complete_reply(
            [ConversationMessage(role="user", text=prompt)],
            system_prompt=COMPANY_CARD_SYSTEM_PROMPT,
            temperature=0.0,
        )
        payload = _parse_json_object(raw)
        return _company_card_from_extracted_payload(
            payload,
            company_name=clean_company,
            target_role=clean_role,
            fallback_source_note=source_note,
            fallback_source_url=source_url,
            source_text=clean_source,
        )
    except Exception:
        return build_company_card(
            company_name=company_name,
            target_role=target_role,
            source_text=source_text,
            business_line=business_line,
            source_note=source_note,
            source_url=source_url,
        )


def build_company_card(
    *,
    company_name: str,
    target_role: str,
    source_text: str = "",
    business_line: str = "",
    source_note: str = "用户提供资料",
    source_url: str = "",
) -> CompanyIntelligenceCard:
    clean_company = company_name.strip() or "目标公司"
    clean_role = target_role.strip() or "目标岗位"
    clean_source = source_text.strip()
    clean_business_line = business_line.strip()

    if clean_source:
        snippets = _important_sentences(clean_source)
        role_points = _company_attention_points(clean_company, clean_source)
        talking_points = snippets[:3] or (f"结合资料说明你为什么关注{clean_company}。",)
        questions = (
            f"请用一两句话说明你对{clean_company}基本业务和企业特色的理解。",
            "你觉得这家公司最值得在面试中主动提到的一点是什么？",
        )
        return CompanyIntelligenceCard(
            company_name=clean_company,
            target_role=clean_role,
            summary=snippets[0] if snippets else f"已读取用户提供的{clean_company}相关资料。",
            business_lines=tuple(_dedupe((clean_business_line, *_keyword_lines(clean_source, ("业务", "产品", "服务", "平台"))))),
            products_or_services=tuple(_dedupe(_keyword_lines(clean_source, ("产品", "服务", "平台", "解决方案")))),
            market_position=tuple(_dedupe(_keyword_lines(clean_source, ("行业", "市场", "领先", "排名", "份额", "生态", "竞争")))),
            financial_strength=(),
            recent_context=(),
            culture_and_values=tuple(_dedupe(_keyword_lines(clean_source, ("价值观", "文化", "使命", "愿景")))),
            role_relevant_points=tuple(role_points),
            interview_talking_points=tuple(talking_points),
            company_understanding_questions=questions,
            source_notes=tuple(note for note in (source_note, f"来源：{source_url}" if source_url else "") if note),
            verification_status="partial",
            confidence=0.68,
        )

    summary = (
        f"当前仅知道目标公司为{clean_company}，岗位方向为{clean_role}。"
        "系统不会把无来源信息当作事实，需要用户后续补充官网、招聘页或公司介绍资料。"
    )
    business_lines = (clean_business_line,) if clean_business_line else ()
    return CompanyIntelligenceCard(
        company_name=clean_company,
        target_role=clean_role,
        summary=summary,
        business_lines=business_lines,
        role_relevant_points=(
            f"准备说明你为什么关注{clean_company}。",
            f"准备说明{clean_role}能为公司业务带来什么贡献。",
            "准备把自己的项目经历和目标岗位职责连接起来。",
        ),
        interview_talking_points=(
            "公司业务理解",
            "岗位匹配动机",
            "个人经历和岗位能力的连接",
        ),
        company_understanding_questions=(
            f"你目前对{clean_company}和{clean_role}岗位有什么理解？如果资料还没核验，也可以先说你的准备思路。",
        ),
        source_notes=("未提供可核验来源，当前为待核验准备卡",),
        verification_status="unverified",
        confidence=0.2,
    )


def search_company_profiles_payload(query: str) -> list[dict[str, object]]:
    return [
        {
            "id": profile.id,
            "name": profile.name,
            "summary": profile.summary,
            "businessLines": list(profile.business_lines),
            "sourceNotes": list(profile.source_notes),
            "sourceUrls": list(profile.source_urls),
        }
        for profile in search_seed_company_profiles(query)
    ]


def company_card_to_payload(card: CompanyIntelligenceCard) -> dict[str, object]:
    return {
        "companyName": card.company_name,
        "targetRole": card.target_role,
        "summary": card.summary,
        "businessLines": list(card.business_lines),
        "productsOrServices": list(card.products_or_services),
        "marketPosition": list(card.market_position),
        "financialStrength": list(card.financial_strength),
        "recentContext": list(card.recent_context),
        "cultureAndValues": list(card.culture_and_values),
        "roleRelevantPoints": list(card.role_relevant_points),
        "interviewTalkingPoints": list(card.interview_talking_points),
        "companyUnderstandingQuestions": list(card.company_understanding_questions),
        "sourceNotes": list(card.source_notes),
        "sourceUrls": [note.removeprefix("来源：") for note in card.source_notes if note.startswith("来源：")],
        "verificationStatus": card.verification_status,
        "confidence": card.confidence,
    }


def company_card_from_payload(payload: object, *, fallback_role: str) -> CompanyIntelligenceCard | None:
    if not isinstance(payload, dict):
        return None
    company_name = str(payload.get("companyName") or payload.get("company_name") or "").strip()
    if not company_name:
        return None
    return CompanyIntelligenceCard(
        company_name=company_name,
        target_role=str(payload.get("targetRole") or payload.get("target_role") or fallback_role),
        summary=str(payload.get("summary") or ""),
        business_lines=tuple(_as_str_list(payload.get("businessLines"))),
        products_or_services=tuple(_as_str_list(payload.get("productsOrServices"))),
        market_position=tuple(_as_str_list(payload.get("marketPosition"))),
        financial_strength=tuple(_as_str_list(payload.get("financialStrength"))),
        recent_context=tuple(_as_str_list(payload.get("recentContext"))),
        culture_and_values=tuple(_as_str_list(payload.get("cultureAndValues"))),
        role_relevant_points=tuple(_as_str_list(payload.get("roleRelevantPoints"))),
        interview_talking_points=tuple(_as_str_list(payload.get("interviewTalkingPoints"))),
        company_understanding_questions=tuple(_as_str_list(payload.get("companyUnderstandingQuestions"))),
        source_notes=tuple(_as_str_list(payload.get("sourceNotes"))),
        verification_status=str(payload.get("verificationStatus") or "unverified"),
        confidence=float(payload.get("confidence") or 0.2),
    )


def _company_card_from_extracted_payload(
    payload: dict[str, Any],
    *,
    company_name: str,
    target_role: str,
    fallback_source_note: str,
    fallback_source_url: str,
    source_text: str,
) -> CompanyIntelligenceCard:
    source_notes = tuple(_as_str_list(payload.get("sourceNotes"), limit=8))
    if fallback_source_url and not any(fallback_source_url in note for note in source_notes):
        source_notes = (*source_notes, f"来源：{fallback_source_url}")
    if not source_notes:
        source_notes = (fallback_source_note,)

    verification_status = str(payload.get("verificationStatus") or "partial")
    if verification_status not in {"verified", "partial", "unverified"}:
        verification_status = "partial"
    confidence = _bounded_float(payload.get("confidence"), default=0.62)

    has_strong_source = "来源等级：official" in source_text or "来源等级：authoritative" in source_text
    has_any_source = "来源等级：" in source_text
    if not has_strong_source and verification_status == "verified":
        verification_status = "partial"
    if not has_strong_source:
        confidence = min(confidence, 0.64)
    if not has_any_source:
        verification_status = "unverified"
        confidence = min(confidence, 0.3)

    forbidden_terms = (target_role, "岗位", "职责", "任职", "JD", "简历匹配")
    questions = tuple(_filter_company_only_items(
        _as_str_list(payload.get("companyUnderstandingQuestions"), limit=6),
        forbidden_terms=forbidden_terms,
        limit=3,
    ))
    if not questions:
        questions = (f"请用一两句话说明你对{company_name}基本业务和企业特色的理解。",)

    role_points = tuple(_filter_company_only_items(
        _as_str_list(payload.get("roleRelevantPoints"), limit=10),
        forbidden_terms=forbidden_terms,
        limit=6,
    ))
    if not role_points:
        role_points = (
            f"准备说明你为什么关注{company_name}。",
            "准备用一两句话连接公司业务、用户价值和个人兴趣。",
        )

    talking_points = tuple(_filter_company_only_items(
        _as_str_list(payload.get("interviewTalkingPoints"), limit=12),
        forbidden_terms=forbidden_terms,
        limit=8,
    ))
    return CompanyIntelligenceCard(
        company_name=company_name,
        target_role=target_role,
        summary=str(payload.get("summary") or f"已基于可检索资料生成{company_name}公司准备卡。")[:260],
        business_lines=tuple(_as_str_list(payload.get("businessLines"), limit=8)),
        products_or_services=tuple(_as_str_list(payload.get("productsOrServices"), limit=10)),
        market_position=tuple(_as_str_list(payload.get("marketPosition"), limit=6)),
        financial_strength=(),
        recent_context=(),
        culture_and_values=tuple(_as_str_list(payload.get("cultureAndValues"), limit=8)),
        role_relevant_points=role_points,
        interview_talking_points=talking_points or role_points[:4],
        company_understanding_questions=questions,
        source_notes=source_notes,
        verification_status=verification_status,
        confidence=confidence,
    )


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.S)
    if match:
        cleaned = match.group(0)
    payload = json.loads(cleaned)
    return payload if isinstance(payload, dict) else {}


def _bounded_float(value: object, *, default: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _filter_company_only_items(
    items: list[str],
    *,
    forbidden_terms: tuple[str, ...],
    limit: int,
) -> list[str]:
    result: list[str] = []
    for item in items:
        if any(term and term in item for term in forbidden_terms):
            continue
        result.append(item)
        if len(result) >= limit:
            break
    return result


def _important_sentences(text: str) -> tuple[str, ...]:
    parts = re.split(r"[。！？\n\r]+", text)
    cleaned = [part.strip(" ，,：:；;") for part in parts if len(part.strip()) >= 10]
    return tuple(cleaned[:6])


def _keyword_lines(text: str, keywords: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(line for line in _important_sentences(text) if any(keyword in line for keyword in keywords))[:4]


def _role_points_from_source(role: str, source_text: str) -> tuple[str, ...]:
    points = _keyword_lines(source_text, ("岗位", "职责", "要求", "能力", role))
    if points:
        return points[:4]
    return (
        f"结合资料说明{role}岗位的核心职责。",
        f"说明自己的经历如何匹配{role}岗位。",
    )


def _company_attention_points(company_name: str, source_text: str) -> tuple[str, ...]:
    points = _keyword_lines(source_text, ("业务", "产品", "服务", "用户", "文化", "价值观", "生态", "行业"))
    if points:
        return points[:4]
    return (
        f"准备说明你为什么关注{company_name}。",
        "准备用一两句话连接公司业务、用户价值和个人兴趣。",
    )


def _dedupe(items: tuple[str, ...]) -> list[str]:
    result: list[str] = []
    for item in items:
        clean = item.strip()
        if clean and clean not in result:
            result.append(clean)
    return result


def _as_str_list(value: object, *, limit: int | None = None) -> list[str]:
    if not isinstance(value, list):
        return []
    items = [str(item).strip() for item in value if str(item).strip()]
    return items[:limit] if limit is not None else items

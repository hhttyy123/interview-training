from __future__ import annotations

import asyncio

from interview.company_search import CompanySearchResult, search_company_web
from interview.company_web import fetch_company_source_text


async def research_company_source_text(
    *,
    company_name: str,
    target_role: str,
    max_pages: int = 5,
) -> tuple[str, list[str]]:
    results = await search_company_web(company_name=company_name, target_role=target_role, limit=15)
    if not results:
        return "", []

    source_chunks = [_result_to_text(result) for result in results]
    fetched_pages = await _fetch_result_pages(results[:max_pages])
    for result, text in fetched_pages:
        if text:
            source_chunks.append(
                f"来源页面：{result.title}\n"
                f"URL：{result.url}\n"
                f"用途分类：{result.category}\n"
                f"来源等级：{result.source_tier}\n"
                f"正文摘要：\n{text[:3600]}"
            )

    urls = []
    for result in results:
        if result.url not in urls:
            urls.append(result.url)
    return "\n\n".join(source_chunks), urls


async def _fetch_result_pages(results: list[CompanySearchResult]) -> list[tuple[CompanySearchResult, str]]:
    tasks = [asyncio.create_task(_safe_fetch(result)) for result in results]
    return await asyncio.gather(*tasks)


async def _safe_fetch(result: CompanySearchResult) -> tuple[CompanySearchResult, str]:
    if result.raw_content.strip():
        return result, result.raw_content
    try:
        return result, await fetch_company_source_text(result.url)
    except Exception:
        return result, ""


def _result_to_text(result: CompanySearchResult) -> str:
    return (
        f"搜索结果：{result.title}\n"
        f"URL：{result.url}\n"
        f"用途分类：{result.category}\n"
        f"来源等级：{result.source_tier}\n"
        f"摘要：{result.snippet}\n"
        f"来源：{result.source}"
    )

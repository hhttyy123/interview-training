from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from interview.company_profiles import seed_company_profile_by_query


@dataclass(frozen=True)
class CompanySearchResult:
    title: str
    url: str
    snippet: str
    source: str
    raw_content: str = ""
    category: str = "general"
    source_tier: str = "unknown"


async def search_company_web(*, company_name: str, target_role: str, limit: int = 5) -> list[CompanySearchResult]:
    provider = os.getenv("COMPANY_SEARCH_PROVIDER", "brave").strip().lower()
    if provider == "tavily":
        include_domains = _official_domains_for_company(company_name)
        query = _tavily_company_query(company_name=company_name)
        return await _search_tavily(query=query, limit=limit, include_domains=include_domains)
    query = f"{company_name} 公司介绍 官网 业务 产品 价值观 企业文化 行业位置"
    if provider == "bocha":
        return await _search_bocha_company(company_name=company_name, limit=limit)
    if provider == "serper":
        return await _search_serper(query=query, limit=limit)
    if provider == "brave":
        return await _search_brave(query=query, limit=limit)
    return []


def _tavily_company_query(*, company_name: str) -> str:
    aliases: list[str] = []
    profile = seed_company_profile_by_query(company_name)
    if profile:
        aliases = [alias for alias in profile.aliases if alias.isascii()][:2]
    alias_text = " ".join(aliases)
    return f"{company_name} {alias_text} official website business products culture company overview".strip()


def _official_domains_for_company(company_name: str) -> list[str]:
    profile = seed_company_profile_by_query(company_name)
    if not profile:
        return []
    domains: list[str] = []
    for source_url in profile.source_urls:
        host = urlparse(source_url).hostname or ""
        if host and host not in domains:
            domains.append(host)
    return domains


async def _search_tavily(*, query: str, limit: int, include_domains: list[str] | None = None) -> list[CompanySearchResult]:
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return []

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "query": query,
        "topic": "general",
        "search_depth": "advanced",
        "max_results": min(max(limit, 1), 10),
        "chunks_per_source": 3,
        "include_answer": False,
        "include_images": False,
        "include_raw_content": True,
    }
    if include_domains:
        body["include_domains"] = include_domains
    timeout = httpx.Timeout(connect=8.0, read=25.0, write=5.0, pool=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post("https://api.tavily.com/search", headers=headers, json=body)
        response.raise_for_status()
    payload = response.json()
    raw_results = payload.get("results", [])
    return [
        CompanySearchResult(
            title=str(item.get("title") or ""),
            url=str(item.get("url") or ""),
            snippet=str(item.get("content") or ""),
            source="tavily",
            raw_content=str(item.get("raw_content") or ""),
        )
        for item in raw_results
        if _is_public_url(str(item.get("url") or ""))
    ][:limit]


async def _search_bocha(
    *,
    query: str,
    limit: int,
    category: str = "general",
    company_name: str = "",
) -> list[CompanySearchResult]:
    api_key = os.getenv("BOCHA_API_KEY", "").strip()
    if not api_key:
        return []

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "query": query,
        "summary": True,
        "count": min(max(limit, 1), 10),
        "page": 1,
    }
    timeout = httpx.Timeout(connect=8.0, read=25.0, write=5.0, pool=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post("https://api.bochaai.com/v1/web-search", headers=headers, json=body)
        response.raise_for_status()
    payload = response.json()
    raw_results = payload.get("data", {}).get("webPages", {}).get("value", [])
    results: list[CompanySearchResult] = []
    for item in raw_results:
        url = str(item.get("url") or "")
        if not _is_public_url(url):
            continue
        title = str(item.get("name") or "")
        tier = _source_tier(url=url, title=title, company_name=company_name)
        if tier == "blocked":
            continue
        results.append(
            CompanySearchResult(
                title=title,
                url=url,
                snippet=str(item.get("snippet") or item.get("summary") or ""),
                source="bocha",
                raw_content=str(item.get("summary") or item.get("snippet") or ""),
                category=category,
                source_tier=tier,
            )
        )
        if len(results) >= limit:
            break
    return results


async def _search_bocha_company(*, company_name: str, limit: int) -> list[CompanySearchResult]:
    queries = (
        ("company_profile", f"{company_name} 官网 关于我们 公司介绍 基本现状 发展历程"),
        ("business_products", f"{company_name} 业务线 产品 服务 平台 用户场景"),
        ("market_position", f"{company_name} 行业位置 竞争优势 平台生态 用户规模"),
        ("company_culture", f"{company_name} 企业文化 价值观 使命 愿景 企业特色"),
        ("interview_notes", f"{company_name} 面试 公司理解 注意点 业务特色 文化特色"),
    )
    results: list[CompanySearchResult] = []
    seen_urls: set[str] = set()
    per_query_limit = min(max(limit, 1), 4)
    for category, query in queries:
        for result in await _search_bocha(
            query=query,
            limit=per_query_limit,
            category=category,
            company_name=company_name,
        ):
            if result.url in seen_urls:
                continue
            seen_urls.add(result.url)
            results.append(result)
    return results[:limit]


async def _search_brave(*, query: str, limit: int) -> list[CompanySearchResult]:
    api_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
    if not api_key:
        return []

    headers = {
        "X-Subscription-Token": api_key,
        "Accept": "application/json",
    }
    params = {
        "q": query,
        "count": min(max(limit, 1), 10),
        "country": "cn",
        "search_lang": "zh-hans",
    }
    timeout = httpx.Timeout(connect=8.0, read=15.0, write=5.0, pool=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get("https://api.search.brave.com/res/v1/web/search", headers=headers, params=params)
        response.raise_for_status()
    payload = response.json()
    raw_results = payload.get("web", {}).get("results", [])
    return [
        CompanySearchResult(
            title=str(item.get("title") or ""),
            url=str(item.get("url") or ""),
            snippet=str(item.get("description") or ""),
            source="brave",
        )
        for item in raw_results
        if _is_public_url(str(item.get("url") or ""))
    ][:limit]


async def _search_serper(*, query: str, limit: int) -> list[CompanySearchResult]:
    api_key = os.getenv("SERPER_API_KEY", "").strip()
    if not api_key:
        return []

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    body = {
        "q": query,
        "num": min(max(limit, 1), 10),
        "hl": "zh-cn",
        "gl": "cn",
    }
    timeout = httpx.Timeout(connect=8.0, read=15.0, write=5.0, pool=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post("https://google.serper.dev/search", headers=headers, json=body)
        response.raise_for_status()
    payload = response.json()
    raw_results = payload.get("organic", [])
    return [
        CompanySearchResult(
            title=str(item.get("title") or ""),
            url=str(item.get("link") or ""),
            snippet=str(item.get("snippet") or ""),
            source="serper",
        )
        for item in raw_results
        if _is_public_url(str(item.get("link") or ""))
    ][:limit]


def _is_public_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    host = (parsed.hostname or "").lower()
    blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
    if host in blocked_hosts or host.endswith(".local"):
        return False
    return True


def _source_tier(*, url: str, title: str, company_name: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    title_lower = title.lower()
    if not host:
        return "blocked"

    official_domains = _official_domains_for_company(company_name)
    if any(_host_matches_domain(host, domain) for domain in official_domains):
        return "official"

    authoritative_hosts = (
        "sse.com.cn",
        "szse.cn",
        "hkexnews.hk",
        "eastmoney.com",
        "yicai.com",
        "caixin.com",
        "36kr.com",
        "latepost.com",
        "stcn.com",
        "cls.cn",
    )
    if any(host == item or host.endswith(f".{item}") for item in authoritative_hosts):
        return "authoritative"

    job_board_hosts = (
        "zhipin.com",
        "nowcoder.com",
        "wondercv.com",
        "lagou.com",
        "liepin.com",
        "51job.com",
        "zhaopin.com",
        "yingjiesheng.com",
        "kanzhun.com",
    )
    if any(host == item or host.endswith(f".{item}") for item in job_board_hosts):
        return "job_board"

    weak_hosts = (
        "zhihu.com",
        "csdn.net",
        "book118.com",
        "docin.com",
        "wenku.baidu.com",
        "jinchutou.com",
        "xuehi.cn",
        "zsdocx.com",
        "mbalib.com",
        "baike.baidu.com",
    )
    if any(host == item or host.endswith(f".{item}") for item in weak_hosts):
        return "weak_reference"

    blocked_title_words = ("模板", "范文", "ppt", "pptx", "文库", "试题", "答案")
    if any(word in title_lower for word in blocked_title_words):
        return "blocked"

    return "unknown"


def _host_matches_domain(host: str, domain: str) -> bool:
    clean = domain.lower().removeprefix("www.")
    return host == clean or host.endswith(f".{clean}") or host == domain.lower()

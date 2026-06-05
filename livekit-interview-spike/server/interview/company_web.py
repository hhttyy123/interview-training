from __future__ import annotations

import html
import ipaddress
import re
from urllib.parse import urlparse

import httpx


MAX_SOURCE_CHARS = 8000


async def fetch_company_source_text(url: str) -> str:
    clean_url = url.strip()
    parsed = urlparse(clean_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("只支持 http/https 公司资料链接")
    _assert_public_host(parsed.hostname or "")

    timeout = httpx.Timeout(connect=8.0, read=15.0, write=5.0, pool=5.0)
    headers = {
        "User-Agent": "InterviewTrainingCompanyResearch/1.0",
        "Accept": "text/html,application/xhtml+xml,text/plain",
    }
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
        response = await client.get(clean_url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "text" not in content_type and "html" not in content_type:
            raise ValueError(f"不支持的资料类型：{content_type or 'unknown'}")
        return extract_readable_text(response.text)


def extract_readable_text(raw: str) -> str:
    text = re.sub(r"(?is)<(script|style|noscript|svg|canvas|iframe).*?>.*?</\1>", " ", raw)
    text = re.sub(r"(?is)<(nav|footer|header|aside).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</(p|div|section|article|li|h1|h2|h3)>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) >= 8]
    return "\n".join(lines)[:MAX_SOURCE_CHARS]


def _assert_public_host(host: str) -> None:
    clean_host = host.strip().lower()
    if not clean_host or clean_host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"} or clean_host.endswith(".local"):
        raise ValueError("不允许抓取本机或内网地址")
    try:
        ip = ipaddress.ip_address(clean_host)
    except ValueError:
        return
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        raise ValueError("不允许抓取本机或内网地址")

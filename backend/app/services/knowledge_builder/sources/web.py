import httpx
from dataclasses import dataclass
from app.config import get_settings

settings = get_settings()

PRIORITY_DOMAINS = [
    "autozone.com",
    "1aauto.com",
    "oreillyauto.com",
    "2carpros.com",
    "wikihow.com",
]


@dataclass
class WebSource:
    url: str
    title: str
    content: str
    domain: str
    is_priority: bool = False


async def search_repair_guides(make: str, model: str, year: int, repair: str) -> list[WebSource]:
    if not settings.tavily_api_key:
        return []

    query = f"{year} {make} {model} {repair} step by step guide"
    results = await _tavily_search(query)
    return results


async def _tavily_search(query: str) -> list[WebSource]:
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "advanced",
        "include_answer": False,
        "max_results": 8,
        "include_domains": PRIORITY_DOMAINS,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            return []
        data = resp.json()

    sources = []
    for item in data.get("results", []):
        domain = _extract_domain(item.get("url", ""))
        sources.append(WebSource(
            url=item.get("url", ""),
            title=item.get("title", ""),
            content=item.get("content", "")[:3000],
            domain=domain,
            is_priority=domain in PRIORITY_DOMAINS,
        ))

    sources.sort(key=lambda x: (x.is_priority, len(x.content)), reverse=True)
    return sources


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""

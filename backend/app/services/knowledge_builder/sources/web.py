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
    # Australian sources
    "repco.com.au",
    "supercheapauto.com.au",
    "4wdaction.com.au",
    "toyota.com.au",
    "ford.com.au",
    "isuzu.com.au",
    "mynrma.com.au",
    "carsales.com.au",
]

# Vehicles not sold in the US — search needs Australian context or results are poor
_AU_ONLY_MAKES_MODELS = {
    ("toyota", "hilux"),
    ("toyota", "landcruiser"),
    ("holden", "commodore"),
    ("holden", "colorado"),
    ("holden", "colorado"),
    ("isuzu", "d-max"),
    ("mitsubishi", "triton"),
    ("nissan", "navara"),
}


@dataclass
class WebSource:
    url: str
    title: str
    content: str
    domain: str
    is_priority: bool = False


def _is_au_vehicle(make: str, model: str) -> bool:
    return (make.lower(), model.lower().replace(" ", "-")) in _AU_ONLY_MAKES_MODELS or \
           (make.lower(), model.lower()) in _AU_ONLY_MAKES_MODELS


async def search_repair_guides(make: str, model: str, year: int, repair: str) -> list[WebSource]:
    if not settings.tavily_api_key:
        return []

    geo = "Australia" if _is_au_vehicle(make, model) else ""
    geo_suffix = f" {geo}" if geo else ""
    query = f"{year} {make} {model} {repair} step by step guide{geo_suffix}"
    results = await _tavily_search(query, au_vehicle=bool(geo))
    return results


_AU_DOMAINS = [
    "repco.com.au", "supercheapauto.com.au", "4wdaction.com.au",
    "toyota.com.au", "ford.com.au", "isuzu.com.au", "mynrma.com.au",
]
_GLOBAL_DOMAINS = ["autozone.com", "1aauto.com", "oreillyauto.com", "2carpros.com", "wikihow.com"]


async def _tavily_search(query: str, au_vehicle: bool = False) -> list[WebSource]:
    url = "https://api.tavily.com/search"
    # For AU-only vehicles use AU sources first; global sources as fallback
    domains = (_AU_DOMAINS + _GLOBAL_DOMAINS) if au_vehicle else _GLOBAL_DOMAINS
    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "advanced",
        "include_answer": False,
        "max_results": 8,
        "include_domains": domains,
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

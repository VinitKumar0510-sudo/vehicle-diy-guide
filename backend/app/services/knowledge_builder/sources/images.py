import httpx
from dataclasses import dataclass
from app.config import get_settings

settings = get_settings()


@dataclass
class StepImage:
    url: str
    source: str  # "youtube" | "web"
    caption: str


def youtube_thumbnail(video_id: str) -> str:
    return f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"


async def fetch_step_images(
    make: str,
    model: str,
    year: int,
    repair: str,
    step_title: str,
    video_ids: list[str],
) -> list[StepImage]:
    images = []

    # YouTube thumbnails from videos we already have — free, no API needed
    for vid_id in video_ids[:2]:
        images.append(StepImage(
            url=youtube_thumbnail(vid_id),
            source="youtube",
            caption=f"{year} {make} {model} — {repair}",
        ))

    # Tavily image search for step-specific diagram/photo
    if settings.tavily_api_key:
        query = f"{year} {make} {model} {step_title} repair diagram"
        tavily_images = await _tavily_image_search(query)
        images.extend(tavily_images)

    return images[:3]


async def _tavily_image_search(query: str) -> list[StepImage]:
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "basic",
        "include_images": True,
        "max_results": 3,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                return []
            data = resp.json()
        return [
            StepImage(url=img, source="web", caption=query)
            for img in data.get("images", [])[:3]
            if img.startswith("http")
        ]
    except Exception:
        return []

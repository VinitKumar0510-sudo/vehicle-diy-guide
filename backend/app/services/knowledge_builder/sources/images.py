import httpx
from dataclasses import dataclass
from app.config import get_settings

settings = get_settings()

# Domains that return product/parts images, not repair photos
JUNK_DOMAINS = [
    "revolutionparts", "rockauto", "amazon", "ebay",
    "autopartswarehouse", "partsgeek", "carparts.com",
    "walmart", "carid.com", "oreillyauto.com/shop",
]


@dataclass
class StepImage:
    url: str
    source: str  # "youtube_embed" | "web"
    caption: str
    video_id: str | None = None  # set for youtube embeds


def youtube_embed_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


async def fetch_step_images(
    make: str,
    model: str,
    year: int,
    repair: str,
    step_title: str,
    video_ids: list[str],
) -> list[StepImage]:
    images = []

    # Embed the most relevant YouTube video (one per guide, not per step)
    # User can watch + scrub to find the relevant moment
    if video_ids:
        images.append(StepImage(
            url=youtube_embed_url(video_ids[0]),
            source="youtube_embed",
            caption=f"{year} {make} {model} — {repair}",
            video_id=video_ids[0],
        ))

    # Action-focused image search — what the step LOOKS like, not the part
    if settings.tavily_api_key:
        action = _extract_action(step_title)
        query = f"how to {action} {repair} step by step photo"
        tavily_images = await _tavily_image_search(query)
        images.extend(tavily_images)

    return images[:3]


def _extract_action(step_title: str) -> str:
    action_words = ["remove", "install", "replace", "compress", "torque",
                    "inspect", "clean", "attach", "disconnect", "apply"]
    title_lower = step_title.lower()
    for word in action_words:
        if word in title_lower:
            idx = title_lower.index(word)
            return step_title[idx:idx + 40]
    return step_title[:40]


async def _tavily_image_search(query: str) -> list[StepImage]:
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "basic",
        "include_images": True,
        "max_results": 5,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                return []
            data = resp.json()

        filtered = [
            img for img in data.get("images", [])
            if img.startswith("http")
            and not any(junk in img.lower() for junk in JUNK_DOMAINS)
            and any(img.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"])
        ]
        return [
            StepImage(url=img, source="web", caption=query)
            for img in filtered[:2]
        ]
    except Exception:
        return []

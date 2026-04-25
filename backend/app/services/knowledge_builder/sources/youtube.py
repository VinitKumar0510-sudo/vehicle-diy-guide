import httpx
from youtube_transcript_api import YouTubeTranscriptApi
from dataclasses import dataclass
from typing import Optional
from app.config import get_settings

settings = get_settings()

TRUSTED_CHANNELS = {
    "UCes1EvRjcKU4sY_UZxFAZHg": "ChrisFix",
    "UC8uT9cgJorJPWu7ITLGo9Ww": "EricTheCarGuy",
    "UCoBizBWfuoQ0NJdABz56sog": "1A Auto",
    "UCuxpxCCevIlF-k-K5YU8XPA": "Scotty Kilmer",
}


@dataclass
class VideoSource:
    video_id: str
    title: str
    channel: str
    transcript: str
    url: str
    relevance_score: float = 0.0


async def search_repair_videos(make: str, model: str, year: int, repair: str) -> list[VideoSource]:
    query = f"{year} {make} {model} {repair} DIY how to"
    video_ids = await _search_youtube(query)
    results = []
    for vid_id, title, channel in video_ids:
        transcript = _fetch_transcript(vid_id)
        if not transcript:
            continue
        results.append(VideoSource(
            video_id=vid_id,
            title=title,
            channel=channel,
            transcript=transcript,
            url=f"https://youtube.com/watch?v={vid_id}",
            relevance_score=_score_video(title, channel, make, model, year, repair),
        ))
    results.sort(key=lambda x: x.relevance_score, reverse=True)
    return results[:5]


async def _search_youtube(query: str) -> list[tuple[str, str, str]]:
    if not settings.youtube_api_key:
        return []

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": 10,
        "key": settings.youtube_api_key,
        "videoDuration": "medium",
        "relevanceLanguage": "en",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return []
        data = resp.json()

    results = []
    for item in data.get("items", []):
        try:
            vid_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel = item["snippet"]["channelTitle"]
            results.append((vid_id, title, channel))
        except (KeyError, TypeError):
            continue
    return results


def _fetch_transcript(video_id: str) -> Optional[str]:
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id)
        return " ".join(s.text for s in transcript)
    except Exception:
        return None


def _score_video(title: str, channel: str, make: str, model: str, year: int, repair: str) -> float:
    title_lower = title.lower()
    score = 0.0
    if make.lower() in title_lower:
        score += 0.3
    if model.lower() in title_lower:
        score += 0.3
    if str(year) in title_lower:
        score += 0.2
    if any(word in title_lower for word in repair.lower().split()):
        score += 0.2
    if channel in TRUSTED_CHANNELS.values():
        score += 0.3
    return min(score, 1.0)

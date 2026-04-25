import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional
from app.config import get_settings

settings = get_settings()

REPAIR_SUBREDDITS = [
    "MechanicAdvice",
    "DIYAuto",
    "AskMechanics",
]

MAKE_SUBREDDITS = {
    "toyota": ["ToyotaTacoma", "Camry", "4Runner", "Corolla"],
    "honda": ["hondacivic", "accord", "crv"],
    "ford": ["f150", "Mustang", "FordTruck"],
    "chevrolet": ["Silverado", "Camaro"],
    "subaru": ["WRX", "subaru"],
    "jeep": ["Jeep", "JeepWrangler"],
}


@dataclass
class RedditPost:
    title: str
    body: str
    top_comments: list[str]
    url: str
    score: int
    subreddit: str


async def fetch_repair_posts(make: str, model: str, year: int, repair: str) -> list[RedditPost]:
    try:
        import praw
    except ImportError:
        return []

    if not settings.reddit_client_id or not settings.reddit_client_secret:
        return []

    def _fetch_sync():
        import praw
        reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
        subreddits = REPAIR_SUBREDDITS.copy()
        make_subs = MAKE_SUBREDDITS.get(make.lower(), [])
        subreddits.extend(make_subs)
        query = f"{year} {make} {model} {repair}"
        posts = []
        for sub_name in subreddits[:4]:
            try:
                sub = reddit.subreddit(sub_name)
                for submission in sub.search(query, limit=3, sort="relevance"):
                    if submission.score < 5:
                        continue
                    submission.comments.replace_more(limit=0)
                    top_comments = [
                        c.body for c in submission.comments[:5]
                        if hasattr(c, "body") and len(c.body) > 50
                    ]
                    posts.append(RedditPost(
                        title=submission.title,
                        body=submission.selftext[:2000],
                        top_comments=top_comments[:3],
                        url=f"https://reddit.com{submission.permalink}",
                        score=submission.score,
                        subreddit=sub_name,
                    ))
            except Exception:
                continue
        posts.sort(key=lambda x: x.score, reverse=True)
        return posts[:8]

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as pool:
        results = await loop.run_in_executor(pool, _fetch_sync)
    return results

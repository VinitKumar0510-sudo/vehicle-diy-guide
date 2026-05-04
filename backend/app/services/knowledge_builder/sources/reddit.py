import httpx
from dataclasses import dataclass

REPAIR_SUBREDDITS = [
    "MechanicAdvice",
    "DIYAuto",
    "AskMechanics",
    "mechanicadvice",
]

MAKE_SUBREDDITS = {
    "toyota":      ["LandCruiser", "4Runner", "Corolla", "ToyotaTacoma"],
    "ford":        ["f150", "FordTruck", "fordranger"],
    "holden":      ["Holden", "AussieMechanics"],
    "isuzu":       ["IsuzuDmax", "AussieMechanics"],
    "mitsubishi":  ["mitsubishi", "AussieMechanics"],
    "nissan":      ["nissanfrontier", "AussieMechanics"],
    "mazda":       ["mazda", "mazdacx5"],
    "hyundai":     ["Hyundai"],
    "kia":         ["kia"],
    "subaru":      ["subaru", "WRX"],
    "volkswagen":  ["Volkswagen"],
    "honda":       ["hondacivic", "accord"],
}

# AU-specific vehicles always get AussieMechanics added
_AU_MAKES = {"toyota", "holden", "isuzu", "mitsubishi", "nissan", "ford"}

HEADERS = {
    "User-Agent": "VehicleDIYGuide/1.0 (repair guide aggregator; read-only)",
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
    query = f"{year} {make} {model} {repair}"
    subreddits = _build_subreddit_list(make)

    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
        tasks = [_search_subreddit(client, sub, query) for sub in subreddits]
        import asyncio
        results = await asyncio.gather(*tasks, return_exceptions=True)

    posts: list[RedditPost] = []
    for batch in results:
        if isinstance(batch, list):
            posts.extend(batch)

    seen = set()
    unique = []
    for p in posts:
        if p.url not in seen:
            seen.add(p.url)
            unique.append(p)

    unique.sort(key=lambda x: x.score, reverse=True)
    return unique[:8]


def _build_subreddit_list(make: str) -> list[str]:
    subs = REPAIR_SUBREDDITS.copy()
    subs.extend(MAKE_SUBREDDITS.get(make.lower(), []))
    if make.lower() in _AU_MAKES and "AussieMechanics" not in subs:
        subs.append("AussieMechanics")
    # deduplicate preserving order
    seen = set()
    out = []
    for s in subs:
        if s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out[:5]


async def _search_subreddit(client: httpx.AsyncClient, subreddit: str, query: str) -> list[RedditPost]:
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {"q": query, "limit": 5, "sort": "relevance", "restrict_sr": "1"}
    try:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception:
        return []

    posts = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        score = post.get("score", 0)
        if score < 25:
            continue

        # Fetch top comments if the post has any
        comments = await _fetch_top_comments(client, post.get("permalink", ""))

        posts.append(RedditPost(
            title=post.get("title", ""),
            body=post.get("selftext", "")[:2000],
            top_comments=comments,
            url=f"https://reddit.com{post.get('permalink', '')}",
            score=score,
            subreddit=subreddit,
        ))
    return posts


async def _fetch_top_comments(client: httpx.AsyncClient, permalink: str) -> list[str]:
    if not permalink:
        return []
    try:
        url = f"https://www.reddit.com{permalink}.json"
        resp = await client.get(url, params={"limit": 5})
        if resp.status_code != 200:
            return []
        data = resp.json()
        comments_listing = data[1]["data"]["children"] if len(data) > 1 else []
        return [
            c["data"]["body"]
            for c in comments_listing
            if c.get("kind") == "t1"
            and len(c.get("data", {}).get("body", "")) > 50
        ][:3]
    except Exception:
        return []

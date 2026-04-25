import httpx
from dataclasses import dataclass


@dataclass
class TSB:
    id: str
    summary: str
    component: str
    date: str
    document_url: str


async def fetch_tsbs(make: str, model: str, year: int) -> list[TSB]:
    url = f"https://api.nhtsa.gov/complaints/complaintsByVehicle?make={make}&model={model}&modelYear={year}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    tsbs = []
    for item in data.get("results", [])[:10]:
        tsbs.append(TSB(
            id=str(item.get("odiNumber", "")),
            summary=item.get("summary", ""),
            component=item.get("components", ""),
            date=item.get("dateOfIncident", ""),
            document_url="",
        ))
    return tsbs

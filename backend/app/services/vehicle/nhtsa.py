import httpx
from dataclasses import dataclass
from typing import Optional


NHTSA_BASE = "https://vpic.nhtsa.dot.gov/api/vehicles"


@dataclass
class VehicleSpec:
    make: str
    model: str
    year: int
    trim: Optional[str] = None
    engine: Optional[str] = None
    body_type: Optional[str] = None
    drive_type: Optional[str] = None
    transmission: Optional[str] = None
    vin: Optional[str] = None


async def decode_vin(vin: str) -> Optional[VehicleSpec]:
    url = f"{NHTSA_BASE}/DecodeVin/{vin}?format=json"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    results = {item["Variable"]: item["Value"] for item in data["Results"]}

    make = results.get("Make", "")
    model = results.get("Model", "")
    year_str = results.get("Model Year", "")

    if not make or not model or not year_str:
        return None

    return VehicleSpec(
        vin=vin,
        make=make,
        model=model,
        year=int(year_str),
        trim=results.get("Trim") or None,
        engine=_build_engine_string(results),
        body_type=results.get("Body Class") or None,
        drive_type=results.get("Drive Type") or None,
        transmission=results.get("Transmission Style") or None,
    )


async def get_makes(year: int) -> list[str]:
    url = f"{NHTSA_BASE}/GetMakesForVehicleType/car?format=json"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    return [item["MakeName"] for item in data["Results"]]


async def get_models(make: str, year: int) -> list[str]:
    url = f"{NHTSA_BASE}/GetModelsForMakeYear/make/{make}/modelyear/{year}?format=json"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    return [item["Model_Name"] for item in data["Results"]]


async def get_recalls(make: str, model: str, year: int) -> list[dict]:
    url = f"https://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    return data.get("results", [])


def _build_engine_string(results: dict) -> Optional[str]:
    displacement = results.get("Displacement (L)")
    cylinders = results.get("Engine Number of Cylinders")
    config = results.get("Engine Configuration")

    if not displacement:
        return None

    parts = [f"{displacement}L"]
    if cylinders and config:
        parts.append(f"{cylinders}-cyl {config}")
    elif cylinders:
        parts.append(f"{cylinders}-cyl")

    return " ".join(parts)

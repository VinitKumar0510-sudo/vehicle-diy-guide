#!/usr/bin/env python3
"""
Pre-build repair guides for the top Australian vehicles.
Checks DB cache first — already-built guides are skipped instantly.
Safe to stop and re-run; resumes from where it left off.

Usage:
    python scripts/build_aus_guides.py              # build all
    python scripts/build_aus_guides.py --dry-run    # show plan, no API calls
    python scripts/build_aus_guides.py --limit 20   # build first N only
"""
import asyncio
import sys
import os
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from app.services.knowledge_builder.agent import build_guide
from app.db.connection import init_db, AsyncSessionLocal
from app.db.guide_repo import find_guide, _infer_system

# ── Australian vehicles (ranked by sales volume + DIY community size) ──────
VEHICLES = [
    # Utes — biggest DIY market in Australia
    {"make": "Toyota",     "model": "HiLux",      "year": 2020, "engine": "2.8L diesel"},
    {"make": "Toyota",     "model": "HiLux",      "year": 2018, "engine": "2.8L diesel"},
    {"make": "Ford",       "model": "Ranger",     "year": 2021, "engine": "2.0L diesel"},
    {"make": "Ford",       "model": "Ranger",     "year": 2019, "engine": "3.2L diesel"},
    {"make": "Isuzu",      "model": "D-Max",      "year": 2021, "engine": "3.0L diesel"},
    {"make": "Mitsubishi", "model": "Triton",     "year": 2020, "engine": "2.4L diesel"},
    {"make": "Nissan",     "model": "Navara",     "year": 2019, "engine": "2.3L diesel"},

    # LandCruisers — iconic in Australia, high shop bills → strong DIY incentive
    {"make": "Toyota",     "model": "LandCruiser", "year": 2019, "engine": "200 Series 4.5L V8 diesel"},
    {"make": "Toyota",     "model": "LandCruiser", "year": 2020, "engine": "79 Series 4.5L V8 diesel"},
    {"make": "Toyota",     "model": "LandCruiser", "year": 2022, "engine": "300 Series 3.3L diesel"},

    # SUVs — high volume, younger owners who Google everything
    {"make": "Toyota",     "model": "RAV4",       "year": 2021, "engine": "2.5L hybrid"},
    {"make": "Toyota",     "model": "RAV4",       "year": 2019, "engine": "2.0L petrol"},
    {"make": "Mazda",      "model": "CX-5",       "year": 2021, "engine": "2.5L petrol"},
    {"make": "Hyundai",    "model": "Tucson",     "year": 2021, "engine": "2.0L petrol"},
    {"make": "Kia",        "model": "Sportage",   "year": 2022, "engine": "2.0L petrol"},
    {"make": "Subaru",     "model": "Outback",    "year": 2021, "engine": "2.5L petrol"},
    {"make": "Volkswagen", "model": "Tiguan",     "year": 2021, "engine": "2.0L TSI"},
    {"make": "Nissan",     "model": "X-Trail",    "year": 2020, "engine": "2.5L petrol"},

    # Sedans/hatches — high volume, budget owners who DIY
    {"make": "Toyota",     "model": "Corolla",    "year": 2020, "engine": "2.0L petrol"},
    {"make": "Mazda",      "model": "Mazda3",     "year": 2020, "engine": "2.0L petrol"},
    {"make": "Hyundai",    "model": "i30",        "year": 2020, "engine": "2.0L petrol"},
    {"make": "Honda",      "model": "Civic",      "year": 2019, "engine": "1.5L turbo"},

    # Holden legacy — massive fleet, no dealer support, forced to DIY
    {"make": "Holden",     "model": "Commodore",  "year": 2017, "engine": "VF 3.6L V6"},
    {"make": "Holden",     "model": "Commodore",  "year": 2015, "engine": "VF 6.0L V8"},
    {"make": "Holden",     "model": "Colorado",   "year": 2018, "engine": "2.8L diesel"},
]

# ── Repairs (ordered: most searched first) ──────────────────────────────────
REPAIRS = [
    "oil change",
    "front brake pad replacement",
    "rear brake pad replacement",
    "air filter replacement",
    "cabin air filter replacement",
    "battery replacement",
    "spark plug replacement",
    "wiper blade replacement",
    "coolant flush",
    "brake fluid flush",
    "serpentine belt replacement",
    "differential oil change",       # huge for Australian utes and 4WDs
    "transfer case fluid change",    # 4WD specific
    "transmission fluid change",
    "power steering fluid change",
    "alternator replacement",
    "starter motor replacement",
    "thermostat replacement",
    "wheel bearing replacement",
    "rotor replacement",
]

COST_PER_GUIDE = 0.09  # AUD ~= USD at current rates, close enough for estimate
DELAY_BETWEEN_BUILDS = 4  # seconds — avoid rate limits


async def check_cached(make, model, year, repair) -> bool:
    """Returns True if this guide is already in the DB."""
    try:
        async with AsyncSessionLocal() as db:
            hit = await find_guide(db, make, model, year, repair)
            return hit is not None
    except Exception:
        return False


async def run(dry_run: bool = False, limit: int | None = None):
    if not dry_run:
        await init_db()

    combos = [(v, r) for v in VEHICLES for r in REPAIRS]
    if limit:
        combos = combos[:limit]

    total = len(combos)
    print(f"\n{'='*65}")
    print(f"  WrenchAI — Australian Guide Pre-Builder")
    print(f"{'='*65}")
    print(f"  Vehicles:  {len(VEHICLES)}")
    print(f"  Repairs:   {len(REPAIRS)}")
    print(f"  Total:     {total} guides")
    print(f"  Max cost:  ~${total * COST_PER_GUIDE:.0f} AUD (skips cached)")
    if dry_run:
        print(f"  Mode:      DRY RUN — no API calls")
    print(f"{'='*65}\n")

    built = 0
    skipped = 0
    failed = 0
    cost_spent = 0.0
    start = time.time()

    for i, (vehicle, repair) in enumerate(combos, 1):
        label = f"{vehicle['year']} {vehicle['make']} {vehicle['model']} — {repair}"
        prefix = f"[{i:>3}/{total}]"

        # Check cache first
        if not dry_run:
            cached = await check_cached(vehicle["make"], vehicle["model"], vehicle["year"], repair)
            if cached:
                print(f"{prefix} CACHED  {label}")
                skipped += 1
                continue

        if dry_run:
            print(f"{prefix} WOULD BUILD  {label}")
            built += 1
            continue

        print(f"{prefix} Building  {label} ...", end="", flush=True)
        t0 = time.time()

        try:
            result = await build_guide(
                make=vehicle["make"],
                model=vehicle["model"],
                year=vehicle["year"],
                repair=repair,
                engine=vehicle.get("engine"),
            )

            elapsed = time.time() - t0
            guide = result.guide

            if guide:
                built += 1
                cost_spent += COST_PER_GUIDE
                conf = f"{guide.confidence_score:.0%}"
                tier = guide.safety_tier
                steps = len(guide.steps)
                flag = " ⚠ LOW CONF" if result.needs_human_review else ""
                print(f"  ✓  {conf} conf · {steps} steps · {tier} · {elapsed:.0f}s{flag}")
            else:
                failed += 1
                print(f"  ✗  guide synthesis failed ({elapsed:.0f}s)")

        except Exception as e:
            failed += 1
            print(f"  ✗  ERROR: {e}")

        # ETA
        done = built + skipped + failed
        elapsed_total = time.time() - start
        rate = done / elapsed_total if elapsed_total > 0 else 1
        remaining = (total - done) / rate if rate > 0 else 0
        eta_min = int(remaining / 60)
        eta_sec = int(remaining % 60)
        print(f"          cost so far: ${cost_spent:.2f} | ETA: {eta_min}m {eta_sec}s")

        await asyncio.sleep(DELAY_BETWEEN_BUILDS)

    # ── Summary ─────────────────────────────────────────────────────────────
    total_time = time.time() - start
    print(f"\n{'='*65}")
    print(f"  DONE")
    print(f"{'='*65}")
    print(f"  Built:    {built}")
    print(f"  Cached:   {skipped}  (free — already in DB)")
    print(f"  Failed:   {failed}")
    print(f"  Cost:     ${cost_spent:.2f} AUD")
    print(f"  Time:     {int(total_time/60)}m {int(total_time%60)}s")
    print(f"{'='*65}\n")

    if failed > 0:
        print(f"  ⚠  {failed} guides failed. Re-run to retry — cached ones are skipped.\n")


def main():
    parser = argparse.ArgumentParser(description="Pre-build Australian repair guides")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without making API calls")
    parser.add_argument("--limit", type=int, default=None, help="Only build first N guides")
    args = parser.parse_args()
    asyncio.run(run(dry_run=args.dry_run, limit=args.limit))


if __name__ == "__main__":
    main()

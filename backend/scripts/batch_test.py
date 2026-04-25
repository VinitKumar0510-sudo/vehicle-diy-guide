#!/usr/bin/env python3
"""
Batch test the knowledge builder across multiple vehicles and repairs.
Produces a quality report showing confidence scores across the matrix.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from app.services.knowledge_builder.agent import build_guide

VEHICLES = [
    {"make": "Toyota", "model": "Camry",  "year": 2019, "engine": "2.5L 4-cyl"},
    {"make": "Honda",  "model": "Civic",  "year": 2020, "engine": "1.5L 4-cyl"},
    {"make": "Ford",   "model": "F-150",  "year": 2020, "engine": "5.0L V8"},
]

REPAIRS = [
    "brake pad replacement",
    "oil change",
    "battery replacement",
]


async def run_batch():
    results = []
    total = len(VEHICLES) * len(REPAIRS)
    count = 0

    for vehicle in VEHICLES:
        for repair in REPAIRS:
            count += 1
            label = f"{vehicle['year']} {vehicle['make']} {vehicle['model']} — {repair}"
            print(f"[{count}/{total}] Building: {label}")

            try:
                result = await build_guide(
                    make=vehicle["make"],
                    model=vehicle["model"],
                    year=vehicle["year"],
                    repair=repair,
                    engine=vehicle.get("engine"),
                )
                guide = result.guide
                results.append({
                    "vehicle": label,
                    "repair": repair,
                    "success": guide is not None,
                    "confidence": guide.confidence_score if guide else 0,
                    "steps": len(guide.steps) if guide else 0,
                    "safety_tier": guide.safety_tier if guide else "—",
                    "difficulty": guide.difficulty if guide else 0,
                    "time_min": guide.time_estimate_minutes if guide else 0,
                    "needs_review": result.needs_human_review,
                    "sources": result.source_counts,
                })
                status = f"✓ {guide.confidence_score:.0%} confidence, {len(guide.steps)} steps" if guide else "✗ FAILED"
                print(f"       {status}")
            await asyncio.sleep(3)  # avoid rate limits between guides
            except Exception as e:
                results.append({
                    "vehicle": label,
                    "repair": repair,
                    "success": False,
                    "confidence": 0,
                    "steps": 0,
                    "safety_tier": "—",
                    "difficulty": 0,
                    "time_min": 0,
                    "needs_review": True,
                    "sources": {},
                })
                print(f"       ✗ ERROR: {e}")

    print_report(results)


def print_report(results):
    print("\n" + "="*70)
    print("  BATCH TEST REPORT")
    print("="*70)

    print(f"\n{'Vehicle':<45} {'Conf':>6} {'Steps':>6} {'Tier':>8} {'Review':>8}")
    print("-"*70)

    total_cost = 0
    cost_per_guide = 0.0876

    for r in results:
        if r["success"]:
            conf = f"{r['confidence']:.0%}"
            steps = str(r["steps"])
            tier = r["safety_tier"]
            review = "⚠️ YES" if r["needs_review"] else "✓ no"
            total_cost += cost_per_guide
        else:
            conf, steps, tier, review = "FAIL", "—", "—", "—"

        label = r["vehicle"][:44]
        print(f"{label:<45} {conf:>6} {steps:>6} {tier:>8} {review:>8}")

    print("-"*70)
    successful = sum(1 for r in results if r["success"])
    avg_conf = sum(r["confidence"] for r in results if r["success"]) / max(successful, 1)
    needs_review = sum(1 for r in results if r["needs_review"] and r["success"])

    print(f"\nSuccessful:     {successful}/{len(results)}")
    print(f"Avg confidence: {avg_conf:.0%}")
    print(f"Needs review:   {needs_review} guides")
    print(f"Est. total cost: ${total_cost:.2f}")
    print(f"\nAt this cost: 1,000 guides = ${1000 * cost_per_guide:.0f}")


if __name__ == "__main__":
    asyncio.run(run_batch())

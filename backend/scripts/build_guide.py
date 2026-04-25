#!/usr/bin/env python3
"""
CLI script to build and inspect a repair guide.
Usage:
    python scripts/build_guide.py --make Toyota --model Camry --year 2019 --repair "brake pad replacement"
"""
import asyncio
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.services.knowledge_builder.agent import build_guide


def print_section(title: str, content: str = ""):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    if content:
        print(content)


async def main():
    parser = argparse.ArgumentParser(description="Build a vehicle repair guide")
    parser.add_argument("--make", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--repair", required=True)
    parser.add_argument("--engine", default=None)
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    print(f"\nBuilding guide: {args.year} {args.make} {args.model} — {args.repair}")
    print("Fetching sources and synthesizing... (this takes ~30-60 seconds)\n")

    result = await build_guide(
        make=args.make,
        model=args.model,
        year=args.year,
        repair=args.repair,
        engine=args.engine,
    )

    if not result.guide:
        print("ERROR: Failed to synthesize guide. Check your API keys and sources.")
        sys.exit(1)

    guide = result.guide

    if args.json:
        output = {
            "title": guide.title,
            "summary": guide.summary,
            "difficulty": guide.difficulty,
            "time_estimate_minutes": guide.time_estimate_minutes,
            "safety_tier": guide.safety_tier,
            "confidence_score": guide.confidence_score,
            "tools_required": guide.tools_required,
            "parts_required": guide.parts_required,
            "steps": guide.steps,
            "warnings": guide.warnings,
            "sources": guide.sources,
            "needs_human_review": result.needs_human_review,
            "source_counts": result.source_counts,
        }
        print(json.dumps(output, indent=2))
        return

    # Human-readable output
    print_section("GUIDE METADATA")
    print(f"Title:      {guide.title}")
    print(f"Difficulty: {'★' * guide.difficulty}{'☆' * (5 - guide.difficulty)} ({guide.difficulty}/5)")
    print(f"Time:       ~{guide.time_estimate_minutes} minutes")
    tier_color = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(guide.safety_tier, "⚪")
    print(f"Safety:     {tier_color} {guide.safety_tier.upper()}")
    print(f"Confidence: {guide.confidence_score:.0%}")
    review_flag = "⚠️  NEEDS HUMAN REVIEW" if result.needs_human_review else "✓ Passes threshold"
    print(f"Review:     {review_flag}")
    print(f"\nSources:    {result.source_counts['web']} web, {result.source_counts['video']} video, {result.source_counts['reddit']} reddit")

    print_section("SUMMARY")
    print(guide.summary)

    if guide.warnings:
        print_section("WARNINGS")
        for w in guide.warnings:
            print(f"  ⚠️  {w}")

    print_section("PRE-FLIGHT: TOOLS REQUIRED")
    for tool in guide.tools_required:
        print(f"  □ {tool}")

    print_section("PRE-FLIGHT: PARTS REQUIRED")
    for part in guide.parts_required:
        qty = part.get("quantity", 1)
        pn = f" [PN: {part['part_number']}]" if part.get("part_number") else ""
        notes = f" — {part['notes']}" if part.get("notes") else ""
        consumable = " (consumable)" if part.get("consumable") else ""
        print(f"  □ {qty}x {part['name']}{pn}{consumable}{notes}")

    print_section(f"REPAIR STEPS ({len(guide.steps)} steps)")
    for step in guide.steps:
        confidence_bar = "▓" * int(step.get("confidence", 0.8) * 10) + "░" * (10 - int(step.get("confidence", 0.8) * 10))
        print(f"\nStep {step['step_number']}: {step['title']}")
        print(f"  {step['instruction']}")
        if step.get("why"):
            print(f"  WHY: {step['why']}")
        if step.get("torque_spec"):
            print(f"  TORQUE: {step['torque_spec']}")
        if step.get("tool_needed"):
            print(f"  TOOL: {step['tool_needed']}")
        if step.get("warning"):
            print(f"  ⚠️  {step['warning']}")
        print(f"  Confidence: [{confidence_bar}] {step.get('confidence', 0.8):.0%}")


if __name__ == "__main__":
    asyncio.run(main())

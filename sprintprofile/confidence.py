from __future__ import annotations

from typing import Any, Callable

from .models import Record

# field name -> getter
CRITICAL: dict[str, Callable[[Record], object]] = {
    "height_m": lambda r: r.athlete.height_m,
    "weight_kg": lambda r: r.athlete.weight_kg,
    "waist_cm": lambda r: r.athlete.waist_cm,
    "weekly_sprint_volume_m": lambda r: r.regimen.weekly_sprint_volume_m,
    "carb_g_per_kg": lambda r: r.diet.carb_g_per_kg,
    "splits": lambda r: r.perf.splits,
}


def confidence(rec: Record) -> dict[str, Any]:
    missing = [k for k, get in CRITICAL.items() if get(rec) is None]
    completeness = 1 - len(missing) / len(CRITICAL)

    if completeness == 1.0:
        tier = "A"
    elif completeness >= 0.5:
        tier = "B"
    else:
        tier = "C"

    return {
        "completeness": round(completeness, 2),
        "profile_tier": tier,
        "missing": missing,
        "research_tasks": [f"document {m} with a citable source" for m in missing],
    }

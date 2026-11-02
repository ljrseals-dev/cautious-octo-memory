from __future__ import annotations

from typing import Any

from .models import Record

YARD_M = 0.9144


def _entry(value: float, tier: str, source: str) -> dict[str, Any]:
    return {"value": round(value, 3), "tier": tier, "source": source}


def derive(rec: Record) -> dict[str, dict[str, Any]]:
    """Tier B arithmetic + one flagged Tier C approximation.

    Keys are OMITTED when inputs are absent. Nothing is null-filled.
    """
    a, d, p = rec.athlete, rec.diet, rec.perf
    out: dict[str, dict[str, Any]] = {}

    # ---- BMI (needs height + weight) ----
    if a.height_m and a.weight_kg:
        out["bmi"] = _entry(a.weight_kg / a.height_m**2, "B",
                            "weight_kg / height_m^2")

    # ---- waist-to-height (needs waist + height) ----
    if a.waist_cm and a.height_m:
        out["waist_to_height"] = _entry(
            a.waist_cm / (a.height_m * 100), "B", "waist_cm / height_cm")

    # ---- Hume lean body mass (needs height + weight + sex) ----
    if a.height_m and a.weight_kg:
        h_cm = a.height_m * 100
        if a.sex.upper() == "M":
            lbm = 0.32810 * a.weight_kg + 0.33929 * h_cm - 29.5336
        else:
            lbm = 0.29569 * a.weight_kg + 0.41813 * h_cm - 43.2933
        out["lbm_kg_est"] = _entry(lbm, "B", "Hume 1966 equation")
        out["body_fat_pct_est"] = _entry(
            (a.weight_kg - lbm) / a.weight_kg * 100, "B",
            "(weight - LBM) / weight")

    # ---- velocity signature (needs distance + time; distance always present) ----
    meters = p.distance_yards * YARD_M
    avg_v = meters / p.time_s
    out["avg_velocity_ms"] = _entry(avg_v, "B",
                                    "distance_m / time_s")
    # Tier C: rule-of-thumb, NOT measured, never used in ranking
    out["peak_velocity_ms_est"] = _entry(
        1.05 * avg_v, "C", "1.05 x avg velocity (approximation)")

    # ---- fueling signature (needs carbs + kcal + weight) ----
    if d.carb_g_per_kg and d.kcal_per_day and a.weight_kg:
        out["carb_kcal_share"] = _entry(
            d.carb_g_per_kg * a.weight_kg * 4 / d.kcal_per_day, "B",
            "carb_g_per_kg * weight * 4 / kcal_per_day")

    return out

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .models import (Athlete, Diet, Performance, Provenance, Record, Regimen,
                     ValidationError)

_ALLOWED_TOP = {"athlete", "regimen", "diet", "perf", "prov"}


def _num(v: Any) -> float | None:
    if v is None or v == "" or v == "null":
        return None
    return float(v)


def from_dict(raw: dict[str, Any], *, strict: bool = True) -> Record:
    if strict:
        unknown = set(raw) - _ALLOWED_TOP
        if unknown:
            raise ValidationError(f"unknown top-level keys: {sorted(unknown)}")

    a = raw.get("athlete", {})
    r = raw.get("regimen", {})
    d = raw.get("diet", {})
    p = raw["perf"]

    splits = p.get("splits")
    if isinstance(splits, str):
        splits = [float(x) for x in splits.split(",") if x.strip()]

    prov = {
        k: Provenance(tier=v.get("tier", "C"), source=v.get("source", "inferred"))
        for k, v in raw.get("prov", {}).items()
    }

    return Record(
        athlete=Athlete(
            name=a["name"],
            sex=a["sex"],
            height_m=_num(a.get("height_m")),
            weight_kg=_num(a.get("weight_kg")),
            waist_cm=_num(a.get("waist_cm")),
        ),
        regimen=Regimen(
            sprint_days_per_week=r.get("sprint_days_per_week"),
            weekly_sprint_volume_m=_num(r.get("weekly_sprint_volume_m")),
            accel_work_pct=_num(r.get("accel_work_pct")),
            max_velocity_pct=_num(r.get("max_velocity_pct")),
            lifting_days_per_week=r.get("lifting_days_per_week"),
            notes=r.get("notes", ""),
        ),
        diet=Diet(
            kcal_per_day=_num(d.get("kcal_per_day")),
            carb_g_per_kg=_num(d.get("carb_g_per_kg")),
            protein_g_per_kg=_num(d.get("protein_g_per_kg")),
            pre_test_fuel=d.get("pre_test_fuel"),
            fasting_protocol=d.get("fasting_protocol"),
        ),
        perf=Performance(
            distance_yards=int(p["distance_yards"]),
            time_s=float(p["time_s"]),
            splits=splits,
        ),
        prov=prov,
    )


def load_json(path: str | Path, *, strict: bool = True) -> Record:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    rec = from_dict(raw, strict=strict)
    rec.validate()
    return rec


def load_many(paths: list[str]) -> list[Record]:
    return [load_json(p) for p in paths]


def load_csv(path: str | Path) -> list[Record]:
    """One row per athlete. Blank cells become None — never defaults."""
    out: list[Record] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            raw = {
                "athlete": {"name": row["name"], "sex": row["sex"],
                            "height_m": row.get("height_m"),
                            "weight_kg": row.get("weight_kg"),
                            "waist_cm": row.get("waist_cm")},
                "regimen": {k: row.get(k) for k in (
                    "sprint_days_per_week", "weekly_sprint_volume_m",
                    "accel_work_pct", "max_velocity_pct",
                    "lifting_days_per_week")},
                "diet": {k: row.get(k) for k in (
                    "kcal_per_day", "carb_g_per_kg", "protein_g_per_kg",
                    "pre_test_fuel", "fasting_protocol")},
                "perf": {"distance_yards": row["distance_yards"],
                         "time_s": row["time_s"],
                         "splits": row.get("splits")},
            }
            rec = from_dict(raw)
            rec.validate()
            out.append(rec)
    return out

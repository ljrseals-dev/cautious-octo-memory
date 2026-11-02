from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal

Tier = Literal["A", "B", "C"]


class ValidationError(ValueError):
    """Raised when a record contains impossible or malformed data."""


@dataclass
class Provenance:
    tier: Tier
    source: str = "inferred"


def _p(tier: Tier, source: str) -> Provenance:
    return Provenance(tier=tier, source=source)


@dataclass
class Athlete:
    name: str
    sex: str
    height_m: float | None = None
    weight_kg: float | None = None
    waist_cm: float | None = None


@dataclass
class Regimen:
    sprint_days_per_week: int | None = None
    weekly_sprint_volume_m: float | None = None
    accel_work_pct: float | None = None
    max_velocity_pct: float | None = None
    lifting_days_per_week: int | None = None
    notes: str = ""


@dataclass
class Diet:
    kcal_per_day: float | None = None
    carb_g_per_kg: float | None = None
    protein_g_per_kg: float | None = None
    pre_test_fuel: str | None = None
    fasting_protocol: str | None = None


@dataclass
class Performance:
    distance_yards: int
    time_s: float
    splits: list[float] | None = None


@dataclass
class Record:
    athlete: Athlete
    regimen: Regimen
    diet: Diet
    perf: Performance
    prov: dict[str, Provenance] = field(default_factory=dict)

    # ---------- validation ----------
    def validate(self) -> None:
        a, p = self.athlete, self.perf

        if a.sex.upper() not in {"M", "F"}:
            raise ValidationError(f"athlete.sex must be 'M' or 'F', got {a.sex!r}")

        if p.distance_yards not in {50, 60}:
            raise ValidationError(
                f"perf.distance_yards must be 50 or 60, got {p.distance_yards}")
        if p.time_s is None or p.time_s <= 0:
            raise ValidationError(f"perf.time_s must be > 0, got {p.time_s}")

        if a.height_m is not None and not (1.2 <= a.height_m <= 2.3):
            raise ValidationError(f"height_m out of range [1.2, 2.3]: {a.height_m}")
        if a.weight_kg is not None and not (30 <= a.weight_kg <= 200):
            raise ValidationError(f"weight_kg out of range [30, 200]: {a.weight_kg}")
        if a.waist_cm is not None and not (40 <= a.waist_cm <= 150):
            raise ValidationError(f"waist_cm out of range [40, 150]: {a.waist_cm}")

        if p.splits is not None:
            if len(p.splits) < 2:
                raise ValidationError("splits must contain at least 2 checkpoints")
            if any(s <= 0 for s in p.splits):
                raise ValidationError("splits must be strictly positive")
            if any(b <= a_ for a_, b in zip(p.splits, p.splits[1:])):
                raise ValidationError("splits must be strictly increasing")

        for name, prov in self.prov.items():
            if prov.tier not in {"A", "B", "C"}:
                raise ValidationError(f"prov[{name!r}].tier invalid: {prov.tier}")

        # plausibility guard: 50y/60y sprint must land in 6-12 m/s
        meters = p.distance_yards * 0.9144
        v = meters / p.time_s
        if not (6.0 <= v <= 12.0):
            raise ValidationError(
                f"implausible average velocity {v:.2f} m/s for "
                f"{p.distance_yards}y in {p.time_s}s — check units")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

Copyright © 2026 Lewis James Seals Jr. All rights reserved. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

sprintprofile

Deterministic, evidence-graded physical-property profiles for 50- and 60-yard sprinters.
Every field carries provenance. Nothing is invented. Gaps are the product.

sprintprofile ingests what is actually documented about a sprinter — training
regimen, diet, anthropometry (height, weight, waist) — and emits a structured
profile that links those inputs to 50/60-yard performance. It is not a coach and
not a data source. It is a contract: a schema, a provenance model, and a set
of rules that make it impossible to mistake an inference for a measurement.

---

Status

Area State
Profiling core (profile, validate, gaps) Implemented, working
Comparison / similarity (compare) Implemented, ranking guard missing (see Known Issues)
Provenance propagation through derivation Buggy — see Known Issues
Brute-genius program search Not implemented — see Roadmap
Seed corpus 2 records (Pender, Washington), both profile_tier: C

Read Known Issues before relying on any output.

---

Why this exists

There is no published dataset pairing a 5.8s 60-yard performance with a
documented diet, training log, and waist measurement. Herb Washington and Mel
Pender ran 5.8 in 1972–73; Evelyn Ashford 6.54 in 1982. We have times. We do not
have the regimens.

A tool that filled those blanks would be lying. So this one doesn't. Instead it:

1. stores only what a source supports,
2. tags every value A / B / C by evidence quality,
3. refuses to compute a derived metric when its inputs are missing,
4. reports every missing critical field as a named research task.

The output doubles as a data-collection checklist. That is the point.

---

Install

```bash
git clone https://github.com/ljrseals-dev/cautious-octo-memory.git
cd cautious-octo-memory
python -m venv .venv && source .venv/bin/activate
pip install -e .
pytest -q
```

Requires Python 3.10+ (uses X | Y union syntax and from __future__ import annotations).

---

Usage

Profile a single athlete

```bash
sprintprofile profile data/records/pender.json
```

Emits stable, sorted JSON:

```json
{
  "athlete": { "name": "Mel Pender", "sex": "M", "height_m": 1.7,
               "weight_kg": 70.0, "waist_cm": null },
  "performance": { "distance_yards": 60, "time_s": 5.8, "splits": null },
  "derived_physical_properties": {
    "avg_velocity_ms":      { "value": 9.457, "tier": "B", "source": "distance_m / time_s" },
    "peak_velocity_ms_est": { "value": 9.929, "tier": "C", "source": "1.05 x avg velocity (approximation)" }
  },
  "confidence": {
    "completeness": 0.33,
    "profile_tier": "C",
    "missing": ["waist_cm", "weekly_sprint_volume_m", "carb_g_per_kg", "splits"],
    "research_tasks": [
      "document waist_cm with a citable source",
      "document weekly_sprint_volume_m with a citable source",
      "document carb_g_per_kg with a citable source",
      "document splits with a citable source"
    ]
  },
  "regimen": { "...": "nulls preserved" },
  "diet":    { "...": "nulls preserved" }
}
```

Note that lbm_kg_est and body_fat_pct_est are absent. Weight is only
Tier C for this athlete, so the derivation is (correctly) suppressed — see
Known Issues for why this is currently not what the code does.

Validate before ingesting

```bash
sprintprofile validate data/records/pender.json   # exit 0
sprintprofile validate bad.json                   # exit 1, reason on stderr
```

Rejects impossible physiology (height outside 1.2–2.3 m, weight outside 30–200 kg,
waist outside 40–150 cm), non-monotonic splits, and average velocities outside
6–12 m/s — the usual unit-error tell.

Find the gaps

```bash
sprintprofile gaps data/records
```

Per-record completeness and missing fields. This is the command that tells you
what to go measure.

Compare — complete records only

```bash
sprintprofile compare data/records/*.json \
  --fields waist_cm,diet.carb_g_per_kg \
  --similarity
```

Records missing any requested field land in excluded with the reason. No
imputation, ever. --similarity computes z-scored Euclidean distances over the
complete subset only; with fewer than two complete records it returns a note
rather than a fabricated matrix.

Exit codes

Code Meaning
0 Success
1 Validation failure (record loaded but physically implausible)
2 Input error (missing file, bad JSON, unknown key, bad field path)

---

The provenance model

This is the part of the product that matters.

Tier Meaning Can be ranked on?
A Directly measured or documented, with a citable source Yes
B Derived arithmetically from Tier A/B inputs Yes
C Population default, approximation, or unsourced estimate No

Rules, enforced by design:

· A field with no source is demoted to C.
· Derived values inherit the worst tier of their inputs.
· Tier C values are emitted with an _est suffix and are excluded from
  ranking, similarity, and any downstream claim.
· Inferred values are never silently mixed with measured ones.

Data model

```
Record = Athlete + Regimen + Diet + Performance + prov

Athlete     name, sex (M|F), height_m, weight_kg, waist_cm
Regimen     sprint_days_per_week, weekly_sprint_volume_m,
            accel_work_pct, max_velocity_pct, lifting_days_per_week, notes
Diet        kcal_per_day, carb_g_per_kg, protein_g_per_kg,
            pre_test_fuel, fasting_protocol
Performance distance_yards (50|60), time_s, splits[]
```

Every field is optional except athlete.name, athlete.sex,
perf.distance_yards, and perf.time_s. Every one of those is null-able in
output but never defaulted in input.

---

Record format

JSON, one file per athlete:

```json
{
  "athlete": {
    "name": "Mel Pender", "sex": "M",
    "height_m": 1.70, "weight_kg": 70.0, "waist_cm": null
  },
  "regimen": {
    "sprint_days_per_week": null,
    "weekly_sprint_volume_m": null,
    "accel_work_pct": null,
    "max_velocity_pct": null,
    "lifting_days_per_week": null,
    "notes": "regimen undocumented in accessible sources"
  },
  "diet": {
    "kcal_per_day": null, "carb_g_per_kg": null,
    "protein_g_per_kg": null, "pre_test_fuel": null,
    "fasting_protocol": null
  },
  "perf": {
    "distance_yards": 60, "time_s": 5.8, "splits": null
  },
  "prov": {
    "athlete.height_m": { "tier": "A", "source": "athlete registry" },
    "athlete.weight_kg": { "tier": "C", "source": "approximate" },
    "perf.time_s":       { "tier": "A", "source": "world record, 1973" }
  }
}
```

CSV ingestion (load_csv) accepts a flat row per athlete; blank cells become
null, never defaults.

---

Known Issues

These are real defects in the current implementation, not roadmap items. The
README documents them because a provenance tool that hides its own provenance
bugs is worthless.

1. Derivation ignores input tier (correctness bug)

derive() labels LBM and body-fat output as Tier B whenever height and
weight are present, without checking their provenance. Pender's weight is
tagged Tier C, so the tool currently emits a Tier B-looking metric derived from
a Tier C input. The test suite asserts this behavior as correct.

Expected: derived value carries the worst input tier (Tier C here), or is
suppressed.

Fix sketch:

```python
def _tier(rec, dotted: str) -> str:
    prov = rec.prov.get(dotted)
    return prov.tier if prov else "C"

def _worst(*tiers: str) -> str:
    return "C" if "C" in tiers else "B" if "B" in tiers else "A"

tier = _worst(_tier(rec, "athlete.height_m"), _tier(rec, "athlete.weight_kg"))
out["lbm_kg_est"] = _entry(lbm, tier, f"Hume 1966 (inputs: {tier})")
```

2. Tier C can enter ranking (contract violation)

compare() and similarity() filter only on None; they never inspect
provenance. A user can rank on peak_velocity_ms_est — a Tier C approximation —
and the tool will happily comply.

Fix: a --allow-tier-c flag (default off) plus a guard that checks
provenance before scoring. Derived fields need a parallel derived_prov map
because record.prov only tracks raw inputs.

3. CLI raises AttributeError on bad field paths

sprintprofile compare ... --fields athlete.nonexistent produces an uncaught
traceback instead of exit code 2. main() should catch AttributeError.

4. Test suite gaps

No coverage for: provenance propagation, similarity(), load_csv(), CLI exit
codes, split validation, or strict-mode unknown-key rejection. The two strongest
invariants in MASTER_PROMPT.md — propagation and ranking exclusion — are
untested.

---

Roadmap

1. Fix provenance propagation in derive(); invert the Pender test.
2. Ranking guard so Tier C cannot enter compare / similarity without
   --allow-tier-c.
3. Emit derived_prov alongside derived_physical_properties.
4. Harden CLI (catch AttributeError, return 2).
5. Close test gaps above.
6. Brute-genius enumerator — the actual search engine this tool was meant to
   feed. Enumerate interventions across Donella Meadows' 12 leverage points
   (data/leverage_points.json), score each combination against an objective
   (e.g. minimizing variance in sprint time across fueling states), and emit
   ranked_programs.json. The hypothesis: deep leverage points (goals, rules,
   paradigm) dominate parameter tweaks. The enumeration is what proves or
   disproves it.

---

Design principles

1. Never invent data. Undocumented means null.
2. Provenance is a first-class primitive. Per-field tier and source.
3. Gaps are the product. Every null is a research task.
4. No cross-contamination. Derived never replaces documented.
5. Determinism. Same input → byte-identical output. No clocks, no randomness,
   no runtime network calls.
6. Fail loudly, never partially. No partial profiles on invalid input.
7. The refusal is the feature. The quality of what the tool declines to
   produce is the measure of its worth.

The full behavioral contract lives in MASTER_PROMPT.md.
That file, not this README, is the source of truth for what the code must do.

---

Repository layout

```
cautious-octo-memory/
├── MASTER_PROMPT.md
├── README.md
├── sprintprofile/
│   ├── models.py        # dataclasses + validation
│   ├── derive.py        # Tier B arithmetic, Tier C flagged approximations
│   ├── confidence.py    # completeness scoring, research-task generation
│   ├── ingest.py        # JSON + CSV loaders
│   ├── rank.py          # compare + similarity (complete records only)
│   └── cli.py           # argparse front end, exit codes
├── data/records/
│   ├── pender.json
│   └── washington.json
└── tests/test_core.py
```

---

Contributing

The highest-value contributions are data, in this order:

1. A Tier A record with waist_cm, weekly_sprint_volume_m,
   carb_g_per_kg, and splits all filled and sourced. One such record moves
   the corpus from "checklist" to "comparison."
2. Fixes for the Known Issues, each with a test that would have caught it.
3. The brute-genius enumerator.

Please do not submit records with inferred values in prov-less fields. A null
is worth more than a guess.

---

License

TBD.

---

Acknowledgments

Methodology informed by Donella H. Meadows, Thinking in Systems: A Primer
(Chelsea Green, 2008). Historical sprint records from public athletic registries.
The gap between those two sources is the reason this tool exists.

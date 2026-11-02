# sprintprofile

Deterministic Python tool that builds evidence-graded physical-property profiles
for sprinters over 50 and 60 yards, linking performance to training regimen,
diet, and anthropometry (height, weight, waist).

## Non-negotiable rules

- NEVER invent data. Nulls stay null.
- Every value carries provenance (Tier A/B/C).
- Gaps are the product — every null is a named research task.
- Deterministic: identical input → byte-identical output.

## Install

```bash
pip install -e .
```

## Usage

```bash
sprintprofile profile data/records/pender.json
sprintprofile validate data/records/pender.json
sprintprofile gaps data/records
sprintprofile compare data/records/*.json --fields waist_cm,diet.carb_g_per_kg --similarity
```

## Tests

```bash
pytest -q
```

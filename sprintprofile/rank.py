from __future__ import annotations

from typing import Any, Iterable, Sequence

from .models import Record


def _get(rec: Record, dotted: str) -> Any:
    obj: Any = rec
    for part in dotted.split("."):
        obj = getattr(obj, part)
    return obj


def compare(records: Sequence[Record], fields: Sequence[str]) -> dict[str, Any]:
    """Table of records where EVERY requested field is non-null.

    Incomplete records are excluded WITH the reason. No imputation.
    """
    included, excluded = [], []
    for rec in records:
        absent = [f for f in fields if _get(rec, f) is None]
        if absent:
            excluded.append({"name": rec.athlete.name, "missing": absent})
        else:
            row = {"name": rec.athlete.name}
            row.update({f: _get(rec, f) for f in fields})
            included.append(row)

    return {"fields": list(fields), "included": included, "excluded": excluded}


def similarity(records: Sequence[Record], fields: Sequence[str]) -> dict[str, Any]:
    """Z-scored Euclidean distance matrix over COMPLETE records only."""
    complete = [r for r in records
                if all(_get(r, f) is not None for f in fields)]
    if len(complete) < 2:
        return {"matrix": [], "note": "fewer than 2 complete records — "
                                      "collect more Tier A data"}

    cols = {f: [float(_get(r, f)) for r in complete] for f in fields}
    stats = {}
    for f, vals in cols.items():
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        stats[f] = (mean, var ** 0.5 or 1.0)

    matrix = []
    for i, a in enumerate(complete):
        row = {"name": a.athlete.name, "distances": {}}
        for j, b in enumerate(complete):
            if i == j:
                continue
            d = sum(((_get(a, f) - _get(b, f)) / stats[f][1]) ** 2 for f in fields)
            row["distances"][b.athlete.name] = round(d ** 0.5, 3)
        matrix.append(row)

    return {"fields": list(fields), "matrix": matrix}

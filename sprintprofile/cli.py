from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .confidence import confidence
from .derive import derive
from .ingest import load_csv, load_json, load_many
from .models import ValidationError
from .rank import compare, similarity


def _profile(rec) -> dict:
    return {
        "athlete": asdict(rec.athlete),
        "performance": asdict(rec.perf),
        "derived_physical_properties": derive(rec),
        "confidence": confidence(rec),
        "regimen": asdict(rec.regimen),
        "diet": asdict(rec.diet),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sprintprofile")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_profile = sub.add_parser("profile")
    p_profile.add_argument("file")

    p_val = sub.add_parser("validate")
    p_val.add_argument("file")

    p_cmp = sub.add_parser("compare")
    p_cmp.add_argument("files", nargs="+")
    p_cmp.add_argument("--fields", required=True,
                       help="comma list, e.g. waist_cm,diet.carb_g_per_kg")
    p_cmp.add_argument("--similarity", action="store_true")

    p_gaps = sub.add_parser("gaps")
    p_gaps.add_argument("dir")

    args = parser.parse_args(argv)

    try:
        if args.cmd == "profile":
            print(json.dumps(_profile(load_json(args.file)),
                             indent=2, sort_keys=True))
            return 0

        if args.cmd == "validate":
            rec = load_json(args.file)
            print(f"OK: {rec.athlete.name} "
                  f"{rec.perf.distance_yards}y in {rec.perf.time_s}s")
            return 0

        if args.cmd == "compare":
            records = load_many(args.files)
            fields = [f.strip() for f in args.fields.split(",") if f.strip()]
            out = compare(records, fields)
            if args.similarity:
                out["similarity"] = similarity(records, fields)
            print(json.dumps(out, indent=2, sort_keys=True))
            return 0

        if args.cmd == "gaps":
            rows = []
            for path in sorted(Path(args.dir).glob("*.json")):
                rec = load_json(path)
                rows.append({"file": path.name, "athlete": rec.athlete.name,
                             **confidence(rec)})
            print(json.dumps(rows, indent=2, sort_keys=True))
            return 0

    except ValidationError as e:
        print(f"validation error: {e}", file=sys.stderr)
        return 1
    except (KeyError, FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"input error: {e}", file=sys.stderr)
        return 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

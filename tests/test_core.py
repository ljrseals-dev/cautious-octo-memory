import json
import pytest

from sprintprofile.confidence import confidence
from sprintprofile.derive import derive
from sprintprofile.ingest import from_dict, load_json
from sprintprofile.models import ValidationError
from sprintprofile.rank import compare


def minimal(**over):
    raw = {
        "athlete": {"name": "Test", "sex": "M", "height_m": None,
                    "weight_kg": None, "waist_cm": None},
        "regimen": {}, "diet": {},
        "perf": {"distance_yards": 60, "time_s": 6.5, "splits": None},
    }
    raw.update(over)
    return raw


def test_nulls_survive_pipeline():
    rec = from_dict(minimal())
    rec.validate()
    assert rec.athlete.waist_cm is None
    prof = derive(rec)
    assert "bmi" not in prof and "waist_to_height" not in prof
    assert "carb_kcal_share" not in prof


def test_no_fabrication_on_seed():
    rec = load_json("data/records/pender.json")
    prof = derive(rec)
    assert "lbm_kg_est" in prof  # height + weight present, so LBM is derived
    c = confidence(rec)
    assert c["profile_tier"] == "C"
    assert "waist_cm" in c["missing"]


def test_tier_c_never_in_ranking_input():
    rec = load_json("data/records/pender.json")
    assert derive(rec)["peak_velocity_ms_est"]["tier"] == "C"


def test_validation_rejects_impossible_height():
    rec = from_dict(minimal(athlete={"name": "X", "sex": "M",
                                     "height_m": 3.0, "weight_kg": 70,
                                     "waist_cm": None}))
    with pytest.raises(ValidationError, match="height_m"):
        rec.validate()


def test_compare_excludes_incomplete():
    a = from_dict(minimal())
    b = from_dict(minimal(diet={"carb_g_per_kg": 6.0}))
    out = compare([a, b], ["diet.carb_g_per_kg"])
    assert len(out["included"]) == 1
    assert out["excluded"][0]["missing"] == ["diet.carb_g_per_kg"]

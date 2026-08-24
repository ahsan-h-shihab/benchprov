from conftest import base_record, with_derived

from benchprov.model import (
    canonical_dumps,
    compute_completeness,
    compute_state,
    expected_record_id,
    language_part,
    slugify,
    unknown_dimensions,
)


def test_slugify():
    assert slugify("FreedomIntelligence/MMLU_Arabic") == "freedomintelligence-mmlu_arabic"
    assert slugify("CohereLabs/Global-MMLU") == "coherelabs-global-mmlu"
    assert slugify("a b/C+D") == "a-b-c-d"


def test_language_part():
    assert language_part(["ar"]) == "ar"
    assert language_part(["kk-Cyrl"]) == "kk-cyrl"
    assert language_part(["de", "fr", "it"]) == "de-fr-it"
    assert language_part(["a1", "b2", "c3", "d4"]) == "multi"  # 4+ collapses


def test_expected_record_id_with_config():
    rec = base_record()
    rec["dataset"]["config"] = "ARC-Challenge"
    assert expected_record_id(rec) == "example-org-mmlu-zz__zz__arc-challenge"


def test_completeness_partial():
    rec = base_record()
    # 5 of 6 known (human_verification unknown), none NA
    assert compute_completeness(rec) == round(5 / 6, 4)
    assert compute_state(rec) == "partial"
    assert unknown_dimensions(rec) == ["human_verification"]


def test_completeness_native_excludes_na():
    rec = base_record()
    rec["translation_type"] = "native_original"
    rec["engine_or_translator"] = "not_applicable"
    rec["human_verification"] = "not_applicable"
    rec["source_language"] = "not_applicable"
    rec["derived_from"] = {"kind": "modeled_on", "parent_id": "cais/mmlu"}
    rec["claims"]["engine_or_translator"] = {"status": "not_applicable", "evidence": []}
    rec["claims"]["human_verification"] = {"status": "not_applicable", "evidence": []}
    rec["claims"]["source_language"] = {"status": "not_applicable", "evidence": []}
    # applicable = 3 (type, license, derived_from), all known -> complete
    assert compute_completeness(rec) == 1.0
    assert compute_state(rec) == "complete"


def test_state_conflicting_takes_precedence():
    rec = base_record()
    rec["claims"]["engine_or_translator"]["status"] = "conflicting"
    rec["claims"]["engine_or_translator"]["conflicts"] = [
        {"value": "gpt-4", "evidence": ["e2"]}
    ]
    assert compute_state(rec) == "conflicting"
    # conflicting still counts as known
    assert compute_completeness(rec) == round(5 / 6, 4)


def test_state_minimal():
    rec = base_record()
    for dim in rec["claims"]:
        rec["claims"][dim] = {"status": "unknown", "evidence": []}
    assert compute_completeness(rec) == 0.0
    assert compute_state(rec) == "minimal"


def test_canonical_dumps_stable():
    rec = with_derived(base_record())
    a = canonical_dumps(rec)
    b = canonical_dumps(dict(reversed(list(rec.items()))))
    assert a == b  # key order irrelevant
    assert "\n" not in a

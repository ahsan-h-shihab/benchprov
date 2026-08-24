from conftest import REPO_ROOT, base_record, with_derived

import pytest

from benchprov.validate import Report, Validator


@pytest.fixture(scope="module")
def validator() -> Validator:
    return Validator(REPO_ROOT)


def errors_of(validator: Validator, rec: dict) -> list[str]:
    report = Report()
    validator.validate_record(rec, report)
    return [f.check for f in report.errors]


def test_valid_record_passes(validator, record):
    report = Report()
    validator.validate_record(record, report)
    assert report.ok, [str(f) for f in report.errors]


def test_missing_required_field(validator, record):
    del record["license"]
    assert "schema" in errors_of(validator, record)


def test_invalid_enum(validator, record):
    record["translation_type"] = "auto-magic"
    assert "schema" in errors_of(validator, record)


def test_bad_language_tag(validator, record):
    record["target_languages"] = ["kk_Cyrl"]  # underscore not allowed
    assert "schema" in errors_of(validator, record)


def test_malformed_url(validator, record):
    rec = with_derived(record)
    rec["evidence"][0]["url"] = "ftp://nope/readme"
    assert "url" in errors_of(validator, rec)


def test_record_id_mismatch(validator, record):
    record["record_id"] = "example-org-mmlu-zz__wrong"
    assert "record-id" in errors_of(validator, record)


def test_unknown_family(validator, record):
    record["root_benchmark"] = "NotAFamily"
    assert "family" in errors_of(validator, record)


def test_value_status_incoherence(validator, record):
    record["engine_or_translator"] = "unknown"  # claim still says verified
    assert "claim-coherence" in errors_of(validator, record)


def test_unknown_status_requires_unknown_value(validator, record):
    record["claims"]["translation_type"]["status"] = "unknown"
    record["claims"]["translation_type"]["evidence"] = []
    rec = with_derived(record)
    assert "claim-coherence" in errors_of(validator, rec)


def test_na_only_for_native(validator, record):
    record["engine_or_translator"] = "not_applicable"
    record["claims"]["engine_or_translator"] = {"status": "not_applicable", "evidence": []}
    rec = with_derived(record)  # translation_type is 'machine'
    assert "applicability" in errors_of(validator, rec)


def test_native_requires_na(validator, record):
    record["translation_type"] = "native_original"
    record["derived_from"] = {"kind": "modeled_on", "parent_id": None}
    record["source_language"] = "not_applicable"
    record["claims"]["source_language"] = {"status": "not_applicable", "evidence": []}
    rec = with_derived(record)  # engine/verification still concrete values
    errs = errors_of(validator, rec)
    assert "applicability" in errs


def test_source_language_na_rule(validator, record):
    record["source_language"] = "not_applicable"
    record["claims"]["source_language"] = {"status": "not_applicable", "evidence": []}
    rec = with_derived(record)  # kind is translation_of -> must be applicable
    assert "applicability" in errors_of(validator, rec)


def test_derived_none_with_parent(validator, record):
    record["derived_from"] = {"kind": "none", "parent_id": "cais/mmlu"}
    record["source_language"] = "not_applicable"
    record["claims"]["source_language"] = {"status": "not_applicable", "evidence": []}
    rec = with_derived(record)
    assert "derived-from" in errors_of(validator, rec)


def test_translation_of_requires_parent(validator, record):
    record["derived_from"] = {"kind": "translation_of", "parent_id": None}
    assert "derived-from" in errors_of(validator, record)


def test_verified_needs_evidence(validator, record):
    record["claims"]["license"]["evidence"] = []
    assert "evidence-required" in errors_of(validator, record)


def test_evidence_ref_must_exist(validator, record):
    record["claims"]["license"]["evidence"] = ["e99"]
    assert "evidence-ref" in errors_of(validator, record)


def test_verified_cannot_rest_on_name_only(validator, record):
    record["evidence"].append({
        "id": "e3", "type": "name_only",
        "url": "https://huggingface.co/datasets/example-org/mmlu-zz",
        "retrieved": "2026-08-19", "note": "dataset id contains 'mmlu-zz'",
    })
    record["claims"]["engine_or_translator"]["evidence"] = ["e3"]
    assert "evidence-strength" in errors_of(validator, record)


def test_name_only_cannot_cite_substantive(validator, record):
    record["claims"]["engine_or_translator"]["status"] = "name_only"
    # still cites e1 (a dataset_card)
    assert "evidence-strength" in errors_of(validator, record)


def test_conflicting_requires_conflicts(validator, record):
    record["claims"]["engine_or_translator"]["status"] = "conflicting"
    rec = with_derived(record)
    assert "conflict" in errors_of(validator, rec)


def test_conflict_value_must_differ(validator, record):
    record["claims"]["engine_or_translator"]["status"] = "conflicting"
    record["claims"]["engine_or_translator"]["conflicts"] = [
        {"value": "gpt-3.5-turbo", "evidence": ["e2"]}
    ]
    rec = with_derived(record)
    assert "conflict" in errors_of(validator, rec)


def test_conflicts_forbidden_without_status(validator, record):
    record["claims"]["engine_or_translator"]["conflicts"] = [
        {"value": "gpt-4", "evidence": ["e2"]}
    ]
    assert "conflict" in errors_of(validator, record)


def test_per_item_flags_requires_block(validator, record):
    record["human_verification"] = "per_item_flags"
    record["claims"]["human_verification"] = {"status": "verified", "evidence": ["e1"]}
    rec = with_derived(record)
    assert "per-item" in errors_of(validator, rec)


def test_native_vs_translation_kind_contradiction(validator, record):
    record["translation_type"] = "native_original"
    record["engine_or_translator"] = "not_applicable"
    record["human_verification"] = "not_applicable"
    record["claims"]["engine_or_translator"] = {"status": "not_applicable", "evidence": []}
    record["claims"]["human_verification"] = {"status": "not_applicable", "evidence": []}
    rec = with_derived(record)  # derived_from still translation_of
    assert "consistency" in errors_of(validator, rec)


def test_stale_completeness_detected(validator, record):
    record["completeness"] = 0.1234
    assert "completeness" in errors_of(validator, record)


def test_stale_state_detected(validator, record):
    record["provenance_state"] = "complete"
    assert "state" in errors_of(validator, record)


def test_validator_never_mutates(validator, record):
    import copy
    frozen = copy.deepcopy(record)
    record["completeness"] = 0.5  # invalid on purpose
    frozen["completeness"] = 0.5
    report = Report()
    validator.validate_record(record, report)
    assert record == frozen  # reported, not repaired


def test_duplicate_record_id_and_coverage(validator):
    a = base_record()
    b = base_record()  # same id, same coverage
    report = Report()
    validator.validate_collection([("a.json", a), ("b.json", b)], report)
    checks = [f.check for f in report.errors]
    assert "duplicate-id" in checks
    assert "duplicate-coverage" in checks


def test_same_dataset_different_language_ok(validator):
    a = base_record()
    b = base_record()
    b["target_languages"] = ["yy"]
    b["record_id"] = "example-org-mmlu-zz__yy"
    report = Report()
    validator.validate_collection([("a.json", a), ("b.json", b)], report)
    assert report.ok


def test_unpinned_evidence_warns_not_fails(validator, record):
    for e in record["evidence"]:
        e.pop("hub_revision", None)
        e.pop("sha256", None)
    report = Report()
    validator.validate_record(record, report)
    assert report.ok
    assert any(f.check == "evidence-unpinned" for f in report.warnings)

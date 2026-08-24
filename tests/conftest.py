from __future__ import annotations

import copy
from pathlib import Path

import pytest

from benchprov.model import compute_completeness, compute_state

REPO_ROOT = Path(__file__).resolve().parents[1]


def base_record() -> dict:
    """A structurally valid, fully coherent synthetic record."""
    rec = {
        "record_id": "example-org-mmlu-zz__zz",
        "schema_version": "0.1.0",
        "dataset": {
            "id": "example-org/mmlu-zz",
            "hub": "huggingface",
            "url": "https://huggingface.co/datasets/example-org/mmlu-zz",
            "revision": "0123456789abcdef",
        },
        "root_benchmark": "MMLU",
        "target_languages": ["zz"],
        "source_language": "en",
        "derived_from": {"kind": "translation_of", "parent_id": "cais/mmlu"},
        "translation_type": "machine",
        "engine_or_translator": "gpt-3.5-turbo",
        "human_verification": "unknown",
        "license": "mit",
        "claims": {
            "translation_type": {"status": "verified", "evidence": ["e1"]},
            "engine_or_translator": {"status": "verified", "evidence": ["e1"]},
            "human_verification": {"status": "unknown", "evidence": [],
                                   "note": "no statement found in card (checked)"},
            "license": {"status": "verified", "evidence": ["e2"]},
            "derived_from": {"status": "verified", "evidence": ["e1"]},
            "source_language": {"status": "verified", "evidence": ["e1"]},
        },
        "evidence": [
            {
                "id": "e1",
                "type": "dataset_card",
                "url": "https://huggingface.co/datasets/example-org/mmlu-zz/raw/0123456789abcdef/README.md",
                "retrieved": "2026-08-19",
                "quote": "ZZ version of MMLU translated by gpt-3.5-turbo.",
                "hub_revision": "0123456789abcdef",
            },
            {
                "id": "e2",
                "type": "hub_metadata",
                "url": "https://huggingface.co/api/datasets/example-org/mmlu-zz",
                "retrieved": "2026-08-19",
                "quote": "license: mit",
                "hub_revision": "0123456789abcdef",
            },
        ],
        "completeness": 0.0,
        "provenance_state": "partial",
        "curated": {"date": "2026-08-19", "by": "tests", "method": "manual"},
    }
    rec["completeness"] = compute_completeness(rec)
    rec["provenance_state"] = compute_state(rec)
    return rec


@pytest.fixture
def record() -> dict:
    return base_record()


def with_derived(rec: dict) -> dict:
    """Recompute stored derived fields after mutation (keeps a record coherent)."""
    rec = copy.deepcopy(rec)
    rec["completeness"] = compute_completeness(rec)
    rec["provenance_state"] = compute_state(rec)
    return rec

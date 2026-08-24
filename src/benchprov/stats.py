"""Registry statistics."""
from __future__ import annotations

from collections import Counter
from statistics import mean, median

from .model import CORE_DIMS


def registry_stats(records: list[dict]) -> dict:
    by_type = Counter(r["translation_type"] for r in records)
    by_verif = Counter(r["human_verification"] for r in records)
    by_state = Counter(r["provenance_state"] for r in records)
    by_family = Counter(r["root_benchmark"] for r in records)
    by_hub = Counter(r["dataset"]["hub"] for r in records)
    by_curation = Counter(r["curated"]["method"] for r in records)
    langs = Counter(lang for r in records for lang in r["target_languages"])
    completeness = [r["completeness"] for r in records]
    unknown_by_dim = Counter(
        dim for r in records for dim in CORE_DIMS if r["claims"][dim]["status"] == "unknown"
    )
    name_only_records = sum(
        1 for r in records if any(r["claims"][d]["status"] == "name_only" for d in CORE_DIMS)
    )
    pinned = sum(
        1 for r in records
        if any(e.get("hub_revision") or e.get("sha256") for e in r["evidence"])
    )
    engines = Counter(
        r["engine_or_translator"] for r in records
        if r["engine_or_translator"] not in ("unknown", "not_applicable")
    )
    return {
        "records": len(records),
        "datasets": len({r["dataset"]["id"] for r in records}),
        "languages": len(langs),
        "by_translation_type": dict(by_type.most_common()),
        "by_human_verification": dict(by_verif.most_common()),
        "by_provenance_state": dict(by_state.most_common()),
        "by_family": dict(by_family.most_common()),
        "by_hub": dict(by_hub.most_common()),
        "by_curation_method": dict(by_curation.most_common()),
        "top_languages": dict(langs.most_common(15)),
        "top_engines_or_translators": dict(engines.most_common(15)),
        "completeness": {
            "mean": round(mean(completeness), 4) if completeness else None,
            "median": round(median(completeness), 4) if completeness else None,
            "min": min(completeness) if completeness else None,
            "max": max(completeness) if completeness else None,
        },
        "unknown_by_dimension": dict(unknown_by_dim.most_common()),
        "records_with_name_only_claims": name_only_records,
        "records_with_pinned_evidence": pinned,
    }

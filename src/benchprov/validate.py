"""Deterministic validation of benchprov records.

Two layers:
1. JSON Schema (structure, enums, patterns) via `jsonschema`.
2. Cross-field rules the schema cannot express (value/status coherence,
   applicability, evidence integrity, derived-field recomputation) and
   registry-level rules (uniqueness, duplicates).

The validator only reports; it never repairs. ERRORs fail validation,
WARNs do not.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import jsonschema

from .model import (
    CORE_DIMS,
    KNOWN_STATUSES,
    PARENT_REQUIRED_KINDS,
    TRANSLATION_STEP_KINDS,
    compute_completeness,
    compute_state,
    expected_record_id,
    load_families,
    load_schema,
)

SENTINELS = ("unknown", "not_applicable")


@dataclass
class Finding:
    level: str          # "ERROR" | "WARN"
    where: str          # record id or file
    check: str          # short machine-usable check name
    message: str

    def __str__(self) -> str:  # pragma: no cover - formatting
        return f"{self.level:5s} [{self.check}] {self.where}: {self.message}"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def error(self, where: str, check: str, message: str) -> None:
        self.findings.append(Finding("ERROR", where, check, message))

    def warn(self, where: str, check: str, message: str) -> None:
        self.findings.append(Finding("WARN", where, check, message))

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "ERROR"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "WARN"]

    @property
    def ok(self) -> bool:
        return not self.errors


def _url_ok(url: str) -> bool:
    try:
        parts = urlparse(url)
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and bool(parts.netloc)


class Validator:
    def __init__(self, root: Path | None = None):
        self.schema = load_schema(root)
        self.families = load_families(root)
        self._checker = jsonschema.Draft202012Validator(self.schema)

    # ---------------------------------------------------------------- single record

    def validate_record(self, record: dict, report: Report, where: str | None = None) -> None:
        rid = where or str(record.get("record_id", "<no record_id>"))

        schema_errors = sorted(self._checker.iter_errors(record), key=lambda e: list(e.absolute_path))
        for err in schema_errors:
            loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
            report.error(rid, "schema", f"{loc}: {err.message}")
        if schema_errors:
            return  # cross-field checks assume a structurally valid record

        claims = record["claims"]
        evidence_ids = [e["id"] for e in record["evidence"]]

        # evidence ids unique
        if len(set(evidence_ids)) != len(evidence_ids):
            report.error(rid, "evidence-ids", "duplicate evidence ids")
        evidence_by_id = {e["id"]: e for e in record["evidence"]}

        # record_id matches identity
        expected = expected_record_id(record)
        if record["record_id"] != expected:
            report.error(rid, "record-id",
                         f"record_id does not match identity; expected '{expected}'")

        # root benchmark family known
        if record["root_benchmark"] not in self.families:
            report.error(rid, "family",
                         f"root_benchmark '{record['root_benchmark']}' not in registry/families.json")

        # URLs
        for url_field, url in [("dataset.url", record["dataset"]["url"])] + [
            (f"evidence[{e['id']}].url", e["url"]) for e in record["evidence"]
        ] + ([("derived_from.parent_url", record["derived_from"]["parent_url"])]
             if record["derived_from"].get("parent_url") else []):
            if not _url_ok(url):
                report.error(rid, "url", f"{url_field}: malformed URL '{url}'")

        # value/status coherence for the six core dimensions
        values = {
            "translation_type": record["translation_type"],
            "engine_or_translator": record["engine_or_translator"],
            "human_verification": record["human_verification"],
            "license": record["license"],
            "derived_from": record["derived_from"]["kind"],
            "source_language": record["source_language"],
        }
        for dim in CORE_DIMS:
            claim = claims[dim]
            status = claim["status"]
            value = values[dim]

            if status == "unknown" and value != "unknown":
                report.error(rid, "claim-coherence",
                             f"{dim}: status 'unknown' requires field value 'unknown' (got '{value}')")
            if value == "unknown" and status not in ("unknown", "conflicting"):
                report.error(rid, "claim-coherence",
                             f"{dim}: value 'unknown' requires status 'unknown' or 'conflicting' (got '{status}')")
            if status == "not_applicable" and value != "not_applicable":
                report.error(rid, "claim-coherence",
                             f"{dim}: status 'not_applicable' requires field value 'not_applicable'")
            if value == "not_applicable" and status != "not_applicable":
                report.error(rid, "claim-coherence",
                             f"{dim}: value 'not_applicable' requires status 'not_applicable'")
            if dim in ("translation_type", "license", "derived_from") and status == "not_applicable":
                report.error(rid, "claim-coherence", f"{dim}: may never be not_applicable")

            # evidence discipline per status
            refs = claim["evidence"]
            missing = [r for r in refs if r not in evidence_by_id]
            if missing:
                report.error(rid, "evidence-ref", f"{dim}: unknown evidence ids {missing}")
            if status in ("verified", "name_only") and not refs:
                report.error(rid, "evidence-required",
                             f"{dim}: status '{status}' requires at least one evidence reference")
            if status == "verified" and refs and all(
                evidence_by_id[r]["type"] == "name_only" for r in refs if r in evidence_by_id
            ):
                report.error(rid, "evidence-strength",
                             f"{dim}: status 'verified' cited only name_only evidence; use status 'name_only'")
            if status == "name_only" and refs and any(
                evidence_by_id[r]["type"] != "name_only" for r in refs if r in evidence_by_id
            ):
                report.error(rid, "evidence-strength",
                             f"{dim}: status 'name_only' cites substantive evidence; use status 'verified'")

            conflicts = claim.get("conflicts")
            if status == "conflicting":
                if not conflicts:
                    report.error(rid, "conflict", f"{dim}: status 'conflicting' requires non-empty conflicts[]")
                if not refs and value != "unknown":
                    report.error(rid, "conflict",
                                 f"{dim}: conflicting with a primary value requires evidence for that value")
            elif conflicts:
                report.error(rid, "conflict", f"{dim}: conflicts[] present but status is '{status}'")
            if conflicts:
                for i, c in enumerate(conflicts):
                    bad = [r for r in c["evidence"] if r not in evidence_by_id]
                    if bad:
                        report.error(rid, "evidence-ref", f"{dim}.conflicts[{i}]: unknown evidence ids {bad}")
                    if c["value"] == value:
                        report.error(rid, "conflict",
                                     f"{dim}.conflicts[{i}]: conflict value equals primary value")

        # applicability rules
        tt = record["translation_type"]
        if tt == "native_original":
            for dim in ("engine_or_translator", "human_verification"):
                if claims[dim]["status"] != "not_applicable":
                    report.error(rid, "applicability",
                                 f"{dim}: must be not_applicable when translation_type is native_original")
        else:
            for dim in ("engine_or_translator", "human_verification"):
                if claims[dim]["status"] == "not_applicable":
                    report.error(rid, "applicability",
                                 f"{dim}: not_applicable only allowed for native_original records")

        kind = record["derived_from"]["kind"]
        src_lang_status = claims["source_language"]["status"]
        if kind in TRANSLATION_STEP_KINDS and src_lang_status == "not_applicable":
            report.error(rid, "applicability",
                         f"source_language: applicable for derived_from.kind '{kind}'")
        if kind not in TRANSLATION_STEP_KINDS and record["source_language"] != "not_applicable":
            report.error(rid, "applicability",
                         f"source_language: must be not_applicable for derived_from.kind '{kind}'")

        # derived_from structure
        parent = record["derived_from"]["parent_id"]
        if kind == "none" and parent is not None:
            report.error(rid, "derived-from", "kind 'none' requires parent_id null")
        if kind in PARENT_REQUIRED_KINDS and parent is None:
            report.error(rid, "derived-from", f"kind '{kind}' requires a parent_id")

        # per-item flags
        if record["human_verification"] == "per_item_flags" and "per_item_provenance" not in record:
            report.error(rid, "per-item", "human_verification 'per_item_flags' requires per_item_provenance")

        # translation_type native_original must not be a translation step
        if tt == "native_original" and kind in TRANSLATION_STEP_KINDS:
            report.error(rid, "consistency",
                         f"native_original contradicts derived_from.kind '{kind}'")
        if tt == "script_conversion" and kind not in ("script_conversion_of", "unknown"):
            report.error(rid, "consistency",
                         f"translation_type script_conversion expects derived_from.kind 'script_conversion_of' (got '{kind}')")

        # stored derived fields must equal recomputation
        comp = compute_completeness(record)
        if record["completeness"] != comp:
            report.error(rid, "completeness",
                         f"stored completeness {record['completeness']} != computed {comp}")
        state = compute_state(record)
        if record["provenance_state"] != state:
            report.error(rid, "state", f"stored provenance_state '{record['provenance_state']}' != computed '{state}'")

        # warnings
        used = set()
        for dim in CORE_DIMS:
            used.update(claims[dim]["evidence"])
            for c in claims[dim].get("conflicts", []) or []:
                used.update(c["evidence"])
        unused = [e for e in evidence_ids if e not in used]
        if unused:
            report.warn(rid, "evidence-unused", f"evidence never referenced by a claim: {unused}")
        for e in record["evidence"]:
            if e["type"] in ("dataset_card", "hub_metadata") and "hub_revision" not in e and "sha256" not in e:
                report.warn(rid, "evidence-unpinned",
                            f"evidence {e['id']} is not revision-pinned (no hub_revision/sha256)")

    # ---------------------------------------------------------------- collections

    def validate_collection(self, records: list[tuple[str, dict]], report: Report) -> None:
        """Cross-record rules over (where, record) pairs that passed (or will be
        run through) validate_record."""
        seen_rids: dict[str, str] = {}
        seen_keys: dict[tuple, str] = {}
        for where, rec in records:
            rid = rec.get("record_id")
            if not isinstance(rid, str):
                continue
            if rid in seen_rids:
                report.error(where, "duplicate-id", f"record_id '{rid}' already used in {seen_rids[rid]}")
            else:
                seen_rids[rid] = where
            ds = rec.get("dataset", {})
            for lang in rec.get("target_languages", []) or []:
                key = (ds.get("id"), ds.get("config"), lang)
                if key in seen_keys:
                    report.error(where, "duplicate-coverage",
                                 f"(dataset={key[0]!r}, config={key[1]!r}, language={key[2]!r}) already covered by {seen_keys[key]}")
                else:
                    seen_keys[key] = rid

    def validate_all(self, records: list[tuple[str, dict]]) -> Report:
        report = Report()
        for where, rec in records:
            self.validate_record(rec, report, where=where)
        self.validate_collection(records, report)
        return report

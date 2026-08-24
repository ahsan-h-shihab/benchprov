"""Build the generated registry from curated source records.

sources/records/*.json  (curated truth)  ->  registry/provenance.jsonl (generated)

The build refuses to write anything if validation reports errors.
Output is deterministic: records sorted by record_id, canonical JSON lines.
"""
from __future__ import annotations

from pathlib import Path

from .model import canonical_dumps, load_sources
from .validate import Report, Validator

REGISTRY_REL = Path("registry") / "provenance.jsonl"


def build_registry_text(root: Path, report: Report | None = None) -> str | None:
    """Validate sources and return the registry file content, or None on errors."""
    report = report if report is not None else Report()
    sources = load_sources(root)
    pairs = [(str(path.relative_to(root)), rec) for path, rec in sources.values()]
    validator = Validator(root)
    for where, rec in pairs:
        validator.validate_record(rec, report, where=where)
    validator.validate_collection(pairs, report)

    # one source file per record, named after the record_id
    for stem, (path, rec) in sources.items():
        rid = rec.get("record_id")
        if isinstance(rid, str) and stem != rid:
            report.error(str(path.relative_to(root)), "filename",
                         f"source file name '{stem}.json' must equal record_id '{rid}'")

    if not report.ok:
        return None
    ordered = sorted((rec for _, rec in pairs), key=lambda r: r["record_id"])
    return "".join(canonical_dumps(r) + "\n" for r in ordered)


def build(root: Path, check_only: bool = False) -> tuple[Report, bool]:
    """Build (or verify) the registry. Returns (report, changed_or_mismatch)."""
    report = Report()
    text = build_registry_text(root, report)
    if text is None:
        return report, False
    out = root / REGISTRY_REL
    current = out.read_text(encoding="utf-8") if out.exists() else None
    if check_only:
        if current != text:
            report.error(str(REGISTRY_REL), "registry-stale",
                         "registry/provenance.jsonl does not match a rebuild from sources/records "
                         "(run 'benchprov build')")
            return report, True
        return report, False
    if current == text:
        return report, False
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")
    return report, True

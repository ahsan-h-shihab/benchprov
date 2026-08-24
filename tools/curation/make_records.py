"""Authoring scaffolding: expand compact curated judgments into full schema
records under sources/records/.

The compact form (see seed_batch_*.py) is where the curator's judgment lives;
this script only mechanizes boilerplate: it pulls pinned evidence anchors
(revision sha, pinned README URL, sha256, retrieval date, hub license tag)
from evidence/snapshots/, assembles evidence items, computes claim statuses
from the cited evidence kinds, and computes completeness/provenance_state via
the same functions the validator uses.

It NEVER invents values: every field value and quote is passed in explicitly
by the curator. Records it writes are then the canonical sources; this script
is not needed to consume the registry.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from benchprov.model import (  # noqa: E402
    compute_completeness,
    compute_state,
    expected_record_id,
    slugify,
)

SNAPDIR = ROOT / "evidence" / "snapshots"
OUTDIR = ROOT / "sources" / "records"

CURATED_BY = "benchprov v0 seed (A. H. Shihab)"
CURATED_METHOD = "assisted"


def load_snapshot(ds_id: str) -> dict:
    p = SNAPDIR / f"{slugify(ds_id)}.json"
    if not p.exists():
        raise FileNotFoundError(f"no evidence snapshot for {ds_id}; run tools/fetch_evidence.py first")
    return json.loads(p.read_text(encoding="utf-8"))


class RecordBuilder:
    """Assemble one record from curator inputs + snapshot anchors."""

    def __init__(self, spec: dict):
        self.spec = spec
        self.snap = load_snapshot(spec["ds"]) if spec.get("hub", "huggingface") == "huggingface" else None
        self.evidence: list[dict] = []
        self._by_key: dict[str, str] = {}

    # -------------------------------------------------- evidence assembly

    def _add(self, key: str, item: dict) -> str:
        eid = f"e{len(self.evidence) + 1}"
        item = {"id": eid, **item}
        self.evidence.append(item)
        self._by_key[key] = eid
        return eid

    def _ensure(self, key: str) -> str:
        if key in self._by_key:
            return self._by_key[key]
        s = self.spec
        snap = self.snap
        retrieved = (snap or {}).get("retrieved") or s.get("retrieved") or "2026-08-19"
        if key == "card":
            if not snap or "readme" not in snap or snap["readme"].get("error"):
                raise ValueError(f"{s['ds']}: no fetched card to cite")
            item = {
                "type": "dataset_card",
                "url": snap["readme"]["pinned_url"],
                "retrieved": retrieved,
                "sha256": snap["readme"]["sha256"],
                "hub_revision": snap["revision"],
            }
            if s.get("card_quote"):
                item["quote"] = s["card_quote"]
            if s.get("card_note"):
                item["note"] = s["card_note"]
            return self._add(key, item)
        if key == "card2":  # a second quote from the same card
            if not snap:
                raise ValueError("card2 needs a snapshot")
            item = {
                "type": "dataset_card",
                "url": snap["readme"]["pinned_url"],
                "retrieved": retrieved,
                "sha256": snap["readme"]["sha256"],
                "hub_revision": snap["revision"],
                "quote": s["card2_quote"],
            }
            if s.get("card2_note"):
                item["note"] = s["card2_note"]
            return self._add(key, item)
        if key == "meta":
            if not snap:
                raise ValueError("meta needs a snapshot")
            hm = snap.get("hub_metadata", {})
            lic = hm.get("cardData_license")
            item = {
                "type": "hub_metadata",
                "url": f"https://huggingface.co/api/datasets/{s['ds']}",
                "retrieved": retrieved,
                "hub_revision": snap["revision"],
                "quote": f"license: {json.dumps(lic) if not isinstance(lic, str) else lic}",
            }
            return self._add(key, item)
        if key == "meta_tags":
            # meta_tags evidence summarizes structured hub metadata; the
            # summary is descriptive, NOT verbatim, so it lives in `note`
            # (the quote field is reserved for verbatim excerpts).
            if not snap:
                raise ValueError("meta_tags needs a snapshot")
            desc = s.get("meta_tags_quote", "")
            note = s.get("meta_tags_note", "")
            joined = "; ".join(x for x in (desc, note) if x) or "hub metadata tags"
            item = {
                "type": "hub_metadata",
                "url": f"https://huggingface.co/api/datasets/{s['ds']}",
                "retrieved": retrieved,
                "hub_revision": snap["revision"],
                "note": joined[:500],
            }
            return self._add(key, item)
        if key == "paper":
            item = {
                "type": "paper",
                "url": s["paper_url"],
                "retrieved": retrieved,
            }
            if s.get("paper_quote"):
                item["quote"] = s["paper_quote"]
            if s.get("paper_note"):
                item["note"] = s["paper_note"]
            return self._add(key, item)
        if key == "name":
            item = {
                "type": "name_only",
                "url": s.get("ds_url") or f"https://huggingface.co/datasets/{s['ds']}",
                "retrieved": retrieved,
                "note": s.get("name_note", f"dataset id: {s['ds']}"),
            }
            return self._add(key, item)
        if key == "content":
            item = {
                "type": "dataset_content",
                "url": s["content_url"],
                "retrieved": retrieved,
            }
            if s.get("content_quote"):
                item["quote"] = s["content_quote"]
            if s.get("content_note"):
                item["note"] = s["content_note"]
            return self._add(key, item)
        if key == "ext":
            item = {
                "type": "external_page",
                "url": s["ext_url"],
                "retrieved": retrieved,
            }
            if s.get("ext_quote"):
                item["quote"] = s["ext_quote"]
            if s.get("ext_note"):
                item["note"] = s["ext_note"]
            return self._add(key, item)
        raise KeyError(f"unknown evidence key: {key}")

    def _claim(self, value_is_unknown: bool, value_is_na: bool, ev_keys: list[str] | None,
               note: str | None = None, conflicts: list[dict] | None = None) -> dict:
        refs = [self._ensure(k) for k in (ev_keys or [])]
        if value_is_na:
            status = "not_applicable"
        elif conflicts:
            status = "conflicting"
        elif value_is_unknown:
            status = "unknown"
        else:
            kinds = {next(e["type"] for e in self.evidence if e["id"] == r) for r in refs}
            status = "name_only" if kinds and kinds <= {"name_only"} else "verified"
        claim: dict = {"status": status, "evidence": refs}
        if conflicts:
            claim["conflicts"] = [
                {"value": c["value"], "evidence": [self._ensure(k) for k in c["ev"]],
                 **({"note": c["note"]} if c.get("note") else {})}
                for c in conflicts
            ]
        if note:
            claim["note"] = note
        return claim

    # -------------------------------------------------- record assembly

    def build(self) -> dict:
        s = self.spec
        snap = self.snap
        hub = s.get("hub", "huggingface")
        url = s.get("ds_url") or (f"https://huggingface.co/datasets/{s['ds']}" if hub == "huggingface" else None)
        if url is None:
            raise ValueError("non-HF records need ds_url")
        revision = (snap or {}).get("revision") or s.get("revision") or "unknown"

        tt = s["tt"]
        engine = s.get("engine", "unknown")
        verif = s.get("verif", "unknown")
        kind = s["kind"]
        src = s.get("src", "unknown")
        if tt == "native_original":
            engine = "not_applicable"
            verif = "not_applicable"
        if kind not in ("translation_of", "script_conversion_of"):
            src = "not_applicable"

        rec: dict = {
            "record_id": "placeholder",
            "schema_version": "0.1.0",
            "dataset": {"id": s["ds"], "hub": hub, "url": url, "revision": revision},
            "root_benchmark": s["family"],
            "target_languages": s["langs"],
            "source_language": src,
            "derived_from": {"kind": kind, "parent_id": s.get("parent")},
            "translation_type": tt,
            "engine_or_translator": engine,
            "human_verification": verif,
            "license": s.get("license", "unknown"),
            "claims": {},
            "evidence": [],
            "completeness": 0.0,
            "provenance_state": "partial",
            "curated": {"date": (snap or {}).get("retrieved") or "2026-08-19",
                        "by": CURATED_BY, "method": CURATED_METHOD},
        }
        if s.get("config"):
            rec["dataset"]["config"] = s["config"]
        if s.get("parent_url"):
            rec["derived_from"]["parent_url"] = s["parent_url"]
        if s.get("per_item"):
            rec["per_item_provenance"] = s["per_item"]
        if s.get("notes"):
            rec["notes"] = s["notes"]

        rec["claims"]["translation_type"] = self._claim(
            tt == "unknown", False, s.get("tt_ev"), s.get("tt_note"), s.get("tt_conflicts"))
        rec["claims"]["engine_or_translator"] = self._claim(
            engine == "unknown", engine == "not_applicable", s.get("engine_ev"),
            s.get("engine_note"), s.get("engine_conflicts"))
        rec["claims"]["human_verification"] = self._claim(
            verif == "unknown", verif == "not_applicable", s.get("verif_ev"),
            s.get("verif_note"), s.get("verif_conflicts"))
        rec["claims"]["license"] = self._claim(
            s.get("license", "unknown") == "unknown", False, s.get("license_ev"),
            s.get("license_note"), s.get("license_conflicts"))
        rec["claims"]["derived_from"] = self._claim(
            kind == "unknown", False, s.get("kind_ev"), s.get("kind_note"))
        rec["claims"]["source_language"] = self._claim(
            src == "unknown", src == "not_applicable", s.get("src_ev"), s.get("src_note"))

        rec["evidence"] = self.evidence
        rec["record_id"] = expected_record_id(rec)
        rec["completeness"] = compute_completeness(rec)
        rec["provenance_state"] = compute_state(rec)
        return rec


def write_records(specs: list[dict]) -> list[str]:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    written = []
    for spec in specs:
        rec = RecordBuilder(spec).build()
        path = OUTDIR / f"{rec['record_id']}.json"
        path.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(rec["record_id"])
        print("wrote", path.name)
    return written

"""Data model constants, path resolution, record IO, and deterministic
derivations (record ids, completeness, provenance state, canonical JSON)."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

CORE_DIMS = (
    "translation_type",
    "engine_or_translator",
    "human_verification",
    "license",
    "derived_from",
    "source_language",
)

KNOWN_STATUSES = ("verified", "name_only", "conflicting")

# Dimensions whose *field value* may carry the given sentinel.
NA_CAPABLE_FIELDS = ("engine_or_translator", "human_verification", "source_language")

TRANSLATION_STEP_KINDS = ("translation_of", "script_conversion_of")
PARENT_REQUIRED_KINDS = ("translation_of", "script_conversion_of", "subset_or_filter_of")


# --------------------------------------------------------------------------- paths

def find_repo_root(start: Path | None = None) -> Path | None:
    """Walk upward looking for a benchprov data root (schema/ + sources/)."""
    env = os.environ.get("BENCHPROV_ROOT")
    if env:
        p = Path(env)
        if (p / "schema" / "provenance.schema.json").is_file():
            return p
    cur = (start or Path.cwd()).resolve()
    for cand in (cur, *cur.parents):
        if (cand / "schema" / "provenance.schema.json").is_file() and (cand / "sources").is_dir():
            return cand
    return None


def _packaged(name: str) -> Path:
    return Path(__file__).parent / "_data" / name


def schema_path(root: Path | None = None) -> Path:
    root = root or find_repo_root()
    if root is not None:
        return root / "schema" / "provenance.schema.json"
    return _packaged("provenance.schema.json")


def families_path(root: Path | None = None) -> Path:
    root = root or find_repo_root()
    if root is not None:
        return root / "registry" / "families.json"
    return _packaged("families.json")


def load_schema(root: Path | None = None) -> dict:
    return json.loads(schema_path(root).read_text(encoding="utf-8"))


def load_families(root: Path | None = None) -> dict:
    data = json.loads(families_path(root).read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


# --------------------------------------------------------------------------- ids

def slugify(identifier: str) -> str:
    """Dataset id -> record-id component. Deterministic, lossy."""
    return re.sub(r"[^a-z0-9._-]", "-", identifier.lower())


def language_part(target_languages: list[str]) -> str:
    if len(target_languages) >= 4:
        return "multi"
    return "-".join(t.lower() for t in target_languages)


def expected_record_id(record: dict) -> str:
    ds = record.get("dataset", {})
    parts = [slugify(str(ds.get("id", ""))), language_part(list(record.get("target_languages", [])))]
    if ds.get("config"):
        parts.append(slugify(str(ds["config"])))
    return "__".join(parts)


# --------------------------------------------------------------------------- derived facts

def compute_completeness(record: dict) -> float:
    claims = record.get("claims", {})
    na = sum(1 for d in CORE_DIMS if claims.get(d, {}).get("status") == "not_applicable")
    known = sum(1 for d in CORE_DIMS if claims.get(d, {}).get("status") in KNOWN_STATUSES)
    applicable = len(CORE_DIMS) - na
    if applicable <= 0:
        return 0.0
    return round(known / applicable, 4)


def compute_state(record: dict) -> str:
    claims = record.get("claims", {})
    if any(claims.get(d, {}).get("status") == "conflicting" for d in CORE_DIMS):
        return "conflicting"
    c = compute_completeness(record)
    if c == 1.0:
        return "complete"
    if c == 0.0:
        return "minimal"
    return "partial"


def unknown_dimensions(record: dict) -> list[str]:
    claims = record.get("claims", {})
    return [d for d in CORE_DIMS if claims.get(d, {}).get("status") == "unknown"]


# --------------------------------------------------------------------------- io

def canonical_dumps(record: dict) -> str:
    """Canonical single-line JSON used for the generated registry."""
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_record_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_sources(root: Path) -> dict[str, tuple[Path, dict]]:
    """All curated source records, keyed by filename stem. Raises on JSON errors."""
    out: dict[str, tuple[Path, dict]] = {}
    for p in sorted((root / "sources" / "records").glob("*.json")):
        out[p.stem] = (p, load_record_file(p))
    return out


def load_registry(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{i}: invalid JSON line: {exc}") from exc
    return records

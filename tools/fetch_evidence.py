"""Fetch pinned evidence snapshots for Hugging Face datasets.

For each dataset id:
  - resolve the current revision sha via the HF API,
  - fetch README.md at that pinned revision,
  - record sha256 of the bytes, the YAML front matter, and candidate
    provenance-relevant lines (translation / engine / human keywords),
  - write evidence/snapshots/<slug>.json.

Snapshots are RAW EVIDENCE for curators. They are not records and are never
consumed by the validator; curated records cite the pinned URLs captured here.

Usage:
  python tools/fetch_evidence.py <dataset_id> [<dataset_id> ...]
  python tools/fetch_evidence.py --file ids.txt
Requires: requests (pip install benchprov[fetch]).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
SNAPDIR = ROOT / "evidence" / "snapshots"

KEYWORDS = re.compile(
    r"(translat|übersetz|перевод|переклад|çevir|অনুবাদ|tarjima|аударма|"
    r"machine[- ]?translat|human[- ]?translat|post[- ]?edit|professional|native speaker|"
    r"annotat|verif|review|crowd|"
    r"gpt-?[345o]|chatgpt|deepl|google translate|googletrans|nllb|opus-mt|marian|m2m100|"
    r"madlad|seamless|tower|aya|claude|gemini|yandex|azure translat|opencc|llama|qwen|deepseek|"
    r"synthetic|generated|adapted|localiz)",
    re.IGNORECASE,
)


def slugify(identifier: str) -> str:
    return re.sub(r"[^a-z0-9._-]", "-", identifier.lower())


def fetch_dataset(ds_id: str, session: requests.Session) -> dict:
    ts = dt.datetime.now(dt.timezone.utc)
    out: dict = {"dataset_id": ds_id, "retrieved": ts.strftime("%Y-%m-%d"),
                 "retrieved_at": ts.isoformat()}
    api = session.get(f"https://huggingface.co/api/datasets/{ds_id}", timeout=40)
    if api.status_code != 200:
        out["error"] = f"api HTTP {api.status_code}"
        return out
    meta = api.json()
    sha = meta.get("sha")
    out["revision"] = sha
    out["hub_metadata"] = {
        "tags": meta.get("tags", []),
        "cardData_license": (meta.get("cardData") or {}).get("license"),
        "cardData_language": (meta.get("cardData") or {}).get("language"),
        "cardData_source_datasets": (meta.get("cardData") or {}).get("source_datasets"),
        "cardData_annotations_creators": (meta.get("cardData") or {}).get("annotations_creators"),
        "downloads": meta.get("downloads"),
        "lastModified": meta.get("lastModified"),
        "gated": meta.get("gated"),
    }
    raw_url = f"https://huggingface.co/datasets/{ds_id}/raw/{sha}/README.md"
    readme = session.get(raw_url, timeout=40)
    if readme.status_code == 200:
        body = readme.content
        text = body.decode("utf-8", errors="replace")
        out["readme"] = {
            "pinned_url": raw_url,
            "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body),
        }
        m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
        if m:
            out["readme"]["yaml_front_matter"] = m.group(1)[:4000]
        prose = text[m.end():] if m else text
        hits, seen = [], set()
        for line in prose.splitlines():
            s = line.strip()
            if not s or len(s) < 8:
                continue
            if KEYWORDS.search(s):
                key = s[:80]
                if key not in seen:
                    seen.add(key)
                    hits.append(s[:400])
            if len(hits) >= 40:
                break
        out["readme"]["provenance_candidate_lines"] = hits
        links = re.findall(r"https?://(?:arxiv\.org|aclanthology\.org|github\.com)[^\s)\">\]]*", text)
        out["readme"]["reference_links"] = list(dict.fromkeys(links))[:10]
    else:
        out["readme"] = {"error": f"README HTTP {readme.status_code}", "pinned_url": raw_url}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--file", help="text file with one dataset id per line")
    ap.add_argument("--force", action="store_true", help="refetch even if a snapshot exists")
    args = ap.parse_args()
    ids = list(args.ids)
    if args.file:
        ids += [l.strip() for l in Path(args.file).read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.strip().startswith("#")]
    if not ids:
        ap.error("no dataset ids given")
    SNAPDIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "benchprov-fetch/0.1"
    ok = 0
    for i, ds in enumerate(ids, 1):
        path = SNAPDIR / f"{slugify(ds)}.json"
        if path.exists() and not args.force:
            print(f"[{i}/{len(ids)}] skip (exists): {ds}")
            ok += 1
            continue
        snap = fetch_dataset(ds, session)
        path.write_text(json.dumps(snap, indent=1, ensure_ascii=False), encoding="utf-8")
        status = snap.get("error") or f"rev {str(snap.get('revision'))[:10]} " \
                                      f"{len((snap.get('readme') or {}).get('provenance_candidate_lines', []))} candidate lines"
        print(f"[{i}/{len(ids)}] {ds}: {status}")
        if "error" not in snap:
            ok += 1
        time.sleep(0.6)
    print(f"done: {ok}/{len(ids)} snapshots")
    return 0 if ok == len(ids) else 1


if __name__ == "__main__":
    sys.exit(main())

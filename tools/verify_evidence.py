"""Re-verify the registry's evidence against its sources.

For every evidence item in every record:
  - re-fetch revision-pinned Hugging Face URLs (raw READMEs, API endpoints),
  - check the recorded sha256 still matches the fetched bytes (pinned URLs
    are immutable, so a mismatch means a recording error),
  - check each recorded quote still appears verbatim in the fetched document
    (whitespace-normalized; bracketed ellipses/completions in quotes are
    treated as wildcards),
  - report, never repair.

Unpinned URLs (papers, external pages, GitHub files) are fetched and
quote-checked only; their content may legitimately drift, so failures there
are reported as WARN rather than ERROR unless --strict.

Usage: python tools/verify_evidence.py [--limit N] [--strict] [--only RECORD_ID]
Requires: requests. Network access required. Exit 0 = no errors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from benchprov.model import load_registry  # noqa: E402

H = {"User-Agent": "benchprov-verify/0.1"}


def norm(text: str) -> str:
    """Normalize to RENDERED text for matching: quotes cite what a reader of
    the card sees, so standard Markdown mechanics are normalized away on both
    sides — inline links become their text, backslash-escapes are unescaped,
    emphasis/code markers are dropped. Content words must still match exactly."""
    text = re.sub(r"\[([^\]]*)\]\s*\((?:[^)]*)\)", r"\1", text)  # [text](url) -> text
    text = re.sub(r"\\([_*`#\[\]])", r"\1", text)             # \_ -> _
    text = text.replace("*", "").replace("`", "")
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", text).strip()


def quote_pattern(quote: str) -> re.Pattern:
    """Rendered-verbatim match; [...] / [text] inside a QUOTE act as wildcards
    (used for elisions), so normalize link syntax before splitting."""
    quote = re.sub(r"\[([^\]]*)\]\s*\((?:[^)]*)\)", r"\1", quote)
    parts = re.split(r"\[[^\]]*\]", quote)
    rx = r"\s*.*?\s*".join(re.escape(norm(p)) for p in parts if norm(p))
    rx = rx.replace(r"\ ", r"\s*")
    return re.compile(rx, re.IGNORECASE)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="verify only the first N records")
    ap.add_argument("--only", help="verify a single record id")
    ap.add_argument("--strict", action="store_true",
                    help="treat unpinned-quote drift as ERROR instead of WARN")
    args = ap.parse_args()

    records = load_registry(ROOT / "registry" / "provenance.jsonl")
    if args.only:
        records = [r for r in records if r["record_id"] == args.only]
    if args.limit:
        records = records[: args.limit]

    session = requests.Session()
    session.headers.update(H)
    cache: dict[str, tuple[int, bytes]] = {}
    errors = warns = checked = 0

    def fetch(url: str) -> tuple[int, bytes]:
        if url not in cache:
            try:
                r = session.get(url, timeout=40)
                cache[url] = (r.status_code, r.content)
            except requests.RequestException as exc:
                cache[url] = (-1, str(exc).encode())
            time.sleep(0.4)
        return cache[url]

    for rec in records:
        for ev in rec["evidence"]:
            if ev["type"] == "name_only":
                continue  # the dataset id itself is the evidence
            checked += 1
            pinned = bool(ev.get("sha256"))
            status, body = fetch(ev["url"])
            where = f"{rec['record_id']}/{ev['id']}"
            if status != 200:
                gated = "gated" in (rec.get("notes") or "").lower() or status in (401, 403)
                if gated:
                    warns += 1
                    print(f"WARN  {where}: HTTP {status} (gated or restricted URL) {ev['url']}")
                else:
                    errors += 1
                    print(f"ERROR {where}: HTTP {status} fetching {ev['url']}")
                continue
            if pinned:
                digest = hashlib.sha256(body).hexdigest()
                if digest != ev["sha256"]:
                    errors += 1
                    print(f"ERROR {where}: sha256 mismatch at pinned URL {ev['url']}")
                    continue
            if ev.get("quote"):
                text = norm(re.sub(r"<[^<>]{0,120}>", " ", body.decode("utf-8", errors="replace")))
                if not quote_pattern(ev["quote"]).search(text):
                    if pinned or args.strict:
                        errors += 1
                        print(f"ERROR {where}: quote not found at {ev['url']}\n      \"{ev['quote'][:120]}\"")
                    else:
                        warns += 1
                        print(f"WARN  {where}: quote not found (unpinned source may have drifted) {ev['url']}")

    print(f"\nchecked {checked} evidence items across {len(records)} records: "
          f"{errors} error(s), {warns} warning(s)")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

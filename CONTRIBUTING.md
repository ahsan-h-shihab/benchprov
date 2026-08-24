# Contributing a provenance record

A record answers, with evidence: *how did this benchmark dataset's
target-language items come to be?* Adding one takes about 20 minutes.

## 1. Gather evidence

```bash
pip install -e ".[fetch]"
python tools/fetch_evidence.py your-org/your-dataset
```

This writes `evidence/snapshots/<slug>.json` with the dataset's current
revision sha, the pinned README URL, its SHA-256, the hub metadata, and
candidate provenance lines. Read the actual card (and at most the paper it
links) before filling anything.

## 2. Write the record

Create `sources/records/<record_id>.json` (the file name must equal the
`record_id`). Start from any existing record as a template, or from
[`docs/schema.md`](docs/schema.md). Ground rules:

- **Never infer.** No engine, translator, verification status, version, or
  license may be filled without evidence you can cite. `unknown` is a fully
  respectable value — it is the point of the registry.
- **Silence is `unknown`, not `none`.** `human_verification: none` requires
  the creators' own account of an automated-only pipeline.
- **Cite pinned URLs.** Use the `.../raw/<sha>/README.md` URL from the
  snapshot, plus `hub_revision`, so your evidence cannot drift.
- **Quote minimally.** ≤300 characters, verbatim, just enough to carry the
  fact.
- **Preserve conflicts.** If two sources disagree, use claim status
  `conflicting` and record both positions with their evidence.
- If provenance differs per language or config, split into multiple records.
- Leave `completeness` / `provenance_state` as your best computation; the
  validator recomputes and will tell you the exact expected values.

## 3. Validate and build

```bash
benchprov validate sources/records/<record_id>.json   # single record
benchprov build                                       # regenerate registry
benchprov validate                                    # whole repository
python -m pytest -q                                   # tests still green
```

Commit both the source record and the regenerated
`registry/provenance.jsonl` (plus the evidence snapshot).

## Adding a new benchmark family

Add a key to `registry/families.json` (and mirror it to
`src/benchprov/_data/families.json` — a test enforces the two stay in sync)
with the family's origin dataset. Records referencing an unknown family fail
validation.

## What is out of scope

Quality judgments, benchmark scores, license interpretation, and any claim
not traceable to evidence.

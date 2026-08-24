# benchprov v0.1 — implementation report (2026-08-24)

Build phase of the validated Project-02 survivor ("Benchmark Translation
Provenance"). Stopping rule met; no external outreach, PRs, or submissions
were made. Repository: this repository (local git, branch `main`; no remote
configured). **Note:** this report describes the v0.1 build as completed and
predates the adversarial pre-release audit; see `docs/PRE_RELEASE_AUDIT.md`
(including its resolution section) for corrections applied afterwards —
figures below reflect the pre-audit state.

## 1. What was built

- **Frozen data model** (`schema/provenance.schema.json`, v0.1.0): one record
  per dataset/config/language-group derivation step; six evidence-bound core
  dimensions (translation_type, engine_or_translator, human_verification,
  license, derived_from, source_language); controlled vocabularies for
  translation type (8 values), verification (6), evidence type (7), claim
  status (5), provenance state (4); deterministic completeness
  (known/applicable over core claims) and derived state, both stored AND
  recomputed. Prose reference in `docs/schema.md`; 14 design decisions in
  `docs/DESIGN_DECISIONS.md` (incl. the MTEB `sample_creation` interop
  mapping).
- **Seed registry**: 104 records / 100 datasets / 81 languages,
  `registry/provenance.jsonl` (generated, sorted, canonical JSON lines) built
  from `sources/records/*.json` (curated truth, one file per record).
  207 evidence items, 98 records with revision-pinned + SHA-256-hashed
  evidence; short verbatim quotes throughout.
- **Validator** (`benchprov validate`): JSON-Schema layer + 20+ cross-field
  rules (value↔status coherence, applicability, evidence discipline incl.
  name_only demotion, conflict preservation, per-item flags, derivation
  constraints, duplicate ids and (dataset, config, language) coverage,
  completeness/state recomputation, family membership, URL well-formedness,
  registry staleness). Reports, never repairs.
- **CLI**: `benchprov inspect | validate | stats | build [--check]`, all with
  `--json`; inspect renders a researcher-facing card (machine translated? by
  what? human verified? evidence? unknowns?) and walks one derivation step
  upstream. UTF-8-safe on Windows consoles.
- **Reproducible ingestion**: `tools/fetch_evidence.py` (pinned-revision
  snapshots with hashes → `evidence/snapshots/`, 108 datasets),
  `tools/curation/` (authoring scaffolding: curator judgments → records),
  `benchprov build --check` (byte-exact registry ↔ sources proof),
  `tools/verify_evidence.py` (re-fetches all cited URLs; hash + verbatim-quote
  checks under documented rendered-text normalization).
- **Tests + CI**: 49 pytest tests (schema, vocabularies, completeness math,
  every validator error class, duplicate detection, build determinism/
  staleness, CLI smoke incl. JSON output, packaged-data sync);
  `.github/workflows/ci.yml` (ubuntu+windows × py3.10/3.12: pytest +
  validate + build --check).
- **Docs**: README (problem, evidence, example, usage, honesty section,
  limitations), CONTRIBUTING (20-minute record workflow), MIT code license +
  CC-BY-4.0 data license.

## 2. Repository structure

```
benchprov/
├── schema/provenance.schema.json      # canonical schema (frozen v0.1.0)
├── registry/
│   ├── provenance.jsonl               # GENERATED registry (104 records)
│   └── families.json                  # benchmark-family registry (21 families)
├── sources/records/*.json             # curated truth (one file per record)
├── evidence/
│   ├── snapshots/*.json               # pinned raw-evidence extracts (108 datasets)
│   └── verify_report_v01.txt          # last full evidence re-verification
├── src/benchprov/                     # model / validate / build / stats / cli (+_data fallback)
├── tools/                             # fetch_evidence, verify_evidence, curation scaffolding
├── tests/                             # 49 tests
├── docs/                              # schema.md, DESIGN_DECISIONS.md, this report
└── README.md, CONTRIBUTING.md, LICENSE, LICENSE-DATA, .github/workflows/ci.yml
```

## 3. Record counts

By translation type: machine 46 · native_original 22 · unknown 12 · mixed 10
· human 10 · lm_generated 3 · script_conversion 1.
By human verification: unknown 67 · not_applicable 22 · none 6 · full 4 ·
per_item_flags 3 · partial 2.
By provenance state: partial 75 · complete 27 · conflicting 1 (a real
hub-tag-vs-card license conflict, preserved) · minimal 1.
Regional wedge: kk 10 records · ru 19 · bn 20 · uz 3 (plus ar 18, tr, fa,
or, th, ja, ko, zh…; 81 languages total; Belebele/FLORES/EU-MMLU/MMLU-ProX
recorded as `mul`). The registry's two Kazakh MMLU translations both
leave the translation engine unnamed in their dataset cards.
Completeness mean 0.78 / median 0.83; 6 records carry
name_only claims (visible, filterable); curation method `assisted` on all
104 (disclosed per record).

## 4. Validation and test results

- `benchprov validate` (sources + registry freshness): **PASS, 0 errors, 0
  warnings**.
- `python -m pytest -q`: **49 passed**.
- Evidence re-verification (`tools/verify_evidence.py`, 207 items):
  **0 errors; 3 warnings** — 2 documented gated-URL 401s (alibayram,
  flores_plus), which is expected behavior for gated datasets, and 0
  remaining quote failures after the correction round.
- Clean-checkout reproduction: fresh `git clone` → `pip install -e ".[dev]"`
  → tests 49/49 → validate PASS → `build --check` byte-identical → stats OK.

The verifier earned its keep against the curator: its first full run caught
14 real defects in my own records — non-verbatim quotes (elided markdown
links, joined lines, one morphological paraphrase of an abstract), summaries
misfiled in `quote` fields, and one hand-typed git sha whose tail I had
fabricated. All fixed at the source level and re-verified; the episode is
recorded in the commit history.

## 5. Known limitations

Documented user-facing in README; the load-bearing ones: seed-not-census
coverage (~100 of thousands of datasets); `mul` records are opaque to
per-language queries; one-step derivation records (chains need walking);
human_verification is majority-unknown from consulted sources (a documentation gap this seed records,
but it caps answers); split-level provenance is `mixed`+notes, not
structured; language tags regex-checked not registry-checked; licenses
verbatim only; 4 gated-dataset records cite auth-required URLs; facts are
as-of recorded dates with drift detectable but not auto-updated.

## 6. Unresolved risks

- **Adoption remains zero and untested** (R1/R2 from the discovery phase):
  demand evidence is real but nobody has asked for *this artifact*; the
  cited-not-consumed failure mode is still live until a consumer exists.
  The README states this explicitly.
- **Freshness pressure**: new translated benchmarks appear weekly; scope
  fencing (families + wedge) is the mitigation, not a maintenance promise.
- **Curation was single-curator and AI-assisted** (disclosed per record and
  in README); per-record quotes make third-party checking cheap, but no
  second curator has reviewed the seed.
- **Socially sensitive rows**: records about named national-program
  datasets (ISSAI ×5, kz-transformers ×2) originally said their translation
  method was "undocumented"; the pre-release audit re-bounded this wording
  to card-level absence at pinned revisions (see PRE_RELEASE_AUDIT.md M5).
- **A handful of judgment calls** are packed into notes rather than schema
  (e.g. MERA as one suite-level record; XNLI's split-mixed status; treating
  copies as carrying content-level translation facts). All are flagged in
  the records themselves.

## 7. Recommended next step

Hold at v0.1 pending your review. The natural next decision (yours, per the
standing rule of separate approval for anything outward-facing) is the
adoption experiment design: pre-registered, one named carrier, smallest
observed contribution genre. The discovery evidence suggests candidates in
this order: (a) publish the repo + registry as a public GitHub repository
and HF dataset (no contact — passive availability); (b) an MTEB-style
metadata contribution or an lm-eval task-README provenance note citing the
registry, where merge = the success signal; (c) EvalEval/Community-Evals
channels. None of this has been started.

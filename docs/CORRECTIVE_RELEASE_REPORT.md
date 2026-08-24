# Corrective release report — benchprov v0.1 (2026-08-24)

Corrective pass applying `docs/PRE_RELEASE_AUDIT.md` (verdict accepted:
GO-WITH-FIXES). Full per-issue detail lives in the audit's §10 resolution
log; this report is the summary of record. Scope framing applied throughout:
a **global** multilingual-benchmark-provenance infrastructure project with a
deliberate kk/ru/bn/uz regional wedge as evidence, not as subject; an
elevated public-evidence-only standard applies to ISSAI/KazLLM-related
records because of the project author's collaboration relationship with that
ecosystem.

## 1. Blockers — all resolved

- **B1 (Global-MMLU `is_annotated` misread).** The record had described the
  parent dataset's `is_annotated` column as a human-translation/post-edit
  flag; the card defines it as a cultural-bias-study annotation flag.
  Fixed: `human_verification` → `partial` (supported directly by the card's
  "professional translations and crowd-sourced post-edits"); the evidence
  now quotes the card's actual definition; the misdescribed
  `per_item_provenance` block was removed; the in-record note discloses the
  correction. The taresco subset record was corrected accordingly
  (verification → `unknown`; misdescription removed).
- **B2 (xnli_bn lineage).** Parent corrected to `nyu-mll/multi_nli`, which
  is what the record's own cited quote says was translated; the
  XNLI-procedure relationship is explained in a note.
- **B3 (Kazakhstan count).** README and implementation report now say "the
  two independently published Kazakh MMLU translations, neither of which
  names a translation engine **in its dataset card**" — bounded to public,
  registry-observable facts.

## 2. Majors — all resolved

M1 verification overreach (mesolitica, NLPCoreTeam → `partial`, informal
checking attested; `none` kept only where affirmed) · M2 method≠verification
(Blind-Review → `unknown`; per-item block relabeled METHOD) · M3 Winogrande
(paper evidence added with verbatim quote) · M4 chained-inference rule
documented in schema.md and applied (Finnish-NLP and taresco claims →
`unknown`/`name_only` with conditionals spelled out; mizinovmv and ik-ram28
derivations → `name_only`) · M5 ISSAI/kz wording bounded to card-level
absence at pinned revisions; program-level attribution removed ("publicly
unspecified" never rendered as "undocumented") · M6 README methodology
wording corrected (sample denominator, pattern-matching detection scope,
sample-bounded "most", traceability sentence, example quote fixed, demand
bullets now link their four PRs/issues incl. EuroEval's merged PR #2071) ·
M7 EU-MMLU license modeled as `conflicting`, consistent with alibayram ·
M8 Belebele and squad_bn → `aggregation_of` with composition notes · M9
engine/translator strings de-invented (five records).

Minors applied: bounded unknown-notes standardized; DoggiAI source
`zh-Hans`; alibayram verbatim `pretty_name` quote restored;
`evidence/README.md` added; schema.md gains the copy/subset
`translation_type` rule, the completeness≠evidence-strength caveat, the
corrected + completed MTEB mapping (post-editing ≠ localization; unmappable
values enumerated; one-directional), and the hub-metadata-as-declaration
caveat; DD15 records deferred naming/vocabulary debts; LICENSE-DATA notes
that records about NC/ND-licensed datasets redistribute metadata and short
quotes only; README documents `--registry` for non-repo installs and frames
registry statistics as seed-descriptive, not ecosystem estimates.

**Additional fix found while applying (disclosed):**
`kz-transformers/kk-socio-cultural-bench-mc` creation was `mixed`, but its
card describes one uniform hybrid process, not item-level variation; under
the elevated standard it is now `unknown` with the card's own description
attached to the claim.

## 3. Final registry count

**104 records · 100 datasets · 81 languages** (unchanged counts; contents
corrected). Creation: machine 46 · native_original 22 · unknown 14 ·
mixed 9 · human 9 · lm_generated 3 · script_conversion 1. Verification:
unknown 69 · not_applicable 22 · partial 5 · full 4 · none 4 ·
per_item_flags 0. States: partial 76 · complete 25 · conflicting 2 ·
minimal 1. Records with name_only claims: 9; revision-pinned evidence in
97 records; curation `assisted` (disclosed) on all 104. Completeness mean
0.7654 / median 0.8333 — lower than pre-audit (0.7769), as honesty demotions
should make it.

## 4. Final validation status

- Schema + cross-field + registry validation: **PASS — 0 errors, 0 warnings**
  (`benchprov validate`).
- Tests: **49/49 pass** (includes builder change for the new conflict/quote
  evidence slots).
- Deterministic build: `benchprov build --check` — registry byte-identical
  to a rebuild from sources.
- Evidence re-verification (`tools/verify_evidence.py`, 206 cited items
  re-fetched): **0 errors, 2 warnings** (both documented gated-URL 401s:
  alibayram/turkish_mmlu, openlanguagedata/flores_plus).
- Clean-checkout reproduction: fresh clone → install → tests → validate →
  `build --check` — re-run after the corrective commits (result recorded in
  the final session log).
- Docs link check: all relative links resolve. Secrets/PII scan: clean;
  local filesystem paths removed from shipped docs.
- Sensitive-row probes re-run: ISSAI and kz-transformers records re-read in
  final form — bounded, neutral, org-level attribution only.

## 5. Remaining warnings

1. Two evidence-verification warnings for gated datasets (401 without an
   authenticated, condition-accepting session) — documented in the affected
   records and in `evidence/README.md`; expected behavior, not defects.
2. Linux CI has never executed (no remote; no local Docker at fix time).
   The workflow covers ubuntu+windows and must be green on first push
   before any announcement.

## 6. Intentionally unresolved (with justification)

- `translation_type` naming (`creation_method` would be accurate) and the
  overloaded `mixed` value: schema-breaking; deferred to v0.2 and recorded
  in DD15 and the audit.
- Split-level provenance modeling (e.g. XNLI's human eval splits vs MT train
  split): v0.2 candidate; represented today as `mixed` + explicit notes and
  called out in README limitations.
- Dead-until-created repository URLs in `pyproject.toml` and the schema
  `$id`: resolve at publish time by creating the repository under that exact
  name.
- The implementation report's quantitative sections intentionally preserve
  the pre-audit figures, now clearly marked as such with a pointer to the
  audit — the document is a historical build record, not current state.

No publication, PRs, maintainer contact, or adoption steps were taken. The
artifact is ready for an independent release decision.

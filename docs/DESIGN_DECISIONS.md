# Design decision record — benchprov v0

Non-obvious choices and why they were made. Format: decision — alternatives —
rationale. Dated 2026-08-24 (schema frozen before large-scale collection).

**DD1. One record = one derivation step, not a materialized chain.**
Alt: embed the full upstream lineage in every record. Rationale: chains
duplicate facts that then rot independently; a step-scoped record has exactly
one evidence surface (its own dataset's statements), and consumers can walk
`derived_from`. Cost: "is there MT anywhere upstream?" needs a walk — the CLI
answers it when parent records exist in the registry, and reports
"upstream not in registry" honestly when they don't.

**DD2. Orthogonal `translation_type` × `human_verification`, not MTEB's
compound enum.** Alt: adopt MTEB `sample_creation` verbatim. Rationale: the
compound values conflate creation and checking ("machine-translated and
verified") and cannot express engine names or per-item flags; orthogonal
fields express everything the compound vocabulary can (a documented mapping
is provided in schema.md) plus the cases it cannot. MTEB interop is preserved
via the mapping rather than the storage format.

**DD3. Post-editing is a `translation_type`, verification is not.**
`hybrid_machine_post_edited` changes the text as part of creation;
`human_verification` records checking. The discovery evidence (Global-MMLU's
mixed MT + professional + crowd post-edits; its per-item `is_annotated`)
requires keeping these apart to avoid overclaiming either.

**DD4. `none` verification requires an affirmative account, silence never
counts.** Alt: infer `none` from minimal cards. Rationale: mission constraint
("never turn absence of evidence into a factual claim"). A card that
describes its complete automated pipeline is evidence about the process; a
card that says nothing is `unknown`.

**DD5. `name_only` is a first-class claim status.** The discovery E1 sample
contained rows whose only provenance signal is the dataset id (e.g. `nllb` in
`Slim205/mmlu_translated_nllb0`). Alt: treat as verified (overclaims) or
unknown (discards a real signal). Keeping it explicit lets consumers filter
by evidence strength; completeness counts it as known but the status is
visible.

**DD6. `conflicting` counts as known for completeness but dominates
`provenance_state`.** A conflicted dimension carries information (two sourced
positions) — the problem is trust, not absence, and the state field is the
trust channel. Conflicts are stored with both values and both evidence sets;
the validator refuses records that resolve a conflict by omission.

**DD7. Licenses recorded verbatim, never normalized.** A license crosswalk is
its own project (and a previously-killed one); benchprov records what the hub
declares (`license: llama3.1`) with evidence, and nothing else. This also
keeps the registry out of legal interpretation.

**DD8. Six core dimensions, deterministic completeness, stored AND
recomputed.** Alt: store only. Rationale: stored values make the registry
useful without tooling (jq/pandas); recomputation makes tampering and drift
detectable ("inconsistent provenance states" is a required validator check).
Rounding to 4 decimals makes the equality check exact across platforms.

**DD9. Sources-of-truth layout: `sources/records/*.json` (curated) →
`registry/provenance.jsonl` (generated, committed).** Alt: edit the JSONL
directly. Rationale: mission requires that no manually edited generated file
be the source of truth; one-file-per-record is diff- and contribution-
friendly; the build is deterministic (sorted by `record_id`, canonical
separators) so `benchprov build --check` can prove the committed registry
matches the sources byte-for-byte.

**DD10. Evidence snapshots store hashes + short quotes, not full third-party
documents.** Alt: vendor full README copies. Rationale: dataset cards are
third-party content with frequently unclear licensing (the permissive-washing
audit made exactly this point); revision-pinned URLs + SHA-256 + ≤300-char
quotes give reproducibility without redistribution risk.

**DD11. Language tags: strict-ish BCP-47 subset by regex, not a language
library.** Alt: depend on `langcodes`. Rationale: zero-surprise deterministic
validation with one dependency fewer; the pattern covers language + script +
region, which is all the registry needs (`kk-Cyrl`, `zh-Hant`, `es-419`).
Cost: no validity check of the letters against the ISO registry — accepted
for v0 and noted in limitations.

**DD12. Native-original "contrast rows" are in scope.** Alt: translated
datasets only. Rationale: the consumer question is "is this translated?";
a registry that can answer "no — natively authored, here's the evidence"
for KazMMLU/CMMLU-class datasets is more useful than one that can only
describe translations. They join their style-family (`root_benchmark: MMLU`,
`derived_from.kind: modeled_on`) so family statistics stay meaningful.

**DD13. Curation method disclosed per record.** `curated.method: assisted`
marks records filled by an AI system reading the evidence under human
direction (all v0 seed records). Alt: silence. Rationale: research-integrity
norm; consumers can weigh it, and the per-record evidence quotes make every
record independently checkable regardless of who filled it.

**DD14. CLI named `benchprov`, package `benchprov`, no third-party CLI
framework.** argparse + stdlib keeps install surface minimal (single runtime
dependency: `jsonschema`). Machine output via `--json` on every subcommand.

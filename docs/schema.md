# benchprov schema reference (v0.1.0)

Canonical machine-readable definition: [`schema/provenance.schema.json`](../schema/provenance.schema.json).
This page explains the model in prose. Anything the two disagree on is a bug;
the JSON Schema plus the validator's cross-field rules are authoritative.

## What one record is

**One record = one derivation step of one dataset (optionally one config /
language group) with uniform provenance.**

- A single-language translated dataset → one record.
- A multilingual dataset whose languages share one creation story → one
  record listing all `target_languages`.
- A multilingual dataset whose creation story differs by language (e.g. one
  language via DeepL, the rest via GPT-3.5) → several records, one per group.
- A record describes **its own step only**. `DoggiAI/GSM8K_zh_tw` is a
  script conversion of `meta-math/GSM8K_zh`; the fact that the parent was
  itself machine-translated from English lives in the parent's record, not
  duplicated here. Chains are walked through `derived_from.parent_id`.
- **Exception — kinds that create no new text** (`subset_or_filter_of`, and
  aggregations that only recombine existing items): `translation_type` then
  describes how the item text was created *wherever that happened*, with
  evidence cited accordingly (usually the parent's statements, or the
  record's own card restating them). The claim's evidence and status must
  reflect that chain — see the chained-claims rule below.
- **Chained claims inherit the weakest premise's status.** If a fact about
  the items is true only *via* a derivation that is itself supported by
  naming alone, the dependent claim must not carry a stronger status than
  `name_only` — or should be recorded as `unknown` with the conditional
  spelled out in its note. A `verified` label always means the cited
  evidence supports the claim about *this* dataset directly.

## Core claim dimensions

Six dimensions carry the record's factual payload. Each has a field holding
the **value** and an entry in `claims` binding that value to **evidence**:

| dimension | field | allowed values |
|---|---|---|
| translation type | `translation_type` | `machine`, `human`, `hybrid_machine_post_edited`, `script_conversion`, `lm_generated`, `native_original`, `mixed`, `unknown` |
| engine / translator | `engine_or_translator` | free string, `unknown`, `not_applicable` |
| human verification | `human_verification` | `full`, `partial`, `per_item_flags`, `none`, `not_applicable`, `unknown` |
| license (as declared) | `license` | free string, `unknown` |
| derivation | `derived_from` | object: `kind` + `parent_id` |
| source language | `source_language` | language tag, `unknown`, `not_applicable` |

### `translation_type`

How the target-language **item text** of this dataset came to be, at this step:

- `machine` — automated translation (NMT engine or LLM prompting).
- `human` — humans translated the items.
- `hybrid_machine_post_edited` — machine output subsequently **edited** by
  humans as part of creation. Distinct from verification: post-editing
  changes the text; verification checks it.
- `script_conversion` — deterministic transliteration / script conversion
  (e.g. OpenCC Simplified→Traditional).
- `lm_generated` — items **generated** in the target language by a model
  (not translations of parent items).
- `native_original` — items natively authored in the target language(s).
- `mixed` — methods differ inside this record's scope and the evidence does
  not allow splitting into cleaner records.
- `unknown` — no evidence of method.

### `human_verification`

Whether the **final target-language items were checked by humans** at this step:

- `full` — the whole set is stated as human-reviewed / QA'd. Human
  translation with an explicit QA step is `full`.
- `partial` — a stated subset or sample was reviewed.
- `per_item_flags` — the dataset ships a per-item field saying which items
  were human-checked (e.g. Global-MMLU `is_annotated`); requires
  `per_item_provenance`.
- `none` — the creators' **own account of the full process** affirms an
  automated-only pipeline (e.g. "instead of manually checking … I automate
  the whole process"). This is an affirmative reading of a complete method
  description — **silence is never `none`**.
- `not_applicable` — only for `native_original` records (there is no
  translation to verify; native QA is out of scope for v0).
- `unknown` — no evidence either way. This is the honest default.

Note: human translation **without** a stated QA/review step is
`translation_type: human` + `human_verification: unknown`. The two dimensions
are deliberately independent.

### known / unknown / not\_applicable, precisely

- A dimension is **known** when its claim status is `verified`, `name_only`,
  or `conflicting` (evidence exists — even weak or contradictory evidence is
  information; `conflicting` is surfaced separately by `provenance_state`).
- A dimension is **unknown** when the curator looked and found no evidence.
  The field value must be the string `unknown` and the claim status
  `unknown`. An `unknown` claim may still cite evidence with a note (e.g.
  "card checked at revision X; no statement"), documenting the search.
- A dimension is **not\_applicable** when it structurally cannot apply:
  - `engine_or_translator`, `human_verification`: iff
    `translation_type == native_original`;
  - `source_language`: iff `derived_from.kind` is **not**
    `translation_of` / `script_conversion_of`.
  `not_applicable` is a determination, not missing data.

### Claim statuses

- `verified` — at least one substantive evidence item (card, hub metadata,
  paper, repo code, dataset content, external page) states the value.
- `name_only` — the only support is the dataset's own naming (e.g. `nllb`
  inside `Slim205/mmlu_translated_nllb0`). Kept explicit because the
  discovery phase showed such rows exist and consumers should see the
  difference.
- `unknown` / `not_applicable` — as above.
- `conflicting` — cited evidence disagrees. The field holds the primary
  (best-attested) value **or** `unknown` if no position is better attested;
  every other position is preserved under `claims.<dim>.conflicts[]` with its
  own evidence. Conflicts are never resolved by dropping a source.

## Deterministic completeness

```
applicable = 6 − (number of core claims with status not_applicable)
known      = number of core claims with status in {verified, name_only, conflicting}
completeness = round(known / applicable, 4)
```

`provenance_state` is derived, in order of precedence:

1. any core claim `conflicting` → `conflicting`
2. `completeness == 1.0` → `complete`
3. `completeness == 0.0` → `minimal`
4. otherwise → `partial`

Both fields are **stored** in the record and **recomputed** by the validator;
a mismatch is a validation error, never silently repaired.

**Completeness measures determinability, not evidence strength.** A
dimension counts as known even when its support is `name_only` or
`conflicting`; consumers who need strength should filter on claim `status`
(the stats command reports how many records carry `name_only` claims).

## Evidence items

Every record carries ≥1 evidence item: `{id, type, url, retrieved, quote?,
sha256?, hub_revision?, note?}`. Prefer **revision-pinned URLs**
(`https://huggingface.co/datasets/<id>/raw/<sha>/README.md`) so the cited
document cannot drift; `sha256` is the hash of the retrieved bytes. Quotes
are short verbatim excerpts (≤300 chars) carrying the fact — enough to
locate and check the claim, no more.

Evidence types: `dataset_card`, `hub_metadata`, `paper`, `repo_code`,
`dataset_content`, `external_page`, `name_only`.

Note that `hub_metadata` (tags such as `source_datasets: original`) is a
**declaration by the dataset depositor**, not independent confirmation; it
counts as substantive evidence of what the depositor declares, no more.

## Identity and uniqueness

- `record_id` = `<dataset-slug>__<language-part>[__<config-slug>]`, where
  dataset-slug is `dataset.id` lowercased with `/`→`-` (and any character
  outside `[a-z0-9._-]`→`-`), and language-part is the `-`-joined language
  tags (lowercased) or `multi` for records covering ≥4 languages.
- No two records may share the same `(dataset.id, dataset.config, language)`
  triple for any language (after expanding `target_languages`).

## Interop: mapping to MTEB `sample_creation`

MTEB's task metadata already carries a translation-provenance vocabulary for
embedding tasks. benchprov's orthogonal fields map onto it **lossily, in one
direction** (benchprov to MTEB; the reverse is not defined):

| benchprov (`translation_type` + `human_verification`) | MTEB `sample_creation` |
|---|---|
| `machine` + `unknown`/`none` | `machine-translated` |
| `machine` + `full`/`partial`/`per_item_flags` | `machine-translated and verified` |
| `hybrid_machine_post_edited` + any | `machine-translated and verified` — **caveat**: MTEB has no post-editing value; its "…and localized" values mean cultural adaptation, *not* post-editing, and must not be used for this |
| `human` + any | `human-translated` |
| `lm_generated` + `full`/`partial` | `LM-generated and verified` |
| `lm_generated` + `none`/`unknown` | **unmappable** (MTEB has no unverified LM-generated value) |
| `script_conversion` | **unmappable** (no MTEB equivalent) |
| `native_original` | `created` / `found` |
| `mixed` | `multiple` |
| `unknown` | **unmappable** (MTEB has no unknown value) |

Engine names, evidence bindings, claim statuses, and per-item flags have no
MTEB counterpart and are lost in any mapping; benchprov records remain the
richer form.

## What v0 deliberately does not model

- Translation **quality** (no scores, no judgments).
- License normalization or compatibility (values are recorded as declared).
- Full upstream chains materialized per record (walk `derived_from` instead).
- Per-item provenance beyond pointing at the dataset's own flag column.
- Benchmark **content** versioning beyond the pinned `dataset.revision`.

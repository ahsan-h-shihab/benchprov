# benchprov — Benchmark Translation Provenance

**A machine-readable, evidence-backed registry of how multilingual and
translated NLP benchmarks were actually created** — machine-translated or
human-translated, by which engine or team, checked by humans or not, under
which license, derived from what.

## The problem

Hundreds of translated variants of MMLU, GSM8K, ARC, HellaSwag, Belebele and
friends circulate on the Hugging Face Hub, and most of the ones we sampled
don't say how they were made. In a structured sample of 96 MMLU-variant
datasets carrying non-English language tags or "translated" naming, **65%
matched none of our translation-engine or human-verification patterns
anywhere in their cards** (the sample includes a few native or synthetic
variants — which only sharpens the point that variant provenance is not
machine-readable). Yet the difference matters: harnesses and papers already
act on it when they can —

- lm-evaluation-harness merged "**Machine Translated.**" warnings into its
  okapi task docs ("results … should be interpreted with this issue in mind")
  — [PR #2168](https://github.com/EleutherAI/lm-evaluation-harness/pull/2168);
- lighteval renamed its Arabic MMLU tasks `arabic_mmlu_mt` / `arabic_mmlu_ht`
  / `arabic_mmlu_okapi` *by translation provenance*, because there was
  nowhere else to put the distinction —
  [PR #372](https://github.com/huggingface/lighteval/pull/372);
- MTEB maintains a `sample_creation` field ("machine-translated and verified",
  …) for embedding tasks — and corrects it when it's wrong —
  [PR #2665](https://github.com/embeddings-benchmark/mteb/pull/2665);
- EuroEval added EU-MMLU specifically because its existing MMLU variants
  "rely on machine translation" —
  [issue #2070](https://github.com/EuroEval/EuroEval/issues/2070) /
  [merged PR #2071](https://github.com/EuroEval/EuroEval/pull/2071).

benchprov gives that distinction a home: one small schema, one registry,
every claim traceable to cited evidence — Hub evidence revision-pinned and
hashed, quotes verbatim, naming-only support explicitly labeled as such.

## What's in v0.1

**104 records** covering **100 datasets** in **81 languages**: the major
translated families (MMLU, MMLU-Pro, GSM8K, ARC, HellaSwag, TruthfulQA,
Belebele, MGSM, XNLI, SQuAD, FLORES…), their originals as contrast rows, and
a deliberate low-resource/regional wedge (Kazakh, Russian, Bengali, Uzbek) as
evidence that the provenance problem also matters in under-resourced, less
centralized language ecosystems — e.g. the two independently published
Kazakh MMLU translations, neither of which names a translation engine in its
dataset card. The registry's own statistics document the gap it addresses:
for **69 of 104 records no human-verification status is determinable from
the sources consulted; for 25 those sources name no translation engine; for
14 they do not even establish machine-vs-human.** Unknown is recorded as
unknown — that is the point. (These figures describe this curated seed, not
an estimate for the whole ecosystem; the seed deliberately includes
well-documented anchor datasets, which if anything flatters the rates.)

## A record, in short

```json
{
  "record_id": "freedomintelligence-mmlu_arabic__ar",
  "dataset": {"id": "FreedomIntelligence/MMLU_Arabic", "hub": "huggingface",
               "revision": "…", "url": "…"},
  "root_benchmark": "MMLU",
  "derived_from": {"kind": "translation_of", "parent_id": "cais/mmlu"},
  "target_languages": ["ar"], "source_language": "en",
  "translation_type": "machine",
  "engine_or_translator": "gpt-3.5-turbo",
  "human_verification": "unknown",
  "license": "mit",
  "claims": { "translation_type": {"status": "verified", "evidence": ["e1"]}, … },
  "evidence": [ {"id": "e1", "type": "dataset_card",
                 "url": "…/raw/<sha>/README.md", "retrieved": "2026-08-24",
                 "quote": "Arabic version of MMLU dataset translated by gpt-3.5-turbo."} ],
  "completeness": 0.8333, "provenance_state": "partial"
}
```

Every core claim binds to evidence items with revision-pinned URLs, SHA-256
hashes, and short verbatim quotes. Conflicts are preserved, not resolved
(one seed record carries a real hub-tag-vs-card license conflict).

## Use it

```bash
pip install -e .
```

(Installed outside the repository — e.g. from a wheel — `inspect`/`stats`
need `--registry path/to/provenance.jsonl`; the registry lives in this
repository, not inside the package.)

```bash
benchprov inspect FreedomIntelligence/MMLU_Arabic   # the provenance card
```

`inspect` answers, with citations: *Is this machine translated? By what? Was
it human verified? What is it derived from? What's still unknown?* It also
walks one step upstream when the parent is in the registry. Add `--json` for
machine-readable output. Then:

```bash
benchprov stats                 # registry-wide counts (types, verification, languages…)
benchprov validate              # validate everything + registry freshness
benchprov build --check         # prove registry/provenance.jsonl == rebuild(sources)
```

Or skip the CLI entirely — `registry/provenance.jsonl` is sorted, canonical
JSON-lines; `jq`/pandas work directly.

## How the data is kept honest

- `sources/records/*.json` are the curated truth (one file per record);
  `registry/provenance.jsonl` is **generated**, and CI proves it matches a
  deterministic rebuild.
- The validator ([`benchprov/validate.py`](src/benchprov/validate.py))
  enforces value↔evidence coherence: a `verified` claim must cite substantive
  evidence; naming-only support is demoted to `name_only`; silence is
  `unknown`, never `none`; `completeness`/`provenance_state` are recomputed
  and must match. It reports; it never repairs.
- `python tools/verify_evidence.py` re-fetches every cited URL and re-checks
  hashes and quotes against the live sources.
- Schema: [`schema/provenance.schema.json`](schema/provenance.schema.json),
  explained in [`docs/schema.md`](docs/schema.md); design rationale in
  [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md).
- Every v0 record is marked `curated.method: "assisted"` — an AI system read
  the evidence and filled the record under human direction. The per-record
  quotes exist so you never have to trust the curator.

## Contributing

One record ≈ 20 minutes: fetch a pinned evidence snapshot, write one JSON
file, `benchprov validate`, done — see [CONTRIBUTING.md](CONTRIBUTING.md).
The rules that matter: never infer; silence is `unknown`; preserve conflicts;
quote minimally; pin revisions.

## Status and honesty

What the evidence behind this project does and does not show:

- **Provenance is missing at scale** — measured (65% of sampled translated
  MMLU variants declare nothing; reproduced in this registry's own stats).
- **Provenance is largely recoverable** — measured (a pre-registered
  40-dataset experiment recovered the creation method for ~74% of rows from
  cards and linked papers; engines for ~65%).
- **Consumers act on provenance when it exists** — observed (the lm-eval /
  lighteval / MTEB / EuroEval artifacts above).
- **Adoption of *this* registry** — **none yet.** benchprov v0.1 is a fresh
  artifact. No harness, leaderboard, or dataset consumes it today, and no
  claim to the contrary should be read into this README.

## Limitations (v0.1)

- **Coverage is a seed, not a census**: ~100 of the thousands of translated
  benchmark datasets; benchmark families beyond the listed ones (and most
  languages' local benchmarks) are absent. Massively multilingual sets use
  `mul` instead of enumerating 100+ language tags, so per-language queries
  don't see inside them.
- **One derivation step per record**: upstream provenance requires walking
  `derived_from` (the CLI does one step); chains longer than the registry's
  contents end in "upstream not in registry".
- **`human_verification` is the weakest-evidenced dimension** (69/104
  unknown from consulted sources) — that reflects how these datasets are
  documented, not a curation shortcut, but it caps what the registry can
  answer today.
- **Split-level provenance** (e.g. XNLI's human dev/test vs MT train) is
  recorded as `mixed` with notes, not modeled structurally.
- **`unknown` is search-bounded**: it means no statement was found in the
  sources each record cites (usually the dataset card at a pinned revision,
  sometimes one linked paper or page). It never means that no provenance
  information exists anywhere, and it never implies the creators did no
  verification.
- **Completeness measures determinability, not evidence strength**: a
  dimension counts as known even when its support is naming-only or
  conflicting — filter on claim `status` for strength (stats report how many
  records carry `name_only` claims).
- **Language tags are format-checked, not registry-validated**; licenses are
  recorded as declared, never normalized or interpreted.
- **Gated datasets** (4 records) cite pinned URLs that require an
  authenticated, condition-accepting session to view.
- Curation date, evidence dates, and revisions are recorded per record;
  facts are as of those dates. Datasets move; `tools/verify_evidence.py`
  detects drift but nothing auto-updates.

## Licenses

Code: [MIT](LICENSE). Registry data and evidence snapshots:
[CC BY 4.0](LICENSE-DATA). Quoted excerpts from third-party dataset cards
and papers remain their authors'; quotes are kept short and cited for
evidencing factual claims.

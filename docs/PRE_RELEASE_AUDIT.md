# Pre-release adversarial audit — benchprov v0.1

Date: 2026-08-24. Auditor stance: skeptical NLP-infrastructure maintainer /
reviewer looking for reasons to reject. Scope: schema, all 104 registry
records, evidence model, validator, CLI, README, implementation report,
repository hygiene. Method: fresh record-by-record evidence-to-claim pass;
programmatic sweeps (quote-less verified claims, unbounded-absence wording,
verification-value review set); primary-source re-checks where the chain
looked thin (Global-MMLU card's `is_annotated` definition, EuroEval issue
#2070 → PR #2071, UNT split contents via datasets-server first-rows);
sentence-level README/report pass; secrets/paths/links/stale-file scans.
Nothing was modified during the audit; this document is the only new file.

---

## 1. Executive verdict: **GO-WITH-FIXES**

The architecture survives adversarial reading: the evidence-binding model,
validator discipline, deterministic build, and honesty framing are sound and
in several places caught the curator's own errors before this audit did.
However, the audit found **3 blocker-class issues** (one factual
misrepresentation of a third-party dataset's field semantics, one lineage
assignment contradicted by its own cited quote, one factually wrong count in
the README about a politically sensitive topic), **8 major issue groups**,
and a set of minor wording/consistency debts. All are record-level or
document-level corrections; none require schema changes to fix. **There are
not zero blockers.** Do not publish until §2 items are fixed and §9 is
re-run.

---

## 2. Blocking issues (fix before any release)

| id | where | finding | evidence |
|---|---|---|---|
| **B1** | `coherelabs-global-mmlu__multi` (and inherited: `taresco-cohere-global-mmlu-filtered-math__multi`) | `per_item_provenance.description` states `is_annotated` is "True for items that were professionally translated / human post-edited; False for raw machine translations". The pinned card defines it differently: **"`is_annotated`: True/False flag to indicate if sample contains any annotations from our cultural bias study."** The record misrepresents a third-party dataset's field semantics, and `human_verification: per_item_flags` rests on that misreading. | Card at pinned revision `0e619dbe…`, Data-Fields section (re-fetched during audit). Fix: correct the description; set `human_verification: partial` (the card's "professional translations and crowd-sourced post-edits" statement supports *partial* directly); keep `per_item_provenance` only if described accurately as a cultural-annotation flag, or drop it. Same for taresco's inherited description. |
| **B2** | `csebuetnlp-xnli_bn__bn` | `derived_from.parent_id = facebook/xnli` contradicts the record's own cited quote: "we translated the **MultiNLI** training data using the English to Bangla translation mod[el]". The items derive from MultiNLI by the XNLI *procedure*, not from XNLI's items. | Record e1 quote. Fix: parent → `nyu-mll/multi_nli` (kind `translation_of`), note the XNLI-procedure relationship; family may stay XNLI with a note or move accordingly. |
| **B3** | `README.md` L35-37; `docs/IMPLEMENTATION_REPORT.md` §3 | "all **three** of Kazakhstan's independent MMLU translations, none of which names its engine" — the registry contains **two** Kazakh MMLU translations (`issai/MMLU_Kazakh`, `kz-transformers/mmlu-translated-kk`). The "three programs" finding from discovery counts a program (AlemLLM/Sherkala lineage) whose translated sets are not published as Hub datasets and are not in the registry. As written, a Kazakh-ecosystem reader can falsify the sentence by counting. Also unbounded: "names its engine" must be "names its engine **in its dataset card**". | Registry contents; discovery evidence. Fix: "two independently published Kazakh MMLU translations — neither of which names its translation engine in its dataset card" (+ optional note that a third national program's translated sets are not published on the Hub). |

---

## 3. Major issues

| id | where | finding | recommended handling |
|---|---|---|---|
| **M1** | `mesolitica-translated-mmlu__ms`, `nlpcoreteam-mmlu_ru__ru` | `human_verification: none` overreaches its own definition ("creators' account affirms an automated-only pipeline"). Both cards *evidence some human noticing* ("We found out some translated answers not really coherent…"; "There are some translation mistakes, especially observed…") — i.e., an informal human check occurred and corrections were not applied. "No fixes applied" ≠ "no human check". | Reclassify to `partial` (an informal, uncorrected review is attested) with notes quoting the same lines, or `unknown`. `none` should remain only where affirmed (murodbek×2 "has **not** undergone human review"; KillerShoaib "Instead of manually checking… I automate"). `patt-hellaswag_th_cleanned__th` is borderline-acceptable (pipeline account is plausibly complete) — keep `none` but strengthen the note. |
| **M2** | `translated-mmlu-blind-review-acl-srw-2025__pt` | `human_verification: per_item_flags` conflates translation *method* with *verification*: the `translation_method` column marks how each item was translated (one arm is Human) — it does not mark human *checking*. | `human_verification → unknown`; keep `per_item_provenance` (it genuinely is per-item provenance) with a description that says "method", not verification. |
| **M3** | `allenai-winogrande__en` | `translation_type: native_original` has status `verified` citing hub metadata that contains **nothing** supporting it (the repo declares no `source_datasets`, no `annotations_creators`, no license; the "crowdsourced Winograd-schema-style problems" text is the curator's own note). The paper that would support it is mentioned in a note but not cited as evidence. | Add the WinoGrande paper as a `paper` evidence item with a quote, or demote the claim. (Contrast: the other native anchors — cais/mmlu, gsm8k, ai2_arc, openbookqa, commonsense_qa, boolq, piqa — cite hub metadata that actually carries `source_datasets: original` / annotator tags; those are acceptable.) |
| **M4** | chained-inference status inflation: `finnish-nlp-belebele-fi-filtered-sft__fi` (tt `human` = verified while the derivation it depends on is `name_only`); `taresco-…` (engine via parent's paper, subset relation itself inferred from preserved YAML columns); `mizinovmv-ru_cais_mmlu__ru`, `ik-ram28-fr-mmlu_professional_medicine__fr` (kind `translation_of cais/mmlu` = verified from YAML field structure + dataset name — structure/name inference marked as verified) | A claim whose truth is conditional on a weaker-status claim should not carry a stronger status than its weakest premise. | Either demote the dependent claims (Finnish tt → status name_only-equivalent via note; mizinovmv/ik-ram28 kind → `name_only`-supported with the YAML cited as corroboration in notes), or add an explicit documented rule in `docs/schema.md` ("chained claims inherit the weakest premise's status") and apply it. The lrana / NovusResearch / fair-forward / Slim205 records already do this correctly — make the standard uniform. |
| **M5** | national-program absence wording: `issai-mmlu_kazakh__kk`, `issai-mmlu-pro_kazakh_russian__kk-ru`, `issai-gsm8k_kazakh_russian__kk-ru`, `issai-arc_kazakh_russian__kk-ru`, `issai-mmlu_redux_2.0_kazakh__kk` (shared note: "the translation method's actor is **undocumented**"), `kz-transformers-mmlu-translated-kk__kk` ("method **undocumented**") | Unbounded absence claims about named national programs. The evidence is card-level absence at a pinned revision; a technical report elsewhere could name the engine, and no exhaustive search was performed. This is exactly the "absence of a field in a card proves nothing exists elsewhere" trap. | Reword to bounded form: "no engine or translating party is named in the dataset card at the pinned revision; no public method statement was located in the sources consulted for this record." The per-claim `engine_note` fields are already bounded — align the `notes`. |
| **M6** | README methodological wording cluster (L10-14, L27-28, L59) | (a) "96 **translated** MMLU-family datasets" — the sampling frame was datasets with non-English language tags or 'translat' in the id, and it demonstrably contained non-translations (native, synthetic, tag-errors); (b) "declared neither … **anywhere in their card**" — detection was a finite keyword/regex battery, not a human read of every card; (c) "most don't say how they were made" generalizes beyond the sampled frame; (d) "**every fact** traceable to **quoted, revision-pinned** evidence" — name_only claims trace to a dataset id (no quote), paper/external evidence is not revision-pinned, and several hub-metadata citations are note-based; (e) the example record's quote says "tranlasted" but the actual Arabic record (correctly) says "translated" — the README example no longer matches the registry. | See §6 for exact replacement wording. |
| **M7** | license-conflict inconsistency: `ec-dgt-ai-eu-mmlu__mul` vs `alibayram-turkish_mmlu__tr` | Same evidence shape, different treatment: alibayram (hub tag `cc-by-nc-nd-4.0` vs card prose `CC BY-NC 4.0`) is modeled as a `conflicting` claim; EU-MMLU (hub tag `mit` vs card prose "made available under the CC BY 4.0 licence") is a note on a `verified` claim. A reviewer will ask why. | Model EU-MMLU's license as `conflicting` (both positions evidenced), or document a principled distinction (e.g. "scope-differing license statements are notes; same-scope contradictions are conflicts") and show EU-MMLU's card statement covers the translations specifically. The first option is simpler and more honest. |
| **M8** | lineage kind precision: `facebook-belebele__mul` (kind `translation_of facebook/flores` — but the *questions/answers* were composed in English and translated; only passages come from FLORES), `csebuetnlp-squad_bn__bn` (kind `translation_of rajpurkar/squad_v2` — but the set also contains natively-written TyDiQA-bn items, per its own note) | `translation_of <parent>` asserts the items derive from the parent's items by translation; both records' own notes describe aggregation. | Change both to `kind: aggregation_of` with the primary parent retained and the composition in notes. (Consequence: `source_language` becomes `not_applicable` under the current applicability rule — acceptable, since a single source language is genuinely not well-defined for aggregates; keep the English-origin fact in notes.) |

Engine/translator specificity overreach (grouped here as **M9**, individually
small but the mission is strict on identity fields):
- `openai-mmmlu__multi`: engine "professional human translators **(unnamed
  vendor)**" — "vendor" is invented; card says only "professional human
  translators". → "professional human translators (not further identified)".
- `jon-tow-okapi_mmlu__multi`: engine "ChatGPT **(gpt-3.5 class**, per
  Okapi/mlmm project docs)" — "gpt-3.5 class" is the curator's gloss; the
  cited README says "using ChatGPT". → drop the gloss.
- `orai-nlp-hellaswag_ht_eu_sample__eu`: engine "**Orai NLP Teknologiak**
  (manual translation)" — the card says "manually translated"; the translator
  identity is inferred from repository ownership. → "manual translation
  (translating party not named in the card)".
- `coherelabs-global-mmlu-lite__multi`: engine derives translator identity
  from a "**Curated by**" line; curation ≠ translation. → soften to "human
  translators / post-editors (per card; parties described only as
  professional annotators and Cohere Labs Community contributors)".
- `juletxara-mgsm__multi`: engine "human annotators **(Shi et al., 2022)**"
  — the parenthetical reads as naming the annotators; it is a paper citation.
  → "human annotators (per Shi et al., 2022)".

---

## 4. Minor issues

1. **README** "67 of 104 records have no determinable human-verification
   status" / "23 cannot name their translation engine" — add "from the
   sources consulted"; determinability is search-bounded (see §6).
2. `alibayram-turkish_mmlu__tr`: the `pretty_name` evidence text ("Özgün
   Türkçe Veri Seti") is verbatim API content but now lives in a `note`
   (side-effect of the blanket meta_tags-summaries-to-note policy). A
   verbatim string may be restored to `quote` for this item.
3. `doggiai-gsm8k_zh_tw__zh-hant`: `source_language: zh` could be `zh-Hans`
   for precision (the parent is Simplified Chinese).
4. Docs: `docs/schema.md` says a record "describes its own step only", yet
   `translation_type` on copy/subset records (LumiOpen, Global-MMLU-Lite,
   taresco, Finnish-NLP, KillerShoaib) intentionally describes the *content's*
   creation wherever it happened. The practice is reasonable and noted per
   record, but the docs never state the rule. Add one paragraph: "for kinds
   that create no new text, `translation_type` describes the item text's
   creation, evidenced accordingly (usually via the parent's statements)."
5. Docs: completeness ≠ evidence strength. A record can be `complete` on
   `name_only` or `conflicting` claims. Stated nowhere user-facing. Add a
   sentence to schema.md and README ("completeness measures how many
   dimensions are determinable, not how strong the evidence is — filter on
   claim `status` for strength").
6. Unknown-claim note wording varies: some claims say only "not stated"
   (unbounded) while others say "not stated in the card at the pinned
   revision". Standardize on the bounded form (validator cannot check this;
   it is a curation convention — affected examples: `ik-ram28…`,
   `lrana…`, `malhajar-arc-tr…`, `mizinovmv…`, `universitytehran…`,
   `novusresearch…`, `issai-mmlu_redux…` engine note).
7. Field-name debt: `translation_type` hosts non-translation values
   (`native_original`, `lm_generated`, `script_conversion`); the accurate
   name is `creation_method`. Not worth a schema break now; record as a
   v0.2 rename candidate in DESIGN_DECISIONS.
8. `mixed` is overloaded (per-language, per-split, per-item, multi-method
   variation are all `mixed` + notes). Works at v0.1 scale; a `variation_axis`
   or split-scoped records are v0.2 candidates. XNLI is the sharpest case: a
   consumer reading only the field could think the *test* split is partly MT
   (it is human-translated; the MT is the train split). The note carries it,
   but see §5.
9. `docs/IMPLEMENTATION_REPORT.md` contained a local Windows filesystem path
   (now removed) and internal project framing
   ("Project-02 survivor") — decide before release whether the report ships
   publicly (rewrite the path/context) or stays internal (exclude from the
   public repo).
10. `pyproject.toml` Repository URL and the schema `$id` point to
    `github.com/ahsan-h-shihab/benchprov`, which does not exist yet — dead
    links until the repo is created under exactly that name.
11. A wheel/sdist install without the repository has no registry on disk
    (`inspect`/`stats` then require `--registry`); packaged `_data` covers
    only schema+families. Document in README install section.
12. Helper evidence extracts (`evidence/snapshots/_paper_quotes*.json` etc.)
    are committed with underscore names alongside per-dataset snapshots —
    legitimate raw evidence, but a naming/README note in `evidence/` would
    prevent them being mistaken for stale scratch.
13. The MTEB interop mapping (schema.md) — see §5, item 4.

---

## 5. Scientific / evidentiary concerns (schema & ontology)

1. **Step-scoped records vs content-scoped `translation_type`** (minor §4.4
   formalized): the ontology is coherent only once the copy/subset rule is
   written down. Do that before external users build on it.
2. **Split-level provenance is flattened into `mixed`.** For XNLI-shaped
   datasets the dataset-level value under-informs the most common consumer
   question ("is the *eval split* human-translated?"). v0.1's note-based
   treatment is defensible and disclosed; a reviewer will still (fairly)
   call it a modeling gap. Keep in README limitations (already there) and
   name XNLI explicitly as the example.
3. **`unknown` semantics are search-bounded and must always say so.** The
   schema documentation defines this correctly; ~a third of unknown-claim
   notes don't carry the bound (§4.6). The registry's headline statistics
   inherit this: "67/104 unknown" means "not determinable from consulted
   sources", not "no human verification happened" and not "no statement
   exists anywhere". README currently states the right thing in the
   Limitations section but the stats sentences above it need the same hedge
   (§6).
4. **MTEB interoperability mapping loses and in one row distorts
   information.** (a) `hybrid_machine_post_edited → "machine-translated and
   localized"` is wrong: MTEB's "localized" means cultural adaptation, not
   post-editing; the least-bad target is "machine-translated and verified"
   with an explicit caveat that MTEB has no post-editing value. (b) No rows
   exist for `script_conversion` (no MTEB equivalent), `lm_generated` without
   verification (MTEB only has "LM-generated and verified"), `unknown`, or
   the `per_item_flags` verification state — state explicitly that these are
   unmappable rather than leaving them absent. The mapping direction
   (benchprov→MTEB) is lossy by design; say that the reverse direction is
   not defined.
5. **Completeness can flatter weak records** (§4.5): `name_only` and
   `conflicting` count as "known". This is a documented, defensible choice
   (information exists), but the interaction (a `complete` record built on
   name-only evidence is possible in principle) must be documented where
   consumers will see it. Current registry check: no record is
   simultaneously `complete` and name-only-based, and stats expose
   `records_with_name_only_claims` — adequate once documented.
6. **Native anchors resting on hub tags**: `source_datasets: original` is a
   self-declared hub tag; treating it as `verified` evidence for
   `native_original` is acceptable but worth one docs sentence
   (hub_metadata evidence = declaration by the depositor, not independent
   confirmation). Winogrande (M3) is the case where even that floor is
   missing.
7. **The registry's own numbers are sample-descriptive, not
   ecosystem-estimates.** 104 curated records were not sampled to be
   representative; "67/104 unknown" describes the seed, and the seed
   deliberately over-includes well-documented anchors (which *lowers* the
   unknown rate vs the ecosystem). This actually strengthens the argument —
   say it that way instead of implying representativeness.

**Evidence-to-claim audit coverage statement:** all 104 records were passed
through programmatic sweeps (value↔evidence-type coherence, quote-less
verified claims, unbounded wording, full review of every non-unknown
`human_verification` and every `none`/`full`/`partial`/`per_item` value, all
`per_item_provenance` blocks, all name_only claims); records not named in
§§2-4 were individually re-read against their quotes during the build's
evidence re-verification (207/207 items re-fetched, 0 hash/quote errors) and
are classified **ACCEPTABLE** as represented. The verifier's rendered-text
quote matching and the two gated-URL warnings (alibayram, flores_plus) are
documented behavior, not defects.

---

## 6. Recommended wording changes (exact replacements)

README:
1. L12-14 → "In a structured sample of 96 MMLU-variant datasets that carry
   non-English language tags or 'translated' naming, **65% matched none of
   our engine or human-verification patterns anywhere in their cards**."
   (Optionally add: "the sample includes a small number of native or
   synthetic variants — which only strengthens the point that variant
   provenance is not machine-readable.")
2. L10-11 "most don't say how they were made" → "most of the sampled
   variants don't say how they were made".
3. L24-25 EuroEval bullet: **verified during this audit** (EuroEval PR
   #2071 "Add EU-MMLU knowledge datasets for 14 languages", merged
   2026-07). Keep the bullet and add the PR link; also link the other three
   bullets' PRs/issues (lm-eval #2168, lighteval #372, MTEB #2665) so every
   demand claim is one click from its evidence.
4. L27-28 → "one small schema, one registry, every claim traceable to cited
   evidence — Hub evidence revision-pinned and hashed, quotes verbatim,
   naming-only support explicitly labeled."
5. L35-37 → per B3.
6. L38-40 → "67 of 104 records have no human-verification status
   determinable **from the sources consulted**; for 23, those sources name
   no translation engine; for 12 they do not even establish machine-vs-
   human."
7. L59 example → use the record's real current quote ("…translated by
   gpt-3.5-turbo.") or switch the example to a record whose card genuinely
   contains the famous typo (e.g. MMLU_Japanese, whose card does say
   "tranlasted"), with `(sic)` noted.
8. Limitations: add one bullet — "**`unknown` is search-bounded**: it means
   no statement was found in the sources each record cites (usually the
   dataset card at a pinned revision, sometimes one linked paper). It never
   means that no provenance information exists anywhere, and it never
   implies the creators did no verification."
9. "Use it" section: add the `--registry` note for non-repo installs (§4.11).

Implementation report: apply B3's fix; replace the local path with a
relative/repo-root reference; change "the documented ecosystem gap" →
"the gap documented across this seed"; note that the report predates this
audit and link here.

Records (wording-only, distinct from the factual fixes above): bounded
absence phrasing per M5; engine strings per M9; unknown-note standard per
§4.6.

---

## 7. Technical release concerns

Verified clean during audit:
- **Determinism**: `benchprov build --check` byte-exact on a fresh clone;
  canonical serialization (sorted keys, LF enforced via `.gitattributes` —
  the CRLF risk on Windows checkouts was identified and fixed pre-audit).
- **Clean checkout**: clone → `pip install -e ".[dev]"` → 49/49 tests →
  `validate` PASS → `build --check` up-to-date → stats OK (Windows,
  py3.12).
- **Secrets/tokens**: none found (pattern sweep over the tree; the HF token
  used for two gated-card fetches was never written to any file).
- **Personal information**: none beyond intended attribution (curator
  initials in `curated.by`, author name in LICENSE/pyproject — the
  maintainer's own identity). No third-party personal data beyond public
  hub usernames inside dataset ids/URLs.
- **Generated-vs-source boundary**: `registry/provenance.jsonl` is generated
  and CI-checked against `sources/records/`; no manually edited generated
  file is authoritative.
- **Docs links**: all relative links resolve.
- **Repo tree**: 253 tracked files, no `__pycache__`/venv/egg-info; working
  tree clean at HEAD.

Open concerns (checklist items, not blockers):
- **Linux untested locally** (Docker daemon down at audit time): the CI
  matrix covers ubuntu + windows but has never executed (no remote). Risk is
  low (pure Python, LF enforced, UTF-8 reconfigured in CLI), but the first
  push should be treated as the Linux test — check CI before announcing
  anything.
- **Dead-until-created URLs**: pyproject `Repository`, schema `$id` (§4.10).
- **Internal docs decision**: IMPLEMENTATION_REPORT (and this audit) contain
  internal context; decide publish-vs-exclude (§4.9). Recommendation:
  publish both after the M-fixes — the transparency is worth more than the
  polish, and this audit finding its own curator's errors is exactly the
  project's argument.
- **License compatibility**: MIT (code) + CC-BY-4.0 (data) + short quoted
  excerpts under quotation right — coherent; LICENSE-DATA already carries
  the quote disclaimer. Note that several *recorded datasets* are NC- or
  ND-licensed; the registry records facts about them and redistributes only
  metadata + quotes, which does not inherit their licenses — one sentence in
  LICENSE-DATA or README would preempt the question.
- **Evidence drift**: `verify_evidence.py` is on-demand; nothing re-checks
  evidence periodically. Fine for v0.1; note in README already covers it.

---

## 8. What the current artifact does and does not establish

**Established, with evidence in-repo:**
- **A. Missing provenance exists**: in the 96-dataset probe and in the
  registry's own seed (67/104 verification-unknown, 23 engine-unknown,
  12 method-unknown — all bounded by consulted sources). The seed
  over-represents well-documented anchor datasets, so these rates are, if
  anything, favorable.
- **B. Provenance is substantially recoverable**: the pre-registered
  40-dataset experiment (method recoverable ~74%, engine ~65%) and the
  registry itself (evidence-backed values for the majority of records).
- **C. Ecosystem demand for provenance distinctions exists**: lm-eval PR
  #2168 (merged MT notices), lighteval PR #372 (provenance-named tasks),
  MTEB PR #2665 (provenance metadata actively curated), EuroEval issue
  #2070 → merged PR #2071 (dataset added expressly for its human-translation
  provenance) — all third-party actions taken before and independently of
  this project.

**Not established:**
- **D. Adoption of this registry**: zero. No consumer, no citation, no
  integration, no endorsement, no contact with any maintainer. Nothing in
  the artifact may imply otherwise, and the README's Status section states
  this correctly.
- The registry is **not comprehensive** (~100 of thousands of variant
  datasets; README says so).
- Missing metadata **does not mean** a translation was undocumented anywhere
  (fix M5/B3 wording to keep this true everywhere).
- `human_verification: unknown` **does not mean** no verification occurred
  (README limitation bullet to be added, §6.8).
- Absence of a statement in a card **does not prove** absence elsewhere
  (same).
- Registry statistics describe the curated seed, not estimates of the full
  ecosystem (§5.7).

---

## 9. Final public-release checklist

Pre-conditions (from this audit):
- [ ] Fix B1 (Global-MMLU + taresco `is_annotated` semantics; verification
      value), B2 (xnli_bn parent), B3 (Kazakhstan count + bounding) in
      sources, rebuild registry.
- [ ] Apply M1-M2 verification reclassifications; M3 Winogrande evidence;
      M4 chained-status rule (docs sentence + demotions); M5 bounded
      wording; M7 EU-MMLU conflict; M8 aggregation kinds; M9 engine strings.
- [ ] Apply §6 README/report wording changes (incl. demand-evidence links
      and the two new limitation sentences); fix the README example record.
- [ ] Docs: copy/subset `translation_type` rule; completeness ≠ evidence
      strength; MTEB mapping corrections (hybrid row + unmappable values);
      hub-declaration caveat; NC/ND-datasets note in LICENSE-DATA or README.
- [ ] `benchprov validate` PASS, `build --check` clean, 49 tests green,
      `verify_evidence.py` 0 errors after all fixes.
- [ ] Re-read the ISSAI / kz-transformers / alibayram rows once more, in
      full, for tone and bounding (the sensitive-rows check).
- [ ] Decide: publish IMPLEMENTATION_REPORT + this audit (recommended) or
      exclude; if publishing, strip local paths / internal framing.
- [ ] Update stats quoted in README/report if fixes change them
      (M1/M2/M7 will: verification and state counts shift).

At publish time:
- [ ] Create the GitHub repository under the exact name in pyproject
      (`ahsan-h-shihab/benchprov`) so Repository URL and schema `$id`
      resolve; push; **verify CI goes green on ubuntu + windows** before any
      announcement.
- [ ] Tag `v0.1.0` after CI is green.
- [ ] Optional HF dataset mirror of `registry/provenance.jsonl` (own
      decision + card).
- [ ] No outreach, no PRs to third parties, no maintainer contact — the
      adoption experiment remains a separate, pre-registered decision.

Post-publish hygiene:
- [ ] Run `tools/verify_evidence.py` once against the published state and
      commit the report.
- [ ] Watch for the first external issue/PR; respond with the same
      evidence-first standard the records use.

---

## 10. Resolution log (corrective pass, 2026-08-24)

Scope note applied with the fixes: the project is framed globally
(multilingual benchmark provenance across the NLP ecosystem); the
kk/ru/bn/uz records are a regional/low-resource wedge and evidentiary
showcase, not the project's subject. An elevated evidence standard now
applies to ISSAI/KazLLM-related records because the project author has a
direct collaboration relationship with that ecosystem: public-card-bounded
wording only, no insider knowledge as evidence, "publicly unspecified"
never rendered as "undocumented".

| issue | resolution |
|---|---|
| **B1** | `coherelabs-global-mmlu__multi`: `human_verification` → `partial`, supported by the card's own "professional translations and crowd-sourced post-edits" statement; the `is_annotated` evidence item now quotes the card's actual definition ("True/False flag to indicate if sample contains any annotations from our cultural bias study") and the record states explicitly that it is a cultural-annotation flag, not a translation-verification flag, with a pointer to this audit. `per_item_provenance` removed (no translation-provenance flag exists). `taresco-…`: verification → `unknown`; the misdescribed per-item block removed; see also M4 below. Original claims preserved in git history; correction noted in-record. |
| **B2** | `csebuetnlp-xnli_bn__bn`: parent → `nyu-mll/multi_nli` (matching its cited quote); note explains the XNLI-procedure lineage and the correction. |
| **B3** | README and implementation report now say "the two independently published Kazakh MMLU translations, neither of which names a translation engine **in its dataset card**"; report figures marked as pre-audit with a pointer here. |
| **M1** | `mesolitica-…` and `nlpcoreteam-mmlu_ru__ru`: `none` → `partial` (informal, unquantified human checking is attested by their own cards; issues left uncorrected), with reclassification notes. `none` retained only where affirmed (murodbek ×2, KillerShoaib) or where the card's account describes a complete automated pipeline (Patt). |
| **M2** | `translated-mmlu-blind-review-…`: verification → `unknown`; `per_item_provenance` description now says METHOD flag explicitly. |
| **M3** | `allenai-winogrande__en`: WinoGrande paper added as evidence with a verbatim crowdsourcing quote; claim no longer rests on empty hub metadata. |
| **M4** | Chained-inference rule documented in `docs/schema.md` ("chained claims inherit the weakest premise's status") and applied: `finnish-nlp-…` creation/engine → `unknown` with the conditional spelled out; `taresco-…` creation → `name_only`, engine/verification/source → `unknown` with conditionals; `mizinovmv-…` and `ik-ram28-…` derivation → `name_only` (dataset-name support), with the YAML structure cited as corroboration where it directly supports a claim (`source_language` for mizinovmv). |
| **M5** | ISSAI shared note rewritten: bounded to "the dataset card … at the pinned revision; no public method statement was located in the sources consulted for this record. This bounds what the record can say — it does not imply the method is undocumented elsewhere." Program-level attribution ("the KazLLM program's benchmark translations") removed — records now attribute only to the publishing Hub organization. kz-transformers note similarly bounded. |
| **M6** | README: sample described accurately (96 MMLU-variant datasets with non-English tags or 'translated' naming; pattern-matching detection scope stated; native/synthetic contaminants acknowledged); "most" bounded to the sample; traceability sentence reworded (naming-only support labeled); example record quote corrected to match the registry; all four demand bullets now link their PRs/issues (including EuroEval merged PR #2071, verified during the audit). |
| **M7** | `ec-dgt-ai-eu-mmlu__mul` license modeled as `conflicting` (hub tag `mit` vs card's CC BY 4.0 statement, both quoted) — consistent with alibayram. Registry now carries 2 conflict records. |
| **M8** | `facebook-belebele__mul` and `csebuetnlp-squad_bn__bn` → `aggregation_of` with composition explained in notes; `source_language` correctly `not_applicable` with explanatory notes. |
| **M9** | Engine strings de-invented: MMMLU "(not further identified)"; jon-tow "(per the Okapi/mlmm project README)"; orai "manual translation (translating party not named in the card)"; Global-MMLU-Lite parties as described in the card; MGSM "(per Shi et al., 2022)". |
| Minors | Unknown-note bounding standardized across flagged records; DoggiAI source → `zh-Hans`; alibayram `pretty_name` restored as a verbatim hub-metadata quote; `evidence/README.md` added; docs: copy/subset `translation_type` rule, completeness ≠ evidence strength, MTEB mapping corrected (post-editing ≠ localization; unmappable values listed; direction stated), hub-metadata-as-declaration caveat, DD15 (naming/vocabulary debts), NC/ND note in LICENSE-DATA, `--registry` install note, seed-not-ecosystem statistics framing. |
| Additional (found while applying) | `kz-transformers/kk-socio-cultural-bench-mc`: creation was recorded as `mixed`, but its card describes one uniform hybrid process ("expert-curated topics with LLM-assisted web mining"), not item-level variation; under the elevated standard for Kazakh records it is now `unknown` with the card's description attached to the claim. |

**Intentionally left unresolved** (with justification): `translation_type`
field name and `mixed` overload (schema-breaking; deferred to v0.2 via
DD15); split-level provenance modeling (v0.2; XNLI documented as `mixed` +
notes); Linux CI execution (no local Docker daemon; CI matrix will run on
first push and must be green before any announcement); dead-until-created
repository URLs in pyproject/schema `$id` (resolve at publish time by
creating the repo under that exact name).

**Post-fix registry state**: 104 records / 100 datasets / 81 languages.
Creation: machine 46, native_original 22, unknown 14, mixed 9, human 9,
lm_generated 3, script_conversion 1. Verification: unknown 69, n/a 22,
partial 5, full 4, none 4 (per_item_flags: none remain). States: partial 76,
complete 25, conflicting 2, minimal 1. Records with name_only claims: 9.
Validation: schema+cross-field PASS (0 errors, 0 warnings); 49/49 tests;
`build --check` clean; evidence re-verification result recorded in
`evidence/verify_report_v01.txt` and `docs/CORRECTIVE_RELEASE_REPORT.md`.

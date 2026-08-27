# Adoption log — passive observation

benchprov is a **passive adoption experiment**: no outreach, no solicited
promotion, no unsolicited PRs. This log records observed signals only.
Discipline (from the project's own rules): stars are not adoption; adoption
is not upstream acceptance; traffic is not scientific impact. The signals
that would count as *usage*: an issue/PR from an unknown party, a tool or
paper consuming `registry/provenance.jsonl`, a citation, a record
contribution.

## Baseline (at publication)

| metric | value |
|---|---|
| recorded at (UTC) | 2026-08-25T03:00:09+00:00 |
| repository | https://github.com/ahsan-h-shihab/benchprov (public) |
| repository created (UTC) | 2026-08-25T02:54:45Z |
| release | v0.1.0 ("benchprov v0.1.0 — Benchmark Provenance"), published 2026-08-25T02:58:33Z |
| default branch / head | main @ 910f212 |
| CI | green (ubuntu-latest + windows-latest x py3.10/3.12) |
| stars | 0 |
| forks | 0 |
| watchers (subscribers) | 0 |
| open issues + PRs | 0 |
| repository traffic (views/clones) | not recordable headlessly (owner-only API); owner can snapshot via Insights -> Traffic |
| package downloads | n/a (not published to PyPI) |
| Hugging Face mirror | not created in this release |

## Observation entries

Append dated entries below; never edit past entries.

- 2026-08-25: baseline recorded at publication. No external signals yet
  (repository minutes old).

- 2026-08-27: **T1 checkpoint (~72h)** — stars 0, forks 0, watchers 0,
  issues/PRs 0 (all unchanged from T0). Owner-view traffic (14-day panel):
  views 18 / **unique visitors 1** (all views map to the owner's own
  publication-day and checkpoint sessions: Overview 14, /actions 1,
  /branches 1, /releases/new 1, /releases/tag/v0.1.0 1; sole referrer
  github.com); clones 27 / unique cloners 13 — consistent with 12 CI-runner
  checkouts (3 workflow runs x 4 jobs) + the owner's one post-publication
  verification clone. No package downloads (not on PyPI), no HF mirror, no
  dependents, no external references found (GitHub repo/issue search + web
  search: only unrelated namesakes, incl. TACC's "BenchPRO" HPC tool and a
  pre-existing oxsat branch from 2026-07-25). Assessment: no observable
  external discovery in this window. Full analysis:
  `docs/ADOPTION_CHECKPOINT_1.md`.

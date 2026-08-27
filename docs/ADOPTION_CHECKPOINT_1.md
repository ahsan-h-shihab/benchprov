# Adoption checkpoint 1 — passive observation, ~72 hours

Read-only audit; nothing in the repository, registry, or release state was
changed for this checkpoint (this document and one append-only log entry are
the instructed outputs). Metrics from the public GitHub API plus the
owner-visible Traffic panel (Insights → Traffic), read 2026-08-27 ≈20:40 UTC.

## 1. Observation window

Publication (T0): 2026-08-25T02:54 UTC (repo created), v0.1.0 released
02:58 UTC. This checkpoint (T1): 2026-08-27 ≈20:40 UTC — ~2.7 days. No
outreach, announcements, cross-links, or engagement actions of any kind were
performed during the window (passive-experiment protocol).

## 2. Current metrics (T1)

| metric | value |
|---|---|
| stars | 0 |
| forks | 0 |
| watchers (subscribers) | 0 |
| open issues | 0 |
| open PRs | 0 |
| issues+PRs ever created | 0 |
| Traffic — total views (14-day panel) | 18 |
| Traffic — unique visitors | **1** |
| Traffic — clones | 27 |
| Traffic — unique cloners | 13 |
| Traffic — referring sites | github.com only (14 views / 1 unique) |
| Traffic — popular content | Overview 14·1, /actions 1·1, /branches 1·1, /releases/new 1·1, /releases/tag/v0.1.0 1·1 |
| package downloads | n/a (not published to PyPI) |
| HF mirror metrics | n/a (no mirror) |
| dependents (dependency graph) | 0 |
| external references found | 0 (see §5) |

## 3. Delta from T0

Social metrics: 0 → 0 across the board (no change). Traffic metrics had no
T0 baseline (the panel needs time to populate); the 14-day panel above
therefore covers the whole life of the repository. Repository content delta
since v0.1.0 remains docs-only (adoption log, checkpoint docs, one README
sentence, topics) — registry/schema/code untouched.

## 4. Traffic interpretation

The traffic is almost fully attributable to the project's own operations:

- **Views (18, 1 unique visitor).** Every listed content path matches the
  owner-session activity from publication day and this checkpoint (repo
  Overview during setup and metadata edits, /actions while verifying CI,
  /releases/new and /releases/tag/v0.1.0 while publishing the release,
  /branches once). One (1) unique visitor across all paths and the sole
  referrer being github.com itself means **no distinct external person is
  visible in the view data at all**. GitHub counts owner visits in Traffic;
  that is what this is.
- **Clones (27, 13 unique cloners).** Known self-generated clone activity:
  GitHub Actions checkouts (3 workflow runs × 4 matrix jobs = 12 ephemeral
  runner identities) plus the owner's single post-publication verification
  clone = 13 — exactly the number of unique cloners observed. The clone
  count is therefore **consistent with zero external clones**. Caveat: this
  is consistency, not proof — one or two external anonymous clones replacing
  assumed CI identities cannot be strictly excluded from aggregate counts,
  but nothing in the data requires them.
- **Stars-vs-traffic discipline:** no inference from stars was made in
  either direction; traffic was read from the analytics panel directly.

## 5. Evidence for/against organic discovery

Against (all observed):
- 1 unique visitor over ~72 h, attributable to the owner.
- Referrers contain no search engines, no aggregators, no external sites.
- GitHub repository search for "benchprov" returns the repo (it **is**
  indexed and findable by name), but nobody searching arrived.
- GitHub issue/PR search across GitHub finds no mention of the project;
  the only textual matches are unrelated namesakes (a `benchprov` branch in
  `evan-a-w/oxsat` created 2026-07-25, predating this repository; and the
  separate HPC tool "BenchPRO"/`benchpro-db` by TACC).
- Web search for "benchprov" + benchmark provenance surfaces only those
  unrelated namesakes and generic provenance-benchmarking literature.
- No dependents, no downloads channel, no forks, no issues.

For: nothing. There is no positive discovery signal of any kind in this
window.

One discoverability observation for the record (no action taken): the
name-adjacent, older project **BenchPRO** (TACC's benchmark orchestrator,
with a `benchpro-db` provenance backend) occupies neighboring search space;
"benchprov" vs "benchpro" is a one-letter distinction that search engines
may conflate. Not a problem today (there is no search traffic to confuse),
but worth remembering when interpreting future referrer data.

## 6. What remains unknown

- Whether search engines have indexed the repository yet (no crawler-driven
  referrals appear, but GitHub pages are typically indexed within days —
  unverifiable from this side without waiting).
- Whether topic-page browsing produced any impressions that did not become
  visits (GitHub exposes no impression data).
- Whether any of the 13 cloners was a genuine external party (aggregate
  counts cannot resolve this; assessed unlikely per §4).
- Anything about *quality* of positioning: with zero external viewers, the
  README/topics have effectively not yet been tested against a single real
  reader.

## 7. Verdict and recommendation

**Verdict: A — no meaningful discovery — with a D qualifier.** The data is
unambiguous that no external person visibly discovered the repository in
this window (this is not "discovery without conversion"; there were no
discoverers). The D qualifier: ~72 hours is too short to conclude the
artifact *cannot* be discovered organically — search indexing, topic
browsing, and incidental encounters operate on week-to-month timescales,
and the experiment has produced zero information about how the artifact
performs *when seen*, because it has not yet been seen.

**Recommendation (assessment only; the decision is the owner's):** continue
the passive window to roughly the two-week mark (T2) — this costs nothing,
completes a fair organic-discovery test, and lets search indexing mature.
If T2 still shows no external signal, the discovery-phase evidence already
predicted this outcome: provenance consumers act through *carriers*
(harnesses, leaderboards), not through search. The right next step then is
a **single controlled intervention** — the smallest observed-genre
contribution at one named carrier (per the implementation report §7:
MTEB-style metadata or an lm-evaluation-harness task-README provenance
note citing the registry), designed so that a merge/non-merge is itself the
measurement. No such intervention has been taken or prepared beyond this
sentence.

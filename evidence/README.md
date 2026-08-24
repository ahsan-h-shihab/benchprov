# Evidence directory

- `snapshots/<dataset-slug>.json` - pinned raw-evidence extracts per dataset:
  hub revision sha, pinned README URL + SHA-256, hub metadata, candidate
  provenance lines. Produced by `tools/fetch_evidence.py`.
- `snapshots/_*.json` - supplementary evidence extracts gathered during
  curation (targeted paper/page quote pulls). The underscore prefix marks
  them as cross-dataset extracts rather than per-dataset snapshots; they are
  part of the evidence trail, not scratch.
- `verify_report_v01.txt` - output of the last full run of
  `tools/verify_evidence.py` (re-fetches every cited URL; checks hashes and
  verbatim quotes).

Nothing in this directory is consumed by the validator or CLI; it exists so
curatorial claims can be audited and reproduced.

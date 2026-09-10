# Anchored Residual Target-Basin Modes v2 — frozen rule

This is the single structural revision after v1: preserve current Fast geometry rank-0 exactly, and use
the already frozen v1 residual-mode score only to choose entries 2 and 3 from current ranks 1..31.

- Mode model, fit rows, score, candidate shortlist, and all constants are identical to v1.
- Entry 1 is always the current Fast rank-0 hub.
- Entries 2 and 3 are the two highest residual-mode scores among current Fast ranks 1..31.
- No utility, Recall, NDC, GT, trace, or validation label is used during routing.
- Online overhead remains 64 mode dot products over the existing top-32 shortlist.
- Non-vacuity: at least 1% of top-3 sets must change.
- Acceptance: new Recall@10 and frozen utility must not be below Fast on both datasets and `L=64/128`.

Validation remains a development split.  Held-out stays untouched; no held-out run is authorized by this
diagnostic alone.


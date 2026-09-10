# P3 saved-structure evidence audit

`analyze_structure.py` reads the two completed partition manifests, their saved
JSON evidence, the frozen P3 protocol and 23 compact u16 label files per dataset.
It never opens graph, GT, base, query vectors, pilot, validation or held-out
inputs, and it never runs partitioning, fitting, search or a new significance
test. Root launches the actual analysis serially after measured search work.

The input directory is accepted only if its source/protocol/P2 gate bindings
match the accepted P3 implementation and preregistration, both branches are
complete, and both fixed two-pass histories are present. The audit then checks:

- Fresh SHA256, shape, ID range and all-node coverage for the common initial,
  raw coarse, canonical coarse, 16 raw child and four complete-pass labels.
- Exact coarse canonicalization by minimum base ID, initial leaf reconstruction
  from the child labels, the initial coarse1.1 bound, each child global leaf
  bound, library epsilon arithmetic, min3 and all final global leaf/coarse caps.
- Identical initial-state SHA for lambda0/1 and exact equality between embedded
  and separately saved initial/branch/pass JSON evidence.
- Original-directed slot totals and consistent M/Q; integer C/S bounds,
  numerator/denominator algebra, coarse-versus-leaf bounds and every derived
  stored floating statistic.
- Per-pass C/S incremental totals, exact integer J change, recorded independent
  full-recompute results, lambda0 GT-move isolation and two-pass completion.
  Because every node is visited once per pass, the actual number of changed
  labels must equal accepted moves, and changed parent IDs must equal reported
  cross-coarse moves.

The analyzer does **not** independently recover C/S from graph/GT. It audits the
partition implementation's saved full-recompute evidence and integer algebra,
while independently recomputing label-based sizes, canonicalization and change
counts. It inherits graph/GT/audit/source/binary input identities from the
accepted partition manifests; only protocol and saved evidence files are
freshly read here.

For both datasets it reports final lambda1-minus-lambda0 C, S, normalized fit
fragmentation, mean distinct fit leaf regions and J evaluated at lambda1. The
J comparison uses exact integer numerators with the common denominator. Both
strict inequalities required by the structure condition are recorded, together
with `P3_gate_passed=false` and `search_gate_evaluated=false`; successful
structure evidence cannot substitute for the paired oracle search gate.

Cost output separates measured symmetric-CSR stages, coarse/child METIS plus cut
verification, incoming CSR, GT10 load/validation, initial full objective,
lambda0/1 branches and GT incidence construction. Branch detail separates
refinement from full recomputation plus label snapshot. Initial induced-CSR
construction and canonicalization were not individually timed, so full
initializer wall is explicitly null. The remaining total wall is reported as
an unitemized subtraction residual with its limitations, without assigning it
to an invented phase. Reused exact-GT cost remains unknown, not zero.

From `/data/netg/ACSG`, after inspecting `--help`:

```bash
.venv_cpu/bin/python hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/analyze_structure.py \
  --partition-manifest hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/partitions/webvid2_5m_light_v1/manifest.json \
  --partition-manifest hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/partitions/yandex_t2i_official10M_ip_v1/manifest.json \
  --protocol hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/protocol.json \
  --output hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/structure_analysis_v1
```

The output directory must be new. Completion writes per-dataset JSON,
`analysis.json` and checksum-bearing `complete.json`; a rejected or incomplete
input leaves `failure.json` and does not become a method NO_GO conclusion.
The internal soft deadline is 2026-09-07 22:59 UTC.

`test_structure_analysis.py --output NEW_DIRECTORY` generates only small
4096-node/32-query evidence fixtures. The initial test validates all 23 label
files and rejects 11 deliberately damaged cases: delta algebra, full-recompute
flag, initial-state identity, cross-coarse move count, lambda0 GT state,
incomplete pass history, label hash, capacity/minimum violation, path escape,
incomplete top-level output and P2 gate binding. A file-open guard confirms that
only generated fixture JSON/u16 files are read. Evidence is
`structure_analyzer_synthetic_v1/result.json`; actual partitions have not been
analyzed by this implementation agent.

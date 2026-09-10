# Frozen objective local-scale audit

`diagnose_objective_local_scale.py` implements only
`objective_local_scale_protocol_v1.json`, SHA256
`abae80a4a2bbf6366e413b21a948a6fa4f27166e1160973cc223681e75cfff91`.
The P3 NOPASS gate remains unchanged. This is a finite descriptive audit, with
no search, fitting, parameter change, new model, new interval or gate reopening.

The root must launch actual inputs serially through the existing controller.
Preparation and synthetic tests do not run the actual graph, GT or labels.

```bash
.venv_cpu/bin/python hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/diagnose_objective_local_scale.py --help
```

Actual command arguments for a new root-controlled output, from
`/data/netg/ACSG`:

```bash
.venv_cpu/bin/python hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/diagnose_objective_local_scale.py \
  --protocol hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/objective_local_scale_protocol_v1.json \
  --output hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/objective_local_scale_diagnosis_v1
```

The output must be new. Internal checks close at 22:59 UTC; the controller
owns the hard deadline, single-heavy-process rule and resource enforcement.
Full-file SHA, numeric adjacency scan and fixed-group summaries are timed
separately. Progress includes checksum bytes, adjacency rows and the last
completed summary group.

## Read boundary and integrity

Before numeric inputs, the script verifies the fixed protocol hash and every
bound P3 gate/protocol, P0 audit, completed target diagnosis and completion
marker, algebra, independent algebra review, partition and fit manifest.
The exact checksum-bound P0 `graph_header` source is imported solely to reparse
the small native header and length metadata. Importing that module does not
execute its audit entry point.

For provenance, a streaming SHA256 reads the complete frozen graph file,
including embedded-vector bytes as uninterpreted bytes. It does not create
a base-vector array or perform vector arithmetic. The graph-info JSON hash
is rechecked. The native header must equal P0 exactly; graph device, inode,
size and modification time must remain unchanged across the audit.

Numeric graph reads use 65,536-row blocks starting at the existing unaligned
adjacency offset. Each block is decoded as little-endian int32. Numeric reads
must end exactly at the adjacency boundary, before embedded-vector metadata
and payload. Only `-1` is padding; every other negative or out-of-range ID is
an integrity failure. Self arcs are counted for comparison with P0 and then
excluded from the objective degree. Duplicate and reciprocal directed arcs
are retained with their original multiplicities.

Incoming and outgoing degrees use int64 arrays. A per-block `bincount` is
indexed by validated node IDs and has exactly the known number of base nodes;
it is never indexed by maximum degree. The scan must reproduce P0 padding,
self and valid-slot counts, the partition/algebra M, and all conservation
identities: sum in = sum out = M and sum total = 2M.

The other numeric inputs are only the existing extracted 20K by 10 fit GT10
file and the three compact saved label arrays: common initialization,
lambda0 final, lambda1 final. Hashes, GT shape/valid IDs/unique ten per row,
label coverage/range/minimum/capacities, shared initialization, fit incidence
counts and fixed final-label movement counts are rechecked against the
completed target diagnosis and partition metadata. First-pass labels, pilot
GT, query vectors, standalone base vectors, validation, held-out, search
counts and timing files are not opened.

## Exact condition and fixed groups

`D(u)` is original valid nonself incoming plus outgoing slot count. The audit
evaluates `D(u) * (9 * Q) < M` with int64 arithmetic after an explicit overflow
bound check; Q is 20,000. Equality is excluded. The reported integer cutoff
is the first integer degree that does not satisfy the strict condition.

All 31 fixed groups are retained:

- Three support populations: all nodes, fit-seen nodes, and unseen nodes.
- Ten fixed fit-frequency intervals: 0, 1, 2, 3, 4, 5–9, 10–19, 20–49,
  50–99, and at least 100.
- Eighteen movement cells: three final-label comparisons, each changed and
  unchanged, crossed with all/seen/unseen support.

Frequency is the number of fit GT10 query rows containing a node; unique
targets per row make it equal to occurrence count. Per-group reports include
unique node count, sum of fit occurrences, satisfying node count/fraction,
satisfying fit-occurrence count/weighted fraction, and in/out/total degree
mean/min/max. Fit-occurrence weighting does not create independent queries;
an empty weighted denominator is null. Frequency bins exhaust nodes exactly
once. Changed and unchanged groups exhaust each support population, and the
changed counts must match completed target-diagnosis evidence.

The total-degree quantile levels are fixed at 0, .25, .5, .75, .9, .95, .99
and 1. They use the exact empirical inverse CDF: zero-based index
`max(0, ceil(p * n) - 1)`. Decimal levels are converted to rational integers
before calculating rank, with no interpolation or floating-rank rounding.
Empty groups have null degree statistics and quantiles. Sparse value/count
histograms use sorting/unique on observed degrees; no allocation depends on
the largest degree. The optional all-base histogram is subject to the frozen
1 MiB cap and must be omitted with a reason when it does not fit. The cap
applies to the **complete standalone compact JSON artifact**, including its
metadata and final newline. Per-dataset and top-level reports contain only
its path, SHA256, byte count and encoding metadata; they do not duplicate the
pair arrays. An omitted histogram creates no histogram file.

## Outputs and limits

The root output contains a complete per-dataset JSON and a combined
`diagnosis.json`, plus a completion marker only after both datasets finish.
All sources and numeric inputs have explicit hashes. No node IDs, GT arrays,
degree vectors or million-row tables are dumped. An interrupted/error run
preserves its output and writes an INCOMPLETE failure record with the last
phase and cursor; it cannot produce a completed stage gate.

Satisfying the degree condition means that any **feasible candidate** for
that node with integer `DeltaS <= -1` strictly improves the lambda1 objective
regardless of its cut increment. This is sufficient only. It does not show
that such a candidate exists, is feasible, is selected, or explains a final
search outcome. This audit does not reconstruct accepted moves, their
actual DeltaC/DeltaS or temporal order. An unseen node has local DeltaS zero,
but its trajectory can still depend on other GT-aware moves, neighborhoods
and capacity states. Final-label differences are not sequential-move counts.
Support, degrees, labels and retrieval are correlated; no causal attribution,
memorization proof, connectivity failure or new auxiliary graph follows.

## Synthetic validation

`test_objective_local_scale.py --output NEW_DIRECTORY` generates all numeric
fixtures locally. `objective_local_scale_synthetic_v3/result.json` records
30 test groups, including the four-node duplicate/reciprocal/self/padding
example and three independently counted random graphs, native unaligned
header/adjacency and read-boundary guards, conservation, strict equality and
int64 overflow boundaries, sparse huge-degree histogram/byte cap, exact
quantiles, all 31 summaries checked against independent Python loops and
sorting, support/movement mismatch rejection, GT/label validity, and a
fixture-only filesystem/NumPy read guard. Histogram tests also check the
complete standalone cap, metadata/newline overhead, fresh SHA/byte binding,
report nonduplication and absent file on omission. The prior v1 fixture remains; it
stopped on a test-harness JSON clone of NumPy integer metadata. A harness-only
deep-copy fix resolved it without changing production source.

Final production review freeze after the root's histogram output-contract
clarification: `148e3ff29259857865e9916f5f3905f2f2d1ffd3c1d843bfd8909a16c18259c8`.
The numerical logic is unchanged. Original `19668fd8...` source, test and
README are preserved under
`objective_local_scale_source_before_histogram_artifact_v1/`, alongside the
unchanged v2 test results. Independent review and any later revision must
name their exact source SHA.

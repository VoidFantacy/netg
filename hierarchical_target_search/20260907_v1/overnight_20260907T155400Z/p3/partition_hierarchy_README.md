# P3 hierarchy partition implementation

`partition_hierarchy.cpp` implements only the preregistered P3 common graph
initialization and two structure branches. It does not choose portals, run ANN
search, train a routing model or issue the P3 research gate. The P2 source and
artifacts are preserved. The current accepted P3 protocol is pinned by full
SHA256 `fea64bc3c6a8046378849f55508198dcfd9a00df880a74e9d93cf22d051a418f`.

## Initialization and exact refinement

The helper opens the original native-v1 IP NSG with `O_RDONLY` and maps only its
adjacency segment. Native unaligned int32 slots are read using `memcpy`. The
copied P2 parser, temporary symmetric-CSR construction and SHA256 helper remain
local to this new P3 source; it does not include or modify the P2 executable.

One common initialization covers every base node. It first runs fixed-seed
METIS16 with coarse cap `floor(11*N/(10*16))`. For each canonical coarse region,
it builds one induced symmetric CSR in RAM with ascending global-to-local IDs,
then runs METIS16 with target `16*F/actual_coarse_size`, where
`F=floor(6*N/(5*256))` is the global leaf cap. The explicit ubvec conservatively
rounds down and compensates METIS's internal `0.0000499` addition. Final integer
checks remain authoritative. Seeds are always 2026090711, ncuts1/niter10,
numbering0. Coarse IDs and child IDs are canonicalized once by their smallest
base ID, producing `leaf=coarse*16+child`. Every leaf must contain at least three
nodes. No capacity repair, relaxed cap, replacement seed or old P2 region reuse
is available.

The symmetric CSR is released before refinement. A separate incoming CSR
stores original source IDs as int32 and offsets as uint64. It excludes padding
and self slots while preserving stored duplicates, directions and reciprocal
edges. Objective cut `C` and total `M` always count those original directed
valid nonself slots. The GT term `S` is the sum over fit queries of the number of
distinct GT10 leaf regions minus one; `J=C/M+lambda*S/(9*Q)`.

Both lambda branches copy the exact same saved initial labels. Each executes
two ascending-base-ID passes. Candidate leaf IDs come from incoming/outgoing
neighbors and, for lambda1 only, the node's incident fit GT10 queries. The
feasible destination with the most negative exact signed `__int128` numerator
`deltaC*(9*Q)+lambda*deltaS*M` is chosen, with ascending destination leaf ID for
ties. Moves immediately update labels, leaf/coarse sizes and, for lambda1,
per-query leaf counts. Both final caps are checked on every move, and the source
leaf must retain at least three nodes.

Lambda0 executes before the GT incidence index is constructed. Its compiled
move path rejects non-null GT state and never generates candidates from GT or
updates query counts. Its GT fragmentation is recomputed only in the independent
post-pass structure scan. Lambda1 uses 200,000 GT incidences and a `Q*256` uint8
count matrix; no `N*256` array is allocated. Candidate degree/presence scratch is
reused with generation markers, avoiding a 256-entry clear for every base node.

After each complete pass, the code independently scans original directed slots
and GT10 rows and checks the exact cut/objective delta, strict descent whenever
any move occurred, full per-query count state for lambda1, all-node coverage,
both capacities and the minimum leaf size. Coarse cut/fragmentation are reported
separately and do not enter move selection.

## Input and output contracts

Actual runs require the root's single-heavy-process controller, current P0
audit, checksum-bound P2 PASS gate, exact frozen P3 protocol and root-generated
fit manifest. The helper additionally requires at least 60 GiB `MemAvailable`
and 10 GiB free disk before partitioning. The controller enforces the run-wide
8 GiB artifact limit and task identity/deadline protection.

The fit manifest must provide:

```json
{
  "status": "COMPLETE",
  "stage": "P3",
  "dataset": "REGISTERED_DATASET",
  "fit_range": [10000, 30000],
  "fit_count": 20000,
  "heldout_accessed": false,
  "pilot_accessed": false,
  "input_audit_sha256": "CURRENT_P0_FILE_SHA256",
  "protocol_sha256": "FROZEN_P3_FILE_SHA256",
  "fit_gt_values_sha256": "P0_FIT_TOP100_VALUES_SHA256",
  "gt10_file": "/absolute/path/gt10.i32",
  "gt10_sha256": "RAW_GT10_FILE_SHA256"
}
```

`gt10.i32` is raw little-endian int32 `[20000,10]`, in the original fit-row order
10000 through 29999. The helper hashes this 800,000-byte file, checks all IDs
and requires each GT10 row to contain unique IDs. It never reads the parent GT
file, query vectors, base vectors, pilot, validation or held-out data. Full
top100 fit identity is inherited from the checksum-bound root extractor and
matched to P0. Full graph SHA is inherited from current P0; graph header and
length are freshly checked.

The output directory must not already exist. Principal outputs are:

- `initial/regions.u16`: common canonical initial labels; the initial manifest
  also binds coarse/child METIS labels, capacities, library ub factors and
  independently checked cuts. Actual failed child/coarse labels and diagnostic
  JSON are retained before an initialization error is rejected.
- `lambda0/pass1.regions.u16`, `pass2.regions.u16`, and the corresponding
  lambda1 files: complete-pass snapshots with SHA256, full objective, structure
  statistics and incremental-verification results in sibling JSON files.
- `lambda0/manifest.json` and `lambda1/manifest.json`: `COMPLETE` only after
  their two passes succeed. Flat fields include `stage`, `dataset`, `n`,
  `nodes`, `regions=256`, `coarse_count=16`, `leaves_per_coarse=16`, numeric
  `lambda`, absolute `labels_file` pointing to pass2, `labels_sha256`,
  `initial_labels_sha256`, `protocol_sha256`, `input_audit_sha256`,
  `fit_manifest_sha256`, `fit_gt_values_sha256`, `input_graph_sha256`,
  `source_sha256` and `binary_sha256`.
- Top-level `manifest.json`: complete only when both branches complete. This
  completion is algorithm execution/correctness, and never P3 search-gate PASS.

Periodic refinement progress records the next ascending node cursor and
accepted-move totals, prints measured throughput/ETA, and retains compact state
on interruption. A caught stop/error writes an `INCOMPLETE` branch manifest and
`incomplete.regions.u16`; no extra objective scan is started after stop.
Completed pass snapshots remain intact. During METIS, the outer controller
provides interrupt/kill protection because its C call has no internal callback.
The fixed internal soft close is 2026-09-07 22:59 UTC. The helper does not resume
an interrupted half-pass automatically or mark interruption as research success.

## Build, tests and launch

From `/data/netg/ACSG`, first inspect the build helper's `--help`, then build into
a fresh directory:

```bash
.venv_cpu/bin/python hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/build_partition_hierarchy.py \
  --output hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/NEW_BUILD
```

The helper records the exact standalone g++ command and source snapshot. It
uses existing METIS/GKlib and nlohmann-json include/library paths, without CMake
changes or downloads. `P3_SOURCE_SHA256` is embedded at compile time; actual
runs reject a runtime source file whose SHA differs. `--sanitize` adds ASan and
UBSan. Source/build snapshots and logs are preserved for every attempted build.

The release currently prepared for independent review is
`partition_build_v4/partition_hierarchy`. Run its `--help` before use. Under the
root controller, the actual invocation is:

```bash
hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/partition_build_v4/partition_hierarchy \
  --graph /ABSOLUTE/FROZEN/GRAPH \
  --dataset REGISTERED_DATASET \
  --audit hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p0/full_audit/audit.json \
  --gate hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P2.json \
  --protocol hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/protocol.json \
  --fit-manifest hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/fit_inputs/REGISTERED_DATASET/manifest.json \
  --output NEW_PARTITION_DIRECTORY \
  --threads 16
```

The default source path is its absolute compiled `__FILE__`; `--source-file` is
available for an identical preserved source snapshot. There are no lambda,
number-of-passes, seed or capacity tuning flags.

Synthetic tests use `--self-test --output NEW_TEST_DIRECTORY --threads 2` and
never open actual graph/GT files. They include 336 exhaustive node/destination
delta comparisons, an independent GT-free brute-force lambda0 reference, an
independent full-J lambda1 reference, two-pass determinism, directed/reciprocal/
duplicate/self/padding cases, all GT count edge cases, exact ties, zero-delta
rejection, GT-only lambda1 candidates, both caps and min3, canonical and induced
CSR checks, failed-structure persistence, complete/interrupted branch metadata,
and a 4096-node full16x16 initialization followed by both two-pass branches with
leaf ID255 represented in GT counts. Existing release evidence is
`partition_synthetic_v3/manifest.json`; current sanitizer evidence is recorded
separately in `partition_sanitizer_synthetic_v2/manifest.json` after completion.
These are implementation checks, not measured results on either real dataset.

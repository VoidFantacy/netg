# Frozen P3 target-generalization diagnostic

This implements only `target_generalization` in the preregistered
`diagnosis_protocol_v1.json` (SHA256
`4bdd1cd92b42d85f89bd69aec980068c9bed0d5aee90917d5ce2ad8db9823959`).
It describes the completed negative P3 branch. It neither changes the NOPASS
gate nor authorizes P4, another fit, a new predictor, a portal change, a graph
change, or a parameter selection.

The root process must launch the real run serially through the existing stage
controller. This script was prepared and tested with generated fixtures only.
Do not run a separate actual-input diagnostic beside plain search timings.

```bash
.venv_cpu/bin/python hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/diagnose_target_generalization.py --help
```

Arguments for the root-controlled real invocation, from `/data/netg/ACSG`:

```bash
.venv_cpu/bin/python hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/diagnose_target_generalization.py \
  --protocol hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/diagnosis_protocol_v1.json \
  --audit hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p0/full_audit/audit.json \
  --output hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p3/target_generalization_diagnosis_v1
```

The output directory must be new. The script stops at the frozen 22:59 UTC
soft deadline. The controller owns global CPU, disk, artifact and hard-deadline
enforcement. The expected runtime is tens of seconds, chiefly parsing the
eight saved count JSON files serially; the expectation is not a measurement.

## Input boundary and integrity

Before any GT, label, or count-file read, the script verifies the fixed
diagnostic protocol hash and its P3 NOPASS gate, completed main analysis,
completed structure analysis, P0 audit, all four models per dataset,
partition/branch manifests, and the shared fit extraction manifest. Every
model/count and needed label identity must agree with the bound completed
analyses. The same initial-label hash binds both branches.

For each dataset it reads the five existing compact little-endian uint16
label arrays: common initial, each branch's first pass, and each final pass.
It rehashes all five and rechecks full coverage, minimum three nodes per leaf,
and the frozen integer leaf/coarse capacities. First-pass labels are used only
to count movement.

The fit input is the existing `gt10.i32`, 20,000 by 10 little-endian int32,
whose SHA and manifest/P0 full-fit identity are verified. Each row must have
ten distinct valid target IDs. It does not reopen the full fit GT parent or
fit query vectors. The full-fit top100 hash is inherited from the audited
manifest, while the extracted top10 file is independently rehashed.

For pilot GT, the script performs one bounded read of the first 10,000
physical top100 ivecs records: exactly 4,040,000 bytes. It checks all 10,000
per-record headers and hashes all 1,000,000 pilot GT values against P0 before
using ranks 0 through 9. It only stats the full parent size; it never hashes
the parent, seeks into its fit suffix, or performs an EOF probe. The report
records the physical read bound and the verified pilot-value hash.

It reads no graph adjacency, base vectors, query vectors, validation or
held-out files, portal vectors, timing files, or probe cache values. The four
models' count JSON files are consumed one at a time. Only the oracle rows
are analyzed; Fast's unmeasured frontier-counter zero sentinels are excluded.

## Quantities and denominators

`D` is the number of distinct leaves containing a query's ten GT targets;
normalized fragmentation is `(D - 1) / 9`. For every query and each of the
three structures, all 256 leaves are sorted by descending GT10 count and
ascending leaf ID for ties. `M4` is the absolute number of GT targets in the
selected four leaves divided by ten. The saved oracle weights condition on
those four leaves and sum to one; they are not absolute M4.

Support is `f(u)`, the number of fit-GT10 queries containing node `u`. Because
each fit row has ten unique IDs, an occurrence count is also a query count.
A target is seen exactly when `f(u) > 0`. All fit targets are necessarily
seen; an empty subgroup ratio is JSON null.

For seen and unseen targets, coverage uses the same full-GT selected four
leaves. Covered-seen divided by ten plus covered-unseen divided by ten equals
full M4 exactly. Optional conditional target coverage uses the corresponding
number of target slots. It does not select a different top4 for a subgroup.
`D_seen` and `D_unseen` can share leaves and are not additive; their conditional
means exclude queries with no targets in that group and must be read with the
target counts.

The report distinguishes all-base unique-node denominators from pilot GT10
target-slot denominators. A node repeated in many pilot queries counts once
in the former and multiple times in the latter. Movement measures include
final leaf/coarse change from common initialization, any change in either
pass, and final lambda1/lambda0 differences. A node moving in pass1 then
returning to its initial leaf in pass2 has no final change but does have an
any-pass change.

Fit and pilot summaries retain every exact D bin from 1 to 10 and covered
target-count bin from 0 to 10. Every pilot support stratum `k_seen = 0..10`
is retained, including empty bins, and the bins must account for all 10,000
queries. Structure deltas explicitly name candidate and reference:
lambda0 minus initialization, lambda1 minus initialization, and lambda1
minus lambda0.

## Saved-search verification and comparisons

The diagnostic independently reconstructs each oracle row's selected region
IDs and tie order from the actual pilot GT10 plus final labels. IDs and
target counts must match exactly; conditional weights use a fixed absolute
tolerance of `1e-12` to allow the C++ `count * 0.1` summation and equivalent
integer-count normalization. Within each model, full saved routes must be
identical across queues and both L values. Frequency/greedy models of the
same branch must both reproduce the same full-GT regions and weights.

Each saved result contains ten IDs, with unique valid IDs and optional `-1`
padding. Actual GT/result intersections reconstruct total, seen and unseen
hit counts. Reconstructed Recall must match every saved Recall value and
batch mean. Total/seen/unseen hit counts and their paired deltas decompose
exactly. Instrumented oracle NDC/MAC/counters must be nonnegative integers;
routing plus graph counts must equal totals.

All original eight fixed P3 contrasts are reported for L64 and L128 on both
datasets. Their reconstructed Recall means, query gain/loss/equality counts
and reported NDC/MAC deltas must reproduce the completed main analysis.
Exactly two additional preregistered descriptive contrasts compare lambda1
minus lambda0 under `oracle_unified`, once for frequency3 and once for
greedy3. Each contrast includes the full-query summary and all eleven exact
`k_seen` strata. There are no new confidence intervals, p values or gates.

NDC, expansions, rejections and evictions are query-level measurements. They
are summarized within query support strata; none is allocated to seen versus
unseen target IDs. Equal Recall means equal hit counts, not necessarily an
identical top10 result set.

## Outputs and interpretation

Each dataset gets `diagnosis.json`, compact `fit_metrics.npz`, and compact
`pilot_metrics_and_search.npz`. NPZ arrays contain parent query IDs, support
counts, structure metrics and derived oracle hit/counter arrays. They do not
duplicate raw GT, raw result-ID arrays, or millions of base-node rows. The
top-level `diagnosis.json` contains both dataset summaries and artifact SHA
bindings; `complete.json` appears only after both complete. A failed run
preserves its output and writes `failure.json` with INCOMPLETE status.

The script also recomputes all three structures' fit fragmentation from the
saved labels and extracted GT10, and checks it against accepted partition
full-recomputation evidence. It does not independently recompute graph cuts.

Finite fit/pilot differences can reflect distribution shift. Support is
correlated with popularity and density, and shared target IDs do not imply
query leakage. Memorization and overfit remain hypotheses. This is oracle
routing, so it cannot diagnose a learned predictor's generalization. The
lambda contrast also changes oracle selection, queue membership and rebuilt
portals. Better abstract target concentration with worse Recall does not
isolate a connectivity cause or prove structural unreachability.

## Synthetic validation

`test_target_generalization.py` creates only small generated fixtures. Run it
with a new `--output` directory. The first validation is preserved at
`target_generalization_synthetic_v1/result.json`: 31 positive/negative groups
passed, including full two-dataset execution, all 10 contrasts and 11 bins,
full-GT versus subgroup top4, transient-return movement, target-slot versus
unique-node counts, bounded physical prefix reads, damaged hashes/headers,
GT and result validity, Recall and counter integrity, route identity, embedded
models, NOPASS gating, and a filesystem/NumPy fixture-only read guard.

Production source SHA at initial review freeze:
`798e9e3b4b61bc4380879b71aedaec1fae28cf1db38df3595ba2b210b498a5b5`.
Later source revisions, if required by review, need their own validation and
review record; this document must not silently label them reviewed.

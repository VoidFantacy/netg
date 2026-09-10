# Objective local-scale audit: independent source review

**PASS_SOURCE_AND_SYNTHETIC_REVIEW**, with no blocking findings. Reviewed frozen source SHA256 `148e3ff29259857865e9916f5f3905f2f2d1ffd3c1d843bfd8909a16c18259c8` against preregistration `abae80a4a2bbf6366e413b21a948a6fa4f27166e1160973cc223681e75cfff91`.

Independent generated fixtures passed **30 checks**. They cover unaligned bounded adjacency reads; duplicate/reciprocal arcs; self/padding accounting; invalid-ID and short-read rejection; integer equality and overflow; exact empirical quantiles; all 31 groups with independent Python denominators and summaries; empty cells; mocked two-dataset provenance preflight; and complete standalone histogram size/hash/omission. Author synthetic v3 evidence also reports PASS for 30 test groups.

The numerical contract matches the protocol: original directed valid nonself arcs retain multiplicity; in/out sums equal M and total degree sums to 2M. The strict condition is `D*(9*Q) < M` after an int64 overflow guard. Fit frequency and label movements bind to the completed target diagnosis. All fixed support, frequency and movement cells remain present; zero occurrence denominators are null.

The full native-file checksum may read embedded-vector bytes only as uninterpreted provenance. Numeric graph reads stay inside adjacency row blocks. The frozen P0 header parser seeks over payloads. Source review found no pilot-GT, query-vector, standalone-base, validation/heldout, ANN, refitting, or graph-write path.

The histogram cap now applies to the entire compact standalone JSON, including metadata and newline. Dataset/top reports store its checksum-bound descriptor rather than duplicating pairs. Earlier source/test snapshots are preserved.

This review read source, protocol and synthetic evidence only and ran generated fixtures; it did not read actual graph, GT, labels or count rows. Actual full-data completion and integrity checks remain the root-controlled execution obligation. Degree coverage is a sufficient-condition diagnostic, not evidence that a feasible improving move exists or a causal explanation of Recall changes. P3 remains NOPASS; P4 and further representation changes remain unauthorized.

# Frozen protocol and input preparation: independent review

Date: 2026-09-08. Scope: full read of `protocol.md` and `tools/prepare_inputs.py`, followed by read-only verification of `inputs/prepared_v2`. This review did not run ANN searches, fit a new model, open raw validation/held-out data, or modify preparation code. The source-path audit is separately recorded in `input_source_audit.md`.

**Verdict: PASS for the current prepared_v2 inputs.** No unresolved blocking defect was found in sampling, dtype conversion, source alignment, or the current provenance bindings. This verdict does not validate the diagnostic runner or establish why Fast loses search recall; those require the separately planned kernel checks and diagnostic results.

## Findings resolved before the formal inputs

The first preparation script used `np.array_equal` under a `byte_equal` label. Numeric equality does not establish byte equality, including for signed zero. The current script compares SHA256 of contiguous array bytes for raw hubs versus their base rows and for reconstructed versus saved prototypes. Both prepared_v2 prototype hashes match the original paired Fast artifacts exactly.

The first preparation script did not bind the protocol/source-path manifest or verify the imported builder's identity. The current script permits only this version's source-path file, verifies the protocol and source-path hashes in `preparation_freeze.json`, checks the current builder against the recorded source identity and the paired builder identity, and saves the binding in both sample manifests. The current paired-manifest hashes were also independently verified during this review. Existing prepared_v1 remains historical; prepared_v2 is the reviewed formal input version.

## Independent artifact verification

All checks below passed using a separate read-only Python verification, with BLAS/OpenMP set to one thread. No shared implementation helper was imported for the sampling or nearest-neighbor verification.

| Check | WebVid | Yandex |
|---|---:|---:|
| Total query rows | 767 | 768 |
| Historical pilot rows | 512 | 512 |
| Unique nearest fit rows | 127 | 128 |
| Random fit rows | 128 | 128 |
| Payload files with matching SHA/shape/dtype/size | 9 | 9 |
| Input identity records checked against expected SHA and current size/mtime | 7 | 7 |
| Full 512-row hash selection independently reproduced | PASS | PASS |
| All 128 nearest and random pairs independently reproduced | PASS | PASS |
| Query bytes equal the selected original train rows | PASS | PASS |
| Output int64 GT equals the original int32 GT values | PASS | PASS |
| Pair row/local-index mappings, cosine values and GT10 overlap | PASS | PASS |

Nearest neighbors were recomputed with normalized float64 training vectors and a separate matrix-vector product for each pilot query. All selected original row IDs matched the prepared manifests. The fit array is in increasing original row order, so `argmax` implements the specified lowest-original-row tie break. Random fit selection excludes the entire set of chosen nearest rows, and the auxiliary suffix is the sorted union. All emitted row IDs are unique, with pilot rows in `[0,10000)` and auxiliary rows in `[10000,30000)`.

The little-endian vecs reader treats each row header as int32, removes the header, and views the payload as float32 or int32 as appropriate. It does not numerically cast floating-point bit patterns through integers. GT is converted to int64 only when the selected payload is emitted, preserving IDs.

Base/graph full-file SHA256 was computed by the preparation owner. This reviewer checked those records against the frozen expected hashes and verified that current file sizes/mtimes still match; it did not duplicate the large sequential reads. All nine emitted payloads per dataset were rehashed directly by this reviewer.

## Identities checked

- Protocol SHA256: `a48fc656a98b40b344492d017bfc1a33af7eb644bc758a4a7582de4d2df9a6f1`.
- Source paths SHA256: `dc655dd791d825fe795d01f4c8163b47a4306f90da25203388856520a159ea43`.
- Current preparation script SHA256: `48b71a35afa13bc0366a1fb8e27926c4965c6c0bd14d94366341c68f78a02f59`.
- Existing builder SHA256: `391870a4be2ffe32aa3e3ac11faff26ac0dc8f7dec03b22973ae430c5b1bfd24`.
- WebVid original and reconstructed prototype SHA256: `1d6481e5d8abdeb23634b3565bce840873a9a12cff0553b26138ce77c53bf5ae`.
- Yandex original and reconstructed prototype SHA256: `39c539d28c8a40c879a37dfeccc72a2a99b99ef26e4d38b35ed5e349e83c28f8`.

## Protocol interpretation and remaining verification boundaries

The protocol keeps current Fast's raw query routing and raw-IP graph search separate from normalized geometric diagnostics. It explicitly scopes the single-entry optimum to the existing H hubs and each fixed L, keeps all recall ties, and does not interpret an arbitrary tie-break label as uniquely correct. The C8 pair/triple experiment is an offline oracle analysis and does not train a reranker or impose the earlier proposed anchor.

The 32 primary paired comparisons and their sampling units are specified before the searches. The protocol also distinguishes nearest-query transfer from target-side oracle choice, handles the possibly negative basin-decomposition term, and limits claims to a previously used training-side pilot. These are appropriate safeguards against equating geometric correlation, oracle headroom, or candidate-ID disagreement with an observed deployable improvement.

Prototype reconstruction invokes the same existing builder. Byte identity therefore verifies that this builder and the current frozen inputs reproduce the saved artifact; it does not independently prove that the GT1-cosine basin is the correct label for finite-beam Recall@10. Kernel count/plain parity, repeated-result parity, actual entry consumption, raw-IP scoring and runner binary provenance remain obligations of the separate runner review and runtime acceptance.

One nonblocking metadata caveat: `prototype_reconstruction.json` inherits `details.requires_aco_dpc=true` from the old builder's hardcoded return dictionary (`benches/run/build_fast_entry_variants.py:174`). This call uses already existing raw QGT hubs and only reconstructs their spherical query prototypes; it does not run ACO or DPC. The paired 20K manifests correctly record `requires_aco_dpc=false`. Interpret this legacy detail field using the actual call path, not as evidence that this preparation reran DPC.

The preparation freeze currently binds protocol and source paths, while each output records the preparation-script SHA. This review confirms those identities for this completed run. Any later script or protocol change needs a new version/binding and re-review rather than reusing this PASS statement.

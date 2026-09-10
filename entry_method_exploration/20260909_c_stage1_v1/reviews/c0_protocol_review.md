# C0 independent protocol and statistical review

Date: 2026-09-09. Reviewer: independent `review_protocol` agent. This review is read-only with respect to source, inputs and root documents; only this review file was created. It evaluates the current user authorization, not the superseded R0 authorization status.

## Decision

**DESIGN_ACCEPTABLE_WITH_LOCK_PROVENANCE_PENDING.** The proposed checkpoint and B formulas use only GT-free original-kernel cost distributions. No scientific protocol change, broader action set or additional authorization is needed. The current protocol covers the requested C0–C2 scope and correctly stops before C3. C0 should be marked complete only after calibration identity/layout checks and the actual build/input/source identities below are attached to the lock evidence. This is not C1 parity acceptance or C2 quality evidence.

## Protocol checks

| Requirement | Finding |
|---|---|
| Paired Fast3, frozen WebVid and official Yandex-IP | Direct HNSW top3 uses the paired 20K prototypes, existing hubs, fixed M16/efConstruction200/efSearch10/seed20260828 and insertion order. Top7 cannot silently replace the starting entries. |
| Bounded split | Per dataset, PCG64 seed20260909 selects 2000 distinct rows from training rows `[0,10000)`. The 128 calibration, 16 real parity and four smoke rows are contained in that same list. Prototype fitting uses disjoint `[10000,30000)`. This remains historical training-development evidence. |
| One GT-free checkpoint per L | `max(1,floor(0.5 * min_dataset median(native expansions)))` matches the implementation. Checkpoints occur after complete rows. It is one selected rule per L, not multiple tested quality checkpoints. |
| One preregistered B | `max(128,64*ceil(max_dataset_L P75(native graph NDC)/128))` matches the implementation; this rounds half of the maximum P75 cost upward to a multiple of 64. It does not claim equal actual suffix NDC. |
| Candidate generation | Independent top7, fixed ranks 3:7, remove initial/duplicate IDs without refill. Router work is paid separately; candidate true base distances must additionally be charged to B. There is no full-H true action scan. |
| Actions | Continue plus up to four force actions; four same-candidate natural controls permit a matched mechanism contrast. Invalid/visited candidates map to continue. |
| State and partial row | Required state and scheduler fields are specified; visited and expanded are distinct. At exhaustion, stop before a new unvisited distance call, preserve row offset/update state, and retain current retset topK. Implementation verification is delegated to C1. |
| Denominators | Early finish, no eligible candidate, no-op and zero gain stay in all 2000 query means. Eligible, executed, trajectory change and Recall improvement are explicitly distinct coverage fields. |
| GT boundary | C0 prepare/calibrate and shared Dataset do not open GT. GT metadata is present in input JSON but scoring access is deferred to a separate process after every branch has been persisted. The eventual scorer must enforce this completion gate. |
| Oracle and mechanism | Main oracle maximizes Recall over continue and eligible force actions, with continue-first ties. Natural controls are excluded from that oracle. Same-slot force-natural contrasts are descriptive; the selected force winner contrast is correctly marked as selection-biased. |
| Statistical family | Four dataset-by-L unconditional paired oracle-minus-continue means; 20,000 query bootstrap replicates, fixed PCG64 seed; Bonferroni familywise 95% corresponds to marginal 98.75% intervals with quantiles 0.00625/0.99375. Branches and L values are not independent sample inflation. |
| C2 gate | All four means must be at least 0.005 Recall (=0.5 pp), all corrected lower bounds positive and intervention coverage nonzero within the recorded actual NDC envelope. PASS establishes common-cap headroom only and requires stopping to report before C3. |
| Cost/wall | NDC distribution, per-query envelope, natural finish, cap exhaustion and diagnostic timing are distinct. Relative NDC uses an explicitly named ratio of means. No diagnostic wall is presented as QPS. |
| Stop and A+B boundary | No quality-driven B/candidate/checkpoint changes, larger model, expansion, validation/held-out or A+B rescue. Future A+B composition requires policy-specific relabeling and a registered interaction before any synergy claim. |

## Required lock-evidence completion

1. `prepare.lock()` currently accepts any nonempty compatible-looking calibration arrays. Before writing `C0: PASS`, verify each expected dataset occurs once, each has exactly `128 × 2` rows, `(sample_index,L)` is unique and complete, row IDs match the sampled input list, and NDC/expansion values are finite, positive integers. Verify both calibrations report no GT access. Save the distributions and derived medians/P75 values so the numerical lock can be recomputed independently.
2. Attach hashes of the actual calibration executable and its build command/compiler/linked libraries, `prepare.py`, `common.hpp`, `calibrate.cpp`, `build.sh`, and the dataset config/identities/sample files to the lock manifest or an immutable linked build/source manifest. The existing `source_manifest.json` protects pre-existing repository files but does not yet identify the newly executed C0 implementation. C1 may evolve independently after that snapshot; it must not retroactively replace C0 provenance.
3. Ensure the build identity distinguishes directly compiled current `ACSG.cpp` from archived library objects. Archive hashes plus compiler/flags and the directly compiled file SHA make the actual calibration binary reviewable even if an archive predates the current checkout. Do not claim all source files were rebuilt unless they were.

These are evidence and input-validation requirements, not changes to the research choices or effect thresholds.

## Execution checks required before C2

- `run_logged.py` currently caps each launched command at two hours and reads only its direct child's RSS. The protocol caps each stage, plus all native/branch calls at 200000 and new artifacts at 5 GiB. Maintain a cumulative stage/call ledger, preflight the exact plain/count/trace repetition count, and monitor aggregate RSS and output size. The 72000 maximum primary C2 count branches become 144000 if each is also repeated for plain timing; other calls must fit in the same 200000 limit.
- Lock identity should be rechecked by quality generation and scoring, including raw-result completion before GT access. Do not rely only on a Boolean assertion recording `GT_opened_before_lock=False`.
- Real C1 must prove direct-top3 baseline parity and count/plain/trace routing parity. `Router::run` currently always instruments routing distance; its recorded wall is therefore counted diagnostic wall until an independent plain path is compared.
- Bootstrap is conditional evidence for this frozen historical training sample and build. It does not supply build variability, fresh held-out generalization or a learned policy estimate. The max-over-observed-actions oracle is an explicit privileged headroom estimand.

## Historical evidence cross-check

Read AGENTS, current main documents, C R0 assessment/state, history 05/06, and linked aggregate original reports/designs; no validation/held-out vector or GT was opened. E14 final WebVid JSON confirms frontier+topology at the 20% policy gives Recall −3.371/−1.416 pp and NDC +2.668/+1.036% at L64/128. Its final Yandex extension is not evidence of a tested chooser. E15's corrected result is trace incremental information PASS with cost alignment FAIL, not absence of trace information. E16's particular query-only Atlas has all four utility intervals crossing zero; its old design states a ratio-of-means cost gate while decision/history report a mean of per-query relative costs. C avoids repeating that ambiguity by explicitly naming its relative-cost aggregation.

## Reviewed initial source identities

```text
protocol.md       5c63d644bb7fd7b002bc762136ea588f4b4d972c5ff080b250bf0f411f59fb07
src/prepare.py    ed1b954876c8b6067206f4598b619e36fcc184476a5225d4431c38e9355a307d
src/common.hpp    965ab8e10ca2b0e7d96da6a658e89232ce23e2a5d75909e35d0e2e446a7a4053
src/calibrate.cpp e7a702886f84a5c58643e8f8729d956f18ab3db91e488ae0327acfcf410242a2
src/build.sh      e71228eee9b5ec138579bdb72cabc1f5ea405b8f4ff3e4c21cc7bee585b5db91
src/run_logged.py 7036f752a5bdcd82d7378979a7deaad68967ebb0966ab2431867ccbbf14d86d4
```

## Addendum: actual C0 lock independently verified

The initial lock-evidence findings have been addressed. The accepted status is now **C0_PROTOCOL_LOCK_REVIEW_PASS**. The initial review above remains as the record of requested checks; it is superseded by this addendum where it describes missing lock bindings or unchecked calibration layout. C1/C2 remain separate gates.

Using the project's `.venv_cpu/bin/python`, independently read both calibration JSONs, both sampled row-ID files, `config.locked.json`, `protocol_lock.json` and the revised `prepare.py`; no GT was opened. Verified all 17 directly bound protocol/config/source/binary/input hashes, both calibration hashes, exactly 256 correctly ordered rows per dataset, both 2000-element unique sampled lists against an independently regenerated PCG64 seed20260909 permutation, sample-index/row-ID/L alignment, and positive integer NDC/expansion counts.

| Dataset | L | Calibration queries | Median completed expansions | P75 full native graph NDC |
|---|---:|---:|---:|---:|
| WebVid | 64 | 128 | 67 | 1074.25 |
| WebVid | 128 | 128 | 131 | 1944.25 |
| Official Yandex-IP | 64 | 128 | 68 | 2106.75 |
| Official Yandex-IP | 128 | 128 | 131 | 3686.75 |

Independent recomputation produces checkpoint 33 completed rows for L64, 65 for L128, and the single global cap **B=1856**, exactly matching the locked configuration. Lock UTC is `2026-09-09T07:06:08.583938+00:00`. `config.locked.json` SHA256 is `df6bf0fb42871265a6a19263ea991df5ab388711b2dfec460667ff19caa84db9`. Revised `prepare.py` SHA256 is `ccb1bf9ff49622b46907c65c5e7cabaaefa0daacb7159fbdfaea6fb8a644db29`; the cost formula, candidate policy and statistical protocol have not changed.

The actual calibration binary is locked at SHA256 `af29da349f17fc6b36f5f6b062a4ffac801deca8437180a646bb912ba9bb908c`. The unchanged `build.sh` compiles the current native `ACSG.cpp` directly and links the existing archives; `bin/parity_v2.build.json` separately records the same compiler/flags and archive SHA identities. A C0-specific auxiliary build identity remains useful for final packaging, but the original C0 source, executable, configuration and calibration outputs are already bound and reproducible as artifacts. This addendum does not claim archived dependencies were rebuilt from current source.

The first verification attempt with system `python3` failed before reading artifacts because NumPy was unavailable; rerunning with the existing CPU environment completed all checks. No method searches or extra samples were run by this reviewer. The cumulative-resource and separate-scoring completion checks listed above still apply before C2.

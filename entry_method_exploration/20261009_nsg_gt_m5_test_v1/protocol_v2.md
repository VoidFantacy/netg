# E173 final public-test measurement, v2

The original protocol.md, v1 code, preliminary timings and interrupted job
remain unchanged. No Recall feedback was read before this cost-only revision.
The first v1 K/L group took 133.76 seconds because, beyond three timed
queries per method, the harness ran repeated full 10K warm-up/count/plain
and another original-GT packet. The predicted grid cost approached 3 hours.
v1 was stopped by the root agent; this is not an algorithm failure.

The final comparison preserves every scientific setting from protocol.md:
both datasets' fixed public-test 10K, real K=1 and K=100, all five requested
L values, all three methods at identical L, the original scalar kernel,
unchanged GT10 router, frozen original M5 table, and three complete timing
rounds with the same method rotation. No training or feedback tuning occurs.

Only redundant work outside formal measurement is reduced:

- One fixed 256-query prefix warm-up per method and K/L point. All three
  full 10K timing rounds are still measured; publish every round and range.
- Independently run and save full plain 10K outputs for all three methods
  at every point. Compute Recall from those full outputs and full test GT.
- Plain/count output bit equality and independent NDC instrumentation use
  256 fixed, evenly distributed query IDs, selected solely by n and index.
  Count arrays/stats describe those 256 queries, not all 10K.
- M5's independent linear merge oracle still checks all 10K outputs, using
  the already computed GT plain packet at the same K/L as its reference.

Formal timing covers the same complete normal batch lifetime and all
online work as v1. Untimed artifacts are checked separately. The final
results come only from a complete fresh v2 grid, not mixed with v1 partial
timings. Prior preparation and interrupted-v1 costs are disclosed separately.

# Label timing scope

The inherited E118 experiment.cpp labels() computes all GT10 routes before its
timed loops. seconds.f64 measures only e.search(...) for the selected entries,
including its wrapper, separately for true K1/K100. It does NOT contain GT10
router cost, the new scorer, or a complete deployment loop. The protocol's
baseline reference T is this measured search-only mean. All cached utility and
time deltas must carry that scope. Full-wall evaluation is conditional and
must pay the entire new policy including default fallback. No cached quantity
will be labelled QPS or a complete end-to-end saving.

# Aggregate input count correction

The initial analyzer incorrectly asserted 32 E103 budgets per K. The source
CSV contains 16 per K, hence 32 across K1/K100. It stopped at the assertion
before writing any accounting result. It had created only an empty results/
directory, input hashes and unchanged root snapshots. Zero search/training ran.

src/analyze_initial.py preserves the original source. The corrected analyzer
requires 16 rows per K, verifies the existing snapshots/input hashes, and writes
to a new results_v2/ directory. No Recall, timing, policy or source CSV changes.

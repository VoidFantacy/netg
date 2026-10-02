# E46 analysis serialization correction

All 737280 row/score checks and 20 gradient checks completed in analyze_verify_v2.py, but gate JSON serialization rejected a NumPy boolean derived from the timing projection. That source/log and its preliminary CSV files in results remain. analyze_verify_v3.py converts projection/decision to native float/bool and writes canonical derived outputs under results_v2. The subsequent plot call had no cost file and wrote no plot; it is run only after successful analysis. No query, native output, model, gate threshold or reservation changes.

# P3 pipeline review v2: R1 fixed

R1 is fixed in both the full P3 evaluation runner and the real-model acceptance runner. They verify the Fast audit binding, hash the actual hubs and IDs against the paired manifest, save all three frozen file bindings, and recheck them before and after each subprocess. Commands use those verified resolved paths. Acceptance also checks that these paths match the accepted P2 prefix inputs.

Old sources are retained under `root_source_versions/fast_binding_r1_before_v1/`. The protocol, model family/order and measurement schedules are unchanged. Acceptance has an optional `--fast-manifest` argument whose default is the existing paired20K manifest.

Both CLIs pass `--help`. Sixteen synthetic file-binding checks passed across both runners, including wrong audit, incorrect raw hashes and post-freeze manifest/raw changes. No real data or ANN was used. Evidence: `fast_binding_r1_checks_v1/report.json`.

The finalizer source remains unchanged from the v1 review. No required source fixes remain in this bounded review; real-model and P3 performance gates are still separate.

Current source hashes:

- evaluation runner: `03eccddc76efa3c2e19a2f747f4e93213ebab57a4ce643984c5d392189729d08`
- acceptance runner: `23bf699c17dd953e62fc4cb401357b2bbb22b4263a36f9c96f299c5203f9f3c3`
- finalizer: `d1945203dc99e7027ebdc9a414a6b1303df5da0988b491dcc15ac1b30f537a7e`

Exact bindings and scope are in `pipeline_independent_review_v2.json`.

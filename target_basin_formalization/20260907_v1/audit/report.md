# Target-Basin E0 audit

Status: **PASS**. Held-out accessed: **false**.

## Checks

- PASS: `webvid.route_is_gt_free_and_anchor_preserved`
- PASS: `webvid.python_cpp_merge_parity`
- PASS: `webvid.fixed_query_route_repeatability`
- PASS: `webvid.count_switch_preserves_routes`
- PASS: `webvid.new_legacy_search_parity`
- PASS: `webvid.count_switch_preserves_search`
- PASS: `yandex.route_is_gt_free_and_anchor_preserved`
- PASS: `yandex.python_cpp_merge_parity`
- PASS: `yandex.fixed_query_route_repeatability`
- PASS: `yandex.count_switch_preserves_routes`
- PASS: `yandex.new_legacy_search_parity`
- PASS: `yandex.count_switch_preserves_search`
- PASS: `synthetic_cpp_merge_tests`
- PASS: `synthetic_python_merge_tests`
- PASS: `reject_K_greater_than_L`
- PASS: `reject_implicit_heldout_access`

## Routing NDC

- webvid: mean `1758.648`, range `1707..1838`, exact component `1638` per query.
- yandex: mean `1764.789`, range `1724..1842`, exact component `1650` per query.

The C++ and Python merge paths match exactly on both 128-query train slices. The new and legacy graph-search paths also match result IDs, Recall, and graph NDC for L=64/128 and K=10. Count/timing modes preserve routes and result IDs.

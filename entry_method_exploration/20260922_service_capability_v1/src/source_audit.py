"""Metadata and source-row audit only. Does not materialize fresh queries/GT."""
from common import *
import subprocess

if __name__ == '__main__':
    start = time.monotonic()
    files = [ROOT/'benches/datasets/WebVid2.5M_light_v1/manifest.json',
             ROOT/'benches/datasets/WebVid2.5M_light_v1/split_source_indices.seed20260826.json',
             ROOT/'benches/datasets/YandexT2I_official10M_ip_v1/manifest.json',
             ROOT/'entry_method_exploration/20260920_wfree_frozen_replication_v1/config.locked.json']
    search = subprocess.run(['rg', '-n', 'query.learn.50M|webvid.query.train.2.5M|"source_selection"',
        'entry_method_exploration', 'benches/run', '-g', '*.json', '-g', '*.py',
        '-g', '!**/source_before*/**', '-g', '!**/source_after*/**', '-g', '!**/vendor/**',
        '-g', '!**/20260922_service_capability_v1/**'], cwd=ROOT, capture_output=True, text=True)
    assert search.returncode in [0, 1]
    (RUN/'reviews/source_reference_scan.txt').write_text(search.stdout)
    selected_rows = read(files[1])
    registered = selected_rows['selected_source_rows']
    assert set(registered) == {'aco_train', 'router_train', 'validation'}
    web_rows = set(sum(registered.values(), []))
    assert len(web_rows) == 45000
    possible_web = set(range(1200000, 1220000)) - web_rows
    e105 = read(files[3])
    assert e105['source_selection']['webvid']['start'] == 2450000
    assert e105['source_selection']['yandex']['start'] == 2000000
    result = dict(status='METADATA_SOURCE_CANDIDATES_AVAILABLE_NOT_BLIND_CERTIFIED',
        files=[identity(p) for p in files], query_payload_opened=False, new_GT=False,
        webvid=dict(source='webvid.query.train.2.5M.fbin', registered_excluded_source_rows=45000,
            proposed_candidate_window=[1200000,1220000], remaining_after_registered_row_exclusion=len(possible_web),
            additionally_excluded_E105_materialized_window=[2450000,2470000]),
        yandex=dict(source='query.learn.50M.fbin', registered_excluded_range=[0,45000],
            additionally_excluded_E105_materialized_window=[2000000,2020000], proposed_candidate_window=[3000000,3020000]),
        remaining_checks=['review all matched historical references', 'freeze policy and power-based sample size',
            'verify source identity and remote range headers if applicable',
            'byte-deduplicate candidate queries against every registered split and historical extra query source',
            'record first-payload-access time; do not call source-order samples semantic independence'],
        seconds=time.monotonic()-start)
    dump(RUN/'reviews/source_audit.json', result)
    print(result['status'], result['webvid']['remaining_after_registered_row_exclusion'])

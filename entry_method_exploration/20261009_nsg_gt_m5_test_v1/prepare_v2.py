from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent
old = json.loads((ROOT / 'preparation_combined.json').read_text())
receipt = dict(status='FROZEN_V2_JOBS_NOT_EXECUTED', scientific_settings_unchanged=True,
               no_quality_feedback_read=True, full_configurations=60,
               full_timed_batches=180, full_timed_query_count=1800000,
               full_plain_query_count=600000, warmup_n=256, count_audit_n=256,
               complete_M5_linear_merge_per_point_n=10000, jobs=[])
for item in old['jobs']:
    job = json.loads(Path(item['path']).read_text())
    job['out'] = str(ROOT / 'results_v2' / job['dataset'])
    job['warmup_n'] = 256
    job['audit_n'] = 256
    job['freeze_timestamp'] = datetime.now(timezone(timedelta(hours=8))).isoformat()
    job['protocol_revision'] = 'v2_cost_only_no_quality_feedback'
    job['full_query_test_count_unchanged'] = True
    path = ROOT / f'jobs/{job["dataset"]}.v2.json'
    if path.exists():
        raise RuntimeError(f'Preserve frozen job {path}')
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + '\n')
    receipt['jobs'].append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(ROOT / 'preparation_v2.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
driver = (ROOT / 'run_tests.py').read_text()
driver = driver.replace('preparation_combined.json', 'preparation_v2.json')
driver = driver.replace('src/build.json', 'src/build_v2.json')
driver = driver.replace("OUT / 'bin/benchmark'", "OUT / 'bin/benchmark_v2'")
driver = driver.replace('source_review.json', 'source_review_v2.json')
driver = driver.replace('run_state.json', 'run_state_v2.json')
driver = driver.replace('.native.log', '.v2.native.log')
target = ROOT / 'run_tests_v2.py'
if target.exists():
    raise RuntimeError(f'Preserve driver {target}')
target.write_text(driver)
print(json.dumps(receipt, ensure_ascii=False))

from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone, timedelta

OUT = Path(__file__).resolve().parent
DATA = Path('/data/netg/ACSG/benches/datasets')
BASE = {
    'webvid2_5m_light_v1': DATA / 'WebVid2.5M_light_v1/base.webvid2_5m.fvecs',
    'yandex_t2i_official10M_ip_v1': DATA / 'YandexT2I_official10M_ip_v1/base.official_first10M.fvecs',
}
receipt = json.loads((OUT / 'preparation.json').read_text())
receipt['status'] = 'FROZEN_COMBINED_DATASET_JOBS_NOT_EXECUTED'
receipt['single_dataset_load'] = True
receipt['prepared_single_K_jobs_retained'] = receipt.pop('jobs')
receipt['jobs'] = []
for dataset, base in BASE.items():
    job = json.loads((OUT / f'jobs/{dataset}.k1.json').read_text())
    job.pop('K')
    job['K_values'] = [1, 100]
    job['base'] = str(base)
    job['verify_loaded_base_words'] = True
    job['out'] = str(OUT / f'results/{dataset}')
    job['warmup_n'] = job['n']
    job['min_free_bytes'] = 1073741824
    job['maxrss_bytes'] = 68719476736
    job['methods'] = ['NSG', 'GT', 'M5']
    job['freeze_timestamp'] = datetime.now(timezone(timedelta(hours=8))).isoformat()
    path = OUT / f'jobs/{dataset}.combined.json'
    if path.exists():
        raise RuntimeError(f'Refusing to overwrite frozen job: {path}')
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + '\n')
    receipt['jobs'].append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(OUT / 'preparation_combined.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(receipt, ensure_ascii=False))

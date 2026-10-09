from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone, timedelta

OUT = Path(__file__).resolve().parent
REPO = Path('/data/netg/ACSG')
OLD = Path('/root/acsg-e172-storage-v2/campaign')
LS = [200, 400, 800, 1000, 1200]
DATASETS = {
    'webvid2_5m_light_v1': ('WebVid2.5M_light_v1', 'query.test.public10K.fvecs', 'gt.test.public10K.ip.top100.ivecs'),
    'yandex_t2i_official10M_ip_v1': ('YandexT2I_official10M_ip_v1', 'query.test.public100K.fvecs', 'gt.test.public100K.ip.ivecs'),
}
stamp = datetime.now(timezone(timedelta(hours=8))).isoformat()
(OUT / 'jobs').mkdir(parents=True, exist_ok=True)
jobs = []
for dataset, (directory, query, gt) in DATASETS.items():
    data = REPO / 'benches/datasets' / directory
    manifest = json.loads((data / 'manifest.json').read_text())
    for K in (1, 100):
        old_job_path = OLD / f'inputs/m5_v6/{dataset}.cal.k{K}.json'
        source = json.loads(old_job_path.read_text())
        table = OLD / f'm5/models/{dataset}/residual_joint.bin'
        job = dict(dataset=dataset, role='public_test', n=10000, query_first=0,
                   dimension=source['dimension'], base_n=source['base_n'],
                   queries=str(data / query), query_format='fvecs',
                   GT=str(data / gt), GT_format='ivecs',
                   query_sha256=manifest['files'][query]['sha256'],
                   GT_sha256=manifest['files'][gt]['sha256'],
                   index=source['index'], anchor=source['anchor'],
                   table=str(table), table_sha256=hashlib.sha256(table.read_bytes()).hexdigest(),
                   K=K, L=LS, out=str(OUT / f'results/{dataset}/k{K}'),
                   warmup_batches=1, timing_repeats=3, cpu=15, threads=1,
                   freeze_timestamp=stamp, no_training=True,
                   methods=['NSG', 'GT10', 'M5'],
                   old_job_source=str(old_job_path),
                   old_job_source_sha256=hashlib.sha256(old_job_path.read_bytes()).hexdigest())
        path = OUT / f'jobs/{dataset}.k{K}.json'
        if path.exists():
            raise RuntimeError(f'Refusing to overwrite a frozen job: {path}')
        path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + '\n')
        jobs.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
receipt = dict(status='PREPARED_NOT_EXECUTED', frozen_at=stamp, datasets=list(DATASETS),
               query_count_each=10000, K=[1, 100], L=LS,
               methods=['NSG', 'GT10', 'M5'], configurations=60, timed_batches=180,
               warmup_batches=60, new_training=False, jobs=jobs)
(OUT / 'preparation.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(receipt, ensure_ascii=False))

import hashlib,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parent;CAMP=R.parents[1]
def main():
    started=time.perf_counter();assert not (R/'results.json').exists() and not (R/'all_comparisons.npz').exists()
    assert json.loads((R.parent/'single_hub_certificate_opportunity_v1/seal.json').read_text())['status']=='AUDITED_COMPLETE_FIXED_VERSION_STOPPED'
    assert time.time()<1790775000
    size=sum(p.stat().st_size for p in CAMP.rglob('*') if p.is_file());free=shutil.disk_usage(CAMP).free
    assert size+384*1024<1024**3 and free>6*1024**3
    sources=['cases.py','run.py','audit.py','prepare.py','theory.md','pipeline_conditions.md','protocol.md']
    c={'deadline_unix':1790776800,'latest_start_unix':1790775000,'max_stage_bytes':384*1024,'main_seconds_cap':60,'audit_seconds_cap':60,
       'source_sha256':{str(R/name):hashlib.sha256((R/name).read_bytes()).hexdigest() for name in sources},'campaign_bytes_before':size,'free_bytes_before':free,
       'preparation_seconds':time.perf_counter()-started,'unix':time.time(),'real_data_inputs':[]}
    with (R/'config.locked.json').open('x') as f:json.dump(c,f,indent=2);f.write('\n')
    print('SYNTHETIC CONFIG FROZEN',c['preparation_seconds'])
if __name__=='__main__':main()

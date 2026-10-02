import os
os.sched_setaffinity(0,{14})
import ast,hashlib,json,shutil,time
from pathlib import Path

R=Path(__file__).resolve().parent;CAMP=R.parents[1]
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def main():
    start=time.perf_counter();previous=R.parent/'shared_batch_full_build_v1';math=R.parent/'hard_mass_certificate_v1'
    assert json.loads((previous/'reviews/seal.json').read_text())['status']=='AUDITED_COMPLETE_WITH_IDENTITY_EXCEPTION'
    assert json.loads((math/'independent_audit.json').read_text())['status']=='PASS'
    assert json.loads((math/'exit_status.json').read_text())=={'main_exit':0,'audit_exit':0}
    pc=json.loads((previous/'config.locked.json').read_text());refs=json.loads((previous/'reviews/validation_references.json').read_text())
    prep=json.loads((previous/'reviews/preparation.json').read_text());datasets={};small={};large={}
    for name,v in pc['cases'].items():
        if v['method']!='Default':continue
        ref=refs[name];old=Path(ref['full_default']);ds=v['dataset']
        datasets[ds]={'base':v['base'],'base_n':v['base_n'],'dimension':v['dimension'],'fit_queries':v['fit_queries'],
            'hub_ids':str(old/'ids.i32'),'exact_ids':str(old/'fit20000.ids.i64'),'approx_ids':ref['teacher_ids'],
            'actual_default_is_hard':not v['soft']}
        for k in ('fit_queries','hub_ids','exact_ids','approx_ids'):
            p=datasets[ds][k];small[p]=ident(p)
        p=v['base'];large[p]=prep['large'][p];st=Path(p).stat()
        assert st.st_size==large[p]['bytes'] and st.st_mtime_ns==large[p]['mtime_ns'] and large[p]['sha256']
    for p in [R/'protocol.md',R/'run.py',R/'audit.py',R/'prepare.py',math/'cone_bound.md']:
        if p.suffix=='.py':ast.parse(p.read_text())
        small[str(p.resolve())]=ident(p)
    used=sum(p.stat().st_size for p in CAMP.rglob('*') if p.is_file());free=shutil.disk_usage(CAMP).free
    assert used+2*1024**2<1024**3 and free>=6*1024**3
    config={'unix':time.time(),'deadline_unix':1790776800,'latest_start_unix':1790775000,'datasets':datasets,
        'small_identity':small,'large_identity':large,'max_new_bytes':2*1024**2,'main_seconds_cap':300,'audit_seconds_cap':300,
        'preparation_seconds':time.perf_counter()-start,'campaign_bytes_before':used,'free_bytes_before':free,
        'base_identity_scope':'Earlier full SHA and verified unchanged size/mtime; no new checksum pass in this diagnostic'}
    with (R/'config.locked.json').open('x') as f:json.dump(config,f,indent=2);f.write('\n')
    print('OPPORTUNITY_PROTOCOL_FROZEN',config['preparation_seconds'],used,flush=True)

if __name__=='__main__':main()

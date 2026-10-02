"""Functional native four-method/recovery checks; never benchmark observations."""
from common import *
import subprocess

def main():
    out=RUN/'reviews/evaluation_smoke';out.mkdir(exist_ok=True);done=out/'complete.json'
    if done.exists():assert json.loads(done.read_text())['evaluate_sha256']==sha(RUN/'bin/evaluate');return
    inp=RUN/'reviews/topology_smoke_input';base=vecs(inp/'base.fvecs');env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    def call(args,log):
        with (out/log).open('w') as f:subprocess.run(['taskset','-c','15']+list(map(str,args)),env=env,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
    if not (out/'synthetic_native.nsg').exists():call([RUN/'bin/make_smoke_nsg',inp/'base.fvecs',out/'synthetic_native.nsg'],'make.log')
    unit(base[:512]).tofile(out/'W.f32');np.arange(512,dtype='i4').tofile(out/'ids.i32');np.fromfile(inp/'cal.f32','f4').reshape(-1,32)[:32].tofile(out/'q.f32')
    cfg=dict(formal=False,threads=1,n=32,L=[32,128,1500],index=str(out/'synthetic_native.nsg'),queries=str(out/'q.f32'),base=str(inp/'base.fvecs'),hnsw_topology=str(RUN/'reviews/topology_smoke/full.topology.gz'),hnsw_complete=str(RUN/'reviews/topology_smoke/complete.json'),methods=[dict(name='NSG'),dict(name='GT10',W=str(out/'W.f32'),ids=str(out/'ids.i32')),dict(name='GATE',W=str(out/'W.f32'),ids=str(out/'ids.i32')),dict(name='HNSW')])
    dump(out/'config.json',cfg);result=out/'results';call([RUN/'bin/evaluate',out/'config.json',result],'first.log')
    original={str(p.relative_to(result)):sha(p) for p in result.glob('*_L*/*') if p.suffix in ['.i32','.f32','.u64']}
    # Simulate a crash after some, but not all, count results were committed at L1500.
    (result/'complete.json').rename(out/'first_complete.json');(result/'NSG_L1500/complete.json').rename(out/'incomplete_point_marker.json')
    call([RUN/'bin/evaluate',out/'config.json',result],'resume.log')
    for rel,digest in original.items():assert sha(result/rel)==digest,rel
    meta=json.loads((result/'complete.json').read_text());assert meta['points']==12 and meta['wall_rounds']==12 and not meta['formal']
    for method in ['NSG','GT10','GATE','HNSW']:assert len(list((result/'incomplete_attempts').glob(f'*/{method}_L1500')))==1
    dump(done,dict(status='PASS',synthetic_only=True,query_rows=32,methods=4,budgets=3,warmup_plain_count_bits_equal=True,completed_budgets_reused=True,partial_budget_four_methods_archived_and_repeated=True,all_ids_distances_routes_ndc_identical_after_resume=True,evaluate_sha256=sha(RUN/'bin/evaluate')))

if __name__=='__main__':main()

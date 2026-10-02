import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;P=R.parent.parent;ROOT=P.parents[1];E=P/'stages/e124_semantic_service_ridge_v1';BASE=ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1';C=json.loads((E/'config.locked.json').read_text());start=time.perf_counter();max_error=0.;affinity_error=0.;profiles=0;affinities=0
I=json.loads((R/'reviews/inputs.json').read_text());summary=json.loads((R/'results/summary.json').read_text())
def unit(x):return x/np.maximum(np.sqrt(np.einsum('ij,ij->i',x,x))[:,None],1e-12)
for p,v in I['files'].items():
    path=Path(p);assert path.stat().st_size==v['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==v['sha256']
for p,v in I['bases_stat_only'].items():st=Path(p).stat();assert st.st_size==v['bytes'] and st.st_mtime_ns==v['mtime_ns']
for ds,dc in C['datasets'].items():
    roles=np.load(R/'results'/f'{ds}.roles.npz');stored=np.load(R/'results'/f'{ds}.profiles.npz');sem=np.load(E/'inputs'/ds/'semantic.npz');owner=sem['owners'];H=len(stored['ids']);d=dc['dimension']
    qr=np.fromfile(dc['fit_source']['queries_file'],'<f4').reshape(20000,d)
    # Original input normalization is float32 np.linalg.norm; reuse that numeric contract only.
    q=(qr/np.maximum(np.linalg.norm(qr,axis=1,keepdims=True),1e-12)).astype('f8')
    hr=np.fromfile(BASE/'inputs'/ds/'raw_hubs.f32','<f4').reshape(H,d);hub=(hr/np.maximum(np.linalg.norm(hr,axis=1,keepdims=True),1e-12)).astype('f8')
    labels={'GT1Hard':np.eye(H)[owner[:,0]],'GT10Hard':np.stack([np.bincount(x[:10],minlength=H)/10 for x in owner])}
    if ds.startswith('web'):labels['GT10Soft']=np.load(R/'results'/f'{ds}.soft_labels.npz')['A']
    halves=[roles['A'],roles['B']];donors=[roles['shuffle_A'],roles['shuffle_B']]
    assert not set(halves[0])&set(halves[1]) and np.array_equal(np.sort(np.concatenate(halves)),np.arange(20000))
    for name,a in labels.items():
        for half,idx in enumerate(halves):
            out=halves[1-half]
            for tag,arows in [('actual',idx),('shuffled',donors[half])]:
                total=np.zeros((H,d))
                if name!='GT10Soft':
                    ranks=1 if name=='GT1Hard' else 10
                    for rank in range(ranks):np.add.at(total,owner[arows,rank],q[idx]/ranks)
                else:
                    for lo in range(0,len(idx),512):total+=a[arows[lo:lo+512]].T@q[idx[lo:lo+512]]
                rebuilt=unit(hub+total);ref=stored[name+'_'+tag][half];err=float(np.abs(rebuilt-ref).max());assert err<1e-11;max_error=max(max_error,err);profiles+=1
                # Forward query scores verify the trace-form mean using a different operation order.
                total_aff=0.
                for lo in range(0,len(out),512):
                    oi=out[lo:lo+512];scores=q[oi]@ref.T;total_aff+=float(np.sum(scores*a[oi]))
                value=total_aff/len(out);key='actual_profile_affinity' if tag=='actual' else 'shuffled_profile_affinity';expected=summary[ds]['families'][name]['cross_half_affinity'][half][key]
                err=abs(value-expected);assert err<1e-12;affinity_error=max(affinity_error,err);affinities+=1
        pa,pb=stored[name+'_actual'];cos=np.einsum('ij,ij->i',pa,pb);centerA=pa-pa.mean(0);centerB=pb-pb.mean(0)
        rho=1-np.linalg.norm(centerA-centerB)**2/(np.linalg.norm(centerA)**2+np.linalg.norm(centerB)**2)
        assert abs(rho-summary[ds]['families'][name]['actual_all_hubs']['centered_profile_replicability'])<1e-12
        assert abs(np.median(np.degrees(np.arccos(np.clip(cos,-1,1))))-summary[ds]['families'][name]['actual_all_hubs']['angle_degrees']['median'])<1e-10
    default='gt10_soft_t1' if ds.startswith('web') else 'gt10_hard'
    assert (BASE/'models'/ds/default/'W.f32').read_bytes()==Path(dc['anchor']['W']).read_bytes()
result={'status':'PASS','same_agent_independent_implementation':True,'seconds':time.perf_counter()-start,'profiles_reaggregated':profiles,'cross_half_query_forward_checks':affinities,'max_profile_error':max_error,'max_affinity_error':affinity_error,'all_direction_statistics_match':True,'current_default_W_matches_original_E24':True,'protected_files':len(I['files']),'large_base_identity_scope':'stat only, consumed target bytes hashed in preparation'}
target=R/'reviews/independent_audit.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

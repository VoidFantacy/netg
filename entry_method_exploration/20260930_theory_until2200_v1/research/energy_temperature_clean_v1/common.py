"""Numerical contracts copied from the audited builder; no default temperature input."""
import hashlib,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
ROOT=R.parents[3]
E125=ROOT/'entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_approximate_target_profiles_v1'
CONFIG=json.loads((E125/'config.locked.json').read_text())
METHODS=['Uniform','EnergyTree','ShuffledEnergyTree']
FEATURE_NAMES=['query_norm','mean_top10_distance_per_qnorm','gap10_11_per_qnorm','spread1_10_per_qnorm',
    'assignment_entropy','assignment_l2_squared','approx_tangent_leverage','weighted_inverse_resultant']
def ident(path):
    p=Path(path);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(path,obj):
    with Path(path).open('x') as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n')
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
def assignment(base,targets,h,temp):
    n=len(targets);a=np.zeros((n,len(h)))
    for rank in range(10):
        z=unit(np.array(base[targets[:,rank]],dtype='f4'))
        for lo in range(0,n,4096):
            hi=min(lo+4096,n);s=z[lo:hi]@h.T
            if temp is None:a[np.arange(lo,hi),s.argmax(1)]+=.1
            else:
                s=s.astype('f8');s-=s.max(1,keepdims=True);s/=temp;np.exp(s,out=s);s/=s.sum(1,keepdims=True);a[lo:hi]+=s/10
    np.testing.assert_allclose(a.sum(1),1.,rtol=1e-13,atol=1e-13);return a
def cheap_inputs(ds):
    c=CONFIG['datasets'][ds]['original'];d=c['dimension'];n=20000
    base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:]
    ids=np.fromfile(c['anchor']['ids'],'<i4');h=unit(np.array(base[ids],dtype='f4'))
    raw=np.fromfile(c['fit_source']['queries_file'],'<f4').reshape(n,d)
    q=unit(raw).astype('f8');qn=np.linalg.norm(raw.astype('f8'),axis=1)
    ap=np.fromfile(E125/'results'/ds/'labels/ids.i32','<i4').reshape(n,100)
    distances=np.fromfile(E125/'results'/ds/'labels/distances.f32','<f4').reshape(n,100).astype('f8')
    gaps=np.zeros(n)
    if ds.startswith('webvid'):
        z=unit(np.array(base[ap[:,0]],dtype='f4'))
        for lo in range(0,n,4096):
            s=z[lo:lo+4096]@h.T;top=np.partition(s,-2,axis=1)[:,-2:];gaps[lo:lo+4096]=top.max(1)-top.min(1)
        temp=max(float(np.median(gaps)),1e-4)
    else:temp=None
    b=assignment(base,ap,h,temp);vp=h.astype('f8')+b.T@q;norm=np.linalg.norm(vp,axis=1);pp=vp/norm[:,None]
    tq=np.maximum(np.sum(q*q,axis=1)[:,None]-(q@pp.T)**2,0)
    features=np.column_stack([qn,distances[:,:10].mean(1)/qn,(distances[:,10]-distances[:,9])/qn,
        (distances[:,9]-distances[:,0])/qn,-np.sum(b*np.log(np.maximum(b,1e-300)),axis=1),
        np.sum(b*b,axis=1),(b*b*tq)@(1/norm**2),b@(1/norm)])
    assert np.isfinite(features).all()
    return {'config':c,'base':base,'h':h,'q':q,'approx_ids':ap,'gaps':gaps,'temp':temp,'b':b,'vp':vp,'norm':norm,'pp':pp,'tq':tq,'features':features}
def energy_on_rows(x,gt,rows):
    a=assignment(x['base'],np.asarray(gt[rows]),x['h'],x['temp'])
    return ((a-x['b'][rows])**2*x['tq'][rows])@(1/x['norm']**2)
def mixed_resultant(x,gt,rows):
    a=x['b'].copy();a[rows]=assignment(x['base'],np.asarray(gt[rows]),x['h'],x['temp'])
    return x['h'].astype('f8')+a.T@x['q']
def tree_record(tree,scale):
    t=tree.tree_;return {'children_left':t.children_left.tolist(),'children_right':t.children_right.tolist(),
        'feature':t.feature.tolist(),'threshold':t.threshold.tolist(),'values':(t.value[:,0,0]*scale).tolist(),
        'samples':t.n_node_samples.tolist(),'scale':scale,'input_cast':'float32'}

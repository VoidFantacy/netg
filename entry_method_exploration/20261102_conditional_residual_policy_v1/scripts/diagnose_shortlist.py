"""Post-formal diagnostic only; no parameter selection or new performance timing."""
from model_io import *
from archive import load_packets
import struct
assert read(R/'reviews/formal_complete.json')['status']=='PASS_FROZEN_FOUR_WINDOW_MATRIX'
rows=[]
for ds in DS:
  for window in ['A','B']:
    raw=load_packets(R/'storage/results'/ds/window)
    for K,L in STATES:
        d=raw[f'k{K}/POLICY_L{L}/selection.bin.gz'];pos=0;features=[];ids=[];groups=[]
        for qi in range(512):
            q,nc=struct.unpack_from('<II',d,pos);pos+=56;assert q==qi;begin=len(ids)
            for j in range(nc):
                ids.append(struct.unpack_from('<i',d,pos)[0]);pos+=4
                features.append(np.frombuffer(d,'<f4',count=104,offset=pos).copy());pos+=416
            groups.append(np.arange(begin,len(ids)))
        assert pos==len(d);ids=np.asarray(ids);f=np.asarray(features)
        model=read(R/'storage/models'/ds/f'k{K}_L{L}'/'model.json');ni=np.fromfile(model['node_ids'],'<i4');ne=np.fromfile(model['node_embeddings'],'<f8').reshape(-1,32)
        model['_ids']=ids;sp=student_predict(model,f,ne,ni)
        td=np.frombuffer(raw[f'k{K}/TEACHER384_L{L}/decisions.i32'],'<i4').reshape(512,4)
        cd=np.frombuffer(raw[f'k{K}/CASCADE384_L{L}/decisions.i32'],'<i4').reshape(512,4)
        counts=[];retained=agreements=has=0
        for qi,ix in enumerate(groups):
            if not len(ix):continue
            order=ix[np.argsort(-sp[ix,1],kind='stable')];sl=list(dict.fromkeys([int(ix[0])]+[int(i) for i in order[:5]]));cand=set(ids[sl]);has+=1;counts.append(len(sl))
            kept=td[qi,0] in cand;retained+=kept;agreements+=cd[qi,0]==td[qi,0]
            if kept:assert cd[qi,0]==td[qi,0]
        rows.append(dict(dataset=ds,window=window,K=K,L=L,queries=512,nonempty_C=has,mean_C=len(ids)/512,mean_shortlist_384=float(np.mean(counts)),
            learned_full_teacher_seed_retained=retained,learned_full_teacher_seed_retention_pct=100*retained/has if has else 0,
            cascade_full_teacher_seed_agreements=agreements,GT_oracle=False))
    print('SHORTLIST_DIAGNOSED',ds,window,flush=True)
csvwrite(R/'analysis/shortlist.csv',rows)

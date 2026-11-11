#!/usr/bin/env python3
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']: os.environ[k]='1'
import json,time,hashlib,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
def main():
    ds=sys.argv[1]; t=time.perf_counter(); c=json.loads((R/f'configs/{ds}.json').read_text()); old=Path(c['backend']); out=R/'models'/ds; out.mkdir(exist_ok=False)
    N,d=c['base']['n'],c['base']['d']; ids=np.fromfile(old/'region_ids.i32','<i4'); codes=np.memmap(old/'codes.u8',dtype='u1',mode='r',shape=(N,16)); off=np.fromfile(old/'offsets.u64','<u8'); book=np.fromfile(old/'codebooks.f32','<f4').reshape(16,256,d//16)
    block_off=[0];region_off=[0];centres=[];sizes=[]
    with (out/'block_ids.i32').open('xb') as fi,(out/'block_codes.u8').open('xb') as fc:
        for r in range(1024):
            lo,hi=int(off[r]),int(off[r+1]); cr=np.asarray(codes[lo:hi]); v=np.concatenate([book[m,cr[:,m]] for m in range(16)],axis=1)
            def split(a):
                if len(a)<=128:
                    if not len(a):return
                    # Leaves retain original order for deterministic tie semantics.
                    a=np.sort(a); ids[lo+a].astype('<i4').tofile(fi); cr[a].tofile(fc)
                    centres.append(v[a].mean(axis=0,dtype=np.float64).astype('<f4')); sizes.append(len(a));block_off.append(block_off[-1]+len(a));return
                axis=int(np.argmax(v[a].var(axis=0,dtype=np.float64))); order=np.argsort(v[a,axis],kind='stable');a=a[order];mid=len(a)//2;split(a[:mid]);split(a[mid:])
            split(np.arange(hi-lo));region_off.append(len(centres))
            if r%128==0:print(json.dumps(dict(dataset=ds,regions=r,blocks=len(centres),seconds=time.perf_counter()-t)),flush=True)
    np.asarray(centres,'<f4').tofile(out/'block_centres.f32');np.asarray(block_off,'<u8').tofile(out/'block_offsets.u64');np.asarray(region_off,'<u8').tofile(out/'region_blocks.u64')
    got=np.fromfile(out/'block_ids.i32','<i4');assert np.array_equal(np.sort(got),np.arange(N));assert max(sizes)<=128 and sum(sizes)==N
    idreg=np.fromfile(old/'id_region.i32','<i4');
    for r in range(1024): assert np.all(idreg[got[block_off[region_off[r]]:block_off[region_off[r+1]]]]==r)
    # Check encoded words against the unchanged original layout.
    inverse=np.empty(N,'<i4');inverse[ids]=np.arange(N,dtype=np.int32);sample=np.random.default_rng(20261028).choice(N,min(N,4096),replace=False)
    nc=np.memmap(out/'block_codes.u8',dtype='u1',mode='r',shape=(N,16));assert np.array_equal(nc[sample],codes[inverse[got[sample]]])
    receipt=dict(status='PASS_BLOCK_PARTITION',dataset=ds,N=N,blocks=len(sizes),max_block_size=max(sizes),seconds=time.perf_counter()-t,threads=1,full_ID_permutation=True,full_region_membership=True,code_samples=4096,query_or_GT_read=False,bytes=sum(p.stat().st_size for p in out.iterdir() if p.is_file()))
    (out/'blocks.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()

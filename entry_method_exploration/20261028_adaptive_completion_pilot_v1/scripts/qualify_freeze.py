#!/usr/bin/env python3
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
import hashlib,json,sys,time
from pathlib import Path
import faiss,numpy as np
R=Path(__file__).resolve().parents[1];OLD=R.parent/'20261017_gt10_residual_comprehensive_v1'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def view(d):
    n=d['n'];dim=d['d'];total=d.get('total_n',n);start=d.get('row_start',0)
    if d['format']=='fvecs':return np.memmap(d['path'],'<f4','r',shape=(total,dim+1))[start:start+n,1:]
    return np.memmap(d['path'],'<f4','r',shape=(total,dim))[start:start+n]
def main():
    t=time.perf_counter();receipts=[];faiss.omp_set_num_threads(1)
    for ds in ['coco','deep10m_l2_v1']:
        c=json.loads((R/f'configs/{ds}.json').read_text());rt=c['router']['name'];p=Path(c['backend'])
        qc=json.loads((R/f'reviews/qualification_{ds}/complete.json').read_text());assert qc['status']=='PASS_E187_QUALIFICATION'
        for L in [100,200]:
            for method,oldmethod in [('GT10','GT10-hard' if rt=='hard' else 'GT10-soft-t1'),('B32',rt+'-JOINT32')]:
                a=R/f'reviews/qualification_{ds}/{method}_L{L}/raw';b=OLD/f'results/{ds}/k100/{oldmethod}_L{L}/raw'
                for name,width in [('ids.i32',100),('distances.f32',100),('entry_ids.i32',3),('profile_distances.f32',3)]:
                    raw=(a/name).read_bytes();assert raw==(b/name).open('rb').read(len(raw)),(ds,L,method,name)
        N,d=c['base']['n'],c['base']['d'];ids=np.fromfile(p/'region_ids.i32','<i4');regions=np.fromfile(p/'id_region.i32','<i4');offset=np.fromfile(p/'offsets.u64','<u8');codes=np.memmap(p/'codes.u8','u1','r',shape=(N,16))
        assert np.array_equal(np.sort(ids),np.arange(N))
        for r in range(1024):assert np.all(regions[ids[int(offset[r]):int(offset[r+1])]]==r)
        sample=np.random.default_rng(19287).choice(N,4096,replace=False);v=np.ascontiguousarray(view(c['base'])[sample]);cent=np.fromfile(p/'centroids.f32','<f4').reshape(1024,d)
        quant=faiss.IndexFlatL2(d) if c['metric_id']==1 else faiss.IndexFlatIP(d);quant.add(cent);_,assignment=quant.search(v,1)
        assert np.array_equal(assignment.ravel(),regions[sample])
        pq=faiss.ProductQuantizer(d,16,8);book=np.fromfile(p/'codebooks.f32','<f4');faiss.copy_array_to_vector(book,pq.centroids);expected=pq.compute_codes(v)
        inverse=np.empty(N,np.int32);inverse[ids]=np.arange(N,dtype=np.int32)
        assert np.array_equal(expected,codes[inverse[sample]])
        receipts.append(dict(dataset=ds,old_native_ID_score_route_prefix_bits_equal=True,qualification_n=128,
            merge_oracles_all_points=True,full_base_ID_partition_checked=N,independent_PQ_assignment_check=4096))
    dump(R/'reviews/qualification_audit.json',dict(status='PASS_E187_QUALIFICATION_AUDIT',datasets=receipts,seconds=time.perf_counter()-t))
    files=[]
    for root in ['src','scripts','configs','models','bin']:
        for p in sorted((R/root).rglob('*')):
            if p.is_file():files.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
    for p in [R/'protocol.md',R/'reviews/build.log',OLD/'src/residual_tools.cpp',R.parent/'20261015_m5_k100_capacity_v1/src/capacity.hpp',R.parent/'20261015_m5_k100_capacity_v1/src/optimized.hpp',Path('/root/acsg-e172-storage-v2/campaign/common/acsg_current.o'),R.parents[1]/'build/ACSG/libACSG.a',R.parents[1]/'build/faiss/faiss/libfaiss.a']:
        files.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
    large=[]
    for ds in ['coco','deep10m_l2_v1']:
        c=json.loads((R/f'configs/{ds}.json').read_text())
        for key in ['base','index']:
            p=Path(c[key]['path'] if key=='base' else c[key]);s=p.stat();large.append(dict(dataset=ds,role=key,path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,inode=s.st_ino,identity='E183 frozen asset plus current stat; base vector stream SHA in backend.json'))
        paths=[c[k]['path'] for k in ['queries','test_gt','train_queries','train_gt']]+[c['table']]+[c['router'][k] for k in ['ids','W','graph']]+[str(Path(c['teacher_dir'])/'raw'/k) for k in ['ids.i32','distances.f32']]
        for name in paths:
            p=Path(name);files.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
    dump(R/'freeze.json',dict(status='FROZEN_BEFORE_FORMAL',timestamp=time.strftime('%Y-%m-%dT%H:%M:%S%z'),files=files,large_assets=large,formal_quality_read=False))
    print('PASS qualification and model/source/config freeze',time.perf_counter()-t)
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Verify complete thin-label artifacts without inspecting audit performance."""
import hashlib,json
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parents[1]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def main():
    result={'status':'PASS','datasets':[],'audit_performance_inspected':False}
    pop=np.array([i.bit_count() for i in range(1024)],dtype='uint8')
    for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
        inp=OUT/'inputs'/ds;c=json.loads((inp/'runner_config.json').read_text());n=c['num_queries'];h=c['hub_count'];root=OUT/'labels'/ds
        done=json.loads((root/'complete.json').read_text());assert done['status']=='COMPLETE' and done['calls']==n*h*2
        hubs=np.fromfile(c['hub_ids'],dtype='int32');gt=np.memmap(c['gt_file'],dtype='int64',mode='r',shape=(n,100))
        checked=[]
        for L in [64,128]:
            ld=root/f'L{L}';assert json.loads((ld/'complete.json').read_text())['logical_search_calls']==n*h
            files={}
            for name,dtype,bytes_ in [('hitcount.u8','uint8',1),('hitmask.u16','uint16',2),('ndc.u32','uint32',4)]:
                p=ld/name;assert p.stat().st_size==n*h*bytes_;files[name]={'bytes':p.stat().st_size,'sha256':sha(p)}
            counts=np.memmap(ld/'hitcount.u8',dtype='uint8',mode='r',shape=(n,h));mask=np.memmap(ld/'hitmask.u16',dtype='uint16',mode='r',shape=(n,h));ndc=np.memmap(ld/'ndc.u32',dtype='uint32',mode='r',shape=(n,h))
            limit=c['fit_count']+c['cal_count']
            for begin in range(0,limit,1024):
                end=min(begin+1024,limit);assert np.all(mask[begin:end]<1024)
                assert np.array_equal(counts[begin:end],pop[mask[begin:end]]) and np.all(ndc[begin:end]>=1)
            ids=np.fromfile(ld/'first2.ids.i32',dtype='int32').reshape(2,h,10)
            for row in range(2):
                for col in range(h):
                    actual=sum(1<<k for k,g in enumerate(gt[row,:10]) if g in ids[row,col])
                    assert actual==int(mask[row,col])
            checked.append({'L':L,'files':files,'fit_cal_rows_structurally_checked':limit,'independent_full_ID_checks':2*h})
        for s in c['seeds']:
            cols=np.fromfile(s['union_columns'],dtype='int32');seedh=np.fromfile(s['hub_ids'],dtype='int32');assert np.array_equal(hubs[cols],seedh)
        result['datasets'].append({'dataset':ds,'logical_calls':done['calls'],'hubs':h,'queries':n,'checks':checked})
    (OUT/'reviews/full_labels_verified.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','logical_calls':sum(d['logical_calls'] for d in result['datasets'])}))
if __name__=='__main__':main()

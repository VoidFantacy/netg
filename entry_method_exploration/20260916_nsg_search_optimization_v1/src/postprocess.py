"""Read-only verification and summaries. Run only after all native queries finish."""
import csv, hashlib, json, math, pathlib, statistics, datetime
import numpy as np
D=pathlib.Path(__file__).resolve().parent.parent
R=D.parent.parent
E=R/'entry_method_exploration/20260915_gate_l2_r1_r100_v1'

def read(p): return json.loads(p.read_text())
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()
def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def write_csv(p,rows):
    assert rows
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    state=read(D/'state.json');assert state['status']=='MEASUREMENTS_COMPLETE',state
    assert state['search_calls']==2296000
    for manifest in ['frozen_code.json','frozen_configs.json']:
        for p,h in read(D/'reviews'/manifest).items(): assert digest(pathlib.Path(p))==h,p
    for p,v in read(D/'reviews/protected.json').items():
        p=pathlib.Path(p);assert p.stat().st_size==v['bytes'] and digest(p)==v['sha256'],str(p)
    old={}
    with (E/'results/metrics.csv').open() as f:
        for x in csv.DictReader(f):old[x['dataset'],int(x['K']),int(x['L']),x['method']]=x
    rows=[];rounds=[];datasets=[];raw=[]
    for name in state['completed']:
        root=D/'results'/name;c=read(root/'config.json');frozen=read(D/'configs'/f'{name}.json');assert c==frozen
        done=read(root/'complete.json');assert done['status']=='PASS' and done['threads']==1 and done['cpu']==15
        assert done['maxrss_kib']<64*1024*1024
        gtpath=pathlib.Path(c['gt']);data=np.fromfile(gtpath,dtype='<i4');width=int(data[0]);assert width>=100
        gt=data.reshape(-1,width+1);assert np.all(gt[:,0]==width) and gt.shape[0]==c['n'];gt=gt[:,1:]
        dsrows=[];timing=read(root/'timing_progress.json') if c['performance'] else []
        for t in timing:
            assert t['threads']==1 and t['cpu']==15 and t['e97_bit_parity'] and t['n']==c['n']
            assert math.isclose(t['qps'],t['n']/t['seconds'],rel_tol=1e-12)
            rounds.append(t)
        for point in c['points']:
            k,L=point['K'],point['L']
            for method in c['methods']:
                m=method['name']
                if m=='HNSW' and not c['performance']:continue
                kernels=['reference'] if m=='HNSW' else (['legacy','optimized'] if c['performance'] else ['optimized'])
                for kernel in kernels:
                    path=root/f'{m}__{kernel}_K{k}_L{L}';pdone=read(path/'complete.json')
                    assert pdone['status']=='PASS' and pdone['per_query_ndc_and_bit_output_parity']
                    reference=pathlib.Path(c['reference_results'])/f'k{k}'/f'{m}_L{L}'
                    for filename,size in [('ids.i32',c['n']*k*4),('distances.f32',c['n']*k*4),('entry_ids.i32',c['n']*3*4),('route_ndc.u64',c['n']*8),('graph_ndc.u64',c['n']*8)]:
                        new=path/filename;ref=reference/filename
                        assert new.stat().st_size==size and ref.stat().st_size==size,str(new)
                        h=digest(new);assert h==digest(ref),str(new)
                        raw.append({'file':str(new.relative_to(D)),'reference':str(ref),'bytes':size,'sha256':h})
                    ids=np.fromfile(path/'ids.i32',dtype='<i4').reshape(c['n'],k)
                    assert np.all(ids>=0)
                    if k>1:assert np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
                    hits=np.array([np.intersect1d(a,b,assume_unique=True).size for a,b in zip(ids,gt[:,:k])],dtype=np.int32)
                    recall=float(hits.mean()/k);o=old[name,k,L,m]
                    assert abs(recall-float(o['recall']))<1e-12,(name,k,L,m,recall,o['recall'])
                    r=np.fromfile(path/'route_ndc.u64',dtype='<u8');g=np.fromfile(path/'graph_ndc.u64',dtype='<u8')
                    for key,v in [('route_ndc_mean',r.mean()),('graph_ndc_mean',g.mean())]: assert abs(v-float(o[key]))<1e-8
                    tr=sorted([t for t in timing if t['method']==m and t['kernel']==kernel and t['K']==k and t['L']==L],key=lambda t:t['repeat'])
                    assert len(tr)==(3 if c['performance'] else 0)
                    assert [t['seconds'] for t in tr]==pdone['seconds']
                    qps=[t['qps'] for t in tr];wall=[t['seconds'] for t in tr]
                    row={'dataset':name,'K':k,'L':L,'method':m,'kernel':kernel,'queries':c['n'],'recall':recall,
                         'qps_mean':statistics.mean(qps) if qps else '', 'qps_min':min(qps) if qps else '', 'qps_max':max(qps) if qps else '',
                         'qps_from_mean_wall':c['n']/statistics.mean(wall) if wall else '', 'zero_hit_queries':int((hits==0).sum()),
                         'route_ndc_mean':float(r.mean()),'graph_ndc_mean':float(g.mean()),'e97_bit_and_ndc_parity':True,'threads':1}
                    for i in range(3):row[f'qps_round{i+1}']=qps[i] if qps else ''
                    rows.append(row);dsrows.append(row)
        planned=1800000 if c['performance'] else 16*c['n']
        assert done['search_calls']==planned
        datasets.append({'dataset':name,'points':len(dsrows),'queries_per_point':c['n'],'search_calls':done['search_calls'],
                         'timed_rounds':done['wall_rounds'],'seconds_excluding_load':done['seconds_excluding_load'],
                         'max_rss_gib':done['maxrss_kib']/1024**2,'bit_and_ndc_parity':'PASS'})
    assert len(rows)==100 and len(raw)==500 and len(rounds)==108
    pairs=[]
    for row in rows:
        if row['kernel']!='optimized' or row['qps_mean']=='':continue
        legacy=next(x for x in rows if x['dataset']==row['dataset'] and x['K']==row['K'] and x['L']==row['L'] and x['method']==row['method'] and x['kernel']=='legacy')
        ratios=[row[f'qps_round{i}']/legacy[f'qps_round{i}'] for i in [1,2,3]]
        pairs.append({'K':row['K'],'L':row['L'],'method':row['method'],'recall':row['recall'],'legacy_qps':legacy['qps_mean'],
                      'optimized_qps':row['qps_mean'],'speedup_percent':100*(row['qps_mean']/legacy['qps_mean']-1),
                      'paired_min_percent':100*(min(ratios)-1),'paired_max_percent':100*(max(ratios)-1),
                      'legacy_repeat_range_percent':100*(legacy['qps_max']-legacy['qps_min'])/legacy['qps_mean'],
                      'optimized_repeat_range_percent':100*(row['qps_max']-row['qps_min'])/row['qps_mean']})
    assert len(pairs)==16
    write_csv(D/'results/metrics.csv',rows);write_csv(D/'results/wall_rounds.csv',rounds);write_csv(D/'results/paired_speedup.csv',pairs)
    write_csv(D/'results/dataset_audit.csv',datasets);dump(D/'reviews/raw_parity.json',raw)
    audit={'status':'PASS','timestamp':datetime.datetime.now().isoformat(),'points':len(rows),'files_verified':len(raw),'raw_bytes':sum(x['bytes'] for x in raw),
           'search_calls':state['search_calls'],'wall_rounds':len(rounds),'datasets':datasets,'frozen_code_and_configs':'PASS','protected_previous_assets':'PASS',
           'recall_and_distance_counts_match_e97':'PASS','new_training_or_graph_builds':0}
    dump(D/'reviews/results_audit.json',audit)
    print(json.dumps(audit,ensure_ascii=False,indent=2))
    print('WEB_SPEEDUPS',json.dumps(pairs,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

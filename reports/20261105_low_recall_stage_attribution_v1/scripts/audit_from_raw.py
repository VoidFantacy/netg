"""Independent stdlib recomputation from original GT and actual timed ID packets."""
from pathlib import Path
import array,csv,json,hashlib,sys,time
from collections import Counter
W=Path(__file__).resolve().parents[3];R=Path(__file__).resolve().parents[1]
E=W/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1'
OLD=W/'reports/20261024_failure_rescue_residual_lt10_v2'
def read(p):return list(csv.DictReader(p.open()))
def ints(p,code='i'):
    a=array.array(code)
    with p.open('rb') as f:a.fromfile(f,p.stat().st_size//a.itemsize)
    if sys.byteorder!='little':a.byteswap()
    return a
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
started=time.perf_counter()
source=read(OLD/'failure_by_L.csv');out=read(R/'analysis/stage_attribution_all_datasets.csv')
summary={(x['dataset'],int(x['L'])):x for x in out}
paths={(x['dataset'],int(x['L']),x['path']):int(x['count']) for x in read(R/'analysis/three_stage_paths.csv')}
effects={(x['dataset'],int(x['L']),x['stage']):x for x in read(R/'analysis/stage_effects_and_costs.csv')}
evaluations=0;groups=0
for ds in dict.fromkeys(x['dataset'] for x in source):
    cfg=json.loads((E/f'configs/{ds}.analysis.json').read_text());d=cfg['eval_gt']
    n=d['n'];width=d.get('width',d.get('k',100));offset=d.get('row_start',0)
    raw=ints(Path(d['path']),'q' if d['format']=='raw_i64' else 'i')
    stride=width+1 if d['format']=='ivecs' else width;head=1 if d['format']=='ivecs' else 0
    gt=[]
    for i in range(offset,offset+n):
        if head:assert raw[i*stride]==width
        v=set(raw[i*stride+head:i*stride+head+100]);assert len(v)==100;gt.append(v)
    for L in sorted({int(x['L']) for x in source if x['dataset']==ds}):
        hits={}
        for p in (x for x in source if x['dataset']==ds and int(x['L'])==L):
            ids=ints(E/f"results/{ds}/k100/{p['source_method']}_L{L}/raw/ids.i32")
            assert len(ids)==n*100
            hh=[]
            for i in range(n):
                row=set(ids[i*100:(i+1)*100]);assert len(row)==100
                hh.append(len(gt[i]&row))
            hits[p['method']]=hh;evaluations+=n
            assert sum(x<10 for x in hh)==int(p['low_count'])
            assert sum(x==10 for x in hh)==int(p['exactly10_count'])
            assert abs(sum(hh)/n-float(p['recall_pct']))<1e-10
        counter=Counter();gfix=gnew=bfix=bnew=0
        for a,b,c in zip(hits['NSG'],hits['GT10'],hits['B32']):
            x,y,z=a<10,b<10,c<10
            counter[f'{int(x)}{int(y)}{int(z)}']+=1
            gfix+=x and not y;gnew+=not x and y;bfix+=y and not z;bnew+=not y and z
        for code in range(8):assert counter[format(code,'03b')]==paths[ds,L,format(code,'03b')]
        result=summary[ds,L]
        for key,v in [('GT10_rescued',gfix),('GT10_new_low',gnew),('B32_rescued',bfix),('B32_new_low',bnew),('B32_rescued_NSG_legacy',counter['110']),('B32_rescued_GT10_induced',counter['010']),('NSG_original_final_rescued',counter['100']+counter['110']),('GT10_induced_final_unresolved',counter['011'])]:assert int(result[key])==v,(ds,L,key)
        for stage,a,b in [('GT10_vs_NSG','NSG','GT10'),('B32_vs_GT10','GT10','B32')]:
            row=effects[ds,L,stage];deltas=[j-i for i,j in zip(hits[a],hits[b])]
            assert abs(sum(deltas)/n-float(row['mean_recall_gain_pp']))<1e-10
            tail=sum(v for h,v in zip(hits[a],deltas) if h<10)/n
            assert abs(tail-float(row['net_recall_gain_from_reference_low_pp']))<1e-10
        groups+=1
    print('AUDIT',ds,flush=True)
oldinputs=json.loads((OLD/'inputs_manifest.json').read_text())
for name,meta in oldinputs.items():
    p=Path(name);assert p.stat().st_size==meta['bytes'] and sha(p)==meta['sha256'],name
identity=json.loads((R/'source_before/identity.json').read_text())
for name,h in identity['sources'].items():assert sha(W/name)==h,name
receipt=dict(status='PASS_STDLIB_ACTUAL_GT_AND_PACKET_RECOMPUTATION',independence='same operator; separate implementation and raw-GT/packet input route; no NumPy import',points=147,three_stage_groups=groups,paths=392,query_point_evaluations=evaluations,original_input_hashes_rechecked=len(oldinputs),protected_sources_unchanged=len(identity['sources']),all_exactly10_excluded=True,new_ANN=0,new_timing=0,seconds=time.perf_counter()-started)
(R/'reviews/raw_audit.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print('PASS_RAW_AUDIT',round(receipt['seconds'],2),'seconds',flush=True)

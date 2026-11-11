"""Report available-method median frontiers without selecting or running new points."""
import csv,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def rows(path):return list(csv.DictReader(path.open()))
def write(path,data):
    with path.open('w') as f:
        w=csv.DictWriter(f,list(data[0]));w.writeheader();w.writerows(data)
def main():
    assert (R/'dense_complete.json').exists();t=time.perf_counter();allrows=[];lookup={}
    for window,name in [('primary','all_primary_points.csv'),('dense','all_dense_points.csv')]:
        p=rows(R/'analysis'/name)
        for x in p:
            if x['method'] not in ['REUSE-SQ','MAIN-SQ']:continue
            controls=[y for y in p if y['dataset']==x['dataset'] and y['K']==x['K'] and
                      (y['method']!=x['method'] or y['L']!=x['L']) and
                      float(y['recall_pct'])>=float(x['recall_pct']) and float(y['qps'])>=float(x['qps'])]
            v=dict(window=window,dataset=x['dataset'],K=x['K'],method=x['method'],L=x['L'],recall_pct=x['recall_pct'],qps=x['qps'])
            for m,label in [('GT10','GT10'),('B32','B32'),('REUSE-PQ','REUSE_PQ')]:
                z=[y for y in controls if y['method']==m];v[label+'_dominating_L']=','.join(y['L'] for y in z);v[label+'_nonoverlap_L']=','.join(y['L'] for y in z if float(y['qps_min'])>float(x['qps_max']))
            v['other_SQ_dominating_points']=','.join(y['method']+'@'+y['L'] for y in controls if y['method'] in ['REUSE-SQ','MAIN-SQ'])
            v['median_nondominated_in_available_grid']=not bool(controls);allrows.append(v);lookup[window,x['dataset'],x['K'],x['method'],x['L']]=v
    write(R/'analysis/all_method_dominance.csv',allrows)
    confirmed=rows(R/'analysis/confirmed_screens.csv');assessed=[]
    for x in confirmed:
        z=lookup['dense',x['dataset'],x['K'],x['method'],x['L']]
        assessed.append(dict(**x,existing_B32_dominating_L=z['B32_dominating_L'],existing_PQ_dominating_L=z['REUSE_PQ_dominating_L'],other_SQ_dominating_points=z['other_SQ_dominating_points'],median_nondominated_in_available_grid=z['median_nondominated_in_available_grid']))
    if assessed:write(R/'analysis/candidate_assessment.csv',assessed)
    else:(R/'analysis/candidate_assessment.csv').write_text('dataset,K,method,L,decision\n')
    v=dict(status='PASS_AVAILABLE_METHOD_FRONTIER_REPORT',rows=len(allrows),assessed=len(assessed),GT_screen_retained=sum(x['decision']=='RETAIN_EXPLORATORY' for x in assessed),GT_retained_but_B32_or_PQ_covered=sum(x['decision']=='RETAIN_EXPLORATORY' and bool(x['existing_B32_dominating_L'] or x['existing_PQ_dominating_L']) for x in assessed),scope='same-window actual finite grid; median dominance and nonoverlap separately recorded; no new experiment or new selection',seconds=time.perf_counter()-t)
    (R/'reviews/all_method_comparison.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True)
if __name__=='__main__':main()

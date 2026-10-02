"""Final read-only integrity, independent control checks, budgets and local document links."""
import datetime
import difflib
import re
import time
from urllib.parse import unquote
from common import *
from prepare_supplement import SUP,ident,calls

def main():
    started=time.monotonic();old=read(RUN/'reviews/old_assets_before.json')['files'];oldchanged=[]
    for x in old:
        p=Path(x['path']);st=p.stat()
        if st.st_size!=x['bytes'] or st.st_mtime_ns!=x['mtime_ns'] or sha(p)!=x['sha256']:oldchanged.append(x['path'])
    assert not oldchanged,oldchanged
    print('OLD_ASSETS_PASS',len(old),flush=True)
    upstream=read(SUP/'reviews/upstream.json')['files']
    for x in upstream:
        p=Path(x['path']);st=p.stat();assert st.st_size==x['bytes'] and st.st_mtime_ns==x['mtime_ns']
        assert sha(p)==x['sha256'],str(p)
    for x in read(SUP/'reviews/frozen_before_search.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
    for x in read(SUP/'reviews/controller_before_search.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
    source=(SUP/'src/evaluate.cpp').read_text();reference=(VERSIONS[26]/'src/evaluate.cpp').read_text()
    assert source==reference.replace('require(m.at("k")==3 && !m.value("exact",false),"three-entry HNSW profile required");',
                                    'require(m.at("k")==3,"three-entry profile required (exact3 or HNSW3)");')
    assert sha(SUP/'src/benchmark_with_nsg.cpp')==sha(VERSIONS[24]/'src/benchmark_with_nsg.cpp')
    lock=read(SUP/'config.locked.json');jobs=read(SUP/'reviews/search_jobs.json');assert len(jobs)==9
    assert sum(x['actual_calls'] for x in jobs)==sum(x['reserved_calls'] for x in jobs)==181376
    assert all(x['status']=='COMPLETE' and x['max_observed_process_threads']==1 and x['stop_reason'] is None for x in jobs)
    verified=0;points=0
    for j in jobs:
        c=read(j['config']);assert calls(c)==j['actual_calls'] and c['threads']==1 and c['query_cpu']==15
        v=read(SUP/'reviews'/f"{j['name']}_verified.json");assert v['status']=='PASS'
        verified+=v['independently_scored'];points+=len(v['checks'])
    assert verified==36448 and points==30
    independent=[];perm=arr(SUP/'models/row_permutation.i64','<i8');assert np.array_equal(np.sort(perm),np.arange(20000))
    assert not np.any(perm==np.arange(20000))
    for ds in DATASETS:
        inp=VERSIONS[24]/'inputs'/ds;meta=read(inp/'prepared.json');h,d=meta['H'],meta['dim']
        ranks=np.load(RUN/'results'/f'{ds}_fit_assignments.npz')['rank_hubs'];hids=arr(inp/'hub_ids.i32','<i4')
        raw=norm(arr(inp/'raw_hubs.f32','<f4',(h,d)));q=norm(arr(inp/'fit/queries.f32','<f4',(20000,d)))
        w=arr(SUP/'models'/ds/'W.f32','<f4',(h,d));assert np.isfinite(w).all()
        assert np.max(np.abs(np.linalg.norm(w,axis=1)-1))<2e-6
        for column in [0,h//2,h-1]:
            # Independent per-hub scalar-weight accumulation, no dense assignment product.
            weight=((ranks[:,0]==hids[column]).astype('float64')+(ranks[perm,1:]==hids[column]).sum(1))*.1
            total=raw[column].astype('float64').copy()
            for i in np.flatnonzero(weight):total+=weight[i]*q[i].astype('float64')
            expected=total/np.linalg.norm(total);err=float(np.max(np.abs(expected-w[column])))
            assert err<2e-6
            independent.append({'dataset':ds,'hub_id':int(hids[column]),'max_abs_error':err,'status':'PASS'})
    original=read(RUN/'reviews/existing_verification.json');assert original['status']=='PASS' and original['rescored_outputs']==169152
    cost=read(SUP/'reviews/execution_complete.json')
    dump(RUN/'results/costs.json',{'existing_analysis_success_seconds':read(RUN/'results/existing_evidence.json')['analysis_seconds'],
       'failed_first_analysis_seconds':None,'failed_first_analysis_reason':'schema-reading failure before new search; external wall not recorded',
       'target_links_seconds':None,'target_links_reason':'read-only postprocessing wall not separately instrumented',
       'supplement_prepare_seconds':read(SUP/'reviews/frozen_before_search.json')['prepared_seconds'],
       'shuffle_construction':read(SUP/'models/construction.json'),'compile_seconds':read(SUP/'bin/evaluate.build.json')['seconds'],
       'query_execution':cost,'new_training_label_calls':0,'exact_GT_from_scratch_seconds':None,'QGT_from_scratch_seconds':None,
       'NSG_from_scratch_seconds':None,'from_scratch_reason':'old frozen assets reused; not newly measured; not zero cost',
       'timing_boundary':'formal QPS only from independent plain wall; process/analysis/compile/count times not QPS'})
    before=['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md'];diff=[]
    for name in before:
        diff+=list(difflib.unified_diff((RUN/'source_before'/name).read_text().splitlines(True),(ROOT/name).read_text().splitlines(True),
                                     fromfile='before/'+name,tofile='after/'+name))
    (RUN/'reviews/document_changes.patch').write_text(''.join(diff))
    cards=sorted((ROOT/'experiment_history').glob('[0-9][0-9]_*.md'))
    docs=[ROOT/x for x in before]+cards+[ROOT/'experiment_history/README.md',RUN/'report.md',RUN/'existing_report.md',
        RUN/'protocol.md',RUN/'results/tables.md',SUP/'protocol.md',RUN/'commands.md']
    missing=[];format_issues=[];count=0
    for p in docs:
        text=p.read_text()
        if len(re.findall(r'^```',text,re.M))%2:format_issues.append(str(p))
        for target in re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)',text):
            target=target.strip().strip('<>')
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target):continue
            part=unquote(target.split('#',1)[0])
            if not part:continue
            count+=1;dest=(p.parent/part).resolve()
            if dest==RUN/'reviews/final_audit.json':continue
            if not dest.exists():missing.append({'file':str(p),'target':target})
    assert len(cards)==16
    index=(ROOT/'s-experiment.md').read_text();assert all(f'](experiment_history/{p.name})' in index for p in cards)
    assert not missing and not format_issues,(missing,format_issues)
    assert 'GT10_MECHANISM_ANALYSIS_PLANNED_UNRUN' not in (ROOT/'s-target.md').read_text()
    for name in ['quality_and_timing','gain_loss_all_L','correspondence_control']:
        for ext in ['png','svg']:assert (RUN/'figures'/f'{name}.{ext}').stat().st_size>1000
    status='GT10_MECHANISM_ANALYSIS_COMPLETE_WITH_BOUNDED_DIAGNOSTICS'
    dump(RUN/'state.json',{'status':status,'complete_unix':time.time(),'existing_analysis_points':108,'existing_rescored_outputs':169152,
         'new_points':30,'new_rescored_outputs':36448,'new_real_calls':181376,'repair_calls':0,'synthetic_calls':0,
         'next_method_selected':False,'heldout_access':False,'all_authorized_stages_complete':True})
    audit={'status':'PASS','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'old_E24_E25_E26_files_full_hash_checked':len(old),'old_assets_changed':oldchanged,'upstream_full_hash_checked':len(upstream),
       'frozen_before_search_unchanged':True,'only_evaluator_change_is_existing_exact3_admission':True,
       'existing_points':108,'existing_independent_outputs':169152,'new_points':points,'new_independent_outputs':verified,
       'actual_normal_calls':181376,'repair_calls':0,'synthetic_calls':0,'all_jobs_actual_threads_1_CPU15':True,
       'shuffle_independent_scalar_reference':independent,'documents_checked':len(docs),'local_links_checked':count,
       'missing_links':missing,'format_issues':format_issues,'all_16_history_cards_indexed':True,
       'heldout_access':False,'next_method_selected':False,'audit_seconds':time.monotonic()-started,
       'limitations':['one build and historical queries','single permutation, not matched ESS/direction','exact supplement only two posthoc positive points',
                      'no direct expansion-path/cache measurements','query intervals descriptive and unadjusted']}
    dump(RUN/'reviews/final_audit.json',audit)
    print('FINAL_AUDIT_PASS',len(old),len(upstream),len(docs),count,flush=True)

if __name__=='__main__':main()

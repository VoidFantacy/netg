"""Close the authorized E26 and tonight's work after all evidence and docs exist."""
import re
import shutil
import time
from pathlib import Path
from urllib.parse import unquote
from common import ROOT,RUN,DATASETS,read,dump,identity,check_lock,frozen_check
from write_report import STATUS


def main():
    lock=check_lock();frozen_check('cal');frozen_check('audit')
    final_path=RUN/'reviews/final_audit.json';assert not final_path.exists()
    integrity=read(RUN/'reviews/immutable_integrity.json');assert integrity['status']=='PASS'
    for before in integrity['protected_upstream']:
        s=Path(before['path']).stat();assert s.st_size==before['bytes'] and s.st_mtime_ns==before['mtime_ns'],before['path']
    assert len(integrity['protected_upstream'])==115
    jobs=read(RUN/'reviews/search_jobs.json');synthetic=read(RUN/'reviews/synthetic_jobs.json')
    assert len(jobs)==8 and all(j['status']=='COMPLETE' and j['max_observed_process_threads']==1 for j in jobs)
    assert sum(j['actual_calls'] for j in jobs)==897280==lock['normal_real_call_cap']
    assert sum(j['reserved_calls'] for j in synthetic)==2268 and all(j['status']=='COMPLETE' for j in synthetic)
    assert not any(j['repair'] for j in jobs)
    assert sum(j['process_seconds'] for j in jobs)<lock['total_search_seconds']
    active=[]
    for j in jobs:
        p=Path(f"/proc/{j['pid']}/cmdline")
        if p.exists() and str(RUN/'bin/evaluate').encode() in p.read_bytes():active.append(j['pid'])
    assert not active
    points=outputs=0
    for ds in DATASETS:
        for stage in ['recovery','cal','audit']:
            v=read(RUN/'diagnostics'/ds/stage/'independent_verification.json')
            assert v['status']=='PASS';points+=v['points'];outputs+=v['independently_scored_outputs']
        v=read(RUN/'results'/ds/'independent_verification.json')
        assert v['status']=='PASS';points+=v['points'];outputs+=v['independently_scored_outputs']
    assert points==110 and outputs==177760
    for check in ['validation_verification','recovery_gate','synthetic_gate','effect_accounting_selftest','profile_math_selftest','selection_selftest','cal_entry_transitions','audit_entry_transitions','validation_entry_transitions']:
        assert read(RUN/'reviews'/f'{check}.json')['status']=='PASS',check
    analysis=read(RUN/'results/analysis.json')
    for ds,d in analysis['datasets'].items():
        assert d['selected_alpha']==.75 and d['cal_selection_status']=='CAL_TARGET_NOT_MET'
        assert not d['development']['audit']['selected']['pooled']['target_met']
        assert not d['validation']['pooled_L64_L128']['stats']['target_met']
    summary=read(RUN/'results/summary.json');assert summary['status']==STATUS
    summary['execution_status']='COMPLETE_CLOSED';dump(RUN/'results/summary.json',summary)
    state={'status':STATUS,'execution_status':'COMPLETE_CLOSED','completed_unix':time.time(),
        'real_calls':897280,'synthetic_calls':2268,'repair_calls':0,'independently_scored_points':110,
        'independently_scored_outputs':177760,'E25_four_curve_bit_regression_outputs':80000,
        'protocol_sha256':lock['protocol_sha256'],'formal_performance_GO':False,
        'cal_audit_and_validation_targets':'NOT_MET_BOTH_DATASETS','primary_alpha':{ds:.75 for ds in DATASETS},
        'active_job':None,'remaining_protocol_stages':[],'validation_opened':True,'heldout_opened':False,
        'validation_scope':'historical first2000 after global freeze and audit',
        'night_task_status':'COMPLETE_EARLY_AT_USER_REQUEST; discuss tomorrow before any new experiment',
        'authorization_update':'authorization_update.md','old_probe_C_or_large_queue_restarted':False}
    dump(RUN/'state.json',state)
    required=['README.md','report.md','commands.md','protocol.md','config.locked.json','authorization_update.md',
        'results/tables.md','results/summary.json','results/analysis.json','results/comparisons.csv','results/costs.json',
        'results/cross_experiment_quality_only.json',
        *[f'figures/{name}.{ext}' for name in ['recall_qps','retention_total_harm','gain_loss_decomposition','deltas_vs_e24'] for ext in ['svg','png']]]
    assert all((RUN/p).is_file() and (RUN/p).stat().st_size for p in required)
    documents=[ROOT/p for p in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']]
    cards=sorted((ROOT/'experiment_history').glob('[0-9][0-9]_*.md'));documents+=cards
    documents += [RUN/p for p in ['README.md','report.md','commands.md','protocol.md','authorization_update.md','results/tables.md']]
    index=(ROOT/'s-experiment.md').read_text();entries=re.findall(r'^\| (E\d{2})\b',index,re.M)
    assert len(cards)==15 and len(entries)==26 and set(entries)=={f'E{i:02}' for i in range(1,27)}
    assert all(str(p.relative_to(ROOT)) in index for p in cards)
    links=[];missing=[]
    for p in documents:
        content=p.read_text();assert len(re.findall(r'^```',content,re.M))%2==0,str(p)
        for target in re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)',content):
            target=target.strip().strip('<>')
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):continue
            resolved=(p.parent/unquote(target.split('#',1)[0])).resolve()
            record={'document':str(p.relative_to(ROOT)),'target':target,'resolved':str(resolved)};links.append(record)
            if not resolved.exists() and resolved!=final_path:missing.append(record)
    assert not missing,missing
    for p in [ROOT/'summary.md',ROOT/'s-target.md',ROOT/'s-experiment.md',ROOT/'experiment_history/15_profile_shrinkage.md',RUN/'report.md']:
        assert STATUS in p.read_text(),str(p)
    assert read(RUN/'reviews/visual_checks.json')['status']=='PASS'
    bytes_before=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
    assert bytes_before<lock['output_limit_bytes'] and shutil.disk_usage(ROOT).free>=lock['min_free_bytes']
    audit={'status':'PASS','completed_unix':time.time(),'execution':state,'active_evaluators':active,
        'scope':'E26 and the latest authorized tonight scope complete; no automatic further experiment',
        'checked_documents':len(documents),'checked_links':len(links),'missing_links':missing,'links':links,
        'document_identities':[identity(p) for p in documents],
        'artifact_bytes_before_final_manifest':bytes_before,'upstream_integrity':identity(RUN/'reviews/immutable_integrity.json'),
        'visual_checks':identity(RUN/'reviews/visual_checks.json'),
        'no_new_queries_after_locked_matrix':True,'E25_sealed_artifacts_preserved':True,'memory_files_modified':False}
    dump(final_path,audit);assert all(Path(item['resolved']).exists() for item in links)
    dump(RUN/'reviews/delivery_manifest.json',{'status':STATUS,'files':[identity(RUN/p) for p in required],
        'state':identity(RUN/'state.json'),'final_audit':identity(final_path),
        'measured_result_files':[identity(p) for folder in [RUN/'diagnostics',*[RUN/'results'/ds for ds in DATASETS]] for p in sorted(folder.rglob('*')) if p.is_file()],
        'source_files':[identity(p) for p in sorted((RUN/'src').iterdir()) if p.is_file()]})
    assert sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())<lock['output_limit_bytes']
    print('E26_FINAL_DELIVERY_PASS',len(documents),'documents',len(links),'links',bytes_before,'bytes',flush=True)


if __name__=='__main__':main()

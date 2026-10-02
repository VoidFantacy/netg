"""Close E25 only; the separately authorized overnight task continues until morning."""
import re
import shutil
import time
from pathlib import Path
from urllib.parse import unquote
from common import ROOT, RUN, DATASETS, read, dump, identity, sha, check_lock, frozen_gate_check

STATUS='SELECTIVITY_NOT_GENERALIZED_NO_FORMAL_GO'


def main():
    lock=check_lock();frozen_gate_check()
    assert not (RUN/'reviews/final_audit.json').exists()
    integrity=read(RUN/'reviews/immutable_integrity.json');assert integrity['status']=='PASS'
    for record in integrity['protected_upstream']:
        p=Path(record['path']);s=p.stat()
        assert s.st_size==record['bytes'] and s.st_mtime_ns==record['mtime_ns'],str(p)
    jobs=read(RUN/'reviews/search_jobs.json');synthetic=read(RUN/'reviews/synthetic_jobs.json')
    assert len(jobs)==10 and all(j['status']=='COMPLETE' and j['max_observed_process_threads']==1 for j in jobs)
    assert sum(j['actual_calls'] for j in jobs)==1089152==lock['normal_real_call_cap']
    assert sum(j['reserved_calls'] for j in synthetic)==5144
    assert all(j['status']=='COMPLETE' for j in synthetic)
    assert not any(j['repair'] for j in jobs)
    active=[]
    for j in jobs:
        p=Path(f"/proc/{j['pid']}/cmdline")
        if p.exists() and str(RUN/'bin/evaluate').encode() in p.read_bytes():active.append(j['pid'])
    assert not active
    points=outputs=0
    for ds in DATASETS:
        for stage in ['recovery','fit','cal','audit']:
            v=read(RUN/'diagnostics'/ds/stage/'independent_verification.json')
            assert v['status']=='PASS';points+=v['points'];outputs+=v['independently_scored_outputs']
        v=read(RUN/'results'/ds/'independent_verification.json')
        assert v['status']=='PASS';points+=v['points'];outputs+=v['independently_scored_outputs']
    assert points==124 and outputs==219584
    assert read(RUN/'reviews/validation_verification.json')['status']=='PASS'
    assert read(RUN/'reviews/recovery_gate.json')['status']=='PASS'
    assert read(RUN/'reviews/synthetic_gate.json')['status']=='PASS'
    assert read(RUN/'reviews/learner_selftest.json')['status']=='PASS'
    report=read(RUN/'results/analysis.json')
    comparisons=[c for c in report['comparisons'] if c['method'] in ['base_gate','dual_gate'] and c['reference']=='e24']
    assert len(comparisons)==20
    assert all(c['delta_recall_pp_95']['low']<=0<=c['delta_recall_pp_95']['high'] for c in comparisons)
    assert not any(c['same_L_recall_better_qps_better_all_three_repeats'] for c in comparisons)
    for ds in DATASETS:
        primary=report['datasets'][ds]['primary_frozen_on_cal']
        assert not report['datasets'][ds]['splits']['audit']['gates'][primary]['pooled_L64_L128']['target_met']
        assert not report['datasets'][ds]['splits']['validation']['gates'][primary]['pooled_L64_L128']['target_met']
    state={'status':STATUS,'execution_status':'COMPLETE_CLOSED','completed_unix':time.time(),
        'real_calls':1089152,'synthetic_calls':5144,'repair_calls':0,'independently_scored_points':124,
        'independently_scored_outputs':219584,'E24_four_curve_bit_regression_outputs':80000,
        'protocol_sha256':lock['protocol_sha256'],'formal_performance_GO':False,
        'audit_and_validation_primary_targets':'NOT_MET_BOTH_DATASETS',
        'primary_frozen_on_cal':{ds:report['datasets'][ds]['primary_frozen_on_cal'] for ds in DATASETS},
        'active_job':None,'remaining_protocol_stages':[],
        'validation_opened':True,'validation_scope':'historical first2000 after freeze and audit',
        'heldout_opened':False,'night_task_status':'continues separately; user summary begins Sep11 07:00 Asia/Shanghai',
        'next_exploration':'one directly related low-cost single-route profile-shrinkage comparison is being considered; requires separate frozen protocol',
        'old_probe_C_or_large_queue_restarted':False}
    dump(RUN/'state.json',state)
    required=['README.md','report.md','commands.md','protocol.md','config.locked.json','overnight_authorization.md',
        'results/tables.md','results/summary.json','results/analysis.json','results/comparisons.csv','results/costs.json',
        'figures/recall_qps.svg','figures/recall_qps.png','figures/retention_harm.svg','figures/retention_harm.png',
        'figures/signal_transfer.svg','figures/signal_transfer.png','figures/deltas_vs_e24.svg','figures/deltas_vs_e24.png']
    assert all((RUN/p).is_file() and (RUN/p).stat().st_size>0 for p in required)
    documents=[ROOT/p for p in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']]
    cards=sorted((ROOT/'experiment_history').glob('[0-9][0-9]_*.md'));documents+=cards
    documents += [RUN/p for p in ['README.md','report.md','commands.md','protocol.md','overnight_authorization.md','results/tables.md']]
    index=(ROOT/'s-experiment.md').read_text();entries=re.findall(r'^\| (E\d{2})\b',index,re.M)
    assert len(cards)==14 and len(entries)==25 and set(entries)=={f'E{i:02}' for i in range(1,26)}
    assert all(str(p.relative_to(ROOT)) in index for p in cards)
    links=[];missing=[];final_path=RUN/'reviews/final_audit.json'
    for p in documents:
        content=p.read_text();assert len(re.findall(r'^```',content,re.M))%2==0,str(p)
        for target in re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)',content):
            target=target.strip().strip('<>')
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):continue
            resolved=(p.parent/unquote(target.split('#',1)[0])).resolve()
            record={'document':str(p.relative_to(ROOT)),'target':target,'resolved':str(resolved)}
            links.append(record)
            if not resolved.exists() and resolved!=final_path:missing.append(record)
    assert not missing,missing
    for p in [ROOT/'summary.md',ROOT/'s-target.md',ROOT/'s-experiment.md',ROOT/'experiment_history/14_selective_profile_gate.md',RUN/'report.md']:
        assert STATUS in p.read_text()
    bytes_before=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
    assert bytes_before<lock['output_limit_bytes'] and shutil.disk_usage(ROOT).free>=lock['min_free_bytes']
    audit={'status':'PASS','completed_unix':time.time(),'execution':state,'active_evaluators':active,
        'scope':'E25 completed exactly; no formal performance GO and no completion of the larger overnight task',
        'checked_documents':len(documents),'checked_links':len(links),'missing_links':missing,'links':links,
        'document_identities':[identity(p) for p in documents],
        'artifact_bytes_before_final_manifest':bytes_before,'upstream_integrity':identity(RUN/'reviews/immutable_integrity.json'),
        'visual_checks':['all four PNGs inspected: two datasets, all methods/negative points, readable axes and legends',
                         'Recall-QPS uses measured median and repeat range; gain/harm chart shows fixed target zone',
                         'uncertainty/deltas and score-transfer figures retain nonpositive results'],
        'no_new_queries_after_locked_matrix':True,'original_documents_preserved':True,'memory_files_modified':False}
    dump(final_path,audit)
    assert all(Path(item['resolved']).exists() for item in links)
    dump(RUN/'reviews/delivery_manifest.json',{'status':STATUS,'files':[identity(RUN/p) for p in required],
         'state':identity(RUN/'state.json'),'final_audit':identity(final_path),
         'source_files':[identity(p) for p in sorted((RUN/'src').iterdir()) if p.is_file()]})
    print('E25_FINAL_DELIVERY_PASS',len(documents),'documents',len(links),'links',bytes_before,'bytes',flush=True)


if __name__=='__main__':main()

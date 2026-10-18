#!/usr/bin/env python3
"""Record actual new costs with nesting boundaries and inherited unknowns."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def read(p):return json.loads(Path(p).read_text())


def main():
    out=ROOT/'analysis/cost_ledger.json';assert not out.exists()
    catalogue=read(ROOT/'reviews/dataset_catalogue.json');datasets={}
    for ds,entry in catalogue['datasets'].items():
        stages={}
        for stage in ('teacher','compile','qualification','benchmark'):
            original=ROOT/'reviews'/f'{stage}_{ds}.execution.json'
            corrected=ROOT/'reviews'/f'{stage}_{ds}.execution.corrected.json'
            p=corrected if corrected.exists() else original;r=read(p)
            assert r['status']=='PASS_NATIVE_EXECUTION'
            complete=read(r['native_complete'])
            stages[stage]={'launch_through_output_checks_seconds':r['elapsed_seconds'],
                'native_internal_outer_seconds_nested':complete.get('outer_seconds'),
                'receipt':str(p),'native_complete':r['native_complete']}
        formal=read(ROOT/'results'/ds/'complete.json')
        walls=[rr['wall_seconds'] for p in formal['results'] for rr in p['rounds']]
        datasets[ds]={'new_stages':stages,'formal_wall_seconds_nested':sum(walls),
            'formal_points':len(formal['results']),'formal_batches':len(walls),
            'current_base_graph_profile_builds':0,
            'inherited_base_graph_profile_GT_cost_seconds':None,
            'inherited_cost_reason':'Reused historical artifacts; no complete cold-start cost was remeasured. Historical receipts remain authoritative and are not reset to zero.',
            'training_role_scope':entry['training_role_scope']}
    builds=[]
    for p in sorted((ROOT/'bin').rglob('build_*.json')):
        r=read(p);builds.append({'receipt':str(p),'status':r['status'],
             'elapsed_seconds':r.get('elapsed_seconds'),'compile_subprocess_seconds_nested':r.get('compile_subprocess_seconds')})
    result={'status':'PASS_ACTUAL_COST_LEDGER','datasets':datasets,'new_builds_including_preserved_initial_attempts':builds,
            'input_full_SHA_seconds':read(ROOT/'reviews/input_freeze.json')['elapsed_seconds'],
            'sample_GT_audit_seconds':read(ROOT/'reviews/gt_sample_audit.json')['elapsed_seconds'],
            'offline_suite_seconds':read(ROOT/'reviews/offline_suite.execution.json')['elapsed_seconds'],
            'formal_suite_seconds':read(ROOT/'reviews/formal_suite.execution.json')['elapsed_seconds'],
            'qualification_regression_seconds':read(ROOT/'reviews/qualification_regression.json')['elapsed_seconds'],
            'pre_resume_successful_teacher_seconds':read(ROOT/'reviews/teacher_deep10m_l2_v1.execution.corrected.json')['elapsed_seconds'],
            'preserved_metadata_only_correction':str(ROOT/'reviews/teacher_deep10m_l2_v1.execution.corrected.json'),
            'nesting':'Do not sum suite + its contained stages, stage + native, or native + formal wall. The resumed offline suite excludes the already successful initial Deep teacher; its separately listed time remains a real cost, with zero scientific replay. Full SHA and sampled GT audit overlapped partly before training, so their elapsed sum is not campaign critical-path time.',
            'unmeasured':['complete historical cold-start cost','exact peak RSS','independent graph/seed variance'],
            'cost_scope_correction':'Execution receipt elapsed starts at launch and is recorded after output checks and hashes. It is a launch-through-verification stage cost, not isolated child wait time.'}
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(out)


if __name__=='__main__':main()

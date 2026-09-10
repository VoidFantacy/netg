#!/usr/bin/env python3
from common import DATASETS, RUN, dump, read

stages={}
for key,path in [('label_process','labels/jobs.json'),('training_process','models/jobs.json'),
                 ('fit_probe_and_cal_process','diagnostics/cal_jobs.json'),('audit_process','diagnostics/audit_jobs.json'),
                 ('validation_process','results/jobs.json')]:
    jobs=read(RUN/path)
    stages[key]={'seconds':sum(x['process_seconds'] for x in jobs),'jobs':jobs}
fit_core={family:sum(read(p)['seconds'] for p in (RUN/'models').glob(f'*/{family}_lambda*/training.json')) for family in ['full','rank8']}
labels=[read(RUN/'labels'/ds/'complete.json') for ds in DATASETS]
diagnostic_calls=sum(read(RUN/'diagnostics'/ds/sp/'results.json')['physical_graph_calls'] for ds in DATASETS for sp in ['fit_probe','cal','audit'])
validation_calls=sum(read(RUN/'results'/ds/'results.json')['physical_graph_calls'] for ds in DATASETS)
costs={'status':'COMPLETE','stages':stages,'preflight_hash_seconds':read(RUN/'inputs/preflight.json')['seconds'],
    'prepare_fit_seconds':sum(read(RUN/'inputs'/ds/'prepared.json')['seconds'] for ds in DATASETS),
    'model_fit_core_seconds':fit_core,'fit_core_scope':'per-model objective optimization and gradient analysis; excludes shared input/SVD setup and export I/O; included within training_process',
    'label_instrumented_seconds':sum(x['seconds'] for x in labels),
    'new_actual_dataset_search_calls':{'labels':sum(x['physical_calls'] for x in labels),
       'label_parity':sum(x['parity_calls'] for x in labels),'fit_cal_audit':diagnostic_calls,'validation_including_warm_count_parity':validation_calls},
    'logical_joint_labels':sum(x['logical_calls'] for x in labels),
    'reused_single_label_dependency':{'fit_query_entry_values_used':20000*(815+821),
        'new_single_label_calls':0,'historical_full_E22_batch_calls':169857792,
        'historical_full_E22_label_seconds':6639.99,
        'scope':'candidate proposal depends on old L128 all-H single labels for this build; direct from-scratch replication would need 32,720,000 such query-entry labels. Historical E22 totals include additional seeds/label-L and are not this method exclusive cost.'},
    'full_from_scratch_offline_seconds':None,
    'unknown_reason':'exact train GT, QGT/prototype, NSG and the necessary single-label subset are reused; their exclusive full rebuild cost was not newly measured',
    'timing_scope':'query QPS comes only from each single-thread independent plain wall; all process totals include other work and are not QPS'}
costs['new_actual_dataset_search_calls']['total']=sum(costs['new_actual_dataset_search_calls'].values())
costs['build_process_seconds']=sum(read(p)['seconds'] for p in (RUN/'bin').glob('*.build.json'))
costs['build_scope']='three standalone compiler invocations; not model/query performance'
dump(RUN/'results/costs.json',costs)
print('COST_LEDGER_COMPLETE',costs['new_actual_dataset_search_calls']['total'])

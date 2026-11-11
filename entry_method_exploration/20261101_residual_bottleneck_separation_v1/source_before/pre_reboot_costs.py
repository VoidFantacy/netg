from common import *
assert (R/'formal_complete.json').exists()
formal=read(R/'formal_complete.json');formal_wall=0.;cal_wall=0.;cal_v1_wall=0.;qual_wall=0.;diag_process=0.
formal_points=cal_points=cal_v1_points=qualification_points=0
for ds in DS:
    for window in ['A','B']:
        c=read(R/'configs'/f'{ds}.{window}.json');native=read(Path(c['output_dir'])/'complete.json')
        formal_points+=native['points']
        formal_wall+=sum(v['wall_seconds'] for p in native['results'] for v in p['rounds'])
        for tag in [window,window+'-full']:
            diag_process+=read(R/'storage/diagnosis'/ds/tag/'complete.json')['native_process_seconds']
    old=read(R/'storage/calibration'/ds/'complete.json');cal_v1_points+=old['points']
    cal_v1_wall+=sum(v['wall_seconds'] for p in old['results'] for v in p['rounds'])
    native=read(R/'storage/calibration_v2'/ds/'complete.json');cal_points+=native['points']
    cal_wall+=sum(v['wall_seconds'] for p in native['results'] for v in p['rounds'])
    for stage in ['runtime_qualification','single_qualification']:
        native=read(R/'storage'/stage/ds/'complete.json');qualification_points+=native['points']
        qual_wall+=sum(v['wall_seconds'] for p in native['results'] for v in p['rounds'])
label_records=read(R/'reviews/labels_training_progress.json')
label_seconds=sum(x['seconds'] for x in label_records if x['stage']=='labels')
training_seconds=sum(x['seconds'] for x in label_records if x['stage']=='train')
build_receipts=[]
for p in (R/'reviews').glob('build*.json'):
    v=read(p)
    if 'argv' in v and 'seconds' in v:build_receipts.append(dict(path=str(p),seconds=v['seconds'],returncode=v['returncode']))
archives=[]
for p in (R/'storage').rglob('packet_archive.json'):
    v=read(p);archives.append(dict(path=str(p),bytes=v['archive_bytes'],original_bytes=v['original_bytes'],seconds=v['seconds']))
result=dict(status='MEASURED_E197_COST_LEDGER',formal_points=formal_points,formal_batches=formal_points*3,
    formal_batch_wall_seconds=formal_wall,calibration_points=cal_points,calibration_batches=cal_points*3,
    calibration_batch_wall_seconds=cal_wall,qualification_matrix_points=qualification_points,
    previous_trace_capture_calibration_v1_points=cal_v1_points,
    previous_trace_capture_calibration_v1_batch_seconds=cal_v1_wall,
    qualification_matrix_batch_wall_seconds=qual_wall,
    actual_single_seed_label_invocations_seconds=label_seconds,
    actual_model_training_invocations_seconds_including_failed_environment_launch=training_seconds,
    public_GT_privileged_candidate_diagnosis_native_process_seconds=diag_process,
    actual_public_model_feature_and_selection_audit_outer_seconds=read(R/'analysis/decision_audit.json')['seconds'],
    fixed_public_pipeline_outer_seconds=formal['outer_process_seconds'],
    native_formal_process_seconds=sum(x['seconds'] for x in formal['records'] if x['stage'].startswith('formal-')),
    native_calibration_v1_process_seconds=sum(x['seconds'] for x in read(R/'reviews/calibration_progress.json')),
    native_calibration_v2_process_seconds=sum(x['seconds'] for x in read(R/'reviews/calibration_v2_progress.json')),
    compilation_attempts=build_receipts,packet_archives=archives,
    extra_full_GT_generation_seconds=0,extra_base_graph_construction_seconds=0,
    offline_training_cost_is_not_current_rejection_criterion=True,
    nesting='Batch wall is contained in each native invocation. Public outer pipeline contains diagnoses, formal invocations, archive checks and administrative SHA. Some compilation overlapped offline labeling; none overlapped calibration/formal performance. Do not add nested stages or claim complete project/human cost.',
    complete_human_and_project_cost=None)
if (R/'reviews/storage_RAM_staging.json').exists():
    result['storage_recovery']=read(R/'reviews/storage_RAM_staging.json')
    result['stopped_formal_attempt_process_seconds']=sum(x['seconds'] for x in formal['records'] if x['stage'].startswith('formal-') and x['returncode']!=0)
    result['completed_formal_process_seconds']=sum(x['seconds'] for x in formal['records'] if x['stage'].startswith('formal-') and x['returncode']==0)
    result['fixed_public_pipeline_outer_seconds_scope']='Last resumed invocation only; completed and stopped native invocations retained in records and native_formal_process_seconds. Not complete calendar duration.'
    result['output_storage_scope']='COCO A normal output files on disk; storage-guarded COCO B attempt retained, then complete B repeated. Subsequent output files on byte-identical RAM staging, outside measured query wall. All frozen methods, models, points and thread conditions unchanged.'
dump(R/'analysis/cost_ledger.json',result)
print(json.dumps({k:v for k,v in result.items() if not isinstance(v,(list,dict))}),flush=True)

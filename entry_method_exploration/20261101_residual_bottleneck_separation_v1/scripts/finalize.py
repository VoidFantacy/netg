from common import *
import re,os,gzip,tarfile
started=time.perf_counter()
formal=read(R/'formal_complete.json');freeze=read(R/'formal_freeze.json')
analysis=read(R/'analysis/analysis_receipt.json');audit=read(R/'analysis/stdlib_audit.json')
decisions=read(R/'analysis/decision_audit.json');cost=read(R/'analysis/cost_ledger.json')
assert formal['points']==freeze['points']==analysis['points']==audit['formal_points']==cost['formal_points']
assert formal['batches']==freeze['batches']==analysis['batches']==audit['formal_batches']==cost['formal_batches']
assert formal['all_28_candidate_bank_diagnoses_complete']
assert decisions['all_actual_timed_seed_and_gate_ID_equal'] and decisions['raw_GT_or_teacher_masks_used'] is False
assert analysis['gate_exact_branch_and_full_model_finite_oracle_bounds']
for x in freeze['files']:assert sha(x['path'])==x['sha256'],x['path']
for x in freeze['large_inherited_inputs']:
    s=Path(x['path']).stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns']
labels=read(R/'labels_freeze.json');bridge=read(R/'reviews/protocol_amendment_bridge.json')
for x in labels['files']:
    if sha(x['path'])!=x['sha256']:
        assert x['path']==bridge['original_path'] and sha(bridge['snapshot'])==x['sha256']
for ds in DS:
    for tag in ['A','B','A-full','B-full']:
        info=read(R/'storage/diagnosis'/ds/tag/'complete.json')
        n=read(R/'configs'/f"{ds}.{tag[0]}.json")['queries']['n']
        assert info['queries']==n and info['query_K_rows']==2*n and info['full_public_main_byte_parity']==2*n
    assert read(R/'storage/models'/ds/'selected.json')['fit_queries']==2048
assert read(R/'analysis/figures/plot_receipt.json')['figures']==3
assert read(R/'reviews/visual_review.json')['status']=='PASS_NATIVE_SCIENTIFIC_FIGURE_VISUAL_REVIEW'
persist=read(R/'reviews/persistent_storage_delivery.json')
assert persist['status']=='PASS_ALL_NEW_EVIDENCE_PERSISTENT_NO_RAM_DEPENDENCY'
assert (R/'storage').resolve()==Path('/root/acsg-e197-storage') and not Path('/root/acsg-e197-storage').is_symlink()
reboot=read(R/'reviews/reboot_recovery_complete.json')
assert reboot['status']=='PASS_11_HASH_RESTORED_2_GIST_NEW_ALL_14_DURABLE'
assert formal['packet_evidence_origins']==dict(original_durable_windows=1,old_timed_packet_SHA_restored_windows=11,new_post_boot_GIST_windows=2)
assert read(R/'reviews/recovery_qualification.json')['payload_files']==416
for x in read(R/'storage/reboot_recovery/plan.json')['original_complete_windows']:
    assert sha(x['original_log'])==x['original_log_sha256'] and sha(x['expected_complete'])==x['expected_sha256']
for x in persist['durable_overflow_files']:
    assert sha(x['durable_path'])==x['sha256']
for x in read(R/'reviews/archive_path_resolution_bridge.json')['archives']:
    assert sha(R/'storage'/x['path'])==x['new_sha256']
    assert sha(R/'storage'/x['snapshot'])==x['snapshot_sha256']
    assert hashlib.sha256(gzip.decompress((R/'storage'/x['snapshot']).read_bytes())).hexdigest()==x['old_sha256']
    assert sha(x['resolved_durable_archive'])==x['payload_archive_sha256']
identities=json.load(gzip.open(persist['all_file_identities'],'rt'))
for x in identities:
    p=R/'storage'/x['path'];assert p.is_file() and p.stat().st_size==x['bytes'] and sha(p)==x['sha256']

def verify_tar_members(archive,records,name_key='member',size_key='bytes',sha_key='sha256'):
    expected={x[name_key]:x for x in records};seen=set()
    process=subprocess.Popen(['zstd','-q','-d','-c',str(Path(archive).resolve())],stdout=subprocess.PIPE)
    with tarfile.open(fileobj=process.stdout,mode='r|') as tar:
        for member in tar:
            payload=tar.extractfile(member).read();ref=expected[member.name]
            assert member.name not in seen
            assert len(payload)==ref[size_key] and hashlib.sha256(payload).hexdigest()==ref[sha_key]
            seen.add(member.name)
    assert process.wait()==0 and seen==set(expected)

metadata_archives=metadata_members=0
for p in (R/'storage').rglob('point_metadata_archive.json'):
    ref=read(p);archive=p.parent/ref['archive'];assert sha(archive)==ref['archive_sha256']
    verify_tar_members(archive,ref['files']);metadata_archives+=1;metadata_members+=len(ref['files'])
stopped=R/'storage/attempts/coco.B.storage_peak/archive_identity.json'
ref=read(stopped);assert sha(stopped.parent/ref['archive'])==ref['archive_sha256']
verify_tar_members(stopped.parent/ref['archive'],ref['files'],name_key='path')

# Verify sealed scientific history. Only mutable root docs may use exact pre-change snapshots.
mutable=['AGENTS.md','LOCAL_CODEX_START.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']
snapshot_roots=[R/'source_before',DESIGN/'source_before',R.parent/'20261101_residual_navigation_cost_controls_v1/source_before']
preserved=[]
for name in ['20261101_residual_navigation_diagnosis_v1','20261101_residual_navigation_cost_controls_v1','20261101_learned_residual_navigation_design_v1']:
    old=R.parent/name;manifest=read(old/'delivery_manifest.json');unchanged=bridged=0
    for x in manifest['files']:
        path=Path(x['path']);path=path if path.is_absolute() else old/path
        if sha(path)==x['sha256']:unchanged+=1;continue
        assert path.is_relative_to(REPO) and str(path.relative_to(REPO)) in mutable,('old science changed',path)
        rel=path.relative_to(REPO)
        assert any((s/rel).exists() and sha(s/rel)==x['sha256'] for s in snapshot_roots),('missing exact root bridge',path)
        bridged+=1
    for x in manifest.get('current_root_files',[]):
        path=REPO/x['path']
        if sha(path)!=x['sha256']:
            rel=path.relative_to(REPO);assert any((s/rel).exists() and sha(s/rel)==x['sha256'] for s in snapshot_roots)
    preserved.append(dict(experiment=name,unchanged_scientific_or_snapshot_files=unchanged,mutable_roots_bridged=bridged,
        original_manifest_sha256=sha(old/'delivery_manifest.json')))
dump(R/'reviews/history_preservation.json',dict(status='PASS_PRIOR_SCIENTIFIC_SEALS_AND_ROOT_BRIDGES',experiments=preserved))

archive_count=0
for p in (R/'storage').rglob('packet_archive.json'):
    entry=read(p);assert sha(entry['archive'])==entry['archive_sha256']
    assert str(entry['archive']).startswith(('/root/acsg-e197-storage/','/data/acsg-e197-durable-overflow/'))
    verify_tar_members(entry['archive'],entry['files'],size_key='payload_bytes',sha_key='payload_sha256')
    assert entry['raw_timed_arrays_byte_exact'] and entry['witness_uncompressed_payload_byte_exact'];archive_count+=1
documents=[R/'README.md',R/'findings_zh.md',R/'report_zh.md',REPO/'summary.md',REPO/'spec.md',REPO/'s-target.md',
           REPO/'s-experiment.md',REPO/'LOCAL_CODEX_START.md',REPO/'experiment_history/197_residual_bottleneck_separation_v1.md']
links=0
for p in documents:
    assert p.exists() and p.stat().st_size>100
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('http://','https://','#')):continue
        target=target.strip('<>').split('#')[0]
        destination=(p.parent/target).resolve()
        assert destination.exists() or destination in [(R/'delivery_validation.json').resolve(),(R/'delivery_manifest.json').resolve()],(p,target)
        links+=1
assert 'E197' in (REPO/'summary.md').read_text()
assert '实施中' not in (REPO/'experiment_history/197_residual_bottleneck_separation_v1.md').read_text()
assert '更正' in (REPO/'s-target.md').read_text() or '瓶颈' in (REPO/'s-target.md').read_text()
assert not list(R.rglob('*.pdf')) and not list((R/'storage').rglob('*.pdf'))
live=[]
for p in Path('/proc').iterdir():
    if not p.name.isdigit() or int(p.name) in [os.getpid(),os.getppid()]:continue
    try:cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
    except OSError:continue
    if any(token in cmd for token in [str(R/'storage/formal_benchmark'),str((R/'storage/formal_benchmark').resolve()),
        str(R/'storage/labels_benchmark'),str(R/'storage/decision_benchmark'),str(R/'scripts/run_public.py'),
        str(R/'scripts/continue_experiment.py'),str(R/'scripts/run_calibration_v2.py'),
        str(R/'storage/recover_packets'),str(R/'scripts/run_reboot_recovery.py'),
        str(R/'scripts/continue_after_reboot.py')]):live.append((p.name,cmd))
assert not live,('unfinished native/pipeline work',live)
validation=dict(status='PASS_E197_FULL_LOCAL_DELIVERY',formal_points=formal['points'],formal_batches=formal['batches'],
    training_single_seed_rows=audit['all_training_label_structural_rows'],actual_model_candidate_decision_rows=decisions['candidate_rows'],
    actual_query_K_L_bank_decisions=decisions['query_K_L_bank_decisions'],public_bank_diagnoses=28,
    prior_scientific_experiments_verified=len(preserved),archive_files_verified=archive_count,
    point_metadata_archives_verified=metadata_archives,point_metadata_members_verified=metadata_members,
    interrupted_storage_attempt_all_bytes_preserved=True,all_new_evidence_durable_no_RAM_dependency=True,
    reboot_original_timing_packet_SHA_restored_windows=11,new_post_boot_GIST_windows=2,
    original_durable_window=1,replayed_work_seed_witness_provenance_disclosed=True,
    local_links_checked=links,full_query_integer_hash_wall_and_selection_audits=True,
    visual_review=True,default_changed=False,new_PDF=False,pending_work=False,seconds=time.perf_counter()-started)
state=dict(status='COMPLETED_BOTTLENECK_SEPARATION_EXPERIMENT_NO_DEFAULT_CHANGE',experiment='E197',
    formal_points=formal['points'],formal_batches=formal['batches'],default_changed=False,new_PDF=False,pending_work=False,
    all_required_numerical_and_document_delivery_checks=True)
dump(R/'state.json',state);dump(R/'delivery_validation.json',validation)
roots=[REPO/name for name in mutable]+[REPO/'experiment_history/197_residual_bottleneck_separation_v1.md']
files=[]
for path in sorted(p for p in R.rglob('*') if p.is_file() and p.name!='delivery_manifest.json'
                   and not p.is_relative_to(R/'storage') and '__pycache__' not in p.parts):
    entry=dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path))
    if path.is_symlink():entry['durable_symlink_target']=str(path.resolve())
    files.append(entry)
for path in sorted(p for p in (R/'storage').resolve().rglob('*') if p.is_file()):
    entry=dict(path=str(R/'storage'/path.relative_to((R/'storage').resolve())),bytes=path.stat().st_size,sha256=sha(path))
    if path.is_symlink():entry['durable_symlink_target']=str(path.resolve())
    files.append(entry)
for path in roots:files.append(dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path)))
dump(R/'delivery_manifest.json',dict(status='SEALED_E197_LOCAL_DELIVERY',files=files,
    default_changed=False,new_PDF=False,pending_work=False))
print(json.dumps(validation),flush=True)

"""E174 identity-only preflight. No vector/GTK value decode or numerical job."""
from pathlib import Path
import datetime, hashlib, json, os, struct, time

REPO = Path('/data/netg/ACSG')
RUN = REPO / 'entry_method_exploration/20261010_m5_residual_regions_v1'
ARC = Path('/root/acsg-e172-storage-v2/campaign')
E173 = REPO / 'entry_method_exploration/20261009_nsg_gt_m5_test_v1'
OLD_PREFIX = '/data/netg/ACSG/entry_method_exploration/20261003_all_methods_experiments_v1'
OUTPUT = RUN / 'reviews/data_preflight.json'

def stat5(path):
    s = Path(path).stat()
    return dict(device=s.st_dev, inode=s.st_ino, size=s.st_size,
                mtime_ns=s.st_mtime_ns, mode=s.st_mode)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def main():
    assert not OUTPUT.exists(), 'Preserve an existing preflight'
    started = time.monotonic()
    errors, records, datasets, roles = [], {}, {}, {}
    large_path = RUN / 'reviews/data_preflight_large_sha.receipt.json'
    large, original = read(large_path), read(E173 / 'data_preflight.json')
    config = read(ARC / 'config.locked.json')
    lock_path = ARC / 'm2/m5_freeze8_storage_v3/all_eight_strong_exports.before_select.locked.json'
    lock = read(lock_path)

    def register(path, expected=None, role=None):
        path, key = Path(path), str(path)
        if key in records:
            if expected and records[key]['sha256'] != expected:
                errors.append('Additional expected SHA mismatch: ' + key)
            return key
        before, tick = stat5(path), time.monotonic()
        digest, after = sha(path), stat5(path)
        records[key] = dict(path=key, bytes=before['size'], sha256=digest,
            expected_sha256=expected, matches_expected_sha256=(digest == expected) if expected else None,
            stat5_before=before, stat5_after=after, stat5_unchanged=before == after,
            hash_seconds=time.monotonic() - tick, hash_cpu_affinity=sorted(os.sched_getaffinity(0)), role=role)
        if expected and digest != expected:
            errors.append('Expected SHA mismatch: ' + key)
        if before != after:
            errors.append('Stat changed during hash: ' + key)
        return key

    register(RUN / 'protocol.md', large['protocol_sha256'], 'prelocked scientific protocol')
    protocol = (RUN / 'protocol.md').read_text()
    pilot = ['GT','M5','M5REG24','M5REG96','M5FIRST96','MFDIRECT','MFREG96','GEODIRECT','GEOREG96']
    confirm = ['GT','M5','M5REG96','MFREG96','GEOREG96']
    assert all(name in protocol for name in pilot + confirm)
    assert '72 pilot点+40确认点=112点' in protocol and '336批' in protocol
    assert '新增拟合、标签教师、模型/表/画像/图构建均0' in protocol
    for item in large['records']:
        item = dict(item)
        historical_stat = original['current_complete_file_records'][item['path']]['stat5_after']
        item['changed_stat_fields_from_E173'] = [k for k in historical_stat if historical_stat[k] != item['stat5_after'][k]]
        item['device_change_closed_by_fresh_full_SHA'] = item['matches_expected_sha256']
        records[item['path']] = item
        assert item['matches_expected_sha256'] and item['stat5_unchanged']
    for path in [large_path, E173/'data_preflight.json', ARC/'config.locked.json', lock_path,
                 ARC/'state.json', REPO/'research_snapshots/20261006_results/report.md',
                 ARC/'m5/compile_postings.py', ARC/'m5/control_config.locked.json',
                 ARC/'m5/geometry_controls_v5.py', Path(__file__)]:
        register(path, role='identity/provenance/program metadata only')
    build = read(E173 / 'src/build_v2.json')
    for path, expected in build['source_sha256'].items():
        register(path, expected, 'original E173 source/scalar object')
    register(E173/'bin/benchmark_v2', build['binary_sha256'], 'original reference ELF')
    register(E173/'src/build_v2.json', role='original reference build receipt')
    for name in ['native.hpp', 'runtime.hpp']:
        register(RUN/'src'/name, build['source_sha256'][str(E173/'src'/name)],
                 'copied original helper; new region code qualifies separately')

    for dataset, dc in config['datasets'].items():
        job = read(E173/'jobs'/f'{dataset}.v2.json')
        dm = read(dc['dataset_manifest'])
        register(dc['dataset_manifest'], original['current_complete_file_records'][dc['dataset_manifest']]['sha256'], 'dataset contract')
        assert dm['metric'] == 'ip'
        assert dm['files'][Path(job['base']).name]['sha256'] == dc['base_expected_sha256'] == records[job['base']]['sha256']
        info = dict(dimension=dc['dimension'], base_n=dc['base_n'], H=dc['H'],
                    default=job['anchor']['name'], base=job['base'], index=job['index'],
                    anchor=job['anchor'], metric='raw_inner_product', normalization=dm['normalization'])
        for path in job['anchor'].values():
            if str(path).startswith('/'):
                register(path, original['current_complete_file_records'][path]['sha256'], 'frozen GT10 model')
        compiler_path = ARC/f'm5/models/{dataset}/compile_manifest.json'
        compiler = read(compiler_path)
        register(compiler_path, role='original TRAIN-only compiler receipt')
        primary = ARC/f'm5/models/{dataset}/residual_joint.bin'
        register(primary, compiler['primary']['sha256'], 'frozen residual_joint')
        for name, item in compiler['controls'].items():
            suffix = 'i32' if name.endswith('global') else 'bin'
            register(ARC/f'm5/models/{dataset}/{name}.{suffix}', item['sha256'], 'TRAIN-only simple control')
        for path, expected in lock['model_sha256'].items():
            if dataset in path:
                register(path.replace(OLD_PREFIX, str(ARC)), expected, 'strong control frozen before first SELECT')
        for name, path in dict(M5=primary,
            missing_frequency=ARC/f'm5/models/{dataset}/missing_frequency.bin',
            fullbase_geometry=ARC/f'm5/control_models/{dataset}/fullbase_geometry.bin').items():
            blob = path.read_bytes()
            header = struct.unpack_from('<8I', blob, 8)
            assert blob[:8] == b'M5POST1\0' and header[:3] == (1, dc['H'], 8)
            assert header[5] == dc['base_n'] and len(blob) == 40 + 45 * header[1] + 8 * header[3]
            info[name] = str(path)
            info[name+'_header'] = dict(version=header[0], H=header[1], b=header[2], hash_n=header[3], pairs=header[4], base_n=header[5])
        for path in [ARC/f'm5/control_models/{dataset}/manifest.json',
                     ARC/f'm5/control_models/{dataset}/geometry_scan/complete.json']:
            register(path, role='historical strong control provenance')
        for path, expected in compiler['input_sha256'].items():
            register(path.replace(OLD_PREFIX, str(ARC)), expected, 'original TRAIN GT/returns/routes SHA only')
        info['primary_TRAIN'] = dict(n=dc['discovery']['n'], queries=dc['discovery']['queries'],
            GT=dc['discovery']['gt'], GT_dtype=dc['discovery']['gt_dtype'],
            K1_Lminus=dc['points'][0]['Lminus'], K100_Lminus=dc['points'][1]['Lminus'],
            cal_read=compiler['cal_read'], confirm_read=compiler['confirm_read'],
            shared_K_table=compiler['shared_K_table'], primary=compiler['primary'])

        role_rows, role_records = {}, {}
        for role in ['fit0','select','fit1','cal','confirm_a','confirm_b']:
            if role in ['fit0','select']:
                entry = dc['discovery' if role == 'fit0' else 'select']
                count, row_path = entry['n'], Path(entry['rows'])
                rr = dict(n=count, queries=entry['queries'], GT=entry['gt'], GT_dtype=entry['gt_dtype'],
                          rows=str(row_path), historical_exposure=True)
                register(row_path, role='historical source-row identity')
            else:
                folder = ARC/'inputs'/dataset/role
                manifest, gt_manifest = read(folder/'manifest.json'), read(folder/'gt_manifest.json')
                count, row_path = manifest['n'], folder/'source_rows.i64'
                assert manifest['status'] == 'PASS_SOURCE_AND_BYTE_DEDUP'
                assert gt_manifest['status'] == 'PASS_EXACT_RAW_IP_GT' and gt_manifest['K'] == 100
                assert manifest['files']['queries.f32']['sha256'] == gt_manifest['query_sha256']
                assert gt_manifest['base_sha256'] == records[job['base']]['sha256']
                register(folder/'manifest.json', role='original registered-byte/source exclusion receipt')
                register(folder/'gt_manifest.json', role='original exact raw-IP GT receipt')
                register(row_path, manifest['files']['source_rows.i64']['sha256'], 'role row identity')
                rr = dict(n=count, dimension=manifest['dimension'], source_candidate_window=manifest['source']['source_rows'],
                    manifest=str(folder/'manifest.json'), GT_manifest=str(folder/'gt_manifest.json'),
                    source=manifest['source'].get('source', manifest['source'].get('url')),
                    byte_exclusion_scope=manifest['scope'], excluded_registered_files=len(manifest['excluded_files']),
                    selection=manifest['selection'], queries=str(folder/'queries.f32'),
                    GT=str(folder/'gt.i32'), GT_dtype='<i4', GT_width=100, rows=str(row_path))
                if role.startswith('confirm'):
                    register(folder/'queries.f32', manifest['files']['queries.f32']['sha256'], 'current query bytes only')
                    register(folder/'gt.i32', gt_manifest['GT_sha256'], 'current GT bytes only')
                    register(folder/'gt_ip.f32', gt_manifest['GT_ip_sha256'], 'saved GT score bytes only')
                    assert records[str(folder/'queries.f32')]['bytes'] == count * dc['dimension'] * 4
                    assert records[str(folder/'gt.i32')]['bytes'] == count * 100 * 4
                    rr['quality_decoded_this_preflight'] = False
                    rr['original_model_fit_or_compile_used_role'] = False
                    rr['prior_exposure_scope'] = 'No original confirmation execution reported in inspected E172 state/final report; no exhaustive unregistered-use or semantic/IID claim'
                    rr['new_use'] = 'fixed pilot, development after feedback opens' if role == 'confirm_a' else 'frozen confirmation; quality opens after all role-native jobs complete'
                else:
                    rr['prior_exposure'] = 'TRAIN/constructor role, not fresh validation' if role == 'fit1' else 'Historical C1 full32768 both datasets; M5 Web K1 first4096 all16 controls'
            raw = row_path.read_bytes()[:count * 8]
            values = [v[0] for v in struct.iter_unpack('<q', raw)]
            assert len(values) == count == len(set(values))
            role_rows[role] = set(values)
            rr.update(source_row_min=min(values), source_row_max=max(values), source_row_unique_count=count)
            role_records[role] = rr
        overlap = [dict(role_a=x, role_b=y, overlap_count=len(role_rows[x]&role_rows[y]))
                   for i,x in enumerate(role_rows) for y in list(role_rows)[i+1:]]
        assert all(item['overlap_count'] == 0 for item in overlap)
        roles[dataset] = dict(roles=role_records, pairwise_source_row_overlaps=overlap,
                             all_six_roles_source_row_disjoint=True,
                             byte_disjoint_scope='Original registered-byte exclusion manifests; no new vector-set or semantic/IID calculation')
        datasets[dataset] = info

    for path, item in records.items():
        item['stat5_after_complete_preflight'] = stat5(path)
        item['stat5_unchanged_through_complete_preflight'] = item['stat5_before'] == item['stat5_after_complete_preflight']
        if not item['stat5_unchanged_through_complete_preflight']:
            errors.append('Stat changed at preflight end: ' + path)
    assert sha(RUN/'protocol.md') == large['protocol_sha256']
    report = dict(schema='E174_DATA_PREFLIGHT_BYTES_AND_ROLES_V1', status='PASS' if not errors else 'HOLD', errors=errors,
        scope='Input/program/source byte identities, original provenance and role exclusions only; new region code/ELF/merge qualifies separately',
        completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), protocol=str(RUN/'protocol.md'),
        protocol_sha256=large['protocol_sha256'],
        prelock=dict(pilot_methods=pilot, confirmation_methods=confirm, pilot_points=72, confirmation_points=40,
                     total_points=112, formal_batches=336, repeats=3, new_fit_training=0,
                     new_model_table_profile_graph_build=0, new_teacher_labels_or_GT=0),
        current_identity=dict(large_receipt=str(large_path), fresh_large_SHA_all_match_expected=True,
            four_large_payload_bytes=sum(x['bytes'] for x in large['records']), hash_cpu_affinity=[14],
            hash_actual_threads_observed=1, hash_observation_pid=18245, large_hash_seconds=large['elapsed_seconds'],
            metadata_small_hash_seconds=time.monotonic()-started, no_concurrent_native_timing=True,
            device_change_closed='Original66309 -> current66305; fresh content SHA equals original; inode/bytes/mtime/mode unchanged'),
        datasets=datasets, roles=roles, registered_input_files=records,
        source_model_supervision=dict(compiler=str(ARC/'m5/compile_postings.py'), source_lines='11-24,26-44,66-98',
            TRAIN='Original discovery/FIT0 20K, original GT1/GT100 and original low-L main returns, same three real routed labels',
            residual='missing1={GT1} minus R1; missing100=GT100 minus R100; target weight100 for missing1 plus1 for missing100,101 if both',
            incidence='Each query-target token linked to each distinct routed label slot; real target IDs from original TRAIN residual support',
            residual_joint='Exact integer marginal covered-token greedy, row capacity8, global greedy arrival order, shared K table',
            new_supervision='No compiler/fit/label/table/profile/graph generation executed',
            limit='Fixed-ID TRAIN objective is not proof of conditional region transfer or test Recall/QPS'),
        strong_control_scope=dict(missing_frequency=dict(source=str(ARC/'m5/compile_postings.py')+':40',
            description='Same original residual tokens/routes/100:1 weights; independent each-row top8 full weighted frequency, real-ID tie; no joint diminishing token marginal',
            scope='TRAIN-only supervised simpler-frequency control'),
            fullbase_geometry=dict(config=str(ARC/'m5/control_config.locked.json'), original_frozen_lock=str(lock_path),
            description='Each original raw router profile W scans exhaustive original frozen base scalar raw-IP top8, real-ID tie; support may extend outside residual U/teacher ID union',
            current_role_GT_or_query_used=False,
            limit='Inherits already learned GT10 profile W; not globally unsupervised; source-of-candidate control does not prove basin independence or bridge efficacy')),
        administrative_access=dict(query_GT_values_decoded=False, quality_results_opened=False,
            access='SHA bytes; only source_rows.i64 values decoded for unique/range/intersection checks',
            GT_format='Original confirmation gt.i32,100 ranks; no gt.i64 conversion',
            public_test_used_for_new_tuning=False, semantic_IID_or_globally_unexposed_claim=False),
        limits=['Byte exclusion covers registered sources only; source-row disjointness is not semantic independence',
                'Two confirmation windows share public train/learn source; role names do not establish all-project non-exposure',
                'Input PASS does not qualify new region runtime/final ELF/wholewall/oracle',
                'New region.hpp and benchmark.cpp have separate upcoming independent source review'],
        producer=str(Path(__file__)))
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status=report['status'], registered_files=len(records), path=str(OUTPUT),
        sha256=sha(OUTPUT), large_seconds=large['elapsed_seconds'], small_seconds=report['current_identity']['metadata_small_hash_seconds'])))
    assert not errors, errors

if __name__ == '__main__':
    main()

"""Read-only evidence checks, followed by sealing this experiment's own outputs."""
import csv, datetime, gzip, hashlib, json, os, subprocess, time, struct
from packet_archive import read_bytes, decode, STORAGE
from pathlib import Path

R = Path(__file__).resolve().parents[1]
REPO = R.parents[1]
DS = ['deep10m_l2_v1', 'sift10m_bigann_l2_v1', 'gist1m_l2_v1',
      'coco', 'flickr30k', 'webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']

def read(p):
    return json.loads(Path(p).read_text())

def sha(p, compressed=False):
    h = hashlib.sha256()
    with (gzip.open(p, 'rb') if compressed else Path(p).open('rb')) as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()

def verify_binding(path):
    v = read(path)
    for x in v['files']:
        p = Path(x['path'])
        assert p.is_file() and sha(p) == x['sha256'], (path, str(p))
        if 'bytes' in x:
            assert p.stat().st_size == x['bytes'], str(p)
    return len(v['files'])

def own_files(root):
    """Explicit roots; never traverse an experiment's storage symlink twice."""
    for directory, subdirs, names in os.walk(root, followlinks=False):
        subdirs[:] = [x for x in subdirs if x != '__pycache__' and
                      not (Path(directory)/x).is_symlink()]
        for name in names:
            p = Path(directory)/name
            if not p.is_symlink():
                yield p

def main():
    t = time.perf_counter()
    assert not (R/'delivery_manifest.json').exists()
    primary, dense, report = [read(R/x) for x in
                              ['primary_complete.json', 'dense_complete.json', 'reviews/report_build.json']]
    assert primary['points'] == 448 and primary['batches'] == 1344
    assert not report['no_PDF'] and not report['default_changed']
    authorization=read(R/'delivery_authorization_update.json')
    assert authorization['user_request']=='这个弄完做个pdf吧，我明天看'
    pdf_build=read(R/'reviews/pdf_build.json')
    assert read(R/'reviews/pdf_validation.json')['status']=='PASS_E191_ALL_PAGE_PDF_AND_ATTACHMENTS'
    assert read(R/'reviews/pdf_visual_review.json')['status'].startswith('PASS')
    assert read(R/'reviews/preseal_checks.json')['status'].startswith('PASS')
    assert sha(Path(pdf_build['path']))==pdf_build['pdf_sha256']
    assert sha(Path(pdf_build['source_script']))==pdf_build['source_sha256']
    assert read(R/'reviews/all_method_comparison.json')['status'].startswith('PASS')
    bindings = {x: verify_binding(R/x) for x in
                ['freeze.json', 'postprocessing_binding.json', 'postprocessing_amendment.json', 'postprocessing_extra_binding.json', 'authorized_pdf_binding.json', 'authorized_pdf_extension_binding.json', 'all_method_report_binding.json', 'storage_preflight_binding.json', 'storage_archive_binding.json', 'dense_freeze.json']}
    for x in read(R/'freeze.json')['large_assets']:
        s = Path(x['path']).stat()
        assert (s.st_size, s.st_mtime_ns, s.st_ino) == (x['bytes'], x['mtime_ns'], x['inode'])
    for x in ['qualification_audit.json', 'legacy_scoring_audit.json', 'posthoc_scoring_audit.json']:
        assert read(R/'reviews'/x)['status'].startswith('PASS'), x
    totals = dict(primary_points=0, primary_batches=0, dense_points=0, dense_batches=0)
    thread_receipts, archives = [], []
    for stage, dataset_list, folder, receipt_prefix, audit_prefix in [
        ('primary', DS, 'results', 'formal', 'results_audit'),
        ('dense', dense['datasets'], 'dense_controls', 'dense', 'dense_results_audit')]:
        for ds in dataset_list:
            p = R/'storage'/folder/ds
            done, audit = read(p/'complete.json'), read(R/f'reviews/{audit_prefix}_{ds}.json')
            receipt = read(R/f'reviews/{receipt_prefix}_{ds}.receipt.json')
            assert receipt['returncode'] == 0 and receipt['max_observed_threads'] == 1
            assert audit['status'].startswith('PASS') and audit['all_actual_packet_hashes_recomputed']
            assert done['points'] == audit['points'] and done['batches'] == audit['batches']
            if stage == 'primary':
                assert done['points'] == 64 and done['batches'] == 192
            totals[stage+'_points'] += done['points']
            totals[stage+'_batches'] += done['batches']
            thread_receipts.append(dict(receipt, stage=stage))
            for point in done['results']:
                d = Path(point['result_dir'])
                packet=hashlib.sha256(struct.pack('<QQ',done['n'],point['K']))
                for name in ['ids.i32', 'distances.f32', 'entry_ids.i32', 'profile_distances.f32']:
                    packet.update(read_bytes(d/'raw'/name))
                packet.update(bytes(done['n']*16))
                assert all(x['packet_sha256']==packet.hexdigest() for x in point['rounds'])
            archived=read(p/'raw_packet_archive.json')
            assert archived['status']=='PASS_VERIFIED_LOSSLESS_TIMED_PACKET_ARCHIVE'
            assert archived['source_audit_sha256']==sha(R/f'reviews/{audit_prefix}_{ds}.json')
            decode(p)
            archive = read(p/'trace_archive.json')
            assert archive['status'].startswith('PASS')
            for x in archive['files']:
                z = Path(x['gzip_path'])
                assert not Path(x['original_path']).exists()
                assert z.stat().st_size == x['gzip_bytes'] and sha(z) == x['gzip_sha256']
                assert sha(z, compressed=True) == x['uncompressed_sha256']
            archives.append(dict(stage=stage, dataset=ds, files=len(archive['files'])))
    assert totals == {k: report[k] for k in totals}, (totals, report)
    old = R.parent/'20261028_coco_fixed_candidate_scoring_v1'
    old_seal = read(old/'delivery_manifest.json')
    for x in old_seal['files']:
        p = Path(x['path'])
        assert sha(p if p.is_absolute() else old/p) == x['sha256']
    required_docs = ['summary.md', 'spec.md', 's-target.md', 's-experiment.md',
                     'LOCAL_CODEX_START.md', 'experiment_history/README.md',
                     'experiment_history/191_seven_dataset_scoring_v1.md']
    for name in required_docs:
        assert '191' in (REPO/name).read_text(), name
    assert (R/'source_before/summary.md').is_file()
    diff = subprocess.run(['git', 'diff', '--check', '--', *required_docs, 'AGENTS.md'],
                          cwd=REPO, text=True, capture_output=True)
    (R/'reviews/document_diff_check.txt').write_text(diff.stdout + diff.stderr)
    assert diff.returncode == 0, diff.stdout + diff.stderr
    owned = list(own_files(R)) + list(own_files((R/'storage').resolve()))
    assert {p.resolve() for p in owned if p.suffix.lower()=='.pdf'}=={Path(pdf_build['path']).resolve()}
    state = dict(status='COMPLETED_NO_DEFAULT_CHANGE', **totals,
                 total_points=totals['primary_points']+totals['dense_points'],
                 total_batches=totals['primary_batches']+totals['dense_batches'],
                 datasets=DS, retained_exploratory_points=report['retained_exploratory_points'],
                 retained=report['retained'], no_PDF=False, PDF_authorized=True, default_changed=False,
                 remaining_required_work=False, PDF=pdf_build['path'], PDF_pages=pdf_build['pages'], timed_packet_bytes_preserved=True, packet_storage='POSIX tar + zstd solid archive; restore with packet_archive.py',
                 completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (R/'state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n')
    validation = dict(status='PASS_E191_COMPLETE_DELIVERY_VALIDATION', **totals,
                      verified_binding_files=bindings, timing_receipts=thread_receipts,
                      trace_archives=archives, old_E190_seal_files_verified=len(old_seal['files']),
                      root_documents=required_docs, no_PDF=False, PDF_authorized=True,
                      seconds_before_manifest=time.perf_counter()-t)
    (R/'delivery_validation.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2)+'\n')
    exclude = {R/'delivery_manifest.json'}
    owned = list(own_files(R)) + list(own_files((R/'storage').resolve()))
    owned += [REPO/x for x in required_docs] + [REPO/'AGENTS.md']
    files = [dict(path=str(p.resolve()), bytes=p.stat().st_size, sha256=sha(p))
             for p in sorted(set(owned)-exclude)]
    seal = dict(status='SEALED_E191_COMPLETE_DELIVERY', files=files,
                total_bytes=sum(x['bytes'] for x in files), **totals,
                external_inherited_assets='freeze.json: read-only identity bindings; not copied or rewritten',
                historical_E190_seal_verified=True, no_PDF=False, PDF_authorized=True,
                seconds=time.perf_counter()-t)
    (R/'delivery_manifest.json').write_text(json.dumps(seal, indent=2)+'\n')
    print(json.dumps(dict(status=seal['status'], files=len(files), **totals,
                          retained_exploratory_points=report['retained_exploratory_points'],
                          seconds=seal['seconds'])), flush=True)

if __name__ == '__main__':
    main()

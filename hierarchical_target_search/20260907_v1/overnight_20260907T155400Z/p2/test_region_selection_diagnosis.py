#!/usr/bin/env python3
"""Tiny synthetic tests only; never access project datasets or existing results."""
import copy
import argparse
import hashlib
import json
from pathlib import Path
from unittest import mock

import numpy as np
import diagnose_region_selection as d


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'selection_diagnosis_synthetic_tests')
    output = parser.parse_args().output.resolve()
    output.mkdir(exist_ok=False)
    analysis = {'status': 'COMPLETE', 'datasets': []}
    for name in d.DATASETS:
        analysis['datasets'].append({'dataset': name, 'audit_status': 'PASS', 'fixed_comparisons': [
            {'contrast': 'oracle_protection', 'L': l, 'candidate': 'oracle_probability',
             'reference': 'oracle_unified', 'paired_query_bootstrap95_pp': [.1, .3]} for l in d.LS]})
    d.positive_oracle_gate(analysis)
    rejected = []
    for change in ('incomplete', 'zero_lower', 'negative_lower', 'missing_L', 'missing_dataset', 'wrong_contrast'):
        x = copy.deepcopy(analysis)
        if change == 'incomplete': x['status'] = 'INCOMPLETE'
        elif change == 'zero_lower': x['datasets'][0]['fixed_comparisons'][0]['paired_query_bootstrap95_pp'][0] = 0
        elif change == 'negative_lower': x['datasets'][1]['fixed_comparisons'][1]['paired_query_bootstrap95_pp'][0] = -.1
        elif change == 'missing_L': x['datasets'][0]['fixed_comparisons'].pop()
        elif change == 'missing_dataset': x['datasets'].pop()
        else: x['datasets'][0]['fixed_comparisons'][0]['candidate'] = 'geom_probability'
        try: d.positive_oracle_gate(x)
        except ValueError: rejected.append(change)
        else: raise AssertionError('invalid oracle precondition accepted: ' + change)
    gt = np.asarray([[0,0,0,1,1,2,2,3,4,5]], dtype=np.int16)
    metrics = d.selection_metrics(gt, np.asarray([[2,3,4,5]]), np.asarray([[0,1,2,3]]),
                                  np.asarray([[3/8,2/8,2/8,1/8]]))
    assert metrics['geometry_absolute_gt10_mass'][0] == .5
    assert metrics['oracle_absolute_gt10_mass'][0] == .8
    assert metrics['gt10_distinct_regions'][0] == 6
    assert metrics['top4_overlap_count'][0] == 2
    assert metrics['intersection_absolute_gt10_mass'][0] == .3
    assert metrics['intersection_fraction_of_oracle_top4_mass'][0] == 3/8
    # Same normalized oracle weights can encode different absolute GT masses.
    both = d.selection_metrics(np.asarray([[0,0,1,1,2,2,3,3,4,5], list(range(10))]),
                               np.asarray([[0,1,2,3], [0,1,2,3]]),
                               np.asarray([[0,1,2,3], [0,1,2,3]]), np.full((2,4), .25))
    assert both['oracle_absolute_gt10_mass'].tolist() == [.8,.4]
    assert d.bin_index(np.asarray([0,.249999,.25,.499999,.5,.749999,.75,1])).tolist() == [0,0,1,1,2,2,3,3]
    # Artificial parent GT12 rows, pilot4 rows. Track physical read ranges.
    rows = np.empty((12,101), dtype='<i4'); rows[:,0] = 100
    rows[:,1:] = np.arange(1200,dtype='<i4').reshape(12,100)
    gt_path = output / 'synthetic_GT_parent.ivecs'; rows.tofile(gt_path)
    ds = {'files': {'drl_train_gt_path': {'path': str(gt_path), 'header': {'bytes': rows.nbytes}, 'sha256': 'SYNTHETIC_PARENT_NOT_REHASHED'}},
          'pilot': {'gt_values_sha256': hashlib.sha256(np.ascontiguousarray(rows[:4,1:]).tobytes()).hexdigest()},
          'graph': {'header': {'n': 2000}}}
    reads = []; original_open = Path.open
    class PrefixReader:
        def __init__(self, f): self.f = f
        def __enter__(self): return self
        def __exit__(self, *args): self.f.close()
        def read(self, n=-1):
            begin = self.f.tell(); value = self.f.read(n); reads.append([begin, begin+len(value)]); return value
        def seek(self, *args): return self.f.seek(*args)
    def track(path, *args, **kwargs):
        f = original_open(path, *args, **kwargs)
        return PrefixReader(f) if path == gt_path else f
    with mock.patch.object(Path, 'open', track):
        selected, evidence = d.read_pilot_gt(ds, nq=4, parent_rows=12)
    assert np.array_equal(selected, rows[:4,1:11])
    assert max(end for begin,end in reads) <= 4*101*4
    # A wrong P0 binding must be rejected before the first GT read.
    model_path, count_path = output/'fake_model.json', output/'fake_count.json'
    model = {'status':'COMPLETE','dataset':d.DATASETS[0],'stage':'P2','heldout_accessed':False,
             'fit_range':[10000,30000],'pilot_labels_used_for_fit':False,'input_audit_sha256':'wrong'}
    count = {'status':'COMPLETE','dataset':d.DATASETS[0],'stage':'P2','split':'pilot',
             'source_query_type':'drl_train','source_query_range':[0,10000],'num_queries':10000,
             'measurement':'count','top_k':10,'rounds':1,'heldout_accessed':False,
             'model_manifest':model,'model_file':str(model_path)}
    d.write_new(model_path,model);d.write_new(count_path,count)
    source = {'evidence':{key:{'path':str(path),'sha256':d.sha(path)} for key,path in [('count',count_path),('model',model_path)]}}
    with mock.patch.object(d,'read_pilot_gt') as forbidden:
        try: d.verify_and_diagnose(d.DATASETS[0],(count_path,model_path),source,{},output,'expected_P0_hash')
        except ValueError as e: assert 'different P0 audit' in str(e)
        else: raise AssertionError('wrong P0 audit binding accepted')
        forbidden.assert_not_called()
    result = {'status':'PASS_SYNTHETIC_SELECTION_DIAGNOSIS_TESTS', 'invalid_gate_cases_rejected': rejected,
              'absolute_mass_and_oracle_conditional_weight_distinguished':True,
              'top4_ID_tie_rule_and_fixed_bin_boundaries':True, 'pilot_GT_prefix_only_physical_reads': reads,
              'full_parent_or_fit_GT_read':False, 'real_dataset_accessed':False,
              'wrong_P0_binding_rejected_before_GT_read':True,
              'script_sha256':d.sha(Path(d.__file__))}
    d.write_new(output/'result.json', result); print(json.dumps(result))


if __name__ == '__main__': main()

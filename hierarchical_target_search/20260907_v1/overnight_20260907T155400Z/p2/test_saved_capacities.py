#!/usr/bin/env python3
"""Small synthetic-only checks for the saved-capacity diagnosis adapter."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path
import random
import subprocess
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('diagnose_saved_capacities.py')
spec = importlib.util.spec_from_file_location('capacity_diagnosis', SCRIPT)
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


def must_reject(call, substring):
    try:
        call()
    except ValueError as e:
        assert substring in str(e), (substring, str(e))
    else:
        raise AssertionError('Expected rejection: ' + substring)


def cpp_allocator_check(out, cxx):
    source = out/'allocator_reference.cpp'
    source.write_text('''#include "ACSG/RegionalSearch.h"
#include <iostream>
int main() {
    int l, region_count, regional, uniform, active;
    while (std::cin >> l >> region_count >> regional >> uniform >> active) {
        acsg::regional::Route route; route.active = active;
        for (int i=0; i<active; ++i) std::cin >> route.regions[i] >> route.weights[i];
        std::array<int,5> caps{};
        const int nq=acsg::regional::allocate(route,l,region_count,regional,uniform,caps);
        std::cout << nq;
        for(int i=0; i<nq; ++i) std::cout << " " << caps[i];
        std::cout << "\\n";
    }
}
''')
    binary = out/'allocator_reference'
    command = [cxx, '-O2', '-std=c++17', '-I', str(d.SOURCE_DEFAULT.parent.parent), str(source), '-o', str(binary)]
    build = subprocess.run(command, capture_output=True, text=True)
    (out/'build.stdout').write_text(build.stdout); (out/'build.stderr').write_text(build.stderr)
    assert build.returncode == 0, build.stderr
    cases = []
    fixed_weights = [[.25]*4, [.5,.25,.125,.125], [1,0,0,0], [.25000001,.24999999,.25,.25],
                     [math.nextafter(.25, 1), math.nextafter(.25, 0), .25, .25],
                     [1e-200, 1, 1e-100, 0]]
    for l in [64,65,66,67,128,129]:
        for weights in fixed_weights:
            for uniform in (False, True):
                cases.append(([9,2,7,4], weights, l, 64, True, uniform))
    rng = random.Random(2026090711)
    for _ in range(1000):
        active = rng.randrange(1,5)
        regions = rng.sample(range(64), active)
        weights = [rng.random()**rng.randrange(1,9) for _ in regions]
        cases.append((regions, weights, rng.choice([32,64,65,127,128]), 64, True, bool(rng.randrange(2))))
    cases.extend([([], [], 64, 64, True, False), ([0], [0], 64, 1, True, False),
                  ([2,3], [0,0], 64, 64, False, False)])
    lines = []
    for regions, weights, l, rc, regional, uniform in cases:
        parts = [str(l), str(rc), str(int(regional)), str(int(uniform)), str(len(regions))]
        for region, weight in zip(regions, weights):
            parts.extend([str(region), format(weight, '.17g')])
        lines.append(' '.join(parts))
    run = subprocess.run([str(binary)], input='\n'.join(lines)+'\n', capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    outputs = run.stdout.splitlines(); assert len(outputs) == len(cases)
    for case, text in zip(cases, outputs):
        regions, weights, l, rc, regional, uniform = case
        caps = d.allocate(regions, weights, l, rc, regional, uniform)
        values = list(map(int, text.split()))
        assert values == [len(caps)] + caps, (case, values, caps)
    (out/'cpp_comparison.json').write_text(json.dumps({'status':'PASS', 'cases':len(cases),
        'command':command, 'source_sha256':d.sha(d.SOURCE_DEFAULT),
        'binary_sha256':d.sha(binary), 'case_generation':'Fixed roundoff/tie/zero cases plus seed2026090711 random cases'},indent=2)+'\n')
    return len(cases)


def row(q, weights, oracle=False):
    r = {'query_id':q, 'entry_ids':[1,2,3,4], 'fast_anchor_id':1, 'shared_seed':0,
         'actual_entry_count':5, 'regions':[9,2,7,4] if not oracle else [8,1,6,3],
         'weights':weights, 'result_ids':list(range(10)), 'recall':.5,
         'routing_ndc':5, 'graph_ndc':20, 'total_ndc':25, 'routing_mac':10,
         'graph_mac':40, 'total_mac':50, 'expanded':15, 'rejected':3, 'evicted_unexpanded':2}
    return r


def fixture(out, dataset):
    model_path = out/'model.json'; count_path = out/'count.json'
    model = {'status':'COMPLETE', 'stage':'P2', 'dataset':dataset, 'region_count':64,
             'active_regions':4, 'fit_range':[10000,30000], 'pilot_labels_used_for_fit':False,
             'heldout_accessed':False, 'labels_file':'/FORBIDDEN_REAL_DATA_ACCESS',
             'graph_file':'/FORBIDDEN_REAL_DATA_ACCESS', 'GT_file':'/FORBIDDEN_REAL_DATA_ACCESS'}
    count = {'status':'COMPLETE', 'stage':'P2', 'dataset':dataset, 'source_query_range':[0,4],
             'num_queries':4, 'split':'pilot', 'source_query_type':'drl_train', 'measurement':'count',
             'top_k':10, 'rounds':1, 'heldout_accessed':False, 'model_manifest':model,
             'model_file':str(model_path.resolve()), 'base_nodes':100, 'dim':2, 'results':[]}
    weights = [[.25]*4, [.5,.25,.125,.125], [.25000001,.24999999,.25,.25], [1,0,0,0]]
    for l in d.LS:
        for method in d.METHODS:
            rows = [row(q, w, method.startswith('oracle')) for q,w in enumerate(weights)]
            if method == 'geom_probability':
                for q in (1,3):
                    rows[q]['result_ids'][0] = 20
                    rows[q]['recall'] = .6
                    rows[q]['graph_ndc'] += 1; rows[q]['total_ndc'] += 1
                    rows[q]['graph_mac'] += 2; rows[q]['total_mac'] += 2
                    rows[q]['expanded'] += 1
            count['results'].append({'method':method, 'search_L':l, 'round':0, 'top_k':10, 'per_query':rows})
    d.write_new(model_path, model); d.write_new(count_path, count)
    analysis_ds = {'dataset':dataset, 'audit_status':'PASS', 'evidence':{
        'count':{'path':str(count_path.resolve()),'sha256':d.sha(count_path)},
        'model':{'path':str(model_path.resolve()),'sha256':d.sha(model_path)}},
        'fixed_comparisons':[{'contrast':'oracle_protection','L':l,'candidate':'oracle_probability',
                             'reference':'oracle_unified','paired_query_bootstrap95_pp':[.1,.2]} for l in d.LS]}
    return count, model, analysis_ds, count_path, model_path


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cxx',default='c++'); a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    assert d.sha(d.SOURCE_DEFAULT) == d.SOURCE_SHA256
    cpp_n = cpp_allocator_check(a.output,a.cxx)
    assert d.allocate([9,2,7,4],[.25]*4,64) == [16,12,12,12,12]
    assert d.allocate([9,2,7,4],[.25]*4,65) == [16,12,13,12,12]
    assert d.allocate([9,2,7,4],[.5,.25,.125,.125],64) == [16,20,12,8,8]
    assert d.allocate([9,2,7,4],[.25000001,.24999999,.25,.25],64) == [16,12,12,12,12]
    for regions, weights, l in [([1,1],[.5,.5],64),([1],[float('nan')],64),([1],[-1],64),
                                 ([1],[0],64),([1,2,3,4],[.25]*4,10)]:
        must_reject(lambda:d.allocate(regions,weights,l),'')
    uniform = d.concentration([1,1,1,1]); peak=d.concentration([1,0,0,0])
    assert uniform['entropy_bits']==2 and uniform['normalized_entropy']==1 and uniform['max_probability']==.25
    assert peak['entropy_bits']==0 and peak['max_probability']==1
    left = row(0,[.25]*4); right=copy.deepcopy(left)
    assert all(d.equality_checks(left,right,True).values())
    rejected_fields=[]
    for field in d.EXACT_FIELDS:
        changed=copy.deepcopy(right)
        if field=='result_ids': changed[field][0]=99
        else: changed[field]+= .1 if field=='recall' else 1
        must_reject(lambda:d.equality_checks(left,changed,True),field)
        assert not d.equality_checks(left,changed,False)[field]
        rejected_fields.append(field)
    changed=copy.deepcopy(right); changed['regions'].reverse()
    must_reject(lambda:d.equality_checks(left,changed,True),'route')
    ds = d.DATASETS[0]
    fixture_dir=a.output/'fixture'; fixture_dir.mkdir()
    count,model,ad,cp,mp=fixture(fixture_dir,ds)
    diagnosis_dir=a.output/'synthetic_diagnosis'; diagnosis_dir.mkdir()
    real_open=Path.open; allowed_reads={cp.resolve(),mp.resolve()}
    accessed=[]
    def restricted_open(self,mode='r',*args,**kwargs):
        if mode.startswith('r'):
            assert self.resolve() in allowed_reads or self.resolve().is_relative_to(diagnosis_dir.resolve()), str(self)
            accessed.append(str(self.resolve()))
        return real_open(self,mode,*args,**kwargs)
    with patch.object(d,'NQ',4),patch.object(Path,'open',restricted_open):
        result=d.verify_and_diagnose(ds,[cp,mp],ad,diagnosis_dir)
    for l in result['by_L']:
        assert l['identical_integer_capacities_count']==2
        assert l['identical_integer_capacities_fraction']==.5
        assert l['equal_capacity_mismatches']==0
        assert l['same_vs_different_capacity_descriptive_strata'][0]['mean_probability_minus_uniform_graph_ndc']==0
        assert l['same_vs_different_capacity_descriptive_strata'][1]['mean_probability_minus_uniform_graph_ndc']==1
    bad=copy.deepcopy(ad); bad['evidence']['count']['sha256']='0'*64
    must_reject(lambda:d.verify_and_diagnose(ds,[cp,mp],bad,diagnosis_dir),'differs from completed main analysis')
    analysis={'status':'COMPLETE','datasets':[ad,copy.deepcopy(ad)]}
    analysis['datasets'][1]['dataset']=d.DATASETS[1]
    d.positive_oracle_gate(analysis)
    for variation in ['incomplete','zero','negative','wrong_method','missing_L']:
        bad=copy.deepcopy(analysis)
        if variation=='incomplete': bad['status']='INCOMPLETE'
        elif variation=='zero': bad['datasets'][0]['fixed_comparisons'][0]['paired_query_bootstrap95_pp'][0]=0
        elif variation=='negative': bad['datasets'][0]['fixed_comparisons'][0]['paired_query_bootstrap95_pp'][0]=-.1
        elif variation=='wrong_method': bad['datasets'][0]['fixed_comparisons'][0]['candidate']='geom_probability'
        else: bad['datasets'][0]['fixed_comparisons'].pop()
        must_reject(lambda:d.positive_oracle_gate(bad),'')
    report={'status':'PASS','script_sha256':d.sha(SCRIPT),'test_script_sha256':d.sha(__file__),
            'cpp_exact_comparison_cases':cpp_n,'equal_capacity_rejected_mismatch_fields':rejected_fields,
            'synthetic_paired_queries':4,'synthetic_Ls':list(d.LS),'source_sha256':d.SOURCE_SHA256,
            'read_boundary':'Only synthetic model/count and newly emitted CSV opened by diagnosis',
            'synthetic_read_paths':sorted(set(accessed)),
            'checks':['allocator tie ID and roundoff saturation','capacity conservation','C++ parity',
                      'same-capacity equality required for every saved exact field','different-capacity changes permitted',
                      'route change rejected','model/count SHA binding','positive main-analysis gate',
                      'conditional entropy/concentration known cases','synthetic end-to-end CSV and strata'],
            'real_data_diagnosis_run':False}
    d.write_new(a.output/'result.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()

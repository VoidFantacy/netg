#!/usr/bin/env python3
"""Small generated-label/manifest fixtures only; never read a real partition."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

SCRIPT = Path(__file__).with_name('analyze_structure.py')
spec = importlib.util.spec_from_file_location('structure_analysis', SCRIPT)
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
N, Q = 4096, 32
DATASET = next(iter(d.DATASET_N))
HASH = 'a'*64


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as f:
        json.dump(value, f, indent=2); f.write('\n')


def label_record(path, labels):
    path.parent.mkdir(parents=True, exist_ok=True)
    labels.astype('<u2').tofile(path)
    return {'path':str(path.resolve()),'sha256':d.sha(path),'dtype':'little-endian uint16',
            'header':False,'rows':len(labels),'bytes':len(labels)*2}


def objective(C=8192, S=256):
    M = 16384
    return {'M_original_directed_valid_nonself_slots':M,'C_leaf_directed_crossing_slots':C,
            'S_fit_distinct_leaf_minus_one':S,'Q':Q,'leaf_cut_fraction':C/M,
            'fit_leaf_fragmentation_normalized':S/(9*Q),'mean_fit_distinct_leaf_regions':1+S/Q,
            'J_lambda0':C/M,'J_lambda1':C/M+S/(9*Q),'lambda0_exact_numerator':str(C*9*Q),
            'lambda1_exact_numerator':str(C*9*Q+S*M),'exact_common_denominator':str(M*9*Q),
            'coarse_crossing_slots_report_only':4096,'coarse_cut_fraction_report_only':4096/M,
            'coarse_S_report_only':128,'mean_fit_distinct_coarse_regions_report_only':1+128/Q}


def metis(labels, cap, minimum, numerator, denominator):
    target=np.float32(numerator/denominator)
    if float(target)>numerator/denominator:target=np.nextafter(target,np.float32(1))
    target=np.nextafter(target,np.float32(1))
    supplied=np.nextafter(np.float32(target-np.float32(.0000499)),np.float32(1))
    effective=np.float32(float(supplied)+.0000499)
    return {'parts':16,'seed':2026090711,'ncuts':1,'niter':10,'numbering':0,'metis_idx_bits':64,'metis_real_bits':32,
            'target_ub_rational':[numerator,denominator],'capacity':cap,'minimum':minimum,
            'region_sizes':np.bincount(labels,minlength=16).tolist(),'structure_pass':True,'violations':[],
            'effective_bound_pass':True,'effective_internal_ubfactor':float(effective),'input_ubvec':float(supplied),
            'library_added_epsilon':.0000499,'metis_edgecut':100,'verified_undirected_edgecut':100,
            'metis_return_code':1,'metis_and_verification_seconds':.1}


def fixture(root, variation=None):
    root.mkdir()
    labels=np.repeat(np.arange(256,dtype=np.uint16),16); coarse=labels//16
    initial_label=label_record(root/'initial/regions.u16',labels)
    coarse_raw=15-coarse
    coarse_stats=metis(coarse_raw,11*N//160,48,11,10)
    coarse_stats['raw_labels']=label_record(root/'initial/coarse_raw.u16',coarse_raw)
    put(root/'initial/coarse.json',coarse_stats)
    children=[]
    for c in range(16):
        child_raw=15-np.repeat(np.arange(16,dtype=np.uint16),16)
        child=metis(child_raw,6*N//1280,3,16*(6*N//1280),256)
        child['coarse_id']=c;child['raw_local_labels']=label_record(root/f'initial/child_{c:02d}_raw.u16',child_raw)
        put(root/f'initial/child_{c:02d}.json',child);children.append(child)
    initial={'status':'COMPLETE','canonicalized_once_before_branches':True,'regions':256,'coarse_count':16,
             'leaves_per_coarse':16,'nodes':N,'labels':initial_label,'labels_file':initial_label['path'],
             'labels_sha256':initial_label['sha256'],'structure':d.label_structure(labels,N),
             'coarse_metis':coarse_stats,'coarse_canonical_labels':label_record(root/'initial/coarse_canonical.u16',coarse),
             'coarse_initial_integer_cap':11*N//160,'children':children}
    top={'status':'COMPLETE','stage':'P3','synthetic':False,'test_fixture_only':True,'actual_dataset_accessed':False,
         'hierarchy_correctness_pass':True,'dataset':DATASET,'n':N,'nodes':N,'regions':256,'coarse_count':16,
         'leaves_per_coarse':16,'cpu_only':True,'heldout_accessed':False,'pilot_accessed':False,
         'base_or_graph_copied':False,'search_graph_modified':False,'CSR_saved_to_disk':False,
         'protocol_sha256':HASH,'source_sha256':d.PARTITION_SOURCE_SHA256,'compile_time_source_sha256':d.PARTITION_SOURCE_SHA256,
         'input_audit_sha256':HASH,'fit_manifest_sha256':HASH,'fit_gt_values_sha256':HASH,'input_graph_sha256':HASH,
         'binary_sha256':HASH,'initial_labels_sha256':initial_label['sha256'],'p2_gate_sha256':HASH,'gt10_sha256':HASH,
         'fit_range':[10000,30000],'fit_count':Q,'initialization':copy.deepcopy(initial),'initial_objective':objective(),
         'input_graph_path':'/FORBIDDEN_GRAPH_READ','gt10_file':'/FORBIDDEN_GT_READ','source_file':'/FORBIDDEN_SOURCE_READ',
         'initializer_CSR':{'nonself_directed_slots':16384,'original_directed_slots':64*N,
                            'count_seconds':.1,'fill_seconds':.1,'sort_unique_seconds':.1,'compact_seconds':.1},
         'incoming_CSR':{'duplicates_and_direction_preserved':True,'directed_nonself_slots':16384,
                         'padding_slots':64*N-16384,'self_slots':0,'wall_seconds':.1},
         'fit_gt10_load_validate_seconds':.1,'initial_objective_seconds':.1,'GT_incidence_build_seconds':.1,
         'wall_seconds':10,'peak_rss_kib':1000}
    initial['objective']=objective()
    for key in ['protocol_sha256','input_audit_sha256','fit_manifest_sha256','source_sha256','binary_sha256']:
        initial[key]=top[key]
    put(root/'initial/manifest.json',initial)
    for lam in (0,1):
        branch={key:top[key] for key in ['dataset','n','nodes','regions','coarse_count','leaves_per_coarse',
            'protocol_sha256','input_audit_sha256','fit_manifest_sha256','fit_gt_values_sha256','input_graph_sha256',
            'source_sha256','binary_sha256','initial_labels_sha256']}
        branch.update(status='COMPLETE',stage='P3',**{'lambda':lam},passes_required=2,passes_completed=2,
                      same_initial_labels_sha256=initial_label['sha256'],initial_state_copy_sha256=initial_label['sha256'],
                      GT_used_for_move_candidates_or_decisions=bool(lam),GT_used_for_posthoc_full_structure_metrics=True,
                      initial_objective=objective(),passes=[],wall_seconds=1.0)
        final_labels=labels.copy()
        if lam: final_labels[0]=1
        for number in (1,2):
            moved=lam and number==1
            saved=label_record(root/f'lambda{lam}/pass{number}.regions.u16',final_labels)
            p={'pass':number,'labels':saved,'structure':d.label_structure(final_labels,N),
               'objective':objective(8192+lam,256-lam),'accepted_moves':int(moved),'cross_coarse_moves':0,
               'next_node_cursor':N,'sum_delta_C':int(moved),'sum_delta_S':-int(moved) if lam else None,
               'all_moves_strictly_negative':True,'GT_S_updated_during_moves':bool(lam),
               'sum_exact_delta_numerator':str(int(moved)*(9*Q-16384)),'wall_seconds':.1,
               'full_recompute':{'C_matches_incremental':True,'exact_J_matches_incremental':True,
                   'pass_strict_descent_if_any_move':True,'S_matches_incremental':True if lam else None,
                   'GT_per_query_region_counts_match':True if lam else None,'lambda0_S_posthoc_only':not bool(lam),
                   'wall_seconds':.1}}
            branch['passes'].append(p)
        final=branch['passes'][-1]
        branch.update(labels_file=final['labels']['path'],labels_sha256=final['labels']['sha256'],labels=final['labels'],
                      final_objective=final['objective'],structure=final['structure'])
        top[f'lambda{lam}']=branch
    if variation=='delta':top['lambda1']['passes'][0]['sum_delta_C']=2
    if variation=='full_recompute':top['lambda1']['passes'][0]['full_recompute']['C_matches_incremental']=False
    if variation=='common_init':top['lambda1']['initial_state_copy_sha256']='0'*64
    if variation=='cross_count':top['lambda1']['passes'][0]['cross_coarse_moves']=1
    if variation=='lambda0_GT':top['lambda0']['passes'][0]['sum_delta_S']=0
    if variation=='missing_pass':top['lambda1']['passes_completed']=1
    if variation=='label_hash':
        changed=final_labels.copy();changed[0]=2;changed.tofile(root/'lambda1/pass1.regions.u16')
    if variation=='capacity':
        changed=np.zeros(N,dtype=np.uint16)
        top['lambda1']['passes'][0]['labels']=label_record(root/'lambda1/pass1.regions.u16',changed)
    if variation=='outside_path':top['lambda1']['passes'][0]['labels']['path']='/FORBIDDEN_GT_READ'
    if variation=='not_complete':top['status']='INCOMPLETE'
    if variation=='gate_binding':top['p2_gate_sha256']='0'*64
    for lam in (0,1):
        b=top[f'lambda{lam}']
        for num,p in enumerate(b['passes'],1):put(root/f'lambda{lam}/pass{num}.json',p)
        put(root/f'lambda{lam}/manifest.json',b)
    put(root/'manifest.json',top)
    return root/'manifest.json'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);a.output=a.output.resolve()
    results=[];accessed=[]
    real_open=Path.open;real_fromfile=np.fromfile
    def watch_open(path,mode='r',*args,**kwargs):
        if mode.startswith('r'):
            assert path.resolve().is_relative_to(a.output),str(path)
            accessed.append(str(path.resolve()))
        return real_open(path,mode,*args,**kwargs)
    def watch_fromfile(path,*args,**kwargs):
        assert Path(path).resolve().is_relative_to(a.output),str(path)
        accessed.append(str(Path(path).resolve()))
        return real_fromfile(path,*args,**kwargs)
    with patch.object(d,'DATASET_N',{DATASET:N}),patch.object(d,'FIT_COUNT',Q):
        valid=fixture(a.output/'valid')
        with patch.object(Path,'open',watch_open),patch.object(d.np,'fromfile',watch_fromfile):
            result=d.analyze_partition(valid,HASH,HASH)
        assert result['status']=='PASS_SAVED_STRUCTURE_EVIDENCE_AUDIT'
        assert result['lambda1_minus_lambda0_final']['registered_structure_condition_met'] is True
        assert result['lambda1_minus_lambda0_final']['S_fit_fragmentation_difference']==-1
        assert len(result['saved_label_evidence'])==23
        assert result['P3_gate_passed'] is False and result['cost']['full_initializer_wall_seconds'] is None
        put(a.output/'valid_analysis.json',result)
        cases={'delta':'Full C','full_recompute':'full-recompute','common_init':'identical saved initialization',
               'cross_count':'changed coarse','lambda0_GT':'Lambda0 unexpectedly','missing_pass':'two completed',
               'label_hash':'SHA256 mismatch','capacity':'violate min3','outside_path':'escapes',
               'not_complete':'completed P3 partition','gate_binding':'P2 gate differs'}
        for variation,expected in cases.items():
            path=fixture(a.output/variation,variation)
            try:
                with patch.object(Path,'open',watch_open),patch.object(d.np,'fromfile',watch_fromfile):
                    d.analyze_partition(path,HASH,HASH)
            except ValueError as e:
                assert expected in str(e),(variation,str(e));results.append({'case':variation,'status':'REJECTED_AS_EXPECTED','error':str(e)})
            else:raise AssertionError('Bad fixture accepted: '+variation)
    report={'status':'PASS','script_sha256':d.sha(SCRIPT),'test_script_sha256':d.sha(__file__),
            'valid_fixture_nodes':N,'valid_fixture_fit_query_count':Q,'actual_saved_labels_checked':23,
            'negative_cases':results,'file_read_boundary':'Only generated fixture JSON/u16 opened; forbidden GT/graph/source paths untouched',
            'unique_fixture_paths_read':len(set(accessed)),'actual_partition_graph_or_GT_analyzed':False}
    put(a.output/'result.json',report);print(json.dumps(report,indent=2))


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Synthetic-only positive, negative, bounded-read and support-denominator tests."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

SOURCE = Path(__file__).with_name('diagnose_target_generalization.py')
spec = importlib.util.spec_from_file_location('target_diagnostic', SOURCE)
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


def require(ok, msg):
    if not ok:
        raise AssertionError(msg)


def rejects(fn, phrase):
    try:
        fn()
    except ValueError as exc:
        require(phrase in str(exc), 'Unexpected error: '+str(exc))
        return
    raise AssertionError('Expected rejection: '+phrase)


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, sort_keys=True, allow_nan=False)+'\n')
    return d.desc(path)


def support_counterexamples():
    # Global top4 counts: 3,2,2,1 (ties choose leaf3); subgroup-only reselection
    # would incorrectly admit leaf4/5 containing the only two seen targets.
    labels = np.array([0,0,0,1,1,2,2,3,4,5], dtype=np.uint16)
    gt = np.arange(10, dtype=np.int32)[None, :]
    seen = np.array([[False]*8+[True,True]])
    metrics = d.oracle_metrics(labels, gt, seen)
    require(metrics['top4'].tolist() == [[0,1,2,3]], 'Global top4 tie order')
    require(metrics['covered'].tolist() == [8] and metrics['covered_seen'].tolist() == [0] and
            metrics['covered_unseen'].tolist() == [8], 'Global top4 subset coverage')
    require(abs(metrics['conditional_weights'].sum()-1) < 1e-15 and metrics['covered'][0]/10 == .8,
            'Conditional weights confused with absolute M4')
    summary = d.metric_summary(metrics, seen.sum(axis=1), np.array([True]))
    require(summary['seen_conditional_target_coverage'] == 0 and summary['unseen_conditional_target_coverage'] == 1,
            'Conditional target-slot denominators')
    empty = d.metric_summary(metrics, seen.sum(axis=1), np.array([False]))
    require(empty['mean_M4_absolute'] is None and empty['seen_conditional_target_coverage'] is None and
            len(empty['distinct_leaf_histogram']) == 10 and len(empty['covered_target_count_histogram']) == 11,
            'Empty bin values or retained exact bins')
    # A transient move returning to initialization must remain an any-pass move.
    init = np.array([0,16,1,2], dtype=np.uint16)
    first = np.array([16,0,1,2], dtype=np.uint16)
    ls = {'common_initial': init, 'lambda0_pass1': first, 'lambda0_final': init.copy(),
          'lambda1_pass1': init.copy(), 'lambda1_final': init.copy()}
    flags = dict(d.movement_flags(ls))
    require(not flags['lambda0_final_leaf_changed_from_initial'].any() and flags['lambda0_any_pass_leaf_changed'].sum() == 2 and
            flags['lambda0_any_pass_coarse_changed'].sum() == 2, 'Transient return move lost')
    # One unseen node appears in several pilot target slots: counts must differ.
    frequency = np.array([10,0,0,0], dtype=np.uint32)
    pilot = np.array([[0,1,2,3,1,2,3,1,2,3], [1,0,2,3,1,2,3,1,2,3]], dtype=np.int32)
    with patch.object(d, 'NFIT', 1):
        pop = d.population_summary(ls, frequency, pilot)
    got = pop['movements']['lambda0_any_pass_leaf_changed']
    require(got['unique_nodes']['unseen']['changed'] == 1 and got['pilot_target_slots']['unseen']['changed'] == 6,
            'Unique node and repeated target-slot counts conflated')
    # Explicit paired direction and exact additive Recall contributions.
    seen_count = np.array([0, 10, 3])
    ref = {'hits': np.array([2,6,6]), 'hits_seen': np.array([0,6,2]), 'hits_unseen': np.array([2,0,4])}
    cand = {'hits': np.array([3,4,6]), 'hits_seen': np.array([0,4,3]), 'hits_unseen': np.array([3,0,3])}
    for key in d.COUNTERS:
        ref[key], cand[key] = np.array([10,20,30]), np.array([11,22,33])
    delta = d.search_delta(cand, ref, seen_count, np.ones(3, dtype=bool))
    require(abs(delta['recall_delta_pp']+10/3) < 1e-12 and delta['query_improved'] == delta['query_harmed'] == delta['query_equal'] == 1,
            'Paired candidate-reference signs')
    require(abs(delta['seen_recall_contribution_delta_pp']+delta['unseen_recall_contribution_delta_pp']-delta['recall_delta_pp']) < 1e-12,
            'Paired support Recall decomposition')
    require(d.search_delta(cand, ref, seen_count, seen_count == 0)['seen_conditional_target_hit_delta'] is None,
            'Empty seen target group must be null')


def prefix_tests(root):
    root.mkdir()
    q, nf, n = 4, 8, 200
    records = np.tile(np.arange(100, dtype='<i4'), (q+nf, 1))
    physical = np.column_stack((np.full(q+nf, 100, dtype='<i4'), records)).astype('<i4').tobytes()
    path = root/'pilot_parent.ivecs'
    path.write_bytes(physical)
    ad = {'files': {'drl_train_gt_path': {'path': str(path), 'header': {'n': q+nf, 'd': 100, 'bytes': len(physical)}}},
          'pilot': {'row_range': [0,q], 'n': q, 'gt_values_sha256': hashlib.sha256(records[:q].tobytes()).hexdigest()}}
    original_open = Path.open
    reads = []
    class PrefixOnly(io.BytesIO):
        def read(self, size=-1):
            require(size >= 0 and self.tell()+size <= q*404, 'Read reached fit suffix')
            reads.append((self.tell(), size))
            return super().read(size)
        def seek(self, *args):
            raise AssertionError('Prefix reader must not seek')
    def guarded_open(p, *args, **kwargs):
        if p.resolve() == path.resolve():
            return PrefixOnly(physical)
        return original_open(p, *args, **kwargs)
    with patch.object(d, 'NQ', q), patch.object(d, 'NFIT', nf), patch.object(Path, 'open', guarded_open):
        gt, evidence = d.read_pilot_prefix(ad, q, n)
        require(gt.shape == (q,10) and reads == [(0,q*404)] and evidence['parent_file_rehashed'] is False, 'Exact physical prefix read')
        bad = copy.deepcopy(ad); bad['pilot']['gt_values_sha256'] = '0'*64
        rejects(lambda: d.read_pilot_prefix(bad,q,n), 'full pilot top100 value SHA')
    with patch.object(d, 'NQ', q), patch.object(d, 'NFIT', nf):
        altered = bytearray(physical); altered[0:4] = (99).to_bytes(4,'little'); path.write_bytes(altered)
        rejects(lambda: d.read_pilot_prefix(ad,q,n), 'per-record GT header')
    rejects(lambda: d.validate_gt10(np.zeros((1,10),dtype=np.int32),1,n), 'Duplicate GT10')
    rejects(lambda: d.validate_gt10(np.arange(190,200,dtype=np.int32)[None,:],1,199), 'outside frozen base')


def fixture(root):
    root.mkdir()
    q, nf, n = 6, 8, 768
    datasets = {'fixture_a': n, 'fixture_b': n}
    p3 = write(root/'p3_protocol.json', {'fixture': True})
    # Fixed fit targets; pilot has six exact support sizes, including empty groups.
    fit_gt = np.stack([np.array([0,1,2,3,6,9,12,15,18,21],dtype=np.int32)+3*i for i in range(nf)])
    support = np.unique(fit_gt)
    unseen = np.setdiff1d(np.arange(60,200,dtype=np.int32), support)
    pilot_gt = np.stack([np.concatenate((support[:k], unseen[:10-k])) for k in (0,1,2,5,10,10)]).astype('<i4')
    initial = np.repeat(np.arange(256,dtype=np.uint16),3)
    l0p1 = initial.copy(); l0p1[[0,48]] = l0p1[[48,0]]
    l0final = initial.copy()  # Both nodes return to initial on pass2.
    l1p1 = initial.copy(); l1p1[[0,96]] = l1p1[[96,0]]
    l1final = l1p1.copy(); l1final[[3,99]] = l1final[[99,3]]
    labels = {'common_initial':initial, 'lambda0_pass1':l0p1, 'lambda0_final':l0final,
              'lambda1_pass1':l1p1, 'lambda1_final':l1final}
    audit_ds = []
    for ds in datasets:
        dr = root/ds; dr.mkdir()
        parent_values = np.tile(np.arange(100,dtype='<i4'),(q+nf,1))
        parent_values[:q,:10] = pilot_gt
        parent_values[q:,:10] = fit_gt
        parent = dr/'parent.ivecs'
        parent.write_bytes(np.column_stack((np.full(q+nf,100,dtype='<i4'),parent_values)).astype('<i4').tobytes())
        audit_ds.append({'dataset':ds, 'graph':{'path':str(dr/'FORBIDDEN_GRAPH'), 'header':{'n':n,'d':4}, 'sha256':'a'*64},
            'fit':{'row_range':[q,q+nf], 'n':nf, 'query_values_sha256':'b'*64,
                   'gt_values_sha256':hashlib.sha256(parent_values[q:].tobytes()).hexdigest()},
            'pilot':{'row_range':[0,q], 'n':q, 'gt_values_sha256':hashlib.sha256(parent_values[:q].tobytes()).hexdigest()},
            'files':{'drl_train_gt_path':{'path':str(parent), 'header':{'n':q+nf,'d':100,'bytes':(q+nf)*404}}}})
    audit_path = root/'audit.json'
    audit_binding = write(audit_path, {'status':'PASS_INPUT_CONTRACT','heldout_accessed':False,'datasets':audit_ds})
    main_ds, structure_ds = [], []
    for ad in audit_ds:
        ds = ad['dataset']; dr = root/ds
        fit_path = dr/'fit_gt10.i32'; fit_gt.astype('<i4').tofile(fit_path)
        fit = {'status':'COMPLETE','stage':'P3','dataset':ds,'fit_range':[q,q+nf],'fit_count':nf,
               'pilot_accessed':False,'heldout_accessed':False,'input_audit_sha256':audit_binding['sha256'],
               'protocol_sha256':p3['sha256'],'fit_gt_values_sha256':ad['fit']['gt_values_sha256'],
               'gt10_file':str(fit_path),'gt10_sha256':d.sha(fit_path)}
        fit_binding = write(dr/'fit_manifest.json',fit)
        lr = dr/'partition'; lr.mkdir()
        label_desc = {}
        for name, arr in labels.items():
            path = lr/(name+'.u16'); arr.astype('<u2').tofile(path)
            label_desc[name] = {**d.desc(path),'rows':n,'bytes':n*2,'dtype':'little-endian uint16','header':False}
        fseen = np.ones_like(fit_gt,dtype=bool)
        objs = {name:{'S_fit_distinct_leaf_minus_one':int((d.oracle_metrics(arr,fit_gt,fseen)['D']-1).sum())} for name,arr in labels.items()}
        top = {'status':'COMPLETE','stage':'P3','dataset':ds,'nodes':n,'regions':256,'protocol_sha256':p3['sha256'],
               'input_audit_sha256':audit_binding['sha256'],'fit_manifest_sha256':fit_binding['sha256'],
               'initial_labels_sha256':label_desc['common_initial']['sha256'],
               'initialization':{'labels':label_desc['common_initial']}, 'initial_objective':objs['common_initial']}
        branch_binding = {}
        for lam in (0,1):
            name = f'lambda{lam}'
            branch = {'status':'COMPLETE','initial_labels_sha256':top['initial_labels_sha256'],
                      'passes':[{'labels':label_desc[name+'_pass1'],'objective':objs[name+'_pass1']},
                                {'labels':label_desc[name+'_final'],'objective':objs[name+'_final']}]}
            top[name] = branch
            branch_binding[name] = write(lr/(name+'.json'),branch)
        top_binding = write(lr/'manifest.json',top)
        models, model_ev, derived = {}, {}, {}
        frequency = np.bincount(fit_gt.ravel(),minlength=n)
        seen = frequency[pilot_gt]>0
        for mi,name in enumerate(d.MODELS):
            branch, rule = name.split('_',1)
            lab = label_desc[branch+'_final']
            model = {'schema_version':2,'status':'COMPLETE','stage':'P3','dataset':ds,'model_name':name,'lambda':int(branch[-1]),
                     'portal_rule':rule,'oracle_diagnostic_only':True,'region_count':256,'coarse_count':16,'leaves_per_coarse':16,
                     'active_regions':4,'portals_per_region':3,'total_portals':768,'fit_range':[q,q+nf],'fit_count':nf,
                     'cpu_only':True,'pilot_accessed':False,'validation_accessed':False,'heldout_accessed':False,'base_nodes':n,
                     'protocol_sha256':p3['sha256'],'input_audit_sha256':audit_binding['sha256'],'graph_sha256':ad['graph']['sha256'],
                     'fit_query_values_sha256':ad['fit']['query_values_sha256'],'fit_gt_values_sha256':ad['fit']['gt_values_sha256'],
                     'protocol':p3,'audit':audit_binding,'labels_file':lab['path'],'labels_sha256':lab['sha256'],
                     'partition_manifest':branch_binding[branch],'fit_manifest':fit_binding,'gt10_sha256':fit['gt10_sha256']}
            model_binding = write(dr/name/'model.json',model)
            oracle = d.oracle_metrics(labels[branch+'_final'],pilot_gt,seen)
            batches = []
            for l in d.LS:
                # Fast deliberately contains no counters or rows; it must never be analyzed.
                batches.append({'search_L':l,'method':'fast','round':0,'UNMEASURED_DO_NOT_TOUCH':True})
                for method in d.METHODS:
                    rows = []
                    for j in range(q):
                        hits = 4+(l==128)+(method=='oracle_probability')+(mi%2==1)-(j%3==0)
                        ids = list(map(int,pilot_gt[j,:hits]))+list(range(600,600+10-hits))
                        count = 100+mi+j+int(method=='oracle_probability')
                        rows.append({'query_id':j,'result_ids':ids,'recall':hits/10,
                                     'regions':oracle['top4'][j].tolist(),'weights':oracle['conditional_weights'][j].tolist(),
                                     'fast_anchor_id':500,'shared_seed':501,'actual_entry_count':3,'entry_ids':[500,501,502],
                                     'routing_ndc':2,'graph_ndc':count,'total_ndc':count+2,
                                     'routing_mac':8,'graph_mac':count*4,'total_mac':(count+2)*4,
                                     'expanded':count//2,'rejected':3,'evicted_unexpanded':1})
                    batch = {'search_L':l,'method':method,'round':0,'per_query':rows,'mean_recall':float(np.mean([x['recall'] for x in rows]))}
                    batches.append(batch)
                    derived[(name,method,l)] = d.parse_oracle_batch(batch,pilot_gt,seen,oracle,n)[0]
            artifact = {'status':'COMPLETE','stage':'P3','dataset':ds,'split':'pilot','source_query_type':'drl_train',
                        'source_query_range':[0,q],'num_queries':q,'measurement':'count','cpu_only':True,'threads':16,'metric':'ip',
                        'top_k':10,'search_Ls':list(d.LS),'rounds':1,'heldout_accessed':False,'oracle_is_deployment':False,
                        'region_count':256,'portals_per_region':3,'base_nodes':n,'model_manifest':model,'model_sha256':model_binding['sha256'],
                        'model_file':model_binding['path'],'index_file':ad['graph']['path'],'results':batches}
            count_binding = write(dr/name/'count.json',artifact)
            model_ev[name] = {'model':model_binding,'count':count_binding,'labels':{'path':lab['path'],'sha256':lab['sha256']},
                              'partition_manifest':branch_binding[branch]}
            models[name] = model
        comparisons = []
        for name,cm,method,rm,refmethod in d.CONTRASTS[:8]:
            for l in d.LS:
                z = d.search_delta(derived[(cm,method,l)],derived[(rm,refmethod,l)],seen.sum(axis=1),np.ones(q,dtype=bool))
                comparisons.append({'L':l,'contrast':name,'candidate_model':cm,'candidate_method':method,
                    'reference_model':rm,'reference_method':refmethod,**{k:z[k] for k in ('recall_delta_pp','query_improved','query_harmed','query_equal')},
                    **{'mean_'+k+'_delta':z['mean_counter_deltas'][k] for k in ('graph_ndc','total_ndc','total_mac')}})
        main_ds.append({'dataset':ds,'evidence':{'audit':audit_binding,'protocol':p3,'models':model_ev,
                                               'common_initial_labels_sha256':top['initial_labels_sha256']},'fixed_comparisons':comparisons})
        structure_ds.append({'dataset':ds,'partition_manifest':top_binding,'common_initial_labels_sha256':top['initial_labels_sha256'],
                             'saved_label_evidence':[{**{'path':v['path'],'sha256':v['sha256'],'rows':n},'regions':256} for v in label_desc.values()]})
    main_binding = write(root/'main.json',{'status':'COMPLETE','datasets':main_ds})
    structure_binding = write(root/'structure.json',{'status':'COMPLETE','datasets':structure_ds})
    gate = {'stage':'P3','status':'NOPASS','decision':'NO_GO_P3_SEARCH_TRANSFER','P4_P8_authorized':False,
            'validation_heldout_authorized':False,'protocol':p3,'evidence':[main_binding,structure_binding]}
    gate_binding = write(root/'gate.json',gate)
    protocol = {'stage':'P3_POST_NOGO_DIAGNOSIS','status':'PREREGISTERED_BEFORE_DIAGNOSTIC_IMPLEMENTATION_AND_NEW_DATA_READS',
                'datasets':list(datasets),'fit_range':[q,q+nf],'pilot_range':[0,q],'structures':list(d.STRUCTURES),
                'method_revision_increment':0,'P4_authorized':False,'new_model_or_auxgraph_authorized':False,
                'P3_protocol':p3,'upstream_P3':gate_binding,'analysis':main_binding,'structure_analysis':structure_binding,
                'interpretation_limits':['Synthetic fixture only.']}
    protocol_path = root/'protocol.json'; pb = write(protocol_path,protocol)
    return {'NQ':q,'NFIT':nf,'DATASET_N':datasets,'P3_PROTOCOL_SHA':p3['sha256'],'PROTOCOL_SHA':pb['sha256']}, protocol_path, audit_path


def integration_and_negative_tests(root):
    # Every data/JSON open must remain in this generated test directory. Original
    # graph paths are absent and Fast batches intentionally lack usable fields.
    with patch.object(d,'NQ',6), patch.object(d,'NFIT',8):
        constants, protocol_path, audit_path = fixture(root/'fixture')
    contexts = [patch.object(d,k,v) for k,v in constants.items()]
    for context in contexts:
        context.start()
    original_open, original_fromfile = Path.open, np.fromfile
    opened = []
    def guard_path(p):
        path = Path(p).resolve()
        require(path.is_relative_to(root.resolve()) or path == SOURCE.resolve(), 'Non-synthetic input read: '+str(path))
        require('FORBIDDEN' not in str(path), 'Forbidden input opened')
        opened.append(str(path))
    def guarded_open(p,*args,**kwargs):
        guard_path(p)
        return original_open(p,*args,**kwargs)
    def guarded_fromfile(file,*args,**kwargs):
        guard_path(file)
        return original_fromfile(file,*args,**kwargs)
    try:
        with patch.object(Path,'open',guarded_open), patch.object(np,'fromfile',guarded_fromfile):
            args = SimpleNamespace(protocol=str(protocol_path),audit=str(audit_path),output=str(root/'complete'))
            require(d.run(args) == 0,'Full synthetic integration failed')
            result = d.read_json(root/'complete/diagnosis.json')
            require(result['status']=='COMPLETE' and result['P3_gate_status_unchanged']=='NOPASS','Output status/gate changed')
            require(len(result['datasets']) == 2,'Missing dataset')
            for ds in result['datasets']:
                require(len(ds['search_contrasts'])==20,'Not all ten contrasts/both L')
                require([x['k_seen'] for x in ds['pilot']['k_seen_strata']] == list(range(11)),'Missing exact support strata')
                require(sum(x['queries'] for x in ds['pilot']['k_seen_strata'])==6,'Strata query loss')
                require(ds['fit']['structures']['common_initial']['unseen_conditional_target_coverage'] is None,'Fit unseen group exists')
                for contrast in ds['search_contrasts']:
                    require(len(contrast['k_seen_strata'])==11,'Search stratum missing')
                    z=contrast['overall']
                    require(abs(z['recall_delta_pp']-z['seen_recall_contribution_delta_pp']-z['unseen_recall_contribution_delta_pp'])<1e-12,
                            'Search contribution summary differs')
                for artifact in ds['artifacts'].values():
                    arrays=np.load(artifact['path'],allow_pickle=False)
                    require(not any('GT' in name or 'result_ids' in name or 'top4' in name for name in arrays.files),'Raw GT/result dump')
            # Preflight rejection must happen before any raw/count read.
            bad_protocol = root/'bad_protocol.json'; bad_protocol.write_text('{}')
            rejects(lambda:d.preflight(bad_protocol,audit_path),'protocol differs')
            _,_,prepared = d.preflight(protocol_path,audit_path)
            ds = prepared['fixture_a']; model_name=d.MODELS[0]
            binding=ds['main']['evidence']['models'][model_name]['count']
            artifact=d.bound_json(binding)
            labels,_=d.load_labels(ds,768)
            gt,_=d.read_pilot_prefix(ds['audit'],6,768)
            fgt,_=d.read_fit_gt10(ds['fit_binding'],ds['fit'],ds['audit'],768)
            seen=np.bincount(fgt.ravel(),minlength=768)[gt]>0
            oracle=d.oracle_metrics(labels['lambda0_final'],gt,seen)
            batch=next(b for b in artifact['results'] if b['method']=='oracle_probability' and b['search_L']==64)
            mutations=(('regions',lambda r:r['regions'].__setitem__(0,255),'oracle regions'),
                       ('weights',lambda r:r['weights'].__setitem__(0,r['weights'][0]+.01),'conditional top4 weights'),
                       ('recall',lambda r:r.__setitem__('recall',.987),'Saved Recall'),
                       ('duplicate_result',lambda r:r['result_ids'].__setitem__(1,r['result_ids'][0]),'Duplicate saved'),
                       ('range',lambda r:r['result_ids'].__setitem__(0,768),'Invalid saved top10'),
                       ('ndc',lambda r:r.__setitem__('total_ndc',999),'Counter additive'),
                       ('negative_counter',lambda r:r.__setitem__('expanded',-1),'Invalid measured oracle counter'),
                       ('query_id',lambda r:r.__setitem__('query_id',5),'query alignment'))
            for _,mutate,phrase in mutations:
                bad=copy.deepcopy(batch); mutate(bad['per_query'][0])
                rejects(lambda:d.parse_oracle_batch(bad,gt,seen,oracle,768),phrase)
            # Exact route control: valid saved oracle selection/weights with a
            # changed anchor is still forbidden for the same model's queue/L.
            bad=copy.deepcopy(artifact)
            next(b for b in bad['results'] if b['method']=='oracle_probability' and b['search_L']==64)['per_query'][0]['fast_anchor_id']=499
            bad_binding=write(root/'bad_route_count.json',bad)
            bd=copy.deepcopy(ds); bd['main']['evidence']['models'][model_name]['count']=bad_binding
            pmetrics={s:d.oracle_metrics(labels[s],gt,seen) for s in d.STRUCTURES}
            rejects(lambda:d.load_search(bd,gt,seen,pmetrics,768),'controls change actual route')
            # Embedded model content and checksum bindings are both checked.
            bad=copy.deepcopy(artifact); bad['model_manifest']['fit_count']=7
            bad_binding=write(root/'bad_model_count.json',bad)
            bd=copy.deepcopy(ds); bd['main']['evidence']['models'][model_name]['count']=bad_binding
            rejects(lambda:d.load_search(bd,gt,seen,pmetrics,768),'model_manifest')
            bd=copy.deepcopy(ds); bd['main']['evidence']['models'][model_name]['count']['sha256']='0'*64
            rejects(lambda:d.load_search(bd,gt,seen,pmetrics,768),'SHA256 mismatch')
            # Gate mutations remain a hard failure even with a correctly bound
            # test-only preregistration hash; production digest is immutable.
            prot=d.read_json(protocol_path); gate=d.bound_json(prot['upstream_P3']); gate['status']='PASS'
            prot['upstream_P3']=write(root/'bad_gate.json',gate)
            badp=write(root/'bad_gate_protocol.json',prot)
            with patch.object(d,'PROTOCOL_SHA',badp['sha256']):
                rejects(lambda:d.preflight(badp['path'],audit_path),'NOPASS gate mismatch')
        return result, opened
    finally:
        for context in reversed(contexts):
            context.stop()


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--output',required=True)
    root=Path(ap.parse_args().output).resolve(); root.mkdir(parents=True,exist_ok=False)
    support_counterexamples()
    prefix_tests(root/'prefix')
    result, opened=integration_and_negative_tests(root)
    summary={'status':'PASS','source':d.desc(SOURCE),'scope':'Generated fixtures only; no actual GT/labels/count rows read.',
             'tests':['same_full_GT_top4_support_coverage','conditional_weights_vs_absolute_mass','all_exact_empty_bins',
                      'transient_pass1_return_move','unique_nodes_vs_repeated_target_slots','candidate_minus_reference_signs',
                      'exact_seen_unseen_Recall_decomposition','empty_target_denominator_null',
                      'physical_prefix_single_bounded_read_no_seek_suffix_or_parent_hash','all_top100_values_SHA_rejection',
                      'per_record_header_rejection','duplicate_GT10_rejection','out_of_range_GT10_rejection',
                      'complete_two_dataset_synthetic_integration','all_10_contrasts_both_L_all_11_strata',
                      'Fast_sentinel_rows_never_analyzed','no_raw_GT_or_results_in_NPZ','protocol_SHA_rejection',
                      'oracle_region_rejection','conditional_weight_rejection','saved_Recall_rejection','duplicate_result_rejection',
                      'result_range_rejection','counter_addition_rejection','negative_counter_rejection','query_alignment_rejection',
                      'same_model_queue_L_route_rejection','embedded_model_rejection','count_SHA_rejection','P3_NOPASS_gate_rejection',
                      'filesystem_and_numpy_fromfile_fixture_only_guard'],
             'guarded_open_count':len(opened),'synthetic_datasets':[x['dataset'] for x in result['datasets']]}
    write(root/'result.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()

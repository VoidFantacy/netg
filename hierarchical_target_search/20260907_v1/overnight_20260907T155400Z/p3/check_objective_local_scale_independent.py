#!/usr/bin/env python3
"""Independent tiny fixtures for the frozen post-NOPASS degree audit. No real data reads."""
import argparse
from collections import Counter
import copy
from fractions import Fraction
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

SOURCE = Path(__file__).with_name('diagnose_objective_local_scale.py')
PROTOCOL = Path(__file__).with_name('objective_local_scale_protocol_v1.json')
EXPECTED_SOURCE = '148e3ff29259857865e9916f5f3905f2f2d1ffd3c1d843bfd8909a16c18259c8'
spec = importlib.util.spec_from_file_location('reviewed_degree_source', SOURCE)
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
CHECKS = []


def check(ok, name):
    if not ok:
        raise AssertionError(name)
    CHECKS.append(name)


def rejects(fn, text, name):
    try:
        fn()
    except ValueError as exc:
        check(text in str(exc), name + ': ' + str(exc)); return
    raise AssertionError(name + ': did not reject')


def graph_checks(root):
    adj = np.array([[1,1,-1,0],[0,2,-1,-1],[3,2,-1,-1],[1,-1,-1,-1]], dtype='<i4')
    prefix = b'header!'; suffix = b'NONNUMERIC_VECTOR_MARKER'
    raw = prefix + adj.tobytes() + suffix
    path = root/'tiny_graph.bin'; path.write_bytes(raw)
    header = {'n':4,'degree':4,'neighbor_count':16,'adjacency_offset':len(prefix)}
    reads = []
    class AdjacencyBytes(io.BytesIO):
        def seek(self, where, whence=0):
            assert where == len(prefix) and whence == 0
            return super().seek(where, whence)
        def read(self, size=-1):
            assert size >= 0 and len(prefix) <= self.tell() <= len(prefix)+adj.nbytes-size
            reads.append((self.tell(),size)); return super().read(size)
    with patch.object(Path, 'open', lambda *a, **k: AdjacencyBytes(raw)):
        incoming,outgoing,total,slots,bounds = d.scan_adjacency(path,header,row_block=3)
    check(incoming.tolist()==[1,3,1,1] and outgoing.tolist()==[2,2,1,1] and total.tolist()==[3,5,2,2],
          'directed duplicates and reciprocal arcs retain multiplicity')
    check(slots=={'invalid_edges':0,'padding':8,'valid_edges':8,'self_edges':2,'valid_nonself_edges':6},
          'self arcs and only minus1 padding excluded')
    check(reads==[(7,48),(55,16)] and bounds['numeric_byte_range']==[7,71] and
          bounds['sum_in']==bounds['sum_out']==6 and bounds['sum_total']==12,
          'unaligned bounded blocks do not interpret vector suffix; exact conservation')
    check(d.sha(path)==hashlib.sha256(raw).hexdigest(), 'full-file provenance hash includes uninterpreted suffix')
    binding={'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()}
    check(d.bound_path(binding)==path.resolve(), 'bound-path positive fixture')
    path.write_bytes(raw+b'x')
    rejects(lambda:d.bound_path(binding),'SHA256 mismatch','bound-path tamper rejected')
    for value in (-2,4):
        bad=adj.copy(); bad[0,0]=value; path.write_bytes(prefix+bad.tobytes()+suffix)
        rejects(lambda:d.scan_adjacency(path,header,row_block=3),'Invalid adjacency ID',f'invalid adjacency {value} rejected before mask')
    path.write_bytes(prefix+adj.tobytes()[:-1])
    rejects(lambda:d.scan_adjacency(path,header,row_block=3),'Short bounded adjacency','short final adjacency block rejected')


def numeric_checks(root):
    check(d.exact_condition(np.array([0,1,2,50000],dtype=np.int32),180000,20000).tolist()==[True,False,False,False],
          'strict equality excluded and int32 inputs promoted before multiplication')
    check(d.exact_condition(np.array([1,2],dtype=np.int64),180001,20000).tolist()==[True,False],
          'integer one-unit boundary preserves strictness')
    rejects(lambda:d.exact_condition(np.array([2**62],dtype=np.int64),180000,20000),'overflow int64','int64 overflow rejected')
    rejects(lambda:d.exact_condition(np.array([-1],dtype=np.int64),180000,20000),'Invalid degree','negative total degree rejected')
    values=np.array([0,7,10**12],dtype=np.int64); counts=np.array([1,98,1],dtype=np.int64)
    expanded=[0]+[7]*98+[10**12]
    expected=[]
    for p in d.QUANTILES:
        numerator,denominator=Fraction(str(p)).as_integer_ratio()
        rank=max(0,(numerator*100+denominator-1)//denominator-1)
        expected.append({'p':p,'degree':expanded[rank],'zero_based_order_index':rank})
    with patch.object(np,'bincount',side_effect=AssertionError('dense degree histogram forbidden')):
        check(d.quantiles_from_sparse(values,counts)==expected, 'decimal-rational inverted-CDF endpoint and p99 ranks')
        histogram=d.compact_histogram(values,counts)
    encoded=json.dumps(histogram['pairs'],separators=(',',':')).encode()
    check(histogram['pairs']==[[0,1],[7,98],[10**12,1]] and histogram['encoded_pair_array_bytes']==len(encoded),
          'sparse large degree histogram has exact compact pair byte count')
    capped=d.compact_histogram(values,counts,limit=999)
    full=(json.dumps(capped,separators=(',',':'))+'\n').encode()
    exact=d.compact_histogram(values,counts,limit=len(full))
    check(exact['included'] and not d.compact_histogram(values,counts,limit=len(full)-1)['included'],
          'histogram complete artifact cap exact equality and one byte excess')
    path=root/'histogram.json'; binding=d.persist_histogram(path,exact); payload=path.read_bytes()
    check(len(payload)==binding['artifact']['bytes']<=exact['limit_bytes'] and
          hashlib.sha256(payload).hexdigest()==binding['artifact']['sha256'] and 'pairs' not in binding and
          json.loads(payload)['pairs']==histogram['pairs'], 'histogram artifact includes metadata newline and reports only checksum binding')
    omitted=d.compact_histogram(values,counts,limit=len(encoded)); absent=root/'omitted.json'
    check(not d.persist_histogram(absent,omitted)['included'] and not absent.exists(),
          'pair-only cap is insufficient and omitted histogram creates no file')
    check(all(x['degree'] is None and x['zero_based_order_index'] is None for x in
          d.quantiles_from_sparse(np.array([],dtype=np.int64),np.array([],dtype=np.int64))), 'empty quantile arrays return null')


def group_checks():
    frequency=np.array([0,1,2,3,4,5,9,10,19,20,49,50,99,100,200,429,0,0,0,0],dtype=np.int64)
    n=len(frequency); q=100; M=2700
    incoming=np.array([0,2,1,3,0,4,1,9,2,2,6,0,1,7,2,3,0,0,0,1],dtype=np.int64)
    outgoing=np.arange(n,dtype=np.int64)%3; total=incoming+outgoing
    labels={'common_initial':np.arange(n,dtype=np.uint16)%4}
    labels['lambda0_final']=labels['common_initial'].copy()
    labels['lambda1_final']=labels['common_initial'].copy(); labels['lambda1_final'][[1,3,17]]^=1
    populations={'all':[True]*n,'seen':[int(f)>0 for f in frequency],'unseen':[int(f)==0 for f in frequency]}
    moves={
        d.MOVEMENTS[0]:[False]*n,
        d.MOVEMENTS[1]:[i in (1,3,17) for i in range(n)],
        d.MOVEMENTS[2]:[i in (1,3,17) for i in range(n)]}
    target={'unique_node_denominators':{p:sum(mask) for p,mask in populations.items()},
            'sum_fit_target_occurrences':1000,'maximum_fit_query_occurrences_of_one_node':429,'movements':{}}
    for variable,changed in moves.items():
        target['movements'][variable]={'unique_nodes':{p:{'changed':sum(c and m for c,m in zip(changed,mask)),
            'denominator':sum(mask)} for p,mask in populations.items()}}
    groups,histogram,integrity=d.all_summaries(incoming,outgoing,total,frequency,labels,M,q,target)
    for group in groups:
        if group['family']=='support': mask=populations[group['population']]
        elif group['family']=='frequency':
            lo,hi=group['frequency_interval_inclusive']; mask=[lo<=int(f) and (hi is None or int(f)<=hi) for f in frequency]
        else:
            mask=[p and (c if group['state']=='changed' else not c) for p,c in
                  zip(populations[group['population']],moves[group['variable']])]
        ids=[i for i,yes in enumerate(mask) if yes]; good=[i for i in ids if int(total[i])*900<M]
        occ=sum(int(frequency[i]) for i in ids); good_occ=sum(int(frequency[i]) for i in good)
        expected={'node_count':len(ids),'fit_target_occurrences':occ,'condition_node_count':len(good),
                  'condition_node_fraction':len(good)/len(ids) if ids else None,
                  'condition_fit_occurrences':good_occ,'condition_fit_occurrence_weighted_fraction':good_occ/occ if occ else None}
        assert all(group[key]==value for key,value in expected.items()), (group,expected)
        for name,array in [('in',incoming),('out',outgoing),('total',total)]:
            subset=[int(array[i]) for i in ids]
            assert group[name+'_degree']=={'mean':sum(subset)/len(subset) if subset else None,
                'min':min(subset) if subset else None,'max':max(subset) if subset else None}
        ordered=sorted(int(total[i]) for i in ids)
        for actual in group['total_degree_quantiles']:
            f=Fraction(str(actual['p'])); rank=max(0,(f.numerator*len(ids)+f.denominator-1)//f.denominator-1) if ids else None
            assert actual['zero_based_order_index']==rank and actual['degree']==(ordered[rank] if ids else None)
    check(len(groups)==31, 'all 31 groups match independent Python masks counts weighted fractions means and quantiles')
    check(sum(g['node_count'] for g in groups if g['family']=='frequency')==n and
          sum(g['fit_target_occurrences'] for g in groups if g['family']=='frequency')==1000,
          'all ten frequency intervals retain endpoints and exhaust occurrences')
    empty=[g for g in groups if g['family']=='movement' and g['variable']==d.MOVEMENTS[0] and g['state']=='changed']
    check(len(empty)==3 and all(g['node_count']==0 and g['condition_node_fraction'] is None and
          g['condition_fit_occurrence_weighted_fraction'] is None for g in empty), 'all empty changed groups retained with null denominators')
    unseen=next(g for g in groups if g['family']=='support' and g['population']=='unseen')
    check(unseen['node_count']==5 and unseen['condition_fit_occurrence_weighted_fraction'] is None,
          'unseen unique node denominator remains distinct from zero occurrence denominator')
    check(histogram['pairs']==[list(x) for x in sorted(Counter(map(int,total)).items())], 'all-base histogram matches independent Counter')
    damaged=copy.deepcopy(target); damaged['movements'][d.MOVEMENTS[2]]['unique_nodes']['seen']['changed']+=1
    rejects(lambda:d.all_summaries(incoming,outgoing,total,frequency,labels,M,q,damaged),'movement count differs','saved movement discrepancy rejected')


def preflight_checks():
    protocol=json.loads(PROTOCOL.read_text())
    data={}; audit_rows=[]; target_rows=[]; algebra_rows=[]; review_rows=[]
    gate={'status':'NOPASS','stage':'P3','decision':'NO_GO_P3_SEARCH_TRANSFER','P4_P8_authorized':False,
          'validation_heldout_authorized':False,'protocol':protocol['P3_protocol']}
    for dataset,n in d.DATASET_N.items():
        def binding(name): return {'path':'/synthetic/'+dataset+'/'+name,'sha256':'hash-'+name}
        labels={name:{**binding(name),'rows':n,'bytes':n*2} for name in d.LABELS}
        partition_binding=binding('partition'); fit_binding=binding('fit_manifest')
        top={'status':'COMPLETE','stage':'P3','dataset':dataset,'nodes':n,'regions':256,
             'protocol_sha256':d.P3_PROTOCOL_SHA,'input_audit_sha256':protocol['P0_audit']['sha256'],
             'initial_objective':{'M_original_directed_valid_nonself_slots':100,'Q':20000},'input_graph_sha256':'graphhash',
             'initialization':{'labels':labels['common_initial']},'initial_labels_sha256':labels['common_initial']['sha256'],
             'fit_manifest_sha256':fit_binding['sha256']}
        for lam in (0,1): top[f'lambda{lam}']={'passes':[{}, {'labels':labels[f'lambda{lam}_final']}],
            'initial_labels_sha256':labels['common_initial']['sha256']}
        fit={'status':'COMPLETE','stage':'P3','dataset':dataset,'fit_count':20000,'fit_range':[10000,30000],
             'input_audit_sha256':protocol['P0_audit']['sha256'],'protocol_sha256':d.P3_PROTOCOL_SHA,
             'pilot_accessed':False,'heldout_accessed':False,'fit_gt_values_sha256':'gtvalues',
             'gt10_file':'/synthetic/'+dataset+'/gt10','gt10_sha256':'gt10hash'}
        data[partition_binding['path']]=top; data[fit_binding['path']]=fit
        audit_rows.append({'dataset':dataset,'graph':{'header':{'n':n},'sha256':'graphhash','expected_sha256':'graphhash'},
            'fit':{'n':20000,'row_range':[10000,30000],'gt_values_sha256':'gtvalues'}})
        target_rows.append({'dataset':dataset,'status':'COMPLETE','nodes':n,'fit_queries':20000,
            'evidence':{'partition_manifest':partition_binding,'saved_labels_rehashed':labels,
                'fit_GT':{'fit_manifest':fit_binding,'gt10':{'path':fit['gt10_file'],'sha256':'gt10hash'}}}})
        algebra_rows.append({'dataset':dataset,'N':n,'Q_fit':20000,'M_directed_valid_nonself':100,'partition_manifest':partition_binding})
        review_rows.append({'dataset':dataset,'N':n,'Q':20000,'M':100})
    data[protocol['P3_protocol']['path']]={}
    data[protocol['upstream_P3']['path']]=gate
    data[protocol['P0_audit']['path']]={'status':'PASS_INPUT_CONTRACT','heldout_accessed':False,'datasets':audit_rows}
    data[protocol['target_diagnosis']['path']]={'status':'COMPLETE','stage':'P3_POST_NOGO_TARGET_GENERALIZATION',
        'P3_gate_status_unchanged':'NOPASS','audit':protocol['P0_audit'],'upstream_P3':protocol['upstream_P3'],'datasets':target_rows}
    data[protocol['target_diagnosis_completion']['path']]={'status':'COMPLETE','diagnosis':protocol['target_diagnosis'],
        'datasets':list(d.DATASET_N),'P3_gate_status_unchanged':'NOPASS'}
    data[protocol['algebra']['path']]={'status':'COMPLETE_POSTHOC_ALGEBRA_ONLY','protocol':protocol['P3_protocol'],
        'gate':protocol['upstream_P3'],'datasets':algebra_rows}
    data[protocol['algebra_independent_review']['path']]={'status':'PASS_ALGEBRA_AND_METADATA_REVIEW',
        'source_analysis':protocol['algebra'],'protocol':protocol['P3_protocol'],'gate':protocol['upstream_P3'],'datasets':review_rows}
    sentinel=object()
    with patch.object(d,'sha',return_value=d.PROTOCOL_SHA),patch.object(d,'read_json',return_value=protocol), \
         patch.object(d,'bound_json',side_effect=lambda b:copy.deepcopy(data[b['path']])),patch.object(d,'import_header',return_value=sentinel):
        actual,prepared,parser=d.preflight('/synthetic/protocol')
        check(set(prepared)==set(d.DATASET_N) and parser is sentinel, 'full two-dataset metadata preflight accepts hand-built contract')
        gate['P4_P8_authorized']=True
        rejects(lambda:d.preflight('/synthetic/protocol'),'P3 NOPASS gate mismatch','gate reopening rejected before numerical reads')
        gate['P4_P8_authorized']=False
        target_rows[0]['fit_queries']=19999
        rejects(lambda:d.preflight('/synthetic/protocol'),'Frozen node/fit count','fit count mismatch rejected')
        target_rows[0]['fit_queries']=20000
        top=data[algebra_rows[0]['partition_manifest']['path']]
        top['lambda1']['initial_labels_sha256']='otherinit'
        rejects(lambda:d.preflight('/synthetic/protocol'),'Branches lack common initialization','branch initialization mismatch rejected')
        top['lambda1']['initial_labels_sha256']=top['initial_labels_sha256']
        fit=data[target_rows[0]['evidence']['fit_GT']['fit_manifest']['path']]
        fit['pilot_accessed']=True
        rejects(lambda:d.preflight('/synthetic/protocol'),'Fit manifest mismatch: pilot_accessed','pilot-contaminated fit manifest rejected')


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',required=True)
    root=Path(parser.parse_args().output).resolve(); root.mkdir(parents=True,exist_ok=False)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED_SOURCE
    graph_checks(root); numeric_checks(root); group_checks(); preflight_checks()
    report={'status':'PASS','source':{'path':str(SOURCE),'sha256':EXPECTED_SOURCE},
        'reviewer_script':{'path':str(Path(__file__).resolve()),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        'protocol':{'path':str(PROTOCOL),'sha256':hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()},
        'scope':'Tiny generated graph and numeric arrays plus hand-built mocked metadata; no actual graph, GT, labels, count rows or ANN.',
        'checks':CHECKS,'check_count':len(CHECKS),'actual_numerical_inputs_read':False,'ANN_executed':False}
    with (root/'report.json').open('x') as f: json.dump(report,f,indent=2,allow_nan=False); f.write('\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()

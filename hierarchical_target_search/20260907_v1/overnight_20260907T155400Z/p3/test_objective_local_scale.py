#!/usr/bin/env python3
"""Tiny generated/reference tests; no actual graph, GT, label or count reads."""
import argparse
from collections import Counter
import copy
from fractions import Fraction
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
from unittest.mock import patch

import numpy as np

SOURCE=Path(__file__).with_name('diagnose_objective_local_scale.py')
spec=importlib.util.spec_from_file_location('local_scale_diagnostic',SOURCE)
d=importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
P0_SOURCE=SOURCE.parent.parent/'p0/audit_inputs.py'


def require(ok,message):
    if not ok:
        raise AssertionError(message)


def rejects(fn,phrase):
    try:
        fn()
    except ValueError as exc:
        require(phrase in str(exc),'Unexpected failure: '+str(exc)); return
    raise AssertionError('Expected failure: '+phrase)


def native_fixture(path,adj):
    n,k=adj.shape; dim=3
    parts=[struct.pack('<i',1),struct.pack('<qiibbB',n,dim,0,1,1,0),
           struct.pack('<ffffiiiiiq',1.,2.,.1,.5,5,0,64,k,0,10),struct.pack('<Q',n),b'\0'*(4*n),
           struct.pack('<Q',n),b'\0'*(4*n),struct.pack('<iQ',k,n*k)]
    offset=sum(map(len,parts)); parts+=[adj.astype('<i4').tobytes(),struct.pack('<Q',n*dim)]
    vector_offset=sum(map(len,parts))
    # Marker payload is never converted to a numeric base array by the audit.
    parts.append(bytes((i%251 for i in range(n*dim*4))))
    raw=b''.join(parts); path.write_bytes(raw)
    return raw,offset,vector_offset


def python_degrees(adj):
    n=len(adj); incoming=[0]*n; outgoing=[0]*n
    c={'invalid_edges':0,'padding':0,'valid_edges':0,'self_edges':0,'valid_nonself_edges':0}
    for u,row in enumerate(adj.tolist()):
        for v in row:
            if v==-1:
                c['padding']+=1
            elif v<0 or v>=n:
                raise ValueError('invalid')
            else:
                c['valid_edges']+=1
                if v==u:
                    c['self_edges']+=1
                else:
                    c['valid_nonself_edges']+=1; incoming[v]+=1; outgoing[u]+=1
    return incoming,outgoing,[a+b for a,b in zip(incoming,outgoing)],c


def test_native_scan(root):
    adj=np.array([[1,1,0,-1],[0,2,1,-1],[3,-1,-1,-1],[1,-1,-1,-1]],dtype=np.int32)
    path=root/'native_graph.bin'; raw,offset,vector_offset=native_fixture(path,adj)
    parser=d.import_header(d.desc(P0_SOURCE))
    header=parser(path)
    require(header['adjacency_offset']==offset and offset%4!=0 and header['vector_offset']==vector_offset,
            'Native unaligned header/adjacency offset')
    reference=python_degrees(adj)
    require(reference[:3]==([1,3,1,1],[2,2,1,1],[3,5,2,2]),'Independent directed multiplicity reference')
    original_open=Path.open; ranges=[]
    class AdjacencyOnly(io.BytesIO):
        def read(self,size=-1):
            require(size>=0 and offset<=self.tell() and self.tell()+size<=offset+adj.size*4,
                    'Numeric read outside adjacency payload')
            ranges.append((self.tell(),size)); return super().read(size)
        def seek(self,off,whence=0):
            require(whence==0 and off==offset,'Numeric scan may seek only to adjacency start')
            return super().seek(off,whence)
    def guarded_open(p,*args,**kwargs):
        if p.resolve()==path.resolve():
            return AdjacencyOnly(raw)
        return original_open(p,*args,**kwargs)
    with patch.object(Path,'open',guarded_open):
        got=d.scan_adjacency(path,header,row_block=2)
    require([got[i].tolist() for i in range(3)]==list(reference[:3]) and got[3]==reference[3],
            'Blocked directed in/out counts differ from independent loops')
    require(got[4]['sum_in']==got[4]['sum_out']==6 and got[4]['sum_total']==12 and
            ranges==[(offset,32),(offset+32,32)],'Conservation or exact bounded reads')
    require(d.sha(path)==hashlib.sha256(raw).hexdigest(),'Full provenance SHA includes uninterpreted payload bytes')
    for invalid in (-2,4):
        bad=adj.copy(); bad[0,0]=invalid
        badp=root/f'invalid_{invalid}.bin'; native_fixture(badp,bad)
        rejects(lambda:d.scan_adjacency(badp,parser(badp),row_block=2),'Invalid adjacency ID')
    short=root/'short.bin'; short.write_bytes(raw[:offset+10])
    rejects(lambda:d.scan_adjacency(short,header,row_block=2),'Short bounded adjacency')
    # Directed duplicates, high indegree and arbitrary row blocks with independent loops.
    rng=np.random.default_rng(7)
    for n in (10,17,33):
        a=rng.integers(-1,n,size=(n,9),dtype=np.int32)
        a[1:,0:3]=0  # Many duplicate arcs into one node, no deduplication.
        p=root/f'random_{n}.bin'; native_fixture(p,a)
        result=d.scan_adjacency(p,parser(p),row_block=7)
        ref=python_degrees(a)
        require([result[i].tolist() for i in range(3)]==list(ref[:3]) and result[3]==ref[3],
                'Random generated directed count reference mismatch')


def independent_summary(incoming,outgoing,total,freq,mask,M,q):
    ids=[i for i,yes in enumerate(mask) if yes]
    good=[i for i in ids if int(total[i])*(9*q)<M]
    n=len(ids); occurrences=sum(int(freq[i]) for i in ids)
    z={'node_count':n,'fit_target_occurrences':occurrences,'condition_node_count':len(good),
       'condition_node_fraction':len(good)/n if n else None,
       'condition_fit_occurrences':sum(int(freq[i]) for i in good),
       'condition_fit_occurrence_weighted_fraction':sum(int(freq[i]) for i in good)/occurrences if occurrences else None}
    for name,values in (('in',incoming),('out',outgoing),('total',total)):
        selected=[int(values[i]) for i in ids]
        z[name+'_degree']={'mean':sum(selected)/n if n else None,'min':min(selected) if n else None,'max':max(selected) if n else None}
    sorted_degrees=sorted(int(total[i]) for i in ids)
    z['total_degree_quantiles']=[]
    for p in d.QUANTILES:
        frac=Fraction(str(p))
        rank=max(0,-(-(frac.numerator*n)//frac.denominator)-1) if n else None
        z['total_degree_quantiles'].append({'p':p,'degree':sorted_degrees[rank] if n else None,'zero_based_order_index':rank})
    return z


def test_condition_groups_histogram(root):
    degrees=np.array([0,1,2,50000],dtype=np.int64)
    require(d.exact_condition(degrees,180000,20000).tolist()==[True,False,False,False],
            'Strict equality excluded or int64 multiplication failed')
    require(d.exact_condition(np.array([1,2],dtype=np.int64),180001,20000).tolist()==[True,False],
            'Exact integer near-boundary test')
    rejects(lambda:d.exact_condition(np.array([2**62],dtype=np.int64),180000,20000),'overflow int64')
    # Sparse histogram handles a huge degree without a dense max-degree allocation.
    vals=np.array([0,10**12],dtype=np.int64); counts=np.array([3,2],dtype=np.int64)
    with patch.object(np,'bincount',side_effect=AssertionError('No dense degree histogram allowed')):
        histogram=d.compact_histogram(vals,counts)
        require(histogram['pairs']==[[0,3],[10**12,2]],'Sparse histogram loses large degree')
        require(histogram['encoded_pair_array_bytes']==len(json.dumps(histogram['pairs'],separators=(',',':'))),'Histogram byte accounting')
        require(not d.compact_histogram(vals,counts,limit=8)['included'],'Histogram limit omission')
        metadata_cap=d.compact_histogram(vals,counts,limit=histogram['encoded_pair_array_bytes']+1)
        require(not metadata_cap['included'] and 'including metadata/newline' in metadata_cap['reason'],
                'Byte cap must include full artifact metadata/newline, not only pairs')
        binding=d.persist_histogram(root/'sparse_histogram.json',histogram)
        payload=(root/'sparse_histogram.json').read_bytes()
        require(binding['artifact']['bytes']==len(payload)<=d.HISTOGRAM_LIMIT and
                binding['artifact']['sha256']==hashlib.sha256(payload).hexdigest() and
                json.loads(payload)==histogram and 'pairs' not in binding,
                'Standalone histogram full-byte cap/hash or no-duplication descriptor')
        omitted=d.persist_histogram(root/'omitted_histogram.json',metadata_cap)
        require(not omitted['included'] and not (root/'omitted_histogram.json').exists(),'Omitted histogram must create no artifact')
        sparse=d.quantiles_from_sparse(vals,counts)
        require([x['degree'] for x in sparse]==[0,0,0,10**12,10**12,10**12,10**12,10**12], 'Exact inverted-CDF rank rule')
        require(all(x['degree'] is None for x in d.quantiles_from_sparse(np.array([],dtype=np.int64),np.array([],dtype=np.int64))),
                'Empty empirical quantile must be null')
    n=16; q=3; M=55
    incoming=np.array([0,1,4,2,1,0,9,3,1,1,2,0,1,4,3,2],dtype=np.int64)
    outgoing=np.array([1,2,0,1,1,0,2,0,1,0,3,1,2,0,3,2],dtype=np.int64)
    total=incoming+outgoing
    frequency=np.array([3]*10+[0]*6,dtype=np.int64)
    labels={'common_initial':np.arange(n,dtype=np.uint16)%4}
    labels['lambda0_final']=labels['common_initial'].copy(); labels['lambda0_final'][[0,1]]=labels['lambda0_final'][[1,0]]
    labels['lambda1_final']=labels['common_initial'].copy(); labels['lambda1_final'][[0,2,12]]=[2,0,3]
    flags={d.MOVEMENTS[0]:[labels['lambda0_final'][i]!=labels['common_initial'][i] for i in range(n)],
           d.MOVEMENTS[1]:[labels['lambda1_final'][i]!=labels['common_initial'][i] for i in range(n)],
           d.MOVEMENTS[2]:[labels['lambda1_final'][i]!=labels['lambda0_final'][i] for i in range(n)]}
    populations={'all':[True]*n,'seen':[v>0 for v in frequency],'unseen':[v==0 for v in frequency]}
    target={'unique_node_denominators':{name:sum(mask) for name,mask in populations.items()},
            'sum_fit_target_occurrences':30,'maximum_fit_query_occurrences_of_one_node':3,'movements':{}}
    for variable,change in flags.items():
        target['movements'][variable]={'unique_nodes':{name:{'changed':sum(a and b for a,b in zip(change,mask)),
                                                            'denominator':sum(mask)} for name,mask in populations.items()}}
    got,histogram,checks=d.all_summaries(incoming,outgoing,total,frequency,labels,M,q,target)
    require(len(got)==31 and checks['frequency_bins_disjoint_exhaustive'],'All 31 fixed groups retained')
    for group in got:
        if group['family']=='support':
            mask=populations[group['population']]
        elif group['family']=='frequency':
            lo,hi=group['frequency_interval_inclusive']; mask=[f>=lo and (hi is None or f<=hi) for f in frequency]
        else:
            ch=flags[group['variable']]; p=populations[group['population']]
            mask=[bool(pm and (change if group['state']=='changed' else not change)) for pm,change in zip(p,ch)]
        expected=independent_summary(incoming,outgoing,total,frequency,mask,M,q)
        require({k:group[k] for k in expected}==expected,'Independent summary mismatch: '+str(group))
    unseen=next(x for x in got if x['family']=='support' and x['population']=='unseen')
    require(unseen['condition_fit_occurrence_weighted_fraction'] is None,'Unseen weighted denominator is zero, not one')
    require(sum(x['node_count'] for x in got if x['family']=='frequency')==n,'Frequency bins lost nodes')
    require(histogram['pairs']==[[degree,count] for degree,count in sorted(Counter(map(int,total)).items())],
            'All-base sparse histogram differs from Counter')
    damaged=copy.deepcopy(target); damaged['movements'][d.MOVEMENTS[0]]['unique_nodes']['seen']['changed']+=1
    rejects(lambda:d.all_summaries(incoming,outgoing,total,frequency,labels,M,q,damaged),'movement count differs')
    damaged=copy.deepcopy(target); damaged['maximum_fit_query_occurrences_of_one_node']=2
    rejects(lambda:d.all_summaries(incoming,outgoing,total,frequency,labels,M,q,damaged),'total/max occurrence')
    return {'groups_checked_against_independent_reference':31,'nodes':n,'fixed_quantile_levels':list(d.QUANTILES)}


def test_saved_GT_labels(root):
    nodes=768; q=3
    gt=np.stack([np.arange(10,dtype='<i4')+i*3 for i in range(q)])
    gtpath=root/'fit.i32'; gt.tofile(gtpath)
    label=np.repeat(np.arange(256,dtype='<u2'),3)
    labelpath=root/'labels.u16'; label.tofile(labelpath)
    prepared={'fit':{'gt10_file':str(gtpath),'gt10_sha256':d.sha(gtpath)},
              'labels':{name:{**d.desc(labelpath),'rows':nodes,'bytes':2*nodes} for name in d.LABELS}}
    with patch.object(d,'Q',q):
        frequency,labels=d.load_fit_and_labels(prepared,nodes)
        expected=Counter(int(x) for row in gt for x in row)
        require(frequency.tolist()==[expected[i] for i in range(nodes)] and set(labels)==set(d.LABELS),'Saved GT occurrence reference')
        bad=gt.copy(); bad[0,1]=bad[0,0]; bad.tofile(gtpath); prepared['fit']['gt10_sha256']=d.sha(gtpath)
        rejects(lambda:d.load_fit_and_labels(prepared,nodes),'invalid/duplicate target')
        gt.tofile(gtpath); prepared['fit']['gt10_sha256']=d.sha(gtpath)
        badlabel=label.copy(); badlabel[0]=256; badlabel.tofile(labelpath)
        for b in prepared['labels'].values(): b['sha256']=d.sha(labelpath)
        rejects(lambda:d.load_fit_and_labels(prepared,nodes),'Invalid fixed final/common label')


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--output',required=True)
    root=Path(ap.parse_args().output).resolve(); root.mkdir(parents=True,exist_ok=False)
    original_open=Path.open; original_fromfile=np.fromfile; opened=[]
    def allowed(path):
        path=Path(path).resolve()
        require(path.is_relative_to(root) or path in (SOURCE.resolve(),P0_SOURCE.resolve()),'Non-synthetic data file opened: '+str(path))
        opened.append(str(path))
    def guarded_open(p,*args,**kwargs):
        allowed(p); return original_open(p,*args,**kwargs)
    def guarded_fromfile(p,*args,**kwargs):
        allowed(p); return original_fromfile(p,*args,**kwargs)
    with patch.object(Path,'open',guarded_open),patch.object(np,'fromfile',guarded_fromfile):
        test_native_scan(root)
        group_reference=test_condition_groups_histogram(root)
        test_saved_GT_labels(root)
        invalid_protocol=root/'invalid_protocol.json'; invalid_protocol.write_text('{}')
        rejects(lambda:d.preflight(invalid_protocol),'differs from frozen preregistration')
    summary={'status':'PASS','source':d.desc(SOURCE),'scope':'Generated fixtures only; source files allowed for import/hash; no actual graph/GT/labels/count rows.',
             'tests':['native_unaligned_header_parser','directed_duplicate_reciprocal_arcs','self_exclusion_and_minus1_padding',
                      'bounded_numeric_adjacency_reads_no_vector_payload','sum_in_out_M_total_2M','full_graph_checksum_uninterpreted_payload',
                      'invalid_negative_and_out_of_range_rejection','short_adjacency_read_rejection','three_random_generated_graph_reference_cases',
                      'strict_equality_excluded','int64_multiplication_50000_by180000','overflow_guard',
                      'sparse_histogram_huge_degree_no_dense_bincount','histogram_byte_limit_omit_with_reason',
                      'full_standalone_histogram_cap_includes_metadata_newline','histogram_file_hash_and_report_descriptor_no_pairs',
                      'omitted_histogram_creates_no_file','empty_and_endpoint_quantiles',
                      'exact_decimal_rational_quantile_rank','all31_group_independent_python_reference','all18_movement_cells',
                      'all10_frequency_bins','empty_weighted_denominator_null','movement_count_mismatch_rejection','fit_support_max_mismatch_rejection',
                      'GT10_frequency_Counter_reference','GT10_duplicate_rejection','label_range_rejection','protocol_SHA_rejection',
                      'fixture_only_Path_open_numpy_fromfile_guard'],
             'group_reference':group_reference,'guarded_file_calls':len(opened),'actual_inputs_read':False}
    d.write_new(root/'result.json',summary); print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()

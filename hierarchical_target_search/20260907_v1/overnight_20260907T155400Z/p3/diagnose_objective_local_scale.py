#!/usr/bin/env python3
"""Frozen read-only degree/support audit of D(u)*9Q < M after P3 NOPASS.

Numeric graph reads are bounded adjacency row blocks. A separately identified
streaming full-file SHA reads embedded-vector bytes only as uninterpreted
provenance bytes. No vector arithmetic, pilot GT, query vectors, ANN or fitting.
"""
from __future__ import annotations

import argparse
import datetime as dt
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

import numpy as np

PROTOCOL_SHA = 'abae80a4a2bbf6366e413b21a948a6fa4f27166e1160973cc223681e75cfff91'
P3_PROTOCOL_SHA = 'fea64bc3c6a8046378849f55508198dcfd9a00df880a74e9d93cf22d051a418f'
DATASET_N = {'webvid2_5m_light_v1': 2505000, 'yandex_t2i_official10M_ip_v1': 10000000}
Q, K, ROW_BLOCK = 20000, 10, 65536
LABELS = ('common_initial', 'lambda0_final', 'lambda1_final')
POPULATIONS = ('all', 'seen', 'unseen')
MOVEMENTS = ('lambda0_final_leaf_changed_from_initial', 'lambda1_final_leaf_changed_from_initial',
             'final_lambda1_vs_lambda0_leaf_difference')
FREQUENCY_BINS = ((0,0),(1,1),(2,2),(3,3),(4,4),(5,9),(10,19),(20,49),(50,99),(100,None))
QUANTILES = (0,.25,.5,.75,.9,.95,.99,1)
HISTOGRAM_LIMIT = 1 << 20
SOFT_DEADLINE = dt.datetime(2026,9,7,22,59,tzinfo=dt.timezone.utc).timestamp()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def deadline():
    require(time.time() < SOFT_DEADLINE, 'Objective local-scale audit soft deadline reached')


def sha(path, progress=None):
    h = hashlib.sha256()
    start = last = time.monotonic()
    size, done = Path(path).stat().st_size, 0
    with Path(path).open('rb') as f:
        while True:
            deadline()
            block = f.read(16 << 20)
            if not block:
                break
            h.update(block); done += len(block)
            if progress is not None:
                progress.update({'phase':'provenance_full_graph_SHA256','bytes_hashed':done,'graph_bytes':size})
            now = time.monotonic()
            if progress is not None and now-last >= 10:
                print(json.dumps({**progress,'wall_seconds':now-start}),flush=True); last=now
    return h.hexdigest()


def desc(path):
    return {'path':str(Path(path).resolve()),'sha256':sha(path)}


def read_json(path):
    return json.loads(Path(path).read_text())


def bound_path(binding):
    path=Path(binding['path']).resolve()
    require(sha(path)==binding['sha256'],'SHA256 mismatch: '+str(path))
    return path


def bound_json(binding):
    return read_json(bound_path(binding))


def expect(obj, values, where):
    for key,value in values.items():
        require(obj.get(key)==value,where+' mismatch: '+key)


def write_new(path,obj):
    with Path(path).open('x') as f:
        json.dump(obj,f,indent=2,allow_nan=False); f.write('\n')


def dataset_map(obj):
    require(len(obj['datasets'])==len(DATASET_N) and {x['dataset'] for x in obj['datasets']}==set(DATASET_N),
            'Missing, duplicate or extra dataset')
    return {x['dataset']:x for x in obj['datasets']}


def import_header(binding):
    path=bound_path(binding)
    spec=importlib.util.spec_from_file_location('frozen_P0_graph_header_for_degree_audit',path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.graph_header


def preflight(protocol_path):
    """Bound JSON/source metadata only; no original graph, labels, fit GT yet."""
    require(sha(protocol_path)==PROTOCOL_SHA,'Local-scale protocol differs from frozen preregistration')
    protocol=read_json(protocol_path)
    expect(protocol,{'status':'PREREGISTERED_BEFORE_IMPLEMENTATION_AND_ACTUAL_DEGREE_READS',
                     'stage':'P3_POST_NOGO_OBJECTIVE_LOCAL_SCALE','datasets':list(DATASET_N),'cpu_only':True,
                     'method_revision_increment':0,'P4_authorized':False,'P3_gate_reopened':False,
                     'new_model_or_auxgraph_authorized':False},'Local-scale protocol')
    require(protocol['support']['exact_frequency_bins']==[list(x) for x in FREQUENCY_BINS] and
            protocol['summaries']['quantile_levels']==list(QUANTILES) and
            protocol['movement_groups']['variables']==list(MOVEMENTS),'Fixed group/quantile definitions differ')
    require(protocol['P3_protocol']['sha256']==P3_PROTOCOL_SHA,'P3 protocol identity differs')
    bound_json(protocol['P3_protocol'])
    gate=bound_json(protocol['upstream_P3'])
    expect(gate,{'status':'NOPASS','stage':'P3','decision':'NO_GO_P3_SEARCH_TRANSFER',
                 'P4_P8_authorized':False,'validation_heldout_authorized':False},'P3 NOPASS gate')
    require(gate['protocol']==protocol['P3_protocol'],'Gate upstream protocol differs')
    audit=bound_json(protocol['P0_audit'])
    expect(audit,{'status':'PASS_INPUT_CONTRACT','heldout_accessed':False},'P0 audit')
    target=bound_json(protocol['target_diagnosis'])
    expect(target,{'status':'COMPLETE','stage':'P3_POST_NOGO_TARGET_GENERALIZATION','P3_gate_status_unchanged':'NOPASS'},'Target diagnosis')
    require(target['audit']==protocol['P0_audit'] and target['upstream_P3']==protocol['upstream_P3'],
            'Target diagnosis gate/audit differs')
    complete=bound_json(protocol['target_diagnosis_completion'])
    expect(complete,{'status':'COMPLETE','diagnosis':protocol['target_diagnosis'],'datasets':list(DATASET_N),
                     'P3_gate_status_unchanged':'NOPASS'},'Target diagnosis completion')
    algebra=bound_json(protocol['algebra'])
    require(algebra['status']=='COMPLETE_POSTHOC_ALGEBRA_ONLY' and algebra['protocol']==protocol['P3_protocol'] and
            algebra['gate']==protocol['upstream_P3'],'Completed algebra identity differs')
    review=bound_json(protocol['algebra_independent_review'])
    require(review['status']=='PASS_ALGEBRA_AND_METADATA_REVIEW' and review['source_analysis']==protocol['algebra'] and
            review['protocol']==protocol['P3_protocol'] and review['gate']==protocol['upstream_P3'],
            'Independent algebra review identity/status differs')
    maps=[dataset_map(x) for x in (audit,target,algebra,review)]
    prepared={}
    for dataset,nodes in DATASET_N.items():
        ad,td,al,rv=(m[dataset] for m in maps)
        require(td['status']=='COMPLETE' and td['nodes']==nodes and td['fit_queries']==Q and
                ad['graph']['header']['n']==nodes and al['N']==rv['N']==nodes and al['Q_fit']==rv['Q']==Q,
                'Frozen node/fit count differs')
        require(al['partition_manifest']==td['evidence']['partition_manifest'],'Algebra/target partition binding differs')
        top=bound_json(al['partition_manifest'])
        expect(top,{'status':'COMPLETE','stage':'P3','dataset':dataset,'nodes':nodes,'regions':256,
                    'protocol_sha256':P3_PROTOCOL_SHA,'input_audit_sha256':protocol['P0_audit']['sha256']},'Partition metadata')
        M=top['initial_objective']['M_original_directed_valid_nonself_slots']
        require(M==al['M_directed_valid_nonself']==rv['M'] and top['initial_objective']['Q']==Q and
                top['input_graph_sha256']==ad['graph']['sha256']==ad['graph']['expected_sha256'],
                'Frozen M/Q/graph identities differ')
        labels={name:td['evidence']['saved_labels_rehashed'][name] for name in LABELS}
        expected_labels={'common_initial':top['initialization']['labels'],
                         'lambda0_final':top['lambda0']['passes'][1]['labels'],
                         'lambda1_final':top['lambda1']['passes'][1]['labels']}
        for name,record in labels.items():
            part=expected_labels[name]
            require(record['path']==part['path'] and record['sha256']==part['sha256'] and
                    record['rows']==nodes and record['bytes']==2*nodes,'Target/partition saved label identity differs')
        require(labels['common_initial']['sha256']==top['initial_labels_sha256'] and
                all(top[f'lambda{lam}']['initial_labels_sha256']==top['initial_labels_sha256'] for lam in (0,1)),
                'Branches lack common initialization')
        fit_binding=td['evidence']['fit_GT']['fit_manifest']; fit=bound_json(fit_binding)
        expect(fit,{'status':'COMPLETE','stage':'P3','dataset':dataset,'fit_count':Q,'fit_range':[10000,10000+Q],
                    'input_audit_sha256':protocol['P0_audit']['sha256'],'protocol_sha256':P3_PROTOCOL_SHA,
                    'pilot_accessed':False,'heldout_accessed':False,'fit_gt_values_sha256':ad['fit']['gt_values_sha256']},'Fit manifest')
        require(top['fit_manifest_sha256']==fit_binding['sha256'] and ad['fit']['n']==Q and ad['fit']['row_range']==[10000,10000+Q],
                'P0/partition fit extraction identity differs')
        require(td['evidence']['fit_GT']['gt10']=={'path':fit['gt10_file'],'sha256':fit['gt10_sha256']},
                'Target diagnostic GT10 binding differs')
        prepared[dataset]={'audit':ad,'target':td,'algebra':al,'review':rv,'partition':top,'M':M,
                           'fit_binding':fit_binding,'fit':fit,'labels':labels}
    return protocol,prepared,import_header(protocol['P0_header_parser_source'])


def scan_adjacency(path,header,progress=None,row_block=ROW_BLOCK):
    """Unaligned little-endian int32 decode confined to the adjacency payload."""
    n,k=header['n'],header['degree']
    require(n>0 and k>0 and row_block>0 and header['neighbor_count']==n*k,'Invalid bounded adjacency shape')
    incoming=np.zeros(n,dtype=np.int64); outgoing=np.zeros(n,dtype=np.int64)
    counts={'invalid_edges':0,'padding':0,'valid_edges':0,'self_edges':0,'valid_nonself_edges':0}
    start=last=time.monotonic(); physical=0
    with Path(path).open('rb',buffering=0) as f:
        f.seek(header['adjacency_offset'])
        for begin in range(0,n,row_block):
            deadline()
            rows=min(row_block,n-begin); wanted=rows*k*4
            raw=f.read(wanted)
            require(len(raw)==wanted,'Short bounded adjacency row block')
            physical+=len(raw)
            a=np.frombuffer(raw,dtype='<i4').reshape(rows,k)
            invalid=(a < -1)|(a >= n)
            require(not np.any(invalid),'Invalid adjacency ID: only -1 padding and in-range node IDs allowed')
            padding=a==-1
            self_edges=a==np.arange(begin,begin+rows,dtype=np.int64)[:,None]
            valid=(a>=0)&~self_edges
            counts['padding']+=int(padding.sum())
            counts['valid_edges']+=int(np.count_nonzero(a>=0))
            counts['self_edges']+=int(self_edges.sum())
            count=int(valid.sum()); counts['valid_nonself_edges']+=count
            outgoing[begin:begin+rows]=valid.sum(axis=1,dtype=np.int64)
            # This dense allocation is indexed by validated node IDs (exactly n),
            # never by max degree. Duplicate arcs increment their target repeatedly.
            incoming+=np.bincount(a[valid],minlength=n)
            if progress is not None:
                progress.update({'phase':'adjacency_numeric_scan','next_node_cursor':begin+rows,
                                 'nodes':n,'adjacency_bytes_read':physical,'M_so_far':counts['valid_nonself_edges']})
            now=time.monotonic()
            if progress is not None and now-last>=10:
                print(json.dumps({**progress,'wall_seconds':now-start}),flush=True); last=now
        require(f.tell()==header['adjacency_offset']+n*k*4,'Numeric graph reader crossed adjacency boundary')
    M=counts['valid_nonself_edges']
    require(counts['padding']+counts['valid_edges']==n*k and counts['valid_edges']==M+counts['self_edges'],
            'Adjacency slot accounting fails')
    require(int(incoming.sum())==int(outgoing.sum())==M,'Directed in/out conservation fails')
    total=incoming+outgoing
    require(int(total.sum())==2*M,'Total in+out degree conservation fails')
    return incoming,outgoing,total,counts,{'numeric_bytes_read':physical,'numeric_byte_range':[header['adjacency_offset'],header['adjacency_offset']+physical],
                                           'read_past_adjacency':False,'row_block_max':row_block,'wall_seconds':time.monotonic()-start,
                                           'sum_in':int(incoming.sum()),'sum_out':int(outgoing.sum()),'sum_total':int(total.sum())}


def exact_condition(total,M,q):
    require(M>0 and q>0 and np.issubdtype(total.dtype,np.signedinteger) and np.all(total>=0),'Invalid degree/M/Q for strict condition')
    require(int(total.max()) <= np.iinfo(np.int64).max//(9*q),'D*9Q would overflow int64')
    return total.astype(np.int64,copy=False)*(9*q) < M


def quantiles_from_sparse(values,counts,levels=QUANTILES):
    n=int(counts.sum())
    if not n:
        return [{'p':p,'degree':None,'zero_based_order_index':None} for p in levels]
    cumulative=np.cumsum(counts,dtype=np.int64)
    result=[]
    for p in levels:
        frac=Fraction(str(p))
        require(0<=frac<=1,'Quantile level outside unit interval')
        rank=max(0,(frac.numerator*n+frac.denominator-1)//frac.denominator-1)
        result.append({'p':p,'degree':int(values[np.searchsorted(cumulative,rank+1,side='left')]),'zero_based_order_index':rank})
    return result


def compact_histogram(values,counts,limit=HISTOGRAM_LIMIT):
    """Sparse degree values only, with a byte bound before list/JSON expansion."""
    require(len(values)==len(counts),'Sparse histogram shape mismatch')
    # Minimal pair JSON is at least six bytes; this avoids expanding very large
    # unique-value sets into Python objects simply to discover they exceed 1MiB.
    if len(values)*6+2>limit:
        return {'included':False,'reason':'Sparse histogram necessarily exceeds byte limit','limit_bytes':limit,
                'distinct_degrees':len(values),'encoding':'JSON array of [degree,node_count] pairs'}
    pairs=[]; used=2
    for degree,count in zip(values,counts):
        pair=[int(degree),int(count)]
        encoded=json.dumps(pair,separators=(',',':'))
        used+=len(encoded)+(1 if pairs else 0)
        if used>limit:
            return {'included':False,'reason':'Exact sparse histogram JSON exceeds byte limit','limit_bytes':limit,
                    'distinct_degrees':len(values),'encoding':'JSON array of [degree,node_count] pairs'}
        pairs.append(pair)
    result={'included':True,'limit_bytes':limit,'encoded_pair_array_bytes':used,'distinct_degrees':len(values),
            'encoding':'JSON array of [degree,node_count] pairs','pairs':pairs}
    encoded=(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')
    if len(encoded)>limit:
        return {'included':False,'reason':'Complete compact histogram artifact, including metadata/newline, exceeds byte limit',
                'limit_bytes':limit,'distinct_degrees':len(values),'encoding':result['encoding']}
    return result


def persist_histogram(path,histogram):
    """Only a checksum-bound descriptor enters reports; pairs occur once on disk."""
    if not histogram['included']:
        return histogram
    data=(json.dumps(histogram,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')
    require(len(data)<=histogram['limit_bytes'],'Complete standalone histogram exceeds frozen byte cap')
    with Path(path).open('xb') as f:
        f.write(data)
    return {'included':True,'artifact':{'path':str(Path(path).resolve()),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)},
            'limit_bytes':histogram['limit_bytes'],'distinct_degrees':histogram['distinct_degrees'],
            'encoding':histogram['encoding'],'pair_values_duplicated_in_report':False,
            'cap_applies_to_complete_serialized_artifact_including_metadata_and_newline':True}


def summarize_group(incoming,outgoing,total,frequency,satisfies,mask):
    n=int(np.count_nonzero(mask)); occurrences=int(frequency[mask].sum(dtype=np.int64))
    good=mask&satisfies
    good_n=int(good.sum()); good_occ=int(frequency[good].sum(dtype=np.int64))
    result={'node_count':n,'fit_target_occurrences':occurrences,'condition_node_count':good_n,
            'condition_node_fraction':good_n/n if n else None,'condition_fit_occurrences':good_occ,
            'condition_fit_occurrence_weighted_fraction':good_occ/occurrences if occurrences else None}
    for name,arr in (('in',incoming),('out',outgoing),('total',total)):
        x=arr[mask]
        result[name+'_degree']={'mean':float(x.mean()) if n else None,'min':int(x.min()) if n else None,'max':int(x.max()) if n else None}
    # Unique does not allocate up to max(degree); it sorts only this group's n values.
    vals,counts=np.unique(total[mask],return_counts=True)
    result['total_degree_quantiles']=quantiles_from_sparse(vals,counts)
    return result,(vals,counts)


def label_change_masks(labels):
    return {MOVEMENTS[0]:labels['lambda0_final']!=labels['common_initial'],
            MOVEMENTS[1]:labels['lambda1_final']!=labels['common_initial'],
            MOVEMENTS[2]:labels['lambda1_final']!=labels['lambda0_final']}


def all_summaries(incoming,outgoing,total,frequency,labels,M,q,target_population,progress=None):
    satisfies=exact_condition(total,M,q)
    support={'all':np.ones(len(total),dtype=bool),'seen':frequency>0,'unseen':frequency==0}
    require({g:int(mask.sum()) for g,mask in support.items()}==target_population['unique_node_denominators'],
            'Fit-support unique node counts differ from completed target diagnosis')
    require(int(frequency.sum(dtype=np.int64))==q*K==target_population['sum_fit_target_occurrences'] and
            int(frequency.max())==target_population['maximum_fit_query_occurrences_of_one_node'],
            'Fit-support total/max occurrence differs from completed target diagnosis')
    groups=[]; histogram=None
    for name,mask in support.items():
        deadline(); summary,sparse=summarize_group(incoming,outgoing,total,frequency,satisfies,mask)
        groups.append({'family':'support','population':name,**summary})
        if name=='all':
            histogram=compact_histogram(*sparse)
    bin_union=np.zeros(len(total),dtype=np.uint8)
    for lo,hi in FREQUENCY_BINS:
        deadline(); mask=(frequency>=lo)&((frequency<=hi) if hi is not None else True)
        bin_union+=mask
        summary,_=summarize_group(incoming,outgoing,total,frequency,satisfies,mask)
        groups.append({'family':'frequency','frequency_interval_inclusive':[lo,hi],**summary})
    require(np.all(bin_union==1),'Frequency bins do not exhaust nodes exactly once')
    changes=label_change_masks(labels)
    movement_checks={}
    for variable,change in changes.items():
        movement_checks[variable]={}
        for population,pmask in support.items():
            expected=target_population['movements'][variable]['unique_nodes'][population]
            actual_changed=int(np.count_nonzero(change&pmask)); denominator=int(pmask.sum())
            require(expected['changed']==actual_changed and expected['denominator']==denominator,
                    'Final label movement count differs from completed target diagnosis: '+variable+'/'+population)
            movement_checks[variable][population]={'changed':actual_changed,'unchanged':denominator-actual_changed,
                                                   'denominator':denominator,'matches_completed_target_diagnosis':True}
            pair=[]
            for state,smask in (('changed',change),('unchanged',~change)):
                deadline()
                summary,_=summarize_group(incoming,outgoing,total,frequency,satisfies,pmask&smask)
                pair.append(summary)
                groups.append({'family':'movement','variable':variable,'state':state,'population':population,**summary})
                if progress is not None:
                    progress.update({'phase':'fixed_group_summaries','groups_completed':len(groups),'last_group':variable+'/'+state+'/'+population})
            require(sum(x['node_count'] for x in pair)==denominator and
                    sum(x['fit_target_occurrences'] for x in pair)==int(frequency[pmask].sum(dtype=np.int64)),
                    'Changed/unchanged groups do not exhaust support population')
    require(len(groups)==31,'All 3 support,10 frequency,18 movement groups required')
    require(sum(x['node_count'] for x in groups if x['family']=='frequency')==len(total),'Frequency node-count conservation fails')
    return groups,histogram,{'support_counts_match_target':True,'fit_occurrences_match_target':True,
                             'frequency_bins_disjoint_exhaustive':True,'movement_groups':movement_checks,
                             'condition_degree_cutoff_exclusive_fraction':f'{M}/{9*q}',
                             'first_integer_degree_not_satisfying':(M+9*q-1)//(9*q),
                             'strict_equality_excluded':True,'condition_arithmetic':'int64 D*(9Q)<M after explicit overflow check'}


def load_fit_and_labels(prepared,nodes):
    fit=prepared['fit']; fp=Path(fit['gt10_file']).resolve()
    require(fp.stat().st_size==Q*K*4 and sha(fp)==fit['gt10_sha256'],'Fit GT10 shape/SHA differs')
    gt=np.fromfile(fp,dtype='<i4').reshape(Q,K)
    require(int(gt.min())>=0 and int(gt.max())<nodes and np.all(np.diff(np.sort(gt,axis=1),axis=1)!=0),
            'Fit GT10 invalid/duplicate target ID')
    frequency=np.bincount(gt.ravel(),minlength=nodes).astype(np.int64)
    require(np.all(frequency[gt]>0),'Fit target must be seen')
    labels={}
    for name,binding in prepared['labels'].items():
        deadline(); path=bound_path(binding)
        require(path.stat().st_size==2*nodes,'Label byte shape differs')
        arr=np.fromfile(path,dtype='<u2')
        require(len(arr)==nodes and int(arr.max())<256,'Invalid fixed final/common label ID')
        sizes=np.bincount(arr,minlength=256)
        require(int(sizes.min())>=3 and int(sizes.max())<=6*nodes//(5*256) and
                int(sizes.reshape(16,16).sum(axis=1).max())<=6*nodes//(5*16),'Labels violate saved capacities/minimum3')
        labels[name]=arr
    return frequency,labels


def file_identity(path):
    s=Path(path).stat()
    return {'device':s.st_dev,'inode':s.st_ino,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}


def diagnose_dataset(dataset,prepared,header_parser,progress,output):
    start=time.monotonic(); nodes=DATASET_N[dataset]
    graph=prepared['audit']['graph']; path=Path(graph['path']).resolve()
    identity=file_identity(path)
    progress.update({'dataset':dataset,'phase':'provenance_full_graph_SHA256'})
    hash_start=time.monotonic(); graph_sha=sha(path,progress); hash_seconds=time.monotonic()-hash_start
    require(graph_sha==graph['sha256']==graph['expected_sha256'],'Full frozen native graph SHA mismatch')
    info_path=Path(graph['info_path']).resolve()
    require(sha(info_path)==graph['info_sha256'],'Frozen graph info JSON SHA mismatch')
    header=header_parser(path)
    require(header==graph['header'] and header['n']==nodes and header['degree']==64,'Fresh native header differs from P0')
    frequency,labels=load_fit_and_labels(prepared,nodes)
    incoming,outgoing,total,counts,scan=scan_adjacency(path,header,progress)
    require({key:counts[key] for key in ('invalid_edges','padding','valid_edges','self_edges')}==graph['adjacency_scan'],
            'Original directed slot counts differ from P0')
    require(counts['valid_nonself_edges']==prepared['M'],'Measured M differs from frozen partition/algebra')
    group_start=time.monotonic()
    groups,histogram,checks=all_summaries(incoming,outgoing,total,frequency,labels,prepared['M'],Q,
        prepared['target']['node_population_and_pilot_target_slots'],progress)
    require(file_identity(path)==identity,'Graph file identity changed during read-only audit')
    histogram_binding=persist_histogram(Path(output)/(dataset+'.total_degree_histogram.json'),histogram)
    return {'schema_version':1,'status':'COMPLETE','stage':'P3_POST_NOGO_OBJECTIVE_LOCAL_SCALE','dataset':dataset,
            'N':nodes,'M_directed_valid_nonself':prepared['M'],'Q_fit':Q,'sufficient_condition':'D(u)*(9*Q) < M, strict integer arithmetic',
            'degree_definition':'Original directed valid nonself incoming+outgoing slots, duplicate arcs retained.',
            'groups':groups,'total_degree_sparse_histogram':histogram_binding,'integrity':{'P0_slot_counts':counts,
                'degree_conservation':scan,'support_and_movement':checks,'graph_file_identity_stable':True,
                'fit_unique10_each_query_validated':True,'numeric_vectors_read':False,'pilot_GT_read':False},
            'inputs':{'graph':{'path':str(path),'sha256':graph_sha,'fresh_full_file_SHA256':True,
                               'checksum_includes_uninterpreted_embedded_vector_bytes':True,'header':header,'file_identity':identity},
                      'graph_info':{'path':str(info_path),'sha256':graph['info_sha256']},
                      'fit_manifest':prepared['fit_binding'],'fit_GT10':{'path':prepared['fit']['gt10_file'],'sha256':prepared['fit']['gt10_sha256']},
                      'labels':prepared['labels'],'partition_manifest':prepared['algebra']['partition_manifest']},
            'cost':{'full_graph_SHA256_seconds':hash_seconds,'adjacency_numeric_scan_seconds':scan['wall_seconds'],
                    'fixed_group_summary_seconds':time.monotonic()-group_start,'total_wall_seconds':time.monotonic()-start},
            'quantile_method':'Exact empirical inverted CDF, index max(0,ceil(p*n)-1), fixed decimal-rational levels; no interpolation.',
            'weighted_denominator':'Fit target occurrences sum f(u), not unique nodes or independent queries; zero denominator null.',
            'movement_interpretation':'Final-state label differences, not accepted sequential moves or temporal counterfactuals.',
            'P3_gate_status_unchanged':'NOPASS','new_CI_or_model_or_gate':False}


def run(args):
    deadline(); started=time.monotonic()
    output=Path(args.output).resolve(); output.mkdir(parents=True,exist_ok=False)
    progress={'phase':'metadata_preflight','dataset':None}
    invocation={'status':'INCOMPLETE','schema_version':1,'stage':'P3_POST_NOGO_OBJECTIVE_LOCAL_SCALE',
                'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'argv':sys.argv,'script':desc(__file__),
                'protocol':desc(args.protocol),'cpu_only':True}
    write_new(output/'invocation.json',invocation)
    try:
        protocol,prepared,header_parser=preflight(args.protocol)
        results=[]
        for dataset in DATASET_N:
            deadline(); result=diagnose_dataset(dataset,prepared[dataset],header_parser,progress,output)
            write_new(output/(dataset+'.json'),result); results.append(result)
            print(json.dumps({'dataset':dataset,'status':'COMPLETE','wall_seconds':result['cost']['total_wall_seconds']}),flush=True)
        report={**invocation,'status':'COMPLETE','datasets':results,'bindings':{k:protocol[k] for k in
            ('upstream_P3','P3_protocol','P0_audit','P0_header_parser_source','target_diagnosis','target_diagnosis_completion','algebra','algebra_independent_review')},
            'scope':protocol['scope'],'interpretation_limits':protocol['interpretation_limits'],
            'access':{'numeric_graph_adjacency_only':True,'full_graph_checksum_only_reads_embedded_vectors':True,
                      'existing_fit_GT10_only':True,'labels_only_common_initial_and_two_finals':True,
                      'pilot_GT':False,'query_vectors':False,'standalone_base_vectors':False,'validation':False,'heldout':False,
                      'ANN':False,'graph_or_partition_writes':False,'model_changes':False},
            'P3_gate_status_unchanged':'NOPASS','P4_authorized':False,'new_CI_computed':False,'automatic_GO':False,
            'wall_seconds':time.monotonic()-started}
        write_new(output/'diagnosis.json',report)
        write_new(output/'complete.json',{'status':'COMPLETE','diagnosis':desc(output/'diagnosis.json'),
                                          'datasets':list(DATASET_N),'P3_gate_status_unchanged':'NOPASS'})
        return 0
    except BaseException as exc:
        write_new(output/'failure.json',{'status':'INCOMPLETE','error_type':type(exc).__name__,'error':str(exc),
                                         'last_progress':progress,'wall_seconds':time.monotonic()-started,'P3_gate_status_unchanged':'NOPASS'})
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--protocol',required=True,help='Frozen objective_local_scale_protocol_v1.json')
    p.add_argument('--output',required=True,help='New output directory; preserves interrupted/older artifacts')
    return run(p.parse_args())


if __name__=='__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import os
import subprocess
import time
from common import DATASETS, RUN, dump, identity, read, sha
from model_config import baseline, method

parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['cal','audit'],required=True);args=parser.parse_args()
env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
jobs=[]
for dataset in DATASETS:
    trained=read(RUN/'models'/dataset/'complete.json')
    assert trained['status']=='ALL_CANDIDATES_TRAINED_BEFORE_CAL'
    for x in trained['models']:assert sha(x['W'])==x['W_sha256']
    if args.stage=='cal':
        candidates=trained['models'];splits=['fit_probe','cal']
    else:
        selected=read(RUN/'models'/dataset/'selection.json')
        candidates=list(selected['selected_new_candidates'].values());splits=['audit']
    for split in splits:
        models=[baseline(dataset)]+candidates
        config=read(RUN/'inputs'/dataset/split/'config.json')
        config.update({'measure_wall':False,'methods':[method(dataset,x,exact=exact) for x in models for exact in [False,True]],'threads':1})
        config_path=RUN/'diagnostics'/f'{dataset}_{split}.json';assert not config_path.exists()
        dump(config_path,config)
        output=RUN/'diagnostics'/dataset/split;output.parent.mkdir(exist_ok=True)
        binary='evaluate' if args.stage=='cal' else 'evaluate_v2'
        cmd=[str(RUN/'bin'/binary),str(config_path),str(output)]
        started=time.monotonic()
        with (RUN/'logs'/f'{dataset}_{split}.log').open('w') as log:
            proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
            dump(RUN/'state.json',{'status':'DIAGNOSTICS_RUNNING','dataset':dataset,'split':split,
                                  'pid':proc.pid,'argv':cmd,'completed_jobs':jobs})
            code=proc.wait()
        jobs.append({'dataset':dataset,'split':split,'argv':cmd,'exit_code':code,'process_seconds':time.monotonic()-started})
        dump(RUN/'diagnostics'/f'{args.stage}_jobs.json',jobs)
        assert code==0,f'{split} failed for {dataset}'
        print(dataset,split,'COMPLETE',flush=True)
    if args.stage=='cal':
        results=read(RUN/'diagnostics'/dataset/'cal/results.json')
        assert results['status']=='COMPLETE' and results['threads']==1
        by_name={x['configuration']['model_name']:x for x in results['methods'] if not x['configuration']['exact']}
        fast=by_name['fast20k_3']
        chosen={};including={}
        for family in ['full','rank8']:
            group=[x for x in candidates if x['family']==family]
            winner=min(group,key=lambda x:(-by_name[x['name']]['total_hits'],by_name[x['name']]['mean_graph_ndc'],-x['lambda']))
            chosen[family]=winner
            metric=by_name[winner['name']]
            better=(metric['total_hits']>fast['total_hits'] or
                    (metric['total_hits']==fast['total_hits'] and metric['mean_graph_ndc']<fast['mean_graph_ndc']))
            including[family]=winner['name'] if better else 'fast20k_3'
        dump(RUN/'models'/dataset/'selection.json',{'status':'SELECTED_BEFORE_AUDIT_AND_VALIDATION',
             'rule':'cal HNSW true joint hits descending, graph NDC ascending, lambda descending',
             'selected_new_candidates':chosen,'best_including_fast':including,
             'cal_results':identity(RUN/'diagnostics'/dataset/'cal/results.json'),
             'audit_used_for_selection':False,'validation_used_for_selection':False,'heldout_used':False})
        print(dataset,'SELECTED', {k:v['name'] for k,v in chosen.items()},flush=True)
dump(RUN/'state.json',{'status':('CAL_SELECTION_COMPLETE' if args.stage=='cal' else 'AUDIT_COMPLETE'),
                       'jobs':jobs,'protocol_sha256':sha(RUN/'protocol.md')})

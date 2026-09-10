#!/usr/bin/env python3
"""Sequential real-data P1 verification; these timings are an audit, not a gain claim."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/data/netg/ACSG')
RUN = Path(__file__).resolve().parents[1]

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def check_time():
    if time.time() >= dt.datetime(2026,9,7,22,59,tzinfo=dt.timezone.utc).timestamp():
        raise RuntimeError('Research deadline closed')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evaluator',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--fast-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--queries',type=int,default=512)
    a=p.parse_args()
    check_time()
    a.output.mkdir(parents=True,exist_ok=False)
    audit=json.loads(a.audit.read_text())
    if audit['status']!='PASS_INPUT_CONTRACT':raise ValueError('Full audit required')
    result={'stage':'P1','status':'INCOMPLETE','purpose':'correctness and measurement audit only',
            'cpu_only':True,'heldout_accessed':False,'evaluator_sha256':digest(a.evaluator),
            'script_sha256':digest(Path(__file__)),'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'datasets':[],'invocations':[]}
    def save():
        tmp=a.output/'report.tmp.json';tmp.write_text(json.dumps(result,indent=2)+'\n');tmp.replace(a.output/'report.json')
    save()
    def invoke(name,args):
        check_time()
        out=a.output/(name+'.json')
        cmd=[str(a.evaluator.resolve()),*args,'--output',str(out.resolve())]
        item={'name':name,'command':cmd,'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'RUNNING'}
        result['invocations'].append(item);save()
        print('P1_INVOKE',name,flush=True)
        with (a.output/(name+'.log')).open('xb') as f:
            child=subprocess.Popen(cmd,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
            item.update(pid=child.pid,pgid=os.getpgid(child.pid));save()
            item['returncode']=child.wait()
        item.update(ended_utc=dt.datetime.now(dt.timezone.utc).isoformat(),status='COMPLETE' if item['returncode']==0 else 'FAILED');save()
        if item['returncode']!=0:raise RuntimeError('Evaluator failed: '+name)
        return json.loads(out.read_text())
    try:
        for ds in audit['datasets']:
            dataset=ds['dataset'];key='webvid' if dataset.startswith('webvid') else 'yandex'
            fast=json.loads((a.fast_root/dataset/'manifest.json').read_text())
            if fast['fit_queries']!=20000 or fast['pilot_queries_used']!=0:raise ValueError('Unpaired baseline')
            args=['--stage','P1','--split','pilot','--dataset',dataset,'--index-file',ds['graph']['path'],
                  '--fast-hubs',fast['hubs_file'],'--fast-ids',fast['ids_file'],'--threads','16',
                  '--top-k','10','--search-ls','64,128','--warmup-queries','128','--hnsw-seed','100']
            count=invoke(key+'_count',args+['--measurement','count','--rounds','1','--methods','fast,fast_unified','--max-queries',str(a.queries)])
            plain=invoke(key+'_plain',args+['--measurement','timing','--rounds','5','--methods','fast,fast_unified','--max-queries',str(a.queries)])
            checks=[]
            for l in [64,128]:
                c={x['method']:x for x in count['results'] if x['search_L']==l}
                one=c['fast'];two=c['fast_unified']
                if one['result_hash_fnv1a64']!=two['result_hash_fnv1a64']:raise ValueError('Real legacy/shared result mismatch')
                for x,y in zip(one['per_query'],two['per_query']):
                    for k in ['query_id','entry_ids','result_ids','recall','routing_ndc','graph_ndc','total_ndc']:
                        if x[k]!=y[k]:raise ValueError('Real legacy/shared '+k+' mismatch')
                    if x['total_ndc']!=x['routing_ndc']+x['graph_ndc']:raise ValueError('NDC accounting mismatch')
                for x in plain['results']:
                    if x['search_L']!=l:continue
                    match=c[x['method']]
                    if x['result_hash_fnv1a64']!=match['result_hash_fnv1a64'] or x['route_hash_fnv1a64']!=match['route_hash_fnv1a64']:
                        raise ValueError('Real count/plain route or result mismatch')
                    if x['mean_recall']!=match['mean_recall']:raise ValueError('Count/plain recall mismatch')
                    if x['min_actual_entry_count']!=3 or x['max_actual_entry_count']!=3:raise ValueError('Wrong actual Fast entry count')
                checks.append({'L':l,'legacy_unified_ids_and_ndc':'PASS','count_plain_ids_and_routes':'PASS',
                               'timing_repeat_identity':'PASS','queries':a.queries,'count_rounds':1,'timing_rounds':5})
            topm=[]
            for m in [4,6,8]:
                data=invoke(key+f'_top{m}',args+['--measurement','count','--rounds','1','--methods','fast_unified','--fast-m',str(m),'--max-queries','32'])
                for point in data['results']:
                    if point['min_actual_entry_count']!=m or point['max_actual_entry_count']!=m:raise ValueError('Top-m silently truncated')
                    if any(len(q['entry_ids'])!=m or len(set(q['entry_ids']))!=m for q in point['per_query']):raise ValueError('Invalid top-m IDs')
                topm.append({'m':m,'queries':32,'Ls':[64,128],'status':'PASS'})
            result['datasets'].append({'dataset':dataset,'paired_fast_manifest':str(a.fast_root/dataset/'manifest.json'),
                                       'checks':checks,'actual_top_m':topm,'status':'PASS'})
            save()
        result['status']='PASS_REAL_DATA_PARITY'
        result['limitation']='P1 real timing is measurement verification only, not method performance evidence. Synthetic regional correctness and independent source timer review are separate required evidence. Legacy parity is same corrected best-first entry IDs, not the historical worst-first end-to-end router.'
    except BaseException as e:
        result['failure']=repr(e);save();raise
    finally:
        result['ended_utc']=dt.datetime.now(dt.timezone.utc).isoformat();save()
    print(json.dumps({'status':result['status'],'report':str(a.output/'report.json')}),flush=True)

if __name__=='__main__':main()

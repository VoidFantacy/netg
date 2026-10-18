#!/usr/bin/env python3
"""Small actual-run qualification and historical output regression, not formal QPS."""
import json
import sys
from pathlib import Path
import time
import numpy as np
from run_suite import ROOT,run,save,state,sha


def main():
    started=time.monotonic();cat=json.loads((ROOT/'reviews/dataset_catalogue.json').read_text())
    root=ROOT/'qualification';root.mkdir(exist_ok=True);rows=[]
    for dataset,entry in cat['datasets'].items():
        c=json.loads(Path(entry['benchmark_config']).read_text());c['queries']['n']=256
        c['timing_repeats']=1;c['output_dir']=str(root/dataset)
        c['K_L']={'1':[100,200] if dataset in ('coco','flickr30k') else [32,200],'100':[100,200]}
        cfg=root/f'{dataset}.json';save(cfg,c);r=run('qualification',cfg,ROOT/'bin/benchmark')
        for result in r['results']:
            if result['family']=='POST':continue
            K=result['K'];L=result['L'];name=result['method']
            base=Path(entry.get('historical_point_results',entry['historical_results']))/f'k{K}'
            old=base/f'{name}_L{L}'
            if dataset in ('coco','flickr30k'):
                old=base/f'{"NSG" if name=="NSG" else "GT10"}_L{L}'/'raw'
            new=Path(result['result_dir'])/'raw';record={'dataset':dataset,'K':K,'L':L,'method':name,'n':256,'files':{}}
            for filename,dtype,width in (('ids.i32','<i4',K),('distances.f32','<f4',K),('entry_ids.i32','<i4',3)):
                op=old/filename;npth=new/filename
                assert op.is_file(),op
                a=np.memmap(op,dtype=dtype,mode='r').reshape(-1,width)[:256]
                b=np.fromfile(npth,dtype=dtype).reshape(256,width)
                equal=bool(np.array_equal(a.view(np.uint32),b.view(np.uint32)))
                record['files'][filename]={'historical':str(op),'new':str(npth),'bits_equal':equal,
                    'mismatched_values':int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32))),
                    'historical_sha256':sha(op),'new_sha256':sha(npth)}
                assert equal,record
            rows.append(record)
        print(json.dumps({'event':'historical_regression_pass','dataset':dataset,'comparisons':sum(x['dataset']==dataset for x in rows)}),flush=True)
    save(ROOT/'reviews/qualification_regression.json',{'status':'PASS_SMALL_ACTUAL_RUN_FULL_WORD_HISTORICAL_REGRESSION',
        'rows':rows,'comparisons':len(rows),'elapsed_seconds':time.monotonic()-started,'scope':'256 already exposed queries per point, complete baseline IDs/score/entry words; all POST qualification oracles; qualification timing excluded from formal reports'})
    state(status='QUALIFICATION_COMPLETE_READY_FOR_FORMAL',active_dataset=None,active_stage=None)


if __name__=='__main__':main()

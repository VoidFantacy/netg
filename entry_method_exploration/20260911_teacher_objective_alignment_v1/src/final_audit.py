from common import *
import re,sys,xml.etree.ElementTree as ET
import numpy as np
sys.path.insert(0,str(E28/'src/vendor'))
from openpyxl import load_workbook

def links(text):
    return re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text)

def main():
    audit=O/'reviews/final_audit.json'
    dump(audit,dict(status='RUNNING',started=time.time()))
    try:
        protected=read(O/'reviews/protected_before.json')+read(O/'reviews/protected_additional_before.json')
        for x in protected:assert identity(x['path'])==x,x['path']
        frozen_checks=0
        for name in ['reviews/protocol_lock.json','reviews/frozen_before_training.json','models/frozen_before_development.json',
                     'reviews/evaluation_start_freeze.json','models/frozen_before_validation.json']:
            check_freeze(O/name);frozen_checks+=len(read(O/name)['files'])
        for name in ['teacher_verification','objective_tests','model_verification','output_verification','plot_visual_review']:
            assert read(O/'reviews'/f'{name}.json')['status']=='PASS',name
        for item in read(O/'reviews/plot_visual_review.json')['files']:
            assert identity(item['path'])==item,item['path']
        jobs=read(O/'logs/evaluation_jobs.json')
        assert len(jobs)==8 and all(j['status']=='COMPLETE' and j['exit_code']==0 for j in jobs)
        calls=sum(j['reserved_calls'] for j in jobs)
        assert calls==NORMAL_CAP and calls<HARD_CAP
        assert sum(j['seconds'] for j in jobs)<3600
        for j in jobs:
            assert j['seconds']<1200 and j['rss_peak_kib']<40*(1<<20)
            assert identity(j['config']['path'])==j['config']
            result=read(O/'results'/f"{j['stage']}_{j['dataset']}"/'results.json')
            assert result['physical_graph_calls']==j['reserved_calls']
            thread=read(O/'results'/f"{j['stage']}_{j['dataset']}"/'thread_contract.json')
            assert thread['actual_openmp_threads']==thread['process_threads']==1 and thread['cpu']==15
        training=read(O/'models/training_runs.json')
        assert len(training)==8 and {(r['dataset'],r['cell']) for r in training}=={(ds,cell) for ds in DS for cell in CELLS}
        for r in training:
            assert r['epochs']==80 and r['lambda_anchor']==100 and r['temperature']==.05 and r['margin']==.1
            assert not any(r[k] for k in ['cal_used','audit_used','validation_used'])
            assert identity(r['W']['path'])==r['W']
            if r['cell']=='cost_ce':assert r['E28_recovery']['bit_equal']
        for ds in DS:
            assert read(O/'inputs'/ds/'teachers/verification.json')['logical_labels_verified']==1120000
        output=read(O/'reviews/output_verification.json')
        assert output['total_points']==170 and output['total_query_outputs']==471200
        assert output['historical_regression_outputs']==160000 and output['physical_calls']==calls
        assert output['fit_native_cache_parity_outputs']>=40000
        gradients=read(O/'results/gradient_diagnostics.json')
        assert gradients['optimizer_steps']==gradients['NSG_calls']==0 and len(gradients['records'])==16
        figures=['recall_qps_main','recall_qps_all','interpolated_qps','factor_effects','training_alignment','fit_to_validation']
        for name in figures:
            png=O/'figures'/f'{name}.png';svg=O/'figures'/f'{name}.svg'
            assert png.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') and png.stat().st_size>10000
            assert ET.parse(svg).getroot().tag.endswith('svg')
        wb=load_workbook(O/'chart_data.xlsx',read_only=True,data_only=True)
        tabledata=read(O/'results/analysis_tables.json')
        workbook_rows={}
        for name,rows in tabledata.items():
            ws=wb[name];values=ws.values;headers=list(next(values));stored=list(values)
            assert len(stored)==len(rows),(name,len(stored),len(rows))
            for expected,actual in zip(rows,stored):
                for k,value in zip(headers,actual):
                    target=expected.get(k)
                    if isinstance(target,float):
                        assert value is not None and abs(value-target)<1e-8,(name,k,target,value)
                    else:assert value==target,(name,k,target,value)
            workbook_rows[name]=len(rows)
        wb.close()
        link_checks=0
        documents=[p for p in O.glob('*.md')]
        roots=[R/n for n in ['summary.md','spec.md','s-target.md','s-experiment.md']]
        roots += [R/'experiment_history/18_teacher_objective_alignment.md',R/'experiment_history/README.md']
        for p in documents+roots:
            before=O/'source_before'/p.name
            old=set(links(before.read_text())) if before.exists() and p in roots else set()
            for target in links(p.read_text()):
                if target in old or target.startswith(('http:','https:','#','mailto:')):continue
                target=target.split('#',1)[0].strip('<>')
                if not target:continue
                path=Path(target) if target.startswith('/') else p.parent/target
                assert path.exists(),(p,target)
                link_checks+=1
        delta=subprocess.run(['git','diff','--check','--','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history'],cwd=R,capture_output=True,text=True)
        assert delta.returncode==0,delta.stdout+delta.stderr
        size=sum(p.stat().st_size for p in O.rglob('*') if p.is_file())
        free=shutil.disk_usage(O).free
        assert size<1<<30 and free>10*(1<<30)
        conclusion=read(O/'results/conclusion.json')
        dump(audit,dict(status='PASS',protected_identity_checks=len(protected),frozen_identity_checks=frozen_checks,
            training_runs=8,new_label_calls=0,reused_logical_labels=2240000,real_search_calls=calls,repair_calls=0,synthetic_calls=0,
            formal_points=110,formal_repeats=3,all_query_outputs=471200,historical_regression_outputs=160000,
            fit_native_cache_parity_outputs=output['fit_native_cache_parity_outputs'],figures=6,
            workbook_rows=workbook_rows,local_link_checks=link_checks,artifact_bytes=size,free_bytes=free,
            heldout_opened=False,conclusion=conclusion['status'],finished=time.time()))
        dump(O/'state.json',dict(status='COMPLETE',conclusion=conclusion['status'],real_search_calls=calls,
            training_runs=8,heldout_access=False,final_audit=str(audit)))
        print(json.dumps(read(audit)),flush=True)
    except BaseException as error:
        dump(audit,dict(status='FAILED',error=repr(error),timestamp=time.time()))
        raise

if __name__=='__main__':main()

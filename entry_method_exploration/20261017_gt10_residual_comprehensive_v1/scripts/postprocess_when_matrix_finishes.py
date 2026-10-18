#!/usr/bin/env python3
"""Wait on a Linux process-exit event, then run postprocessing once, sequentially."""
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    launch=ROOT/'reviews/postprocess_pipeline.launch.json';receipt=ROOT/'reviews/postprocess_pipeline.json'
    assert not launch.exists() and not receipt.exists()
    original=json.loads((ROOT/'reviews/qualified_matrix_pipeline.launch.json').read_text());pid=original['pid']
    scripts=['collect_costs.py','analyze_results.py','independent_results_audit.py','diagnose_boundaries.py','render_pdf.py']
    frozen={str(ROOT/'scripts'/name):sha(ROOT/'scripts'/name) for name in scripts}
    launch.write_text(json.dumps({'pid':os.getpid(),'waited_matrix_pid':pid,'script_sha256':frozen,'started_unix':time.time(),'waiting':'Linux pidfd process-exit event; no repeated process polling'},indent=2)+'\n')
    try:
        fd=os.pidfd_open(pid)
        select.select([fd],[],[])
        os.close(fd)
    except ProcessLookupError:pass
    result=json.loads((ROOT/'reviews/qualified_matrix_pipeline.json').read_text())
    assert result['status']=='PASS_QUALIFIED_FORMAL_MATRIX_ANALYSIS_PENDING','Formal pipeline did not succeed; preserve all artifacts'
    for path,digest in frozen.items():assert sha(path)==digest,'Postprocessor changed while waiting: '+path
    final=ROOT/'analysis/final_v1';delivery=ROOT/'analysis/delivery_v1'
    pdf=delivery/'NETG_E183_GT10与残差_七数据集及失败查询_20261017.pdf'
    steps=[('costs',['collect_costs.py']),('analysis',['analyze_results.py','--out',str(final)]),
           ('audit_selftest',['independent_results_audit.py','--selftest']),
           ('independent_audit',['independent_results_audit.py','--analysis',str(final)]),
           ('boundary_diagnostics',['diagnose_boundaries.py','--analysis-dir',str(final)]),
           ('finalize_report',['analyze_results.py','--finalize-report',str(final),'--out',str(delivery)]),
           ('render_pdf',['render_pdf.py','--report',str(delivery/'report_zh.md'),'--output',str(pdf),'--receipt',str(delivery/'pdf_render_receipt.json')])]
    started=time.monotonic();records=[]
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',OMP_DYNAMIC='FALSE')
    for name,args in steps:
        p=ROOT/'logs'/f'post_{name}.log';assert not p.exists();begin=time.monotonic()
        argv=[sys.executable,str(ROOT/'scripts'/args[0]),*args[1:]]
        print(json.dumps({'event':'post_stage_start','stage':name,'log':str(p)}),flush=True)
        with p.open('x') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,env=env)
        records.append({'stage':name,'argv':argv,'exit_code':r.returncode,'elapsed_seconds':time.monotonic()-begin,'log':str(p)})
        if r.returncode:
            receipt.write_text(json.dumps({'status':'FAIL_POSTPROCESS_PRESERVE_ATTEMPT','stages':records},indent=2)+'\n')
            raise RuntimeError('Postprocessing failed: '+name)
    receipt.write_text(json.dumps({'status':'PDF_GENERATED_VISUAL_REVIEW_AND_ROOT_DOCUMENTS_PENDING','stages':records,'elapsed_seconds':time.monotonic()-started,'pdf':str(pdf)},indent=2)+'\n')
    state_path=ROOT/'state.json';state=json.loads(state_path.read_text());state.update(status='PDF_GENERATED_REVIEW_PENDING',pdf=str(pdf),updated_unix=time.time())
    state_path.write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n')


if __name__=='__main__':main()

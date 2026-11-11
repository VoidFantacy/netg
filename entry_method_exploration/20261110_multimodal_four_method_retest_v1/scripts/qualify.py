from pathlib import Path
import sys,os,json,time,subprocess,shutil,hashlib
import numpy as np
RUN=Path(__file__).resolve().parents[1];ROOT=RUN.parents[1]
sys.path.insert(0,str(RUN/'src'))
from common import dump,sha,resource_check
OLD=ROOT/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1'
E97=ROOT/'entry_method_exploration/20260915_gate_l2_r1_r100_v1'
ENV=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')

def compare(old,new,K,n=256):
    checks={}
    for name,width in [('ids.i32',K),('distances.f32',K),('entry_ids.i32',3)]:
        a=np.fromfile(old/name,dtype='<u4',count=n*width);b=np.fromfile(new/name,dtype='<u4')
        equal=a.size==b.size and np.array_equal(a,b)
        checks[name]={'equal':equal,'values':b.size,'old':str(old/name),'new_sha256':sha(new/name)}
        assert equal,checks
    return checks

def run(cmd,log):
    assert not log.exists();t=time.monotonic()
    with log.open('x') as f:p=subprocess.run(['taskset','-c','15',*map(str,cmd)],stdout=f,stderr=subprocess.STDOUT,env=ENV)
    assert p.returncode==0,(p.returncode,str(log))
    return time.monotonic()-t

def main():
    assert (RUN/'reviews/missing_gates_ready.json').exists()
    assert not (RUN/'reviews/qualification.json').exists()
    lock=json.loads((RUN/'config.locked.json').read_text());rows=[];legacy=[]
    for ds in lock['datasets']:
        c=json.loads((RUN/'configs'/f'{ds}.qualification.json').read_text())
        dump(RUN/'state.json',{'status':'QUALIFYING','dataset':ds,'pid':os.getpid(),'formal_completed':0})
        elapsed=run([RUN/'bin/benchmark','qualification',RUN/'configs'/f'{ds}.qualification.json'],RUN/'logs'/f'{ds}_qualification.log')
        result=json.loads((Path(c['output_dir'])/'complete.json').read_text())
        assert result['points']==16 and result['full_merge_oracle_passed']
        family=c['routers'][0]['name']
        names={'NSG':'NSG','GT10':'GT10-soft-t1' if family=='soft' else 'GT10-hard','GT10+Residual':family+'-JOINT32'}
        for row in result['results']:
            if row['method']=='GATE':continue
            old=OLD/'results'/ds/f'k{row["K"]}'/f'{names[row["method"]]}_L{row["L"]}'/'raw'
            new=Path(row['result_dir'])/'raw'
            checks=compare(old,new,row['K'])
            rows.append({'dataset':ds,'K':row['K'],'L':row['L'],'method':row['method'],'checks':checks})
        # E97's independently compiled legacy GATE path is run on the same 256 queries.
        # Temporary output uses shm because the old binary checks ordinary-user available space.
        # Copy and verify every artifact to persistent storage before deleting this task's scratch.
        query=c['queries'];n=query['n'];dim=query['d'];start=query.get('row_start',0)
        if query['format']=='fvecs':q=np.memmap(query['path'],dtype='<f4',mode='r').reshape(-1,dim+1)[start:start+n,1:]
        else:
            assert query['format']=='raw_f32';q=np.memmap(query['path'],dtype='<f4',mode='r').reshape(-1,dim)[start:start+n]
        inp=RUN/'inputs'/ds;inp.mkdir(exist_ok=True);qpath=inp/'qualification_queries.f32';np.asarray(q).tofile(qpath)
        gate=c['routers'][1]
        for K in [1,100]:
            tmp=Path('/dev/shm')/f'acsg_e200_legacy_{ds}_k{K}';assert not tmp.exists()
            cfg={'threads':1,'formal':False,'index':c['index'],'n':256,'K':K,'metric_id':0,'queries':str(qpath),'L':[100,200],
              'methods':[{'name':'GATE','ids':gate['ids'],'W':gate['W']}], 'dataset_order':0}
            cp=RUN/'configs'/f'{ds}.legacy_gate_k{K}.json';dump(cp,cfg)
            seconds=run([E97/'bin/evaluate',cp,tmp],RUN/'logs'/f'{ds}_legacy_gate_k{K}.log')
            dest=RUN/'reviews/legacy_gate'/ds/f'k{K}';assert not dest.exists();shutil.copytree(tmp,dest)
            for path in tmp.rglob('*'):
                if path.is_file():assert sha(path)==sha(dest/path.relative_to(tmp))
            for L in [100,200]:
                checks=compare(dest/f'GATE_L{L}',Path(c['output_dir'])/f'k{K}'/f'GATE_L{L}'/'raw',K)
                legacy.append({'dataset':ds,'K':K,'L':L,'checks':checks,'legacy_process_seconds':seconds})
            shutil.rmtree(tmp)
        print('QUALIFIED',ds,'old method comparisons',len(rows),'GATE comparisons',len(legacy),flush=True)
    dump(RUN/'reviews/qualification.json',{'status':'PASS','new_native_points':64,'old_NSG_GT10_B32_comparisons':rows,'legacy_GATE_comparisons':legacy,
       'scope':'256 exposed queries each; ID/distance/entry words; native residual merge oracle; no formal QPS claimed','legacy_binary_sha256':sha(E97/'bin/evaluate')})
    dump(RUN/'state.json',{'status':'QUALIFIED_READY_TO_FREEZE','formal_completed':0,'formal_pending':640})

if __name__=='__main__':main()

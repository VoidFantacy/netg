"""Freeze and run the fixed E200 matrix. No concurrent numerical work."""
from pathlib import Path
import os,sys,json,time,hashlib,subprocess,gzip,shutil,traceback
RUN=Path(__file__).resolve().parents[1];ROOT=RUN.parents[1]
sys.path.insert(0,str(RUN/'src'))
from common import dump,sha,resource_check
ENV=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')

def paths_in(value):
    if isinstance(value,dict):
        for v in value.values():yield from paths_in(v)
    elif isinstance(value,list):
        for v in value:yield from paths_in(v)
    elif isinstance(value,str) and value.startswith('/'):
        p=Path(value)
        if p.is_file():yield p

def compress_job(out):
    records=[]
    for p in sorted(out.glob('k*/*/raw/*')):
        assert p.suffix!='.gz'
        digest=sha(p);dest=Path(str(p)+'.gz');assert not dest.exists()
        with p.open('rb') as src,gzip.open(dest,'wb',compresslevel=1) as dst:shutil.copyfileobj(src,dst,4*1024**2)
        h=hashlib.sha256()
        with gzip.open(dest,'rb') as f:
            for block in iter(lambda:f.read(4*1024**2),b''):h.update(block)
        assert h.hexdigest()==digest
        records.append({'file':str(p.relative_to(out)),'payload_sha256':digest,'bytes':p.stat().st_size,'gzip_sha256':sha(dest),'gzip_bytes':dest.stat().st_size})
        p.unlink()
    dump(out/'archive_manifest.json',{'status':'PASS_PAYLOAD_ROUNDTRIP','files':records,'compressed_outside_formal_wall':True})

def freeze(lock):
    assert json.loads((RUN/'reviews/qualification.json').read_text())['status']=='PASS'
    assets=set()
    for ds in lock['datasets']:
        c=json.loads((RUN/'configs'/f'{ds}.json').read_text())
        assets.update(paths_in(c))
        gt=json.loads((ROOT/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1/configs'/f'{ds}.analysis.json').read_text())['eval_gt']
        assets.add(Path(gt['path']))
        for K in [1,100]:
            job=json.loads(json.dumps(c));job['K_L']={str(K):c['K_L'][str(K)]};job['output_dir']=str(RUN/'results'/ds/f'k{K}_run')
            cp=RUN/'configs'/f'{ds}.formal_k{K}.json';assert not cp.exists();dump(cp,job)
    assets.update(p for p in (RUN/'configs').glob('*.json'))
    assets.update(p for p in (RUN/'src').glob('*') if p.is_file())
    assets.update([RUN/'bin/benchmark',RUN/'config.locked.json',RUN/'protocol.md',Path(__file__),RUN/'reviews/qualification.json'])
    build=json.loads((RUN/'bin/build_benchmark.json').read_text());assets.update(map(Path,build['input_sha256']))
    t=time.monotonic();records={}
    for p in sorted(assets):
        s=p.stat();records[str(p)]={'sha256':sha(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
    for ds in ['coco','flickr30k']:
        out=RUN/'models'/ds/'gate_disjoint_labels_v1';meta=json.loads((out/'complete.json').read_text())
        assert sha(out/'best.pt')==meta['checkpoint_sha256']
        assert sha(out/'W.f32')==meta['best']['embedding_sha256']
    result={'status':'FROZEN_BEFORE_FORMAL','head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':records,'full_hash_seconds':time.monotonic()-t,'formal_points':640,'formal_batches':1280,'formal_queries':11200000}
    dump(RUN/'formal_freeze.json',result);return result

def verify(fr,full=False):
    for name,identity in fr['files'].items():
        p=Path(name);s=p.stat();assert s.st_size==identity['bytes'] and s.st_mtime_ns==identity['mtime_ns'],name
        if full:assert sha(p)==identity['sha256'],name

def main():
    lock=json.loads((RUN/'config.locked.json').read_text());resource_check()
    fp=RUN/'formal_freeze.json'
    fr=json.loads(fp.read_text()) if fp.exists() else freeze(lock)
    verify(fr,True);receipts=[];completed=0;t0=time.time();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    for ds in lock['datasets']:
        for K in [1,100]:
            cp=RUN/'configs'/f'{ds}.formal_k{K}.json';c=json.loads(cp.read_text());out=Path(c['output_dir'])
            if (out/'complete.json').exists():
                old=json.loads((out/'complete.json').read_text());assert old['points']==80 and old['formal_batches']==160
                assert (out/'archive_manifest.json').exists(),'completed native job needs explicit compression recovery'
                completed+=80;continue
            assert not out.exists(),'preserve partial job; explicit recovery required, no silent retiming'
            resource_check();verify(fr);log=RUN/'logs'/f'{ds}_formal_k{K}.log';assert not log.exists()
            start=time.time();cmd=['taskset','-c','15',str(RUN/'bin/benchmark'),'benchmark',str(cp)]
            with log.open('x') as f:
                p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=ENV)
                dump(RUN/'state.json',{'status':'MEASURING','dataset':ds,'K':K,'formal_completed':completed,'formal_total':640,'orchestrator_pid':os.getpid(),'child_pid':p.pid,'boot_id':boot,'started_unix':start,'log':str(log),'job_output':str(out)})
                print('START_FORMAL',ds,K,p.pid,flush=True);code=p.wait()
            rec={'dataset':ds,'K':K,'exit_code':code,'command':cmd,'native_process_seconds':time.time()-start,'log':str(log)}
            receipts.append(rec);dump(RUN/'reviews/formal_process_costs.json',receipts)
            assert code==0,(ds,K,log)
            result=json.loads((out/'complete.json').read_text());assert result['points']==80 and result['formal_batches']==160 and result['all_round_bits_equal']
            dump(RUN/'state.json',{'status':'ARCHIVING','dataset':ds,'K':K,'formal_completed':completed+80,'orchestrator_pid':os.getpid(),'boot_id':boot})
            arch_start=time.time();compress_job(out);rec['archive_seconds']=time.time()-arch_start;dump(RUN/'reviews/formal_process_costs.json',receipts)
            completed+=80;verify(fr);print('COMPLETE_FORMAL',ds,K,completed,flush=True)
    assert completed==640;verify(fr,True)
    dump(RUN/'reviews/measurement_complete.json',{'status':'PASS','points':640,'batches':1280,'queries':11200000,'all_frozen_inputs_full_sha_after':True,'suite_process_seconds':time.time()-t0,'cost_scope':'includes native jobs, archiving and identity checks; internal walls are nested'})
    dump(RUN/'state.json',{'status':'MEASUREMENT_COMPLETE_ANALYSIS_PENDING','formal_completed':640,'formal_batches':1280,'orchestrator_pid':os.getpid(),'boot_id':boot})

if __name__=='__main__':
    try:main()
    except BaseException as e:
        p=RUN/'reviews'/f'run_failure_{int(time.time())}.json';dump(p,{'error':repr(e),'traceback':traceback.format_exc()})
        dump(RUN/'state.json',{'status':'RUN_FAILED_REVIEW_REQUIRED','error':repr(e),'failure':str(p),'orchestrator_pid':os.getpid()});raise

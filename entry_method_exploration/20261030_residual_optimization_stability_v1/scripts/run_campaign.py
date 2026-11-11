from common import *
import subprocess,shutil,datetime

def frozen_files():
    paths=[R/'protocol.md',R/'selection_freeze.json',R/'inherited_assets.json',R/'storage/benchmark']
    for sub in ['src','scripts','configs']:
        paths += [p for p in (R/sub).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    paths += [p for p in (R/'storage/inputs').rglob('*') if p.is_file()]
    for a in read(R/'reviews/build.json')['argv']:
        p=Path(a)
        if p.is_file() and (p.suffix in ['.a','.o'] or p.name=='g++'):paths.append(p)
    paths += [OLD/'src/benchmark.cpp',R.parent/'20261017_gt10_residual_comprehensive_v1/src/residual_tools.cpp',R.parent/'20261015_m5_k100_capacity_v1/src/capacity.hpp']
    return [ident(p) for p in sorted(set(paths))]

def native(ds,window):
    qualify=window=='qualification';cfg=R/f'configs/{ds}.{window}.json';c=read(cfg);out=Path(c['output_dir'])
    if (out/'complete.json').exists():
        j=read(out/'complete.json');assert j['status']==('PASS_E194_QUALIFICATION' if qualify else 'PASS_E194_FORMAL');return
    assert shutil.disk_usage('/data').free>.65*2**30 and shutil.disk_usage('/root').free>.7*2**30
    env=os.environ.copy();env.update({k:'1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']})
    log=R/f'reviews/{ds}.{window}.log';assert not log.exists(),'preserve failed attempt; inspect before rerun'
    t=time.perf_counter();peak=0;nt=0
    with log.open('x') as f:
        p=subprocess.Popen([str(R/'storage/benchmark'),'qualification' if qualify else 'formal',str(cfg)],cwd=REPO,env=env,preexec_fn=lambda:os.sched_setaffinity(0,{15}),stdout=f,stderr=subprocess.STDOUT)
        while p.poll() is None:
            try:
                v=dict(line.split(':',1) for line in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in line)
                nt=max(nt,int(v.get('Threads','0')));peak=max(peak,int(v.get('VmRSS','0 kB').split()[0])*1024)
            except FileNotFoundError:pass
            time.sleep(.25)
    rec=dict(dataset=ds,window=window,returncode=p.returncode,seconds=time.perf_counter()-t,peak_rss=peak,max_threads=nt,affinity=[15],environment={k:env[k] for k in env if k.endswith('NUM_THREADS')})
    dump(R/f'reviews/{ds}.{window}.receipt.json',rec);print(json.dumps(rec),flush=True)
    assert p.returncode==0 and nt==1,rec
    subprocess.run([sys.executable,str(R/'scripts/audit.py'),ds,window],cwd=REPO,check=True)

if __name__=='__main__':
    freeze=R/'formal_freeze.json'
    if not freeze.exists():dump(freeze,dict(status='FROZEN_BEFORE_QUALIFICATION_AND_FORMAL',time=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=frozen_files(),planned_points=256,planned_batches=768))
    else:
        for f in read(freeze)['files']:assert sha(f['path'])==f['sha256'],f['path']
    for ds in DS:
        dump(R/'state.json',dict(status='QUALIFICATION',dataset=ds,default_changed=False));native(ds,'qualification')
    dump(R/'reviews/qualification_complete.json',dict(status='PASS_20_POINTS_NATIVE_AND_STDLIB_AUDITS'))
    for ds in DS:
        for window in ['public','confirmation']:
            dump(R/'state.json',dict(status='FROZEN_FORMAL_T1',dataset=ds,window=window,planned_points=256,default_changed=False));native(ds,window)
    dump(R/'state.json',dict(status='FORMAL_COMPLETE_ANALYSIS_PENDING',formal_points=256,formal_batches=768,default_changed=False))
    print('E194_ALL_FORMAL_COMPLETE',flush=True)

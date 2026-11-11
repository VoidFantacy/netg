from common import *
import subprocess,shutil
mode=sys.argv[1]
def launch(argv,label):
    t=time.perf_counter();log=R/'reviews'/f'{label}.log';assert not log.exists(),label
    with log.open('w') as f:p=subprocess.run(['taskset','-c','15',*argv],cwd=REPO,stdout=f,stderr=subprocess.STDOUT,timeout=7200)
    v=dict(argv=argv,returncode=p.returncode,seconds=time.perf_counter()-t,log=str(log));dump(R/'reviews'/f'{label}.receipt.json',v);assert p.returncode==0,(label,log.read_text()[-5000:]);print(label,'PASS',round(v['seconds'],2),flush=True)
if mode=='qualification':
    for ds in DS:
        conf=R/'configs'/f'{ds}.qualification.json'
        if not (Path(read(conf)['output_dir'])/'complete.json').exists():launch([str(R/'storage/benchmark'),'qualification',str(conf)],f'{ds}.qualification')
        c=read(conf);c.update(output_dir=str(R/'storage/legacy_qualification'/ds),K_L={'1':[200],'100':[200]},completion_L={'1':[200],'100':[200]},methods=['GT10','B32','REUSE-PQ','REUSE-SQ']);old=R/'configs'/f'{ds}.legacy.json';dump(old,c)
        launch([str(OLD/'storage/benchmark'),'qualification',str(old)],f'{ds}.legacy')
        newer=Path(read(conf)['output_dir']);older=Path(c['output_dir']);pairs=[]
        for K in [1,100]:
            for m in ['GT10','B32','REUSE-SQ']:
                a=read(newer/f'k{K}/{m}_L200/round0.json');b=read(older/f'k{K}/{m}_L200/round0.json');assert a['packet_sha256']==b['packet_sha256'],(ds,K,m);pairs.append(dict(K=K,method=m,packet_sha256=a['packet_sha256']))
        dump(R/'reviews'/f'{ds}.legacy_parity.json',dict(status='PASS_SIX_PACKET_PREFIX_PARITY',pairs=pairs))
    files=[ident(p) for folder in ['src','scripts','configs'] for p in (R/folder).glob('*') if p.is_file()]
    files += [ident(R/'protocol.md'),ident(R/'storage/benchmark'),ident(R/'input_freeze.json')]
    files += [ident(p) for p in (R/'storage/meta').glob('*/*') if p.is_file()]
    dump(R/'formal_freeze.json',dict(status='FROZEN_BEFORE_FORMAL',time=time.time(),files=files,qualification_points=140,legacy_control_points=56,legacy_parity_comparisons=42))
    dump(R/'state.json',dict(status='QUALIFIED_READY_FOR_FORMAL',formal_points=1260,formal_batches=3780,default_changed=False))
else:
    freeze=read(R/'formal_freeze.json')
    for x in freeze['files']:assert sha(x['path'])==x['sha256'],x['path']
    completed=[]
    for ds in DS:
        for window in ['A','B']:
            assert shutil.disk_usage('/root').free>300<<20,'root storage reserve'
            conf=R/'configs'/f'{ds}.{window}.json';out=Path(read(conf)['output_dir'])
            if not (out/'complete.json').exists():launch([str(R/'storage/benchmark'),'formal',str(conf)],f'{ds}.{window}')
            completed.append(read(out/'complete.json'));dump(R/'state.json',dict(status='RUNNING_DETAILED_MATRIX',completed=completed,default_changed=False))
    dump(R/'formal_complete.json',dict(status='PASS_ALL_1260_POINTS_3780_BATCHES',completed=completed,points=sum(x['points'] for x in completed),batches=sum(x['batches'] for x in completed)))
    dump(R/'state.json',dict(status='NATIVE_COMPLETE_ANALYSIS_PENDING',formal_points=1260,formal_batches=3780,default_changed=False))

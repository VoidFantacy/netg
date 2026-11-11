from common import *
LS=[100,128,160,200,256,320,400,512,640,800,1000]
NEW=['DIST96','DIST384','FAST96','FAST384','CASCADE96','CASCADE384','ADAPT','POLICY','TEACHER384','OLD-CACHED384','MODEL1','DIST1-FULL']
def points(extra=None,qual=False):
    p=set()
    for K in [1,100]:
        for L in (LS+[32,64] if K==1 else LS):
            for m in ['GT10','OPT-B32','Q8-B32']:p.add((K,L,m))
    for K,L in STATES:
        for m in NEW+['REUSE-SQ']+(['POLICY-OFF'] if qual else []):p.add((K,L,m))
    for K,L,m in extra or []:p.add((K,L,m))
    if qual:p={v for v in p if v[:2] in STATES}
    return [dict(K=k,L=l,method=m) for k,l,m in sorted(p)]
for ds in DS:
    c=read(R/'configs'/f'{ds}.k100.L200.labels.json')
    models=[dict(K=K,L=L,path=str(R/'storage/models'/ds/f'k{K}_L{L}'/'model.json')) for K,L in STATES]
    for stage,n,first,audit in [('qualification',16,2560,True),('calibration',512,2560,False)]:
        cfg=dict(c,queries=dict(c['queries'],row_start=first,total_n=3072,n=n),test_gt=dict(c['test_gt'],row_start=first,total_n=3072,n=n),
                 model_files=models,points=points(qual=stage=='qualification'),output_dir=str(R/'storage'/stage/ds),window=stage,audit=audit)
        dump(R/'configs'/f'{ds}.{stage}.json',cfg)
    for K,L in STATES:
        cfg=dict(model_file=str(R/'storage/models'/ds/f'k{K}_L{L}'/'model.json'),labels_dir=str(R/'storage/labels'/ds/f'k{K}_L{L}'))
        dump(R/'configs'/f'{ds}.k{K}.L{L}.inference.json',cfg)
print('BASE_MATRIX',len(points()),'per window')

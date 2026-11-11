from common import *
PRIMARY=['ALWAYS','DIST384','FAST384','TEACHER384','F-STATIC','F-PRE75','F-PRE90','F-POST75','F-POST90','F-PRE90-LATE','N-STATIC','N-PRE75','N-PRE90','N-POST75','N-POST90','N-CPOST75','N-CPOST90','N-PRE90-LATE']
def points(qual=False):
    p=set()
    for K in [1,100]:
        ls=[100,128,160,200,224,256,320,400,512,640,800,1000]+([32,64] if K==1 else [])
        for L in ([200] if qual else ls):
            for m in ['GT10','OPT-B32']:p.add((K,L,m))
        for m in ['Q8-B32','REUSE-SQ']+PRIMARY+(['F-FORCE-OFF','F-FORCE-ON','N-FORCE-OFF','N-FORCE-ON'] if qual else []):p.add((K,200,m))
    return [dict(K=k,L=l,method=m) for k,l,m in sorted(p)]
for ds in DS:
    gates=[dict(K=K,path=str(R/'storage/gates'/ds/f'k{K}.json')) for K,L in STATES]
    c=read(R/'configs'/f'{ds}.k1.labels.json');c.update(gate_files=gates,queries=dict(c['queries'],row_start=2560,total_n=3072,n=64),test_gt=dict(c['test_gt'],row_start=2560,total_n=3072,n=64),output_dir=str(R/'storage/qualification'/ds),qualification=True,points=points(True),window='qualification')
    dump(R/'configs'/f'{ds}.qualification.json',c)
    for window in ['A','B']:
        c=read(R/'configs'/f'{ds}.{window}.json');c.update(gate_files=gates,points=points(),qualification=False);dump(R/'configs'/f'{ds}.{window}.formal.json',c)
print('MATRIX',len(points()),'per window;',8*len(points()),'total',flush=True)

from common import *
from archive import archive
assert read(R/'reviews/training_complete.json')['status']=='PASS_EIGHT_MODELS'
assert read(R/'reviews/build_formal.json')['returncode']==0
recs=[]
for ds in DS:
    for K,L in STATES:
        cfg=R/'configs'/f'{ds}.k{K}.L{L}.inference.json'
        r=run(['taskset','-c','15',str(R/'storage/formal_benchmark'),'inference',str(cfg)],R/'reviews'/f'{ds}.k{K}.L{L}.inference.log')
        result=json.loads(Path(r['log']).read_text().splitlines()[-1]);assert result['status']=='PASS_NATIVE_NUMPY_ALL_LABEL_PREDICTIONS'
        dump(R/'reviews'/f'{ds}.k{K}.L{L}.inference.json',result);recs.append(r)
    cfg=R/'configs'/f'{ds}.qualification.json'
    recs.append(run(['taskset','-c','15',str(R/'storage/formal_benchmark'),'matrix',str(cfg)],R/'reviews'/f'{ds}.qualification.log'))
    archive(R/'storage/qualification'/ds)
    print('QUALIFIED',ds,flush=True)
dump(R/'reviews/qualification_complete.json',dict(status='PASS_ALL_NATIVE_MODELS_AND_BRANCHES',records=recs))
for ds in DS:
    cfg=R/'configs'/f'{ds}.calibration.json'
    r=run(['taskset','-c','15',str(R/'storage/formal_benchmark'),'matrix',str(cfg)],R/'reviews'/f'{ds}.calibration.log')
    archive(R/'storage/calibration'/ds);print('CALIBRATED',ds,r['seconds'],flush=True)
dump(R/'reviews/calibration_complete.json',dict(status='PASS_TWO_COMPLETE_WALL_CALIBRATIONS'))

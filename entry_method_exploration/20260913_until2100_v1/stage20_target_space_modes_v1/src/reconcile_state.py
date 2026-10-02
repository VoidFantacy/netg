from common import *
p=O/'state.json';before=read(p);assert before['builds']==0 and read(O/'results/cost.json')['builds']==4
shutil.copy2(p,O/'reviews/state_before_build_counter_correction.json');after=dict(before,builds=4);dump(p,after)
dump(O/'reviews/build_counter_correction.json',dict(status='PASS',reason='analyze.py inherited E78 final-state builds=0. E79 actual builder logs and cost correctly record4. Frozen analyzer source and raw kept unchanged.',before=before,after=after,new_ANN=0))
print('E79_STATE_BUILD_COUNT_CORRECTED')

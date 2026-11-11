from common import *
from archive import archive
freeze=read(R/'formal_freeze.json')
for ref in freeze['sources']+freeze['configs']:assert sha(ref['path'])==ref['sha256'],ref['path']
records=[]
for ds in DS:
    for window in ['A','B']:
        r=run(['taskset','-c','15',str(R/'storage/benchmark'),'matrix',str(R/'configs'/f'{ds}.{window}.formal.json')],R/'reviews'/f'{ds}.{window}.formal.log');records.append(r)
        archive(R/'storage/results'/ds/window);dump(R/'reviews/formal_progress.json',records);print('FORMAL_DONE',ds,window,r['seconds'],flush=True)
for ref in freeze['sources']+freeze['configs']:assert sha(ref['path'])==ref['sha256'],ref['path']
dump(R/'reviews/formal_complete.json',dict(status='PASS_FROZEN_EIGHT_WINDOW_MATRIX',records=records,points=freeze['points']))

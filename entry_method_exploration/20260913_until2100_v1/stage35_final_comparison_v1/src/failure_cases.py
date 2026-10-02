from pathlib import Path
import sys
import numpy as np
F=Path(__file__).resolve().parents[1];C=F.parent
sys.path.insert(0,str(C/'stage32_final_tooling_v1/src'))
from common import read,dump,table,DS,LS,threads,freeze
from scoring_v3 import raw
threads();O=F/'supplement_v1';assert read(O/'verification.json')['status']=='PASS';cases=[];sources=[Path(__file__),F/'selection.json'];selected=read(F/'selection.json')
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(12,6),layout='constrained')
for ax,ds in zip(axes,DS):
 c=read(F/'inputs'/ds/'config.json');new=selected['datasets'][ds]['best_new'];ref='baseline_soft' if ds==DS[0] else 'gt10_hard';rows=np.fromfile(c['row_ids'],np.int64);gt=np.fromfile(c['gt_file'],np.int64).reshape(2000,100);data={}
 for name in [ref,new]:
  for L in LS:
   p=F/'results'/ds/(name+'_L'+str(L));data[name,L]=raw(p);sources+=list(p.glob('*'))
 mat=[];labels=[]
 for typ,eligible in [('rescued',np.flatnonzero((data[ref,128]['hits']==0)&(data[new,128]['hits']>0))),('new_failure',np.flatnonzero((data[ref,128]['hits']>0)&(data[new,128]['hits']==0)))]:
  ids=sorted(eligible,key=lambda i:int(rows[i]))[:2];assert len(ids)==2
  for i in ids:
   bh=[int(data[ref,L]['hits'][i]) for L in LS];nh=[int(data[new,L]['hits'][i]) for L in LS];cases.append(dict(dataset=ds,namespace='validation',selection='first two source rows per L128 failure direction; descriptive',kind=typ,source_row=int(rows[i]),reference=ref,candidate=new,baseline_hits=' '.join(map(str,bh)),new_hits=' '.join(map(str,nh)),GT10=' '.join(map(str,gt[i,:10])),baseline_entries=' '.join(map(str,data[ref,128]['entries'][i])),new_entries=' '.join(map(str,data[new,128]['entries'][i]))))
   mat.extend([bh,nh]);labels.extend([f'{typ} q{rows[i]} P',f'{typ} q{rows[i]} new'])
 a=np.array(mat);ax.imshow(a,aspect='auto',vmin=0,vmax=10,cmap='YlGnBu');ax.set_xticks(range(5),LS);ax.set_yticks(range(len(labels)),labels);ax.set_xlabel('L');ax.set_title('Web: composed repair vs P' if ds==DS[0] else 'Yandex: compact vs P')
 for i in range(len(labels)):
  for j in range(5):ax.text(j,i,str(a[i,j]),ha='center',va='center',color='white' if a[i,j]>=6 else 'black')
fig.suptitle('Matched-P failure rescue and newly failed queries\nFirst two source rows in each direction at L128; all five L shown; no selection feedback')
fig.savefig(O/'figures/failure_cases_both_directions.png',dpi=160);fig.savefig(O/'figures/failure_cases_both_directions.svg');plt.close(fig);table(O/'failure_cases_both_directions.csv',cases);freeze(O/'failure_case_input_freeze.json',[p for p in sources if p.is_file()])
text='\n按L128每种方向取源行最小的两条，保留全五L命中（顺序64/128/256/400/800），只是事后失败解释：\n\n| 数据 | 方向/源行 | P命中 | 新方法命中 |\n|---|---|---|---|\n'
for c in cases:text+=f"| {'Web' if c['dataset']==DS[0] else 'Y'} | {c['kind']} / {c['source_row']} | {c['baseline_hits']} | {c['new_hits']} |\n"
text+='\n![双向失败案例全五L](supplement_v1/figures/failure_cases_both_directions.png)\n\n[八例GT10/入口全表](supplement_v1/failure_cases_both_directions.csv)。原全401条完整表保持，不以个例替代整体判断。\n'
(O/'failure_cases_report_fragment.md').write_text(text)
print(text)

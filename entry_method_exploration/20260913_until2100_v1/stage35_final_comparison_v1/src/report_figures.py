from pathlib import Path
import sys,csv
import numpy as np
F=Path(__file__).resolve().parents[1];C=F.parent
sys.path.insert(0,str(C/'stage32_final_tooling_v1/src'))
from common import DS,LS,read,threads,freeze,dump
threads();O=F/'supplement_v1';A=F/'analysis_v1';assert read(O/'verification.json')['status']=='PASS';D=O/'figures';D.mkdir()
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
pair=list(csv.DictReader((A/'paired.csv').open()));ci=list(csv.DictReader((O/'paired_query_intervals.csv').open()))
fig,axes=plt.subplots(3,3,figsize=(14,11),layout='constrained')
for row,(ds,new,ref,title) in enumerate([(DS[0],'composed10','baseline_soft','Web: repair vs matched GT10-P'),(DS[0],'composed10','compact10','Web: repair vs compact origin'),(DS[1],'compact10','gt10_hard','Yandex: compact vs GT10-P')]):
 p=sorted([r for r in pair if r['dataset']==ds and r['candidate']==new and r['reference']==ref],key=lambda r:int(r['L']));assert len(p)==5
 for col,(key,ylabel) in enumerate([('delta_recall_pp','Recall change (pp)'),('QPS_change_pct','QPS change (%)'),('failure','Zero-hit failure change')]):
  ax=axes[row,col];values=np.array([int(r['new_failures'])-int(r['rescued']) if key=='failure' else float(r[key]) for r in p]);ax.plot(LS,values,'o-',lw=1.4)
  if key=='QPS_change_pct':ax.vlines(LS,[float(r['all_range_low_pct']) for r in p],[float(r['all_range_high_pct']) for r in p],color='C0',alpha=.7)
  ax.axhline(0,color='k',lw=.7);ax.set_xscale('log',base=2);ax.set_xticks(LS,[str(L) for L in LS]);ax.set_xlabel('L');ax.set_ylabel(ylabel);ax.set_title(title);ax.grid(alpha=.2)
fig.suptitle('Frozen final comparison: historical validation 2,000\nQPS bars: five-run cross-range, not confidence intervals; all raw points retained')
fig.savefig(D/'paired_deltas.png',dpi=160);fig.savefig(D/'paired_deltas.svg');plt.close(fig)
failures=list(csv.DictReader((A/'failures.csv').open()));fig,axes=plt.subplots(1,2,figsize=(13,9),layout='constrained')
for ax,ds in zip(axes,DS):
 cells=[r for r in failures if r['dataset']==ds and int(r['L'])==128];names=list(dict.fromkeys(r['model'] for r in cells));rows=sorted({int(r['source_row']) for r in cells})[:24];lookup={(int(r['source_row']),r['model']):int(r['hits']) for r in cells};mat=np.array([[lookup[row,name] for name in names] for row in rows]);ax.imshow(mat,aspect='auto',vmin=0,vmax=10,cmap='YlGnBu');ax.set_xticks(range(len(names)),names,rotation=25,ha='right');ax.set_yticks(range(len(rows)),[str(r) for r in rows]);ax.set_ylabel('Validation source row');ax.set_title(('WebVid' if ds==DS[0] else 'Yandex')+' — first 24 zero-union queries at L128')
 for i in range(len(rows)):
  for j in range(len(names)):ax.text(j,i,str(mat[i,j]),ha='center',va='center',color='white' if mat[i,j]>=6 else 'black',fontsize=8)
fig.suptitle('GT10 hit counts; failure means zero hits\nComplete 401-query × five-L × all-method table: failed_queries_all_L.csv')
fig.savefig(D/'failure_queries.png',dpi=160);fig.savefig(D/'failure_queries.svg');plt.close(fig)
dump(O/'figure_scope.json',dict(original_figures_preserved=True,corrected_caption_scope='Original analysis failures.csv is 812 query-L events/4230 method cells. Complete supplement is 401 unique queries/10730 five-L-method cells.',paired_plots='No new data, QPS full cross-range not CI',failure_sample='First 24 source rows per dataset with any zero at L128',new_ANN=0))
freeze(O/'figure_input_freeze.json',[Path(__file__),A/'paired.csv',A/'failures.csv',O/'paired_query_intervals.csv',O/'verification.json'])
print('REPORT_FIGURES_READY')

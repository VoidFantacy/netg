from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def plots(out,title):
 out=Path(out);points=list(csv.DictReader((out/'points.csv').open()));folder=out/'figures';folder.mkdir(exist_ok=False)
 for metric,stem,xlabel in [('recall_pct','recall_qps','Recall@10 (%)'),('failure_rate_pct','failure_qps','Zero-GT10 failure rate (%)')]:
  fig,axes=plt.subplots(1,2,figsize=(13,5),layout='constrained')
  for ax,ds in zip(axes,DS):
   names=list(dict.fromkeys(r['model'] for r in points if r['dataset']==ds))
   for name in names:
    a=sorted([r for r in points if r['dataset']==ds and r['model']==name],key=lambda r:int(r['L']));x=[float(r[metric]) for r in a];y=np.array([float(r['QPS']) for r in a]);low=np.array([float(r['QPS_min']) for r in a]);high=np.array([float(r['QPS_max']) for r in a]);ax.errorbar(x,y,yerr=[y-low,high-y],marker='o',ms=4,lw=1.3,capsize=2,label=name)
   ax.set_title('WebVid' if ds==DS[0] else 'Yandex');ax.set_xlabel(xlabel);ax.set_ylabel('QPS, median and range of five complete wall batches');ax.grid(alpha=.2);ax.legend(fontsize=8)
  fig.suptitle(title);fig.savefig(folder/(stem+'.png'),dpi=160);fig.savefig(folder/(stem+'.svg'));plt.close(fig)
 fig,axes=plt.subplots(2,3,figsize=(14,8),layout='constrained')
 for di,ds in enumerate(DS):
  for ax,key,ylabel in zip(axes[di],['recall_pct','QPS','failure_rate_pct'],['Recall@10 (%)','QPS (five-run median)','Zero-GT10 failure rate (%)']):
   for name in dict.fromkeys(r['model'] for r in points if r['dataset']==ds):
    a=sorted([r for r in points if r['dataset']==ds and r['model']==name],key=lambda r:int(r['L']));ax.plot([int(r['L']) for r in a],[float(r[key]) for r in a],marker='o',ms=4,label=name)
   ax.set_xscale('log',base=2);ax.set_xticks(LS,[str(L) for L in LS]);ax.set_xlabel('L');ax.set_ylabel(ylabel);ax.set_title(('WebVid' if di==0 else 'Yandex')+' — '+ylabel);ax.grid(alpha=.2)
   if key=='QPS':ax.legend(fontsize=7)
 fig.suptitle(title);fig.savefig(folder/'three_metrics_by_L.png',dpi=160);fig.savefig(folder/'three_metrics_by_L.svg');plt.close(fig)

 # Show a fixed source-row sample of L128 failures; complete all-L union stays in CSV.
 failures=list(csv.DictReader((out/'failures.csv').open()));fig,axes=plt.subplots(1,2,figsize=(13,9),layout='constrained')
 for ax,ds in zip(axes,DS):
  cells=[r for r in failures if r['dataset']==ds and int(r['L'])==128];names=list(dict.fromkeys(r['model'] for r in cells));rows=sorted(set(int(r['source_row']) for r in cells))[:24]
  if not rows:ax.text(.5,.5,'No zero-GT10 failures at L128',ha='center');continue
  lookup={(int(r['source_row']),r['model']):int(r['hits']) for r in cells};mat=np.array([[lookup[row,name] for name in names] for row in rows]);im=ax.imshow(mat,aspect='auto',vmin=0,vmax=10,cmap='YlGnBu');ax.set_xticks(range(len(names)),names,rotation=25,ha='right');ax.set_yticks(range(len(rows)),[str(r) for r in rows]);ax.set_ylabel('Source row');ax.set_title(('WebVid' if ds==DS[0] else 'Yandex')+' — first24 zero-union rows at L128')
  for i in range(len(rows)):
   for j in range(len(names)):ax.text(j,i,str(mat[i,j]),ha='center',va='center',color='white' if mat[i,j]>=6 else 'black',fontsize=8)
 fig.suptitle(title+'\nFailure = zero GT10 hits; all-query/L/method returns and GT remain in failures.csv');fig.savefig(folder/'failure_queries.png',dpi=160);fig.savefig(folder/'failure_queries.svg');plt.close(fig)

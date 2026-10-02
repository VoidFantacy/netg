from pathlib import Path
import csv,json,hashlib,time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1];R=TB/'stages/e115_score_topology_factorial'
rows=list(csv.DictReader((R/'results/metrics.csv').open()));datasets=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];names=['WebVid','Yandex'];cells=[['A_P_GP','C_P_GU'],['B_U_GP','D_U_GU']]
assert len(rows)==72;out=R/'figures';out.mkdir(exist_ok=True);assert not (out/'score_topology.png').exists()
fig,axes=plt.subplots(3,2,figsize=(9.6,10),layout='constrained');plotdata=[]
for r,(K,field,label) in enumerate([(1,'recall','Recall@1'),(100,'recall','Recall@100'),(1,'mean_route_ndc','Router distances')]):
 matrices=[];deltas=[]
 for ds in datasets:
  table={x['method']:x for x in rows if x['dataset']==ds and int(x['K'])==K and int(x['L'])==128};assert len(table)==4
  mat=np.array([[float(table[m][field])*(100 if field=='recall' else 1) for m in row] for row in cells]);matrices.append(mat);deltas.append(mat-mat[0,0])
 v=max(float(np.abs(x).max()) for x in deltas);v=max(v,1e-10)
 for col,(mat,delta) in enumerate(zip(matrices,deltas)):
  ax=axes[r,col];im=ax.imshow(delta,cmap='RdBu' if field=='recall' else 'RdBu_r',vmin=-v,vmax=v)
  ax.set_xticks([0,1],['GT10 graph GP','Unit graph GU'],fontsize=9);ax.set_yticks([0,1],['GT10 score P','Unit score U'],fontsize=9)
  ax.set_title(names[col]+' | '+label,fontsize=11)
  for i in range(2):
   for j in range(2):
    absolute=f'{mat[i,j]:.4f}%' if field=='recall' else f'{mat[i,j]:.2f}'
    diff=f'{delta[i,j]:+.4f} pp' if field=='recall' else f'{delta[i,j]:+.2f}'
    ax.text(j,i,absolute+'\n('+diff+')',ha='center',va='center',fontsize=10,color='white' if abs(delta[i,j])>.62*v else 'black')
    plotdata.append(dict(dataset=datasets[col],K=K,L=128,field=field,method=cells[i][j],absolute=float(mat[i,j]),delta_from_A=float(delta[i,j]),row=i,col=j))
  fig.colorbar(im,ax=ax,shrink=.7,label='Change from A (pp)' if field=='recall' else 'Change from A')
fig.suptitle('GT10 score / router graph factorial\n4096 exposed queries per dataset; fixed NSG; L=128; diagnostic counts',fontsize=13)
fig.savefig(out/'score_topology.png',dpi=180);fig.savefig(out/'score_topology.pdf');plt.close(fig)
(out/'plot_data.json').write_text(json.dumps(dict(created_unix=time.time(),source_sha256=hashlib.sha256((R/'results/metrics.csv').read_bytes()).hexdigest(),rows=plotdata,formal_QPS=False),indent=2)+'\n')
print('Figure created; visual inspection still required')

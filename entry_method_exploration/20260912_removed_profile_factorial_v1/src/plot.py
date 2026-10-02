from shared import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads(8)
d=read(O/'results/diagnosis.json')
fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
for ax,ds,name in zip(axes,DS,['WebVid / removed hub 1627796','Yandex / removed hub 8309868']):
 ms=[next(m for m in d['metrics'] if m['dataset']==ds and m['cell']==cell) for cell in CELLS]
 gains=np.array([m['gain_hits'] for m in ms])*10/1024;loss=np.array([m['loss_hits'] for m in ms])*10/1024
 ax.bar(range(4),gains,color='#2166ac',label='Gross gain');ax.bar(range(4),-loss,color='#b2182b',label='Loss')
 ax.plot(range(4),gains-loss,'ko-',lw=1,ms=4,label='Net');ax.axhline(0,color='gray',lw=.6)
 ax.set(xticks=range(4),xticklabels=['C\ncenter','F\nfull','S\ntarget only','R\nrest only'],ylabel='Recall change from C (pp)',title=name)
axes[0].legend(fontsize=8)
fig.suptitle('E42: all 1,024 queries per dataset; fixed target/rest interventions')
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('whole_pool.'+ext),dpi=170)
plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11,3.6),layout='constrained')
for ax,s,name in zip(axes,d['datasets'],['WebVid','Yandex']):
 cases=sorted(s['cases'],key=lambda x:x['role']!='positive')
 matrix=np.array([[c['hits'][cell] for cell in CELLS] for c in cases])
 ax.imshow(matrix,vmin=0,vmax=10,cmap='Blues',aspect='auto')
 ax.set(xticks=range(4),xticklabels=['C: center','F: full','S: target','R: rest'],yticks=range(2),
        yticklabels=[f"{c['role']}\nrow {c['row']}" for c in cases],title=name+' — frozen case hits / 10')
 for i in range(2):
  for j in range(4):ax.text(j,i,str(matrix[i,j]),ha='center',va='center',color='white' if matrix[i,j]>=6 else 'black',fontsize=15)
fig.suptitle('Selected diagnostic cases; full-pool gains and harms reported separately')
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('frozen_cases.'+ext),dpi=170)
plt.close(fig)
print('2 figures exported as PNG/SVG/PDF')

from control import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

data=read(O/'results/diagnosis.json')['contexts']
batch=list(csv.DictReader((O/'results/batches.csv').open()))
fig,axes=plt.subplots(1,2,figsize=(11,4.4),layout='constrained')
colors=['#2166ac','#67a9cf','#b2182b','#ef8a62']
labels=['WebVid / initial','WebVid / selected','Yandex / initial','Yandex / selected']
for s,color,label in zip(data,colors,labels):
    rows=[x for x in batch if x['dataset']==s['dataset'] and x['context']==s['context']]
    axes[0].plot([int(x['batch']) for x in rows[:3]],[float(x['median_cos_data']) for x in rows[:3]],'o-',color=color,label=label)
    axes[1].plot([int(x['batch']) for x in rows],[float(x['mean_variance']) for x in rows],'o-',color=color,label=label)
axes[0].axhline(0,color='gray',lw=.7);axes[0].axhline(.3,color='gray',ls='--',lw=.8)
axes[0].set(xlabel='Queries per disjoint group',ylabel='Median data-gradient cosine',ylim=(-1,1),xticks=[128,256,512],title='Fixed perturbations: direction agreement')
axes[0].legend(fontsize=8,loc='lower left')
axes[1].set(xlabel='Queries per group',ylabel='Mean conditional variance trace',title='Query sampling uncertainty',xscale='log',yscale='log',xticks=[128,256,512,1024])
axes[1].xaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
axes[1].xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
fig.suptitle('E39: fixed parameters and 8 actions; no optimizer updates',fontsize=13)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('batch_diagnosis.'+ext),dpi=170)
plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(11,4.4),layout='constrained')
pos=np.arange(4)
axes[0].bar(pos-.18,[s['primary512_cos_data'] for s in data],.36,label='Data reward',color='#2166ac')
axes[0].bar(pos+.18,[s['primary512_cos_total'] for s in data],.36,label='Including regularization',color='#d6604d')
axes[0].set(xticks=pos,xticklabels=['WebVid\ninitial','WebVid\nselected','Yandex\ninitial','Yandex\nselected'],ylim=(-1,1),ylabel='Cosine of first / second 512 gradients',title='Preregistered primary split')
axes[0].axhline(0,color='gray',lw=.7);axes[0].axhline(.3,color='gray',ls='--',lw=.8);axes[0].legend(fontsize=8)
axes[1].bar(pos,[s['discriminating_queries'] for s in data],color=colors)
axes[1].set(xticks=pos,xticklabels=['WebVid\ninitial','WebVid\nselected','Yandex\ninitial','Yandex\nselected'],ylabel='Queries with unequal hits among 8 actions',title='Actual hit feedback among 1,024 queries')
for j,s in enumerate(data):axes[1].text(j,s['discriminating_queries']+.5,str(s['discriminating_queries']),ha='center',fontsize=10)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('fixed_contexts.'+ext),dpi=170)
plt.close(fig)
print('2 figures saved as PNG/SVG/PDF')

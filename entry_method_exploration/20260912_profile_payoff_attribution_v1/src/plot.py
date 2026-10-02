from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
contract();s=read(O/'results/diagnosis.json')['contexts'];acts=list(csv.DictReader((O/'results/actions.csv').open()))
labels=['WebVid\ninitial','WebVid\nselected','Yandex\ninitial','Yandex\nselected']
fig,axes=plt.subplots(1,2,figsize=(11,4.4),layout='constrained');x=np.arange(4)
axes[0].bar(x-.18,[a['ceiling_pp'] for a in s],.36,label='Best measured config per query',color='#80b1d3')
axes[0].bar(x+.18,[a['best_static_pp'] for a in s],.36,label='Best single measured config',color='#2166ac')
axes[0].set(xticks=x,xticklabels=labels,ylabel='Recall improvement over fixed center (pp)',title='Observed opportunity within 9 configurations')
axes[0].legend(fontsize=8)
axes[1].bar(x,[a['uncovered_gain']*10/1024 for a in s],label='Gain not covered by best static config',color='#fdb462')
axes[1].bar(x,[a['collateral_loss']*10/1024 for a in s],bottom=[a['uncovered_gain']*10/1024 for a in s],label='Collateral loss of best static config',color='#b2182b')
axes[1].set(xticks=x,xticklabels=labels,ylabel='Gap to per-query best (pp)',title='Coverage and damage are different')
axes[1].legend(fontsize=8)
fig.suptitle('E40: retrospective diagnosis; no new search or model updates',fontsize=13)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('payoff_gap.'+ext),dpi=170)
plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
for ax,cs,label in zip(axes.flat,s,labels):
 a=[r for r in acts if r['dataset']==cs['dataset'] and r['context']==cs['context'] and r['action']!='center']
 gains=np.array([int(r['gross_gain_hits']) for r in a])*10/1024;loss=np.array([int(r['loss_hits']) for r in a])*10/1024
 ax.bar(np.arange(8),gains,color='#2166ac',label='Gross gains')
 ax.bar(np.arange(8),-loss,color='#b2182b',label='Losses')
 ax.plot(np.arange(8),gains-loss,'ko-',lw=1,ms=3,label='Net')
 ax.axhline(0,color='gray',lw=.7);ax.set(xticks=np.arange(8),xlabel='Frozen perturbation action',ylabel='Recall change (pp)',title=label.replace('\n',' / '))
axes[0,0].legend(fontsize=8)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('action_gain_loss.'+ext),dpi=170)
plt.close(fig)
print('Two figures generated in PNG/SVG/PDF.')

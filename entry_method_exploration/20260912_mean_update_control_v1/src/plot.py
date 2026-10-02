from shared import *
threads(8)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rr=read(O/'results/analysis.json');fig,axes=plt.subplots(2,2,figsize=(12,7.6),layout='constrained')
for row,ds in enumerate(DS):
 r=[x for x in rr['contexts'] if x['dataset']==ds];name='WebVid' if row==0 else 'Yandex';x=np.arange(10)
 ax=axes[row,0];ax.bar(x-.18,[v['batch_net_hits'] for v in r],.36,label='Original batch-gradient update');ax.bar(x+.18,[v['full_net_hits'] for v in r],.36,label='Full-train-gradient update')
 ax.set(xticks=x,xticklabels=STEPS,xlabel='Independent frozen pre-update step',ylabel='Net hit change across 4096 queries',title=f'{name}: actual deterministic one-step outcome');ax.axhline(0,color='black',lw=.7);ax.legend(fontsize=8)
 ax=axes[row,1];ax.plot(STEPS,[v['sampled_best_net_hits'] for v in r],'o-',label='Best of original eight actions or no-op (post hoc)')
 ax.plot(STEPS,[v['full_net_hits'] for v in r],'s-',label='Full-gradient deterministic step');ax.set(xlabel='Independent frozen pre-update step',ylabel='Net hit change across 4096 queries',title=f'{name}: sampled opportunity vs actual update');ax.legend(fontsize=8)
 for ax in axes[row]:ax.grid(axis='y',alpha=.18);ax.spines[['top','right']].set_visible(False)
fig.suptitle('Same-state gradient substitution: small positive signal, most updates quality-flat\nNo state is propagated; context totals are not one deployable model',fontsize=14)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'mean_update_control.{ext}',dpi=160)
plt.close(fig);print('E45 plots written')

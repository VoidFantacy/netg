from shared import *
threads(8);resources()
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rr=read(O/'results/analysis.json');fig,axes=plt.subplots(2,3,figsize=(15,8.2),layout='constrained')
for row,ds in enumerate(DS):
 contexts=[x for x in rr['contexts'] if x['dataset']==ds];d=next(x for x in rr['datasets'] if x['dataset']==ds);name='WebVid' if row==0 else 'Yandex'
 x=np.arange(10);ax=axes[row,0]
 ax.bar(x-.18,[r['full_affected_queries'] for r in contexts],.36,label='Full 4096')
 ax.bar(x+.18,[r['old_affected_queries'] for r in contexts],.36,label='Original batch 128')
 ax.set(xticks=x,xticklabels=STEPS,xlabel='Frozen pre-update step',ylabel='Queries with any hit change',title=f'{name}: observed quality feedback');ax.legend(fontsize=8)
 ax=axes[row,1];near=[d['near_gain_hits_all_actions'],-d['near_loss_hits_all_actions']];far=[d['far_gain_hits_all_actions'],-d['far_loss_hits_all_actions']]
 ax.bar([0,1],near,label='Anchor-entry near stratum');ax.bar([0,1],far,bottom=near,label='Complement')
 ax.axhline(0,color='black',lw=.6);ax.set(xticks=[0,1],xticklabels=['Gains','Losses'],ylabel='Hit events across 80 fixed actions',title=f'{name}: gains and harms');ax.legend(fontsize=8)
 ax=axes[row,2];values=[r['U_variance_ratio'] if r['U_variance_ratio'] is not None else np.nan for r in contexts]
 ax.plot(STEPS,values,'o-',label='Per-context variance ratio');ax.axhline(1,color='grey',ls=':',label='Equal variance');ax.axhline(.5,color='firebrick',ls='--',label='Aggregate gate: 0.5')
 ax.set(xlabel='Frozen pre-update step',ylabel='Stratified / uniform U variance',title=f'{name}: aggregate ratio {d["U_variance_ratio"]:.3f}');ax.legend(fontsize=8)
 for ax in axes[row]:ax.grid(axis='y',alpha=.18);ax.spines[['top','right']].set_visible(False)
fig.suptitle('Fixed local actions: full-train effects and conditional sampling variance\nSame W, hub and eight directions; no training or QPS claim',fontsize=14)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'sampling_diagnosis.{ext}',dpi=160)
plt.close(fig)
print('E44 figures written')

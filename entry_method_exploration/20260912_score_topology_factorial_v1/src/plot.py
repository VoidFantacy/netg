from shared import *
threads(8)
sys.path.insert(0,str(R/'entry_method_exploration/20260911_gt10_shared_transform_v1/src/vendor'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=read(O/'results/analysis.json');fig,axes=plt.subplots(2,2,figsize=(11,7))
for col,ds in enumerate(r['datasets']):
 labels=['Joint A','Score only S','Topology only T'];x=np.arange(3);g=[ds[f]['gain_hits'] for f in ['A','S','T']];l=[ds[f]['loss_hits'] for f in ['A','S','T']]
 ax=axes[0,col];ax.bar(x-.18,g,.36,label='Gained hits',color='#2d8c70');ax.bar(x+.18,[-v for v in l],.36,label='Lost hits',color='#bd5b49')
 for xx,a,b in zip(x,g,l):ax.text(xx-.18,a+3,str(a),ha='center',fontsize=9);ax.text(xx+.18,-b-5,str(-b),ha='center',va='top',fontsize=9)
 ax.axhline(0,color='grey',lw=.8);ax.set_xticks(x,labels);ax.set_ylim(-max(l)*1.3,max(g)*1.25);ax.set_title('WebVid' if col==0 else 'Yandex-IP');ax.set_ylabel('Hit changes, summed over fixed actions');ax.legend(fontsize=8)
 ax=axes[1,col];best=[ds[f]['best_net_hits'] for f in ['A','S','T']];coverage=[ds[f]['uncovered_oracle_hits'] for f in ['A','S','T']];own=[ds[f]['own_loss_gap'] for f in ['A','S','T']]
 ax.bar(x,best,label='Best static net',color='#477eaa');ax.bar(x,coverage,bottom=best,label='Uncovered oracle gains',color='#d9ac42');ax.bar(x,own,bottom=np.array(best)+coverage,label='Own losses of best action',color='#bd5b49')
 ax.set_xticks(x,labels);ax.set_ylabel('Per-context oracle decomposition');ax.legend(fontsize=8);ax.grid(axis='y',alpha=.15)
fig.suptitle('Same original 20 contexts / 160 actions: score vs HNSW adjacency\nDiagnostic sums across contexts, not a deployable model',fontsize=12);fig.tight_layout()
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'factorial_mechanism.{ext}',dpi=170)
plt.close(fig)

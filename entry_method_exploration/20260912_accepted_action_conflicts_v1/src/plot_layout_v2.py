from shared import *
threads(8);resources()
assert read(O/'reviews/verification.json')['status']=='PASS'
backup=O/'figures/v1';backup.mkdir()
for ext in ['png','svg','pdf']:shutil.copy2(O/'figures'/f'accepted_action_trajectories.{ext}',backup/f'accepted_action_trajectories.{ext}')
sys.path.insert(0,str(R/'entry_method_exploration/20260911_gt10_shared_transform_v1/src/vendor'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(2,2,figsize=(12,7));colors={'E52':'#267792','E53':'#b96b35','E56':'#728746'}
for col,ds in enumerate(DS):
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  eff=np.load(O/'results'/ds/rec['key']/'effects.npz')
  for row,phase in enumerate(['train','monitor']):
   yy=np.r_[0,np.cumsum(eff[phase+'_delta_hits'].sum(1))/(4096 if phase=='train' else 1024)*10]
   axes[row,col].plot(np.arange(201),yy,'-' if rec['seed']==SEEDS[0] else '--',color=colors[rec['stage']],lw=1.4,label=f'{rec["stage"]} seed{rec["seed"]%100}')
 for row in range(2):axes[row,col].axhline(0,color='grey',lw=.7);axes[row,col].grid(alpha=.2);axes[row,col].set_xlabel('Immutable decision step');None
 axes[0,col].set_title('WebVid' if col==0 else 'Yandex-IP');axes[0,col].set_ylabel('Train4096 recall change (pp)');axes[1,col].set_ylabel('Monitor1024 recall change (pp)')
handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.955),ncol=6,fontsize=9);fig.suptitle('Every accepted action: frozen trajectories, no checkpoint reselection');fig.tight_layout(rect=(0,0,1,.91))
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'accepted_action_trajectories.{ext}',dpi=170,bbox_inches='tight')
plt.close(fig);
dump(O/'reviews/plot_layout_revision.json',dict(status='PRESENTATION_ONLY',reason='Prevent left axis label clipping and put shared legend outside data panels',source='src/plot_layout_v2.py',data_changed=False,old_figures='figures/v1'))

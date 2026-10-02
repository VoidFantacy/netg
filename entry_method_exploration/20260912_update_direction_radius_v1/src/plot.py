from shared import *
threads(8)
sys.path.insert(0,str(R/'entry_method_exploration/20260911_gt10_shared_transform_v1/src/vendor'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
r=read(O/'results/analysis.json');fig,axes=plt.subplots(1,2,figsize=(12,4.5));tags=['M','D25','D50','D100','B25','B50'];x=np.arange(6)
for ax,ds,title in zip(axes,r['datasets'],['WebVid','Yandex-IP']):
 g=[ds['tags'][t]['gain_hits'] for t in tags];l=[ds['tags'][t]['loss_hits'] for t in tags]
 ax.bar(x-.18,g,.36,color='#2e886f',label='Gained hits');ax.bar(x+.18,[-v for v in l],.36,color='#bd584b',label='Lost hits');ax.axhline(0,color='grey',lw=.8)
 ax.set_xticks(x,['Original M','Adam 1/4 r','Adam 1/2 r','Adam 1 r','Best 1/4','Best 1/2'],rotation=25,ha='right');ax.set_title(title);ax.set_ylabel('Hit changes, summed over 20 fixed states');ax.legend(fontsize=8);ax.grid(axis='y',alpha=.15)
fig.suptitle('Larger updates cross discrete search boundaries, but can also cause damage\nFixed original directions and states; diagnostic sums, not a trained model',fontsize=11);fig.tight_layout()
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'direction_radius.{ext}',dpi=170)
plt.close(fig)

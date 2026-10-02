from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
s=read(O/'results/diagnosis.json');quality=read(O/'results/quality.json');figdir=O/'figures';figdir.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
names=['WebVid','Yandex-IP'];colors=['#285a94','#d69a2d','#419476','#b74e78'];fig,axes=plt.subplots(2,2,figsize=(12,8),gridspec_kw={'height_ratios':[2,1]})
for j,x in enumerate(s):
 q={z['method']:z for z in quality if z['dataset']==x['dataset']};methods=['ANN three','Exact three','ef40 three','C8 true triple oracle'];labels=['HNSW\nef=10','Exact\nall profiles','HNSW\nef=40','C8 triple\noracle (GT)'];ys=[q[m]['recall_pct'] for m in methods]
 ax=axes[0,j];bars=ax.bar(range(4),ys,color=colors,width=.64);bars[-1].set_hatch('//');ax.set_xticks(range(4),labels);ax.set_ylim(min(ys)-3,max(ys)+2);ax.set_ylabel('Recall@10 (%)');ax.set_title(names[j]+' — actual three-entry NSG',loc='left',fontweight='bold');ax.grid(axis='y',alpha=.16);ax.set_axisbelow(True)
 for b,y in zip(bars,ys):ax.text(b.get_x()+b.get_width()/2,y+.14,f'{y:.3f}',ha='center',fontsize=10)
 n=x['nonconstant_queries'];counts=[x['A0_in_ann3_nonconstant'],x['A0_seen_nonconstant']-x['A0_in_ann3_nonconstant'],n-x['A0_seen_nonconstant']];left=0;ax=axes[1,j]
 for count,color in zip(counts,['#285a94','#d69a2d','#b6bfc8']):
  width=count/n*100;ax.barh([0],[width],left=left,color=color,height=.5)
  ax.text(left+width/2,0,str(count),ha='center',va='center',color='white' if color=='#285a94' else '#1c2833',fontweight='bold');left+=width
 ax.set_xlim(0,100);ax.set_ylim(-.7,.7);ax.set_yticks([]);ax.set_xlabel('Share of queries with unequal single-entry utility (%)');ax.set_title(f'{names[j]} — {n} informative queries',loc='left',fontweight='bold');ax.spines['left'].set_visible(False)
fig.suptitle('Where useful HNSW entry points are lost',x=.07,ha='left',fontsize=18,fontweight='bold',y=.985)
fig.text(.07,.934,'128 preselected historical training queries per dataset · frozen GT10 graphs · NSG L128 · single thread',fontsize=10,color='#475569')
fig.legend(handles=[Patch(color='#285a94',label='At least one best single entry in final 3'),Patch(color='#d69a2d',label='Best single entry scored, none in final 3'),Patch(color='#b6bfc8',label='No best single entry scored')],loc='lower center',bbox_to_anchor=(.5,.027),ncol=1,frameon=False)
fig.text(.07,.008,'Top: oracle runs all 56 triples and selects using GT; no deployable gain claimed. Bottom: all tied best single entries count.',fontsize=9,color='#475569')
fig.subplots_adjust(left=.075,right=.975,top=.875,bottom=.23,wspace=.24,hspace=.64)
for ext in ['png','svg','pdf']:fig.savefig(figdir/('selection_diagnosis.'+ext),dpi=180,facecolor='white')
plt.close(fig)
dump(O/'reviews/plot_source.json',dict(status='GENERATED_REQUIRES_VISUAL_REVIEW',sources=[str(O/'results/diagnosis.json'),str(O/'results/quality.json')],figures=['selection_diagnosis.png','selection_diagnosis.svg','selection_diagnosis.pdf']))
print('PLOTS_WRITTEN')

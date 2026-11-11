from pathlib import Path
import csv,json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib import font_manager
from matplotlib.lines import Line2D
import numpy as np
W=Path(__file__).resolve().parents[3];R=Path(__file__).resolve().parents[1]
E=W/'entry_method_exploration/20261104_gate_timing_cost_v1'
for n in ['Regular','Bold']:font_manager.fontManager.addfont(str(E/f'storage/fonts/NotoSansSC-{n}.ttf'))
family=font_manager.FontProperties(fname=str(E/'storage/fonts/NotoSansSC-Regular.ttf')).get_name()
plt.rcParams.update({'font.family':family,'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False,'svg.fonttype':'none'})
def read(name):return list(csv.DictReader((R/'analysis'/name).open()))
A=read('stage_attribution_four_multimodal.csv');P=read('original_point_metrics.csv');S=read('stage_effects_and_costs.csv')
DS=['coco','flickr30k','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];CN=dict(zip(DS,['COCO','Flickr30k','WebVid','Yandex']))
LS=[100,128,200,400,800,1000,1200];BLUE,GREEN,ORANGE,GRAY='#276B9C','#16826C','#CF8550','#8D9DA8'
arts=[];figs=[]
def text(fig,x,y,s,size=10,bold=False,color='#263D4F'):
    a=fig.text(x,y,s,va='top',fontsize=size,weight='bold' if bold else 'normal',color=color,linespacing=1.5);arts.append(a);return a
def page(title,subtitle):
    fig=plt.figure(figsize=(12.5,8.5),facecolor='white');text(fig,.055,.955,title,21,True);text(fig,.055,.895,subtitle,10)
    text(fig,.055,.025,'E183既有完整单线程结果的事后复算 · 严格K100命中0–9 · 2026-11-05 · 无新增实验',8,color='#657785');return fig
def save(fig,name):
    fig.canvas.draw();w,h=fig.canvas.get_width_height()
    for a in arts:
        if a.figure is fig:
            b=a.get_window_extent(fig.canvas.get_renderer());assert b.x0>=0 and b.y0>=0 and b.x1<=w+1 and b.y1<=h+1,(name,a.get_text(),b)
    fig.savefig(R/f'figures/{name}.png',dpi=180);fig.savefig(R/f'figures/{name}.svg');figs.append(name);plt.close(fig)
def get(rows,ds,L):return next(x for x in rows if x['dataset']==ds and int(x['L'])==L)

fig=page('低于10%召回的查询：NSG → GT10 → GT10+B32',
         '每个点均为原窗口实测；各子图纵轴尺度不同。相同L的三阶段分解，不是等费用比较。')
for i,ds in enumerate(DS):
    ax=fig.add_axes([.09+(i%2)*.475,.515-(i//2)*.36,.38,.255])
    for m,c,marker,ls,label in [('NSG',GRAY,'o','--','原NSG'),('GT10',BLUE,'s','-','GT10'),('B32',GREEN,'^','-','GT10+B32')]:
        a=sorted([x for x in P if x['dataset']==ds and x['method']==m],key=lambda x:int(x['L']))
        ax.plot(LS,[float(x['low_pct']) for x in a],c=c,marker=marker,lw=1.8,ms=5,ls=ls,label=label)
    ax.set_title(CN[ds],weight='bold',fontsize=12);ax.set_xscale('log',base=2);ax.set_xticks(LS,[str(x) for x in LS],rotation=28,fontsize=8)
    ax.set_xlabel('搜索预算 L',fontsize=9);ax.set_ylabel('低召回查询占比（%）',fontsize=9);ax.grid(alpha=.15);ax.set_ylim(bottom=0)
    if ds=='flickr30k':ax.set_ylim(0,.025);ax.text(.5,.62,'三种方法各L均为 0 / 5,000\n当前窗口无事件，救出率不可评估',transform=ax.transAxes,ha='center',va='center',fontsize=10,color='#506472')
    if ds=='coco':ax.set_ylim(0,.025)
handles=[Line2D([],[],c=c,marker=m,lw=1.8,label=l,ls=ls) for c,m,l,ls in [(GRAY,'o','原NSG','--'),(BLUE,'s','GT10','-'),(GREEN,'^','GT10+B32','-')]]
fig.legend(handles=handles,ncol=3,loc='upper center',bbox_to_anchor=(.5,.855),frameon=False)
text(fig,.06,.087,'COCO在L200：0 → 1 → 1条；Flickr全L均0条。事件稀少时，不能由零变化判断方法普遍无效。',9.5)
text(fig,.06,.053,'“几何迷失”在本图仅表示Recall@100<10%的操作口径，不单凭低召回现象确认几何成因。',9)
save(fig,'01_failure_rate_all_L')

fig=page('分别解决多少：救出、新增与净变化',
         '正柱为跨过10%门槛的救出数，负柱为新增低召回数，黑线为净救出数。两阶段救出率的分母不同。')
for col,ds in enumerate(DS[2:]):
    for row,stage in enumerate(['GT10_vs_NSG','B32_vs_GT10']):
        ax=fig.add_axes([.09+col*.475,.515-row*.36,.38,.255]);a=[get([x for x in S if x['stage']==stage],ds,L) for L in LS];x=np.arange(7)
        ax.bar(x,[int(v['rescued']) for v in a],.62,color=BLUE if row==0 else GREEN,label='救出')
        ax.bar(x,[-int(v['new_low']) for v in a],.62,color=ORANGE,label='新增低召回')
        ax.plot(x,[int(v['net_reduction']) for v in a],c='#344B5D',marker='o',ms=4,lw=1.4,label='净救出')
        ax.axhline(0,color='#798C99',lw=.8);ax.set_xticks(x,[str(L) for L in LS],rotation=25,fontsize=8)
        ax.set_ylabel('查询数');ax.yaxis.set_major_locator(MaxNLocator(integer=True));ax.set_title(CN[ds]+('：GT10相对NSG' if row==0 else '：B32相对GT10'),fontsize=12,weight='bold');ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
        if row==0 and col==0:ax.legend(ncol=3,loc='upper left',bbox_to_anchor=(0,1.28),frameon=False,fontsize=8)
text(fig,.06,.085,'WebVid / L200：GT10救出113条、同时新增24条，净减少89条；B32再救7条、无新增，净减少7条。',9.5)
text(fig,.06,.050,'Yandex / L200：GT10救出128条、同时新增40条，净减少88条；B32再救1条、无新增。',9.5)
save(fig,'02_rescued_and_introduced')

fig=page('L200来源分解：B32修复了哪一部分',
         '将原NSG低召回队列与GT10新引入的低召回队列分开；这是按顺序记账，不是独立因果贡献。')
ax=fig.add_axes([.26,.275,.65,.49]);labels=[];segments=[]
for ds in DS[2:]:
    a=get(A,ds,200);labels += [f"{CN[ds]}：原NSG低召回\n{a['NSG_low']}条",f"{CN[ds]}：GT10新增低召回\n{a['GT10_new_low']}条"]
    segments += [[int(a['GT10_rescued']),int(a['B32_rescued_NSG_legacy']),int(a['NSG_original_final_unresolved'])],[0,int(a['B32_rescued_GT10_induced']),int(a['GT10_induced_final_unresolved'])]]
data=np.array(segments);left=np.zeros(4)
for j,(label,c) in enumerate([('GT10已救出',BLUE),('B32额外救出',GREEN),('最终仍低召回','#BBC8D0')]):
    vals=data[:,j];ax.barh(np.arange(4),vals,left=left,color=c,label=label,height=.58)
    for i,v in enumerate(vals):
        if v:ax.text(left[i]+v/2,i,str(v),ha='center',va='center',fontsize=11,color='white' if j<2 and v>3 else '#21394A')
    left+=vals
ax.set_yticks(np.arange(4),labels,fontsize=10);ax.invert_yaxis();ax.set_xlabel('查询数');ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True);ax.legend(ncol=3,loc='upper left',bbox_to_anchor=(-.02,1.16),frameon=False,fontsize=10)
text(fig,.06,.207,'WebVid：B32救出5条原NSG遗留问题＋2条GT10新增问题，最终仍有24＋22＝46条低召回。',11,bold=True)
text(fig,.06,.151,'Yandex：B32救出1条原NSG遗留问题，未救出GT10新增问题，最终仍有45＋40＝85条。',11,bold=True)
text(fig,.06,.093,'COCO：原NSG为0条，GT10新增1条，B32未修复。Flickr：三阶段均0条，无可用尾部救出事件。',10)
text(fig,.06,.052,'达到10%即记为脱离；不表示达到90%或完整找齐100个近邻。同一查询在不同L重复出现，不跨L累加。',9)
save(fig,'03_L200_source_decomposition')

fig=page('平均召回收益与低召回修复：是两个不同指标',
         '各颜色为同一数据集，连线仅连接七个实测L；星形为L200。不拟合跨数据集因果关系。')
colors=dict(zip(DS,['#8D65A8','#C58C43',GREEN,BLUE]))
for i,stage in enumerate(['GT10_vs_NSG','B32_vs_GT10']):
    ax=fig.add_axes([.09+i*.475,.27,.38,.50])
    for ds in DS:
        a=[get([x for x in S if x['stage']==stage],ds,L) for L in LS]
        xx=[float(x['net_failure_rate_drop_pp']) for x in a];yy=[float(x['mean_recall_gain_pp']) for x in a]
        ax.plot(xx,yy,marker='o',ms=4,c=colors[ds],lw=1.3,label=CN[ds]);ax.scatter(xx[2],yy[2],marker='*',s=180,color=colors[ds],edgecolor='white',lw=.7,zorder=6)
    ax.axvline(0,c='#81919C',lw=.8);ax.axhline(0,c='#81919C',lw=.8);ax.set_title('GT10相对NSG' if i==0 else 'B32相对GT10',weight='bold',fontsize=12)
    ax.set_xlabel('低召回查询比例净下降（百分点）',fontsize=9);ax.set_ylabel('平均Recall@100净增加（百分点）',fontsize=9);ax.grid(alpha=.15);ax.legend(frameon=False,fontsize=9)
text(fig,.06,.185,'COCO / L200：B32平均Recall提高1.3715个百分点，但低于10%的那1条查询没有被修复。',11,bold=True)
text(fig,.06,.128,'WebVid / L200：B32救回20,257个GT成员，其中仅75个来自原低召回队列，占0.37%。',11,bold=True)
text(fig,.06,.072,'因此，当前直接补点的平均收益主要来自常规遗漏补回；尾部救出还须逐L、逐队列单独评估，并付完整查询费用。',9.5)
save(fig,'04_tail_repair_vs_mean_recall')
receipt=dict(status='BUILT_PNG_SVG_PENDING_VISUAL_REVIEW',figures=figs,PDF=False)
(R/'reviews/plot_build.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print('Built',len(figs),'PNG/SVG pairs; no PDF')

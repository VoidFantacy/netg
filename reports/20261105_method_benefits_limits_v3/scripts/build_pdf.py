"""Append benefits, strict low-recall repair and concise limitations to method PDF."""
from pathlib import Path
from collections import defaultdict
import csv,json,hashlib,sys,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import numpy as np

W=Path(__file__).resolve().parents[3];R=Path(__file__).resolve().parents[1]
E=W/'entry_method_exploration/20261104_gate_timing_cost_v1'
T=W/'reports/20261105_low_recall_stage_attribution_v1'
M=W/'reports/20261105_current_method_summary_v1'
def read(p):return list(csv.DictReader(p.open()))
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def write(name,rows):
    with (R/'analysis'/name).open('w',newline='') as f:
        w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=read(E/'analysis/points.csv');A=read(T/'analysis/stage_attribution_four_multimodal.csv');S=read(T/'analysis/stage_effects_and_costs.csv')
OLD=read(W/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/final_v1/points.csv')
DS=['coco','flickr30k','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];CN=dict(zip(DS,['COCO','Flickr30k','WebVid','Yandex']))
LS=[100,128,200,400,800,1000,1200]
groups=defaultdict(list)
for p in P:
    if p['method'] in ['GT10','OPT-B32']:groups[p['dataset'],int(p['K']),int(p['L']),p['method']].append(p)
curves=[]
for (ds,k,L,m),rows in groups.items():
    assert len(rows)==2 and {x['window'] for x in rows}=={'A','B'}
    n=sum(int(x['n']) for x in rows);us=sum(float(x['mean_us'])*int(x['n']) for x in rows)/n
    curves.append(dict(dataset=ds,K=k,L=L,method=m,n=n,recall_pct=100*sum(int(x['hits']) for x in rows)/(n*k),qps=1e6/us,complete_us=us))
write('E199_two_family_curves.csv',curves)
costs=[]
for ds in DS:
    family='soft' if ds.startswith('webvid') else 'hard'
    for k in [1,100]:
        def point(m):return next(x for x in OLD if x['dataset']==ds and int(x['K'])==k and int(x['L'])==200 and x['method']==m)
        g=point('GT10-soft-t1' if family=='soft' else 'GT10-hard');b=point(family+'-JOINT32')
        a=next(x for x in A if x['dataset']==ds and int(x['L'])==200)
        costs.append(dict(dataset=ds,label=CN[ds],K=k,L=200,n=g['n'],GT10_recall_pct=g['recall_pct'],B32_recall_pct=b['recall_pct'],recall_gain_pp=float(b['recall_pct'])-float(g['recall_pct']),GT10_qps=g['qps'],B32_qps=b['qps'],qps_change_pct=(float(b['qps'])/float(g['qps'])-1)*100,extra_us=1e6/float(b['qps'])-1e6/float(g['qps']),B32_extra_low_recall_rescues=a['B32_rescued'] if k==100 else '',low_recall_definition='Recall@100 < 10%' if k==100 else 'not evaluated under K100 tail definition'))
write('E183_L200_benefits_and_costs.csv',costs)
for n in ['Regular','Bold']:font_manager.fontManager.addfont(str(E/f'storage/fonts/NotoSansSC-{n}.ttf'))
family=font_manager.FontProperties(fname=str(E/'storage/fonts/NotoSansSC-Regular.ttf')).get_name()
plt.rcParams.update({'font.family':family,'font.size':10,'pdf.fonttype':42,'svg.fonttype':'none','axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
NAVY,BLUE,GREEN,GRAY='#223D51','#276B9C','#16826C','#8D9DA8'
artists=[];titles=[];figures=[];page_no=3
def txt(fig,x,y,s,size=10,bold=False,color=NAVY):
    a=fig.text(x,y,s,va='top',fontsize=size,weight='bold' if bold else 'normal',color=color,linespacing=1.5);artists.append(a);return a
def new(title,subtitle,source):
    global page_no
    page_no+=1;titles.append(title);fig=plt.figure(figsize=(11.69,8.27),facecolor='white')
    txt(fig,.055,.953,title,21,True);txt(fig,.055,.891,subtitle,9.3)
    txt(fig,.055,.027,source,7.8,color='#627786');txt(fig,.928,.027,f'{page_no:02}',8,color='#627786');return fig
def tab(fig,headers,rows,rect,widths=None,size=9.3):
    ax=fig.add_axes(rect);ax.axis('off');t=ax.table(cellText=rows,colLabels=headers,cellLoc='center',bbox=[0,0,1,1],colWidths=widths);t.auto_set_font_size(False);t.set_fontsize(size)
    for (i,j),c in t.get_celld().items():
        c.set_edgecolor('#D9E4EA');c.set_linewidth(.6);c.PAD=.04
        if i==0:c.set_facecolor(NAVY);c.get_text().set_color('white');c.get_text().set_weight('bold')
        elif i%2==0:c.set_facecolor('#F0F6F5')
    return t
def save(pdf,fig,name):
    fig.canvas.draw();w,h=fig.canvas.get_width_height()
    for a in artists:
        if a.figure is fig:
            b=a.get_window_extent(fig.canvas.get_renderer());assert b.x0>=0 and b.y0>=0 and b.x1<=w+1 and b.y1<=h+1,(name,a.get_text(),b)
    pdf.savefig(fig);fig.savefig(R/f'figures/{name}.png',dpi=180);fig.savefig(R/f'figures/{name}.svg');figures.append(name);plt.close(fig)
def get(rows,ds,L):return next(x for x in rows if x['dataset']==ds and int(x['L'])==L)

extra=R/'reviews/appended_pages.pdf'
with PdfPages(extra,metadata={'Title':'当前方法的收益、低召回修复与局限：新增页'}) as pdf:
    for k in [1,100]:
        fig=new(f'残差收益：Recall@{k}–QPS',
            '只比较GT10与GT10+B32（完整16K表）；右上越好，纵轴为完整单线程QPS的对数刻度。',
            'E199 · 每集1,024条已曝光查询（两批合并） · 仅展示合并曲线 · 2026-11-05图形修订')
        for i,ds in enumerate(DS):
            ax=fig.add_axes([.085+(i%2)*.485,.505-(i//2)*.355,.385,.255])
            for m,c in [('GT10',BLUE),('OPT-B32',GREEN)]:
                rows=sorted([x for x in curves if x['dataset']==ds and x['K']==k and x['method']==m],key=lambda x:x['L'])
                ax.plot([x['recall_pct'] for x in rows],[x['qps'] for x in rows],c=c,lw=2,marker='o',ms=3)
            assert len(ax.lines)==2 and all(line.get_alpha() in (None,1) for line in ax.lines)
            ax.set_title(CN[ds],weight='bold',fontsize=12);ax.set_xlabel(f'Recall@{k}（%）',fontsize=9);ax.set_ylabel('完整单线程 QPS（对数）',fontsize=9)
            ax.set_yscale('log');ax.grid(alpha=.14,which='both');ax.tick_params(labelsize=8)
        fig.legend(handles=[Line2D([],[],c=BLUE,lw=2,label='GT10'),Line2D([],[],c=GREEN,lw=2,label='GT10＋B32直接补点')],ncol=2,loc='upper center',bbox_to_anchor=(.5,.855),frameon=False,fontsize=10)
        line='COCO/WebVid有较明显收益区间；Flickr在小预算等局部有效，Yandex收益弱且窗口间不稳定。' if k==1 else 'COCO/WebVid收益较清楚；Flickr幅度较小、局部有效，Yandex曲线接近或低于GT10。'
        txt(fig,.06,.094,line,10,True)
        txt(fig,.06,.056,'连线仅连接实测L，不能视为精确等Recall测量；并非每个预算都获益。B32采用返回等价的工程优化实现。',8.8)
        save(pdf,fig,f'0{page_no}_recall_k{k}')

    fig=new('低召回修复：NSG → GT10 → GT10+B32',
        '严格定义：单条Recall@100<10%，即命中0–9个；恰好10个排除。各图纵轴尺度不同。',
        'E183完整窗口 · COCO/WebVid/Yandex各10,000条，Flickr5,000条 · 原GT/实际返回已复核')
    styles=[('NSG_low_pct',GRAY,'o','--','原NSG'),('GT10_low_pct',BLUE,'s','-','GT10'),('B32_low_pct',GREEN,'^','-','GT10+B32')]
    for i,ds in enumerate(DS):
        ax=fig.add_axes([.085+(i%2)*.485,.505-(i//2)*.355,.385,.255]);rows=[get(A,ds,L) for L in LS]
        for key,c,m,ls,label in styles:ax.plot(LS,[float(x[key]) for x in rows],c=c,marker=m,ms=4,lw=1.7,ls=ls,label=label)
        ax.set_xscale('log',base=2);ax.set_xticks(LS,[str(L) for L in LS],rotation=28,fontsize=7.5);ax.set_title(CN[ds],fontsize=12,weight='bold');ax.set_xlabel('搜索预算 L',fontsize=9);ax.set_ylabel('低召回查询比例（%）',fontsize=9);ax.grid(alpha=.15);ax.set_ylim(bottom=0)
        if ds in DS[:2]:ax.set_ylim(0,.025)
        if ds=='coco':ax.text(.98,.96,'共10,000条查询\nGT10较NSG新增1条（L100–400）\nB32未新增，也未救回',transform=ax.transAxes,ha='right',va='top',fontsize=8,color=NAVY,bbox=dict(facecolor='white',edgecolor='none',alpha=.88,pad=3))
        if ds=='flickr30k':ax.text(.5,.60,'各L三种方法均0条\n原队列为空，救出率不可评估',transform=ax.transAxes,ha='center',va='center',fontsize=9,color='#566F7F')
    fig.legend(handles=[Line2D([],[],c=c,marker=m,lw=1.7,ls=ls,label=label) for key,c,m,ls,label in styles],ncol=3,loc='upper center',bbox_to_anchor=(.5,.855),frameon=False,fontsize=9)
    txt(fig,.06,.094,'WebVid的B32随七个L额外救出48、30、7、4、0、0、0条；Yandex为0、0、1、1、1、1、1条。',9.2,True)
    txt(fig,.06,.056,'低召回只是这里的“几何迷失”操作标签，不单凭该现象确认几何成因；达到10%也不等于达到高召回。',8.7)
    save(pdf,fig,'06_failure_rate_all_L')

    fig=new('L200分阶段贡献：救出多少，也新增多少',
        'GT10相对NSG统计，B32相对GT10统计；救出率分母不同。以下为固定同L记账，不是独立因果贡献。',
        'E183完整窗口 · 同L非等费用比较 · 四集以外的旧七集数据见原分析CSV · 2026-11-05整理')
    rows=[]
    for ds in DS:
        a=get(A,ds,200);rows.append([CN[ds],a['NSG_low'],a['GT10_low'],a['B32_low'],a['GT10_rescued']+' / '+a['GT10_new_low'],a['B32_rescued']+' / '+a['B32_new_low']])
    tab(fig,['数据','NSG低召回','GT10低召回','+B32低召回','GT10救出 / 新增','B32救出 / 新增'],rows,[.055,.62,.89,.20],[.14,.14,.14,.14,.22,.22],9.5)
    ax=fig.add_axes([.27,.245,.65,.265]);labels=[];data=[]
    for ds in DS[2:]:
        a=get(A,ds,200);labels += [f"{CN[ds]}：NSG原队列 {a['NSG_low']}条",f"{CN[ds]}：GT10新增 {a['GT10_new_low']}条"]
        data += [[int(a['GT10_rescued']),int(a['B32_rescued_NSG_legacy']),int(a['NSG_original_final_unresolved'])],[0,int(a['B32_rescued_GT10_induced']),int(a['GT10_induced_final_unresolved'])]]
    vals=np.array(data);left=np.zeros(4)
    for j,(label,c) in enumerate([('GT10已救出',BLUE),('B32再救出',GREEN),('最终仍低召回','#BBC8D0')]):
        ax.barh(range(4),vals[:,j],left=left,color=c,height=.6,label=label)
        for i,v in enumerate(vals[:,j]):
            if v:ax.text(left[i]+v/2,i,str(v),ha='center',va='center',fontsize=9,color='white' if j<2 and v>3 else NAVY)
        left+=vals[:,j]
    ax.set_yticks(range(4),labels,fontsize=9);ax.invert_yaxis();ax.set_xlabel('查询数',fontsize=9);ax.xaxis.set_major_locator(MaxNLocator(integer=True));ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True);ax.legend(ncol=3,loc='upper left',bbox_to_anchor=(0,1.23),frameon=False,fontsize=9)
    txt(fig,.06,.165,'WebVid：GT10净减少89条，B32再减少7条（5条NSG遗留＋2条GT10新增）。',11,True)
    txt(fig,.06,.112,'Yandex：GT10净减少88条，B32再减少1条；COCO的1条是GT10新增，B32未新增也未救回。',10)
    txt(fig,.06,.065,'不同L中的相同query不能累加成独立救出人数；救出一些查询时，也须保留新增低召回的损伤统计。',8.8)
    save(pdf,fig,'07_stage_contribution')

    fig=new('收益规模、完整成本与局限',
        '下表为E183同L200实测：R为平均Recall，费用为完整单线程查询。相同L的质量/费用取舍不等于前沿获胜。',
        '方法与原始报告保留 · 本版仅整理既有证据，无新增实验、训练或默认变更 · 2026-11-05')
    rows=[]
    for c in costs:
        rows.append([c['label']+' / '+str(c['K']),f"{float(c['GT10_recall_pct']):.4f}",f"{float(c['B32_recall_pct']):.4f}",f"{c['recall_gain_pp']:+.4f}",f"{c['qps_change_pct']:+.2f}",f"{c['extra_us']:+.2f}",c['B32_extra_low_recall_rescues'] if c['K']==100 else '—'])
    tab(fig,['数据 / K','GT10 R%','+B32 R%','ΔR pp','Δ完整QPS %','增加µs/query','额外救出低召回'],rows,[.055,.47,.89,.35],[.17,.13,.13,.12,.14,.15,.16],9.2)
    txt(fig,.06,.438,'最后一列只统计Recall@100<10%的跨门槛救出；K1不混入这一口径。收益是否划算仍需对照附近GT10预算。',8.8)
    txt(fig,.06,.388,'局限一：方法组合与工程实现成分较重',12,True)
    txt(fig,.06,.350,'保留方案依托既有图搜索、画像路由、覆盖选表与精确合并；当前材料对独立算法机制、适用条件和创新性的论证仍不充分。',10.3)
    txt(fig,.06,.263,'局限二：残差收益不全面，平均收益也不等于迷失修复',12,True)
    txt(fig,.06,.225,'收益依赖数据、K/L和候选支持。COCO/WebVid较明确，Flickr局部、Yandex偏弱；COCO的B32增加1.3715pp，却未救出GT10新增的低召回查询。',10.3)
    txt(fig,.06,.145,'WebVid的B32新增20,257个GT命中，仅75个来自原低召回队列，占0.37%；主要作用仍是补常规遗漏。',9.5,True)
    txt(fig,.06,.096,'证据边界：第4–5页为E199每集1,024条曝光查询；本表和尾部为E183完整窗，不混拼绝对QPS；有限预算不代表普适收益。',8.5)
    txt(fig,.06,.058,'这里的工程性是研究定位判断，并非本轮文献新颖性检索结论。当前默认仍为GT10。',8.5)
    save(pdf,fig,'08_benefits_costs_limits')

sys.path.insert(0,str(E/'storage/pdf_renderer'))
import pymupdf
original=M/'ACSG_当前方法总结_GT10与直接残差补点_20261105.pdf'
before=sha(original);final=R/'ACSG_当前方法_残差收益_低召回修复与局限_20261105.pdf'
base=pymupdf.open(original);tail=pymupdf.open(extra);assert len(base)==3 and len(tail)==5
base.insert_pdf(tail);base.set_metadata({'title':'ACSG 当前方法、残差收益、低召回修复与局限','author':'ACSG research','subject':'Current GT10+B32 method; E199 benefit curves; E183 strict low-recall accounting; concise limitations'})
base.save(final,garbage=4,deflate=True);base.close();tail.close();assert sha(original)==before
check=pymupdf.open(final);old=pymupdf.open(original)
for i in range(3):assert check[i].get_text()==old[i].get_text(),i
assert len(check)==8
dump(R/'reviews/pdf_build.json',dict(status='BUILT_PENDING_RENDER_AND_VISUAL_REVIEW',pdf=final.name,pdf_sha256=sha(final),pages=8,original_first_three_pages_text_identical=True,original_pdf_sha256=before,appended_titles=titles,figures=figures,new_experiments=0,default_changed=False))
print('Built 8-page combined PDF; original three pages preserved; appended five pages.')

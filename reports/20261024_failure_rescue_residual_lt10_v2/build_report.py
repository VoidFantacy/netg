#!/usr/bin/env python3
"""Five-page corrected report: strict low-recall query failure by every measured L."""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
from pathlib import Path
import csv,hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Patch

R=Path(__file__).resolve().parent
PDF=R/'ACSG_低于10%召回的查询比例_全L修正版_20261024.pdf'
LABELS=['Deep10M','SIFT10M','GIST1M','WebVid','Yandex','COCO','Flickr30k']
LS=[100,128,200,400,800,1000,1200]
COL={'NSG':'#9aaaba','GT10':'#416e9f','B32':'#168d80'}
INK='#172f40';MUTED='#536b7c';GRID='#e5edf3';GOLD='#daa34f'
for f in ['Regular','Bold']:font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-'+f+'.ttc')
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':10,'pdf.fonttype':3,
    'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False,
    'axes.edgecolor':'#cbd7e0','text.color':INK,'axes.labelcolor':MUTED,
    'xtick.color':MUTED,'ytick.color':MUTED,'savefig.facecolor':'white'})

def rows(name):return list(csv.DictReader((R/name).open()))
S=rows('failure_by_L.csv');C=rows('paired_rescue_by_L.csv')
s={(r['label'],r['method'],int(r['L'])):r for r in S}
c={(r['label'],r['comparison'],int(r['L'])):r for r in C}
H=np.load(R/'per_query_hits.npz')
KEY={r['label']:r['dataset'] for r in S}
def iv(r,k):return int(r[k])
def fv(r,k):return float(r[k]) if r[k]!='' else None
def perc(v,digits=2):return '—' if v is None else f'{v:.{digits}f}%'
def text(fig,x,y,t,size=10,color=INK,**kw):return fig.text(x,y,t,fontsize=size,color=color,va='top',**kw)
def page(n,title,subtitle):
    fig=plt.figure(figsize=(11.69,8.27));text(fig,.05,.955,f'{n:02d}',12,COL['B32'],weight='bold')
    text(fig,.10,.958,title,22,weight='bold');text(fig,.05,.897,subtitle,10.3,MUTED,linespacing=1.5)
    fig.add_artist(plt.Line2D([.05,.95],[.073,.073],transform=fig.transFigure,color=GRID,lw=1))
    text(fig,.05,.045,'ACSG  /  2026-10-24  /  E183原始返回复算  /  严格 Recall@100 < 10%  /  无新ANN或计时',8.2,MUTED)
    text(fig,.95,.045,f'{n} / 5',9,MUTED,ha='right');return fig
def table(fig,rect,cols,data,widths=None,size=10):
    ax=fig.add_axes(rect);ax.axis('off')
    t=ax.table(cellText=data,colLabels=cols,cellLoc='center',loc='center',bbox=[0,0,1,1],colWidths=widths)
    t.auto_set_font_size(False);t.set_fontsize(size)
    for (i,j),cell in t.get_celld().items():
        cell.set_edgecolor('white');cell.set_linewidth(1.5)
        cell.set_facecolor('#e6eef4' if i==0 else ('#f1f6f9' if i%2 else '#ffffff'))
        cell.set_text_props(color=INK,weight='bold' if i==0 else 'normal')
    return t
def save(fig,pdf,n):
    fig.canvas.draw();pdf.savefig(fig)
    fig.savefig(R/f'figures/page_{n:02d}.png',dpi=145);fig.savefig(R/f'figures/page_{n:02d}.svg');plt.close(fig)

def first(pdf):
    fig=page(1,'失败率口径修正：单条查询 Recall 低于10%',
        '每条查询返回100个结果，与该查询的原GT100比较。失败率 = 命中0–9个的查询数 ÷ 全部查询数。')
    text(fig,.05,.822,'9 / 100 = 9% → 计为失败       10 / 100 = 10% → 不计入       99 / 100 = 99% → 不计入',12,COL['B32'],weight='bold')
    text(fig,.05,.762,'GT10的失败率随L变化（单元格：占全部query的比例）',12,weight='bold')
    data=[[lab]+[perc(fv(s[lab,'GT10',L],'low_pct')) for L in LS] for lab in LABELS]
    table(fig,[.05,.34,.90,.365],['数据集']+['L'+str(L) for L in LS],data,[.16]+[.12]*7,size=10.4)
    text(fig,.05,.282,'WebVid：1.92% → 0.53% → 0%       Yandex：1.67% → 0.86% → 0.14%',13,COL['GT10'],weight='bold')
    text(fig,.05,.231,'上行为L100 → L200 → L1200；L改变搜索候选池容量，所以比例必须随L分别报告。',10.4)
    text(fig,.05,.179,'旧PDF把K100“未满100”作主要失败口径，不符合本次问题，已由本修正版取代。\nK=1的召回只有0或100%，不能替代K100的低召回尾部；GT10方法名中的10也不是本门槛。',10.2,MUTED,linespacing=1.5)
    save(fig,pdf,1)

def second(pdf):
    fig=page(2,'各数据集：NSG、GT10与残差的全L失败率',
        '纵轴均为Recall@100 < 10%的query比例；每个点来自真实K100返回。面板纵轴范围不同，请按刻度读取。')
    for i,lab in enumerate(LABELS):
        row,col=divmod(i,4);ax=fig.add_axes([.06+.235*col,.53-.35*row,.197,.245])
        values=[]
        for method in ['NSG','GT10','B32']:
            yy=[fv(s[lab,method,L],'low_pct') for L in LS];values+=yy
            ax.plot(range(7),yy,marker={'NSG':'s','GT10':'o','B32':'^'}[method],ms=3.7,lw=1.6,
                    color=COL[method],label={'NSG':'NSG','GT10':'GT10','B32':'GT10+B32'}[method],
                    linestyle='--' if method=='B32' else '-')
        ax.set_title(lab,loc='left',fontsize=12,weight='bold',pad=9)
        ax.set_xticks(range(7),[str(L) for L in LS],rotation=45,ha='right',fontsize=8)
        ax.set_ylim(-max(max(values)*.055,.004),max(max(values)*1.18,.10))
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=100,decimals=2))
        ax.tick_params(axis='y',labelsize=8);ax.grid(axis='y',color=GRID)
        if i==0:ax.set_ylabel('低召回查询比例',fontsize=9)
        if max(values)==0:ax.text(.5,.4,'三方法均为0条',transform=ax.transAxes,ha='center',color=MUTED,fontsize=10)
    fig.legend(handles=[Patch(facecolor=COL[m],label={'NSG':'NSG','GT10':'GT10','B32':'GT10+B32残差'}[m]) for m in COL],
        loc='upper left',bbox_to_anchor=(.77,.40),frameon=False,fontsize=11)
    text(fig,.77,.265,'L为类别刻度，等距摆放。\n连线只帮助读实测点，\n不代表未测L的预测。',10,MUTED,linespacing=1.5)
    text(fig,.05,.118,'Deep/SIFT/WebVid固定soft，其他固定hard；B32为同家族残差表。GIST 1K query，其余10K，Flickr 5K。',9.8,MUTED)
    save(fig,pdf,2)

def third(pdf):
    fig=page(3,'救回要分两层：改善一点，还是脱离低召回？',
        '两图分母都是同L的原GT10低召回query；“脱离”指从0–9个命中升到至少10个，不代表高召回或找齐100个。')
    for j,(field,count,title) in enumerate([
        ('low_net_improved_pct','low_net_improved_count','A. 有所改善：新命中数 > 原命中数'),
        ('exit_rate_pct','exit_low_count','B. 脱离低召回：新命中数 ≥ 10')]):
        a=np.full((7,7),np.nan)
        for i,lab in enumerate(LABELS):
            for k,L in enumerate(LS):
                v=fv(c[lab,'B32_vs_GT10',L],field)
                if v is not None:a[i,k]=v
        ax=fig.add_axes([.15+.455*j,.30,.385,.48]);cm=plt.get_cmap('YlGnBu').copy();cm.set_bad('#edf1f5')
        ax.imshow(np.ma.masked_invalid(a),cmap=cm,vmin=0,vmax=100,aspect='auto')
        ax.set_xticks(range(7),['L'+str(L) for L in LS],rotation=35,ha='right',fontsize=8.5)
        ax.set_yticks(range(7),LABELS if j==0 else [],fontsize=10)
        ax.tick_params(length=0);ax.set_title(title,loc='left',fontsize=11.5,pad=16,weight='bold')
        for i,lab in enumerate(LABELS):
            for k,L in enumerate(LS):
                r=c[lab,'B32_vs_GT10',L];den=iv(r,'reference_low_count');num=iv(r,count)
                val=fv(r,field);t=f'{val:.1f}%\n{num}/{den}' if den else '—\n0条'
                ax.text(k,i,t,ha='center',va='center',fontsize=8.4,color='white' if val is not None and val>55 else INK)
    text(fig,.05,.206,'WebVid / L200：26/53条有所改善，其中7条升到至少10%，19条改善后仍低于10%。',11,COL['B32'],weight='bold')
    text(fig,.05,.158,'Yandex / L200：5/86条有所改善，其中1条脱离低召回。灰格“—”表示原低召回query为0，救回率无分母。\n样本小的格子波动很大：例如1/1不是普遍100%有效；原始条数必须一起看。',10,MUTED,linespacing=1.5)
    save(fig,pdf,3)

def fourth(pdf):
    fig=page(4,'残差的总体增益，大多来自原本≥10%的查询',
        '固定K100 / L200。将所有实际救回的GT成员，按该query在补全前是否低于10%分组；不是按最终召回率分组。')
    ax=fig.add_axes([.15,.51,.74,.27]);y=np.arange(7)
    low=[fv(c[lab,'B32_vs_GT10',200],'share_rescued_members_from_low_pct') for lab in LABELS]
    ax.barh(y,low,color=GOLD,label='来自原低召回query');ax.barh(y,100-np.array(low),left=low,color=COL['B32'],label='来自原≥10% query')
    ax.set_yticks(y,LABELS,fontsize=10);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('占全部被救回GT成员的比例（%）')
    ax.legend(loc='upper left',bbox_to_anchor=(0,1.20),ncol=2,frameon=False,fontsize=10)
    for i,v in enumerate(low):ax.text(101,i,f'{v:.2f}%',va='center',fontsize=9,color=MUTED)
    data=[]
    for lab in LABELS:
        r=c[lab,'B32_vs_GT10',200];a=s[lab,'GT10',200];b=s[lab,'B32',200]
        data.append([lab,f"{iv(r,'low_net_improved_count')}/{iv(r,'reference_low_count')}",
            f"{iv(r,'exit_low_count')}/{iv(r,'reference_low_count')}",
            f"{iv(r,'low_rescued_members')}/{iv(r,'total_rescued_members')}",f"{100*(fv(b,'qps')/fv(a,'qps')-1):+.2f}%"])
    table(fig,[.05,.165,.90,.25],['数据集','低召回query改善','低召回query脱离','低召回成员救回 / 全部成员救回','完整QPS变化'],data,
        [.15,.17,.17,.32,.19],size=9.8)
    text(fig,.05,.118,'0/0表示没有原低召回query，比例无定义。COCO残差总体增益明显，但L200唯一低召回query未被改善。',9.8,MUTED)
    save(fig,pdf,4)

def fifth(pdf):
    fig=page(5,'L增大与残差补全：解决低召回的效果要分别看',
        '上图固定“GT10 / L200已经低于10%”的同一批query，比较残差或增大L后升到至少10%的条数。\n耗时倍率 = 原GT10/L200 QPS ÷ 各方案QPS，表示完整batch平均查询耗时；费用未配平。')
    for j,lab in enumerate(['WebVid','Yandex']):
        ax=fig.add_axes([.09+.46*j,.565,.36,.20]);ds=KEY[lab];base=H[f'{ds}__GT10__L200'];cohort=base<10
        configs=[('B32',200,'L200+B32'),('GT10',400,'L400 GT10'),('GT10',1200,'L1200 GT10')]
        counts=[int((cohort&(H[f'{ds}__{m}__L{L}']>=10)).sum()) for m,L,_ in configs]
        ax.barh(range(3),counts,color=[COL['B32'],COL['GT10'],COL['GT10']],height=.55)
        ax.set_yticks(range(3),[v[2] for v in configs],fontsize=9);ax.invert_yaxis();ax.set_xlim(0,int(cohort.sum())*1.55)
        ax.set_title(f'{lab}：原低召回{int(cohort.sum())}条',loc='left',fontsize=12,weight='bold',pad=12)
        ax.set_xlabel('同一原低召回队列中，升到至少10%的条数',fontsize=9);ax.grid(axis='x',color=GRID);ax.set_axisbelow(True)
        for i,((m,L,_),v) in enumerate(zip(configs,counts)):
            ratio=fv(s[lab,'GT10',200],'qps')/fv(s[lab,m,L],'qps')
            ax.text(v+.5,i,f'{v}条  /  耗时×{ratio:.2f}',va='center',fontsize=9)
    text(fig,.05,.465,'GT10入口也会同时救回和新增低召回query：L200的成对转移',11,weight='bold')
    data=[]
    for lab in LABELS:
        r=c[lab,'GT10_vs_NSG',200]
        data.append([lab,str(iv(r,'reference_low_count')),str(iv(r,'exit_low_count')),str(iv(r,'enter_low_count')),str(iv(r,'result_low_count'))])
    table(fig,[.05,.195,.90,.235],['数据集','NSG低召回条数','GT10救出原低召回','GT10新增低召回','最终GT10低召回'],data,[.20]*5,size=9.7)
    text(fig,.05,.155,'已测相邻L中，三方法的低召回集合均未观察到新增成员；这是当前返回的事实，不能保证其他图/模型仍单调。',9.6,MUTED)
    text(fig,.05,.117,'此前空间关联分析针对“遗漏量/未满100”，不能直接当作低于10%尾部的结论；多数集尾部仅0–几条，需保留样本限制。',9.6,MUTED)
    save(fig,pdf,5)

def markdown():
    lines=['# Recall@100低于10%的查询比例：全L修正报告','',
        '2026-10-24。用户澄清：失败是**单条查询Recall低于10%**。此前v1将K100未满100作为主要失败口径，不符合该问题；本报告替代其失败率与救回率解释，旧原件保留。','',
        '[五页PDF]('+PDF.name+')。复用E183实际计时返回；7集、K100、7个已测L、三方法共147点、1,176,000次query-point复算；56K唯一query。没有新ANN/GT/训练/性能测量。','',
        '## 口径','',
        '- `r(q)=|返回Top100 ∩ 原GT100|/100`；低召回失败严格为`r(q)<0.10`，即命中0–9个，恰好10个排除。','- 失败率分母为同数据集、同方法、同L的全部query。','- 残差有所改善率：原GT10低召回队列中，新命中数增加的query比例。','- 残差脱离低召回率：原GT10低召回队列中，新命中数至少10的query比例；称“救回”时明确采用该含义。达到10%不代表达到90%或100%。','- 分母为0时比例记为空/—；0条不是0%有效。K1单列不能替代K100尾部。','',
        '## GT10全L失败率','',
        '| 数据集 | '+' | '.join('L'+str(L) for L in LS)+' |','| --- | '+' | '.join(['---']*7)+' |']
    for lab in LABELS:lines.append('| '+lab+' | '+' | '.join(perc(fv(s[lab,'GT10',L],'low_pct')) for L in LS)+' |')
    lines+=['','## L200三方法与残差救回','',
        '| 数据集 | NSG低召回 | GT10低召回 | B32低召回 | 残差有所改善/原低召回 | 残差脱离/原低召回 | 低召回成员救回/全部成员救回 |',
        '| --- | --- | --- | --- | --- | --- | --- |']
    for lab in LABELS:
        r=c[lab,'B32_vs_GT10',200];den=iv(r,'reference_low_count')
        cells=[lab]+[perc(fv(s[lab,m,200],'low_pct')) for m in ['NSG','GT10','B32']]
        cells +=[f"{iv(r,'low_net_improved_count')}/{den}",f"{iv(r,'exit_low_count')}/{den}",f"{iv(r,'low_rescued_members')}/{iv(r,'total_rescued_members')}"]
        lines.append('| '+' | '.join(cells)+' |')
    lines+=['','## 修正后的判断','',
        '1. 失败比例随L明显变化，必须逐L报告，不能固定L200后概括所有工作点。WebVid GT10由L100的1.92%降到L200的0.53%、L1200的0%；Yandex对应1.67%、0.86%、0.14%。',
        '2. 残差能使部分低召回query越过10%门槛，但作用具有数据与L差异。WebVid L100救出48/192（25%），L200救出7/53（13.21%）；Yandex L200为1/86（1.16%）。零队列不可评估救回率。',
        '3. 原低召回query变好，不代表已脱离：Web L200改善26/53，只有7/53越过10%；其余19条仍低于10%。',
        '4. 残差总体Recall增益与严重低召回修复不同。L200只有Web 75/20257（0.37%）、Yandex8/570（1.40%）救回成员来自原低召回队列；COCO13715个成员救回都来自原已≥10%的query。',
        '5. GT10也可能新增严重低召回。L200 Deep由NSG0条变GT10 2条，COCO由0条变1条；需同时报告救出与新增，不能只报净比例下降。',
        '6. 当前所有相邻已测L，三方法低召回集合未观察到新增成员；这只是当前保存返回的事实，不是搜索单调性定理。更大L与残差的对比不是费用匹配实验，PDF单列完整batch平均耗时倍率。',
        '7. 旧空间关联针对成员遗漏量/未满100等结果，不能直接移植成“低于10%”关联。多数数据集该尾部仅0–几条，无法用原广义失败表得出稳定尾部空间规律。当前空间特征保持事后诊断身份。','',
        '## 范围、来源和核验','',
        '固定家族沿用原报告：Deep/SIFT/Web为soft，其他hard，残差均同家族B32；不按L切换赢家。GIST1K、Flickr5K，其余10K。指标保持原始L2/raw-IP与严格ID GT；三轮原QPS中位数不重新测量。','',
        'analyze.py从实际raw/ids.i32与原GT逐条重算，并对齐147点原hits/mean Recall；audit_counts.py以另一份stdlib set/array实现重算全部147点和98组配对，非独立人员审查。恰好10命中单列，避免旧1..10分层越界。输入SHA前后核对。','',
        '[全L三方法统计](failure_by_L.csv) · [成对救回及新增](paired_rescue_by_L.csv) · [低召回query行](low_query_rows.csv) · [全命中数分布](hit_distributions.csv) · [跨L逐query转移](cross_L_query_transitions.csv) · [逐query命中数NPZ](per_query_hits.npz) · [输入SHA](inputs_manifest.json) · [整数核验](integer_audit.json)。','',
        '原E183/E184及v1文件不回写；本目录保存修正前现行文档副本。当前默认GT10保持，无新性能或默认替换。']
    (R/'report_zh.md').write_text('\n'.join(lines)+'\n')

def main():
    assert not (R/'delivery_validation.json').exists(),'delivered report is protected; create new version'
    assert json.loads((R/'integer_audit.json').read_text())['status']=='PASS_STDLIB_SET_RECOMPUTATION'
    (R/'figures').mkdir(exist_ok=True)
    with PdfPages(PDF,metadata={'Title':'ACSG 低于10%召回的查询比例：全L修正版','Author':'ACSG','Subject':'Strict per-query Recall@100 < 10%; all measured L'}) as pdf:
        for fn in [first,second,third,fourth,fifth]:fn(pdf)
    markdown()
    (R/'build_receipt.json').write_text(json.dumps(dict(pdf=PDF.name,pages=5,sha256=hashlib.sha256(PDF.read_bytes()).hexdigest(),
        source_points=147,strict_below_10=True),ensure_ascii=False,indent=2)+'\n')
    print(str(PDF))
if __name__=='__main__':main()

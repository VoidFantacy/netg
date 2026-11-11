"""Read-only E199 synthesis: two main comparisons, stop tested complex branches."""
from pathlib import Path
import csv, hashlib, json, math, sys
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import font_manager
from matplotlib.lines import Line2D
import numpy as np

W = Path(__file__).resolve().parents[3]
R = Path(__file__).resolve().parents[1]
E = W / 'entry_method_exploration/20261104_gate_timing_cost_v1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):
    return list(csv.DictReader((E / 'analysis' / name).open()))
def dump(name, obj):
    (R / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
def write_csv(name, rows):
    with (R / 'analysis' / name).open('w', newline='') as f:
        out = csv.DictWriter(f, list(rows[0])); out.writeheader(); out.writerows(rows)
def num(r, k): return float(r[k])

P, A, S, F, RR = [read(n) for n in ['points.csv','aggregate.csv','stage_aggregate.csv','frontier.csv','rerank_aggregate.csv']]
assert len(P) == 736
DS = ['coco','flickr30k','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
CN = dict(zip(DS, ['COCO','Flickr','WebVid','Yandex']))
def find(rows, ds, k, m):
    return next(r for r in rows if r['dataset'] == ds and int(r['K']) == k and r['method'] == m)

# Pool equal query workloads using time, never arithmetic mean QPS.
groups = defaultdict(list)
for p in P: groups[(p['dataset'],int(p['K']),int(p['L']),p['method'])].append(p)
pooled = []
for (ds,k,l,m), rows in groups.items():
    assert len(rows) == 2 and {r['window'] for r in rows} == {'A','B'}
    n = sum(int(r['n']) for r in rows)
    recall = 100 * sum(int(r['hits']) for r in rows) / (n*k)
    us = sum(num(r,'mean_us')*int(r['n']) for r in rows) / n
    pooled.append(dict(dataset=ds,K=k,L=l,method=m,n=n,recall_pct=recall,mean_us=us,qps=1e6/us))
    if l == 200:
        a = find(A,ds,k,m)
        assert math.isclose(recall,num(a,'recall_pct'),abs_tol=1e-10)
        assert math.isclose(1e6/us,num(a,'qps'),rel_tol=1e-12)
write_csv('pooled_points.csv', pooled)
primary = ['F-PRE90','F-POST90','N-PRE90','N-POST90','N-CPOST90']
pf = [r for r in F if r['method'] in primary]
assert len(pf) == 80 and sum(r['covered']=='True' for r in pf) == 79
uncovered = [r for r in pf if r['covered']!='True']
assert len(uncovered) == 1
assert uncovered[0]['dataset'] == DS[2] and uncovered[0]['window'] == 'A'
assert math.isclose(num(uncovered[0],'quality_threshold_QPS_change_pct'),.025419813646,abs_tol=1e-6)
allgates = [r for r in F if r['method'] in primary or r['method'].endswith('75')]
for ds in DS:
    for k in [1,100]:
        for m in {r['method'] for r in allgates}:
            rows = [r for r in allgates if r['dataset']==ds and int(r['K'])==k and r['method']==m]
            assert not (len(rows)==2 and all(r['covered']!='True' for r in rows))
assert all(r['covered']=='True' for r in F if r['method']=='ALWAYS')

for name in ['Regular','Bold']:
    font_manager.fontManager.addfont(str(E/f'storage/fonts/NotoSansSC-{name}.ttf'))
plt.rcParams.update({'font.family':'Noto Sans SC','font.size':10,'pdf.fonttype':42,
    'svg.fonttype':'none','axes.unicode_minus':False,'axes.spines.top':False,
    'axes.spines.right':False,'axes.titleweight':'bold'})
# Use the registered font's actual family name (varies with font metadata).
plt.rcParams['font.family'] = font_manager.FontProperties(fname=str(E/'storage/fonts/NotoSansSC-Regular.ttf')).get_name()
BLUE, GREEN, GRAY, ORANGE = '#27649A','#19816C','#9AA1A8','#D58B3C'
PDF = R/'残差方法筛选与成本_图解精简版_20261104.pdf'
titles, figs, text_artists = [], [], []
def text(fig,x,y,s,size=10,color='#22384A',bold=False):
    a=fig.text(x,y,s,va='top',fontsize=size,color=color,weight='bold' if bold else 'normal',linespacing=1.55)
    text_artists.append(a); return a
def page(title, subtitle):
    fig=plt.figure(figsize=(11.69,8.27),facecolor='white')
    titles.append(title)
    text(fig,.055,.955,title,21,bold=True)
    text(fig,.055,.895,subtitle,9.5,color='#596975')
    text(fig,.055,.028,'E199 原测量的图解整理 · 2026-11-04 · 无新实验 · 默认不变',8,color='#647684')
    text(fig,.925,.028,f'{len(titles):02}',8,color='#647684')
    return fig
def save(pdf,fig,name):
    fig.canvas.draw()
    width,height=fig.canvas.get_width_height()
    for a in text_artists:
        if a.figure is fig:
            b=a.get_window_extent(fig.canvas.get_renderer())
            assert b.x0>=0 and b.y0>=0 and b.x1<=width+1 and b.y1<=height+1,(name,a.get_text(),b)
    pdf.savefig(fig)
    fig.savefig(R/f'figures/{name}.png',dpi=180)
    fig.savefig(R/f'figures/{name}.svg')
    figs.append(name);plt.close(fig)

def recall_page(pdf,k):
    fig=page(f'Recall@{k}–QPS：主线收敛为原搜索与直接补残差',
             '蓝线：原搜索；绿线：直接补点。灰点汇总复杂流程及其消融，不再逐个列成研究方法。右上越好。')
    for i,ds in enumerate(DS):
        ax=fig.add_axes([.085+(i%2)*.485,.505-(i//2)*.355,.385,.255])
        for m,c in [('GT10',BLUE),('OPT-B32',GREEN)]:
            # Pale A/B curves expose public-window variation; bold curve is descriptive pooling.
            for win in ['A','B']:
                rows=sorted([r for r in P if r['dataset']==ds and int(r['K'])==k and r['method']==m and r['window']==win],key=lambda r:int(r['L']))
                ax.plot([num(r,'recall_pct') for r in rows],[num(r,'qps') for r in rows],c=c,alpha=.2,lw=1)
            rows=sorted([r for r in pooled if r['dataset']==ds and r['K']==k and r['method']==m],key=lambda r:r['L'])
            ax.plot([r['recall_pct'] for r in rows],[r['qps'] for r in rows],c=c,lw=2,marker='o',ms=3,zorder=3)
        cloud=[r for r in P if r['dataset']==ds and int(r['K'])==k and r['method'] not in ['GT10','OPT-B32','Q8-B32','REUSE-SQ']]
        ax.scatter([num(r,'recall_pct') for r in cloud],[num(r,'qps') for r in cloud],c=GRAY,s=15,alpha=.42,zorder=2,edgecolors='none')
        q=find(pooled,ds,k,'Q8-B32')
        ax.scatter(q['recall_pct'],q['qps'],marker='^',s=64,c=GREEN,edgecolor='white',lw=.7,zorder=5)
        sq=find(pooled,ds,k,'REUSE-SQ')
        ax.scatter(sq['recall_pct'],sq['qps'],marker='D',s=38,c='white',edgecolor='#3C4651',lw=1,zorder=5)
        ax.set_title(CN[ds],fontsize=12,pad=7)
        ax.set_xlabel(f'Recall@{k}（%）',fontsize=9)
        ax.set_ylabel('完整单线程 QPS（对数）',fontsize=9)
        ax.set_yscale('log');ax.grid(alpha=.14,which='both');ax.tick_params(labelsize=8.5)
    handles=[Line2D([],[],c=BLUE,lw=2,label='原搜索'),Line2D([],[],c=GREEN,lw=2,label='直接补点（16K表）'),
             Line2D([],[],c=GREEN,marker='^',ls='',ms=7,label='同一补点方法（8K表 / L200）'),
             Line2D([],[],c=GRAY,marker='o',ls='',ms=5,label='复杂流程与消融 / L200'),
             Line2D([],[],c='#3C4651',marker='D',mfc='white',ls='',ms=6,label='既有 SQ 条件对照 / L200')]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.85),ncol=3,fontsize=8.5,frameon=False)
    text(fig,.06,.095,'粗线/大标记为 A/B 各512条的合并描述；浅线为逐窗曲线，灰点为逐窗原值。三轮完整wall用于速度。',9)
    text(fig,.06,.062,'K1控制L32–1000；K100控制L100–1000。门/导航固定L200。折线只连接实测点；两窗均已曝光，不能视为新盲确认。',8.5)
    save(pdf,fig,f'0{1 if k==100 else 2}_recall_k{k}')

with PdfPages(PDF,metadata={'Title':'残差方法筛选与成本：图解精简版','Author':'ACSG research','Subject':'E199 synthesis; no new measurements; prune tested complex branches'}) as pdf:
    recall_page(pdf,100)
    recall_page(pdf,1)

    fig=page('残差开关时机：当前版本停止扩展',
             '只比较同一整段残差流程的三种开关位置；离线固定、搜索前判断、搜索后判断是对照设置。')
    text(fig,.06,.828,'80个主门窗口点中79个被强控制覆盖；剩余一点仅快0.025%，B窗未复现。',13,bold=True)
    methods=['F-STATIC','F-PRE90','F-POST90']; labels=['离线固定','搜索前','搜索后'];colors=['#677887',BLUE,ORANGE]
    timing_rows=[]
    for panel,k in enumerate([1,100]):
        ax=fig.add_axes([.085,.505-panel*.325,.85,.225])
        x=np.arange(4);barw=.23
        for j,(m,label,c) in enumerate(zip(methods,labels,colors)):
            rows=[find(A,ds,k,m) for ds in DS]
            bars=ax.bar(x+(j-1)*barw,[num(r,'mean_us') for r in rows],barw,color=c,label=label)
            for b,r in zip(bars,rows):
                ax.text(b.get_x()+b.get_width()/2,b.get_height()+8,f"{num(r,'recall_pct'):.2f}%",ha='center',va='bottom',fontsize=8,rotation=0)
                timing_rows.append(dict(dataset=r['dataset'],K=k,method=m,recall_pct=r['recall_pct'],complete_us=r['mean_us'],qps=r['qps']))
        ax.set_xticks(x,[CN[ds] for ds in DS]);ax.set_ylabel(f'K{k} 完整 µs/query',fontsize=9)
        ax.set_ylim(0,1350);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
        if panel==0:ax.legend(ncol=3,loc='upper left',bbox_to_anchor=(0,1.2),frameon=False,fontsize=9)
    text(fig,.06,.115,'柱顶为Recall；柱高为完整耗时，越低越好。搜索前/后判断在WebVid、Yandex K100有小幅质量与费用取舍，',9)
    text(fig,.06,.082,'但未形成稳定强前沿收益。同一模型单独移动位置不改答案/工作量；不能据此继续堆门模型或阈值。',9)
    text(fig,.06,.049,'图为整段残差开关；保留直接补点、只开关追加导航的其他对照已纳入80点判定。主搜索始终完整执行。',8.5)
    save(pdf,fig,'03_gate_timing')
    write_csv('timing_comparison.csv',timing_rows)

    fig=page('成本：复杂流程的额外费用主要在哪里',
             '左图用正式完整wall；右图是另行重放的阶段诊断。两者计时边界不同，不能把右图相加当作左图。')
    ax=fig.add_axes([.085,.385,.405,.385]);x=np.arange(4);bw=.19
    for j,(m,label,c) in enumerate([('GT10','原搜索',BLUE),('OPT-B32','直接补点16K',GREEN),('Q8-B32','直接补点8K','#75B9A1'),('ALWAYS','学习筛选＋精排＋导航','#A6ADB4')]):
        rows=[find(A,ds,100,m) for ds in DS]
        ax.bar(x+(j-1.5)*bw,[num(r,'mean_us') for r in rows],bw,label=label,color=c)
    ax.set_xticks(x,[CN[d] for d in DS]);ax.set_ylabel('K100 / L200 完整 µs/query');ax.legend(ncol=2,fontsize=8,frameon=False,loc='upper left',bbox_to_anchor=(0,1.19));ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    ax=fig.add_axes([.59,.385,.34,.385]);left=np.zeros(4);cost_rows=[]
    stage_specs=[('candidate_C_mean_us','候选评分','#9DC7D7'),('student_shortlist_mean_us','学生＋短名单','#78B7B9'),('rerank_total_mean_us','精排局部','#D9A364'),('expansion_mean_us','辅助扩展','#678A9D')]
    for key,label,c in stage_specs:
        vals=[num(find(S,d,100,'ALWAYS'),key) for d in DS]
        ax.barh(np.arange(4),vals,left=left,color=c,label=label)
        if key!='candidate_C_mean_us':
            for i,v in enumerate(vals):ax.text(left[i]+v/2,i,f'{v:.0f}',ha='center',va='center',fontsize=8)
        left+=vals
    ax.set_yticks(np.arange(4),[CN[d] for d in DS]);ax.invert_yaxis();ax.set_xlabel('profile µs/query（不含主搜索）');ax.legend(ncol=2,fontsize=8,frameon=False,loc='upper left',bbox_to_anchor=(-.04,1.19));ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    for ds in DS:
        r=find(S,ds,100,'ALWAYS')
        cost_rows.append(dict(dataset=ds,complete_us=find(A,ds,100,'ALWAYS')['mean_us'],**{key:r[key] for key,_,_ in stage_specs}))
    text(fig,.06,.282,'当前流程增加了候选评分、学生选点、短名单精排和独立辅助扩展；局部精排约20–24µs，',11,bold=True)
    text(fig,.06,.237,'学生＋名单约72–116µs，扩展约148–232µs。每个阶段更便宜，仍需最终Recall–QPS值得付费。',10)
    text(fig,.06,.170,'离线新增：Flickr/Yandex标签286.38秒、学生/教师训练110.19秒；四集门标签74.22秒、门拟合3.29秒。',9)
    text(fig,.06,.126,'COCO/WebVid复用E198，继承成本未归零。模型文件约61.18MiB、门约99.44KiB，均不等于运行内存。',9)
    text(fig,.06,.082,'正式完整batch共1119.37秒，包含于正式进程1711.39秒，不能重复相加；本页没有新增性能测试。',9)
    save(pdf,fig,'04_cost_breakdown');write_csv('cost_breakdown.csv',cost_rows)

    fig=page('精排收益不足以支撑当前复杂分支：停止继续堆叠',
             '在相同8K候选表、单入口384预算下，比较“学生选1”与“短名单重排选1”。图示是实测边际变化。')
    rr=[]
    for k in [1,100]:
        for ds in DS:
            r=next(r for r in RR if r['dataset']==ds and int(r['K'])==k and r['method']=='ALWAYS' and r['reference']=='FAST384')
            rr.append(r)
    x=np.arange(4);bw=.32
    for panel,(key,ylabel) in enumerate([('recall_gain_pp','Recall增加（百分点）'),('formal_extra_us','完整耗时增加（µs/query）')]):
        ax=fig.add_axes([.085+panel*.485,.47,.385,.30])
        for j,(k,c) in enumerate([(1,'#8AAAC4'),(100,ORANGE)]):
            rows=[next(r for r in rr if r['dataset']==d and int(r['K'])==k) for d in DS]
            bars=ax.bar(x+(j-.5)*bw,[num(r,key) for r in rows],bw,label=f'K{k}',color=c)
            for b,r in zip(bars,rows):
                value=num(r,key); offset=(.004 if panel==0 else 2)*(1 if value>=0 else -1)
                ax.text(b.get_x()+b.get_width()/2,value+offset,f"{value:.{3 if panel==0 else 1}f}",ha='center',va='bottom' if value>=0 else 'top',fontsize=8.5)
        ax.set_xticks(x,[CN[d] for d in DS]);ax.set_ylabel(ylabel);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
        ax.set_ylim((-.13,.12) if panel==0 else (0,155));ax.axhline(0,color='#697987',lw=.7)
        ax.legend(ncol=2,frameon=False,fontsize=9,loc='upper left')
    text(fig,.06,.385,'K1无正增益，WebVid还下降0.098个百分点；K100仅增加0.022–0.086个百分点。',11,bold=True)
    text(fig,.06,.330,'K100完整耗时增加23–38µs；K1增加23–129µs。差额含扩展变化；完整级联16个窗口点均被强控制覆盖。',9.3)
    text(fig,.06,.256,'保留：原搜索基线、直接残差补点及已验证的返回等价省费。',12,bold=True,color=GREEN)
    text(fig,.06,.204,'停止：当前学习选点、精排导航、前后置门控版本的扩展和换名重试。',12,bold=True,color='#9A563C')
    text(fig,.06,.145,'历史M5/B32/SQ条件有效结果保留原身份；8K直接表只保留有限网格观察，不能宣称默认替换。',9.3)
    text(fig,.06,.096,'范围：四个多模态集、A/B已曝光窗口、固定图/画像、L200复杂流程、单入口384；不推论所有残差或门控都无效。',9)
    text(fig,.06,.052,'旧实验与16页报告完整归档；本次只改变研究优先级和呈现方式，不重训、不扩点、不改默认。',9)
    save(pdf,fig,'05_rerank_and_decision');write_csv('rerank_marginal.csv',rr)

identity=json.loads((R/'source_before/identity.json').read_text())
for p,h in identity['sources'].items(): assert sha(W/p)==h,p
dump('analysis/derivation_checks.json',dict(status='PASS_DERIVED_NUMBERS_AND_SOURCE_PRESERVATION',source_points=len(P),pooled_points=len(pooled),primary_gate_points=len(pf),covered=79,uncovered=uncovered,all_full_cascade_points_covered=16,pooled_equal_to_existing_aggregate=True,no_new_measurements=True,protected_sources=len(identity['sources'])))
dump('reviews/pdf_build.json',dict(status='BUILT_PENDING_ACTUAL_PDF_RENDER_AND_VISUAL_REVIEW',pdf=PDF.name,sha256=sha(PDF),pages=len(titles),titles=titles,figures=figs))
print(json.dumps(dict(pdf=str(PDF),pages=len(titles),figures=figs),ensure_ascii=False))

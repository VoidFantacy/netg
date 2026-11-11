#!/usr/bin/env python3
"""E185 presentation and current-document synchronization after the fixed probe."""
from pathlib import Path
import csv,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
R=Path(__file__).resolve().parent;A=R/'analysis';REPO=R.parents[1]
REL=str(R.relative_to(REPO));PDF=R/'ACSG_流形相关几何与残差_诊断图_20261024.pdf'
for suffix in ['Regular','Bold']:font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-'+suffix+'.ttc')
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':10,'pdf.fonttype':3,'axes.unicode_minus':False,
    'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#c8d4df','text.color':'#193549',
    'axes.labelcolor':'#536b7c','xtick.color':'#536b7c','ytick.color':'#536b7c'})
S=list(csv.DictReader((A/'dataset_summary.csv').open()));D=list(csv.DictReader((A/'adjusted_associations.csv').open()))
X=list(csv.DictReader((A/'cross_dataset_correlations.csv').open()));labels=[r['label'] for r in S]
COL=['#416e9f','#168d80'];INK='#193549';MUTED='#536b7c'
def f(r,k):return float(r[k]) if r[k]!='' else None
def txt(fig,x,y,t,size=10,color=INK,**kw):fig.text(x,y,t,fontsize=size,color=color,va='top',**kw)
def page(n,title,subtitle):
    fig=plt.figure(figsize=(11.69,8.27));txt(fig,.05,.955,f'{n:02d}',12,COL[1],weight='bold')
    txt(fig,.10,.958,title,21,weight='bold');txt(fig,.05,.895,subtitle,10.3,MUTED,linespacing=1.5)
    fig.add_artist(plt.Line2D([.05,.95],[.074,.074],transform=fig.transFigure,color='#e5edf3'))
    txt(fig,.05,.044,'ACSG  /  E185  /  2026-10-24  /  3584条固定样本 + 56K旧查询分层  /  无新ANN、训练、GT或QPS',8.3,MUTED)
    txt(fig,.95,.044,f'{n} / 2',9,MUTED,ha='right');return fig
def table(fig,rect,columns,rr,size=10):
    ax=fig.add_axes(rect);ax.axis('off');t=ax.table(cellText=rr,colLabels=columns,bbox=[0,0,1,1],cellLoc='center')
    t.auto_set_font_size(False);t.set_fontsize(size)
    for (i,j),cell in t.get_celld().items():
        cell.set_edgecolor('white');cell.set_linewidth(1.4);cell.set_facecolor('#e6eef4' if i==0 else ('#f1f6f9' if i%2 else 'white'))
        cell.set_text_props(color=INK,weight='bold' if i==0 else 'normal')
def save(fig,pdf,num):
    pdf.savefig(fig);fig.savefig(A/f'figure_{num}.png',dpi=170);fig.savefig(A/f'figure_{num}.svg');plt.close(fig)
def plots():
    with PdfPages(PDF) as pdf:
        fig=page(1,'局部几何：近邻共享与遗漏共享',
            '每集固定512条测试query；在合法16K训练query中找最近一条。对照为与最近query具有相同入口重合数的随机query。')
        y=np.arange(7)
        for j,(near,control,title) in enumerate([
            ('nearest_GT_overlap_pct','matched_GT_overlap_pct','A. GT100共享：平均交集数 / 100'),
            ('nearest_missing_coverage_pct','matched_missing_coverage_pct','B. 遗漏共享：覆盖测试遗漏成员的比例')]):
            ax=fig.add_axes([.15+.455*j,.39,.32,.38]);a=[f(r,near) for r in S];b=[f(r,control) for r in S]
            ax.barh(y-.17,a,height=.29,color=COL[1],label='最近训练query');ax.barh(y+.17,b,height=.29,color='#b0becd',label='入口重合数匹配随机query')
            ax.set_yticks(y,labels if j==0 else []);ax.invert_yaxis();ax.set_xlim(0,max(a)*1.28)
            ax.set_title(title,fontsize=11,loc='left',pad=17,weight='bold');ax.grid(axis='x',color='#e5edf3');ax.set_axisbelow(True)
            ax.set_xlabel('比例（%）；两图分母不同')
            for i,(v,w) in enumerate(zip(a,b)):
                ax.text(v+.15,i-.17,f'{v:.2f}',va='center',fontsize=8.5);ax.text(w+.15,i+.17,f'{w:.2f}',va='center',fontsize=8.5)
            if j==0:ax.legend(loc='upper left',bbox_to_anchor=(0,-.16),frameon=False,fontsize=9)
        txt(fig,.05,.24,'COCO：GT100共享 42.00% vs 18.29%；遗漏覆盖 10.51% vs 2.61%。',12,COL[1],weight='bold')
        txt(fig,.05,.191,'遗漏覆盖配对差值 +7.90pp，按query重采样描述区间[6.37, 9.54]pp；不是当前残差表的最终修复率。',10.2)
        txt(fig,.05,.145,'支持局部邻近与目标/遗漏共享有关。匹配仅控制入口重合数量，不配平全部入口ID、频次或库规模，不能解释为因果。\n单例匹配层保留最近query自身（各集2–9条），这些配对不提供几何区分；IP侧余弦只作查询空间诊断。',9.7,MUTED,linespacing=1.5)
        save(fig,pdf,1)
        fig=page(2,'几何有关，不等于“维数越低，残差越有效”',
            '左图局部秩来自GT100目标向量的中心化PCA，属于局部线性紧致度；不是真实流形维数。右图遗漏修复引用原L200/B32。')
        for j,(feat,title) in enumerate([('local_PR100_median','A. 局部有效秩与成员修复率'),('nearest_GT_overlap_pct','B. 邻域共享与成员修复率')]):
            ax=fig.add_axes([.10+.46*j,.54,.35,.24]);xx=[f(r,feat) for r in S];yy=[f(r,'member_repair_pct') for r in S]
            ax.scatter(xx,yy,s=38,color=COL[j]);ax.set_yscale('log');ax.grid(color='#e5edf3',alpha=.8);ax.set_axisbelow(True)
            ax.set_title(title,loc='left',fontsize=11,weight='bold',pad=14)
            ax.set_ylabel('原遗漏成员修复率（%，对数轴）',fontsize=9);ax.set_xlabel('局部有效秩中位数' if j==0 else '最近训练GT100平均重合（%）',fontsize=9)
            for x,y,lab in zip(xx,yy,labels):
                shift=(4,-10) if j==1 and lab=='Yandex' else (4,3)
                ax.annotate(lab,(x,y),xytext=shift,textcoords='offset points',fontsize=8.5)
            ax.margins(x=.17,y=.18)
        data=[[r['label'],f"{f(r,'local_PR20_median'):.1f}",f"{f(r,'local_PR50_median'):.1f}",f"{f(r,'local_PR100_median'):.1f}",f"{f(r,'member_repair_pct'):.3f}%"] for r in S]
        table(fig,[.05,.205,.90,.235],['数据集','GT20局部秩','GT50局部秩','GT100局部秩','L200成员修复率'],data,size=10)
        txt(fig,.05,.16,'七集秩相关：局部GT100有效秩ρ=0.429；最近训练GT100重合ρ=0.964。七集规模/metric/容量密度未配平。',9.8,MUTED)
        txt(fig,.05,.118,'控制原命中段和训练残差频次四分位后，高分离度组改善概率差：COCO +12.04pp，WebVid +1.09pp。\n粗分层不是因果调整；这些是“有所改善”概率差，不是Recall<10%的查询失败率。',9.6,MUTED,linespacing=1.45)
        save(fig,pdf,2)

def report():
    lines=['# E185：流形相关几何与残差收益的具体检查','',
        '**结论：新诊断支持局部几何连续性与遗漏共享有关；不支持用单一“维数越低越有效”规律解释残差。没有证明真实流形因果，也没有得到可直接部署的净收益预测器。**','',
        '[两页图表PDF]('+PDF.name+') · [固定协议](protocol.md)。继承E183七集固定家族、K100/L200/B32；每集512条固定随机query，共3584，另外对全部旧56K查询做双因素分层。原检索metric/图/表/默认不变，无新ANN、训练、GT或QPS。','',
        '## 1. 实测局部连续性','',
        '对每条样本test query，在合法16K残差训练query中寻找最近一条。L2原平方欧氏距离，IP侧用单位query余弦作为查询空间诊断（没有把原raw-IP检索改成余弦）。记录两query GT100共享，以及最近训练query的实际训练遗漏对test遗漏的覆盖。对照为随机训练query，以及与最近query相对test有同样入口重合数量的随机query。','',
        '| 数据集 | 最近query GT重合 | 入口匹配对照GT重合 | 最近query遗漏覆盖 | 入口匹配对照遗漏覆盖 |',
        '| --- | --- | --- | --- | --- |']
    for r in S:lines.append('| '+r['label']+' | '+' | '.join(f"{f(r,k):.2f}%" for k in ['nearest_GT_overlap_pct','matched_GT_overlap_pct','nearest_missing_coverage_pct','matched_missing_coverage_pct'])+' |')
    lines+=['','GT重合为每条query交集成员数/100后取均值；遗漏覆盖为交集遗漏成员总数/样本test遗漏总数，两者分母不同。最近训练query没有恰好重合的query向量（各集按所选距离零值均0）。','',
        'COCO最近训练query的遗漏覆盖比入口匹配对照高7.90pp，按query配对bootstrap描述区间[6.37,9.54]pp。WebVid/Flickr也有明显的局部共享。Deep/SIFT虽然最近query有约5% GT重合，但其最近训练遗漏几乎不覆盖test遗漏，表明“邻居类似”与“会漏相同的点”仍是不同条件。','',
        '**限制：**匹配只控制入口重合数0..3，不是全部入口ID/频次/基线难度的完整匹配。若分层只有最近query自身，就保留自身作对照并报告；各集2–9条，该部分差值0。对照不构成随机干预。配对bootstrap未由第二脚本重算；同一训练邻居可能被复用，query重采样不建模全部共享依赖。','',
        '## 2. 测了局部形状，结果不是简单低维优势','',
        '对GT前20/50/100个目标向量分别中心化，计算局部协方差特征值的participation ratio `(sum λ)^2/sum λ²`，并记录GT100前10方向能量。GT窗口沿原任务排序，不保证是某个base锚点的局部球；因此这是检索目标集合的局部线性紧致度，不能写成严格流形内在维数，窗口变化也不是曲率估计。','',
        '| 数据集 | 局部GT20秩 | GT50秩 | GT100秩 | 原L200成员修复率 |','| --- | --- | --- | --- | --- |']
    for r in S:lines.append('| '+r['label']+' | '+' | '.join(f"{f(r,k):.2f}" for k in ['local_PR20_median','local_PR50_median','local_PR100_median'])+f" | {f(r,'member_repair_pct'):.4f}% |")
    lines+=['','SIFT/Deep局部GT100有效秩约19.69/22.86，COCO为27.59；COCO并不是这些数据中局部秩最低的，却有更高的成员修复率。七集PR20/50/100与成员修复率的Spearman为0.286/0.321/0.429；前10方向能量为−0.643。最近训练GT重合与修复率为0.964。不能据此作跨数据因果归因：库大小、query/GT密度、表槽密度、metric和训练差异未配平。','',
        '## 3. 频次相近时，几何是否仍有关联','',
        '全56K按原GT命中数[0..9,10..49,50..79,80..89,90..94,95..99]与GT100平均训练残差频次四分位分层。层内在几何特征中位数两侧比较，按纳入query数加权；满100查询不纳入改善分析。每侧至少8条。','',
        '| 数据集 | 高背景分离度组改善概率差pp | 纳入原未满100query |','| --- | --- | --- |']
    for r in S:
        a=next(v for v in D if v['dataset']==r['dataset'] and v['scope']=='all_existing_queries' and v['feature']=='background_separation_z' and v['control']=='baseline_hits_and_residual_frequency')
        lines.append(f"| {r['label']} | {f(a,'improved_probability_high_minus_low_pp'):+.2f} | {a['included_queries']} |")
    lines+=['','COCO高GT100方向集中度组也高12.14pp；Web对应1.99pp。局部PR100在512样本、同样分层后的改善概率差方向混合（Deep0、SIFT−1.56、GIST+3.34、Web−7.20、Yandex−1.27、COCO+1.13、Flickr−2.24pp），无简单统一维数规律。Deep样本中无改善，SIFT仅3条；这些差不能视作稳定效应。','',
        '频次可能是几何影响收益的中介。控制频次后减弱不能证明几何无关；剩余关联也不能证明几何直接导致收益。基线和频次分层仍粗，层内混杂未消除。所有几何/GT特征为事后诊断，不能当作免费线上信息。','',
        '## 4. 对机制与新数据集判断的意义','',
        '更具体的待检验链条是：局部几何连续性 → 相邻query共享近邻目标 → 某些搜索遗漏跨query重复 → 有限入口表能迁移补回。此次直接补充了前两项共享测量，支持这条链的一部分；图的有限搜索如何造成重复遗漏、表容量与完整费用仍是另外环节。','',
        '在局部近似d维、采样密度稳定等假设下，半径r的小邻域质量可近似写为μ(q,r)≈c(q)r^d；n条独立训练query中至少一条落入该邻域的概率为1−(1−μ)^n。这是条件模型，用来说明维数、密度、训练量共同决定局部覆盖；现有PCA秩不等于该d，也未拟合该公式。更低维不保证图遗漏相同，更高共享也不保证支付补点费用后净收益为正。','',
        '新数据集值得测的候选指标是：训练query对查询分布的局部覆盖、近邻集合共享、遗漏共享在独立校准query上的迁移，并结合L/容量/完整wall比较；不能仅凭当前七集相关给一个维数阈值。当前没有新准入器、门控或默认替换。','',
        '## 5. 核验、成本和原件保护','',
        '成功诊断123.540秒；另有一次入口匹配单例失败，原代码/日志/空输出目录保留，失败wall未记录，修正范围见correction_01.json。第二份stdlib集合/秩/分层核验3584条配对、10752组GT/遗漏集合、168秩相关和126组分层差，不导入主分析器/NumPy。14个Gram/SVD一致性及56个全16K距离直接核对由主进程不同代数路径检查；未称独立人员审查。小输入SHA前后不变，大base仅核stat并继承旧身份，读取的GT100样本向量另存SHA。','',
        '此前严格Recall<10%的全L报告仍有效；本轮结果中的“改善/遗漏共享”不是低召回失败率，不能互相替代。原E183/E184/两版失败率PDF和seal不回写。','',
        '[逐集结果](analysis/dataset_summary.csv) · [3584逐query](analysis/sample_query_metrics.csv) · [分层关联](analysis/adjusted_associations.csv) · [跨集相关](analysis/cross_dataset_correlations.csv) · [整数/秩第二实现](analysis/audit.json) · [运行收据](analysis/receipt.json)。','',
        '参考：[局部维数与检索难度](https://arxiv.org/abs/1907.07387)、[近邻目标频次与数据分布](https://www.jmlr.org/papers/v11/radovanovic10a.html)。文献不证明当前残差机制因果。']
    (R/'report_zh.md').write_text('\n'.join(lines)+'\n')

def sync():
    def edit(name,old,new):
        p=REPO/name;t=p.read_text();assert t.count(old)==1,(name,old);p.write_text(t.replace(old,new))
    edit('summary.md','最新研究是[E184空间分布与失败修复诊断](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/report_zh.md)；最新正式性能是',
        '最新研究是[E185流形相关几何探查]('+REL+'/report_zh.md)，承接[E184空间分布诊断](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/report_zh.md)；最新正式性能是')
    edit('summary.md','两轮各自已完成，','上述诊断与性能轮次各自已完成，')
    edit('summary.md','## 残差与空间分布的判断\n\n',
        '## 残差与空间分布的判断\n\nE185新补3584条固定样本局部PCA和最近训练query对照，另对56K原query增加基线/频次双因素分层。**支持局部几何连续性与遗漏共享有关，不支持单一“越低维越有效”。** COCO最近训练GT100重合42.00%，入口重合数匹配对照18.29%；训练遗漏覆盖10.51% vs 2.61%（是单条最近训练query的覆盖，不是B32最终修复率）。\n\nCOCO局部GT100有效秩27.59，高于SIFT19.69/Deep22.86，却有更高残差修复率。原命中段与训练残差频次分层后，高分离度组改善概率差COCO+12.04pp、Web+1.09pp；局部秩差值方向跨集混合。PCA秩不是真实流形维数；粗分层/七集相关不能作因果或新数据净收益准入器。完整[结果与局限]('+REL+'/report_zh.md)。\n\n')
    edit('summary.md','E184成功诊断170.346秒、','E185成功诊断123.540秒，另有单例匹配失败日志（失败wall未知）；第二份stdlib集合/秩/分层核验通过，仍无新ANN/GT/训练/QPS。E184成功诊断170.346秒、')
    edit('spec.md','## 7. 构建、来源与重跑依赖',
        '## 6.1 E185流形相关几何探查\n\n['+REL+'/]('+REL+'/report_zh.md)只读旧角色/GT/主返回。每集PCG64 seed20261025取512条：GT20/50/100目标向量中心化Gram谱计算局部participation ratio；该量不是流形维数。对合法16K训练query的最近query，L2原平方欧氏，IP单位query余弦仅诊断，不改原raw-IP。配对随机/入口重合数匹配对照；单例层保留自身并报告。另对56K旧几何按命中段与残差频次四分位描述分层。输出逐query CSV/NPZ、Gram/SVD检查、二实现核验、图表与PDF。GT特征均事后，未实现线上门控或新准入规则；旧metric/计时合同不变。\n\n## 7. 构建、来源与重跑依赖')
    edit('s-target.md','E184诊断、E183性能矩阵均已完成。','E185/E184诊断、E183性能矩阵均已完成。')
    edit('s-target.md','## 优先三：检验几何是否提供额外、可部署的信息\n\n',
        '## 优先三：检验几何是否提供额外、可部署的信息\n\n[E185]('+REL+'/report_zh.md)已支持局部邻近与GT/遗漏共享有关，局部有效秩无统一方向，不能归结为简单低维优势。下一问题收窄为：局部训练覆盖/邻域共享能否在未知query上预测同等完整费用下的净收益，并在频次、规模和容量控制后保留解释力。当前只有曝光数据的离线关联，尚无新准入器或执行队列。\n\n')
    edit('s-experiment.md','最新研究是E184离线诊断；','最新研究是E185局部几何探查；')
    edit('s-experiment.md','| E184 |','| E185 | 流形相关局部几何与遗漏共享 | 3584固定样本/56K分层；支持局部连续性关联，无简单低维规律或净收益准入器 | [卡片](experiment_history/185_manifold_residual_probe_v1.md) |\n| E184 |')
    edit('LOCAL_CODEX_START.md','6. [E184报告]',
        '6. [E185局部几何报告]('+REL+'/report_zh.md)、[3584样本](./'+REL+'/analysis/sample_query_metrics.csv)、[第二实现核验]('+REL+'/analysis/audit.json)；本轮无新性能。\n7. [E184报告]')
    edit('LOCAL_CODEX_START.md','E184复算七集56K已有查询，','E185在固定样本上测局部形状和最近训练query共享，支持局部连续性与遗漏共享有关，未证明真实流形因果或形成净收益准入器。E184复算七集56K已有查询，')
    edit('readme.md','## 最新研究\n\n',
        '## 最新研究\n\n- [E185：流形相关局部几何与残差]('+REL+'/report_zh.md)。3584固定样本：COCO局部邻近与GT/遗漏共享明显，局部有效秩无简单统一规律；无新性能、门控或准入器。[两页图表PDF]('+REL+'/'+PDF.name+')。\n')
    edit('experiment_history/README.md','最新诊断是[E184](184_residual_geometry_diagnosis_v1.md)，','最新诊断是[E185](185_manifold_residual_probe_v1.md)，')
    edit('experiment_history/README.md','| [184_residual_geometry_diagnosis_v1.md]',
        '| [185_manifold_residual_probe_v1.md](185_manifold_residual_probe_v1.md) | E185：流形相关局部几何与残差遗漏共享 |\n| [184_residual_geometry_diagnosis_v1.md]')
    card='''# E185：流形相关局部几何与残差遗漏共享

2026-10-24，用户要求具体检查流形关系，完成固定离线诊断。继承E183七集/K100/L200/固定家族B32；每集512条，共3584条，另对原56K几何统计做双因素分层。无新ANN/GT/训练/QPS，默认GT10保持。

测量GT20/50/100目标集合局部PCA参与秩（不是流形维数），以及最近合法训练query与随机/入口重合数匹配对照的GT共享和遗漏共享。COCO最近训练GT100重合42.00% vs匹配18.29%，遗漏覆盖10.51% vs2.61%；Web/Flickr也较明显。COCO局部GT100秩27.59，不比SIFT19.69/Deep22.86更低，跨集不支持简单低维优势。局部连续性关联与维数规律必须分开。

原命中段与训练残差频次四分位分层后，COCO高背景分离度组改善概率仍高12.04pp，Web1.09pp；局部秩效果方向混合。粗分层非因果，频次可能是中介；七集规模/metric/图/训练与容量密度未配平。最近训练GT重合与成员修复率跨七集ρ=0.964，不是普遍准入规则。所有GT特征属于事后诊断，不提供新数据集净收益保证。

成功wall123.540秒；第一尝试排除最近训练query后遇匹配单例失败，代码/日志/空输出保留，失败wall未知。修正仅在单例层保留自身（各集2–9条，差值0），没有改样本或模型。第二份stdlib集合/秩/分层核对3584配对、10752集合、168相关/126分层差；主进程14 Gram/SVD与56全16K直接距离检查通过。同作者不同实现，bootstrap未第二实现复算。无新性能或默认替换。

后续问题是局部训练覆盖/邻域共享能否预测未知query在同等完整费用下的收益，尚未实现准入器或线上门控。原严格Recall<10%全L报告保留其口径，不能被本轮广义遗漏关联替代。诊断收口，无待恢复矩阵。

'''
    card+='[完整报告](../'+REL+'/report_zh.md) · [协议](../'+REL+'/protocol.md) · [两页PDF](../'+REL+'/'+PDF.name+') · [逐集结果](../'+REL+'/analysis/dataset_summary.csv) · [核验](../'+REL+'/analysis/audit.json) · [收据](../'+REL+'/analysis/receipt.json)。\n'
    (REPO/'experiment_history/185_manifold_residual_probe_v1.md').write_text(card)

def main():
    assert not (R/'delivery_validation.json').exists(),'delivered artifacts protected'
    assert json.loads((A/'audit.json').read_text())['status']=='PASS_SECOND_STDLIB_SET_RANK_STRATA_IMPLEMENTATION'
    plots();report()
    if '--figures-only' in sys.argv:return
    sync()
    (R/'README.md').write_text('# E185：流形相关几何与残差\n\n[中文报告](report_zh.md) · [两页图表PDF]('+PDF.name+') · [固定协议](protocol.md)。\n\n仅离线诊断，样本和模型冻结；无新任务ANN、GT、训练或QPS。原件保护、样本与频次分层、指标限制、失败修正和费用均在报告及analysis收据。\n')
    print('BUILT and synchronized E185',PDF)
if __name__=='__main__':main()

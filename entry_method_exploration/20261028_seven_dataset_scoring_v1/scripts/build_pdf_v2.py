"""Detailed Chinese PDF, authorized after the scientific matrix was frozen."""
import os
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[name]='1'
import csv, datetime, hashlib, json, math, sys, unicodedata
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
sys.path.insert(0,'/tmp/acsg_e187_pdf_tool')
import fitz
R=Path(__file__).resolve().parents[1]
PDF=R/'E191_七数据集_K1_K100_综合测试报告.pdf'
DS=['deep10m_l2_v1','sift10m_bigann_l2_v1','gist1m_l2_v1','coco','flickr30k','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
LABEL=dict(zip(DS,['Deep10M','SIFT10M','GIST1M','COCO','Flickr30k','WebVid','Yandex10M']))
METHODS=['GT10','B32','REUSE-PQ','REUSE-SQ','MAIN-SQ']
COLORS=dict(zip(METHODS,['#1d4ed8','#64748b','#d97706','#dc2626','#059669']))
def rows(path):return list(csv.DictReader(path.open())) if path.exists() else []
def f(x,key):return float(x[key]) if x.get(key) not in [None,''] else float('nan')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def wrap(text,width=138):
    lines=[];line='';used=0
    for c in text:
        n=2 if unicodedata.east_asian_width(c) in 'WF' else 1
        if c=='\n' or used+n>width:
            lines.append(line);line='';used=0
            if c=='\n':continue
        line+=c;used+=n
    if line:lines.append(line)
    return lines
class Pages:
    def __init__(self,out):self.out=out;self.n=0;self.titles=[];self.date=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')
    def page(self,title,subtitle=''):
        self.n+=1;self.titles.append(title);fig=plt.figure(figsize=(11.69,8.27),facecolor='white')
        fig.text(.045,.948,title,fontsize=18,weight='bold',color='#0f172a',va='top')
        if subtitle:fig.text(.047,.902,subtitle,fontsize=8.7,color='#475569',va='top')
        fig.text(.045,.026,'E191  |  真实 K1 / K100  |  完整单线程 wall  |  历史曝光测试，一套图/画像  |  '+self.date,fontsize=7.5,color='#64748b')
        fig.text(.95,.026,str(self.n),fontsize=8,ha='right',color='#64748b');return fig
    def save(self,fig):self.out.savefig(fig);plt.close(fig)
def notes(fig,items,y=.83,size=10,width=138,step=.029,x=.05):
    for item in items:
        for line in wrap(item,width):fig.text(x,y,line,fontsize=size,va='top',color='#1e293b');y-=step
        y-=.012
    return y
def table(fig,head,data,box,size=8.8,widths=None):
    if not data:data=[['—']*len(head)]
    ax=fig.add_axes(box);ax.axis('off')
    tab=ax.table(cellText=data,colLabels=head,colWidths=widths,cellLoc='center',bbox=[0,0,1,1])
    tab.auto_set_font_size(False);tab.set_fontsize(size)
    for (i,j),cell in tab.get_celld().items():
        cell.set_edgecolor('#dbe3ec');cell.set_linewidth(.5)
        cell.set_facecolor('#e5eef8' if i==0 else '#f6f8fb' if i%2==0 else 'white')
        if i==0:cell.set_text_props(weight='bold',color='#1e3a5f')
    return tab
def plot(ax,point_rows,ds,K,title):
    any_rows=False
    for m in METHODS:
        p=sorted([x for x in point_rows if x['dataset']==ds and x['K']==str(K) and x['method']==m],key=lambda x:int(x['L']))
        if not p:continue
        any_rows=True;ax.errorbar([f(x,'recall_pct') for x in p],[f(x,'qps') for x in p],
           yerr=[[f(x,'qps')-f(x,'qps_min') for x in p],[f(x,'qps_max')-f(x,'qps') for x in p]],
           color=COLORS[m],fmt='-o',ms=2.5,lw=1,capsize=2,label=m)
    ax.set_title(title,fontsize=10);ax.set_xlabel('Recall (%)',fontsize=8);ax.set_ylabel('完整 T1 QPS',fontsize=8);ax.tick_params(labelsize=7);ax.grid(alpha=.2)
    if any_rows:ax.legend(fontsize=6.7,loc='best')
    else:ax.text(.5,.5,'该 K 无追加控制',ha='center',va='center',transform=ax.transAxes)
def main():
    assert (R/'primary_complete.json').exists() and (R/'dense_complete.json').exists()
    auth=json.loads((R/'delivery_authorization_update.json').read_text());assert auth['user_request']=='这个弄完做个pdf吧，我明天看'
    rec=json.loads((R/'reviews/report_build.json').read_text());interpretation=json.loads((R/'reviews/interpretation.json').read_text());points=rows(R/'analysis/all_primary_points.csv');pairs=rows(R/'analysis/all_paired.csv');coverage=rows(R/'analysis/all_coverage.csv');strata=rows(R/'analysis/all_source_strata.csv');dense=rows(R/'analysis/all_dense_points.csv');confirmed=rows(R/'analysis/confirmed_screens.csv');cost=rows(R/'analysis/cost_ledger.csv');diag=rows(R/'analysis/scoring_diagnostic.csv');loss=rows(R/'analysis/merge_loss_summary.csv')
    get=lambda ds,K,m:next(x for x in points if x['dataset']==ds and x['K']==str(K) and x['method']==m and x['L']=='200')
    pair=lambda ds,K,m:next(x for x in pairs if x['dataset']==ds and x['K']==str(K) and x['method']==m and x['L']=='200')
    cov=lambda ds,m:next(x for x in coverage if x['dataset']==ds and x['K']=='100' and x['method']==m and x['L']=='200')
    font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams.update({'font.family':'Noto Sans CJK JP','axes.unicode_minus':False,'pdf.fonttype':3,'font.size':9})
    with PdfPages(PDF,metadata={'Title':'E191 七数据集 K1/K100 来源、评分与完整费用综合测试','Author':'ACSG','Subject':'Actual measured Recall/QPS and source coverage; detailed Chinese report'}) as out:
        doc=Pages(out)
        fig=doc.page('七数据集综合测试：先看结果与适用范围','原矩阵 448 点 / 1344 轮；另一次密集控制 '+str(rec['dense_points'])+' 点 / '+str(rec['dense_batches'])+' 轮')
        overview=[]
        for ds in DS:
            b=get(ds,100,'GT10');s=get(ds,100,'REUSE-SQ');p=pair(ds,100,'REUSE-SQ');c=cov(ds,'REUSE-SQ')
            overview.append([LABEL[ds],f"{f(b,'recall_pct'):.4f} / {f(b,'qps'):.1f}",f"{f(s,'recall_pct'):.4f} / {f(s,'qps'):.1f}",f"{f(p,'recall_delta_pp'):+.4f}",f"{f(p,'extra_time_pct'):+.1f}%",f"{c['scanned_covered']}/{c['members_missing']}"])
        table(fig,['K100 / L200','GT10 Recall% / QPS','SQ Recall% / QPS','ΔRecall pp','完整耗时增幅','扫描覆盖/原遗漏'],overview,(.045,.47,.91,.36),8.5)
        notes(fig,[f"112个SQ来源/预算点中，相对GT10原网格筛选阳性{rec['primary_positive_points']}个；一次冻结密集控制后保留{rec['retained_exploratory_points']}个探索点。默认E99 GT10保持。",
            '评分准确性、遗漏来源覆盖、完整查询费用分别判断。源外救回证明扩展了旧残差ID来源，不等于证明完全不依赖训练邻域。',
            '共享较强/弱来自既有观测，并非人工因果配平；本轮分别给出全部七集、两K及完整预算控制。',
            '详细数据CSV、协议与授权说明嵌入PDF附件；实际timed包和模型保留在项目storage，未把诊断上限当免费线上方法。'],y=.42,size=10)
        doc.save(fig)
        fig=doc.page('详细结论：哪些已证实，哪些还没有？','以下判断依据全部七集结果与一次密集控制；具体数字可回查后续页面和PDF附带CSV')
        notes(fig,interpretation['conclusions'],y=.83,size=10.5,step=.031)
        doc.save(fig)
        fig=doc.page('数据与角色：到底测了哪些共享情形？','旧E185的最近训练query诊断：每集固定512条；本轮不是新共享标签或因果实验')
        catalogue={x['dataset']:x for x in rec['catalogue']};data=[]
        for x in cost:
            h=catalogue[x['dataset']];data.append([LABEL[x['dataset']],f"{int(x['N']):,} × {x['d']}",x['metric'],x['test_queries'],f"{h['old_GT100_overlap_pct']:.2f}%",f"{h['old_nearest_training_missing_coverage_pct']:.2f}%",x['family']+'/'+x['H']])
        table(fig,['数据','base N×d','原metric','test n','旧GT100重合','旧最近训练遗漏覆盖','固定家族/H'],data,(.045,.49,.91,.35),8.4)
        notes(fig,['Deep/SIFT的最近训练邻域重合与遗漏覆盖很低；COCO/Flickr较高，Web居中。GIST/Yandex另按各自实测保留，不能仅按多模态/单模态命名推断来源可用性。',
            '最近训练query的遗漏覆盖，与整个旧16K残差ID并集覆盖是不同量。后者在本轮按实际GT10遗漏重新计算并分层。',
            '原图、原metric与GT10画像不改；IP不变成cosine，L2不新增归一化。固定家族、H、维度、库规模和训练密度并未因果配平。',
            '新块表只用合法前12K同教师遗漏；末4K不拟合、不选配置。B32沿旧16K表，仅作正式参考。测试query历史已曝光，无新的系统盲确认。'],y=.44,size=10)
        doc.save(fig)
        fig=doc.page('方法与公平计量：来源、评分、精算分别控制')
        table(fig,['方法','候选来源与访问','近似评分','追加原metric精算'],[
            ['GT10','原画像路由 + 原图主搜索','无补全','0'],['B32','三行旧ID表去重，排除主返回','无近似筛选','实际候选数，≤96'],
            ['REUSE-PQ','三个hub各8块 + 主返回最高8块；扫描≤2048','global PQ','≤96'],
            ['REUSE-SQ','与REUSE-PQ逐query同pool/扫描块与顺序','SQ8','≤96'],
            ['MAIN-SQ','仅真实主返回最高8块；实际≤1024；K1仅1块','SQ8','≤96']],(.045,.51,.91,.33),8.5)
        notes(fig,['K1实际只返回/消费一个主结果，对GT1评测；K100真实返回100、对GT100评测。两K固定共享K100教师表及96精算上限，不称各K最优。',
            'MAIN-SQ去掉训练遗漏块表，同时改变来源信息和实际访问量；它不是纯共享因果消融，原GT10仍有监督。',
            '完整wall包含正常Batch分配/初始化、路由、主搜、全部补全、六数组复制与销毁。加载、预热、保存、hash、GT和oracle在外，suite另记。',
            '串行单方法、CPU15、实际1线程、OMP/BLAS等均1；每点三轮交错顺序，报告中位数与范围。PQ/SQ/块中心/精算次数分别计，不能相加冒充总NDC或阶段耗时。',
            'PQ通常M16，Yandex d200合法适配M20；SQ码为d字节，PQ码为M字节。SQ全部原base minmax编码，无query/GT训练；旧资产构建债不清零。'],y=.46,size=9.5,step=.028)
        doc.save(fig)
        for K in [1,100]:
            fig=doc.page(f'完整单线程表现：K={K}，固定 L200','每格为 Recall (%) / QPS；全部来自本轮同一计时窗口，三轮QPS中位数')
            data=[]
            for ds in DS:data.append([LABEL[ds]]+[f"{f(get(ds,K,m),'recall_pct'):.4f}%\n{f(get(ds,K,m),'qps'):.2f}" for m in METHODS])
            table(fig,['数据']+METHODS,data,(.045,.29,.91,.54),9.3)
            notes(fig,['同L提高Recall但降低QPS是费用取舍；综合收益还须与更大L的GT10比较。B32和PQ参考始终保留。',
                '完整平均query耗时增幅 = QPS_GT10 / QPS_method − 1；它与QPS降幅不是同一个百分比。小样本变化同时看成员/查询原始计数与描述性区间。'],y=.23,size=10)
            doc.save(fig)
        fig=doc.page('K100/L200覆盖链：扫描到了什么，保住多少？','成员发生次数；不能当成修复同数量的query。PQ与SQ逐query扫描集合一致')
        data=[]
        for ds in DS:
            p=cov(ds,'REUSE-PQ');s=cov(ds,'REUSE-SQ');z=pair(ds,100,'REUSE-SQ')
            data.append([LABEL[ds],s['members_missing'],z['missing_in_old_source'],s['pool_covered'],s['scanned_covered'],p['shortlist_covered'],s['shortlist_covered'],s['rescued'],z['rescued_source_out'],z['members_damaged']])
        table(fig,['数据','原遗漏','旧全源内遗漏','池覆盖','扫描覆盖','PQ短名单','SQ短名单','SQ最终救回','旧源外救回','损伤'],data,(.04,.43,.92,.4),7.7)
        notes(fig,['PQ→SQ只约束当前已扫描候选的评分损失；它不能救回当前扫描范围外的遗漏。pool→scan是当前块代表排序与预算损失，scan→shortlist是评分/96容量损失。',
            'shortlist→final还取决于原metric精算、严格Top-K、重复向量/GT-ID与浮点边界；全量保留并分类，未修改GT。',
            '源外为旧16K完整残差ID并集之外，不是仅B32之外，也不代表从未出现于任何GT10监督。共享因果结论不由这一列推出。'],y=.37,size=10)
        doc.save(fig)
        fig=doc.page('相对GT10有价值，是否也超过已有补全？','所有比较限于同窗口、同K的实际已测点；中位QPS覆盖与三轮范围另行保留')
        assessment=rows(R/'analysis/candidate_assessment.csv');data=[]
        for ds in DS:
            a=[x for x in assessment if x['dataset']==ds and x['decision']=='RETAIN_EXPLORATORY']
            data.append([LABEL[ds],len(a),sum(bool(x['existing_B32_dominating_L']) for x in a),sum(bool(x['existing_PQ_dominating_L']) for x in a),sum(x['median_nondominated_in_available_grid']=='True' for x in a)])
        table(fig,['数据','GT10探索门保留','其中被B32覆盖','其中被PQ覆盖','未被任何已测方法覆盖'],data,(.045,.43,.91,.4),8.7)
        notes(fig,['GT10探索门保留只说明相对默认参照有局部研究价值；若旧B32或PQ已以更高/相同Recall及中位QPS覆盖它，则尚无优于已有补全的证据。B32/PQ覆盖列可重叠。',
            '全部候选仍按原GT10筛选结论保留，不修改原门或新增测试点。本表是已有实测结果的进一步说明；有限网格未覆盖不等于已证明全局最佳。',
            'B32沿旧16K训练表，新块表12K；它是可用参考，训练量没有配平。中位QPS覆盖不等于统计显著损伤，三轮不重叠控制另列CSV。'],y=.37,size=10)
        doc.save(fig)
        fig=doc.page('MAIN-SQ：不读训练遗漏块表，还能补回多少？','K100/L200；原主返回和实际扫描量同时变化，不能当纯来源或纯共享因果消融')
        data=[]
        for ds in DS:
            p=pair(ds,100,'MAIN-SQ');x=get(ds,100,'MAIN-SQ');r=pair(ds,100,'REUSE-SQ')
            data.append([LABEL[ds],f"{f(p,'recall_delta_pp'):+.4f}",f"{f(p,'extra_time_pct'):+.2f}%",p['members_rescued'],p['rescued_source_out'],f"{f(x,'scanned_codes_per_query'):.1f}",f"{f(x,'exact_scores_per_query'):.1f}",f"{f(r,'recall_delta_pp')-f(p,'recall_delta_pp'):+.4f}"])
        table(fig,['数据','MAIN Δpp','MAIN额外耗时','MAIN救回','其中旧源外','MAIN扫码/q','精算/q','REUSE额外Δpp'],data,(.04,.43,.92,.4),8.3)
        notes(fig,['MAIN-SQ保留原GT10的监督，只去掉追加的训练遗漏块表。它检验真实主返回的局部块能否提出新候选，而非无监督系统。',
            '若MAIN接近REUSE且费用更低，表明这一固定版本中追加块表/更多访问带来的边际收益有限；是否综合胜出仍按密集同窗口GT10控制判断。',
            'K1只有一个真实主返回块，实际≤128码，故不能把K100的MAIN覆盖或费用借给K1。'],y=.37,size=10)
        doc.save(fig)
        for ds in DS:
            c=next(x for x in cost if x['dataset']==ds)
            fig=doc.page(LABEL[ds]+'：两K的完整曲线与固定L对照',f"{c['N']} × {c['d']}，{c['metric']}，test n={c['test_queries']}；线段仅连接实际L，误差线为三轮范围")
            plot(fig.add_axes((.075,.53,.385,.30)),points,ds,1,'K1：原矩阵')
            plot(fig.add_axes((.565,.53,.385,.30)),points,ds,100,'K100：原矩阵')
            data=[]
            for m in METHODS:
                a=get(ds,1,m);b=get(ds,100,m);p=pair(ds,100,m) if m!='GT10' else None
                data.append([m,f"{f(a,'recall_pct'):.4f} / {f(a,'qps'):.1f}",f"{f(b,'recall_pct'):.4f} / {f(b,'qps'):.1f}",f"{f(p,'recall_delta_pp'):+.4f}" if p else '—',f"{f(p,'extra_time_pct'):+.1f}%" if p else '—',f"{p['members_rescued']}/{p['members_damaged']}" if p else '—',p['rescued_source_out'] if p else '—'])
            table(fig,['L200','K1 Recall% / QPS','K100 Recall% / QPS','K100 Δpp','额外耗时','救回/损伤','旧源外'],data,(.045,.285,.91,.17),8.2)
            s=cov(ds,'REUSE-SQ');p=cov(ds,'REUSE-PQ');n=[x for x in confirmed if x['dataset']==ds];kept=[x for x in n if x['decision']=='RETAIN_EXPLORATORY']
            notes(fig,[f"K100/L200：原遗漏{s['members_missing']}；扫描覆盖{s['scanned_covered']}；PQ→SQ短名单{p['shortlist_covered']}→{s['shortlist_covered']}；SQ最终救回{s['rescued']}。",
                f"原网格SQ方法筛选阳性{len(n)}点；密集同窗口后保留{len(kept)}点。"+('对应K/L/来源保留作场景候选。' if kept else '本固定版本尚未通过密集探索门，不能外推所有后继无效。'),
                '曲线为原矩阵窗口；下一部分单列密集控制窗口。完整各L、计数、区间与来源分层见PDF附带CSV。'],y=.23,size=9.2,step=.028)
            doc.save(fig)
        for ds in DS:
            cases=[x for x in confirmed if x['dataset']==ds]
            if not cases:continue
            fig=doc.page(LABEL[ds]+'：一次冻结的密集GT10控制','只比较本补充窗口；候选模型、来源、码数及精算预算不变，不与原窗口绝对QPS拼接')
            plot(fig.add_axes((.075,.55,.385,.28)),dense,ds,1,'K1：密集控制窗口')
            plot(fig.add_axes((.565,.55,.385,.28)),dense,ds,100,'K100：密集控制窗口')
            table(fig,['K','方法','L','原筛选速度差%','密集速度差%','密集预算Δpp','密集决定'],[[x['K'],x['method'],x['L'],f"{f(x,'primary_speed_delta_pct'):+.2f}",f"{f(x,'dense_speed_delta_pct'):+.2f}",f"{f(x,'dense_budget_recall_delta_pp'):+.4f}",x['decision'].replace('RETAIN_EXPLORATORY','保留探索').replace('COVERED_BY_DENSE_GT10','被密集GT10覆盖').replace('NO_DENSE_SCREEN_PASS','未通过密集门')] for x in cases],(.045,.15,.91,.30),7.6)
            notes(fig,['探索门：达到候选Recall的最快已测GT10上，速度≥+2%且三轮同向；或完整费用内最佳GT10之上Recall≥+0.05pp。',
                '有限离散控制不是精确等Recall；一次补充后收口，不迭代细分到通过。保留探索点不等于默认替换或新盲确认。'],y=.115,size=8.3,step=.023)
            doc.save(fig)
        fig=doc.page('旧源外查询：原遗漏完全不在旧残差来源时的表现','K100/L200，事后按GT分层；no_old_source不是线上可见门控特征')
        data=[]
        for ds in DS:
            for m in ['REUSE-SQ','MAIN-SQ']:
                x=next((z for z in strata if z['dataset']==ds and z['K']=='100' and z['L']=='200' and z['method']==m and z['stratum']=='no_old_source'),None)
                if x:data.append([LABEL[ds],m,x['queries'],x['members_missing'],f"{f(x,'recall_delta_pp'):+.4f}",x['members_rescued'],x['members_damaged']])
        table(fig,['数据','方法','query数','原遗漏成员','ΔRecall pp','救回','损伤'],data,(.045,.28,.91,.55),8.5)
        notes(fig,['这是在原遗漏对整个旧16K源覆盖为零的query上统计；结果不能改称整个系统从未使用监督。其他覆盖比例层及K1完整数据在all_source_strata.csv。',
            '原主返回已完整的query单列no_missing，零分母没有包装成100%修复。数据来源与预算可支付性须同时判断。'],y=.22,size=9.6)
        doc.save(fig)
        tail=[x for x in pairs if x['K']=='100']
        for start in range(0,len(DS),2):
            group=DS[start:start+2];selected=[x for x in tail if x['dataset'] in group]
            fig=doc.page('严重失败与恢复：'+' / '.join(LABEL[x] for x in group),'严重失败严格为GT100交集0–9；恰好10排除。成员数与query数分别计')
            table(fig,['数据','方法','L','原0–9','现0–9','原失败改善','脱离0–9','新增0–9','完整恢复q','损伤成员'],[[LABEL[x['dataset']],x['method'],x['L'],x['original_lt10'],x['final_lt10'],x['lt10_improved'],x['lt10_escaped'],x['new_lt10'],x['complete_recovered_queries'],x['members_damaged']] for x in selected],(.035,.14,.93,.70),7.1)
            notes(fig,['“有所改善”“脱离严重失败”“完整恢复”互不替代；很少的尾部个例不外推。全query分布与K1零命中恢复在附带all_paired.csv。'],y=.10,size=8.5,step=.023)
            doc.save(fig)
        for start in range(0,len(diag),21):
            fig=doc.page('评分只读诊断：同一扫描ID上的float64精确96','每集固定128query、seed20261028；未改在线参数，不是免费在线方法或原生反事实')
            table(fig,['数据','K','方法','样本原遗漏','扫描覆盖','实际短名单','精确96覆盖'],[[LABEL[x['dataset']],x['K'],x['method'],x['original_missing'],x['scanned_missing'],x['actual_shortlist_missing'],x['float64_exact96_missing']] for x in diag[start:start+21]],(.045,.18,.91,.65),8.0)
            notes(fig,['精确96只在实际扫描候选中按原metric float64排序。它可帮助区分近似评分损失与96容量，不提供当前扫描范围外的覆盖。',
                '全量shortlist→final损失另逐例检查重复向量不同ID与分数边界；未修改严格GT-ID或并列规则。'],y=.13,size=8.8,step=.024)
            doc.save(fig)
        fig=doc.page('短名单到最终返回：严格GT-ID损失的全量分类','以下为跨两K/全部原预算累加的成员事件；不是去重query数。重复向量与近边界可重叠')
        data=[]
        for ds in DS:
            for m in ['REUSE-PQ','REUSE-SQ','MAIN-SQ']:
                a=[x for x in loss if x['dataset']==ds and x['method']==m]
                data.append([LABEL[ds],m,sum(int(x['shortlist_to_final_lost']) for x in a),sum(int(x['lost_with_identical_vector']) for x in a),sum(int(x['lost_near_boundary']) for x in a)])
        table(fig,['数据','方法','短名单→返回损失','有完全相同向量的其他ID','靠近最终距离边界'],data,(.045,.18,.91,.65),8.1)
        notes(fig,['边界分类是只读诊断，不修改GT、并列ID或严格Recall口径；近边界阈值见posthoc_scoring.py。重复向量与边界列不互斥，不能相加当总损失。'],y=.12,size=9,step=.025)
        doc.save(fig)
        fig=doc.page('实际成本：查询费用、suite与辅助内存分别看')
        table(fig,['数据','主suite分','内含timed分','补充suite分','采样峰RSS GiB','辅助数组MiB','本轮模型MiB'],[[LABEL[x['dataset']],f"{f(x,'formal_suite_seconds')/60:.2f}",f"{f(x,'formal_internal_seconds')/60:.2f}",f"{f(x,'dense_suite_seconds')/60:.2f}",f"{f(x,'formal_sampled_peak_RSS_GiB'):.2f}",f"{f(x,'auxiliary_array_MiB'):.1f}",f"{f(x,'owned_model_MiB'):.1f}"] for x in cost],(.04,.43,.92,.4),8.3)
        notes(fig,['suite包含内部timed、预热、保存与oracle，不重复相加。旧图/GT/画像/教师以及复用块/码本历史构建债不清零，完整冷启动总费用未知。',
            '共同benchmark装载的辅助数组和RSS，不等于默认GT10部署依赖或某单方法的最低内存。离线准备可多线程，实际线程与耗时在cost_ledger.csv；正式全部实际1线程。',
            '新增大产物在/root/acsg-e191-storage，经项目storage链接。实际timed原raw保留，重建trace可无损gzip并保留原SHA；未删除旧科学证据。',
            '完整QPS与操作次数没有给出粗路由/解码/筛选/精算/合并的阶段占比，本报告不从总wall指认单一时间瓶颈。'],y=.37,size=9.7)
        doc.save(fig)
        fig=doc.page('核验、证据限制与接续边界')
        hist=sum(json.loads((R/f'reviews/results_audit_{ds}.json').read_text())['historical_full_packets_equal'] for ds in DS)
        notes(fig,[f"已完成：原448点/1344轮 + 一次密集{rec['dense_points']}点/{rec['dense_batches']}轮；资格140点另计。历史GT10/B32完整返回包{hist}点一致；全部真实timed包三轮bits/SHA、补全oracle和预算核验通过。",
            '第二份stdlib实现复算质量、成员/查询救损、扫描覆盖链、严格严重失败与离散预算参照。训练hub表全部重建，SQ编码/原metric/筛选阈值另抽检；同一执行者不同实现，不称独立人员复现。',
            '5000次配对bootstrap仅作描述，无多比较调整或语义IID保证，未由第二实现独立重算；三轮计时不是三份独立质量样本。所有公共test历史已曝光，一套图/画像，无新系统盲确认。',
            f"密集控制后保留{rec['retained_exploratory_points']}个场景探索点。保留对应数据/K/L/来源，先核相邻预算、损伤与实际费用，再冻结合法新查询确认；不自动修改E99默认。",
            '若当前源/扫描覆盖低，单纯改评分不能越过覆盖上限；若扫描内目标已保住，继续改评分的增益空间应另核。降低费用或扩大来源均属后继提案，本轮未自动启动。',
            '主报告：entry_method_exploration/20261028_seven_dataset_scoring_v1/report_zh.md；当前根文档：summary.md、spec.md、s-target.md、s-experiment.md。旧E190科学seal保持。',
            '用户后续明确要求完成后制作PDF；旧冻结no_PDF字段是此前交付计划，科学矩阵和停止条件未因交付格式改变。PDF包含汇总CSV/协议附件，完整原包由项目storage复现。'],y=.83,size=10,step=.029)
        doc.save(fig)
        page_titles=doc.titles
    attachments=['analysis/all_primary_points.csv','analysis/all_dense_points.csv','analysis/all_paired.csv','analysis/all_coverage.csv','analysis/all_source_strata.csv','analysis/all_discrete_comparisons.csv','analysis/all_dense_comparisons.csv','analysis/confirmed_screens.csv','analysis/cost_ledger.csv','analysis/scoring_diagnostic.csv','analysis/merge_loss_summary.csv','protocol.md','delivery_authorization_update.json','reviews/interpretation.json','analysis/all_method_dominance.csv','analysis/candidate_assessment.csv']
    pdf=fitz.open(PDF)
    for name in attachments:
        p=R/name;pdf.embfile_add(p.name,p.read_bytes(),filename=p.name,ufilename=p.name,desc='E191 measured evidence / frozen contract')
    tmp=R/'reviews/pdf_with_attachments.pdf';pdf.save(tmp,garbage=4,deflate=True);pdf.close();os.replace(tmp,PDF)
    v=dict(source_script=str(Path(__file__).resolve()),source_sha256=sha(Path(__file__)),status='PASS_E191_DETAILED_PDF_BUILD',path=str(PDF),pages=len(page_titles),page_titles=page_titles,attachments=[dict(path=x,sha256=sha(R/x)) for x in attachments],pdf_sha256=sha(PDF),generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),explicit_PDF_authorization=auth['user_request'],scientific_configuration_changed=False)
    (R/'reviews/pdf_build.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v[k] for k in ['status','path','pages','pdf_sha256']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()

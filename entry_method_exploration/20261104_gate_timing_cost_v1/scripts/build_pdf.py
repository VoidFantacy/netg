from common import *
import textwrap,unicodedata
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import font_manager
FONT=str(R/'storage/fonts/NotoSansSC-Regular.ttf');BOLD=str(R/'storage/fonts/NotoSansSC-Bold.ttf')
font_manager.fontManager.addfont(FONT);font_manager.fontManager.addfont(BOLD)
plt.rcParams.update({'font.family':font_manager.FontProperties(fname=FONT).get_name(),'font.size':9,'pdf.fonttype':42,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
def load(name):
    with open(R/'analysis'/name) as f:return list(csv.DictReader(f))
A=load('aggregate.csv');G=load('gate_aggregate.csv');S=load('stage_aggregate.csv');RR=load('rerank_aggregate.csv');D=load('pre_post_summary.csv');P=load('points.csv');F=load('frontier.csv');facts=read(R/'analysis/summary_facts.json');cost=read(R/'analysis/cost_ledger.json');audit=read(R/'analysis/analysis_receipt.json');stdlib=read(R/'analysis/stdlib_audit.json')
cn={'coco':'COCO','flickr30k':'Flickr','webvid2_5m_light_v1':'WebVid','yandex_t2i_official10M_ip_v1':'Yandex'}
lookup=lambda rows,ds,K,m:next(r for r in rows if r['dataset']==ds and int(r['K'])==K and r['method']==m)
f=lambda r,k:float(r[k]) if r[k] not in ['',None] else None
num=lambda x,d=2:'NA' if x in ['',None] else f'{float(x):.{d}f}'
PDF=R/'E199_残差门控时机与精排成本_20261104.pdf';titles=[];artists=[];page=0
def wrap(s,width=104):
    lines=[];line='';n=0
    for ch in str(s):
        if ch=='\n':lines.append(line);line='';n=0;continue
        w=2 if unicodedata.east_asian_width(ch) in 'WF' else 1
        if n+w>width:lines.append(line);line='';n=0
        line+=ch;n+=w
    if line:lines.append(line)
    return '\n'.join(lines)
def text(fig,x,y,s,size=10,color='#213647',weight='normal',width=None):
    a=fig.text(x,y,wrap(s,width) if width else s,fontsize=size,color=color,weight=weight,va='top',linespacing=1.5);artists.append(a);return a
def new(title,subtitle=''):
    global page
    page+=1;titles.append(title);fig=plt.figure(figsize=(11.69,8.27),facecolor='white');text(fig,.055,.955,title,21,weight='bold');text(fig,.055,.895,subtitle,9.5,color='#536675');text(fig,.055,.032,'E199 · 2026-11-04 · CPU15 / 实际单线程 · 两曝光窗口 · 完整wall为性能判据',7.5,color='#657584');text(fig,.92,.032,f'{page:02}',8,color='#657584');return fig
def tab(fig,headers,rows,rect,size=8.3,widths=None):
    ax=fig.add_axes(rect);ax.axis('off');t=ax.table(cellText=rows,colLabels=headers,cellLoc='center',colLoc='center',bbox=[0,0,1,1],colWidths=widths);t.auto_set_font_size(False);t.set_fontsize(size)
    for (i,j),cell in t.get_celld().items():
        cell.set_edgecolor('#dbe4eb');cell.set_linewidth(.45);cell.PAD=.03
        if i==0:cell.set_facecolor('#213f57');cell.get_text().set_color('white');cell.get_text().set_weight('bold')
        elif i%2==0:cell.set_facecolor('#f2f6f9')
    return t
def save(pdf,fig):
    fig.canvas.draw();w,h=fig.canvas.get_width_height()
    for a in artists:
        if a.figure is fig:
            box=a.get_window_extent(fig.canvas.get_renderer());assert box.x0>=-1 and box.x1<=w+1 and box.y0>=-1 and box.y1<=h+1,(page,a.get_text(),box)
    pdf.savefig(fig);plt.close(fig)
with PdfPages(PDF,metadata={'Title':'E199 残差门控时机与精排成本','Author':'ACSG research','Subject':'Four multimodal datasets, pre/post residual gating, complete single-thread wall'}) as pdf:
    fig=new('残差开关时机与精排成本','COCO / Flickr / WebVid / Yandex · 真实Recall@1、Recall@100 · 主研究L200')
    text(fig,.055,.83,'本轮门控尚无稳定替换强基线的收益。',14,weight='bold')
    text(fig,.055,.775,f"完成 {facts['points']} 点 / {facts['batches']} 轮完整单线程测量；主门策略 {facts['primary_gate_points']} 个窗口点。",11)
    text(fig,.055,.73,f"其中 {facts['primary_covered']} 点被同期强控制覆盖；{facts['primary_range_covered']} 点的覆盖也通过三轮速度观测范围检查。",11)
    text(fig,.055,.68,'比较对象：离线固定开关、主搜索前预测、主搜索后预测；同一PRE模型挪到POST位置作为单变量对照。',10.5,width=136)
    rows=[]
    for ds in DS:
        for m in ['F-STATIC','F-PRE90','F-POST90']:
            a=lookup(G,ds,100,m);rows.append([cn[ds],m,num(a['recall_pct'],4),num(a['qps']),num(a['enable_pct'],1),num(a['retention_pct'])+'/'+num(a['retention_min_window_pct'])])
    tab(fig,['数据 / K100','方法','Recall %','完整QPS','启用 %','保留% 合/最低窗'],rows,[.055,.21,.89,.43],9)
    text(fig,.055,.16,'表为A/B各512查询的合并描述：按命中数合并Recall，按每查询时间合并QPS。90为cal目标，正式保留率单独实测。',9,width=142)
    text(fig,.055,.105,'唯一未覆盖点速度差仅+0.0254%、三轮范围重叠、另一窗未复现；该门仍全部启用。',9,width=142)
    text(fig,.055,.065,'强控制：同期GT10 / 完整OPT-B32 / REUSE-SQ。默认未自动替换；有限网格未覆盖不构成全局优越证明。',9,width=142);save(pdf,fig)

    fig=new('实验实际比较的决策','离线训练规则与逐query触发分开；主搜索过程内的逐步早停不在本轮范围')
    blocks=[('STATIC：离线固定开关','按dataset/K/L在独立cal决定全开/全关；cal有正增量则全开，否则全关。不是离线知道每条未来查询的答案。'),('PRE：主搜索前预测','query到达并完成相同路由，使用22维特征预测：16维query投影＋范数、路由分数差、K/L。主搜索照常完整运行。'),('POST：主搜索后预测','使用相同PRE特征，加主Top-K的首/末距离、跨度、均值、标准差、最大相邻差，共28维；在C评分前决定。'),('PRE-LATE：只改变执行位置','同一PRE模型、同一阈值、同一输入，在主搜索后执行。全部返回和动作字节一致；时延差不能解释为信息更充分。')]
    yy=.82
    for title,body in blocks:text(fig,.055,yy,title,12,weight='bold');text(fig,.055,yy-.044,body,10,width=138);yy-=.16
    save(pdf,fig)

    fig=new('补全语义、精排流程与计量','固定单入口384，避免自适应预算混淆门位置')
    text(fig,.055,.82,'F：全残差开关',13,weight='bold');text(fig,.055,.775,'拒绝 → 只返回主结果；启用 → C精算＋学生短名单＋教师重排＋单入口384扩展。PRE/POST都能跳过C精算。',10.5,width=138)
    text(fig,.055,.675,'N：只控制追加导航',13,weight='bold');text(fig,.055,.63,'C始终精算并参与最终答案；门只控制后续导航。额外CPOST使用12维C/主返回摘要。前移N门不会省掉必须保留的C。',10.5,width=138)
    text(fig,.055,.525,'快速模型与小名单',13,weight='bold');text(fig,.055,.48,'节点塔34→64→32离线预存；查询塔25→64→两个32维头；另23维便宜线性特征。本轮固定使用384头。每query学生top5＋最近1去重≤6，再用104维/128棵树HGB精排选1。',10.5,width=138)
    text(fig,.055,.35,'完整wall与成本剖析',13,weight='bold');text(fig,.055,.305,'正式路径不插阶段时钟，包含正常Batch创建、全部查询处理、六数组复制和销毁。另跑profile并核每条返回一致；profile分段是诊断，不能把阶段和换算成正式QPS。',10.5,width=138)
    text(fig,.055,.17,'GT只在离线生成实际收益标签及返回后的评测使用。重模型预测收益，不会在线把6个入口逐个完整搜索。',10,width=138);save(pdf,fig)

    for ds in DS:
        fig=new(f'{cn[ds]}：开关质量与完整费用','主结果为90%校准保留目标；STATIC与PRE-LATE提供固定开关和时机控制')
        rows=[]
        for K in [1,100]:
            for m in ['F-STATIC','F-PRE90','F-POST90','N-STATIC','N-PRE90','N-POST90','N-CPOST90']:
                r=lookup(G,ds,K,m);rows.append([K,m,num(r['recall_pct'],4),num(r['qps']),num(r['mean_us']),num(r['enable_pct'],1),num(r['retention_pct'])+'/'+num(r['retention_min_window_pct']),r['false_rejected_positive_queries']])
        tab(fig,['K','方法','Recall %','完整QPS','µs/query','启用 %','保留% 合/最低窗','误拒正例'],rows,[.055,.37,.89,.45],8.5)
        ax=fig.add_axes([.08,.105,.40,.20]);methods=['F-PRE90','F-POST90','N-PRE90','N-POST90','N-CPOST90'];ys=np.arange(len(methods));on=[f(lookup(G,ds,100,m),'enable_pct') for m in methods];kept=[f(lookup(G,ds,100,m),'retention_pct') for m in methods]
        ax.barh(ys-.15,on,height=.28,color='#769dbd',label='启用率');ax.barh(ys+.15,[np.nan if x is None else x for x in kept],height=.28,color='#37a18f',label='正增量保留');ax.set_yticks(ys,methods,fontsize=7.5);ax.set_xlim(0,105);ax.invert_yaxis();ax.legend(loc='upper left',bbox_to_anchor=(0,-.18),ncol=2,fontsize=7,frameon=False);ax.set_title('K100：启用与保留',fontsize=9)
        ax=fig.add_axes([.58,.105,.35,.20]);
        for bm,color in [('GT10','#a5b1bc'),('OPT-B32','#376e9b')]:
            vals=[]
            for L in sorted(set(int(r['L']) for r in P if r['dataset']==ds and r['K']=='100' and r['method']==bm)):
                rr=[r for r in P if r['dataset']==ds and r['K']=='100' and r['method']==bm and int(r['L'])==L];vals.append((sum(float(r['recall_pct']) for r in rr)/2,1e6/(sum(float(r['mean_us']) for r in rr)/2)))
            ax.plot(*zip(*vals),color=color,lw=1,label=bm)
        for m,color in [('ALWAYS','#c26955'),('F-PRE90','#7256a8'),('F-POST90','#e3a052')]:
            r=lookup(A,ds,100,m);ax.scatter(f(r,'recall_pct'),f(r,'qps'),s=22,color=color,label=m)
        ax.set_xlabel('Recall@100 %',fontsize=8);ax.set_ylabel('完整QPS',fontsize=8);ax.tick_params(labelsize=7);ax.legend(fontsize=6,loc='best',frameon=False);ax.set_title('K100：同期有限控制网格',fontsize=9);save(pdf,fig)

    stages=['route','main_search','gate_features','gate_predict','candidate_C','student_shortlist','rerank_features','rerank_predict','expansion','merge'];colors=['#d4dce3','#9daeba','#a186b8','#775d98','#4f90b8','#75b4ba','#e6ac64','#ce7e4c','#299781','#b9d8a6'];labels=['路由','主搜','门特征','门预测','C评分','学生/名单','精排特征','精排预测','扩展','合并']
    for ds in DS:
        fig=new(f'{cn[ds]}：阶段成本与精排费用','K100/L200 · profile为另行重放诊断；每条输出与正式包相同')
        methods=['GT10','Q8-B32','FAST384','ALWAYS','TEACHER384','F-PRE90','F-POST90','N-CPOST90'];ax=fig.add_axes([.075,.49,.85,.30]);bottom=np.zeros(len(methods))
        for j,stage in enumerate(stages):
            vals=[f(lookup(S,ds,100,m),stage+'_mean_us') for m in methods];ax.bar(np.arange(len(methods)),vals,bottom=bottom,color=colors[j],label=labels[j]);bottom+=vals
        ax.set_xticks(np.arange(len(methods)),methods,fontsize=7.3);ax.set_ylabel('profile µs/query',fontsize=9);ax.legend(ncol=5,loc='upper center',bbox_to_anchor=(.5,1.22),fontsize=7.5,frameon=False);ax.grid(axis='y',alpha=.15)
        rows=[]
        for m in methods:
            r=lookup(S,ds,100,m);a=lookup(A,ds,100,m);rows.append([m,num(a['mean_us']),num(r['gate_total_mean_us']),num(r['student_shortlist_mean_us']),num(r['rerank_features_mean_us']),num(r['rerank_predict_mean_us']),num(r['expansion_mean_us']),num(a['aux_exact_per_query'],1)])
        tab(fig,['方法','正式完整µs','门µs','学生/名单µs','精排特征µs','精排预测µs','扩展µs','辅助精算/query'],rows,[.055,.16,.89,.255],8.1)
        text(fig,.055,.112,'GT10/B32分段使用返回等价逐query适配层，并非原优化batch严格分解。门normal/profile同一查询逻辑；时钟、分配、复制/销毁与缓存会形成差额。',8.8,width=146)
        text(fig,.055,.065,'辅助精算与重特征邻接访问分别保存；相同384上限不代表实际展开量相同。完整QPS始终来自未插阶段时钟的三轮测量。',8.8,width=146);save(pdf,fig)

    for K in [1,100]:
        fig=new(f'K{K}：精排是否值得付费','相同候选bank与384上限；拆分重特征、树预测及入口改变后的实际扩展')
        rows=[]
        for ds in DS:
            for m,ref in [('ALWAYS','FAST384'),('ALWAYS','DIST384'),('TEACHER384','ALWAYS')]:
                r=next(x for x in RR if x['dataset']==ds and int(x['K'])==K and x['method']==m and x['reference']==ref);rows.append([cn[ds],m+'/'+ref,num(r['recall_gain_pp'],4),num(r['formal_extra_us']),num(r['rerank_feature_delta_us']),num(r['rerank_predict_delta_us']),num(r['expansion_delta_us']),num(r['aux_exact_delta'],1)])
        tab(fig,['数据','方法/参照','Recall变化pp','完整增加µs','特征增加µs','预测增加µs','扩展变化µs','精算变化'],rows,[.055,.30,.89,.49],8.2,widths=[.09,.21,.12,.12,.12,.12,.12,.10])
        text(fig,.055,.225,'ALWAYS=CASCADE384：最近1＋学生top5，再教师选1。FAST384只有学生选1；TEACHER384对全C运行相同教师。',10,width=140)
        text(fig,.055,.155,'正值/负值均按实际测量保留。级联与全C教师可能选择不同入口，预测较高不保证真实收益较高；教师预测不是GT上界。',10,width=140)
        text(fig,.055,.085,'不能把“完整耗时差”全部命名为精排成本；应同时看局部特征/树费用、最终救回与实际扩展变化。',10,width=140);save(pdf,fig)

    fig=new('75%与90%校准目标的敏感性','K100合并描述；减少启用后的召回/费用代价必须由正式窗口重新验证')
    rows=[]
    for ds in DS:
        for fam,variant in [('F','PRE'),('F','POST'),('N','PRE'),('N','POST'),('N','CPOST')]:
            a,z=[lookup(G,ds,100,f'{fam}-{variant}{t}') for t in [75,90]];rows.append([cn[ds],fam+'-'+variant,num(a['enable_pct'],1)+'/'+num(z['enable_pct'],1),num(a['retention_pct'])+'/'+num(z['retention_pct']),num(a['recall_pct'],4)+'/'+num(z['recall_pct'],4),num(a['qps'])+'/'+num(z['qps'])])
    tab(fig,['数据','门','启用% 75/90','保留% 75/90','Recall% 75/90','QPS 75/90'],rows,[.055,.18,.89,.64],8.1)
    text(fig,.055,.125,'阈值候选和目标在正式前冻结；没有根据测试Recall追加阈值。NA为全开策略无正增量，不能解释成100%保留或识别成功。',9.2,width=142);save(pdf,fig)

    fig=new('离线成本、资产与验证','继承资产保留历史成本；嵌套费用不重复相加')
    rows=[['新Flickr/Yandex标签进程',num(cost['new_label_process_seconds'])+' s'],['新Flickr/Yandex学生/教师训练',num(cost['new_model_training_process_seconds'])+' s'],['四集实际门标签进程',num(cost['gate_label_process_seconds'])+' s'],['四集门模型拟合进程',num(cost['gate_fit_process_seconds'])+' s'],['正式完整batch wall',num(cost['formal_complete_batch_seconds'])+' s'],['正式进程（含加载/warmup/profile/核验）',num(cost['formal_process_seconds'])+' s'],['八状态模型文件（不等于RSS）',num(cost['model_artifact_bytes']/2**20)+' MiB'],['门模型文件',num(cost['gate_artifact_bytes']/2**10)+' KiB']]
    tab(fig,['成本项目','本轮实测/定义'],rows,[.055,.43,.89,.37],10)
    text(fig,.055,.365,'COCO/WebVid复用E198；对应标签和模型训练费用仍属于历史成本。未重建原图/router/SQ后端，不能把它们的继承成本记成零。共同benchmark的全部加载RAM不等于新门的单独部署增量。',10,width=138)
    text(fig,.055,.245,f"验证：{audit['checks']['packets']}个包、{audit['checks']['linear_fullsort_queries']}条query合并witness、{audit['checks']['independent_gate_decisions']}项门决策；stdlib另核{stdlib['counts']['points']}点/{stdlib['counts']['rounds']}轮，旧兼容包{stdlib['counts']['old_compatible_packets']}个。",10,width=138)
    text(fig,.055,.115,'独立核验指同一执行者采用不同实现。全部新证据持久化，旧科学文件/seal/PDF保留；阶段剖析不作为另一次性能确认。',10,width=138);save(pdf,fig)

    fig=new('如何解释这次实验','根据真实可省工作与信息收益判断时机；不把校准目标当成已兑现结果')
    cc=facts['pre_post_pooled_decisions'];text(fig,.055,.82,f"16组F/N、数据/K的合并描述：PRE覆盖POST {cc.get('PRE covers POST',0)}组，POST覆盖PRE {cc.get('POST covers PRE',0)}组，取舍或相同 {cc.get('tradeoff or equal',0)}组。",12,width=120)
    text(fig,.055,.745,'PRE/POST在26/32个窗口配置中返回包相同；不能用7比6判断两种时机的通用优劣。',10,width=140)
    text(fig,.055,.69,'相同PRE模型移动位置后，返回和动作完全一致。由于主搜索仍完整执行，提前做相同决定不会自动减少主搜索；主要差异来自可用信息与所跳过的残差工作。全关状态当前PRE/POST仍构造特征，STATIC无此开销，可做快路径优化。',11,width=132)
    text(fig,.055,.55,'F与N回答不同问题：F能跳过整段补全，但也放弃直接C答案；N保留直接答案，因此门再早也不能省掉必须执行的C评分。',11,width=132)
    text(fig,.055,.42,'精排判断同时看三项：局部特征/模型费用、真实新增召回、选中入口后的实际展开费用。更少精排候选与更低完整耗时不能互相替代。',11,width=132)
    text(fig,.055,.29,'边界：四个多模态集、两个已曝光窗口、固定Q8来源、单入口384与L200；K1事件稀疏，512开发兼门fit，三轮wall不是三份独立质量样本。有限网格不证明全局最优。',10.5,width=136)
    text(fig,.055,.15,'原始逐窗结果：analysis/points.csv、gates.csv、stage_costs.csv、rerank_costs.csv、placement.csv、frontier.csv。默认选择与具体后继结论见同目录report_zh.md / findings_zh.md。',10,width=138);save(pdf,fig)
dump(R/'reviews/pdf_build.json',dict(status='PASS_PDF_BUILT_AND_FIGURE_TEXT_BOUNDS',pdf=str(PDF),sha256=sha(PDF),pages=page,titles=titles,source_files=['aggregate.csv','gate_aggregate.csv','stage_aggregate.csv','rerank_aggregate.csv','points.csv','summary_facts.json','cost_ledger.json'],not_yet_actual_pdf_rendered=True))
print('PDF_BUILT',page,str(PDF),flush=True)

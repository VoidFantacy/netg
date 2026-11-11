#!/usr/bin/env python3
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import csv,json,math,unicodedata
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
R=Path(__file__).resolve().parents[1];A=R/'analysis'
DS=['coco','deep10m_l2_v1'];LABEL={'coco':'COCO','deep10m_l2_v1':'Deep10M'}
METHODS=['GT10','B32','REG-NN','REG-Q','REG-R'];COLOR=dict(zip(METHODS,['#293d51','#198b83','#d49b25','#7186ba','#b55780']))
def rows(name):return list(csv.DictReader((A/f'{name}.csv').open()))
def num(x,k):return float(x[k])
def fmt(x,d=2):return f'{float(x):.{d}f}'
def mdtable(head,data):return ['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+['| '+' | '.join(map(str,r))+' |' for r in data]+['']
def main():
    pts=rows('points');pairs=rows('paired');comps=rows('discrete_comparisons');summary=json.loads((A/'summary.json').read_text());audit=json.loads((R/'reviews/results_audit.json').read_text())
    p={(x['dataset'],x['method'],int(x['L'])):x for x in pts};z={(x['dataset'],x['method'],int(x['L'])):x for x in pairs};c={(x['dataset'],x['method'],int(x['L'])):x for x in comps}
    regional=[x for x in comps if x['method'].startswith('REG-')]
    region_dom=sum(bool(x['dominated_by_GT_L']) for x in regional)
    enough=[x for x in regional if x['target_speed_delta_pct'] and num(x,'target_speed_delta_pct')>=2 and x['target_speed_three_rounds_positive']=='True']
    budgetwins=[x for x in regional if x['budget_recall_delta_pp'] and num(x,'budget_recall_delta_pp')>=.05 and x['budget_GT_three_rounds_within']=='True']
    verdict=f'区域补全18点中，{region_dom}点被本轮某个实测L的GT10在Recall和中位QPS两项同时覆盖；达到事前速度筛选的点{len(enough)}个，达到预算筛选的点{len(budgetwins)}个。'
    lead=('本轮区域补全尚未建立可支付的Recall–QPS提升，保留GT10默认，停止该固定后端进入动作选择器。' if not enough and not budgetwins else '区域补全存在局部候选收益，按离散实测与波动逐点判断；未建立新默认。')
    lines=['# E187：自适应残差补全首轮实验','',f'2026-10-28；COCO与Deep10M；真实K100；原46配置/138轮，另加6个GT10控制/18轮，合计52点/156完整单线程批次。','',f'**{lead}** {verdict}','',
        '这是E186候选来源pilot，不是完整动作选择器。所有模型在正式矩阵前冻结；原测试已历史曝光，不能称盲确认。当前默认E99 GT10不变；E183的其他五集/K1证据继续保留，不能将本轮范围扩写为七集两K已验证。','',
        '## 固定L200：新方法到底提升多少','',
        'Recall以百分比显示；差值为百分点pp。QPS为同一新二进制、完整wall三轮中位数，括号内为最小–最大；没有拼接旧QPS。']
    mainrows=[]
    for ds in DS:
        for m in METHODS:
            x=p[ds,m,200];zz=z.get((ds,m,200))
            mainrows.append([LABEL[ds],m,fmt(x['recall_pct'],4)+'%',fmt(x['qps'],1),fmt(zz['recall_delta_pp'],4) if zz else '—',fmt(zz['qps_delta_pct'])+'%' if zz else '—',f"{x['failed_lt10']}/10000"])
    lines+=mdtable(['数据','方法','Recall@100','完整QPS','对GT10 ΔRecall pp','对GT10 ΔQPS','严格低召回数'],mainrows)
    lines+=['每个补全法L100/200/400均运行，原GT10另测128/160/256/320/512/640/800/1200；补充COCO L408/432/464、Deep L101/201/401。完整52点及三轮范围见[points.csv](analysis/points.csv)，逐query见[压缩CSV](analysis/query_metrics.csv.gz)。同L增Recall与更慢构成取舍，结论以真实跨L预算对照补充。','',
        '## 同目标Recall及同完整预算：离散实测对照','',
        '对每个补全点，在GT10所有实测点中找“达到至少该Recall的最快点”，报告速度差；另找“不超过补全耗时的最高Recall点”，报告Recall差。不插值、不称精确等Recall/等费用；这是固定有限网格的离散对照。速度三轮同向与预算三轮均可用另列CSV，三轮不构成统计独立重复。','']
    compdata=[]
    for ds in DS:
        for m in METHODS[1:]:
            x=c[ds,m,200]
            compdata.append([LABEL[ds],m,x['target_GT_L'] or '未覆盖',fmt(x['target_speed_delta_pct'])+'%' if x['target_speed_delta_pct'] else '—',x['budget_GT_L'] or '未覆盖',fmt(x['budget_recall_delta_pp'],4) if x['budget_recall_delta_pp'] else '—',x['dominated_by_GT_L'] or '无'])
    lines+=mdtable(['数据','补全L200','达到至少同Recall的GT10 L','补全速度差','预算内GT10 L','补全Recall差 pp','同时覆盖此点的GT10 L'],compdata)
    lines += [verdict,'', '全部24个补全点的离散对照保留在[discrete_comparisons.csv](analysis/discrete_comparisons.csv)，不只显示赢家；图中连线用于阅读，不作为新增测量。事前参考为速度+2%且三轮同向，或预算内Recall+0.05pp，均不是跨数据总体保证。','',
        '### 原网格错觉与补充控制','',
        '原46点保持不动，首次分析保留在analysis_original_v1。原网格上COCO区域L400似乎比GT10 L512快4.8–6.8%，但Recall只比同L主搜多0.0389–0.0562pp；Deep B32也因多0.0012–0.0047pp而需要跳到下一大L，出现17–25%的名义阈值速度差。这不能证明净收益。','',
        '据此另立[补充协议](controls_v1/protocol.md)并在新控制查询前冻结，只加上述6个GT10近邻L、18轮，不改区域模型/方法/原返回或计时，不按结果继续添点。属于测试曝光后的保守费用核验，不是盲确认，也不冒称原协议预设的46点。最终对照使用52点；初次对照CSV仍原样保留。','',
        '补充控制和原候选处于不同时间窗口，缓存/频率漂移限制保留；CSV另列GT10最慢轮仍快于候选最快轮的覆盖L。即使范围不重叠，也不是时间随机化复现或跨机器保证。原窗口已经覆盖的区域点与后补控制覆盖分开理解，不将该控制用于精确收益估计。','',
        '## 来源是否突破了旧表：成员救回与损伤','',
        '全库登记允许候选来自训练残差源外，实际救回仍受区域选择、PQ shortlist和原metric严格合并限制。源为E183完整16K训练遗漏的未截断并集；“源外”不等同新语义或测试独立。下表均相对同L实际GT10主包，L200。','']
    lines+=mdtable(['数据','补全','原遗漏成员','救回 / 损伤','源外救回','遗漏修复率','改善查询 / 全部','恢复100/100'],[[LABEL[ds],m,z[ds,m,200]['members_missing'],z[ds,m,200]['members_rescued']+' / '+z[ds,m,200]['members_damaged'],z[ds,m,200]['rescued_source_out'],fmt(z[ds,m,200]['member_repair_pct'],3)+'%',z[ds,m,200]['improved_queries']+'/10000',z[ds,m,200]['full_recovered_queries']] for ds in DS for m in METHODS[1:]])
    lines+=['源外救回能验证新来源的作用，但不能单独证明净收益。区域方法只是查询剩余目标的一个可达来源；候选上限同为96不等于费用相同。成员损伤按原严格ID GT保留，不改GT、不回填结果。','',
        '## 原始结果条件化是否有效','',
        'REG-NN取粗距离前2；REG-Q仅q/区域大小/粗rank；REG-R增加原R的区域计数与分数摘要。Q/R同后端、12K训练、α10和top8选2；同工作机会不等于同实际扫描量，选中的区域大小可以不同。L200模型固定迁移到L100/400。','']
    lines+=mdtable(['数据','L','REG-R−REG-Q Recall pp','REG-R对REG-Q QPS变化','R扫描码/query','Q扫描码/query'],[[LABEL[ds],L,fmt(num(p[ds,'REG-R',L],'recall_pct')-num(p[ds,'REG-Q',L],'recall_pct'),4),fmt(100*(num(p[ds,'REG-R',L],'qps')/num(p[ds,'REG-Q',L],'qps')-1))+'%',fmt(p[ds,'REG-R',L]['scanned_codes_per_query'],1),fmt(p[ds,'REG-Q',L]['scanned_codes_per_query'],1)] for ds in DS for L in [100,200,400]])
    lines+=['Deep L200的REG-R相对REG-Q只多救回2个成员；最近区域REG-NN反而救出原2条低召回query，而Q/R均未脱离低召回。COCO的R条件化增加召回但仍明显落后B32。说明本轮固定标签/特征没有同时学到平均遗漏与严重失败；不能把“使用更多主结果信息”直接当作更好的补全。','',
        '本轮只验证一个低容量线性选择模型。其成败不能否定主结果条件化这一类机制；标签预测更准也未必选择更好，更未必更便宜。未训练混合ID/区域动作开关或逐query门控，不能宣称自适应选择器已完成。','',
        '## 失败率按用户定义：Recall@100严格低于10%','',
        '命中0–9个是失败；恰好10个排除。分母每个点10000条查询。有所改善与升到≥10%单列，达到10%也不代表高召回。原失败极少时，0/1、1/2等比例不具稳定泛化意义。','']
    lines+=mdtable(['数据','L','GT10失败','B32失败','REG-NN失败','REG-Q失败','REG-R失败'],[[LABEL[ds],L]+[p[ds,m,L]['failed_lt10']+'/10000' for m in METHODS] for ds in DS for L in [100,200,400]])
    lines+=mdtable(['数据','补全L200','原失败','有所改善','脱离<10%','新增失败','救回成员来自原失败 / 全救回'],[[LABEL[ds],m,z[ds,m,200]['original_lt10'],z[ds,m,200]['lt10_improved'],z[ds,m,200]['lt10_escaped'],z[ds,m,200]['new_lt10'],z[ds,m,200]['rescued_from_original_lt10']+' / '+z[ds,m,200]['members_rescued']] for ds in DS for m in METHODS[1:]])
    lines+=['平均Recall收益来自哪个原命中段，可以从逐queryCSV重算；不能以成员修复率替代严重失败查询修复。','',
        '## 在线与离线成本、复现和边界','',
        '正式评测CPU15、实际1线程，OMP/BLAS/MKL/NUMEXPR全部1；同一时间只运行一个被测方法，没有并发训练/标签/其他性能测试。所有方法计入正常Batch分配初始化、原路由/主搜、补全、统一六数组复制和正常销毁。模型/索引加载、预热、保存/hash、GT评价和oracle在wall之外。','',
        '后端全1024粗代表评分，top8选2，全扫这两区域16字节PQ码，排除原R，96个候选用主核DistanceComputer精算并严格合并；global PQ不是量化残差。IP只对辅助粗代表采用球面训练，不归一化原base/query或改变任务metric。','']
    costs=[]
    for s in summary['summaries']:
        ds=s['dataset'];be=s['backend'];env=s['environment'];tr=s['training']
        costs.append([LABEL[ds],fmt(be['elapsed_seconds']),fmt(env['backend_resident_bytes']/2**20,2),fmt(s['formal_internal_seconds']),fmt(s['formal_outer_seconds']),fmt(tr['seconds'])])
    lines+=mdtable(['数据','后端离线秒/8线程','区域数组MiB','正式内部wall秒','suite外层秒','选择器训练秒/1线程'],costs)
    lines+=['区域数组为centroids/codebooks/IDs/ID→region/offsets/codes的精确载荷，另有少量JSON模型与临时对象；不是进程峰值RSS，也不含共同主图/向量。基线进程也装载该后端以保持同环境，但GT10/B32不使用它；单独部署GT10/B32无需这份额外RAM。B32沿原≤256KiB预算，文件身份冻结。','',
        '原生runner只为区域法记录扫描/精算；B32原JSON中0是未插桩占位，不能解释为无额外精算。第二实现从真实主包和表重构其候选数：','']
    lines+=mdtable(['数据','L','B32额外精算/query'],[[LABEL[x['dataset']],x['L'],fmt(x['extra_exact_scores_per_query'],3)] for x in audit['B32_exact_score_counts']])
    lines+=['区域法计数见points.csv。正式内部wall已经包含在suite外层耗时，不能二者相加；suite包括原图加载、预热、保存、校验与穷举合并oracle。成功构建、特征、训练、资格测试的收据均保留reviews与models；历史资产首次构建费用未重计。','',
        '训练角色：原合法16K残差query中前12K训练区域模型、后4K校准（仅描述、不选参数）；原B32使用完整16K，是冻结参考，训练量不等。Q/R两者训练量相同。fit/cal/test逐向量SHA无交叠，COCO继承原组去重；Deep未声称语义独立，原画像可使用过合法fitquery。原test曾在历史实验使用，未引入新盲确认。','',
        f"核验：52点真实timed返回、156轮receipt、三轮bit/SHA稳定；B32及三种区域法从同L实际GT10包重构的合并oracle通过；全base分区排列核验、4096点独立编码核验、旧程序128query前缀ID/score/route及{audit['historical_full_10K_packets_bit_equal']}个完整10K旧包逐字一致。第二份stdlib集合统计/packet SHA/两份冻结输入核验{audit['seconds']:.3f}秒，通过。由同一执行者使用不同实现，不称独立人员审查。",'',
        '冻结前曾在Deep资格测试尚未完成时提前启动资格汇总，因complete.json尚不存在而退出；未产生正式结果或改模型。等待完成后同脚本通过，记录在reviews/process_notes.md。Deep原图padding−1警告继承旧资产，正常加载；原生前缀一致，无图修改。','',
        '原46点冻结后不改模型、nprobe、PQ、容量或原网格；新增6个GT10控制单独协议/freeze并披露事后性质。本轮不测K1/其他五集，也未控制主图/数据规模/特征/metric等跨集因素，不能给流形因果解释或新的数据净收益准入器。成对bootstrap仅作当前query队列的质量不确定性描述，未做多重比较校正，不包含图/模型重训变异。','',
        '## 后续判断','',lead+' '+verdict,'',
        '应先把来源可达率和每个救回的在线成本一起优化，再决定是否值得构造动作选择器。若继续，需独立协议研究更廉价的区域路由/更小的扫描预算及成本感知选择；不要仅扩大当前region扫描或训练更复杂门控来掩盖来源费用。保留“不补全”选项，按独立校准与未参与选择的确认决定数据集/K/L配置。','',
        '[原协议](protocol.md) · [冻结manifest](freeze.json) · [全部点](analysis/points.csv) · [成对救损](analysis/paired.csv) · [离散对照](analysis/discrete_comparisons.csv) · [第二实现核验](reviews/results_audit.json) · [PDF](ACSG_自适应残差补全_实验对比_20261028.pdf)','']
    (R/'report_zh.md').write_text('\n'.join(lines))
    font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';font_manager.fontManager.addfont(font)
    plt.rcParams.update({'font.family':font_manager.FontProperties(fname=font).get_name(),'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False,'font.size':10,'pdf.fonttype':3})
    pdf=PdfPages(R/'ACSG_自适应残差补全_实验对比_20261028.pdf')
    def page(title,i):
        f=plt.figure(figsize=(11.7,8.3));f.text(.055,.945,title,size=18,weight='bold',color='#253b4d');f.text(.055,.025,f'E187 · COCO / Deep10M · K100 · 冻结曝光测试 · 2026-10-28                                      {i}/6',size=8,color='#647585');return f
    def text(f,y,lines,size=11):
        wrapped=[];budget=int(1420/size)
        for line in lines:
            buf='';width=0
            for ch in line:
                w=2 if unicodedata.east_asian_width(ch) in ['W','F'] else 1
                if width+w>budget:wrapped.append(buf);buf='';width=0
                buf+=ch;width+=w
            if buf:wrapped.append(buf)
        f.text(.06,y,'\n'.join(wrapped),va='top',fontsize=size,linespacing=1.65)
    def tab(f,head,data,rect,fontsize=9):
        ax=f.add_axes(rect);ax.axis('off');t=ax.table(cellText=data,colLabels=head,loc='upper center',cellLoc='center',bbox=[0,0,1,1]);t.auto_set_font_size(False);t.set_fontsize(fontsize)
        for (rr,cc),cell in t.get_celld().items():
            cell.set_edgecolor('#dbe3e8');cell.set_facecolor('#eaf0f4' if rr==0 else ('#f6f8fa' if rr%2==0 else 'white'))
            if rr==0:cell.set_text_props(weight='bold',color='#253b4d')
        return ax
    f=page('新来源能补回遗漏，是否值得这笔费用？',1)
    text(f,.885,[lead,verdict,'原46点+6个GT10控制 · 共156轮；每点10K query，完整wall。下表固定L200。'],11)
    tab(f,['数据','方法','Recall@100','完整QPS','ΔRecall pp','ΔQPS','<10%查询'],mainrows,[.055,.31,.89,.40],9)
    text(f,.25,['GT10：原主搜索；B32：冻结的残差ID表。',
        'REG-NN：最近2区域；REG-Q：仅q特征选区域；REG-R：加入原返回结果摘要。',
        '区域法从全库取候选；三者同后端、同96个精算上限，扫描费用仍可能不同。',
        '默认GT10保持；本轮不是K1/七集验证，也没有新盲确认。'],10)
    pdf.savefig(f);plt.close(f)
    f=page('Recall–QPS：必须和更大 L 的主搜索比较',2)
    for ri,ds in enumerate(DS):
        for col in [0,1]:
            ax=f.add_axes([.075+col*.47,.55-ri*.39,.39,.29])
            for m in METHODS:
                xx=sorted([x for x in pts if x['dataset']==ds and x['method']==m],key=lambda x:int(x['L']))
                ax.plot([num(x,'recall_pct') for x in xx],[num(x,'qps') for x in xx],'-o',color=COLOR[m],ms=3,label=m,lw=1.3)
                ax.fill_between([num(x,'recall_pct') for x in xx],[num(x,'qps_min') for x in xx],[num(x,'qps_max') for x in xx],color=COLOR[m],alpha=.1)
            ax.set(xlabel='Recall@100 (%)',ylabel='完整 QPS',title=LABEL[ds]+('：全部实测' if col==0 else '：高召回区间'))
            if col:ax.set_xlim(96 if ds=='coco' else 97,100)
            ax.grid(alpha=.18);ax.legend(fontsize=7,ncol=3,frameon=False)
    text(f,.09,['点是实测，中间连线仅便于阅读；阴影为3轮最小–最大。未用插值判定性能提升。'],9)
    pdf.savefig(f);plt.close(f)
    f=page('来源突破与代价：看实际救回，也看扫描量',3)
    for col,ds in enumerate(DS):
        ax=f.add_axes([.09+col*.46,.48,.36,.32]);xx=[z[ds,m,200] for m in METHODS[1:]]
        inside=[num(x,'rescued_source_in') for x in xx];outside=[num(x,'rescued_source_out') for x in xx]
        ax.bar(METHODS[1:],inside,label='训练残差源内',color='#739aaa');ax.bar(METHODS[1:],outside,bottom=inside,label='源外',color='#d7a340')
        for j,x in enumerate(xx):ax.text(j,inside[j]+outside[j],str(x['members_rescued']),ha='center',va='bottom',fontsize=9)
        ax.set(title=LABEL[ds]+'：L200实际救回成员',ylabel='query–GT成员事件');ax.legend(fontsize=8,frameon=False);ax.grid(axis='y',alpha=.18)
    rr=[]
    for ds in DS:
        for m in METHODS[1:]:
            x=p[ds,m,200];nn=next(y['extra_exact_scores_per_query'] for y in audit['B32_exact_score_counts'] if y['dataset']==ds and y['L']==200) if m=='B32' else num(x,'extra_exact_scores_per_query')
            rr.append([LABEL[ds],m,'—' if m=='B32' else fmt(x['scanned_codes_per_query'],0),fmt(nn,2),z[ds,m,200]['members_damaged']])
    tab(f,['数据','方法L200','扫描PQ码/query','额外精算/query','损伤成员'],rr,[.09,.13,.82,.26],9)
    text(f,.09,['全库登记解决“能不能提出新ID”，不保证有限扫描预算具有成本优势。'],9)
    pdf.savefig(f);plt.close(f)
    f=page('严格低召回失败：平均召回收益不能替代尾部修复',4)
    tab(f,['数据','L','GT10','B32','REG-NN','REG-Q','REG-R'],[[LABEL[ds],L]+[p[ds,m,L]['failed_lt10'] for m in METHODS] for ds in DS for L in [100,200,400]],[.07,.53,.86,.28],10)
    text(f,.87,['失败＝每条查询仅命中0–9个GT100成员；表中分母每格均为10000。'],11)
    rr=[[LABEL[ds],m,z[ds,m,200]['original_lt10'],z[ds,m,200]['lt10_improved'],z[ds,m,200]['lt10_escaped'],z[ds,m,200]['rescued_from_original_lt10']+' / '+z[ds,m,200]['members_rescued']] for ds in DS for m in METHODS[1:]]
    tab(f,['数据','方法L200','原失败','有改善','升到≥10%','原失败贡献 / 全救回成员'],rr,[.07,.16,.86,.30],9)
    text(f,.105,['原失败只有少量查询，尾部比例不稳定；有所改善和脱离低召回是两回事。'],10)
    pdf.savefig(f);plt.close(f)
    f=page('真实预算对照与原结果 R 的作用',5)
    tab(f,['数据','方法L200','同目标GT L','速度差','预算内GT L','Recall差pp','覆盖GT L'],compdata,[.04,.49,.92,.32],8)
    text(f,.875,['同目标：GT10达到至少补全点Recall的最快实测点；预算内：不超补全耗时的最高Recall点。'],10)
    rrows=[[LABEL[ds],L,fmt(num(p[ds,'REG-R',L],'recall_pct')-num(p[ds,'REG-Q',L],'recall_pct'),4),fmt(100*(num(p[ds,'REG-R',L],'qps')/num(p[ds,'REG-Q',L],'qps')-1))+'%'] for ds in DS for L in [100,200,400]]
    tab(f,['数据','L','R−Q Recall pp','R对Q QPS变化'],rrows,[.12,.16,.76,.25],10)
    text(f,.10,['本轮只测试固定线性选择器；结果不代表所有主结果条件化方法的上限。',
        '速度差仅是离散阈值比较，GT对照可能有更高Recall；不能读成精确等Recall加速。'],9)
    pdf.savefig(f);plt.close(f)
    f=page('固定控制、额外成本与证据范围',6)
    text(f,.875,['COCO：118272×512，raw-IP；Deep：10M×96，squared L2。原图/GT10/metric保持。',
        '区域模型：合法16K中12K fit、4K cal；固定ridge α10；cal不选参数。',
        'B32：原完整16K训练的冻结参考。原test已曝光，不能称盲确认。',
        '后端：1024区域，global PQ M16×8bit，top8选2，全扫描，最多96次原核精算。',
        '完整wall：分配初始化→路由/主搜→补全全部步骤→六数组复制→正常销毁。',
        'CPU15、实际单线程；模型加载/预热/保存/GT评价/oracle不在查询wall内。',
        '补充6控制在读出原46点后单独冻结，只增GT10近邻L，不改变新方法。',
        '时间窗口不同，缓存/频率漂移保留；原网格覆盖15/18区域点，补充后18/18。'],10)
    tab(f,['数据','后端离线秒\n8线程','区域数组\nMiB','内部wall秒','suite秒','模型训练秒'],costs,[.07,.39,.86,.15],9)
    text(f,.34,['内部wall已经包含在suite耗时，不可相加；额外RAM是数组载荷，不是总进程峰值。',
        '核验：旧原生128条前缀逐字一致；全分区排列和4096条PQ编码检查通过。',
        '原46点加6个独立冻结GT控制：52真实包/156轮，三轮bit/SHA和合并oracle通过。',
        '第二份stdlib集合实现复核所有质量整数；同一执行者，不称独立人员审查。',
        '本轮不验证流形因果、K1、其他五集或逐query动作开关；默认不变。',
        '完整CSV、逐query证据、协议、模型、收据及详细解释见同目录 report_zh.md。'],10)
    pdf.savefig(f);plt.close(f);pdf.close()
    (A/'conclusion.json').write_text(json.dumps(dict(lead=lead,regional_points=18,regional_dominated=region_dom,regional_speed_screen_points=len(enough),regional_budget_screen_points=len(budgetwins),verdict=verdict),indent=2,ensure_ascii=False)+'\n')
    print(lead,verdict)
if __name__=='__main__':main()

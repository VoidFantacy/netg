from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

rows=list(csv.DictReader((R/'analysis/points.csv').open()));pairs=list(csv.DictReader((R/'analysis/optimization_pairs.csv').open()));stable=list(csv.DictReader((R/'analysis/stability.csv').open()));v=read(R/'analysis/verdict.json')
receipts=[read(R/f'reviews/{ds}.{window}.receipt.json') for ds in DS for window in ['public','confirmation']]
suite_seconds=sum(x['seconds'] for x in receipts)
peak_rss=max(x['peak_rss'] for x in receipts)
gt_seconds=sum(x['seconds'] for x in read(R/'reviews/exact_gt_all.json'))
batch_seconds=sum(sum(float(x[f'qps_round{j}'])**-1*int(x['n']) for j in range(3)) for x in rows)
def fmt(x,d=2):return f'{float(x):.{d}f}'
def yes(x):return str(x)=='True'
def table(headers,rs):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rs])

fig,axs=plt.subplots(2,2,figsize=(12,9),layout='constrained')
colors={'GT10':'#555555','B32':'#2871ae','OPT-B32':'#004c99','REUSE-SQ':'#d98823','OPT-SQ':'#ba3d12'}
for i,ds in enumerate(DS):
 for j,K in enumerate([1,100]):
    ax=axs[i,j]
    for window,ls in [('public','--'),('confirmation','-')]:
     for method,col in colors.items():
        aa=sorted([x for x in rows if x['dataset']==ds and int(x['K'])==K and x['window']==window and x['method']==method],key=lambda x:int(x['L']))
        ax.plot([float(x['recall_pct']) for x in aa],[float(x['qps']) for x in aa],marker='o',markersize=3,linestyle=ls,color=col,label=f'{method} / {window}')
    ax.set(title=f'{"COCO" if ds=="coco" else "WebVid"} / K={K}',xlabel=f'Recall@{K} (%)',ylabel='Complete single-thread QPS');ax.grid(alpha=.2)
axs[0,0].legend(fontsize=7,ncol=2)
fig.savefig(R/'analysis/recall_qps.png',dpi=160);fig.savefig(R/'analysis/recall_qps.svg');plt.close(fig)

summary=[]
for ds in DS:
 for method in ['OPT-B32','OPT-SQ']:
    pp=[x for x in pairs if x['dataset']==ds and x['method']==method];ss=[x for x in stable if x['dataset']==ds and x['method']==method]
    gains=[float(x['qps_gain_pct']) for x in pp]
    summary.append([ds,method,f'{sum(yes(x["screen_pass"]) for x in pp)}/{len(pp)}',f'{sum(yes(x["both_windows_pass"]) for x in ss)}/{len(ss)}',f'{min(gains):+.2f}..{max(gains):+.2f}%',f'{float(np.median(gains)):+.2f}%'])
kept=[x for x in stable if yes(x['both_windows_pass'])]
kept_table=table(['数据','K','L','优化','公共QPS增幅%','确认QPS增幅%'],[[x['dataset'],x['K'],x['L'],x['method'],fmt(x['public_gain_pct']),fmt(x['confirmation_gain_pct'])] for x in kept])
sq=[x for x in rows if x['method']=='REUSE-SQ']
sq_open=[x for x in sq if not yes(x['GT_or_B32_covered'])]
sq_table=table(['数据','窗口','K','L','Recall%','完整QPS','GT质量阈值速度优势%','B32质量阈值速度优势%'],[[x['dataset'],x['window'],x['K'],x['L'],fmt(x['recall_pct'],4),fmt(x['qps']),fmt(x['GT_threshold_speed_gain_pct']),fmt(x['B32_threshold_speed_gain_pct'])] for x in sq_open])

strows=[]
for x in stable:
    strows.append([x['dataset'],x['K'],x['L'],x['method'],fmt(x['public_gain_pct']),fmt(x['confirmation_gain_pct']),'是' if yes(x['both_windows_pass']) else '否'])

examples=[]
for ds in DS:
 for K in [1,100]:
  for window in ['public','confirmation']:
    for method in ['B32','OPT-B32','REUSE-SQ','OPT-SQ']:
        a=next(x for x in rows if x['dataset']==ds and x['window']==window and int(x['K'])==K and int(x['L'])==200 and x['method']==method)
        examples.append([ds,window,K,method,fmt(a['recall_pct'],4),fmt(a['qps']),fmt(a['mean_us']),a['rescued'],a['lost'],a['GT_cover_L'] or '无',a['B32_cover_L'] or '无'])

confirm=[]
for ds in DS:
 for K in [1,100]:
    for method in ['B32','REUSE-SQ']:
        a=next(x for x in rows if x['dataset']==ds and x['window']=='public' and int(x['K'])==K and int(x['L'])==200 and x['method']==method)
        b=next(x for x in rows if x['dataset']==ds and x['window']=='confirmation' and int(x['K'])==K and int(x['L'])==200 and x['method']==method)
        confirm.append([ds,K,method,fmt(a['gain_pp'],4),f'{fmt(a["gain_CI_lo"],4)}..{fmt(a["gain_CI_hi"],4)}',fmt(b['gain_pp'],4),f'{fmt(b["gain_CI_lo"],4)}..{fmt(b["gain_CI_hi"],4)}',b['improved_queries']])

text=f'''# E194 等价省费与查询稳定性实验报告

2026-10-30。完成256正式点/768完整单线程批次，以及20资格点。默认E99 GT10保持。本轮优化原B32/SQ后端、补齐强基线并检验新查询稳定性，没有训练新门或更换原图/画像/metric。

## 结论

全部优化点的六数组返回逐字节等价，原B32候选顺序、SQ的pool/扫描块/Top96和逐query访问计数一致；性能筛选通过{v['optimization_screen_pass']}/{v['paired_points']}点，两个查询窗口均通过的配置{v['stable_configurations']}/{v['configurations']}。通过标准为同L完整QPS中位增幅>=2%且三轮配对同向；它是探索筛选，不是统计显著性或跨图默认替换证据。未通过配置仍报告真实效应，不一票否决整条路线。

{table(['数据','优化','通过点','跨窗口均通过配置','完整QPS增幅范围','中位增幅'],summary)}

可保留的等价省费配置只有两集K100/L100的OPT-B32，幅度约2.2–2.5%；更高L及K1的这次实现未达到预定稳定筛选。OPT-SQ的Top96替换不推广为稳定优化，但原SQ局部质量/费用结果继续保留。

{kept_table}

优化原有补全执行费用与证明补全优于GT10/B32是两件事。下表及完整CSV保留强控制覆盖，不能将等价省费都称作新的Recall–QPS前沿。历史E173/E191正面证据保留原时点与完整费用，本轮未用旧绝对QPS拼新点。

原B32的88点均未被本轮同窗口GT10离散网格同时覆盖，支持保留这一强基线；有限网格和同图/画像限制仍在。原SQ的{sum(yes(x['GT_or_B32_covered']) for x in sq)}/24点被GT10或B32覆盖，余下3点如下，其中COCO/K100/L400在两窗均未被覆盖。质量阈值对照可有略高Recall，尤其约2%的B32阈值余量不能当精确等Recall或充分调预算后的胜出：

{sq_table}

WebVid确认窗K100/L200的原SQ救回5074个成员，同时损失1个原命中成员；该query净命中未下降，优化版完全继承原结果。该损失保留，未做未经验证的并列/浮点因果归因，不声称补全过程零损伤。

## 实际范围与来源

COCO和WebVid各public/confirmation两个固定2048-query窗口、真实K1/K100。每组GT10与B32共11档L=[100,128,160,200,256,320,400,512,640,800,1000]；OPT-B32固定100/200/400/800，COCO的SQ/OPT-SQ固定100/200/400，WebVid固定200/400/800。没有根据本轮阳性追加矩阵。B32继承原16K训练表，SQ继承前12K教师遗漏块表；两者监督/容量不同。本轮省费在各自内部配对，不将B32/SQ差异当纯评分或容量因果。

COCO确认来自E181原未分配身份组，排除旧qgt/profile/residual/test；WebVid确认从官方原始2.5M训练query源固定抽样，与已登记ACO/router-train/validation/public-test和GT10 fit/cal/audit/validation/recovery逐向量SHA去重。确认源行和SHA见storage/inputs，不声称语义独立或全历史绝未曝光。旧public仍是曝光测试。

确认GT按全原base/raw-IP IndexFlatIP生成，无额外归一化。各固定8条用float64分块暴力检查，GT100集合及GT1全部一致；近并列数量/分数见exact_gt收据，不修改GT去消除损伤。本轮一套图/画像；新query不等于新图或独立人员复现。

## 等价优化的实质

OPT-B32：用固定512槽开放寻址表替代原候选plan的线性主返回成员/重复检查，保留三hub及行内到达次序。所有候选先按原metric评分，严格小于才替换。K1简化单元素堆，K100沿原heap。异常主返回回原apply。没有减少候选源或精算容量。

OPT-SQ：相同pool、块中心排序、<=2048码和<=96追加精算，SQ8分数连续保存，再nth_element取Top96、按(distance,arrival)排序。没有用较小预算牺牲召回换速度，也没有更换SQ码或分数实现。

正式CPU15、实际1线程、OMP/BLAS/MKL/NUMEXPR均1，单方法串行。每点预热256、三轮方法轮转。正常Batch分配/初始化、路由、主搜、补全、六数组复制与销毁全部计wall；GT/hash/保存/oracle在外。B32访问量在wall外重构，SQ计数沿原调用，均不是总NDC。没有把分段微计时相加代替完整wall。本轮验证组合实现费用，不把全部QPS变化因果归于某个单一操作。

## 全部优化配置的跨窗口表现

{table(['数据','K','L','优化','public QPS增幅%','confirmation增幅%','两窗通过'],strows)}

三轮只重复费用，同一窗口质量仅一份样本；QPS范围不作为置信区间。不同L和窗口不混拼。两窗未通过可能是收益小、波动或实际变慢，以原三轮和单点为准。

## L200完整费用与强基线

{table(['数据','窗口','K','方法','Recall%','完整QPS','us/query','救回成员','损失成员','GT覆盖L','B32覆盖L'],examples)}

GT/B32覆盖表示至少相同整数命中数且中位QPS不低（至少一项严格更好）的已测离散点。只比较同dataset/window/K，质量阈值速度不是自动的精确等Recall。其他L和三轮范围、同费用质量差全部见points.csv。SQ在WebVid的任何新观察都要与强B32比较。

## 新查询上的补全收益

{table(['数据','K','方法','public增益pp','配对bootstrap95%','confirmation增益pp','配对bootstrap95%','确认改善query数'],confirm)}

质量区间为固定seed1000次query bootstrap；同一query的主返回与补全成对。稀少K1事件需连同改善query数看，不将成员救回数当作改善query数。优化版质量严格等于原版，所以本表只列原后端。

## 证据、成本与交付

冻结协议、selection_freeze、formal_freeze绑定源码/脚本/配置/binary/静态库/新输入和原模型身份。大base/图继承历史来源并核stat，小资产完整SHA。原E193封存的科学文件验证通过，已变的可变根文档通过历史source_before/SHA桥接；本轮修改前根文档也已留存。最初封存检查未包含历史README桥接的失败尝试保留，未触及任何科学文件或性能。

全部实际timed四数组、三轮六数组hash、访问包和完整wall保留于/root/acsg-e194-storage，经storage链接。native核每条query的标量合并/全排序、B32候选次序和SQ候选/访问等价，另用stdlib array/set/hashlib复算全部点的命中、有效性和hash；同执行者不同实现，非独立人员复现。

正式四个套件进程合计{suite_seconds/60:.2f}分钟，包含加载/预热/原生核验；其中768个完整测量batch合计{batch_seconds/60:.2f}分钟，两项嵌套不可相加。新确认GT离线耗时{gt_seconds:.2f}秒（8线程），编译{read(R/'reviews/build.json')['seconds']:.2f}秒，另外记账。共享benchmark峰RSS约{peak_rss/2**30:.2f}GiB，不意味着GT10或B32部署依赖全部SQ/PQ数组。原训练表/码本/码不重建，原构建债不清零；OPT-B32逻辑哈希工作区为2KiB，OPT-SQ复用原已reserve的2048项缓冲，不新增全base模型。

[完整256点](analysis/points.csv) · [56组优化配对](analysis/optimization_pairs.csv) · [28个跨窗配置](analysis/stability.csv) · [逐query命中](analysis/per_query_hits.npz) · [Recall–QPS图](analysis/recall_qps.svg) · [协议](protocol.md) · [冻结](formal_freeze.json) · [状态](state.json)
'''
(R/'report_zh.md').write_text(text)
print('E194_REPORT_AND_SVG_PNG_COMPLETE',flush=True)

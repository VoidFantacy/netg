import sys,csv
from pathlib import Path
RUN=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RUN/'src'))
from common import *
assert not (RUN/'report.md').exists()
decision=read(RUN/'reviews/decision.json');fit=read(RUN/'results/fit_decomposition.json')
metrics=list(csv.DictReader((RUN/'results/metrics.csv').open()));actions=list(csv.DictReader((RUN/'results/action_effects.csv').open()))
def label(ds,f):return ('WebVid' if ds.startswith('webvid') else 'Yandex')+' '+f
def tab(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |' for row in rows])
def interval(x):return f'[{x[0]:+.4f}, {x[1]:+.4f}]'
def metric(ds,name,K):return next(r for r in metrics if r['dataset']==ds and r['method']==name and int(r['K'])==K)
fit_table=tab(['族','原ESS中位数','GroupMean ESS中位数','画像转角中位数','真实D能量 / 置换期望'],[[label(r['dataset'],r['family']),f"{r['original_ESS_median']:.2f}",f"{r['GroupMean_ESS_median']:.2f}",f"{r['GroupMean_angle_median']:.2f}°",f"{r['residual_frobenius_squared']/r['null_permutation_expected_frobenius_squared']:.2f}×"] for r in fit])
mechanism_table=tab(['族','K','原画像−四置换均值（pp）','描述性95%区间','四个置换的独立方向值（pp）'],[[label(r['dataset'],r['family']),r['K'],f"{r['real_minus_permutation_mean_pp']:+.4f}",interval(r['CI95_descriptive']),', '.join(f'{v:+.4f}' for v in r['real_minus_each_permutation_pp'])] for r in decision['mechanism']])
primary_table=tab(['族','K','原GT10 exact Recall','GroupMean exact Recall','差值（pp）','98.75%区间','零命中 原→新'],[[label(r['dataset'],r['family']),r['K'],f"{r['baseline_recall']*100:.4f}%",f"{r['candidate_recall']*100:.4f}%",f"{r['delta_recall_pp']:+.4f}",interval(r['CI98_75']),f"{r['baseline_failed']}→{r['candidate_failed']}"] for r in decision['primary']])
ann_table=tab(['族','K','当前默认ANN Recall','零命中 ANN→候选exact','候选exact−当前ANN（pp）'],[[label(r['dataset'],r['family']),r['K'],f"{float(metric(r['dataset'],'DefaultANN',r['K'])['recall'])*100:.4f}%",f"{metric(r['dataset'],'DefaultANN',r['K'])['failed_queries']}→{r['candidate_failed']}",f"{r['delta_vs_current_ANN_pp']:+.4f}"] for r in decision['primary']])
gt1_table=tab(['族','K','GT10 exact−GT1 exact（pp）','GT10 exact / GT1 exact Recall'],[[label(ds,f),K,f"{(float(metric(ds,f.title()+'OriginalExact',K)['recall'])-float(metric(ds,'GT1Exact',K)['recall']))*100:+.4f}",f"{float(metric(ds,f.title()+'OriginalExact',K)['recall'])*100:.4f}% / {float(metric(ds,'GT1Exact',K)['recall'])*100:.4f}%"] for ds,c in LOCK['datasets'].items() for f in c['families'] for K in LOCK['K']])
selected=[r for r in actions if 'GroupMean' in r['method'] and r['family']==('soft' if r['dataset'].startswith('webvid') else 'hard')]
action_table=tab(['族','K','改变入口的查询','改变返回的查询','Recall增 / 损查询','多找回 / 少找回目标','净目标数'],[[label(r['dataset'],r['family']),r['K'],f"{r['changed_entry_queries']}/4096 ({float(r['changed_entry_pct']):.2f}%)",r['changed_output_queries'],f"{r['higher_recall_queries']} / {r['lower_recall_queries']}",f"{r['gained_target_hits']} / {r['lost_target_hits']}",r['net_target_hits']] for r in selected])
jobs=read(RUN/'reviews/jobs.json');prepare=read(RUN/'reviews/models_frozen.json');search=read(RUN/'reviews/search_complete.json')
report=f'''# E106：GT10条件机制分析与条件聚合检验

2026-09-20，已完成“机制推导 → 唯一候选 → 冻结实验 → 独立核验”的第一轮闭环。**STOP_GROUPMEAN_CANDIDATE**：两集均未达到事前质量门，不进入该候选的实际ANN建图/完整wall阶段。原默认WebVid GT10-soft-t1、Yandex GT10-hard及生产E99保持。没有找到稳定改进，也没有由本轮证明GT10收益的完整原因。

## 这轮改变了什么认识

GT10包含非随机的组内query–目标关联，但这种向量结构强，不等于真实搜索收益强。在保持每hub权重多重集与ESS的干预中，原画像相对四个条件置换没有稳定的Recall优势。把组内关联全部平均掉，同样没有稳定获益。两项结果只限制当前解释，不能推出“细节完全无用”或“GT10仅靠平滑有效”。

更早需要核对的前提是比较对象。当前两集、真实K1/K100、L128、精确画像路由下，GT10相对GT1的Recall差异本身就是混合的。既有GT10相对NSG的系统收益、GT10相对GT1的增量、相同Recall下的QPS，必须分别解释。本轮没有NSG单入口对照或新QPS，不能否定[E103完整五集前沿](../20260916_optimized_five_dataset_r1_r100_v1/report.md)，也不能用这一个L替代它。

## 先推导：GT10究竟估计了什么

原画像是固定相关性权重下的闭式球面代理解，详见[上一轮理论复盘](../20260920_gt10_theory_review_v1/report.md)。令单位query为z_i，完整GT10归属向量为a_i，g_i为该query的GT1目标最近原hub。以g分组，计数n_g，平均归属m_g，平均query方向c_g。对每hub h，未归一化画像严格满足：

\\[
v_h=u_h+\\sum_i a_{{ih}}z_i
=\\underbrace{{u_h+\\sum_g n_gm_{{gh}}c_g}}_{{B_h}}
+\\underbrace{{\\sum_g\\sum_{{i\\in g}}(a_{{ih}}-m_{{gh}})(z_i-c_g)}}_{{D_h}}.
\\]

B保留GT1区域内部共同的多目标关系；D保留该区域内query方向与更细目标归属的交叉矩。GT1 hard在组内归属恒定，所以D=0；但GT10相对GT1的差异不全等于D，B也发生改变。

固定query，在每个同GT1组内均匀置换**完整a行**。每hub所有权重值、质量、平方和、ESS及query总质量均严格不变；GT1 hard标签保留。干预通过画像方向起作用，方向并非应固定的混杂因素。单例组不动，不强制无固定点。

\\[
E_\\pi[v_h^\\pi]=B_h,\\qquad
E_\\pi\\|D_h^\\pi\\|^2
=\\sum_{{g:n_g>1}}\\frac{{\\sum_{{i\\in g}}(a_{{ih}}-m_{{gh}})^2\\;\\sum_{{i\\in g}}\\|z_i-c_g\\|^2}}{{n_g-1}}.
\\]

后一式由无放回置换协方差及组内中心化得到；它是固定fit表上的干预尺度，不能冒充泛化误差或Recall定理。[推导、反例和旧分支区别](research.md)在fit及查询访问前锁定，[六种置换的独立枚举核验](reviews/analytic_check.json)通过。

由Eπ[vπ]=B只推导一个候选：**GroupMean=normalize(B)**。它在未归一化向量上取条件平均，再归一化；没有alpha、组数或网络选型。若需迁移的方向主要由B表示，它可能更稳；若D含有效信息，它可能变差。条件平均本身没有一般的MSE/Recall改进保证。GroupMean会增加ESS，严格匹配ESS的是置换对照，不能混淆两者。

Web soft沿用硬GT1分组，未保留query特定的GT1软概率，其机制结果不能称为纯第2–10名尾部效应。hard两集为主要机制，Web soft用于匹配实际默认。此项区别于E27全局tail打乱、E26单位画像插值、E80目标条件化子画像、E95查询矩构图；不声称条件置换本身是新算法。

## fit结果：关联存在，但还不能叫作搜索信号

各族20K合法fit query，原画像/归属摘要恢复；V=B+D最大误差7.07e−14。画像原件用于baseline，不用舍入后的重建文件替代。

{fit_table}

真实D能量是随机干预期望的4.91–8.95倍，四个实际置换能量接近解析期望。说明当前fit关联有结构；不证明结构有检索价值，亦不提供总体显著性。

## 再检验：完整固定对照

模型全部冻结后，复制E105各4096条已曝光query及其原GT100作机制/开发验证，非新盲测。Web14/Y8方法：GT1 exact，每族原GT10 exact、GroupMean exact、四固定seed置换exact，另原默认真实ANN。全H原IP距离取真实3入口，再进同一原raw-IP NSG；实际返回K1/K100，L128。缓存路线只服务质量归因，不测在线QPS。

原默认ANN逐条恢复E105的入口、返回ID、距离bits和NDC。各方法完整count/plain输出一致，独立Python集合评分核验全部4096行；重复query及同三入口的输出/距离bits/NDC全匹配。每点8条返回距离使用原base做float64检查，exact每方法16条做独立全H排序检查。

条件置换结果，单位均为百分点：

{mechanism_table}

六项描述性95%区间全部跨0，每项的四个seed方向均混合。四次随机干预不是四套独立数据，也不是校准的条件独立p值。此结果不支持“同GT1区域内细粒度对应必然提供稳定Recall收益”；也不是等效性证明，区间仍容许正负效应。

![条件对应机制检验](figures/conditional_correspondence.png)

## 候选结果：未过预锁门

冻结主门要求Web soft与Y hard各自两K均值不降、至少一项≥0.5pp且至少一项校正98.75%区间下界>0；四主指标各20000次固定seed配对bootstrap。Web hard只作辅助，不用于重新选Web默认。

{primary_table}

两集均未过门，四主区间全部跨0。Web两个半段方向相反；Y两个半段都是小正值，但不足以通过门。Web hard辅助R1/R100为−0.1709/+0.0198pp，同样不能支持另选主族。Web soft K100零命中4→0这一正面变化完整保留，但平均Recall略降；不能只挑失败query子集宣布有效。

为防止把精确路由的收益计入新画像，下表另列当前实际ANN基线；候选仍是exact，不是已部署ANN对比：

{ann_table}

![GroupMean质量检验](figures/groupmean_quality.png)

## 事后解释：画像、入口和真实收益之间隔了什么

以下只统计本轮已有全量输出，不新增搜索、不改变冻结门，脚本/全部36项保存在[action_effects.py](postprocess/action_effects.py)与[完整CSV](results/action_effects.csv)。

{action_table}

GroupMean改变Web soft 75.59%、Y hard 59.99%的三入口，但K1只有98/52条查询命中改变；K100只有739/310条查询命中数改变。其余入口改动未转化成当前指标差异。发生改变的查询又同时存在收益和损失，Web K100额外找回2136个目标却丢失2227个，Y为1793与1767。**改变很多入口不等于获得很大的净改进空间。** 此处计数是查询各自GT内的命中次数，不是全库去重目标数。

更直接的前提检查如下，均为已测相同exact路由条件：

{gt1_table}

因此本轮不能从“GT10在这组条件上一定更准”出发构造故事。所有条件置换的平均graph NDC都略高于对应原GT10；主族GroupMean的NDC增加Web0.3622%、Y0.0656%。这些是实际距离计算量的描述，未做对应成本显著性/完整wall验证，不能换算QPS或据此声称保留了性能优势。

## 本轮之后，理论任务应如何收敛

先识别要解释的是**哪个baseline、哪段预算和哪种收益**。本轮只完成对“组内细节/条件平滑”的一次可证伪检验；目前尚未识别GT10相对NSG整体收益中，查询画像、真实hub覆盖、多入口和搜索路径各自的贡献。

已明确的缺口是代理到真实搜索的转换：q·p_h描述查询与训练目标区域的相关性；实际U_K,L(q,S)由三入口共同触发的有限预算轨迹决定。闭式代理目标再精确，也未控制两者误差；B/D分解本身不改变这个事实。需要建立可验证的路径/预算条件和反例，再推导新目标或可部署动作，不能把D能量大、ESS增加、角度变小当作收益定理。

下一方法立项必须先说明它如何区别于已有真实联合效用监督E104、已停的WFree E105和历史局部动作分支，并在同监督简单控制上提出会失败的可检验预言。此处不提出已被实验支持的新网络、收缩系数或门控方法；**停止GroupMean及其参数追加**。实际ANN/独立完整wall是通过质量门后的条件步骤，本候选未满足条件，所以不产生后续运行队列。

## 成本、身份与交付

fit闭式构造约{prepare['seconds']:.2f}秒，编译约{read(RUN/'reviews/build.json')['seconds']:.2f}秒；搜索编排约{search['seconds']:.2f}秒（含输入/身份准备与加载），四搜索子进程合计{search['child_seconds']:.2f}秒；主要独立评分约{read(RUN/'reviews/analysis_complete.json')['seconds']:.2f}秒。它们不是在线延迟/QPS。最大搜索RSS约{max(j['complete']['maxrss_kib'] for j in jobs)/1024**2:.2f}GiB。

共361856次NSG调用、16448次原默认小图ANN路由；前16行smoke与全4096行主测试分开保留。构造15份闭式候选/置换画像，**0梯度训练、0新GT、0新图、0新K10、0正式QPS**。CPU15、方法及数据串行、实际线程1；总量低于预锁400000次NSG、3600秒子进程和40GiB上限。

原fit/GT/归属/模型等23个保护文件SHA在前后核验；两完整base按E105 GT manifest重验SHA，大图沿用身份并核对stat、加载合同及内嵌base抽查，未声称重新全NSG哈希。模型与源码分别在评估载荷访问前封存。旧root文档的修改前快照、更新前快照以及全部正负结果保留；新报告/图表与根文档同步后由[收尾审计](reviews/completion_audit.json)确认完成。

证据入口：[冻结协议](protocol.md) · [配置](config.locked.json) · [全部44点指标](results/metrics.csv) · [完整候选配对](results/candidate_pairs.csv) · [候选/原画像零命中并集](results/failure_queries.csv) · [全方法逐query命中](results/aligned_hits.npz) · [原始搜索成本](reviews/jobs.json) · [数值核验](reviews/numeric_verification.json) · [预锁门判定](reviews/decision.json)。全方法原始返回保留于results各数据集目录；failure_queries.csv仅为原画像与GroupMean的失败并集，不能当所有置换方法失败清单。
'''
(RUN/'report.md').write_text(report)
print('Report written',len(report.splitlines()),'lines')

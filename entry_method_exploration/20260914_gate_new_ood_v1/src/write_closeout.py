"""Build reviewable report and synchronize the four project document roles."""
from common import *
import csv, shutil

def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n|'+ '|'.join(['---']*len(headers))+'|\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)

def main():
    assert json.loads((RUN/'reviews/final_numeric_audit.json').read_text())['status']=='PASS'
    rows=list(csv.DictReader((RUN/'results/metrics.csv').open())); keyed={(x['dataset'],x['method'],int(x['L'])):x for x in rows}
    names=dict(zip(DATASETS,['WebVid','Yandex','LAION']))
    methods=['NSG','GT10','GATE','HNSW']
    costs=json.loads((RUN/'results/offline_costs.json').read_text()); notes=json.loads((RUN/'results/cost_accounting_notes.json').read_text())
    runtime=json.loads((RUN/'results/runtime_actual.json').read_text())
    common=list(csv.DictReader((RUN/'results/common_recall.csv').open()))
    threshold_rows=[]
    for ds,targets in zip(DATASETS,[[.7,.8,.9],[.9,.95,.99],[.8,.9,.95]]):
        for target in targets:
            row=[names[ds],f'{target*100:g}%']
            for method in methods:
                p=next(x for x in common if x['dataset']==ds and x['method']==method and float(x['target_recall'])==target)
                row.append(f"{float(p['qps']):.1f} / {p['L']} / {float(p['measured_recall'])*100:.3f}%" if p['achieved']=='True' else '未达到')
            threshold_rows.append(row)
    endrows=[]; failrows=[]; trainrows=[]; ndcrows=[]
    for ds in DATASETS:
        failrows.append([names[ds]]+[f"{float(keyed[(ds,m,1500)]['failed_query_rate'])*100:.2f}% ({keyed[(ds,m,1500)]['failed_queries']}/10000)" for m in methods])
        for m in methods:
            x=keyed[(ds,m,1500)];endrows.append([names[ds],m,f"{float(x['recall_at10'])*100:.3f}%",f"{float(x['qps_mean']):.2f}",f"{float(x['failed_query_rate'])*100:.2f}%",f"{float(x['gt1_miss_rate'])*100:.2f}%"])
        tr=json.loads((RUN/'models'/ds/GATE_MODEL/'complete.json').read_text());c=next(x for x in costs if x['dataset']==ds);n=next(x for x in notes if x['dataset']==ds)
        trainrows.append([names[ds],tr['epochs'],tr['best']['epoch'],f"{c['gate_label_seconds']:.2f}",f"{c['gate_training_seconds']:.2f}",f"{n['effective_GATE_known_preparation_subtotal_seconds']/60:.2f}"])
        for m in ['GT10','GATE']:
            x=keyed[(ds,m,128)];ndcrows.append([names[ds],m,f"{float(x['route_ndc_mean']):.2f}",f"{float(x['graph_ndc_mean']):.2f}",f"{float(x['qps_mean']):.2f}"])
    report=f'''# E96：三数据集 GATE / GT10 / NSG / HNSW 完整比较

2026-09-15 完成。三套完整底库、每集10000条公开测试query，四方法、16预算、每点三次单线程平均：192点、576次计时全部通过。最终方法为 `gate_release10_v2`；Web/Y被替代的旧采样训练不进入结果。

WebVid和Yandex上，GT10在全部16个预算点的实测Recall及平均QPS都高于GATE，GATE没有进入这两集的已测点联合Pareto集合。按三次计时范围，Web有13/16点、Yandex有14/16点完全分离；其余微小速度差不作统计显著性判断。LAION有质量与速度取舍：GATE在L1500达到96.287% Recall、145.86 QPS、3条零命中；GT10为96.154%、148.94 QPS、6条零命中。GATE多0.133个百分点Recall、QPS低2.06%，且只相差3条失败，不能概括成全面胜出。

GT10与全量HNSW也有交叉，不能宣称GT10在所有召回目标上最快。本轮没有替换项目默认方法；Web保持GT10-soft-t1、Y保持GT10-hard，LAION本轮在开发集选出soft-t1。E95固定H增强分支的停止结论保持原适用范围。

## 图与完整数据

![Recall与QPS](figures/recall_qps.final.png)

![零命中失败率](figures/failed_query_rate.final.png)

[Recall–QPS PDF](figures/recall_qps.final.pdf) · [失败率PDF](figures/failed_query_rate.final.pdf) · [192点完整数据](results/metrics.csv) · [配对挽救与新增失败](results/paired_queries.csv) · [各召回门槛最快已测点](results/common_recall.csv)。初始图保留；最终图只修正图例及配对明细文件名，指标不变。

## 达到相同召回门槛的速度

下表每格为 **QPS / L或efSearch / 实测Recall**，从全部16点选择达到门槛的最快实测点，不插值、不外推。不同方法可能超过门槛的程度不同，因此表格描述门槛约束下的已测选择，不等于精确相同Recall的连续曲线拟合。

{table(['数据集','最低Recall','NSG','GT10（我们）','GATE（适配）','HNSW'],threshold_rows)}
Web的四方法均未达到95%；Y的GT10在当前固定10000条query上刚过99%，不能把这一阈值跨越解释为稳健的总体99%保证；LAION四方法均未达到99%。完整曲线与所有未达标值均保留。

## 最大预算及失败定义

主失败定义是 **返回top10与exact GT top10交集为空，即单query Recall@10=0**。它不等于漏掉任意真近邻，也不等于GT1未返回；后者单独列出。L和HNSW efSearch不是等工作量，下面是最大预算的实际端点。

{table(['数据集','方法','Recall@10','平均QPS','零命中率','GT1未返回率'],endrows)}
每个点都有原始IDs、距离、真实入口、路由/底图NDC以及逐query hits、零命中、GT1 miss文件；没有从公测中筛除失败query。配对明细在同预算下统计，不能当作等工作量比较。例如LAION L1500，GATE相对GT10挽救3条零命中、新增0条，75条query命中增加、22条减少；Web则挽救2条、新增4条。

## 实际方法与训练流程

底库分别为WebVid 2505000×512 raw-IP、Yandex官方前10000000×200 raw-IP、LAION 10004480×512 unit-IP。每集使用原冻结NSG和匹配的exact GT；Y从公开100K取前10000条，另两集使用公开10K。Web和LAION公开测试query同源；这些public资产有项目历史曝光。结论适用于本轮三个工作负载，不声称三套全新盲测分布。

1. **NSG**：原底图、原固定单入口、原 `search_new` mode2。**GT10**：真实QGT hub（Web815、Y/LAION821）→ fit20K的GT10归属权重累计单位query画像及真实hub先验→单位画像Micro-HNSW M16/efC200/ef10→top3映射真实ID并升序→原NSG。画像不是800个原始base向量。Web/Y复用冻结画像；LAION用cal1024、L128比较hard/soft-t1，按总命中、底图NDC、hard平局优先选择soft-t1（8447对8435命中），公测前冻结。
2. **GATE hub与特征**：两层32×16 HBKM得到512真实hub；在原NSG中固定5近+5远，至多5hop/1000节点采样，构造Graph2Vec及原hub向量特征。Web的HBKM实物复用，其余两集本轮构建。原协议误记8×8×8，已在新hub构建前由来源manifest修正。
3. **GATE标签**：训练query为router_train[10000:20000]，monitor为[2048:3072]，每集11024×512次L64/K1搜索；以GT1首次发现的图深度构造监督，仅当最终返回GT1时该hub标签有效，其余为999。三集共16932864次标签搜索，原kernel与observer返回/距离逐位核验。正负样本规则沿固定release逻辑，每hub最多50正、50负形成三元组；训练过滤只作用于监督样本，不作用于最终10000条公测。
4. **GATE训练及导出**：hub向量与Graph2Vec经fusion Transformer和hidden2024 tower生成d维入口向量，cosine triplet margin1；Adam 1e-5、batch16384、seed42、最多200epoch，monitor RouteAcc连续20轮不改善停止，冻结最佳checkpoint。修正batch/sequence维度并验证单条/批量输出独立；每batch同hub合并forward是CPU适配，会共享该hub的dropout。本版不是作者代码的逐位原样复现。导出512个单位W后，线上只有query归一化、小HNSW M256/efC256/ef10/top3（release heap顺序映射）及原NSG，没有query神经网络前向。
5. **全量HNSW**：在各完整base上独立构建M32/efC200/seed20260828，离线16线程；构建RNG加锁、实际有序拓扑冻结。原float32向量无损恢复，所有节点的向量/标签/层级/有序邻接及128条query逐位往返验证通过。gzip仅保存拓扑以避免复制数十GB向量，在线搜索使用完整内存索引；保存/加载不计入QPS。

GATE训练10K与GT10 fit20K不同，不能称离线工作量相等。[原协议](protocol.md)、[HBKM修正](hbkm_provenance_amendment.md)、[采样修正](sampling_amendment.md)、[方法说明](method_notes.md)和各模型config为精确配置。GATE参考[固定release](https://github.com/jacksondca/gate/tree/229f18dadb791ddede22597e44d5ceb028b104ba)，本轮NSG/IP、序列维度、采样上限和CPU实现的差异已记录；不将适配结果冒称论文原始数字。

## 时间、工作量与可解释边界

全部正式点串行、CPU15、实际进程及OMP/BLAS/MKL线程均为1。预算固定32、48、64、96、128、160、200、256、320、400、512、640、800、1000、1250、1500。每点一整批warmup、三轮plain wall、一次独立count；主QPS是三个10000/wall的算术平均，同时保留10000/平均wall。所有轮次及count的IDs/距离/入口一致。计时包含完整路由、必要归一化、映射、排序、图搜索及内存结果写出；GT评分、计数、磁盘I/O、加载和构图在计时外。

正式阶段从2026-09-14 21:16:46到09-15 02:02:15，合计 **{runtime['formal_stage_hours']:.3f}小时（4小时45分29秒）**；Web/Y/LAION分别85.82/83.47/116.18分钟。576次计时共5760000条query调用；加warmup/count共9600000条。此前正式矩阵估计6.22小时；19:30给出的剩余总时间估计7–8小时、保守5.5–13小时，实际到矩阵结束约6小时32分，文档收尾另计。

{table(['数据集','实际epoch','选中epoch（从0计）','标签秒','最终tower训练秒','GATE有效准备已知小计/分钟'],trainrows)}
有效准备小计包含最终特征、标签、tower及本轮已知HBKM；Web历史HBKM未知。LAION特征945.11秒已包含HBKM922.57秒，不能重复相加；LAION整个features子进程1211.23秒另含输入准备与身份核验。历史GT、原NSG构建及Web/Y继承画像的完整成本未知，记为null。被替代Web训练739.51秒、取消的旧Y训练至少518.70秒另记，环境重启丢失的在途成本不冒称完整已测。[分项原值](results/offline_costs.json) · [避免重复计费的说明](results/cost_accounting_notes.json)。

HNSW程序记录的累计构建秒为Web262.85、Y1083.03、LAION1528.86；Y含358.18秒检查点写出，LAION恢复计时包含恢复加载且未覆盖失败保存的全部开销，不把三个值统称纯插入成本。另列保存/恢复/核验。LAION磁盘保护失败阶段1606.45秒及成功恢复144.42秒在独立记录中保留；完成节点未重建。它只影响离线耗时，正式矩阵没有失败重跑。

L128的实测成本例子如下。GATE小图每query路由约288–301次距离计算，GT10约107–112次；底图工作也不同，所以只看Recall或某一NDC不能替代完整QPS。

{table(['数据集','方法','路由NDC均值','底图NDC均值','完整QPS均值'],ndcrows)}
三次计时范围是观察范围，query bootstrap和Wilson区间是描述性不确定性；三次重复并非三批独立query。高L的几条失败差异不作分布层面的显著性保证。

## 验收与存储

[最终数值审计](reviews/final_numeric_audit.json)核对192点/576轮、实际单线程、唯一boot、无正式重跑、逐query记录、三次均值、288条配对恒等式、60条召回门槛选择、模型/二进制/原源码与静态库身份。三集预检、标签parity、模型独立性、完整HNSW往返、合成评测恢复均通过；图像已另行目视核查。封存见[完成记录](complete.json)。

磁盘保护时，本轮未完成LAION构建目录曾转存系统盘并保留原路径链接。测试结束后，按用户明确授权删除已解压原归档`/data/netg.tar.gz`（53154931501字节），逐文件SHA校验把LAION索引恢复到项目内普通目录；原base/NSG/GT/模型及失败产物保留，系统盘校验副本也保留。见[恢复记录](reviews/storage_recovery_20260914T2113/manifest.json)和[最终存储记录](reviews/storage_closeout/manifest.json)。
'''
    (RUN/'report.md').write_text(report)
    snap=RUN/'reviews/docs_before_closeout';snap.mkdir(exist_ok=False)
    for name in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
        shutil.copy2(ROOT/name,snap/name.replace('/','__'))
    hist=ROOT/'experiment_history/88_gate_three_dataset_comparison.md';assert not hist.exists()
    hist.write_text('''# E96：GATE三数据集完整比较

2026-09-14启动，09-15完成。用户授权GATE、当前GT10、NSG、全量HNSW在WebVid/Yandex/LAION比较，16个预算至1500，每点三次单线程平均，交付Recall–QPS与失败率；不以方法质量删点，不追加第四集。它是独立对照实验，不是重启E95固定H增强分支。

实物位于[独立E96目录](../entry_method_exploration/20260914_gate_new_ood_v1/report.md)。输入为三集完整base及公开10K，Y取public100K前10K；原NSG/GT身份冻结。Web/LAION测试query同源，public资产已有项目曝光；最终query未用于本轮模型选择。

GT10沿真实QGT hub→GT10 query画像→Micro-HNSW top3→原NSG。Web/Y沿冻结soft-t1/hard；LAION只按cal1024、L128选soft-t1。GATE用两层32×16 HBKM、512真实hub、release10的5近5远子图、Graph2Vec、GT1首次发现hop监督、cosine triplet tower及静态W导出；线上小HNSW3入口到原NSG。训练10K、monitor1024，与GT10 fit20K不同。全量HNSW在每集完整base构建M32/efC200，保存无损有序拓扑并逐节点/128query核验。详细适配差异和配置见原报告及协议，不能称作者程序逐位复现。

结果：192点、576次plain wall及独立count完成，实际CPU15/线程1/单boot/串行；逐query共192万组输出，两种集合评分及最终配对、均值、身份审计通过。Web和Y的GATE全部16个点均被同预算GT10的Recall/平均QPS直接支配；LAION高预算有较高Recall与较低速度的取舍，L1500 GATE96.287%/145.86QPS/3失败，GT1096.154%/148.94QPS/6失败。全量HNSW与GT10前沿交叉，不能称GT10处处最快。默认未替换。

最大预算零命中数（NSG/GT10/GATE/HNSW）：Web13/4/6/11，Y18/13/16/29，LAION7/6/3/48，分母各10000；主失败为Recall@10=0，GT1漏失另报。三次计时范围和query描述区间不构成普遍显著性保证。

正式阶段4.758小时，原估计6.22小时；从09-14 21:16:46到09-15 02:02:15。最终GATE tower训练639.97/751.71/1331.11秒；标签151.23/200.82/230.21秒。LAION特征945.11秒已含HBKM922.57秒，成本不得相加。原GT/NSG/继承画像成本未知；被替代训练和在途丢失成本单列。

关键修正保留历史：原HBKM层级误读8×8×8在新hub构建前改32×16；旧动态子图采样[-0:]错误在public测试前修正为固定release10，并重训Web/Y，旧产物不进入正式结果。环境重启增加训练/HBKM/HNSW/按完整L块评测恢复。LAION全节点构建后最终保存触发磁盘下限，检查点转存系统盘续存，全节点未重建；所有正式点一次完成。用户后来授权删除原归档，测试后删除netg.tar.gz并逐文件校验将LAION索引恢复项目目录，旧数据/图/模型/失败产物保留。

主要证据：[报告与图](../entry_method_exploration/20260914_gate_new_ood_v1/report.md)、[锁定协议](../entry_method_exploration/20260914_gate_new_ood_v1/protocol.md)、[采样修正](../entry_method_exploration/20260914_gate_new_ood_v1/sampling_amendment.md)、[完整指标](../entry_method_exploration/20260914_gate_new_ood_v1/results/metrics.csv)、[数值审计](../entry_method_exploration/20260914_gate_new_ood_v1/reviews/final_numeric_audit.json)、[成本](../entry_method_exploration/20260914_gate_new_ood_v1/results/offline_costs.json)、[完成封存](../entry_method_exploration/20260914_gate_new_ood_v1/complete.json)。下一步以新的用户任务为准；本轮没有新增调参或默认部署。
''')
    p=ROOT/'experiment_history/README.md';t=p.read_text();anchor='|---|---|\n';assert anchor in t;t=t.replace(anchor,anchor+'| [88 GATE三数据集完整比较](88_gate_three_dataset_comparison.md) | E96三集完整base/公开10K、192点576轮单线程；Web/Y GT10支配GATE，LAION高预算质量速度取舍，失败率/成本/恢复与全部证据 |\n',1);p.write_text(t)
    p=ROOT/'s-experiment.md';t=p.read_text();start=t.index('E96 正在');end=t.index('## 1. 已执行的实验与诊断');t=t[:start]+'''2026-09-15最新完成E96：三数据集、四方法、16预算至1500、192点576轮单线程；Web/Y GT10在全部预算支配GATE的Recall/平均QPS，LAION高预算存在质量速度取舍，默认未替换。见[复盘88](experiment_history/88_gate_three_dataset_comparison.md)及[完整报告](entry_method_exploration/20260914_gate_new_ood_v1/report.md)。E95固定H增强分支停止结论保留，E94是更早的旧分支最终矩阵。

> 更新截至2026-09-15。本文负责历史概览与复盘索引；原协议、源码、配置和实测产物决定实现与结论，原始证据保留原处。当前结果见[summary](summary.md)，实现合同见[spec](spec.md)，后续任务见[s-target](s-target.md)。

'''+t[end:];anchor='|---|---|---|---|\n';assert anchor in t;t=t.replace(anchor,anchor+'| E96 GATE三数据集完整比较 | 三套完整base/10K query、四方法、16预算、192点576次单线程wall | Web/Y全部GATE点被GT10支配；LAION高预算质量/速度取舍，默认未替换；失败率与完整成本边界保留 | [88 完整对照](experiment_history/88_gate_three_dataset_comparison.md) |\n',1);p.write_text(t)
    p=ROOT/'summary.md';t=p.read_text();first=t.index('2026-09-14 E96');end=t.index('\n',first)
    current='''2026-09-15 E96已完成：WebVid/Yandex/LAION完整底库、各10000公开query，GATE（release10适配）、当前GT10、NSG、全量HNSW，16预算至1500；192点576次单线程wall及逐query评分、配对、身份/线程审计通过。正式阶段4.758小时，图表已检查，原始结果全部保留。[报告与图](entry_method_exploration/20260914_gate_new_ood_v1/report.md) · [完整CSV](entry_method_exploration/20260914_gate_new_ood_v1/results/metrics.csv) · [复盘88](experiment_history/88_gate_three_dataset_comparison.md)。

Web/Y上，GT10在全部16预算均有高于GATE的Recall和平均QPS；LAION高预算有取舍：L1500 GATE96.287%/145.86QPS/0.03%零命中，GT1096.154%/148.94QPS/0.06%。全量HNSW与GT10也有前沿交叉，不能称任何方法全条件最快。Web/Y最大预算的GT10分别93.506%/192.05QPS/0.04%、99.007%/206.44QPS/0.13%。主失败定义为Recall@10=0，GT1漏失另报。默认Web软/Y硬保持，LAION本轮cal选择soft-t1；没有按public结果追加训练。

最终GATE训练639.97/751.71/1331.11秒，标签151.23/200.82/230.21秒；历史GT/NSG/继承画像成本未知，不能当零。LAION特征已含HBKM，不重复计费。旧采样错误、环境重启和存储保护恢复均已隔离记录；所有正式点在同一boot一次完成。按用户授权删除原netg.tar.gz后，LAION索引已校验恢复项目目录；原base/NSG/GT/模型不变。Web/LAION公开query同源，结论不是三套全新盲测。以下保留已结束E95分支的历史结果。
''';p.write_text(t[:first]+current+t[end:])
    p=ROOT/'s-target.md';t=p.read_text();start=t.index('2026-09-14 当前任务');end=t.index('\n',start);p.write_text(t[:start]+'''2026-09-15 E96用户任务已完成：三集完整四方法192点/576轮、Recall–QPS与失败率图、原始CSV、成本、报告和身份/单线程/逐query验收均已交付；不需要继续当前runner或追加网格。Web/Y GT10优于本轮GATE适配，LAION高预算保留质量与速度取舍；默认保持，后续工作以新的用户目标为准。[结果报告](entry_method_exploration/20260914_gate_new_ood_v1/report.md) · [完成记录](entry_method_exploration/20260914_gate_new_ood_v1/complete.json)。以下为E95已结束增强分支的历史停止范围。'''+t[end:])
    p=ROOT/'spec.md';t=p.read_text();start=t.index('E96 独立实现补充：');end=t.index('\n## ',start)
    contract='''E96独立实现位于`entry_method_exploration/20260914_gate_new_ood_v1/src/`，最终GATE模型名`gate_release10_v2`。三集输入SHA及原NSG内base向量逐位身份、机械提取的首次发现depth observer与原kernel返回、tower批/单条独立性、全量HNSW有序拓扑/向量/标签/128query往返全部通过。原ACSG源码和静态库不改。

`prepare.py`读取原native NSG并构造32×16 HBKM真实hub、固定5近5远/5hop/1000节点特征；`labels.cpp`只在train/monitor生成L64/K1真实首次发现hop；`train_gate.py`以cosine triplet/Adam训练并导出单位W。`profiles.py`仅在LAION fit20K构造hard/soft候选并以cal1024选择。具体CPU/IP、batch维度及旧采样修正见[协议及修正](entry_method_exploration/20260914_gate_new_ood_v1/report.md)。

`build_hnsw.cpp`在完整base构建M32/efC200，topology/checkpoint保存有序层级邻接与标签，原float32向量从绑定SHA的base逐位恢复；恢复机制见[recovery](entry_method_exploration/20260914_gate_new_ood_v1/recovery.md)。`evaluate.cpp`包含原NSG单入口、GT10画像小图3入口、GATE小图3入口和完整HNSW四条实际调用链；只GATE在线归一化query，GT10按原raw query/IP路由，NSG保持原query/metric。GATE heap映射顺序、GT10真实ID升序均由count分支核验入口注入。

正式执行192点/576轮，16预算32至1500；CPU15/实际进程及库线程1，单方法串行。每点warmup+3次plain wall+count，所有ID/距离/入口逐位相同；距离计数通过真实DistanceComputer/距离函数包装在独立count分支记录，plain定时不启用计数器。QPS为三轮N/wall均值，另存N/平均wall；GT与磁盘I/O/加载/构建外置。原始逐query文件、metrics、配对、bootstrap/Wilson描述区间、召回门槛最快实测点和PNG/PDF均有独立输出。最终数值审计只读已有返回，不运行新ANN；源码/模型从preflight至formal结束身份不变。[验收](entry_method_exploration/20260914_gate_new_ood_v1/reviews/final_numeric_audit.json)。
'''
    t=t[:start]+contract+t[end:]
    old='大文件默认写入 `/data`。E96 的新建LAION完整HNSW在最终保存时触发该卷1.5GiB空余保护，未完成构建目录逐文件SHA校验转存到 `/root/acsg-artifacts/20260914_gate_new_ood_v1/laion10m_acsg_v1/hnsw`，原E96路径保留符号链接；这是本轮存储容量例外，不移动原base/NSG/历史模型。转存与中断文件证据见[E96存储恢复](entry_method_exploration/20260914_gate_new_ood_v1/reviews/storage_recovery_20260914T2113/manifest.json)，不改变图构建/恢复格式或在线计时合同。'
    assert old in t;t=t.replace(old,'大文件默认写入 `/data`。E96曾因1.5GiB空余保护将未完成LAION构建文件校验转存系统盘；正式测试后，按用户授权删除已解压`/data/netg.tar.gz`，逐文件SHA核验将索引恢复项目普通目录。系统盘校验副本保留，原base/NSG/GT/历史模型不变，保存/加载均不计入QPS。[存储收尾证据](entry_method_exploration/20260914_gate_new_ood_v1/reviews/storage_closeout/manifest.json)。',1);p.write_text(t)
    p=RUN/'recovery.md';p.write_text(p.read_text()+'\n## 2026-09-15完成\n\n三集正式192点/576轮在同一boot一次完成；未使用正式L块恢复。LAION离线全节点检查点恢复验证通过。用户授权清理原归档后，所有本轮主索引已逐文件校验恢复项目/data目录，系统盘副本保留。见reviews/storage_closeout/manifest.json；不再接续历史PID。\n')
    print('Report, history card 88, and four document roles synchronized; final seal still pending.')

if __name__=='__main__':main()

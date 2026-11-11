#!/usr/bin/env python3
"""Write a single current view, with dated history kept outside the root documents."""
from pathlib import Path
import csv
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
ARC='experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive'
E184='entry_method_exploration/20261024_residual_geometry_diagnosis_v1'
E183='entry_method_exploration/20261017_gt10_residual_comprehensive_v1'
def readrows(p):return list(csv.DictReader(p.open()))
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
        ['| '+' | '.join(map(str,r))+' |' for r in rows])
def put(p,s):p.write_text(s.strip()+'\n')
def main():
    before=json.loads((HERE/'before_manifest.json').read_text())
    for name,v in before.items():assert hashlib.sha256((REPO/name).read_bytes()).hexdigest()==v['sha256'],name
    data=readrows(REPO/E184/'analysis/dataset_summary.csv')
    points=readrows(REPO/E183/'analysis/final_v1/points.csv')
    def qps(s,m):return float(next(p['qps'] for p in points if p['dataset']==s['dataset'] and p['method']==m and p['K']=='100' and p['L']=='200'))
    failure_table=table(['数据集','K1失败率','K100未满100查询','原未满100查询中净改善','遗漏成员修复率'],[
        [s['label'],f"{float(s['GT_K1_failed_pct']):.2f}%",f"{float(s['GT_K100_incomplete_pct']):.2f}%",
         f"{float(s['K100_improved_incomplete_pct']):.2f}%",f"{float(s['K100_member_repair_pct']):.4f}%"] for s in data])
    perf_table=table(['数据集','GT10 Recall@100 / QPS','B32 Recall@100 / QPS','同L净Recall pp / QPS变化'],[
        [s['label'],f"{float(s['GT_K100_recall_pct']):.4f}% / {qps(s,'GT10-soft-t1' if s['router']=='soft' else 'GT10-hard'):.2f}",
         f"{float(s['B32_K100_recall_pct']):.4f}% / {qps(s,s['router']+'-JOINT32'):.2f}",
         f"+{float(s['K100_net_recall_pp']):.4f} / {float(s['K100_QPS_delta_pct']):+.2f}%"] for s in data])
    docs={}
    docs['summary.md']=f'''# ACSG 当前结论

更新于2026-10-24。**默认保留GT10：WebVid为GT10-soft-t1，Yandex为GT10-hard；共享NSG实现保留E99优化。** 残差补全仍是研究方案，没有替换默认。

最新研究是[E184空间分布与失败修复诊断]({E184}/report_zh.md)；最新正式性能是[E183七集评测]({E183}/analysis/delivery_v2/report_zh.md)。两轮各自已完成，当前没有待恢复的实验队列；长期“可靠Recall–QPS综合改进”目标未因此达成。

## 当前方法和性能判断

GT10用查询画像选择三个真实入口，再执行固定NSG。残差表在主搜索后补算候选并合并，不改变主遍历。E183保留原始L2/raw-IP、真实K1/K100、完整单线程wall，645点/1935批；E184只复算已有56K查询并新增离线几何诊断，没有新ANN、GT、训练或QPS。

- GT10对Deep/SIFT有迁移收益；GIST较弱且有混合结果。
- B32相对自身GT10：WebVid/COCO两K共同Recall区间的既有折线均受益；Flickr交叉，Yandex K100较低；Deep/SIFT K100较低，GIST混合。
- 同L增召回且变慢是补点取舍；不能据此否定完整曲线改善。共同Recall区间的折线描述不等于新增等Recall实测，也不外推未测L。

下面固定L200；Deep/SIFT/Web用soft，其余hard，补全为同家族B32。QPS直接引用E183三轮完整wall中位数，不能与E99/E103等不同核、不同计时批次的绝对速度拼接。

{perf_table}

## 失败与改进比例

{failure_table}

K1失败为实际K1未命中GT1；K100未满100包括只少一个成员。“原失败中净改善”的分母是原未满100查询，“遗漏成员修复率”的分母是原遗漏成员；两者都不等于整条查询已找齐。COCO完整恢复100/100为1402/8532（16.43%），Web为34/9916（0.34%）。主L200损伤0；全已有B32预算的5个边界损伤事件照常保留。

## 残差与空间分布的判断

**空间结构与主搜失败有关，静态残差收益另受遗漏目标重现、路由覆盖和容量保留约束。** 不能概括为多模态天然有效、越小越有效或越聚集越有效。

- Deep/SIFT超过99%的测试遗漏不在当前训练残差源里。固定源即使全取且不计费用，额外Recall上限仅0.0195/0.0140pp；保持当前路由源则为0.0086/0.0062pp。扩大当前表无法补源外目标。
- GIST的10886个遗漏→训练源4242→路由源1117→B32救回66，路由和保留损失明显，不能沿用单一“源外”解释。Yandex训练源覆盖仅7.528%，来源和选择都受限。
- 跨七集，训练残差目标重复倍率与成员修复率Spearmanρ=0.964，原遗漏成员率ρ=0.214。七集规模、metric、特征、图、训练和容量密度未配平；源覆盖还与救回有结构包含关系，相关不是因果证明。
- 数据集内几何分离与遗漏数多数负相关。按原遗漏量粗分层后，Web/COCO高分离组改善概率高8.17/11.50pp，高训练残差频次组高44.69/19.61pp；几何仍有条件关联，粗分层不构成因果调整。GT几何特征尚不能作为免费在线门控。
- E182同源规模对照已显示：固定H的小库优势在密度控制后不再单调；H还改变路由和每hub训练密度，不能归结为纯规模规律。

## 核验、成本与限制

E184成功诊断170.346秒、stdlib set/Counter第二实现4.368秒；56K逐条整数、9项跨集秩相关和14项条件差值核验通过，每集8条query验证8192背景样本的距离矩公式。由同一执行者完成不同实现，不称独立人员审查；首类型错误失败日志保留，失败wall未记录。

E183正式suite18267.58秒（约5.07h），包含内部正式wall、预热和保存核验；不能与1935内部wall再相加。独审407.80秒，历史完整冷启动成本未知。完整费用见[E183账本]({E183}/analysis/cost_ledger.json)与[E184收据]({E184}/analysis/receipt.json)。

单图/单画像、已曝光公共查询、GIST仅1K、8192背景样本、描述性相关及未独立重算的旧bootstrap/插值限制保留。没有新增盲确认、因果干预、默认替换或可靠性能结论。

## 证据与文档入口

[E184详细报告]({E184}/report_zh.md) · [逐集CSV]({E184}/analysis/dataset_summary.csv) · [56K查询CSV]({E184}/analysis/query_metrics.csv) · [覆盖链]({E184}/analysis/coverage_chain.csv) · [第二实现核验]({E184}/analysis/integer_audit.json) · [E183全部645点]({E183}/analysis/final_v1/points.csv) · [E183独审]({E183}/reviews/independent_results_audit.json)。

实现与数据合同见[spec](spec.md)，后续研究问题见[s-target](s-target.md)，历史见[s-experiment](s-experiment.md)。清理前历次“当前/运行中/截止安排”的完整正文已[归档]({ARC}/summary.md)，仅保留历史身份，不作为当前队列。
'''
    docs['spec.md']=f'''# ACSG 代码架构与实现契约

更新于2026-10-24。本文维护当前实现、输入/输出、metric、artifact及计量合同；结论见[summary](summary.md)，下一研究问题见[s-target](s-target.md)。详细历史模块合同已[归档]({ARC}/spec.md)，原实现没有因文档整理被删除或改写。

## 1. 当前主链与实现位置

```text
合法训练query/GT → QGT选择真实base入口H → GT10目标归属 → 单位query画像W
raw query → 画像Micro-HNSW → 三个真实base ID → 原NSG search_new(mode=2) → Top-K
残差研究分支：同一主返回 → 三行冻结posting去重/评分 → Top-K合并
GT只在训练监督或搜索返回后的评测层读取
```

GT10画像为`p_h=normalize(unit(x_h)+Σ_i a_ih unit(q_i))`；a来自训练GT前10个目标与真实hub的hard/soft归属，不是在线神经网络。GT10方法名的10与评测K独立。QGT按簇中query及其GT候选选择全局唯一真实ID，不等于质心GT1或GT全局投票。

| 模块 | 当前源码/配置 | 关键边界 |
| --- | --- | --- |
| 索引/搜索 | [ACSG.cpp](ACSG/ACSG.cpp)、[ACSG.h](ACSG/ACSG.h)、[IndexACSG.cpp](ACSG/IndexACSG.cpp) | 冻结邻接、真实ID、原DistanceComputer、visited与retset |
| 基础Fast构造 | [build_fast_entry_variants.py](benches/run/build_fast_entry_variants.py) | 原GT1画像及QGT分支；不能把旧30K Fast当GT10同训练量控制 |
| GT10画像 | [E24 build_profiles.py](entry_method_exploration/20260910_gt_topk_profiles_v1/src/build_profiles.py)、[E97 L2适配](entry_method_exploration/20260915_gate_l2_r1_r100_v1/src/build_profiles.py) | GT-topK hard/soft、当前W/ID映射以manifest为准 |
| 通用评测 | [test.cpp](benches/test.cpp)、[DataLoader](benches/datasets/DataLoader.hpp) | 选择split/metric；旧命令不自动代表新实验合同 |
| E183实际计时与补全 | [benchmark.cpp]({E183}/src/benchmark.cpp)、[residual_tools.cpp]({E183}/src/residual_tools.cpp)、[configs]({E183}/configs/) | 原scalar主核、真实timed包、后置精确评分合并 |
| E184离线诊断 | [analyze.py]({E184}/analyze.py)、[audit_integers.py]({E184}/audit_integers.py) | 只读旧返回/原向量；无ANN、训练、GT生成或QPS |

旧ACO→DPC→Neural Router、区域搜索、RL、多画像及证书等版本各有自己的历史实现/未实现边界，见[历史索引](s-experiment.md)；不属于当前GT10必需调用链。

## 2. 搜索接口与不变量

`ACSG::search_new(dis, topk, I, D, visited, mode, custom_enterpoints, retset_buf)`：mode0/1/2为原随机/固定权重/自定义入口模式。主结果必须为真实base ID和实际任务距离。

- mode2最多消费输入前三个位置，再用visited去重，重复不补位。调用方验证`0≤id<N`；旧注释不能替代ID检查。
- `search_L`是候选池容量，不是距离计算预算；正式K100要求L≥100。返回retset Top-K，不以其他独立global-topK语义代换。
- HNSW内部slot和base ID必须显式映射；heap-pop与真实ID排序是不同合同，各实验保留其配置。
- 现有`SearchTrace`不是完整可恢复搜索状态，retset/visited也不是pause/resume接口。独立C状态机属于历史工具，不能写成原接口已有能力。
- 画像W为单位向量，路由实现的`1-qᵀW`对固定非零q排名与余弦等价，数值不泛称已归一化余弦。原raw query/base不因路由而额外归一化。
- 主图为带向量的原生二进制时，`.json`后缀不表示JSON。padding −1保留其未用槽意义；原有序邻接/实际kernel身份属于复现输入。

E99共享NSG预取和候选复制优化的合同见[详细卡片](experiment_history/92_nsg_search_optimization.md)。E183沿其冻结的scalar实现，不能与不同优化核的旧绝对QPS拼接。

## 3. 当前七集评测域

| 数据集/key | N × d | metric | E183 H / 测试query | 原入口次序 |
| --- | --- | --- | --- | --- |
| Deep / deep10m_l2_v1 | 10M × 96 | squared L2 | 800 / 10000 | sorted_ids |
| SIFT / sift10m_bigann_l2_v1 | 10M × 128 | squared L2 | 800 / 10000 | sorted_ids |
| GIST / gist1m_l2_v1 | 1M × 960 | squared L2 | 800 / 1000 | sorted_ids |
| WebVid / webvid2_5m_light_v1 | 2505000 × 512 | raw IP | 815 / 10000 | sorted_ids |
| Yandex / yandex_t2i_official10M_ip_v1 | first 10M × 200 | raw IP | 821 / 10000 | sorted_ids |
| COCO / coco | 118272 × 512 | raw IP | 815 / 10000 | heap_pop |
| Flickr / flickr30k | 31782 × 512 | raw IP | 815 / 5000 | heap_pop |

真实base/query/GT、图、W、ID及角色路径以[E183配置]({E183}/configs/)和[dataset catalogue]({E183}/reviews/dataset_catalogue.json)为准，文件名不是身份。Deep/SIFT/GIST已完成接入，旧“未接入/不属正式协议”仅是历史时点。L2不强行归一化成IP；Web源近单位范数也不等于额外归一化；Yandex保持原IP，GT须对应first-10M库。

训练/验证/测试角色不混用。E183五集残差fit可共享原画像fit前16K；COCO/Flickr残差角色独立，须分别披露。已曝光公共测试不是新盲确认。LAION是历史迁移控制：其公共query与Web来源重合，不算独立第三query workload；本地图索引已清理，重放需重建，原数据/证据保留。

## 4. 残差补全合同

E183每个hard/soft家族用合法16K query、K100/L200遗漏生成单位query–GT成员token；保留全局未截断源、hub源、token、B8→32嵌套行。正式仅B8/B32，K1/K100共享同张K100教师表是固定条件，不称各K最优。

每query取三个路由行，B32去重前最多96候选。排除主返回及重复ID后按原metric补算，和同K/L实际GT10主包合并；不启动第二次主搜索，不改visited/展开/停止。候选覆盖与最终救回分别统计，近并列/浮点损伤保留，不能事后改GT。

E176的M5OPT、M5RES12、PAIR/WIDE及E179–182其他表属于独立版本；其容量、训练源、计时核、费用和结果不能借给当前版本。完整历史接口读[旧spec归档]({ARC}/spec.md)并沿卡片找到对应协议。

## 5. 指标、计时与证据

- 新评测仅真实K=1/K=100。Recall@K为GT_K与返回Top-K集合交集除以K；K1必须实际返回首名命中GT1。旧Recall@10不改名复用。
- K100查询失败可定义未满100或少于90，须声明门槛。逐query改善、完整恢复、成员救回/损伤及其分母分开。
- 正式性能统一单方法串行、实际threads=1，OMP/BLAS/MKL/NUMEXPR=1；CPU/亲和性和实际线程进收据。离线多线程另记，不能换算QPS。
- QPS用独立完整batch wall；E183包含正常Batch创建、初始化、路由、主搜、补点、统一六向量复制及正常销毁。加载、GT评分、hash、写盘、oracle和预热在wall外单列。
- E183首轮保存真实timed ID/距离/入口/画像分数，另两轮bits/SHA一致；POST与同K/L实际GT10主包的独立标量/线性合并oracle通过。零NDC布局不是0次距离，`counts_collected=false`。
- 三轮计时不是三份独立质量样本。曲线保留真实L、重复Recall分支；插值只作描述，不外推。独审范围以收据为准，不自动延伸到全部GT、bootstrap或因果。
- E183独审复算645点、1935轮、540救损、360覆盖、2088分层、360级联、3600频次及全部TRAIN源；未独立重算bootstrap、折线和全部实际greedy序列。

## 6. E184诊断artifact

`analysis/query_metrics.csv`和各集NPZ按原query行对齐；含K1/K100 mask、频次和几何，另有覆盖链、四分位、秩相关、原遗漏数分层以及全部已有B32预算敏感性表。

几何按原squared L2/负IP float64重评分原GT100目标；每集PCG64 seed20261024抽8192个base，保存ID/样本向量SHA。背景z为`(背景距离均值−GT100距离)/背景标准差`，不是论文原始relative contrast；有效秩`tr(C)^2/tr(C^2)`来自中心化样本协方差，不是流形内在维数。每集8query直接验证距离矩。整库SHA继承E183，本次只核stat；小输入SHA前后核对。

`audit_integers.py`用stdlib set/Counter复核56K整数，不导入主analyzer/NumPy；`finalize.py`另核9项秩相关/14项条件差值。它们由同一执行者完成，不称独立人员审查。E184交付时的根文档身份和旧验收原件保留；后续文档整理另有[维护收据](experiment_history/_maintenance/20261024_current_state_cleanup_v1/README.md)，不在新布局回跑旧根文档suffix门。

## 7. 构建、来源与重跑依赖

工作区`/data/netg/ACSG`，解释器`.venv_cpu/bin/python`；C++17/本地Faiss CPU依赖。先核当前CMake cache、静态库、对象、源码补丁、编译参数和目标帮助，再配置构建。历史命令/绝对路径不等于可移植运行包，文档清理不触发构建或实验。

| 改变项 | 必须重新绑定或生成的下游 |
| --- | --- |
| base / metric / normalization / 图或kernel | 相应GT、图、模型、响应、计数、计时；具体依赖按是否兼容判定 |
| 训练角色 / GT / H / 画像公式 | hub/画像/小图及其下游响应、表和评测 |
| router图 / 参数 / ID映射 / 次序 | 入口、主返回、依赖其遗漏的表和评测 |
| K / L / 合并或计时边界 | 对应真实搜索结果、费用和比较 |
| 仅兼容汇总、绘图、说明 | 复用原科学数组，只重做派生产物 |

新版本保存协议、源码/配置/输入/模型身份、aligned实际返回、费用和状态；旧失败/修正/封存不回写。source-only、工具验收、质量通过、性能通过和默认替换是不同事实。未测成本写null及原因，嵌套费用不相加；历史冷启动/训练债不清零，旧预算不是新额度。
'''
    docs['s-target.md']=f'''# ACSG 后续研究问题

更新于2026-10-24。持久目标是相对当前默认的**可靠Recall–QPS综合改进**。GT10默认和E99共享核保持；E184诊断、E183性能矩阵均已完成。本次结论同步与文档清理不启动训练、建图、GT、性能或旧runner。

## 当前判断

[E184]({E184}/report_zh.md)将主搜几何难度与残差目标可复用性区分开；Deep/SIFT源外主导，GIST路由/保留损失突出，Web/COCO有较多可复用遗漏，Yandex源覆盖仍低。几何在粗分层后仍有条件关联，不是因果证明或在线预测器。实际数值和完整费用只在[summary](summary.md)维护。

## 优先一：证明未知查询上有可复用的遗漏来源

对Deep/SIFT类，先回答合法训练源能否覆盖未知失败目标，而不是直接扩大现有表。候选输入应来自互斥、可追溯的训练角色；测试query/GT/失败标签不用于选源、调表或定容量。

比较同源简单目标频次/遗漏频次控制，报告训练到独立查询角色的来源覆盖、救损和完整费用。如果固定源乐观质量上限已不足以偿还目标质量差距，停止该源下的扩容解释，不外推所有残差方法无效。

## 优先二：检验路由和容量能否利用已有源

对GIST、Yandex以及Web/COCO的剩余遗漏，区分源内但当前路由未覆盖、路由源内但有限表未保留、候选存在但最终未救回。比较必须同源、同K/L、同实际主图与合理容量/费用控制。

H改变入口层和每hub训练密度，不能把它只当表容量；总槽数、不同目标数、每query候选数、实际救回与Recall分母分别报告。静态表/路由的改变是新方法版本，不能借旧返回相加模拟收益。

## 优先三：检验几何是否提供额外、可部署的信息

在固定来源和简单频次控制下，先在未参与选择的query角色检验几何是否仍有额外解释力；区分“query容易失败”与“补全相对默认有净收益”。GT100分离度属于离线诊断，不直接进入线上决策。

若形成只依赖线上可见信息的规则，推理、检索、访存、去重、补算和输出都计入完整wall；用真实K1/K100和声明工作区间的曲线判断。几何更好、目标更集中、NDC更少或离线更省都不能替代Recall–QPS证据。

## 进入与退出条件

新工作先固定问题、来源/角色、方法与最强简单控制、K/L、计量、资源和结束边界。方法/数据角色冻结后，完成输出/来源核验和完整单线程串行比较，报告效应量、救损、质量不确定性及运行波动；相关场景的新来源复核与实际取舍支持默认替换。

未知或未证明非劣不等于已证明有害；局部信号可以保留，但不逐批加样本/seed/容量直到通过。历史预算、期限、STOP和源码准入只约束各自版本，不恢复为当前队列，也不替代新范围的实际成本和来源核对。

当前没有在执行的后续研究计划。上述三项是待检验的问题，没有新增模型、门控、确认集或性能结论。范数敏感路由等旧提案仍为[理论归档](entry_method_exploration/20261011_norm_aware_profile_theory_v1/theory.md)，不能写成现有能力。

## 历史目标与接续

旧阶段的08:00/13:00/16:00/22:00截止、E172运行/挂起措辞和旧CAL/confirm前件全文见[归档]({ARC}/s-target.md)，保留原时点，不是今天的工作队列。

<a id="2026-10-03-新对话接续入口"></a>

2026-10-03的历史交接入口已移至[当时全文]({ARC}/s-target.md#2026-10-03-新对话接续入口)。本锚点只兼容旧链接；当前接续一律从[LOCAL_CODEX_START.md](LOCAL_CODEX_START.md)开始。
'''
    latest=[
        ('184_residual_geometry_diagnosis_v1.md','E184','空间分布与失败修复','离线诊断完成；七集56K，无新性能，默认不变'),
        ('183_gt10_residual_comprehensive_v1.md','E183','七集GT10与残差综合评测','645点/1935完整T1；最新正式性能，默认不变'),
        ('182_m5_scale_control_v1.md','E182','同源规模与容量密度','216点单轮；固定H小库优势在密度控制后不再单调'),
        ('181_m5_multimodal_transfer_v1.md','E181','COCO/Flickr独立迁移','120点单轮；COCO受益、Flickr K100交叉'),
        ('180_m5_k100_capacity_v1.md','E180','K100来源与嵌套扩容','扩容有质量收益；曲线解释以E181修正及E183新矩阵为准'),
        ('179_m5_k100_objective_v1.md','E179','同16K目标对齐','小幅Recall收益，没有稳定QPS增益'),
        ('178_profile_routing_risk.md','E178','画像路由风险','局部小L选择失配；范数匹配影响有限，未替换默认'),
        ('177_entry_representation_quick.md','E177','真实入口/代表query表示','有限测试无可靠默认替换依据'),
        ('176_m5_residual_completion_curve_v1.md','E176','M5工程省费与剩余遗漏补全','对M5OPT无严格双升；速度和残差质量贡献分开'),
        ('175_m5_region_budget_curve_v1.md','E175','区域补全五L曲线','Recall多升但同L全慢，未新增双升预算组合'),
        ('174_m5_residual_regions.md','E174','一跳区域补全','独立版本完成；不把邻域几何机会当净收益'),
        ('173_nsg_gt_m5_public_test_retest.md','E173','原M5公开测试','历史60点/180批已完成；不是当前正在执行'),
        ('172_all_methods_experiment_campaign.md','E172','五方法及三联动旧阶段','保留未完成范围和来源/成本记录，不作为当前恢复队列'),
        ('171_overnight_algorithm_collision_and_certificates.md','E171','五机制理论与DOCX联动','理论阶段已完成；不把提案当已实现或新性能'),
        ('92_nsg_search_optimization.md','E99','共享NSG实现优化','保留当前共享核优化；旧绝对QPS不能拼入E183')]
    for name,_,_,_ in latest:assert (REPO/'experiment_history'/name).exists(),name
    docs['s-experiment.md']=f'''# ACSG 实验与研究索引

更新于2026-10-24。最新研究是E184离线诊断；最新正式性能是E183。当前判断只读[summary](summary.md)，实现合同读[spec](spec.md)，后续问题读[s-target](s-target.md)。历史卡片里的“当前/待执行”仅指原记录时点。

## 最近研究与当前依赖

'''+table(['记录','主题','状态与一句话判断','详细复盘'],[[eid,topic,state,f'[卡片](experiment_history/{name})'] for name,eid,topic,state in latest])+f'''

## 完整历史与理论

[全部详细卡片](experiment_history/README.md)按文件原编号索引；早期卡片编号和正文实验E编号不一定相同，不按文件名前缀擅自重编号。

旧的多视角/注意力、probe-reroute、A+B、RL、多画像、有限beam及证书路线均保留其原协议、失败、修正和证据。理论文稿、SOURCE_ONLY、工具准备/验收与正式实验不是同一状态。

[范数敏感画像路由理论](entry_method_exploration/20261011_norm_aware_profile_theory_v1/theory.md)仍为THEORY_ONLY_UNIMPLEMENTED_UNTESTED；不能因有文档或源码审查就称性能通过。

查旧方法时从卡片进入协议、配置、state/gate、结果和修正，证据不足写未知。旧进程状态、期限和恢复命令已从当前入口移出，完整旧索引[归档]({ARC}/s-experiment.md)供复核。
'''
    docs['LOCAL_CODEX_START.md']=f'''# ACSG 当前接续入口

更新于2026-10-24；仓库`/data/netg/ACSG`，分支`research/state-20261002`，基底HEAD `96cf05d5410cf51272048cd1f90b4bb194e23c62`。E174–184及本次整理为本地工作；HEAD不能冒称包含这些未提交产物，也不把旧远端快照当当前工作区。

## 先读什么

1. [AGENTS.md](AGENTS.md)：协作、文档职责、数据/性能/历史保护约定。
2. [summary.md](summary.md)：唯一当前结论、实际Recall/QPS和证据限制。
3. [spec.md](spec.md)：当前实现、七集metric、数据/计时/复现合同。
4. [s-target.md](s-target.md)：后续三个研究问题及进入/退出条件。
5. [s-experiment.md](s-experiment.md)与[历史目录](experiment_history/README.md)：讨论旧方案时再沿卡片回原证据。
6. [E184报告]({E184}/report_zh.md)、[状态]({E184}/state.json)、[整数核验]({E184}/analysis/integer_audit.json)；涉及性能再读[E183报告]({E183}/analysis/delivery_v2/report_zh.md)、[645点]({E183}/analysis/final_v1/points.csv)及[独审]({E183}/reviews/independent_results_audit.json)。

## 当前结论与边界

默认GT10保持：Web软t1/Y硬，E99共享NSG核保持。E184复算七集56K已有查询，区分几何难度、遗漏目标重现、路由与容量；是离线关联诊断，无新ANN/GT/训练/QPS。E183仍为最新性能，Web/COCO残差曲线受益，Flickr/GIST混合，Deep/SIFT及Yandex K100收益不足以统一替换默认。

当前没有待恢复实验队列。历史期限、训练额度、挂起进程、CAL/confirm门和旧runner只属于对应记录；接续先核当前状态，不自动运行。GT几何特征不能充当免费线上信息，已曝光测试不是新盲确认。

## 可复制的只读接续提示词

```text
在/data/netg/ACSG接续研究。先只读核git branch与HEAD，再依LOCAL_CODEX_START.md阅读AGENTS和四主文档。请报告当前默认、最新E184诊断、E183实测Recall/QPS、费用、证据限制及尚未实施的下一问题。讨论旧方案时沿s-experiment进入原卡片/协议/结果。保留旧科学字节与角色；本次只读理解，不训练、构图、生成GT、恢复runner、重测性能或修改默认。
```

2026-10-24整理前的旧交接全文见[归档]({ARC}/LOCAL_CODEX_START.md)；科学产物仍在原目录，大向量/图/静态库/teacher响应不因Git文件齐全就可移植复跑。
'''
    docs['readme.md']=f'''# ACSG：GT10入口路由与残差补全研究

更新于2026-10-24。**当前默认是GT10**：由训练目标构造查询画像，Micro-HNSW选择三个真实base入口，再搜索固定NSG；WebVid为soft-t1，Yandex为hard。原ACO→DPC→Neural Router属于历史路线，不是当前默认流水线。

[开始阅读](LOCAL_CODEX_START.md) · [当前结论](summary.md) · [实现合同](spec.md) · [后续问题](s-target.md) · [历史索引](s-experiment.md)。

## 最新研究

- [E184：残差与空间分布/失败修复]({E184}/report_zh.md)。七集56K已有查询的离线诊断：几何难度与残差可复用性需要分开，不能单归因多模态或库规模；无新性能，默认不变。
- [E183：七集完整性能]({E183}/analysis/delivery_v2/report_zh.md)。645点/1935完整单线程批次；WebVid/COCO的残差曲线受益，其余数据按范围判断。[简版PDF]({E183}/analysis/concise_v1/NETG_E183_NSG_GT10_残差_简版报告_20261018.pdf) · [645点CSV]({E183}/analysis/final_v1/points.csv)。

残差补全在固定主返回后查冻结posting、去重、按原metric评分合并，不改变主图遍历；它仍为研究方案。所有当前数字、费用和限制以summary及实际协议/审计为准。

## 实现与复现

核心代码在[ACSG](ACSG/)，评测/数据配置在[benches](benches/)，隔离研究在[entry_method_exploration](entry_method_exploration/)。使用本地CPU依赖和`.venv_cpu`，具体输入、源码、kernel和计时边界读[spec](spec.md)。旧绝对路径或一键命令不代表新实验已授权/可重跑；当前没有待恢复队列。

文档清理前的旧NETG介绍、构建/ACO命令、论文作图说明已[归档]({ARC}/readme.md)。历史结果、源码和大资产保持原位；这次整理没有训练、性能重测、Git提交或发布。
'''
    # Keep the established collaboration rules, and make current-vs-history maintenance explicit.
    agents=(REPO/'AGENTS.md').read_text()
    agents=agents.replace('历史完整版本留快照，不在spec/summary中不断累积流水账。',
        '历史完整版本留快照，不在spec/summary中不断累积流水账；当前结论采用单一现行版本，过期“最新/运行中/截止安排”移入带日期的历史归档。')
    docs['AGENTS.md']=agents+f'''
## 文档整理与文件清理（2026-10-24）

四根文档各维护一份现行视图，不再以持续前插“CURRENT”块堆积互相矛盾的状态。详细历史读s-experiment/experiment_history；旧根报告原路径可保留短跳转，归档全文应明确历史时点。维护修改另留快照和收据，不回写旧实验seal、manifest或当时验收结果。

用户明确要求清理时，先核引用/manifest/封存/Git和实际用途。已确认无引用且可由保留源码重建的临时缓存可清理；纳入旧manifest的缓存亦按证据保留。当前源码、模型、数据/GT/图、实际返回、计时、失败日志及历史原件不因“旧”而自动删除。此次维护记录见[清理说明](experiment_history/_maintenance/20261024_current_state_cleanup_v1/README.md)。
'''
    # All detailed cards stay at the same paths; file numbers are card IDs, not inferred E IDs.
    cards=sorted([p for p in (REPO/'experiment_history').glob('*.md') if re.match(r'^\d+[a-z]?_',p.name)],
        key=lambda p:(int(re.match(r'\d+',p.name).group()),p.name),reverse=True)
    cardrows=[]
    for p in cards:
        first=next((l.lstrip('# ').strip() for l in p.read_text().splitlines() if l.startswith('# ')),p.stem)
        cardrows.append([f'[{p.name}]({p.name})',first.replace('|','\\|')])
    docs['experiment_history/README.md']='''# ACSG 详细实验与研究记录

更新于2026-10-24。最新诊断是[E184](184_residual_geometry_diagnosis_v1.md)，最新正式性能是[E183](183_gt10_residual_comprehensive_v1.md)。当前结论见[summary](../summary.md)，简要索引见[s-experiment](../s-experiment.md)。

下面按原卡片文件号排序，保留全部详细记录和原路径。早期卡片号与正文E编号不一定相同，不将它们重新编号。卡片中的“当前/最新/运行中/待执行”是历史原文，不代表当前队列；状态、范围和修正要沿原协议/结果复核。

## 全部详细卡片

'''+table(['原卡片文件','原题（历史）'],cardrows)+'''

## 维护与归档

[2026-10-24结论同步与文档清理](_maintenance/20261024_current_state_cleanup_v1/README.md)保存清理前完整根文档、可读历史副本、引用检查和文件清单。旧数据、模型、图、失败记录及科学manifest仍在原处；维护收据不修改实验结论。
'''
    for name in ['实验总结.md','总结.md','研究方向.md','advisor_progress_report.md','recent_ten_days_report_20260911.local.md',
                 'finite_beam_reachability_goal.md','aco_router_fast_entry.md','command.md']:
        docs[name]=f'''# 历史文档入口：{name}

本文原稿已于2026-10-24归档至[历史全文]({ARC}/{name})，保留原结果、措辞、命令和时点；本路径仅用于兼容旧链接。

当前项目结论见[summary.md](summary.md)，方法/复现合同见[spec.md](spec.md)，后续问题见[s-target.md](s-target.md)。新会话从[LOCAL_CODEX_START.md](LOCAL_CODEX_START.md)开始；原稿中的“当前/待执行/下一步”不代表现行状态。
'''
    for name,body in docs.items():put(REPO/name,body)
    changes={name:{'before_bytes':before[name]['bytes'],'after_bytes':(REPO/name).stat().st_size,
                   'before_lines':before[name]['lines'],'after_lines':len((REPO/name).read_text().splitlines())} for name in docs}
    (HERE/'document_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'rewritten_documents':len(docs),'detailed_cards_preserved':len(cards),
        'four_root_bytes_before':sum(before[n]['bytes'] for n in ['summary.md','spec.md','s-target.md','s-experiment.md']),
        'four_root_bytes_after':sum((REPO/n).stat().st_size for n in ['summary.md','spec.md','s-target.md','s-experiment.md'])},ensure_ascii=False))

if __name__=='__main__':main()

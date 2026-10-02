# 119｜E117四动作入口集合试验

2026-09-20，用户“试试”授权的独立试验。`STOP_ENTRY_SET_PILOT`，条件完整预算扩测未启动，原Web GT10-soft-t1 / Yandex GT10-hard与生产E99保持。只选主搜索开始前的真实入口集合；主搜索、底图、画像、小图、raw-IP、L及停止规则未改。

## 机制、数据和查重边界

一次原GT10 HNSW取相同top3，按实际画像距离/真实ID确定rank。四动作：原三入口、仅rank1、仅rank2、仅rank3。六特征为画像/真实入口分数间隔及raw-IP最优者的画像rank；额外3次真实入口点积计费。CostTree固定最大深度2、叶≥512，以等K召回差−0.1×相对时间差训练；RecallTree只含召回，ShuffledTree固定seed打乱完整四动作标签。共6次树拟合，无梯度网络、超参数/候选/seed网格。

共享排名特征、实际reward、小评分器和成本目标已有E15/E16/E36/E85先例。本版具体范围是同次实际top3、1/3入口四动作、实际K1/K100和完整成本，并非论文新颖性证明。原E116 ID绑定试验未重启。

每集E24 fit20K前10000条拟合、最后4096条接受，源行[10000:20000] / [25904:30000]，字节互斥。原画像曾使用这些query，所有源均历史开发曝光，接受仅不参与本版选择器拟合。两集模型冻结后才打开接受载荷；E105的4096批与未曝光held-out均不进入本版。

训练L128/K100四真实动作标签，首返回作K1标签且由实际K1/链接原核验收；时间按256-query块轮换五变体、四重复，包含路由及特征。接受八方法×双K×双集32点/96轮完整wall，实际K1/K100分别调用、CPU15/线程1、串行、warmup+3plain+count。Feature3专门量化特征开销，不冒充免费特征。

## 结果

CostTree相对匹配GT10：

| 数据/K | GT10 Recall→CostTree | ΔRecall pp | ΔQPS | 零命中救回/新增 |
|---|---|---:|---:|---:|
| Web/1 | 75.5127%→75.5615% | +0.048828 | −0.272% | 21/19 |
| Web/100 | 65.9097%→65.8899% | −0.019775 | −0.147% | 1/0 |
| Yandex/1 | 90.6982%→90.6494% | −0.048828 | +0.137% | 29/31 |
| Yandex/100 | 83.5886%→83.4565% | −0.132080 | −0.319% | 8/12 |

四个98.75%配对Recall区间均跨0。K1失败数Web1003→1001、Y381→383；K100零命中Web4→3、Y27→31。K100净成员数−81/−541，不能只看零命中改善。

fit固定最强动作为Web GT10、Y Single1。CostTree对Y Single1 R1/R100为−0.244141/−0.170410pp，QPS−0.195/−0.672%；等K增量−0.207275pp、98.75%区间[−0.460571,+0.052491]。主质量均值/正区间/完整QPS三项门均失败，仅“不低于打乱标签平均质量”通过。Web两棵真实标签树选择相同动作；Y成本项改变选择并比RecallTree速度均值更高，但未产生质量速度联合收益。

固定Single1在接受侧四项Recall均值都比GT10和CostTree高，但对GT10四区间也跨0、Web K100 QPS−0.708%，不据此改默认。学习不能只修复多入口退化，也必须超过强简单控制。

实际ANN四动作免费oracle的R1空间对GT10为Web3.5400/Y2.4170pp，对接受侧最强固定动作3.3691/2.2217pp；K100对应1.7175/1.5588pp和1.6958/1.5205pp。两个K分别oracle、查看GT且选择免费，不是一个可部署策略同时实现的增量。低成本初始化特征与固定浅树未把该空间转成可靠净收益，不外推所有入口选择不可学习。

## 成本、核验和接续

1,159,856次NSG、1,215,200次路由、2,275,680次额外特征点积。控制器561.12秒（9.35分钟），编译两次共18.74秒单列，6次树拟合3.22秒，采样最大RSS约9.922GiB；独立核验约1.17秒。新文件约225MB，0新GT/大小图/梯度网络/未曝光held-out，编译与完整实现复盘耗时不冒充线上QPS。

训练/plain/count/原E99返回及实际K1前缀、全接受默认E116恢复、学习策略完整动作返回、Python/C++动作、六特征独立算术/采样原向量、源行/字节互斥、独立GT评分/损伤、单线程/调用账本/源码模型冻结与原件保护均通过。kernel逐字继承，生产ACSG.cpp未改；大base/NSG用继承SHA来源及当前stat，不冒称本次全图hash。所有任务终止，无待运行阶段。

停止本版，不增加深度/候选/λ/阈值/seed，不按接受失败query定向修复。保留全部正负与默认；完整预算扩测未执行，不能将一个L称正式完整前沿。

[报告](../entry_method_exploration/20260920_entry_set_pilot_v1/report.md) · [冻结协议](../entry_method_exploration/20260920_entry_set_pilot_v1/protocol.md) · [配置](../entry_method_exploration/20260920_entry_set_pilot_v1/config.locked.json) · [模型冻结](../entry_method_exploration/20260920_entry_set_pilot_v1/reviews/models_frozen.json) · [32点指标](../entry_method_exploration/20260920_entry_set_pilot_v1/results/metrics.json) · [全部配对](../entry_method_exploration/20260920_entry_set_pilot_v1/results/paired.csv) · [主门](../entry_method_exploration/20260920_entry_set_pilot_v1/results/gate.json) · [独立审计](../entry_method_exploration/20260920_entry_set_pilot_v1/reviews/independent_numeric_audit.json) · [账本](../entry_method_exploration/20260920_entry_set_pilot_v1/reviews/cost_ledger.json) · [状态](../entry_method_exploration/20260920_entry_set_pilot_v1/state.json)。

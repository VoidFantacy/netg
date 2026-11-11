# ACSG 当前接续入口

更新于2026-10-28；仓库`/data/netg/ACSG`，分支`research/state-20261002`，基底HEAD `96cf05d5410cf51272048cd1f90b4bb194e23c62`。E174–187为本地未提交工作，HEAD不包含这些完整产物。当前没有待恢复的实验矩阵，默认GT10不变。

## 阅读顺序

1. [AGENTS.md](AGENTS.md)：数据/单线程/文档职责及历史保护。
2. [summary.md](summary.md)、[spec.md](spec.md)、[s-target.md](s-target.md)、[s-experiment.md](s-experiment.md)。
3. [E187实验报告](entry_method_exploration/20261028_adaptive_completion_pilot_v1/report_zh.md)、[六页图表PDF](entry_method_exploration/20261028_adaptive_completion_pilot_v1/ACSG_自适应残差补全_实验对比_20261028.pdf)、[52点](entry_method_exploration/20261028_adaptive_completion_pilot_v1/analysis/points.csv)、[离散预算对照](entry_method_exploration/20261028_adaptive_completion_pilot_v1/analysis/discrete_comparisons.csv)、[核验](entry_method_exploration/20261028_adaptive_completion_pilot_v1/reviews/results_audit.json)。
4. 涉及几何看E185/E184原报告；七集两K性能看E183。旧方案从历史索引进卡片、原协议、结果与修正。

## 当前边界

本轮区域补全尚未建立可支付的Recall–QPS提升，保留GT10默认，停止该固定后端进入动作选择器。 区域补全18点中，18点被本轮某个实测L的GT10在Recall和中位QPS两项同时覆盖；达到事前速度筛选的点0个，达到预算筛选的点0个。 E187仅两集K100曝光数据pilot；全base新来源已实现，完整动作接口/逐query开关尚未实现，未验证K1/其余五集，无新盲确认或默认替换。E186原件仍保留当时理论身份。

失败严格是单query Recall@100<10%，即0–9命中，成员修复与尾部改善/脱离分开。新来源源外可达不等于费用可支付；下一步若继续须新协议降访问成本，不能在旧test上改模型到通过。几何关联不作流形因果或净收益准入器。

## 只读接续提示词

```text
在/data/netg/ACSG接续。先只读核branch与HEAD，再依LOCAL_CODEX_START.md读AGENTS和四主文档。报告GT10默认、E187两集K100真实Recall/QPS与更大L预算对照、源外救回与成本、R相对Q的作用、严格<10%尾部及证据范围。说明E186哪些部分已实现、哪些仍未实现；七集两K仍读E183，几何读E185/E184。旧方法沿卡片到原协议与结果，不改历史，不训练、不恢复runner、不调参或重测，除非当前用户另行授权。
```

修改前入口见[E187快照](entry_method_exploration/20261028_adaptive_completion_pilot_v1/source_before/LOCAL_CODEX_START.md)。原大资产、静态库、对象和数据/图并不因Git文件齐全就可移植复跑。

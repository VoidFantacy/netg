<!-- E183_CURRENT_BEGIN -->
# 当前接续：E183 七集综合测试与详细PDF完成（2026-10-17）

最新完成E183：七集（含Deep/SIFT/GIST原L2）、645点/1935完整T1批次；[32页详细PDF](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/NETG_E183_GT10与残差_七数据集及失败查询_详细报告_20261017.pdf)、[中文报告](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)、[详细复盘](experiment_history/183_gt10_residual_comprehensive_v1.md)、[状态](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/state.json)。GT10在Deep/SIFT可迁移；B32在这两集收益很小、K100曲线较低；GIST混合。Web/COCO补全曲线受益，Flickr交叉、Yandex K100较低。默认仍E99 GT10，有限矩阵完成，无待恢复队列。先读AGENTS与四根文档顶部E183，再读报告/审计；不要启动旧runner。

基底HEAD仍96cf05d5410cf51272048cd1f90b4bb194e23c62、research/state-20261002；E183是本地新产物，未提交/发布。旧结果和失败收据完整保留。
2026-10-18 简版交付：[四页PDF](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/concise_v1/NETG_E183_NSG_GT10_残差_简版报告_20261018.pdf) · [简版文字](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/concise_v1/report_zh.md)。每图仅NSG、GT10、GT10＋残差三线，另有统一L200失败查询表；315点全部复用既有结果，固定同家族B32，无新增实验，详细版保留。
<!-- E183_CURRENT_END -->

# 本地 Codex 接续入口（2026-10-11）

持久目标：**可靠的 Recall–QPS 综合改进**。当前默认仍是 E99 GT10：WebVid `GT10-soft-t1`、Yandex `GT10-hard`；原 M5 保留。E176 有限尝试已完成并停止，尚不足以替换默认。

目标仓库为 `VoidFantacy/netg`，发布分支 `research/state-20261002`，发布父提交为 `84dc95730818a750e72a425bd0f96a25e3604ffb`。编写此入口时，服务器工作区 `git rev-parse HEAD` 实测为 `96cf05d5410cf51272048cd1f90b4bb194e23c62`。新发布提交尚未生成；接续时以实际 checkout 的 HEAD 和发布收据核实身份，不能把上述两种身份混为一谈。

在本地仓库根目录先执行只读命令：

```bash
git branch --show-current
git rev-parse HEAD
```

按顺序阅读：

1. [AGENTS.md](AGENTS.md)
2. [summary.md](summary.md)：当前结论；顶部 E176 块优先于保留的旧状态。
3. [spec.md](spec.md)：实现、输入域、计时与复跑合同。
4. [s-target.md](s-target.md)：目标、停止和后续授权边界。
5. [s-experiment.md](s-experiment.md)：历史索引。
6. [E176 详细复盘](experiment_history/176_m5_residual_completion_curve_v1.md)；浏览用 [相对链接副本](research_snapshots/20261011_e176/portable/experiment_176.md)。
7. [E176 原 README](entry_method_exploration/20261010_m5_residual_completion_curve_v1/README.md)，再由 [快照入口](research_snapshots/20261011_e176/README.md) 读审计、结果和图。

E176 为两集各已曝光公共10K，K1/K100、五档 L、八方法，160点/480批次；没有新确认集。M5RES12 对原 M5 的同 L 严格双升为点 QPS 中位数口径 **8/20**，冻结配对比率 primary 为 **9/20**；对 M5OPT 为 **0/20**，PAIR 对 WIDE12 为 **0/20**。工程省费与补全质量贡献须分开，不从曲线连线推断未测 L。

仓库中的代码、汇总图表和审计可直接阅读。科学原件保留服务器绝对路径身份；浏览副本仅改链接。复跑还依赖外部 base/query/GT、图、静态库和 teacher responses，见 [外部资产与迁移边界](research_snapshots/20261011_e176/external_assets.md)。不要直接启动带服务器路径的旧 runner。

可复制给本地 Codex 的初始提示词：

```text
我在 VoidFantacy/netg 的 research/state-20261002 接续 ACSG。持久目标是可靠的 Recall/QPS 双提升。先只读执行 git branch --show-current 与 git rev-parse HEAD，核对实际仓库身份；依 LOCAL_CODEX_START.md 的顺序读 AGENTS、四份根文档、E176 历史与 README、协议/锁、审计、结果和曲线。

请先报告当前默认、E176 的实际 Recall/QPS 证据、费用、停止结论和局限。保留 GT10 默认与原 M5，区分点中位数双升8/20和配对 primary9/20，以及对M5OPT/对WIDE均0/20。公共10K已曝光、没有新确认。

这次接续只授权只读核实和报告，不自动执行实验、训练、距离/GT计算、恢复旧队列、修改默认或历史文件。E176 每数据集额外900秒FIT授权已用于历史尝试，实际Web469.14秒/Y472.99秒；它不是本地新训练额度。若讨论下一步，先给有证据边界的研究方案；复跑须另核外部资产迁移、域/metric/角色一致性及新的执行授权。
```

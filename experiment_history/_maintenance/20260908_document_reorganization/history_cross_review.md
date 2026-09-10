# 历史索引与 04/05/06 交叉复核

复核日期：2026-09-08。范围为 `s-experiment.md`、`experiment_history/04_utility_and_representation.md`、`05_probe_reroute.md`、`06_finite_beam_and_atlas.md`，另核新版 `spec.md` 的工具环境路径。复核者未撰写上述三张卡。仅读取当前 Markdown、小型 JSON report/decision 和相关脚本片段；未打开原始 query/GT/base/图、NPZ/trace 大数组，没有构建、训练、ANN 或新统计实验。

**最终结论：PASS，指定范围内无未解决的实质或阻断问题。** 三张卡都有动机、实现、split/预算、数值结果、成本/未知项、版本状态和原件链接，不是链接桩。初次交叉阅读提出的两项文档精度补充及主维护者指出的 modes 训练范围歧义，已按授权直接修复于04；初阅证据与建议保留在下文，最终修复记录见第4节。

## 1. 关键误读项检查

| 检查项 | 现场原始证据 | 对索引/详细卡的判断 |
|---|---|---|
| utility residual 是否被抹成跨数据失败 | `utility_residual_entry_results/webvid_train10k_top32_l64_128_r10_a025_c005_t1_v1_validation10k/validation_10k_top3_3run.json`：validation10K、3 runs，K10/L64/128/200/400 分别 +0.110/+0.077/+0.114/+0.085 pp，graph NDC 均微降 | PASS。E09 和 04 明确 WebVid 局部微正、缺 Yandex/独立构建/完整成本，不写跨数据失败或方法 GO。原 JSON 另有 K100/L64 无效行，本轮核验只取有效 K10 行 |
| finite-beam v1 终态更正 | `finite_beam_reachability_diagnostics/v1_audit/analysis.md` 明确拒绝旧 `NO_GO_TRACE_NOT_INCREMENTAL`，改为 `NO_GO_NOT_LIGHTWEIGHT` / `TRACE_INCREMENTAL_PASS_COST_ALIGNMENT_FAIL_COMPRESSION_UNTESTED`；四项增量 utility CI 下界正，三项成本 gate 失败，收益集中性亦失败 | PASS。E15、易误读条目及 06 均采用更正，保留原 v1，不将 trace 信息与轻量部署混为一谈 |
| Atlas/v2 是否误否定一般可学习性 | `v2_distillation/decision.json` 的四个 utility CI 均跨 0，Recall/成本条件通过，terminal 为 `NO_GO_NOT_PREDICTABLE` | PASS。E16/06 将失败限制为 64-NN、局部支持、1 SE、top8、复用400-query audit 的具体机制，不否定任意重教师/轻学生 |
| probe 隐藏 L16/32 成本 | `probe_reroute_results/analysis.md` 明确旧 L10/16/32 trace 却只计 L10 的版本不能支持预算 claim；双数据 `l10_only_gain01_v2/report.json` 的 `used_probe_Ls=[10]` | PASS。E13 与 05 明确旧预算口径无效，检测 signal 与改道选择及完整在线成本分别记录 |
| probe 的监督是否被误写为 single/仅几何 | 原 analysis 与最终 `webvid_probe10_top32_topology_v4` 明确 merged Recall + probe/second-search NDC、trace/frontier/topology | PASS。E14/05 记录了已有真实 merged utility 监督、两阶段重新搜索及结果合并；没有冒充原位 resumable state |
| 最终 probe Yandex 是否被误记已跑 | 原 analysis 记最终 topology chooser WebVid gate 失败，Yandex extension 未运行；Yandex detector/budget oracle 是此前独立结果 | PASS。05 显式区分两者 |
| BTG 是否遗漏 v2/v3/v4 或把修订当独立重复 | 逐读 `btg_falsification_v1` 至 `v4/analysis.md` 及四份小型 report.json；四版均 NO-GO，v3/v4 的主 gate 为 per-dataset train-tuned | 核心 PASS。04 包含全部版本入口与最终 shared/per-dataset 表，明确不是独立重复；建议 2 补充中间版本的具体变化 |
| modes 是否区分 v1/v2 anchored | 两份 design 与全部 v1 eval、四份 v2 eval；v1 primary score fallback 不保留 entry anchor，v2 才强制 rank0 | 核心 PASS。04 明確机制差别及底层 Fast primary 用过30K的历史，未虚称整模型对前10K完全隔离；建议 1 补表格 split |

## 2. 初阅提出的两项文档精度补充（已落实）

### 建议 1：给 modes 表显式标注 validation10K，并补 train gate 的阶段衔接

04 第5节先同时介绍 train 与 validation，随后表内 v1 的 WebVid +0.172/+0.072 pp、Yandex +0.032/−0.003 pp，以及 anchored 的 +0.176/+0.085、+0.017/−0.017 pp，均来自 **validation10K**。数值正确，但表头没有显式标 split，容易被读成前述 train gate 的结果。

建议表标题或首句写“以下为 validation10K”。可补一行 train10K 的阶段记录：v1 WebVid +0.216/+0.159 pp、Yandex +0.143/+0.095 pp；v2 anchored WebVid +0.229/+0.167 pp、Yandex +0.122/+0.075 pp（L64/128）。这些 train Recall 均为正，区别于随后 validation 的 Yandex L128 微负。它们是同一原型/模型上的阶段结果，不是额外独立 build，也不单独证明所有 gate 条件通过。

核对来源：`target_basin_mode_diagnostics/v1/eval/{webvid,yandex}_{train,validation}10k.json`，及 `v2_anchored/{webvid,yandex}_{train,validation}_eval.json`。本轮只读这些约2KB的均值结果，未读取原始路由数组。

### 建议 2：给 BTG 补短版本表，避免 v2/v3 的修正只剩链接

04 已有完整主方法、最终结果与各版链接，所以不是整体链接桩；但中间演进目前只写“诊断规则/门槛演进”。逐份 report 可明确补为：

| 版本 | 原 report 可支持的差别 |
|---|---|
| v1 | 共享配置 h1/temp0.5/gamma0.5/margin0.1；WebVid ΔU+0.001896，Yandex−0.001343，跨数据失败 |
| v2 | 新增显式 shared minimax 选择规则：先最大化两训练dev中最小 utility 增益，再均值、较低 NDC/改道率；选 h4/temp0.25/gamma0.1/margin0，两个 validation ΔU 均微负 |
| v3 | 主 gate 改为每数据集各自 train-only 选择的配置；shared 是更严格的迁移诊断。WebVid个别调参 PASS、Yandex FAIL，最终仍 NO-GO |
| v4 | 本轮递归比对 v3/v4 小型 report，数值、配置、decision 与 routes SHA 相同；差别为 analysis_script SHA、版本输出路径与 wall。不能描述为新的性能改善或第四次独立重复 |

四份 report 的 `framework_version` 仍写 `btg_falsification_v1`，因此目录版号、原 analysis、implementation SHA 与具体 gate 要一起识别，不宜只用这个沿用字段抹掉 v2–v4。旧文件保留，不建议在整理轮回写修正它们。

## 3. 路径、完整性与未扩展范围

- 对总索引、三张卡和新版 spec 的全部 Markdown 本地链接做存在性检查：无缺失目标。
- 新版 spec 明确工具根为 `hierarchical_target_search/20260907_v1/tools/`，两环境链接均为完整项目相对路径；现场确认 `env.sh` 和 `roargraph-env.sh` 实际存在。根目录短路径 `tools/env.sh`/`tools/roargraph-env.sh` 不存在，没有误写为可用入口。
- spec 保留核心 `.venv_cpu` 与基线/MKL/OpenMP 隔离，不把依赖 smoke 升级为方法 PASS；与历史03一致。
- 三张卡明确 oracle 免费事后选择、graph NDC 与端到端成本、重复 timing 与独立 build 的区别。未发现给旧失败分支恢复执行权限的语句；历史 source 的“下一步”均有范围限定。
- 本轮没有重新证明旧训练/验证原始输入完整性、重新生成 bootstrap 或遍历大 trace/GT 数组；核查结论限于现存小型报告、配置及脚本所能支持的历史内容。对于准备迁移的正文，这已覆盖所指定关键状态和版本风险。

主索引 E08 的“单centroid未给出有效改进”可酌情改成“有局部同L Recall提升，但未证同成本/跨数据收益”，与 04 的 +0.35～+0.82 pp 正值更直接一致。这是措辞精度建议，不改变既有停止结论。

## 4. 授权修复与最终复核

主维护者随后明确授权直接补充04，其余根文件不改。已完成：

1. modes 表前显式注明 validation10K，并加入 v1/v2 的两数据集 train10K 正点，避免混淆 train gate 与 validation 微负结果。
2. 将“残差/modes 的 fit 与前10K不相交”限定为本节 target-basin modes 的后20K fit；显式排除第4节 utility residual，后者用前10K标签。基础 Fast primary 用过30K的限制保留。
3. BTG 增补 v1–v4 简短版本表、v3/v4数值/路由SHA一致和沿用 framework_version 的识别限制。没有修改原报告、配置、路由或原始数据。

修复后的04仅增加历史说明；上述核定数值、停止状态、split使用历史及测量边界均保持。再次检查04与本复核报告的格式及04全部本地 Markdown 链接，无缺失目标。其余根文件没有由本复核者修改；E08建议已交主维护者判断。最终状态 PASS。

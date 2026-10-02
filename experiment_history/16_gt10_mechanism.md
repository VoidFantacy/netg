# 16｜GT10收益机制分析与限定补测

2026-09-11，E27。状态`GT10_MECHANISM_ANALYSIS_COMPLETE_WITH_BOUNDED_DIAGNOSTICS`。按用户指定的GT10 hard对matched GT1 hard，先完成已有证据A–C，再为明确缺口冻结小协议并完成D。E24/E25/E26原资产和状态保留，2A/3A/聚类/rank等方法分支未启动。

## 对象、输入和已核对机制

两数据集原fit20K、base/raw-IP/NSG、QGT seed20260828、H815/821、三个唯一真实入口固定。重建GT1/GT10 hard及cal冻结GT1/GT10 soft归属，核对原digest/support/W，连接每rank目标、画像、实际入口、GT10 mask、route/graph NDC和独立wall。

GT10每query总质量仍1，将unit(query)分给不同目标所归属的hub；平均不同hub数WebVid5.993、Yandex4.571，离开GT1的质量71.844%/58.447%。mass中位近似不变，ESS中位16→67.361、22→60.082；query方向集中度0.727→0.703、0.643→0.616，画像角位移中位11.66°/11.19°。它同时改变目标信息和支持/平滑，不能只把ESS当原因。

WebVid补齐的13个原零支持hub没有成为validation新增入口；Yandex原本没有零支持hub。实际换三入口78.10%/63.65%，却只有少数query改变命中数。同实际三入口的ID/距离bits/hits/mask/graph NDC全相同，五L入口不变。WebVid任一L获益/受损query144/128、兼有29；Yandex50/50、兼有8。所有query和正负L保留，不按效果筛分母。

## 质量、近似后端与重复速度

GT10−GT1 hard五L Recall pp：WebVid+0.285/−0.085/−0.115/−0.110/+0.040；Yandex+0.120/+0.335/+0.035/+0.080/+0.060。Fast相对NSG的既有贡献另列，不全归给GT10。E25/E26的Yandex A1是hard，WebVid A1是soft；不能混作同画像重复。

本轮只补WebVid两硬画像历史validation2K五L，各三次独立warm/plain。QPS中位比值+1.360%/+0.890%/+0.583%/+0.484%/+0.339%，15个对应轮次差均正；原E24部分约3%幅度未保留。质量曲线与E24七字段逐位相同，中间三个L仍有质量损失。Yandex L128旧+2.563%速度在E25/E26变为−0.184%/+0.038%，没有稳定的原幅度速度证据；其+0.335pp命中变化仍保留。

旧cal/audit exact/HNSW全部复核后，只补两个原正点的exact3：WebVid validation L64的GT10−GT1为exact +0.435pp（+87命中），HNSW +0.285pp（+57）；Yandex L128为exact +0.310pp（+62），HNSW +0.335pp（+67）。两点去除近似仍保留收益，后端交互−0.150/+0.025pp；不外推其它L，不称画像exact3为搜索效用oracle。两点按已有正信号选作事后机制诊断，不是盲验证。

## 对应关系与平滑控制

每数据集一个固定tail_shuffle，PCG64 seed20260911第一份排列（0固定点）：保留0.1 GT1项，第2–10名归属整组从donor query搬来。每rank全局hub频次、每hub总质量、每query总质量保留；ESS、GT1/tail重合和画像方向不匹配。只测原cal/audit L128 exact/HNSW，不进入validation候选或模型选择。

真实GT10−shuffle的四点pp为WebVid+0.273/+0.205/+0.566/+0.664，Yandex+0.859/+0.215/+0.186/−0.049（cal HNSW/exact、audit HNSW/exact）。shuffle ESS更高77.358/70.251，7/8质量却较低，支持query–真实目标对应关系值得保留；但八个差区间均跨0，shuffle位移又更大，不能完成独立因果份额分解。WebVid shuffle cal仍优于GT1，所以一般混合也可有局部作用。

## 搜索成本和剩余缺口

WebVid graph NDC五L减少1.191%/0.725%/0.499%/0.290%/0.115%，route NDC128.549→118.317。L128独立总wall466.300→462.185μs，route-only6.964→6.597、graph-only450.165→446.603；分项不相加。路由约占总wall1.49%，不支持把主要速度变化归于Micro-HNSW。

按全query分母分摊WebVid L64 graph NDC变化，获益组+0.9305、持平组−6.3785、受损组−5.5765。部分少算来自受损事件，不能称有效query都更省。Yandex L128总graph NDC反而+0.539，旧速度幅度也未复现；没有扩展路径长度/cache硬件证据。

Yandex L128获益组的GT目标hub入口覆盖反而降低，受损组却升高，说明几何覆盖不等于有限L三入口作用。支持/角位移/重合度分层跨段不稳定，与E25规则迁移不足及E26插值不保离散效用相容；其75%/25%增强门槛不用于否定原GT10。

建议保留query相关分数归属、质量1、GT1/GT10 hard与原冻结soft对照；画像几何与真实finite-L三入口作用的差距仍是研究问题。尚未证明2A可学习，没有自动开启标签、模型或其它队列。

## 执行、资源与原始证据

已有分析108点169152输出独立评分，新增搜索0。补测30点36448输出独立评分，9个job一次成功；真实调用181376（恢复640、shuffle16512、局部exact16064、重复140160及分项8000），修复0、合成0。查询进程总242.491s，峰值约9.918GiB，CPU15/实际线程1；进程时间含加载/count/I/O，不能换QPS。原GT/QGT/NSG从零成本未新测。

GT1 manifest schema差异引起新分析器首轮读取错误，日志保留；修正读取后通过，没有真实调用或旧资产改动。5634个E24/E25/E26文件登记并核验保护。所有开发/validation有历史使用；held-out未读取/hash/评测。

- [完整报告](../entry_method_exploration/20260911_gt10_mechanism_v1/report.md)、[已有A–C](../entry_method_exploration/20260911_gt10_mechanism_v1/existing_report.md)、[完整表](../entry_method_exploration/20260911_gt10_mechanism_v1/results/tables.md)。
- [已有阶段协议](../entry_method_exploration/20260911_gt10_mechanism_v1/protocol.md)、[补测协议](../entry_method_exploration/20260911_gt10_mechanism_v1/supplement/protocol.md)、[配置预算](../entry_method_exploration/20260911_gt10_mechanism_v1/supplement/config.locked.json)、[状态](../entry_method_exploration/20260911_gt10_mechanism_v1/state.json)。
- [已有分析](../entry_method_exploration/20260911_gt10_mechanism_v1/results/existing_evidence.json)、[补测分析](../entry_method_exploration/20260911_gt10_mechanism_v1/supplement/results/analysis.json)、[成本](../entry_method_exploration/20260911_gt10_mechanism_v1/supplement/reviews/execution_complete.json)、[最终验收](../entry_method_exploration/20260911_gt10_mechanism_v1/reviews/final_audit.json)。

本轮完成后收口；下一分支由用户明确指定，统一见[s-target](../s-target.md)。

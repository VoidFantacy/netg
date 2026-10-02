# 102｜E107 表示与入口数的系统因素对照

2026-09-20完成，状态COMPLETE_INITIALIZATION_FACTORIAL；用户16:00活动目标继续。本轮区分GT10相对固定NSG的整体收益、query画像与多入口，E106及旧模型不重训。结果需要修正原先解释：原单位hub的query自适应路由已获得大部分均值收益，不能把全部系统增益归于GT10画像。

原H、NSG、raw-IP、E105各4096已曝光query/GT固定，UnitHub/GT1/默认GT10三表示×1/3入口，加固定NSG单入口与默认ANN；K1五L64/128/256/400/800，K100四L128/256/400/800，共144点。Web GT10 soft对GT1 hard还包含软归属变化，Yandex均hard。原H选取本身用QGT/GT，单位hub不是完全无监督方法。全H exact及缓存路由无新在线QPS。

L128单位hub单入口对固定NSG，Web R1/R100 +4.5898/+1.3228pp、Yandex +1.3672/+1.0408pp；当前默认ANN为+4.2725/+1.3127pp、+1.6113/+1.2871pp。默认ANN质量/零命中为Web75.3174%/65.5408%、1011/5，Y90.6250%/83.7917%、384/24。Web单位hub3对GT1画像3在全9点均值更高；Yandex画像作用混合。GT10相对GT1未形成完整稳定增量。

单位hub1→3的18点均值全正；GT10为17负/1正，仅1个描述性区间排除0，点间共用query且预算相关。GT10 L128的K1救回/损害为Web58/67、Y28/40；K100实际GT成员新增/丢失4903/5117、2897/3513。原内核五节点强连通反例也核验：新增更近入口可挤出有用分支，因此没有一般单调保证；不证明真实NSG普遍出现该五节点结构。

实际1181184 NSG、16448原ANN路由，另2次合成；搜索约1203.26秒、总编排1221.61秒、独立分析30.53秒。0新GT/图/训练/K10/QPS。CPU15/线程1/串行，前16行与原E99一致，全4096行count/plain及对应E105/E106控制恢复；同L K1为K100首返回且距离bits/NDC一致。144指标、270配对、36交互、两个PNG/PDF全部保留。

默认与生产E99保持，E103仍是最新完整五集前沿。下一步先补单位hub普通小图/同seed GT10重建控制与匹配完整wall，不由精确路由宣布GO；理论学习草案须先检查完美代理信息的实际作用。论文度量/可导航假设不套用到当前raw-IP有限beam。

[完整报告](../entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/report.md) · [配对](../entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/results/paired.csv) · [协议](../entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/protocol.md) · [解释口径](../entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/reviews/interpretation_notes.md) · [状态](../entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/state.json)。

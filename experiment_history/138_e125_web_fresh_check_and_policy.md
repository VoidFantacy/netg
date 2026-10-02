# 138 E125冻结模型Web新查询单点复测与判定策略修订

2026-09-22用户要求简单复测，并明确调整旧门一票否决。模型/教师/画像/小图不改，另冻Web K1/L1000、4096新源query、三次完整wall和单点95%描述区间；无新候选实验号。

GT10-soft-t1命中3719/4096、R1=90.795898%、QPS419.559；ApproxTarget10命中3713、R1=90.649414%、QPS419.121。救回6/损伤12、差−0.146484pp，95%区间[−0.341797,+0.048828]，QPS−0.104439%、三次范围重叠。旧批3/7、−0.097656pp；两批均小幅为负，不能称无损，但也不因单区间未过而取消有费用价值的候选。

当前决策RETAIN_LOW_COST_CANDIDATE，默认不替换。原E125标签64.591/28.040秒相对原exact20K312.862/1417.293秒的成本信号保留；资源/阶段不同，不称同资源加速。旧协议、原98.75%门和STOP历史不回改；新策略已写AGENTS、s-target及独立策略文件。

新源窗口[2470000,2490000)，与全部登记split、E105整个20K候选窗口及原20K拟合输入字节互斥；源顺序取样，不是全源随机/语义独立声明。新4096 exactGT、8条独立float64全库检查；40992 NSG、40960 ANN，无训练/图。CPU15实际1线程，全部warm/plain/count一致、32个E99返回/计数核验。8192输出独立重评分、卷积复核bootstrap、37源/模型身份通过。

补充原28条增损只读核验：新18/旧10均无重复向量或数值容差内同分，最小GT分数差0.001242/0.001094；不是ID同分造成的小差异，评分不变。

首次taskset启动前监控过早断言导致0搜索退出，原脚本/日志保留；只修监控exec时序后成功。查询作业102.656秒，GT79.113秒；准备、GT、编译、查询成功作业合计190.532秒。固定单组结束，无追加到通过的循环。

证据：[报告](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_web_fresh_check_v1/report.md) · [独立核验](../entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_web_fresh_check_v1/reviews/independent_audit.json) · [研究策略](../entry_method_exploration/20260922_until2200_improvement_v1/research_decision_policy.md)。

补充事后只读对齐：新Web1150条更换三入口集合，仅21条K1返回ID改变；旧Web/Y为1111/875条换集合、13/27条改返回。全部12288行独立set/list复核，无新搜索或选择规则。不代表相同搜索轨迹或全H已无空间。[核验](../entry_method_exploration/20260922_until2200_improvement_v1/reviews/routing_robustness_summary.json)。

# E64 查询启动绑核修正与一次修复预留

首次WebVid启动，父控制器CPU8立即检查taskset子进程，taskset尚未exec evaluator时观察到继承CPU8而触发停止。子进程已kill+wait返回−9，native日志0字节，results目录没有文件，未生成query/config/thread_contract/timing记录，未进入evaluator main。实际搜索0；原111440 NSG完整预留保留。原run/log/jobs不覆盖。

独立run_v2.py在Popen的preexec_fn中先设置CPU15，再exec同SHA evaluator，Popen返回时已经绑核；原生自身依旧核验CPU15和线程1，控制器持续核验。相同候选、输入、诊断门、计时、二进制、预算与截止规则不变。没有新反馈可用于方法改动。

本次人为审查后的单次实现修复额外预留111440，正常222880，合计334320，修复后硬cap350000；失败旧预留不释放，后续再次失败停止本stage不再扩cap。analyse_v2只汇总两个实际完成job，同时报告失败预留、真实调用与修复。此次不构成参数/数据/方法网格扩张。

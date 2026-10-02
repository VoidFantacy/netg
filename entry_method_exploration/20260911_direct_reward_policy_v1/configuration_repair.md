# 首次fit启动的零查询配置修正

首次WebVid fit在创建第二个Policy时退出：生成配置将当前默认画像写为不存在的`gt10_soft/W.f32`，正确身份是E30已采用的`gt10_soft_t1/W.f32`。修正依据为E30 `validation_webvid2_5m_light_v1/results.json`中`model_name=gt10_soft,L=64`的完整配置，不重新选温度。

失败输出、旧配置、旧控制器和日志全部保留。原evaluate.cpp先构造全部Policy，再进入plain/count/原kernel循环；失败发生在第二个Policy读取W的初始化阶段，输出只有首个基线HNSW建图及输入/线程文件，无timing_progress、逐点返回或GT评分。因此本次失败已核实实际NSG调用为0；消耗约5秒进程wall和一次基线建图，均记入离线成本。它不是搜索中途失败或查询部分执行。

原控制器在启动前保守预留160064次调用，本修正新增显式的“加载模型前失败且可证明0次NSG”记账例外：保留gross reserved_calls=160064及FAILED状态，并单独标注verified_actual_calls=0、charged_calls=0。只有此已核实的零查询失败释放预留；其余失败仍按完整预留计费。正常矩阵799568与实际调用硬cap800000均不增加，失败wall仍计入90分钟上限。此资源记账例外在重试和任何新检索结果产生前写入，不能用于丢弃已执行的搜索或性能结果。

新`deployment_common_v2.py`仅修正默认模型来源、启动前完整检查W/mapping/tie_ids/候选画像、失败预留释放例外及独立`fit_v2`输出路径；复用原已冻结的evaluate二进制、模型、C8策略、候选/slot全量parity和全部收益门。新`run_deployment_v2.py`不覆盖旧fit目录；后续仍完整执行原比较矩阵，正式wall/线程/门槛不变。

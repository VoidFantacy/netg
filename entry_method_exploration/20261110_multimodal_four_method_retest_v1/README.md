# E200 多模态四方法加密重测

2026-11-10，完整640点/1280正式单线程批次/1120万查询已完成；每点两遍、每K20档L。COCO/Flickr30k/WebVid/Yandex完整测试角色，NSG/GT10/GT10＋直接残差/GATE，真实K1/K100。原生与独立数值核验、实际图形审阅完成，默认E99 GT10保持。

结果：COCO/WebVid直接残差有明确收益，Flickr按质量目标取舍，Yandex优先GT10。GATE160点均被同矩阵其他方法覆盖；结论限于冻结模型/图/预算和已曝光查询。详细实际Recall、完整QPS、负例、尾部与费用读[中文报告](analysis/final_v1/report_zh.md)。

- [Recall@1曲线](analysis/final_v1/figures/recall_qps_k1.png)、[SVG](analysis/final_v1/figures/recall_qps_k1.svg)；[Recall@100曲线](analysis/final_v1/figures/recall_qps_k100.png)、[SVG](analysis/final_v1/figures/recall_qps_k100.svg)。
- [640点CSV](analysis/final_v1/points.csv)、[1280轮计时](analysis/final_v1/rounds.csv)、[480组配对](analysis/final_v1/paired.csv)、[门槛](analysis/final_v1/targets.csv)、[覆盖关系](analysis/final_v1/frontier.csv)、[派生证据](analysis/final_v1/report_evidence.json)。
- [协议](protocol.md)、[固定矩阵](config.locked.json)、[101项冻结文件](formal_freeze.json)、[配置](configs/)、[源码](src/)。
- [测量完成](reviews/measurement_complete.json)、[64点资格](reviews/qualification.json)、[独立核验](analysis/final_v1/independent_audit.json)、[复核与交付收据目录](reviews/)。最终完整交付收据为reviews/delivery_validation.json；阶段pending字段保留当时身份，当前状态读[state](state.json)。
- [正式进程/压缩费用](reviews/formal_process_costs.json)、[新GATE准备费用](reviews/gate_preparation_costs.json)、[训练重启恢复证据](reviews/recovery_boot1/)、[最初根文档](source_before/)、[最终更新前快照](reviews/root_before_final/)。

主QPS为两次N/wall算术平均，另存平均wall与合并QPS；CPU15实际T1、原scalar核、完整输出生命周期。首轮实际包保留，第二轮逐字/SHA相同；2560个payload按gzip无损压缩且往返核验。无PDF。继承构建费用非零，Flickr中断未提交费用未知；不将主机停机时间当训练费用。

自动阶段脚本finish_pipeline.py已结束。重放或复查先读协议、冻结身份与实际state；不要根据旧PID或历史“测量中”段落重启已完成计时。旧科学产物、模型、图、GT和seal保持。

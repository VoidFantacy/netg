# E200 多模态四方法加密重测

2026-11-10，用户授权测试NSG、GT10、GT10＋直接残差、GATE；每点两遍平均，比以前增加预算点。

当前任务未完成，阶段和进程身份以[state.json](state.json)、[pipeline.json](pipeline.json)及实际/proc活性为准。不要因观察超时或旧状态文件重复启动进程。

固定范围：COCO/Flickr30k/WebVid/Yandex完整测试集，真实K1/K100，每K20档L，640点、1280完整单线程批次。GT10沿Web软/其余hard，残差沿完整16K/B32；GATE是E97修正标签的外部入口基线，COCO/Flickr按原流程补建缺失模型。默认保持。

- [冻结协议](protocol.md)、[固定矩阵](config.locked.json)、[配置目录](configs/)。
- [GATE准备入口](scripts/prepare_missing_gate.py)、[资格与历史回归](scripts/qualify.py)、[正式串行计时及无损归档](scripts/run_suite.py)。
- [主分析](scripts/analyze.py)、[独立stdlib核验](scripts/audit.py)、[阶段接续](scripts/finish_pipeline.py)。
- [修改前根文档](source_before/)、[原实现来源](reviews/source_origins.json)、[新编译收据](bin/build_benchmark.json)。

主表QPS使用两次N/wall的算术平均，另存两次wall、平均wall和合并QPS。全部费用沿完整输出生命周期；保存首轮实际返回并逐字节核第二轮，压缩在计时外串行，逐文件SHA往返核验。正式结果不与旧绝对QPS拼接。最终交付文字、CSV、PNG/SVG；用户未要求PDF。

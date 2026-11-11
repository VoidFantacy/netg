# E200：四多模态集NSG/GT10/直接残差/GATE加密重测

2026-11-10完成。用户要求每点两次平均、增加预算点、沿既有口径比较。完整执行COCO/Flickr30k/WebVid/Yandex、四方法、真实K1/K100、各20档L，640点/1280批次/1120万查询；公开测试分别10000/5000/10000/10000条。只用新完整wall，默认E99 GT10保持。

GT10固定WebVid soft-t1及其余hard，残差完整16K/B32加返回等价工程优化。四方法共用原scalar主核与原raw-IP/base/图，CPU15实际T1，计时包括正常Batch分配/路由/搜索/补点/六数组复制销毁。QPS为两次N/wall算术平均，原wall、平均wall与合并QPS另存。GATE为E97外部入口基线，非E199残差门。

COCO/Flickr GATE沿原标签/拓扑/训练流程补建；合法residual前10K训练、随后1024 monitor，与测试向量/身份组分离，但与完整B32监督重叠，原GT10监督规模亦不同。Web/Y模型复用。Flickr训练主机重启后从完整epoch7模型/优化器/RNG接续epoch8，最终最佳W未变；全部正式计时在恢复之后，未提交训练费用未知，日志和检查点保留。

结果：COCO K1残差L200的99.1200% / 2423.64优于GT10 L320的98.8800% / 1695.32（+42.96% QPS）；K100残差L200为96.7159% / 2397.12，对GT10 L256的96.6528% / 2038.59（+17.59%）。WebVid K1残差L640为91.1300% / 526.47，对GT10 L800的90.7500% / 427.63（+23.11%）；K100残差L960为90.0171% / 352.85，对GT10 L1120的89.9997% / 305.80（+15.39%）。都是离散实际点，不是严格等Recall比较。

Flickr95%门槛残差对GT10的K1/K100提速24.61%/5.07%，K100在90%/99%门槛反而慢5.89%/1.95%。Yandex已达到的预定门槛均GT10更快，残差L200的K1/K100仅增0.1400/0.0570pp并增完整耗时1.64%/2.35%。GATE160点均被同期其他方法覆盖。不能把有限网格未覆盖点数当整体胜率；公开测试已曝光、两遍波动非置信区间、方法训练量不同。

L200严格低召回NSG→GT10→残差为COCO0→1→1、Flickr0→0→0、Web142→53→46、Yandex174→86→85；GATE0/0/112/126。残差不是普遍尾部修复。160个残差点159个Recall提高、1个持平，无逐查询命中数下降，但两个查询跨L共4个正确成员替换事件均99→99，原GT与事件保持。

费用：正式wall总13723.78s；八个原生进程总14037.69s；归档78.95s；完整run_suite命令14240.44s，均有包含关系，不重复求和。新GATE准备已记录下界2079.17s，不含未知未提交中断费用；继承资产历史成本未清零。

验证：64资格点（48旧E183包、16旧E97 GATE）通过；640点两轮bits/SHA及全量残差merge oracle通过；stdlib另核640点、1280轮、480配对、96门槛、640覆盖行和2560个gzip payload。101项冻结输入正式前后完整SHA一致。两PNG实际查看，SVG32条曲线各20标记；独审是同执行者不同实现。旧科学文件/模型/seal保持，根文档另留快照。未生成PDF、未恢复旧残差门/导航或修改默认。

[报告](../entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/report_zh.md) · [全部点](../entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/points.csv) · [两轮](../entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/rounds.csv) · [协议](../entry_method_exploration/20261110_multimodal_four_method_retest_v1/protocol.md) · [独立核验](../entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/independent_audit.json) · [工作目录与验收](../entry_method_exploration/20261110_multimodal_four_method_retest_v1/README.md)。

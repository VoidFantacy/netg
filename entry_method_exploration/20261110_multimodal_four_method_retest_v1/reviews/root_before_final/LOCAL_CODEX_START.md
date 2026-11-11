# ACSG 当前接续入口

2026-11-10，工作区/data/netg/ACSG，HEAD96cf05d5410cf51272048cd1f90b4bb194e23c62。用户新授权E200：四多模态集NSG、GT10、GT10＋直接残差、外部GATE入口基线，真实K1/K100，各20档L，每点两遍取平均。640点/1280批次，COCO/Flickr GATE已补建、四集64个资格点和全部历史返回回归通过，正式矩阵正在串行测量；实时阶段和PID读[state](entry_method_exploration/20261110_multimodal_four_method_retest_v1/state.json)，固定范围读[协议](entry_method_exploration/20261110_multimodal_four_method_retest_v1/protocol.md)。不能凭本文旧状态启动第二个进程，应先核对应PID/日志。

默认E99 GT10保持；本轮使用原scalar核、完整测试角色，GT10固定Web软/其余hard、完整16K/B32表。旧残差学习选点/精排导航/门控的停止边界保持；本轮GATE是E97外部入口方法，不是恢复E199残差门。

先读AGENTS、summary、spec、s-target、s-experiment，再读本轮协议、config.locked.json和实时state。E199是前一完成实验；旧报告入口见[8页综合版](reports/20261105_method_benefits_limits_v3/README.md)。旧根文档原字节在[E200 source_before](entry_method_exploration/20261110_multimodal_four_method_retest_v1/source_before/)，旧科学原件与seal保持。

后续论文/汇报先读[论文写作约定](论文写作约定.md)：入口不够好→GT10；好入口后仍有遗漏→直接残差补点；训练GT/测试评测/线上未知答案分开，完整费用解释旧方案取舍。

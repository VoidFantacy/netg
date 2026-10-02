import pathlib
R=pathlib.Path('/data/netg/ACSG');base='entry_method_exploration/20260916_nsg_search_optimization_v1'
common=f'E99进行中（2026-09-16）：已按用户要求先提交Git备份`2739b09a`（分支`backup/pre-nsg-optimization-20260916_103846`），随后实现共享NSG邻居预取和保持等距顺序的候选池复制优化。合成差分与ASan/UBSan通过；正在冻结执行WebVid四个Recall@1/100预算点的新旧内核同进程对照，以及Yandex/Deep/SIFT/GIST完整公开query的一致性回归。[协议]({base}/protocol.md) · [实时状态]({base}/state.json)。'
texts={
 'summary.md':common+' 全矩阵尚未完成，不将局部计时写成最终收益；E97/E98结果及旧库保留。',
 's-target.md':common+' 本轮已获用户授权，不需再次确认。完成后逐位复核返回/入口/NDC、画图分析并同步文档；不扩LAION、Recall@10、新训练/构图或网格。入口模型默认保持。',
 'spec.md':common+f' 生产实现位于`ACSG/ACSG.cpp`与`ACSG/detail/CandidatePool.h`；不改API/对象布局/原距离计算。可独立链接的新库为`{base}/bin/libACSG.optimized.a`，原`build/ACSG/libACSG.a`不覆盖。候选定位保留完整L，只缩短有效前缀复制；非有限/sentinel分数回退原复制长度。',
 's-experiment.md':common+' 详细复盘待全部结果验收后写入历史92。'
}
for name,text in texts.items():
 p=R/name;s=p.read_text();assert 'E99进行中' not in s;s=s.replace('\n\n','\n\n'+text+'\n\n',1);p.write_text(s)

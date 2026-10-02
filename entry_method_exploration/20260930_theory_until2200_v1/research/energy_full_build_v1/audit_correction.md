# 距离bit审计边界修正

原audit.py保持不变。首轮四份原生路由已通过且消费2048 ANN，随后Python在pilot距离bit与旧20K文件比较时失败。diagnose_gt_tail.py对全部4条差异query进行独立float64全库top100检查，顺序与ID完全相同；最大新旧分数差8.94e−8，全部落在旧最后32条短尾批。当前每批256，旧同形状2048构建的pilot距离全部逐位恢复。Y无距离差异。

audit_v2.py只对已逐条核验的短尾分数差作显式披露，仍要求全部ID、其他距离bits、特征／树／预测／选行／V/W、图和原生plain-count核验；没有重构候选或重跑原生ANN。费用与原批规则不变。不能再写全部GT距离无条件逐位相同。first audit原生分段wall未保存，不补造总审计wall。

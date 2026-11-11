# E185：流形相关局部几何与残差遗漏共享

2026-10-24，用户要求具体检查流形关系，完成固定离线诊断。继承E183七集/K100/L200/固定家族B32；每集512条，共3584条，另对原56K几何统计做双因素分层。无新ANN/GT/训练/QPS，默认GT10保持。

测量GT20/50/100目标集合局部PCA参与秩（不是流形维数），以及最近合法训练query与随机/入口重合数匹配对照的GT共享和遗漏共享。COCO最近训练GT100重合42.00% vs匹配18.29%，遗漏覆盖10.51% vs2.61%；Web/Flickr也较明显。COCO局部GT100秩27.59，不比SIFT19.69/Deep22.86更低，跨集不支持简单低维优势。局部连续性关联与维数规律必须分开。

原命中段与训练残差频次四分位分层后，COCO高背景分离度组改善概率仍高12.04pp，Web1.09pp；局部秩效果方向混合。粗分层非因果，频次可能是中介；七集规模/metric/图/训练与容量密度未配平。最近训练GT重合与成员修复率跨七集ρ=0.964，不是普遍准入规则。所有GT特征属于事后诊断，不提供新数据集净收益保证。

成功wall123.540秒；第一尝试排除最近训练query后遇匹配单例失败，代码/日志/空输出保留，失败wall未知。修正仅在单例层保留自身（各集2–9条，差值0），没有改样本或模型。第二份stdlib集合/秩/分层核对3584配对、10752集合、168相关/126分层差；主进程14 Gram/SVD与56全16K直接距离检查通过。同作者不同实现，bootstrap未第二实现复算。无新性能或默认替换。

后续问题是局部训练覆盖/邻域共享能否预测未知query在同等完整费用下的收益，尚未实现准入器或线上门控。原严格Recall<10%全L报告保留其口径，不能被本轮广义遗漏关联替代。诊断收口，无待恢复矩阵。

[完整报告](../entry_method_exploration/20261024_manifold_residual_probe_v1/report_zh.md) · [协议](../entry_method_exploration/20261024_manifold_residual_probe_v1/protocol.md) · [两页PDF](../entry_method_exploration/20261024_manifold_residual_probe_v1/ACSG_流形相关几何与残差_诊断图_20261024.pdf) · [逐集结果](../entry_method_exploration/20261024_manifold_residual_probe_v1/analysis/dataset_summary.csv) · [核验](../entry_method_exploration/20261024_manifold_residual_probe_v1/analysis/audit.json) · [收据](../entry_method_exploration/20261024_manifold_residual_probe_v1/analysis/receipt.json)。

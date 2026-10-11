# E176 固定交付入口

已完成160点/480批次/800比较/60机制记录及独立审计。默认仍为GT10；原M5保留。

先读 [E176判定与方法归因](/data/netg/ACSG/experiment_history/176_m5_residual_completion_curve_v1.md)；完整原件见 [冻结报告](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/report.md)。

相对原M5的点中位QPS口径双升8/20（配对原端点9/20）；公平成本基础M5OPT下双升0/20。WebVidK100五点组合收益可见；winner条件化未优于route-only版本，未建立新可靠替换。

[主曲线PNG](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/recall_qps_budget_curves.png) · [主曲线SVG](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/recall_qps_budget_curves.svg) · [机制曲线](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/mechanism_budget_curves.png) · [全部点](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/points.csv) · [全部800解释](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/interpretation.csv) · [费用账](/data/netg/ACSG/entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/cost_ledger_supplement.md)。

source/model身份见execution_lock.json、fit_execution_lock.json、parameter_lock.json；实际状态见run_state.json、fit_state.json；行政schema修正单列reviews/analysis_schema_correction_v2.json。原冻结sources/results/report/figures均保留，交付renderer与补充解释不改方法或科学端点。

两集都用已曝光public_test10K，非新确认。全部新工作限于本次批准的额外900秒/数据集FIT及冻结矩阵；E176有限版本完成后停止，不自动启动新拟合/搜索或历史队列。最终交付状态与资源复核见state.json和reviews/final_delivery_review.json。

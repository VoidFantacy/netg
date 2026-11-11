# 七集失败率、救回率与残差作用：六页图表PDF

2026-10-24。[打开PDF](ACSG_失败率_救回率与残差作用_20261024.pdf)。横向A4、可缩放矢量图，已对实际PDF渲染页面检查。

| 页 | 内容 | 主要口径 |
| --- | --- | --- |
| 1 | NSG、GT10、GT10＋残差的失败率 | K1未命中GT1；K100未满100；分母均为全部query |
| 2 | GT10与残差的救回率、完整修复与成员补回 | 分别对原NSG/原GT10失败；逐query改善不等于100/100 |
| 3 | 残差在线流程与遗漏分区 | 源外、路由未覆盖、有限表未保留、实际救回 |
| 4 | 净Recall增量、完整QPS费用与实际数值 | 统一K100/L200；pp与百分比、对数轴均标明 |
| 5 | 七集全部K100预算曲线 | NSG/GT10/B32共147既有点；三轮QPS范围，真实L顺序 |
| 6 | 空间分布与目标重现的关联 | 训练残差重复、背景分离度；描述性关联，非因果证明 |

固定展示继承E183简版：Deep/SIFT/WebVid用soft，其余hard，残差统一同家族B32；同一数据集不按L切换赢家。前四页固定L200；第5页保留全部已有K100预算。测试query共56,000，GIST仅1,000。

数据来自[E183实际结果](../../entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/final_v1/)和[E184离线诊断](../../entry_method_exploration/20261024_residual_geometry_diagnosis_v1/report_zh.md)。本次只重排与画图，没有新ANN、GT、训练、计时、独立确认或默认变化。E183/E184原科学文件与封存收据未修改。

[图表数据CSV](chart_data.csv) · [L200原比较行](L200_source_comparisons.csv) · [147曲线点](K100_measured_curves.csv) · [输入身份](inputs_manifest.json) · [绘图检查](build_checks.json) · [实际PDF渲染](pdf_render_receipt.json) · [最终核验](delivery_validation.json)。单页PNG/SVG在figures/，实际PDF截图在review_pages/。

`build_pdf.py`为只读CSV的绘图器；`render_review.py`使用临时目录中的PyMuPDF渲染实际PDF；`verify_pdf.py`以另一份stdlib计算核对图表数字。交付后拒绝覆盖PDF，后续修订应另建版本；旧根文档副本仅用于记录本次加入PDF入口前的状态。

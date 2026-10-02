# ACSG 9月13日交付入口

**尚未找到稳定优于当前GT10起点的新方法，默认保持。** 最终对照已完整完成：两个数据集各2000查询、五L五轮、50原点/250整批wall，包含原NSG、Fast、当前GT10起点和实际新方法。

- [中文报告与四组图](../session13_report_v1/report.md)：QPS–Recall、QPS–失败率、按L三指标、双向失败案例。
- [六页PDF](../session13_report_v1/report.pdf)：监督208已在实际Chrome PDF查看器逐页查看全部六页，完整中文正文与图表通过。
- [离线交互报告](../session13_report_v1/report.html)：全部50原点及401失败query的10730个完整五L方法单元，支持查询和CSV下载；监督205/206已覆盖桌面、手机、全部交互与真实下载。
- [原始最终报告](../stage35_final_comparison_v1/report.md)、[50点CSV](../stage35_final_comparison_v1/analysis_v1/points.csv)、[250轮wall](../stage35_final_comparison_v1/analysis_v1/timings.csv)、[完整失败查询CSV](../stage35_final_comparison_v1/supplement_v1/failed_queries_all_L.csv)。

Web组合相对compact五L均修复部分召回损失并减少零命中；相对匹配GT10-soft P，五L召回仍低。Yandex compact低L局部正、高L损伤。五轮QPS范围未支持稳定整体加速。失败严格为零GT10命中，命中一个不失败；减少失败不保证总Recall提高。

完整在线路由、原NSG和输出纳入单线程独立wall，CPU15，GT/count/hash/JSON/build/load在外。E94的700800 NSG/560000 HNSW、994.213秒操作与695.047秒纯wall分开；当天累计6854176 NSG/17820080 HNSW/360普通小图构建不变。完整离线训练及GT总成本仍有未知项。

P-fit包含旧train/monitor，aux/cal/audit均历史使用，动作接受反馈算训练。最终对照使用E34历史validation2000，模型选择先冻结，最终反馈未回流，held-out未开。局部支持稀疏与查询间增损/并图交互不能推出共享表示无解，详见[机制说明](../session13_report_v1/mechanism_note.md)。

第14会话仅核验交付及同步接续，新增训练/ANN/构图/GT/QPS均0。原报告和封存保持；PDF验收为继承监督208的实际证据，本会话未重启浏览器。整日21:00目标仍未由本会话标完成，最终交付/会话退出由监督者接续。[当前安全交接](../handoff_session14.md)。

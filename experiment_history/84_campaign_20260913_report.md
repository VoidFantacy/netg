# 84｜9月13日整日汇报整理（第13会话，非新增实验）

E60–E94 的整日接续以已冻结的 E94 最终矩阵收口：两集各 2000 查询、五 L 五轮、50 原点 / 250 wall 已在第11会话完成；本会话没有重跑已完成阶段，没有新训练、ANN、构图、GT、模型选择或 QPS，也没有新实验编号。

新增中文 Markdown、六页 PDF、四组 PNG/SVG，以及单文件离线 HTML。HTML 内嵌全部50原点和401失败查询的10730个完整五L方法单元，可按 validation 源行查看命中、GT10、真实入口和返回，下载CSV；两数据集、所有方法和双向既定案例完整保留，不拼开发曲线。

本次只核对50点/250轮/65配对的表级算术和10730个呈现单元逐字段一致；原100000返回集合评分、70000基线回归等是继承的E94验收，第12会话另复算50000，不能把这些重复记为本会话新评分。监督205/206实际Chrome在桌面1280/手机390对全部401query×五L及下载独立核验通过，页面最终字节恢复到该实际验收SHA。执行沙箱两次浏览器启动分别受setsockopt/shutdown EPERM阻断，发生在页面加载前；失败原件和独立成功证据分账。PDF用Matplotlib直接导出，文字页预览及四图目检，无浏览器打印或独立PDF渲染器验收的虚假声明。

方法判断不变：Web组合对compact五L Recall/零命中均改善，但对匹配GT10-soft P五L Recall仍低；Y compact低L小正、高L损伤，尚无稳定整体前沿增益，默认保持。E60小动作的辅助支持稀疏与E89父恢复的训练增损并存，属于不同动作/角色；不能从局部失败推断共享表示无解。简短机制说明另存，不覆盖任何旧卡片。

E94实际700800 NSG / 560000 HNSW，原生操作994.213s与250纯wall695.047s分开；当天累计6854176 NSG / 17820080 HNSW / 360普通小图构建不变，旧开发220点/1100wall分属四批。训练/GT总成本未知项保留。第13会话输出预算16MiB，另72MiB预留、free floor6.45GiB；实际输出和进程终态见closeout。整日goal未由本会话标完成。

根文档旧快照在session13/source_before；新详细说明另建本卡，原history83及其seal不动。s-experiment改正当前索引的E93“最终尚未运行”歧义；s-target转到当前交接并保留第12会话v2纠正入口。spec接口/计量无变化，经检查保留字节。

[中文汇报](../entry_method_exploration/20260913_until2100_v1/session13_report_v1/report.md) · [离线HTML](../entry_method_exploration/20260913_until2100_v1/session13_report_v1/report.html) · [PDF](../entry_method_exploration/20260913_until2100_v1/session13_report_v1/report.pdf) · [机制范围](../entry_method_exploration/20260913_until2100_v1/session13_report_v1/mechanism_note.md) · [本阶段协议](../entry_method_exploration/20260913_until2100_v1/session13_report_v1/protocol.md) · [呈现核对](../entry_method_exploration/20260913_until2100_v1/session13_report_v1/reviews/presentation_verification.json) · [实际浏览器证据](../entry_method_exploration/20260913_until2100_v1/session13_report_v1/reviews/browser_resolved.json) · [E94原报告](../entry_method_exploration/20260913_until2100_v1/stage35_final_comparison_v1/report.md)。

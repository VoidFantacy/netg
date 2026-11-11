# E187 技术过程记录

- 使用独立E187目录，不修改E183–186科学产物、源码或seal。根文档修改前保存在source_before。
- 原生编译首次成功；完整命令见build_receipt.json，binary、原静态库及对象SHA在freeze.json。
- Deep资格测试加载原图时打印padding −1警告，与原资产一致；不改图，旧程序ID/score/route前缀逐字一致。
- 首次资格汇总在Deep资格进程仍运行时提前启动，因资格complete.json不存在而FileNotFoundError退出，未生成freeze/正式结果或改变模型。等待Deep资格完成后原脚本通过；正式矩阵只在成功freeze后启动。
- 原生计数Stats只覆盖REG系列。B32 JSON原始0是占位；不回写原计时包。第二实现按实际主返回及冻结表重构B32精算候选数，报告明确说明，完整在线wall已包含这些精算。
- 正式矩阵冻结后不改源程序、模型、参数或配置。报告/核验脚本可新增，但不能以测试质量反馈回改模型。

- C1汇总初次因变量名controls被局部对照列表覆盖而TypeError退出；失败日志analyze_C1.log及部分派生输出analysis_failed_C1_v1保留。修正汇总变量名后从原timed包重算，不变更搜索源码/模型/配置/返回/计时。
- 原46点读出后另立controls_v1协议/freeze，限定6个GT10近邻L以排除稀疏网格名义速度增益；原46点和analysis_original_v1均保留。补充时间窗口不同，报告披露缓存/频率漂移限制。

- 第一版PDF使用pdf.fonttype42嵌入CJK TTC后实际渲染出现错误字形（边界/文本数检查无法发现）。失败PDF/contact sheet与只核边界的收据保留pdf_font42_failure。改为Type3矢量字形后重新渲染并逐页目视核查；不影响任何科学数组或计时。

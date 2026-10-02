# 127 GT10强项、后继瓶颈与改进方向

2026-09-22，用户要求研究至17:00，解释GT10为什么难以超过并给出方向。本记录是历史数据只读分析、源码/理论和15项一手来源核对，不分配新性能实验号。

## 结果与新增证据

默认仍WebVid GT10-soft-t1 / Yandex GT10-hard，生产E99。E103最新完整五集比较、E118最新候选完整曲线均不改；E119/E120及record125负结果保留其拟合/质量局部正值。

主判断是GT引导的真实候选H、静态query画像压缩及便宜的小图路由共同组成强默认；“十目标自身大幅胜GT1”不受全部控制支持。UnitHub控制已继承QGT选点，不是无监督基线；路由占总时间很小，不能把系统收益全部归因其NDC下降。闭式亲和最优也不是Recall最优。

新增同批E118 fit/L128分析：原top3各单入口加默认，只覆盖全H单入口加默认事后增益的Web K1/K100 21.23%/27.30%、Y 25.76%/31.55%。全H K1 oracle仍有17.8223/8.0566pp，但可救query中有效hub比例中位只有2.33%/9.93%。K100有损动作对平均幅度约为有益动作的两倍；Y正动作对更多，随机换入口仍损失1.0116pp。oracle免费查看结果，不是可部署策略；不是全部三入口组合的上界。

另从E107/E120原缓存重算23个K/L点：七策略在高预算越来越多地命中数相同。Web K100/L1250七策略oracle仅0.4272pp，Y K100/L256为0.8125pp；有限族不能代表高预算全H。两批4096 query不同，不相减作归因；都属已曝光历史资料。

## 理论与方向

理论将候选遗漏、给定在线表示的信息不足、估计/选择遗憾分开；现有矩阵只识别经验候选遗漏。补齐闭式球面亲和、方向误差、代理桥接误差、局部响应稳定、净增损及有限动作选择界的条件/反例；标准工具不包装为新颖性。

优先完善GT10机制/边界论文。入口方法仅保留原路由状态离线编译真实hub的待证伪信息假设；允许超出当前top3才可触及更多遗漏机会，但对齐信息、目标预算收益、查询外泛化、完整成本及前作差异均未过门，实施候选0。若未来另扩底图/预算研究范围，先区分目标预算动作空间不足与动作识别失败。不得据此重开已停止参数网格或旧runner。

## 执行、费用与核验

3个只读分析/核验脚本、4幅图、11页PDF、主报告/理论/文献/方向文档。主核算0.1932秒、机会分解0.0856秒、独立重写整数核验1.9609秒；这些不是搜索QPS或全部人工研究成本。0新ANN/NSG、训练、GT、图、正式计时或新鲜测试载荷。

关键检查覆盖6,709,248个query×动作的K1标签/位图、23点响应统计及原始输入SHA。同会话不同实现，不是独立人员审稿。PDF独立解析关键数字、页边界及空页检查通过，11页已逐页查看。首轮字体/CLI打印问题保留失败件，最终本地Playwright渲染；文档依赖仅在/tmp独立目录，未修改项目运行环境。

原四主文档、AGENTS及输入身份留存；不覆盖旧模型、图、标签、报告或dirty源文件。最终封存以本版本state及completion_audit为准。

## 原始证据

- [研究主报告](../entry_method_exploration/20260922_gt10_strength_review_v1/report.md) · [11页PDF](../entry_method_exploration/20260922_gt10_strength_review_v1/GT10现状与改进方向.pdf)
- [理论与反例](../entry_method_exploration/20260922_gt10_strength_review_v1/theory.md) · [改进方向](../entry_method_exploration/20260922_gt10_strength_review_v1/directions.md) · [一手文献](../entry_method_exploration/20260922_gt10_strength_review_v1/literature/review.md)
- [核验](../entry_method_exploration/20260922_gt10_strength_review_v1/reviews/numeric_audit.json) · [同批候选覆盖](../entry_method_exploration/20260922_gt10_strength_review_v1/results/same_cohort_candidate_coverage.json) · [状态](../entry_method_exploration/20260922_gt10_strength_review_v1/state.json)

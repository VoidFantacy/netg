# v4 独立文献与新颖性复核

2026-09-08。复核对象：[report.md](../report.md)、[method.md](../method.md)。只进行文本、公式和一手源码静态核查，没有训练、ANN 运行、原始数据读取或环境修改。本审查不独立复算主报告的本地统计。

**结论：核心文献归属和新颖性边界通过；发现两处小型可修正项，不影响推荐方向。TAO 式逐行搜索效用树仍是未实现的适配设计；Filter Tree 定理没有被错误当成 ACSG Recall 保证；GATE/LRSG 的既有机制得到明确承认。**

## 1. 两项修正

1. `report.md` Filter Tree 段将普通 0/1 多分类 regret 系数写为 `log2(H)`，应精确改为 `ceil(log2(H))`。原稿 Corollary 4.2 使用向上取整；815/821 不是 2 的整数幂，不能省去取整。[原稿](https://mi.eng.cam.ac.uk/~mjfg/local/Projects/filter_tree.pdf)，[本地抽取](../sources/filter_tree/paper.txt)，lines 229–235。
2. `report.md` LRSG 作者代码链接目前使用 `master`，应固定到已核查的 `53ddfded604a4ad4c11de4e2a9672d515a014378`，并可加 `#L108`。稳定链接是：[NoProjAgent/PrecomputedWalkerAgent](https://github.com/dbaranchuk/learning-to-route/blob/53ddfded604a4ad4c11de4e2a9672d515a014378/lib/walker_agent.py#L108)。这是证据身份修正，不改变所述代码行为。

这两项已发给主审查者；本文件没有同时改动共享主报告，避免覆盖并行编辑。

## 2. TAO：正确区分框架、现有实现与本地适配

主报告明确说借用 TAO 的固定树交替训练结构，将原分类损失改成逐 query×entry 的实测搜索损失，并注明未实现、未运行。`method.md` 又明确叶动作选择、当前左右子树输出、差值权重、代理优化后真实目标验收以及后代到达行重算。这里没有把作者 TAO 说成现成 ACSG 训练器，也没有把局部更新或经验单调性说成全局/泛化保证。

本次独立复读的[作者当前发布](https://faculty.ucmerced.edu/mcarreira-perpinan/research/TAO.html)副本提供具体对应：

- `tao.py:294–345` 和 `:395–449` 分别计算两个子树的实际预测损失、取差生成左右标签、按绝对差赋权；`strict_update` 可在精确损失变差时拒绝分支更新。因此“子树代价差加权”与“检查真实损失”本身已是 TAO 代码机制，不能再列为本项目发明。
- `models/leaf.py:18–89` 的分类叶聚合类别分布并以最高者预测。它不强制全树每类仅出现一次，支持多叶同类的归属表述。
- 本地 utility 版本仍需实现按入口动作列汇总收益选择叶 ID、逐行选取入口效用的 loss、原 kernel 标签合同、样本约束和模型导出。现有分类/回归 driver 不能仅替换名称就宣称已支持这些合同。
- 当前作者 release 的 README 标注 2026，含分类和回归接口，不应笼统称“2018 原版只支持 0/1 分类”。主报告说的是所引用 2018 论文的分类树结构及当前用途，没有作这一错误断言。

本次复核重点是当前作者代码与主报告适配边界；没有重新逐页审阅 TAO 2018 论文全部推导。论文逐页覆盖和发布版本应以配套策略编译文献审计为准。`method.md` 的 weighted binary loss 恒等关系可独立核对：固定左右子树，令两动作损失为 `c_left,c_right`，选择损失等于 `min(c_left,c_right) + abs(c_left-c_right)·1[选错较优侧]`。以 `c=R*−R` 得到报告的 Recall 差权重，零差行不强迫区分；这是适配正确性的局部代数事实，不是训练成功定理。

## 3. Filter Tree：普通 regret 与成本敏感 regret 已分开

重新读本地原稿 Algorithm 1/2 和 Theorem 4.1/Corollary 4.2：

- Algorithm 1 使用当前左右子树各自实际输出的类别 `a,b`，训练标签取低成本的一侧，权重为 `abs(c_a-c_b)`。报告正确排除了两侧免费 oracle 最优值。
- Theorem 4.1 的成本敏感界含诱导分布下的二分类 regret 及 `E[sum_n importance_n]`。这里的二分类 regret 是经该归约/权重处理定义的对象，不是可直接代入任意节点训练误差。
- Corollary 4.2 在普通 0/1 多分类代价结构下将权重和界为 `ceil(log2(H))`。一般 Recall 损失矩阵不满足仅一条相关路径上权重为 1 的特殊结构，故不能沿用该系数；更不能将它直接赋给允许重复动作且迭代修改叶动作的 TAO 适配。
- 报告“线性分支、每动作唯一叶时选择域凸”的条件是足够明确的：一条叶路径是多个线性半空间的交。这个几何推断不适用于使用非线性节点分类器的所有 Filter Tree 变体，也不表示其原稿只能使用线性模型。主报告保留了线性条件，没有泛化到所有变体。

原文来源：[Filter Tree 原稿](https://mi.eng.cam.ac.uk/~mjfg/local/Projects/filter_tree.pdf)；本地抽取 lines 133–174、194–235。本次没有找到或使用可确认的原稿作者可执行实现，报告没有伪造复现结论。

## 4. GATE/LRSG 的定位正确

主报告承认旧 NETG/GATE 的真实 probe 监督、复杂入口侧表示和 raw query 对离线表达打分，没有声称新树首次使用搜索标签、首次取消在线 query MLP或首次实现离线重在线轻。[GATE 作者在线测试](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/tests/test_gate_search.cpp#L56)支持 raw query 检索 hub embedding 的事实；GATE 的 hop 监督不能与当前 K10/L64、128 的直接 Recall 目标混为一谈。

LRSG 的 NoProjAgent 明确吸收线性 query 变换至节点侧，并保留固定 query bias 加法；它不证明任意非线性 query 网络都能离线消除。主报告只说线性变换转移，表述成立。其学习对象是搜索中途的路由评分和最终验证，不是冻结原搜索后的起点选择；报告已分清。[固定版本作者代码](https://github.com/dbaranchuk/learning-to-route/blob/53ddfded604a4ad4c11de4e2a9672d515a014378/lib/walker_agent.py#L108)、[论文](https://proceedings.mlr.press/v97/baranchuk19a/baranchuk19a.pdf)

“仅加强入口侧模型不能改变 raw-query 线性评分的基本边界”针对固定单向量内积分数成立；它不否认多原型、非线性 query 输入、组合路由或搜索中状态反馈可改变边界。主报告是在该限定架构下比较，不是宣称所有 embedding 方法均无能力。

## 5. 引用支持范围与最终边界

TAO、Filter Tree、LRSG 和 policytree 引用在主报告中承担机制来源；本地 oracle 与历史失败另链本地报告。没有用作者性能数字替代 ACSG 效果，没有对“首次”“保证超越 Fast”“全局最优”作无证据宣称。主报告把重模型叫作参照而非上界，把树叫作待证伪候选，这些边界应保留。

建议仅完成上述系数与固定版本链接的小修正。无需因本轮独立文献审查重新扩展论文池、启动实验或改变主推荐。最终论文贡献强弱仍取决于对硬标签树、同容量普通成本敏感模型、GATE/既有入口路径和 Fast 的隔离比较；本轮设计本身没有证明可发表的新颖性或性能优势。

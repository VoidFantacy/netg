# 三入口真实收益排序：单构建探索协议

2026-09-10。用户在完成低秩/梯度/MLP研究后指示“推进一下这个方案试试”，授权实现、标注、训练和轻量比较。独立版本；原源码、图、GT、标签、模型、旧实验结果保留。

## 问题与范围

验证固定真实入口身份、Fast锚定的完整W能否从三入口联合搜索收益中学习，并与同目标rank8对照。不是恢复旧A+B自由映射，也不是恢复E07的在线候选交互ranker或E20固定anchor/C8组合器。

- WebVid2.5M及official Yandex first10M，原raw-IP、K10、冻结NSG、QGT seed20260828，各自H815/821。
- 复用E22已经隔离的fit20K、cal1024、audit1024；Fast先验为相同fit20K构建的paired prototype。它们属于历史开发池，不声称项目级全新未见样本。
- 本轮只用fit构造训练目标；cal只选正则强度。audit不用于拟合/选择。模型冻结后，各数据集validation前2000条作最终五点探索；held-out不打开。
- 所有学习入口始终固定一向量对应一真实hub；在线raw query→Micro-HNSW direct top3→原search_new(mode2)。不学习pi，不增加H，不用query端MLP，不改原搜索kernel。

## 固定的组合采样及标签

仅L128产生训练标签，一份模型用于五个测试L。每fit query最多4组context，每组6个候选第三入口，总上限24个三入口调用（每数据集480,000；两数据集960,000），相同有序三元组可缓存去重。

先以Fast先验精确内积确定top3及其后续几何顺序；同时读取本构建H的旧L128 single hit/NDC，**只用于提议训练候选**，不能当联合收益。排序ties固定真实ID规则。

前三组context分别保留原top3中的两个；第四组使用top3之外的两个入口（一个几何靠前，一个旧single收益靠前，去重）。每个context的第三入口候选依次包括：原top3中可用者、两个后续几何入口、两个全H single效用候选、一个全H均匀随机入口。全部互异且不在context内；随机种子及每query序列固定。context只用于离线比较，线上没有固定anchor。候选数量是本次标注预算，不是线上入口候选池上限。

每次调用原kernel，从三个互异真实入口启动同一共享搜索过程；搜索函数不接收GT，返回后评分，记录hits、GT10 mask、graph NDC和完整top10 ID。每组6个第三入口两两比较，最多15对；以真实三入口hit差生成偏好。零差不强迫唯一赢家，所有query仍留在质量统计分母。NDC不加入训练奖励，本轮单独观察质量与成本。

## 训练与模型选择

令W=P0+τD；τ取fit查询Fast top1与top8分数差的中位数，下限1e−6。分数差除以τ，使优化单位在两个数据集更接近；query仍为raw，导出W不归一化。

固定pairwise logistic损失，权重为两次真实联合hit差绝对值，按每query归一化；无有效pair的query贡献零，整体除以完整Nfit。正则项为λ||D||²/(2H)，λ固定{0.1,1,10}。这等价于对W−P0的显式二次锚定，两个参数化使用同一个目标。

- Full：D为自由H×d矩阵，零初始化。固定目标凸且λ>0时强凸。
- Rank8：D=(VZ)ᵀ，V为d×8、Z为8×H，Z=0；V初始化为该共同目标在D=0处梯度的前8个右奇异方向。仅使用fit梯度，不使用训练后的Full解、cal或validation。该初始化避免无依据的随机子空间限制；没有每步QR或hard命中单调验收。
- 两者使用float64、PyTorch LBFGS、strong-Wolfe、history50、max_iter300/max_eval375、tolerance_grad1e−9/tolerance_change1e−12。最终导出float32 W。记录函数评估、梯度、正则/数据损失、残差和耗时；Full另给强凸梯度残差的最优性差距上界。达到预算但未收敛如实报告，不将它解释为函数类不可能。
- 六个候选全部训练完再作cal真实三入口HNSW搜索。每族按cal总hits最高、再graph NDC较低、再较强λ选一个新候选；同时记录若允许Fast回退会选谁。即使新候选不如Fast，也不将回退冒充方法改善。
- 小型fit诊断固定读取fit前1024条；精确top3与HNSW top3的真实搜索同时记录，区分代理拟合、泛化与部署损失。它不是完整fit质量均值。cal/audit的精确/近似比较及所有基线查询均单线程；只对最终选中候选做audit。

## 评测和停止边界

模型在validation打开前冻结。最终各2000条、L64/128/256/400/800、NSG-Medoid、原Fast30K direct3、matched Fast20K direct3、Full3、Rank8-3，共50点。paired Fast20K及学习模型共用H、真实ID标签、M16/efConstruction200/ef10、HNSW seed20260828，选出的三个真实ID统一升序后交给原kernel，与组合标签的入口顺序一致；原Fast30K保留seed100与原heap顺序，另列训练口径差异。排序开销包含在完整wall中。

每点一轮完整预热、一次独立plain端到端wall；方法顺序随数据集/L轮换。全量count在timer外另跑，并对照返回ID/距离bits/入口；每点16query另与冻结原wrapper验证。记录Recall@10、QPS、零命中失败数、配对挽救/新增失败、route/graph/total NDC。单次wall只能作探索描述。

显式OMP/OpenBLAS/MKL=1、threads=1，实际OpenMP team检查为1。一次只跑一个被测方法，不并发训练、标签或其他性能测量。标注可16线程、训练可16线程，离线耗时单列，不称查询QPS。原图/base/source/library和输入hash启动前核对；身份或parity失败立即停止依赖阶段，保留失败原件后修复。

这轮不运行MLP、策略梯度、新rank或额外seed，不恢复旧大矩阵/C。不根据validation扩展调参。最终无论正负都报告完整五点结果及对照；没有性能正信号则本版本收口。新的探索不以某一L的Recall、fit损失或oracle代替整体Recall–QPS结论。

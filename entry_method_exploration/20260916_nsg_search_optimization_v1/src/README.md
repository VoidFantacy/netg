# E99 构建、验证与恢复

生产修改仅在 `ACSG/ACSG.cpp` 与新增的 `ACSG/detail/CandidatePool.h`。`search_new`接口、对象布局、原Faiss距离函数和所有入口方法保持；原静态库不覆盖。新库 `../bin/libACSG.optimized.a` 由原 `IndexACSG.cpp.o` 与新编译的ACSG实现组成，正式 benchmark 实际链接此库。下一次正常CMake编译也会使用生产源码中的优化。

旧源码已提交到本地Git分支 `backup/pre-nsg-optimization-20260916_103846`，commit `2739b09a67f3ca0b6f145d43690d36345df3182c`。它保存6115个现有源码、脚本、配置和文档文件；主分支与原暂存区未改。备份脚本使用独立Git index，逐个从提交回读bytes核验。大型数据/索引/模型/构建产物保持原位，不声称这些文件已存入Git。完整清单见 `../reviews/git_backup.json`。

可用 `git show 2739b09a:ACSG/ACSG.cpp` 检查修改前实现，用 `git diff 2739b09a -- ACSG/ACSG.cpp` 检查本次修改。新头文件另见生产路径。恢复时只提取需要的文件，避免对整个工作树reset，因为主分支仍保留用户原先的未提交工作。

## 工具顺序

1. `prepare_build.py` 从source_before生成独立命名空间的旧kernel并编译普通回归/评测程序。旧、新kernel共享同一图邻接和base storage，visited/候选scratch独立。不能在正式计时期间重新编译。
2. 普通 `regression.cpp` 差分回归覆盖35,856个候选池用例及8,656次图查询；`build_checks.py` 生成可用静态库、链接最终benchmark，并对新内核及测试程序执行ASan/UBSan。外部旧参考库并未全部插桩。
3. `run_validation.py` 要求两个回归PASS和冻结SHA通过，按五集顺序串行执行。配置、CPU15、所有库/进程单线程、输入返回身份均有断言。运行目录必须新建；失败原件不覆盖。
4. `postprocess.py` 仅在所有测量完成后，逐文件核对五类原始返回/NDC的500文件、重算Recall，并生成CSV。不运行ANN或训练。
5. `plot_results.py` 只读验收后的CSV绘制PNG/PDF。四个预锁点没有插值成完整前沿；误差条是三次实测范围，不是置信区间。

本目录首次普通回归失败来自测试validator对NaN默认trace字段做JSON数值相等比较，已改为序列化表示相等并保留旧日志。生产代码未因此改动，见 `../reviews/regression_validator_fix.json`。正式库和native源代码以 `../reviews/frozen_code.json` 的SHA为准；早期 `native_build.json` 是最初构建过程记录，不是最终冻结清单。

## 与E98短池控制的区别

E98把传给旧插入函数的K整体缩短为有效候选数，会改变原二分查找的边界和等距排序。例如容量4、仅一个有效 `(id=0,dist=1)`，再插入 `(id=1,dist=1)`，短池路径与原函数顺序不同。E99始终使用完整容量L确定位置和重复ID规则，只缩短memmove长度；非有限值或FLT_MAX破坏有效前缀假设时，该query后续恢复原复制长度。E98在真实WebVid上的一致性结果仍保留，但不能据此推断它对所有边界输入等价。

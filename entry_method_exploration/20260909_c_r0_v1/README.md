# 方案 C：同一搜索状态上的一次补充入口干预

状态：`R0_CONDITIONAL_DIAGNOSTIC_DESIGN_ONLY_UNRUN`。

本目录记录 2026-09-09 对方案 C 的独立调研、源码可行性审计、近期前作边界以及与 A+B 的条件性接口。当前结论是：

> **C 有独立的机制诊断价值，但尚不是可用方法，也不应现在并入 A+B。只保留一个有界的“同状态有限动作 oracle → 状态增量可学性”否决路径；任一门失败即停止。**

C 的窄定义是在一个仍在运行的冻结 NSG 搜索中，从同一个完整状态 `S_t` 克隆分支，在同一个预登记剩余 graph-NDC 上限 `B` 下比较 `continue` 与最多四个 `force-expand(e)`。它不重新启动第二次搜索，不丢弃当前 pool/visited/frontier，也不把旧独立单入口效用当作新标签。

- [`assessment.md`](assessment.md)：本地证据、相关工作、状态／动作语义、最小 gate、成本与 A+B 联动条件。
- [`state.json`](state.json)：机器可读决策、全部未执行标志与下一步授权边界。
- [`source_manifest.json`](source_manifest.json)：本轮使用的本地证据与外部一手来源。

本轮补入了两个会显著收窄原创性叙事的近邻：2012 年 Query-driven Iterated Neighborhood Graph Search 已在同一搜索的 queue/result/visited 历史中加入新 pivot；2026 年 ANNiE-S 已在一次 live graph search 的自适应 checkpoint 上调用模型并继续原状态。因此 C 不能声称首次动态搜索、首次中途加入口、首次同状态恢复或首次使用搜索状态。当前仅保留以下条件性方法候选：

> **在可字节等价恢复的完整 finite-beam 状态上，用同状态成对反事实标签学习一次 `continue`／远端 `force-expand` 的边际动作价值；各分支使用同一个预登记的剩余 graph-NDC cap，并保存各自实际 NDC，最终按完整成本包络验收。**

旧 [`v5 C 专题`](../../entry_selection_research/20260908_v5/reviews/adaptive_intervention.md)保留其当时证据；本目录补齐 QING、ANNiE 等前作并取代它作为当前 C 的 R0 判断。旧 E14 rerouter 的停止结论没有被撤销，但其最终 v4 chooser 只在 WebVid 运行，Yandex 最终扩展未运行；只有新动作的同状态 oracle 与 learnability gate 都通过，才可能建立不同于旧失败分支的新证据。

本轮没有修改搜索源码、构建程序、生成 checkpoint、运行 ANN、训练模型、访问 validation/held-out 或授权后续执行。

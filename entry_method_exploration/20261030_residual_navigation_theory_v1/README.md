# 2026-10-30 残差补全与导航价值理论同步

状态：`THEORY_ONLY_UNIMPLEMENTED_UNTESTED`。本次仅按用户“同步一下”整理理论、核对既有证据并同步根文档；没有新实验编号、训练、构图、ANN运行、新GT、性能结果或默认替换。

正文见[理论重评与后继问题](theory_zh.md)。核心是分别判断补点的答案价值与导航价值；入度、有效出边、局部密度和有限预算可达性具有不同含义，低密度/低连通度的因果解释尚未确认。保留历史有效M5/B32/SQ，E194仍是最新完成实验。

阅读顺序：根目录[summary](../../summary.md) → [spec](../../spec.md) → [s-target](../../s-target.md) → 本文正文 → 正文引用的E174/E194原协议与结果。本文不恢复旧runner，不把未实现的搜索状态、入口选择或图修复写成现有功能。

修改前6份入口/索引文档见[source_before](source_before/)，身份见[source_manifest](source_manifest.json)。E194原交付清单在修改前完整核验；修改后通过这些原字节快照桥接可变文档，其余清单项及原封存文件保持原身份。文档链接、快照、封存桥接和内容边界核验见[validation](validation.json)；该核验属于文档验收，不是算法或性能验证。

默认E99 GT10保持：WebVid `GT10-soft-t1`、Yandex `GT10-hard`。详细提案状态见[state](state.json)。

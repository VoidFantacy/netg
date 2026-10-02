# 2026-10-02 ACSG研究状态Git快照

本快照按用户要求保存当前状态、实验记录、现行方法和相关源码。提交到新的本地research分支；不覆盖main，不推送远端，不清理本地数据或旧构建产物。

- 当前默认：生产E99；WebVid GT10-soft-t1、Yandex GT10-hard。
- 最新真实性能实验：[166](../../experiment_history/166_target_bank_frozen_curve.md)。尚无可靠的完整Recall–QPS综合改进，默认未替换。
- 最新封存理论交付：[169](../../experiment_history/169_gt10_algorithm_paper_theory.md)，含现行算法、GT10理论与论文稿，未启动新实验。
- 对话中刚提出的改进：[容量约束图服务归属](current_method.md)，未实现、未实验；补充保存，不回改169封存目录。
- 主交接：[summary](../../summary.md)、[spec](../../spec.md)、[s-target](../../s-target.md)、[历史索引](../../s-experiment.md)；[详细历史](../../experiment_history/README.md)保留原协议与原结果身份。

snapshot_manifest.json逐项记录本次纳入文件的SHA256/字节数、筛选规则及省略产物位置。数据、GT/返回数组、图、画像矩阵、模型checkpoint、虚拟环境、训练逐步输出和大型原始结果继续保留本地；仅特例保存167封存诊断中两个小型bucket_alignment.npz，以保持该交付包完整。此Git快照不能单独替代实验输入。文档中的绝对数据路径与artifact引用保持原历史含义，不伪装成已入库文件。

Faiss仍由原gitlink固定基准版本；[faiss_worktree.patch](faiss_worktree.patch)完整保存本地源文件和权限差异，[faiss_identity.json](faiss_identity.json)保存基准commit、修改文件身份及补丁校验。重建时在该基准版本的独立Faiss工作树执行 `git apply --binary /path/to/faiss_worktree.patch`，不要对已经含相同修改的工作树重复应用。本次没有移动Faiss/main。旧HEAD还包含build/_deps的gitlink而.gitmodules缺相应映射，这一历史构建限制保持；需要依赖时按当前构建合同重新准备，不能把旧build目录视为可移植环境。

source_before/保存本次补充前的根交接文件。169等封存文件只验证字节身份，不重新调用会要求live root仍等于旧截止快照的检查器；根文档合法追加Git接续信息不改变历史封存事实。本次检查只涉及Git内容、文件身份和交接链接，没有运行数学程序或实验。

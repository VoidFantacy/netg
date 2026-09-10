# A+B 下一阶段主线：文档更新记录

2026-09-09，在 C stage1 完成并按门停止后，用户要求更新文档，将 A+B 列为下一阶段主线。

- [s-target](../../../s-target.md)：A+B 为第一优先级，下一项为最小协议；保留 existing-H exact、micro-index、完整 Recall–QPS 顺序门槛。C 退出推进队列，D 后置。
- [summary](../../../summary.md)：记录主线切换及其证据边界，保留 C 的全部实测结论。
- [s-experiment](../../../s-experiment.md) 与 [设计历史09](../../09_research_designs_not_experiments.md)：记录计划接续，不新增实验编号或方法结果。

本次没有架构/API/输入/计量合同变化，spec.md 经核对保持不变。未启动标签生成、训练、ANN 搜索或 validation/held-out 访问。

source_before 与 source_after 保存本次四份文档快照，changes.diff 为精确差异。before_manifest.json 保存修改前身份；update_manifest.json 保存修改后身份与保护检查。C stage1 的 8263 个封存文件及 delivery manifest 均未改变，A+B 联合 R0 四个原件保持历史身份。

文档验证实际命令（工作目录 /data/netg/ACSG）：

```bash
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/reviews/check_documents.py experiment_history/_maintenance/20260909_ab_mainline_v1/document_checks.json --final
```

[检查结果](document_checks.json)：27 份文档、457 个本地链接、10 张历史卡、E01–E21，通过。该检查中相对 C stage1 初始快照的允许变化包含旧 spec 更新；本次是否修改以 before_manifest/update_manifest 为准，本次 spec 未变。原 C 交付清单中的根文档 SHA 属于当时快照，不要求本次更新后的根文档继续匹配旧 SHA。

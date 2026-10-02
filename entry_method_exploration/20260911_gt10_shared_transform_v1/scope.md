# E28研究范围与状态

状态`SHARED_TRANSFORM_EXPLORATION_COMPLETE_NO_FORMAL_GO`，本版本已完成并收口。研究比较GT10 hard锚定的共享linear、小MLP和free静态入口表；在线raw query→单份microHNSW top3→真实hub→原NSG。完整协议和调用预算在[protocol](protocol.md)，结果在[report](report.md)，最终核验在[final_audit](reviews/final_audit.json)。

初始化阶段的临时表述保存在[scope_initialized](reviews/scope_initialized.md)，不作为当前状态。历史fit/cal/audit/validation边界保持，held-out未访问。所有后续训练/搜索需新的独立版本与授权，不重启本目录。

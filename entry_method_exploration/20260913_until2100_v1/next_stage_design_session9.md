# 第9会话后下一阶段（设计，未执行）

E86/E87已完整停止；E88为缓存诊断。先读handoff_session9、root docs和监督记录，再运行resume_inspect_v9.py。不得重跑旧阶段。

优先完成晚间最终对照准备：候选v10保留全部旧60对象，新增3个非零主候选、1个Y零更新别名和4个机制控制。目录不等于选中；E87 Y零更新与所有neighbor控制不得冒充best_new。基于已暴露开发反馈写独立最终协议，冻结best_all/best_new具体配置/模型/图身份、别名去重、选择规则和可报告结论，然后才能读E34历史validation2000输入。最终结果不回流训练/选型，held-out未授权。

元数据草稿session9_final_preparation已核对原NSG、Fast、匹配GT10、Web额外GT10-soft的模型字节、E73完整wall评测器和2000行规模。不是runner。实际每点1warm+5wholewall+1count+16原kernel，14016 NSG；profile每点14000 HNSW。45/55点示例630720/770880 NSG和225/275wall，实际矩阵重算。保留同批所有方法、五L五轮轮换CPU15/线程1；输出完整route+NSG+输出wall，计时外GT/count/hash/序列化/load/build。旧E74的2048/112640/8192等常数及旧deadline必须改成参数；最终query不同，不能套旧aux前缀回归。最终输入打开前冻结选择，之后只做正确性/完整性修正，不能为阳性重新选方法。

若仍有时间开实质新方向，E88支持画像排序是当前提议的限制：先在已暴露fit确认真正优于compact的P独有hub在画像分数中的竞争性，按全部fit统计损伤/支持分布，再考虑固定预算的离线画像/得分目标。只看某条边的支持query会遗漏Web的支持外损伤；更好P完整策略也不等于单目标好。新的动作/训练信号必须对应最终实际三入口，并留全fit/冻结aux接受；不要直接放宽E87支持数/边数/阈值。该方向尚未实现/拟合/评测，不重启旧runner。

硬截止：20:00停新训练、20:40停新增查询、21:00报告。始终串行唯一写者，原底层NSG/base/GT/rawIP不变；大文件只/data，不清旧artifact。当前72MiB晚间与交接预留继续保持，累计新输出以session9_closeout/resource_accounting.json为准。

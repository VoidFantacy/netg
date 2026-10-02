# ACSG 下一阶段目标与接续

2026-09-12，E54完整模型四格完成并独立验收。

下一阶段E55固定17候选/集：匹配默认、E47 RL/ES各双seed，以及本次E52/E53双seed的全部A/S/T共12模型；候选池在四格查询前已经锁定，不按此处结果删选。先独立128条普通二进制恢复，再cal1024原U/低NDC/固定序择优，冻结best_all和best_new。最终WebVid五方法/Yandex四方法与NSG、Fast30K、FastGT10-hard同机单线程五L五轮，历史validation2000，Recall/QPS/零GT10失败率三指标；总710144 NSG/225wall轮。若默认优于新候选，明确说明；最终结果不回流换模型。21:40停止新查询，22:00交付。

[E55查询前协议](entry_method_exploration/20260912_final_method_comparison_v1/protocol.md)和源码已准备，尚未冻结执行。原17候选/集不按四格结果删选；单线程串行、旧源保护、最终GT不进训练。cal来自router_train，validation来自另一源命名空间，局部行号重合不等于查询重合；源记录与实际向量双重核验。

# 会话4本地stop-condition源码核对（只读，未实现新策略）

2026-09-13 12:34，E71 wall进行时只读小段源码，不做数值评分/构图/ANN。原始源码均未修改。用途是给后继会话解释可尝试的实现边界，不能当已测得distinct-hub性能。

- `benches/hnswlib/hnswalg.h:314` 的 `searchBaseLayerST` 按physical internal node管理两个heap；已有callback可接管consider/stop/remove-extra，并在结果加入/移除时收到 **external label**。E66/E70当前不使用callback，仍是 `searchKnn`→bare-bone分支。
- `searchStopConditionClosest:1331`在构造最终vector时直接复制top_candidates的internal node ID，未调用getExternalLabel；而普通searchKnn会转换。即使当前slot label恰与internal插入序相同，也应显式internal→external slot→real hub验证，不把接口返回类型当真实ID。
- `remove_point_from_result`在hnswalg.h:427传入的第三参数是刚考虑的candidate `dist`，不是刚弹出的point距离。因此新callback若只按label维护hub引用计数可忽略此参数；若依赖移除距离，必须另行修正独立适配或按已记录label查值，不能直接信任此参数。
- `stop_condition.h`已有MultiVectorSearchStopCondition，按doc计数不是新概念。其BaseMultiVectorSpace从向量尾追加doc ID取值，不能读取现有float-only冻结图。该本地MultiVectorInnerProductSpace构造器还未见给成员dim_赋值，而get_dist_func_param返回&dim_；未执行该类，不对其上游版本作推断。推荐后继若采用，直接实现使用slot外部label映射的BaseSearchStopCondition，不实例化这个不兼容space。
- 现成MultiVectorStop另维护dist/doc heap，tie语义与NSW的CompareByFirst heap并非同一排序。新实现应通过label计数/原生实际弹出事件管理，避免对平分元素假定两个heap同步弹同一doc。输出仍需按明确distance/slot规则选每hub最佳、取三真实hub并canonical升序。

候选思路（尚未冻结/编译/运行）：在已冻结的P/duplicate/mode三种物理图上，只改变候选结果宽度为10个不同真实hub，原普通ef10/30作为参照。单画像一hub一slot的callback恢复控制用来排除API路径/tie改变，duplicate用于检查冗余槽，mode用于真实收益。必须先合成验证最大多重度/平分/内部外部ID映射/移除/不足三hub/回调复位，再真实预检与完整L128历史aux，最后另测完整wall。按doc计宽仍不保证更少距离或更好NSG；不能宣称等工作量、10倍有效宽度或新颖性。是否值得下一步以E71完整成本结果为依据，当前不启动。

补充：监督12:57 review_065检查CompareByFirst仅比较distance，旧searchKnn截k先于external转换，stopCondition反向pop完整堆；完整数组先按external label排序再截3可能破坏singleton tie恢复。只有原堆相同且filter不变时，反向pop数组前3等价原堆截k子集。下一实现须验证原堆/早停及合成tie，不将新mode的排序合同混同旧singleton控制。来源为supervisor_notes当前只读源码补充，无新查询。

# 距离复用的接口前件与最简单控制

2026-10-02，纯源码/理论审查。以下接口未实现或编译，没有补trace或性能。对应[候选A](candidate_gates.md)、[完整成本门](full_cost_conditions.md)。

## 已确定的一次重复与局部handoff

原HNSW的成功、非空、无删除/过滤的`searchKnn`调用至少重复一次相同physical slot距离。初始entry先评分；每次上层严格改进同时保存`currObj/curdist`；进入base时传了`currObj`却没有传`curdist`，base再次用相同query、向量地址、callback和dimension评分该终点。maxlevel=0仍有这一次重复。这是源码调用恒等性，没有量出省时。

依据：[初始评分/上层更新/调用base](../20260930_theory_until2200_v1/research/query_target_transfer_v1/src/common/hnswlib/hnswalg.h:1276)、[base起点评分与过滤分支](../20260930_theory_until2200_v1/research/query_target_transfer_v1/src/common/hnswlib/hnswalg.h:329)。历史审查代理在现有entry_method源码内未找到已执行的同形handoff控制；这是限定范围的项目检索，不是全局新意证明。

更强的简单对照是`UpperHandoff`：将完整原`curdist` bits交给base的起点评分事件，仅在原分支本来会评分时复用。保原逻辑请求/observer计数、visited与heap转移。nonbare删除或过滤分支原来会用max sentinel，不能盲目注入`curdist`。本次两路原HNSW没有删除/过滤，但接口合同必须保留这些条件。

该控制每query只复用已持有的局部值，不为全部R请求增加dense lookup。Default3与TargetBank都应有同形控制；通用memo要胜过原版、handoff及同memo默认中事前冻结的更快默认，才能认领额外效果。handoff也可能被已有编译/流水影响抵消，未预测任何QPS。更多默认控制时，成本公式中的`max(S_default,0)`相应改为所有冻结默认净节省的最大值。

## 紧凑有效key设计仅提供可审查接口

一个没有容量/淘汰调参的参考设计是SoA：原physical slot→dense有效key的uint32数组，加每key的uint64 stamp与uint32 distance bits。一次完整query使用一个epoch，上下层共享；物理图节点始终不合并。已曝光ID计数若最终通过跨slot原生bit一致门，则20000槽的静态数组payload为Web约269468 bytes、Y316052 bytes（`4×20000+12×U`，U=15789/19671）；这不含分配/对齐/上下文开销，也不代表实际缓存占用或收益。默认815/821画像槽可各自作key。

dense key的必要条件是：所有被合并槽在该query和原回调下返回相同bits。相同real-ID或相同向量bytes单独不足以证明这一点：一般callback可能按地址对齐改变归约。当前`space_ip.h`输入用`loadu`，归约与尾块依维度、callback构造时固定，源码未见输入地址分支；仍须保实际跨槽bit门。失败时可限定physical slot key，或明确包含全部地址相关算术路径签名，不能把数学点积相等当bit一致。

生命周期合同还须固定：bank/query字节不可变、参数/kernel/FP环境不变、评分值不受调用次数或slot身份影响；无并发写、递归重入或在一个epoch中切换query。重入需独立上下文；64bit epoch回绕预先规定清stamp，费用归入触发query；异常退出不能让下一query沿用旧epoch；miss时先写完整bits、成功后才publish stamp，每次warm/count/plain方法调用均有自己的beginQuery。若FP exception flags会被读取、清除或触发trap，须额外处理其可观察副作用。画像、raw-target、raw-base和不同kernel各有namespace，不跨查询共享。

逻辑请求数不随命中减少，native-dot次数单独计；命中时保留原计数/观察事件。lookup、映射、store、stamp、query边界以及所有缓存相互作用计入完整wall。获取physical slot可在原调用点传入或从原data pointer识别，但方式及费用必须事前冻结；本稿不选择一个未经测量的更快实现。

状态仍为`HOLD_MEMO_MISSING_NATIVE_TRACE_AND_MATCHED_FULL_WALL`。已确定的一次重复不证明足以跨越旧23.282μs缺口；静态重复槽也不证明通用表优于局部handoff。若后续有授权，应先验收native保真和最强简单控制，再讨论净收益，今天不执行。

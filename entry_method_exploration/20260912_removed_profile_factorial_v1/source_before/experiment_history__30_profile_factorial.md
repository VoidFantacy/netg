# 30. E41 目标画像与其余画像的2×2隔离

2026-09-12，状态`COMPLETE_TARGET_REST_FACTORIAL_WEBVID_LOCAL_SIGNAL_YANDEX_TARGET_NULL`。[报告](../entry_method_exploration/20260912_profile_factorial_v1/report.md)、[协议](../entry_method_exploration/20260912_profile_factorial_v1/protocol.md)、[锁定配置](../entry_method_exploration/20260912_profile_factorial_v1/config.locked.json)、[完成审计](../entry_method_exploration/20260912_profile_factorial_v1/reviews/completion_audit.json)、[验收](../entry_method_exploration/20260912_profile_factorial_v1/reviews/final_audit.json)。用户明确要求执行E40的未运行控制；本次八格全部完成，没有新训练。

## 设计、输入与结果

固定E40两案例：WebVid selected/action3/hub42091，Yandex zero/action0/hub9339959；各用E39原1024训练query。C=全中心，F=全原扰动，S=只改目标行，R=只改其余行。逐字复制既有单位W，S/R未必为原共享参数可达像。原H/ID/顺序、普通HNSW M16/efC200/seed20260828/ef10及原NSG raw-IP/L128/K10保持，0optimizer。

WebVid的一个有效单画像改动可以从全局负收益中分离：只改hub42091保留正例1→5，负例保持9，全1024净增4命中且无新增损伤。Yandex的hub9339959单独改动没有命中收益，其余画像块已能重现完整扰动的收益与损伤。当前证据支持按实际干预分配画像责任，不能按最终新增入口直接归因；未建立跨数据集学习方法或泛化优势。

| 数据集 | 配置 | 新增命中G | 损伤L | 净增命中 | ΔRecall pp | 受益/受损query |
|---|---|---:|---:|---:|---:|---:|
| WebVid | C 原中心 | 0 | 0 | +0 | +0.0000 | 0/0 |
| WebVid | F 完整扰动 | 22 | 52 | -30 | -0.2930 | 12/16 |
| WebVid | S 只改目标画像 | 4 | 0 | +4 | +0.0391 | 1/0 |
| WebVid | R 只改其余画像 | 18 | 52 | -34 | -0.3320 | 11/16 |
| Yandex | C 原中心 | 0 | 0 | +0 | +0.0000 | 0/0 |
| Yandex | F 完整扰动 | 20 | 23 | -3 | -0.0293 | 6/5 |
| Yandex | S 只改目标画像 | 0 | 0 | +0 | +0.0000 | 0/0 |
| Yandex | R 只改其余画像 | 20 | 23 | -3 | -0.0293 | 6/5 |


## 案例与解释

| 冻结query（train/source行） | C 原中心 | F 完整扰动 | S 仅目标 | R 仅其余 |
|---|---:|---:|---:|---:|
| WebVid positive 707/26913 | 1 | 5 | 5 | 1 |
| WebVid negative 3282/22588 | 9 | 0 | 9 | 0 |
| Yandex positive 3349/19628 | 0 | 8 | 0 | 8 |
| Yandex negative 3962/21906 | 10 | 0 | 10 | 0 |


WebVid S只帮助row707一条query，无新损伤；F的22个增益中只保留4个，其余18个在R中，全部52个损伤也在R中。该正点必须保留，但相对E37已选中心、且案例/训练数据有历史GT使用，不是独立泛化或默认替换证据。Yandex R已经重现F全部命中/入口，目标行不是本次命中差的必要来源；S自身仍有一条入口变化但没有命中变化。

两集2048条query的命中I=F−S−R+C逐条为0，未观察到命中层非线性交互；NDC/U并非严格无交互。坏路径出现某hub不等于该hub画像更新造成损伤，R中该hub画像保持中心也可能进入坏路径。两个因素同时包含画像评分与普通小图重建的影响，不隔离访问/图机制，不证明任意共享表示硬冲突。

## 执行与保护

实际8192次正常NSG+384次parity=8576，低于10000硬限；HNSW8448次、普通构图8次、optimizer更新0、新GT0。两个查询进程串行CPU15/实际线程1，合计19.000s，其中索引加载14.678s、构建0.381s；含计数/写盘/验收，不能当QPS。峰值RSS约5.441/9.950GiB。

8192完整返回独立GT集合评分、4096旧输出逐位恢复、128query三路parity、八W行构造与2048交互独立复算通过。原E37–E40整目录/大NSG/native依赖SHA保持，根文档前件保存；没有新原validation/held-out访问/hash，保护旧隔离开发产物的字节读取单列。全部模型/图/返回原件保留，无新QPS/默认更换。

## 接续边界

当前hub42091/9339959的2×2已完成；停止重训/调σ来救Yandex目标无效分支，不把WebVid单query正值升级全H训练。下一最小设计为原同负例中唯一被移除画像（WebVid1627796/Yandex8309868）的责任隔离，尚未构图/查询；同四格预计8576/硬限10000、0optimizer，无排队任务，详见[s-target](../s-target.md)。旧局部信号及E37开发门保持。

[全池表](../entry_method_exploration/20260912_profile_factorial_v1/results/metrics.csv)、[逐query](../entry_method_exploration/20260912_profile_factorial_v1/results/queries.csv)、[案例](../entry_method_exploration/20260912_profile_factorial_v1/results/cases.csv)、[原始JSON](../entry_method_exploration/20260912_profile_factorial_v1/results/diagnosis.json)、[图](../entry_method_exploration/20260912_profile_factorial_v1/figures/whole_pool.svg)。

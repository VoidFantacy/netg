# E41 目标入口画像与其余画像2×2控制

2026-09-12，状态`COMPLETE_TARGET_REST_FACTORIAL_WEBVID_LOCAL_SIGNAL_YANDEX_TARGET_NULL`。用户要求的八格控制全部实际完成。[协议](protocol.md)、[锁定配置](config.locked.json)、[完整结果](results/diagnosis.json)、[独立核验](reviews/independent_verification.json)、[完成审计](reviews/completion_audit.json)、[最终验收](reviews/final_audit.json)。

## 当前结论

WebVid的一个有效单画像改动可以从全局负收益中分离：只改hub42091保留正例1→5，负例保持9，全1024净增4命中且无新增损伤。Yandex的hub9339959单独改动没有命中收益，其余画像块已能重现完整扰动的收益与损伤。当前证据支持按实际干预分配画像责任，不能按最终新增入口直接归因；未建立跨数据集学习方法或泛化优势。

两集全部2048条query的命中交互I=F−S−R+C均为0；当前观测是两个画像块命中效果相加，不能写成已发现非线性耦合。总NDC/原U有小非零交互，不能将命中相加扩展为所有搜索工作和浮点奖励也严格相加。

## 干预、来源与四格

C全部画像取E39对应中心，F全部取E40冻结原动作；S只把目标hub一行换成F，R只将F目标行换回C。WebVid selected/action3，目标42091（内部slot17），Yandex zero/action0，目标9339959（slot771）。S实际各只改1行，R分别改814/820行；所有行都逐字复制既有单位float32 W，未训练或插值，S/R不冒称原共享RL可达checkpoint。

案例/正负行从E40原attribution_cases直接冻结，未按新结果更换；WebVid来自E37已选μ140，Yandex来自μ0，两个中心身份不同，不能并为同一训练阶段。全部query为E39原1024训练行，原4096输入/GT/源行不改，有历史使用，非独立泛化测试。

每格普通HNSW M16/efConstruction200/seed20260828/ef10、原真实ID/顺序、direct3升序→原NSG L128/K10，raw-IP/embedded base不变。改画像会自然改变普通重建的邻接，所以本控制识别整个画像块干预（评分与小图均可能改变），未隔离HNSW访问路径或独立图效应。

## 全1024收益与损伤

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


表中以该集固定中心C为参照；WebVid C是E37已选模型，不能把S的+0.0391pp称为对当前默认GT10的独立改进。S只帮助一条已选过的训练query，没有新损伤，是局部机制信号。F原本增加22命中、损失52；S仅保留其中4个增益，R保留另18个且产生全部52个损伤。其余收益没有被抹去，不能称S保留了F全部收益。

Yandex S全池命中与C相同，R全池命中与F相同；R/F入口也完全相同，但route NDC不同。S仍改变一条query入口而没有改变命中，不能写成画像/搜索完全不动。Yandex目标单行的原改善未保留，预设局部案例条件未过；WebVid同时完整保留指定改善并消除指定损伤，局部条件通过。两件事不构成双集方法GO。

## 冻结案例与反事实

| 冻结query（train/source行） | C 原中心 | F 完整扰动 | S 仅目标 | R 仅其余 |
|---|---:|---:|---:|---:|
| WebVid positive 707/26913 | 1 | 5 | 5 | 1 |
| WebVid negative 3282/22588 | 9 | 0 | 9 | 0 |
| Yandex positive 3349/19628 | 0 | 8 | 0 | 8 |
| Yandex negative 3962/21906 | 10 | 0 | 10 | 0 |


WebVid正例row707只有目标画像块带来+4：S=C+4，F=R+4；负例row3282只有其余画像块带来−9：R=C−9，F=S−9。R中hub42091画像仍是中心值，但它依然进入坏三入口并使9→0；仅凭该入口出现把损伤归给其画像更新，会归错责任。

Yandex两条案例中，目标画像保持中心值的R已经重现0→8和10→0；S两条都维持C。因此E40“新增同hub有正负”的关联，不能证明该hub画像改动导致这些收益或损伤。本结论不表示这个真实入口自身没有NSG作用，而是该画像行的这次改动对本设置的命中效应为零。

每query I=0的强度限于当前两个固定块、现有幅度、单次确定重建和这2048训练query。它并不证明所有方向都可加，也不证明全部共享表示足够/不足。完整query/入口/因素主效应见[逐query表](results/queries.csv)，四格案例入口/计数见[案例表](results/cases.csv)。

## 成本、核验和保护

实际8192次正常NSG+384次parity=8576，低于10000硬限；HNSW8448次、普通构图8次、optimizer更新0、新GT0。两个查询进程串行CPU15/实际线程1，合计19.000s，其中索引加载14.678s、构建0.381s；含计数/写盘/验收，不能当QPS。峰值RSS约5.441/9.950GiB。

主分析CPU8/线程1约0.083s，独立复核约0.402s；不含协议/源码编写、保护hash、绘图和人工阅读。WebVid S相对C graph NDC +0.00397%、total +0.00466%；Yandex S graph0%、total约+0.000099%，这些不是wall/QPS改进。

八份W行来源/单位范数独立验证；C/F四个图的W/拓扑/物理图SHA恢复E39，4096条正常输出按ID/距离bits/入口/两NDC逐位回归。每格16query做count/serialized plain/original kernel三路，128条parity原始输出另与正常结果逐位一致。全部8192返回独立集合评分，2048交互及四条冻结案例、八个全池G/L/奖励重算通过。

E37–E40整目录前后SHA保持，原大NSG和native依赖SHA核验；没有新GT/optimizer/validation/held-out原始读取或hash，保护读取包括旧隔离开发产物，未沿旧manifest递归访问原评估集。原画像/模型/大图/默认保持，根文档修改前件独立保存。全部物理W/小图在models，原始aligned返回在results，调用/线程/时间与进程状态在logs/jobs.json。

[全池图](figures/whole_pool.svg)、[冻结案例图](figures/frozen_cases.svg)。本版本8格预算收口，无新训练/评测排队。

## 接续：验证负例中被移除画像的责任，尚未执行

当前2×2已经完成，不重跑、不追加本次标签或训练。停止把Yandex的9339959当作已识别有效画像；WebVid42091保留为单query的局部正信号，不据此启动全H自由画像训练。

唯一最小后续是把同一固定负例里被移除的画像作为新目标：WebVid row3282原移除hub1627796，Yandex row3962原移除hub8309868。两者来自原冻结三入口差集，均唯一，不按新结果挑hub。这检验坏改道是否来自原入口画像被压低，而不是新增入口自身变好；仍可能包含普通小图重建效应。

沿用各自原C/F、同1024名单和W行字节，再做C/F/S/R：S只改该被移除画像，R改其余但保留它。若S能复现原负例损伤而R消除它，支持该画像改动在这个背景下既能产生损伤、又是完整扰动中该损伤的必要组成；两条件分别报告。若不成立，不据此遍历全H或扩大网格。完整1024的G/L与新增损伤继续收费，不只看负例。

建议仍双集四格8192正常+384parity=8576、总硬限10000、8构图、0optimizer/新GT/新validation/held-out，无QPS。此为新版本待冻结方案，当前没有这些新目标的反事实结果或排队任务。保留原C/F回归、CPU15单线程、输入/输出SHA、失败完整预留合同。

确认责任之后才讨论按入口构造小动作、用真实反事实奖励进行信用分配；不能直接把全局reward分给所有最终入口。E22/E28–E32自由表示/目标实验仍须作为约束，原有局部收益不能替代独立开发和完整Recall–QPS。当前没有新训练授权被推断或任务排队。


## 实际命令

原目录一次性冻结、拒绝覆盖。准备、两集查询、后评分/核验/绘图串行，日志保留；重跑须建立新版本，不能直接覆盖当前产物：

```bash
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 8 timeout 1800 .venv_cpu/bin/python entry_method_exploration/20260912_profile_factorial_v1/src/prepare.py
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 15 timeout 1800 .venv_cpu/bin/python entry_method_exploration/20260912_profile_factorial_v1/src/run.py webvid2_5m_light_v1
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 15 timeout 1800 .venv_cpu/bin/python entry_method_exploration/20260912_profile_factorial_v1/src/run.py yandex_t2i_official10M_ip_v1
```

分析/独立复核/绘图为src/analyze.py、src/verify.py、src/plot.py，使用相同单线程环境、CPU8，均不增加NSG或训练。

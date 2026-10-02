# E87：完整策略真实收益提出新目标、实际单边筛选

2026-09-13第9串行会话。E86固定几何候选的训练收益仅局部迁移，Web aux对compact+18/失败−3仍不及P/E84，Y−4/0；原门保持。本版改变候选来源，既不扩大旧64/47名单，也不改变E86筛边阈值。固定原compact画像/图/H815/821及原NSG/base/rawIP/GT，在线仍静态小图一次路由和原三入口NSG。

仅用原fit20K=router_train[10000:30000]的真实P与E86已完成compact完整返回。对P命中数严格多于compact的query，枚举P三入口中不在compact三入口的真实hub。目标取此hub在compact bank对本raw query float64内积最高的slot（tie小slot）；源为原compact实际排序首slot。若源有底层空槽且目标非旧邻居，则给该边加(P_hits−compact_hits)权重票，并单列独立query支持数。每源取总权重最高、tie目标slot小的一条，要求至少2个不同query支持；全局按(weight票降序,source升序,target升序)取前min(64,N)。不扫阈值/源/目标/种子。原完整三入口差只用于候选提议，不将差值当目标hub或新增边的因果信用。

候选名单在任何新响应前冻结；保存全部真实source rows、P/compact hits与完整三入口、所有提议事件/票/目标slot及实际合法性。每候选与E84/E86原边是否重合仅记录，不据重合排除或回选。固定近邻控制为相同source的最高float64画像内积其他hub非邻居，tie小slot；度匹配而非长度匹配。

沿用E86已验同SHA route helper实际独立加边、全20K plain/count路由、7slot/距离bits及还原bytes；全部新NSG响应仍调用E69同SHA helper。缓存增加已验证E86原compact全fit，以同query/namespace/row/完整三入口/原NSG/kernel/IP/L128/K10/GT键复用；routeNDC全部实测。单边接受仍全fit净命中>0、两个10000半区>=0、zero失败不增、总NDC<=原compact1.01。所有合格边一次合并，原source最多一边；再测全fit并图及同source度控制，报告非加性，不能按并图反馈删改再选。无合格边时明确零更新，不称成功。保存全部正/负/平边。第一候选物理图128回归；无候选则明确未执行该回归，0调用。

全部双集模型/训练及源身份验收并冻结后，aux7952原历史池仅接受，本版不入教师。六方法：P、compact、E84几何图、E86固定筛边图、新utility、匹配neighbor，128预检后7952，原L128/ef10/7slot去重3。新主方法对P/compact/E84/E86全量净命中>0、两半3976均>=0、zero失败不增；对neighbor全/两半>=0且zero失败不增；并图fit全正/两半非负/失败不增且有实际接受边。至少一集完整门通过才另建完整双集wall协议，否则停止本候选生成/筛边版本，不扩大名单或按aux重训。对照之间同三入口必须返回/距离bits/graphNDC相同。

数据角色：P-fit含旧train/monitor；全aux/两半、cal/audit都已有历史暴露，接受反馈计训练信息。所有用于候选提议的NSG输出属于训练监督，不能称几何无标签。E34最终原始query/GT与held-out本版不打开，不按旧最终反馈选型。

预算前瞻：最多128边；全fit路由候选+两基线+四并图为5360000 HNSW，另第一候选物理回归最多512，总训练<=5360512。训练新增NSG每集16384、总32768（含plain/count补缺/192基线原kernel回归），失败全预留无自动查询重试。辅助NSG194304/HNSW193920；总NSG<=227072/HNSW<=5554432。实际无候选减记相应未执行调用。所有ANN串行CPU15、实际进程/OMP/BLAS/MKL/NUMEXPR/BLIS1线程、RSS32GiB；训练job1200s，17:55停新训练job、18:02停新辅助job、18:10硬停query，18:23:29前安全交接。任何调用缺口超cap在下批前停止，不缩数据或改门重跑。

本阶段96MiB、session9全部新输出192MiB（含E86全部封存），额外晚间64MiB/交接8MiB，新floor6.55GiB；现场free约6.815GiB，预留剩余额度后核验。输入/binary/已有缓存引用，不复制大文件，不清理旧产物或修改Codex配置。无新编译/普通构图/GT/梯度；2离线提议筛边拟合、最多6静态安装分别记账。新/继承P/GT/几何候选成本与纯wall分开，0QPS阶段只报质量与计数。

完成history76、s-experiment、summary、s-target；新候选proposal与source_code=0/1/2旧P/mode/compact、3新键的artifact合同同步spec。每阶段source_before/root_after与finalseal、失败全表/图/campaign handoff保留。整日20:00/20:40/21:00门不变，会话完成不等于整日目标完成。

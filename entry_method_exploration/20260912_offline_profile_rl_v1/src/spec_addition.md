
## 离线画像策略优化与普通HNSW重建（E37，2026-09-12）

[独立协议](entry_method_exploration/20260912_offline_profile_rl_v1/protocol.md)将学习放在离线静态画像构造阶段。固定当前GT10画像P、H815/821、真实ID映射、原base/raw-IP/NSG；只用train4096单位query二阶矩生成B(d×16)。[common.py](entry_method_exploration/20260912_offline_profile_rl_v1/src/common.py)实现W=normalize(P+0.25(PB)(tanh(X)/4)Bᵀ)，float64计算、float32导出；X=0直接复制P字节。输出画像会改变普通HNSW重建后的邻接，但没有独立边操作或在线策略模型。

[environment.cpp](entry_method_exploration/20260912_offline_profile_rl_v1/src/environment.cpp)提供create/build/run/save/verify/data/stat C接口，[native.py](entry_method_exploration/20260912_offline_profile_rl_v1/src/native.py)绑定。每个候选画像从零以原M16/efConstruction200/seed20260828/原ID插入顺序建普通HNSW，efSearch10、direct top3，三个真实ID升序进入原NSG L128/K10。C++不读取GT，返回完整ID/距离/入口/route与graph NDC；Python后评分真实命中及零命中事件。每次构图保存W SHA和入口、层级、全部有序邻接的拓扑SHA。接口拒绝非有限/非单位画像、非法query行与非协议L，原项目hnswlib和大图不修改。

[train.py](entry_method_exploration/20260912_offline_profile_rl_v1/src/train.py)是one-step Gaussian参数策略：每个动作采样整份静态画像系数，同一份图服务batch128。奖励为命中增量减0.1倍逐query总NDC相对变化、0.1倍零命中事件变化及画像均方漂移。RL使用8个独立扰动的score-function/leave-one-out估计；ES对照使用4对正负扰动。两者同高斯平滑黑箱目标、表示和调用预算，不将其称作两个不同模型族；没有多步PPO、固定C8重排或旧三元组标签代理。

两集各RL/ES双seed，200更新/次，σ0.3、Adam、cosine步长、梯度范数与参数均值限制均由[锁定配置](entry_method_exploration/20260912_offline_profile_rl_v1/config.locked.json)及协议定义。step0和20..200存完整确定性train512/monitor1024结果；非零checkpoint按monitor U及graph NDC门选择，选中/末点分别输出mu.f64、W.f32、graph.hnsw和identity.json。全部动作/扰动/batch/奖励/返回/optimizer轨迹保存，12800份重复大画像由冻结系数与B重建，原始H/NSG仍为冻结依赖。

[部署控制器](entry_method_exploration/20260912_offline_profile_rl_v1/src/deploy.py)在全部模型冻结并通过独立训练复算后才准备历史cal1024；按cal U/总NDC/seed冻结选择，再准备audit1024。实际部署直接使用与E34逐字一致的无hook[评测binary](entry_method_exploration/20260912_offline_profile_rl_v1/bin/evaluate)。在线仅raw query→普通HNSW top3→ID升序→原NSG，无query投影/MLP/组合枚举，GT只在全部原始搜索后打开。选中模型与训练checkpoint在fit128完整字节一致；plain/count/原kernel和五L相同入口/图均独立核验。

当前GT10、RL、ES、Fast30K、NSG在两集历史audit1024上各L64/128/256/400/800，共50点。每点一次完整warmup和5次轮换plain整批wall，CPU15、进程/OMP/BLAS/MKL1线程、无同时训练或重分析。timer包含完整路由、映射、NSG和输出，GT/count/hash/build/load/IO在外。L128的route-only/graph-only单独测量，不相加充当完整wall。Fast30K是原训练量/seed的历史基线，非本轮同训练量消融。

[独立审计](entry_method_exploration/20260912_offline_profile_rl_v1/src/audit_training.py)复算全部GT交集、奖励、12800动作画像hash、1600次更新和88checkpoint；[分析](entry_method_exploration/20260912_offline_profile_rl_v1/src/analyze.py)从原始输出重算质量/NDC/五轮QPS、配对结果和共同区间插值，并导出CSV、Excel和PNG/SVG/PDF。[最终验收](entry_method_exploration/20260912_offline_profile_rl_v1/reviews/final_audit.json)验证旧资产保护、真实调用、线程、所有图表/工作簿/文档链接，结果及证据限制由[summary](summary.md)/[历史26](experiment_history/26_offline_profile_rl.md)维护。

本轮train4096、monitor1024、cal1024、audit1024源行互斥，但原画像及数据都有历史使用，非全管线盲测；没有读取/hash新的validation/held-out原始输入。改变P/B/参数化/图参数/H或插入映射需重建受影响画像/小图/反馈；query、GT、NSG、metric、L/K、入口次序变化需重新核验或生成反馈。模型冻结、开发门与历史audit曲线不构成默认替换或独立正式性能GO。

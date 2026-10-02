# E63 原零命中query质量重权（前瞻协议）

2026-09-13，独立串行会话2。E61保持每query质量1，未直接加强原零命中query；E62评分/拓扑均有损伤。此版本固定原GT10成员归属，仅改变query质量，检验直接加强失败训练query能否带来净收益。先读history04→E09原builder/manifest：E09是top32单入口signed advantage×连续hardness残差，此处是原三入口zero-hit身份的正权GT10聚合；不称难度重权新颖，也不抹掉E09局部正值。

## 画像与控制

冻结E61原P、20K训练输入及E33基线完整返回。z=1[hits@10=0]，固定w=(1+z)*20000/(20000+sum z)，原a=10个GT目标的原raw-hub hard/soft归属均值，W=normalize(unit(raw_hub)+Σw*a*unit(query))。WebVid保持GT10-soft-t1，Yandex保持GT10-hard；总query质量20000、raw prior权重1保持。零权变化w=1重构须逐字恢复P及原assignment SHA。

三模型/集：baseline、zero_mass2、sham_mass2。随机对照固定seed20260913，在完整20K无放回随机选与zero-hit相同数量query，同权重分布/总量；不保持真实难度、hub质量或位移幅度。sham不参与推荐。画像全部冻结后才运行新模型。

原base/raw-IP/GT/NSG/H815、821/ID映射不变；普通Micro-HNSW M16/efConstruction200/efSearch10/seed20260828，direct3升序真实ID进入原NSG L128/K10。无在线新网络、probe、重排或重建大图。

## 角色与门

P-fit=router_train[10000:30000]，含历史train4096/monitor1024，全部已在E33使用；zero-hit标签用于画像训练。cal=[0:1024]只按固定门选型；audit=[1024:2048]仅报告固定模型结果，已历史和今日使用，不称盲集。Fast30K曾拟合全router_train。E34最终validation2000不进入本阶段任何训练/选择；held-out不打开。引用E61同namespace/row/query/GT缓存，完整原路由恢复和64行/图三路parity后才认可复用。

唯一推荐候选zero_mass2按cal净命中>0、zero-hit数不增、mean totalNDC≤baseline×1.01进入下一阶段；audit不回选。fit净值、全部11原命中组的GT成员得失、救回/新增失败独立报告；fit负必须保留，不能仅称迁移问题。随机对照只解释。无门通过停止该2倍版本，不扫强度或随机seed。通过只是开发信号，须后续独立完整wall才能讨论性能。方法选择与终测分开；最终日期deadline保持21:00，本会话最迟11:14:29安全交接。

## 执行、预算与验收

每集3图×22048实际路由；与同query原P完整三入口相同者仅复用原NSG返回，route NDC每次重算，变化者真实搜索。每图64query三路parity额外192 NSG/128 HNSW。每集最多44672 NSG、66528 HNSW、3build，预留45000/集，总90000 NSG/134000 HNSW/6build，失败完整预留、不自动重试。新GT0、梯度更新0。旧44096基线返回生成成本不当零。

单native CPU15、实际进程与OMP/BLAS/MKL/NUMEXPR/BLIS1；查询和重分析串行，全部工具terminal实际退出后才启独立分析。单集native600秒、10:55停止启动、11:05停止新增查询；根文档同步和handoff在11:14前。阶段≤192MiB、free≥7GiB、RSS≤32GiB，使用E61输入路径避免复制大文件。所有源/输入身份、root source_before、完整W/物理图/返回/patch/计数保留；绝不删除旧产物。

验收：独立集合重评分原20K zero-hit身份、随机集合重放、总质量与raw prior恒等、原A0/P逐字恢复，独立逐rank流式聚合六W，132288输出与mask/缓存键、六物理图全字节、384三路parity及cal规则重算。开发操作wall分构建/route/NSG/缓存/评分/I/O，不当QPS。本阶段不打开最终反馈。

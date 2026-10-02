# E89：真实效用筛选的局部父画像恢复

2026-09-13第10独立串行会话，前瞻协议。E77全局半收缩同时消除旧收益与旧损伤；E87/E88说明有用完整策略中的目标hub往往没有现画像前三资格。本版从另一端干预：只对有限的竞争子画像组恢复原父P，并用实际完整三入口NSG效用选择。不是再加边、全局alpha扫描、低ESS剪枝或完整策略差的单hub信用。旧门保持。

固定E73 compact的1771/2067个slot、815/821真实hub、原父P、映射/顺序、所有层邻接/层级/入口、ef10/七slot去重3、原NSG/base/rawIP/L128/K10。每个动作选一个有两个子画像的hub，把两个子行逐字复制成该hub原父P；父行和其他hub不动。不删除物理slot，不重建图，不声称画像评分或路由单调；重复P会改变近似遍历，全部作用都计入实际响应。最终线上仍一份静态画像小图→三真实入口→原NSG，无在线模型/额外归一化。

候选只用冻结fit20K router_train[10000:30000]、E66原P与E86原compact完整响应和compact七slot。对P_hits>compact_hits的query，取compact前三中的P未选hub；仅当实际代表它的首返回slot为非父子画像时，对该hub记一票、权重为完整策略命中差。每hub独立query支持>=2，按总权重降序/真实hub ID升序取最多32个，两个子slot一次同组恢复。完整策略差只作提议，不作信用。所有query/事件/分数差/完整三入口/候选、未入选原因先保存，候选名单在新ANN之前冻结。记录被提议子画像相对同hub父P的原raw-query分数提升及非正/近界，但不据此新增筛选。

逐候选独立从原compact开始恢复两行，全20K原生plain/count路由，逐query七slot/距离bits/三入口parity；只按query字节/namespace/source row/完整canonical三入口/冻结NSG/kernel/rawIP/L128/K10/GT身份精确复用NSG，所有新键执行count/plain。route NDC均重新测量。每动作接受门：全fit净命中>0，固定两半10000各>=0，zero失败不增，总NDC<=原compact1.01。全部合格动作同时提交一次，不按合并反馈回删/重选；真实测全fit合并结果、相互作用与原收益/新损伤。

固定对照：从全部双子画像hub中，排除主臂已选hub，用PCG64(20260913)排列取同数量hub作同样父恢复。对照在其任何响应前冻结，主臂选择不读取对照结果。控制匹配恢复hub/子行数和所有非向量图字节，不匹配训练支持、原画像位移或query损伤；不能单凭主控差宣称标签的纯因果作用。零接受时主/控为明确的原compact零更新副本，不作新方法收益。

原compact全20K返回须回归E86；32query count/plain/reference回归原kernel。第一候选保存物理W/graph并在128query恢复内存动作全部route字段，然后在恢复后的内存图再次测128query等于原compact，检查动作撤销/重复调用没有残留。最终主/控全W与物理图向量逐字验证，覆盖所有非向量bytes不变；所有新返回集合独立重评分，完整缓存来源、单动作patch、routeNDC、拓扑身份与调用账保存。

双集全部模型/训练验收并冻结后，aux7952 router_train[2048:10000]只作本版本接受。五配置P、compact、E84 shortcut参考、主恢复、随机同数量恢复；128预检后全7952，timing_repeats=0。主臂需有非零恢复、合并fit接受门通过；aux对P及compact全净命中>0/固定3976两半各>=0/失败不增/总NDC<=+1%，对随机控制全/两半净命中>=0且失败不增。E84差异完整报告，不据其结果变规则。至少一集通过才另立同批完整双集五L五轮wall协议；均失败就停止此候选/动作/筛选规则，不改幅度、32上限、阈值或seed。质量通过仍非性能GO。

训练输入含旧4096train/1024monitor，aux及两半/cal/audit已历史暴露；任何接受/诊断反馈计训练信息，不称独立未观察泛化。E34历史validation2000原query/GT/row及held-out本版本不打开。最终完整对照另立协议，最终反馈不得回流。

预算：双集最多64动作；每集baseline+32动作+主/控各全20K双路，1400000HNSW，另第一动作物理128双路与恢复128双路512；训练HNSW<=2801024。每集新NSG硬限32768，含32×3原kernel回归；双集合65536。aux五方法含128预检/7952完整plain/count+每点16原kernel，161920NSG/161600HNSW。总NSG<=227456，HNSW<=2962624，无新GT/普通构图/梯度；2离线效用筛选拟合、最多6物理向量安装（2首次动作回归+4主/控）分别记账。失败保留全预留，禁止自动查询重试，超cap在下一批前停止。

串行CPU15、进程及OMP/BLAS/MKL/NUMEXPR/BLIS1，主环境CPU-only，RSS32GiB。训练job每集1200s、查询job600s；18:40停止新增训练job，18:55停止新增aux job、19:05查询硬停，19:21:48会话安全退出。阶段128MiB、session10累计192MiB，另晚间64MiB/交接8MiB，新floor6.45GiB；实际free约6.76GiB，预留全部剩余输出后仍约6.50GiB。大输入引用，只/data写大文件，所有旧封存/未提交代码不改不清理。

完成后保存完整失败query并集/GT10/入口/返回、训练与接受图、费用及限制；history78→s-experiment→summary/s-target，新增离线接口同步spec。每阶段根文档source_before/root_after、freeze/state/handoff和工具实际terminal状态保持。整日20:00停训练、20:40停新query、21:00交付，当前完成不等于整日目标完成。

# E66 单小索引的 GT10 多画像（前瞻协议）

2026-09-13，会话3；在画像训练/新ANN前冻结。唯一写入者串行运行，12:13:18前交接，整日目标未完成。固定原base/raw-IP/NSG/GT/H815或821。动机是检验多个query方向能否补足单画像表示；共享画像冲突与两个真实模态尚未证实。已追溯history04、旧E10设计/builder/router及train10K结果：旧GT1硬盆两模态只在原top32内重排，额外64点积且无完整单线程wall。本版本用当前GT10归属并直接在3H索引查询，不换名重跑旧runner，不宣称新颖性。

## 冻结构造

仅P-fit20K=router_train[10000:30000]训练。unit-query Q、unit-raw-hub R和原GT10 hard(Yandex)/soft-t1(WebVid) A逐字恢复E63的原assignment SHA；原P=unit(R+A^T Q)逐字恢复。保持每query质量1，不读取NSG收益训练画像。Web dense A全量保留，不截断小权重。

每hub父质量 M=sum A，ESS=M²/sum A²；M<8或ESS<16时两新增slot均逐字复制P。其它父hub固定20轮加权球面两均值。初始化seed0=argmax_q A_qh*(1+Q_q·P_h)，seed1=argmax_q A_qh*(1-Q_q·Q_seed0)，并列按fit源行升序。每轮按Q·center最大分两类，平分归0；center=unit(sum assigned A*Q)。空类/零向量保持原center并标记退化，最终整hub回退。20轮后的最后分配用于输出，不以开发质量停步。

子质量 M_m及ESS_m单独计算；任一M_m<2或ESS_m<8，或曾有空/零类，整hub两slot复制P。合格者S_m=sum assigned A*Q，rho_m=M_m/M，新增画像U_m=unit(rho_m R+S_m)。两个新增slot的query质量合计原A、raw prior合计1；另存原P是额外冻结画像，不能声称三个slot总训练质量等于原单slot。无log-prior在线偏置；合格子画像均unit、等候选地位，这是预锁模型选择，未隔离随机分群或质量偏置效应。

三方法：原P/原物理图baseline；每hub三份P的duplicate3P容量控制；原P+两模态的mode3P实际候选。slot顺序为hub升序、每hub[P,U0,U1]，外部label为唯一slot j，mapping[j]=真实hub，tie_ids=j。mode的首slot和所有退化slot逐字为P。每hub恰三slot，physical count=3H2445/2463，unique real count=H815/821。

## 在线与接口验收

新Policy独立版本，原hnswlib/NSG不改。M16/efConstruction200/efSearch10/seed20260828；一张小图searchKnn(raw_q,7)，7个不同slot按distance升序、同分slot ID升序排列；按真实hub首次出现去重，前三hub最终按真实ID升序输入原NSG，L128/K10。7个slot且每hub最多3槽保证至少3个不同hub；不足7、越界/非法映射、容量合同不合即拒绝，无隐式补搜。原单画像与Fast legacy分支保持原逻辑。图加载需验证所有坐标bytes和slot/真实label两种合同，包括count重载；不能按W重建代替物理图。

合成验收覆盖重复/ties/非法容量/小样本拒绝和序列化前后路由；两个数据集各128个fit query、三方法plain/count+每方法16原kernelparity；baseline对E61原返回/入口/两NDC逐位恢复。所有7slot距离/标签及最终三hub导出供独立去重重算。新输入input_total_rows声明完整原文件长度，再只取明确前N行，避免复制大输入；未经声明不得默默截断。

## 数据角色、开发规则

完整fit20K与历史aux7952=router_train[2048:10000]各跑三方法；aux两半3976/3976均已用于E64动作/模型选择，属于辅助选型训练反馈。P-fit含旧train4096/monitor1024；旧cal/audit历史及今日使用，不称盲测。本阶段不新增cal/audit查询，只读取复用容器内字节并明确截取前20K。Fast30K/E10已用这些namespace行；不得称项目未观察。E34历史validation2000与held-out均不进入新输入、选择、训练或评测。

mode3P唯一候选，duplicate仅机制控制不推荐。进入后续性能候选门：fit净命中>=0；aux相对baseline净命中>0、固定两半各>=0、零命中失败数不增、mean totalNDC<=baseline*1.01。另报告相对duplicate的全量成员/净命中/失败变化，若未胜duplicate不得把增益归因于模态信息。门失败停止此固定容量版本，不扫阈值/簇数/种子。局部正值与损伤保留；门通过仍只是开发质量信号，不能由NDC/同LRecall/操作wall给性能GO。后续完整QPS若执行必须另立协议、含NSG/Fast/GT10匹配起点与实际新候选同批多L多轮。

## 预算与保护

查询全新plain/count，不套用缓存预算：预检6方法点*(2*128+16)=1632 NSG；完整开发双集3*(2*(20000+7952)+32)=335616，合计337248 NSG，HNSW336960。正常4个新3H图构建、2个baseline源图加载；后续12个方法点加载预检物理图。失败完整预留，NSG硬限350000，额外技术修复需留原件并另记预算，不自动重试大job。合成小图另限8build/1024路由/0NSG。无新GT/梯度。

新目录累计<=128MiB、free>=7GiB、RSS<=32GiB，不复制base/NSG/大输入，不删除任何旧产物。聚合CPU8/数值库1线程，最长900秒/集；全部ANN与查询CPU15、显式threads1、OMP/OpenBLAS/MKL/NUMEXPR/BLIS1，单个被测方法，无并发训练/评分。查询job最长900秒，11:50后不启动新job、12:00硬停新增查询；12:13:18前封存/交接。记录实际进程线程、原生调用与构建/加载/评分/I/O分项；开发操作wall不是QPS。

先保存根文档source_before，再冻结源/协议/输入/模型。所有raw返回、7slot/三真实入口、距离bits/NDC、训练support/分配bits/两mode sums、图/源码/命令/hash保留；独立集合评分、原baseline恢复、图bytes、去重、质量/先验守恒、plain/count/原kernel均验收。完成后更新详细历史、索引、summary、s-target和spec接口合同，保存root_after封存；主要子阶段后读supervisor_notes。E65及所有历史封存保持，晚间20:00/20:40/21:00截止不变。

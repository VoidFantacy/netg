# E30 等效三入口集合监督：执行前协议

2026-09-11。用户授权依次执行多集合教师、单教师对照、漂移控制、真实检索及最终Recall–QPS择优。独立版本，不复用E29剩余预算。原raw-IP、base、NSG/kernel、H815/821及原GT10 hard锚点不变。fit/cal/audit/validation均有历史使用；本地探索，不读取或hash held-out。

## 1. 标签与可接受集合

复用E28每集fit20k×56个C8完整三元组的真实L128/K10标签，合计224万逻辑标签；绑定图、query/GT/row IDs、H、入口升序、kernel身份，并从原始top10 IDs全量复算hits/masks。

每query的G包含所有“hits为C8最高，且在最高hits组内graph NDC最少”的完整三元组。没有成本容差；相同NDC不等于相同wall。原唯一教师T0须属于G，仍沿用原score/realID打破并列规则。输出G的56位mask、唯一教师槽、原实际GT10槽及有/无额外命中空间组。统计整体及两组的等效数量、命中/成本分布。候选外组合未知，不用0填效用，不作为已知负例。

## 2. 仅改变可接受集合的两次训练

共同W=normalize(P+AP)，无偏置共享linear，A=0初始化；P为原GT10 hard。z=unit(q)W^T/.05，F(S)=sum(z_h,h∈S)。已标注竞争域C为完整56三元组。

对可接受集合族A_q定义：

`ell(F,A_q)=max_{S∈C}(F(S)+.1*1[S∉A_q])−max_{T∈A_q}F(T)`。

single使用A_q={T0}，multi使用A_q=G。两者相同竞争域、margin、模型、优化器、全fit样本权重和预算。该损失等于best-known-bad与best-accepted之间的hinge；若所有56均可接受则损失0。损失≥.1×C内argmax不被接受的指示量；零损失使C内最优被接受。保证仅在C内，不保证全H精确top3、HNSW或NSG。multi包含max减max，不能声称凸优化/收敛保证；它允许任一好组合，不强迫所有好组合都取得高分。训练不混合成员频率，不新增在线重排。

float64、Adam lr.003、全fit梯度累积batch1024、λ100×mean_h||W_h−P_h||²、80epoch、最后epoch、seed20260911、CPU8。每集single/multi各一次，共4次训练，无模型/seed/超参网格。记录81个目标/梯度/漂移点及每10epoch的完整组合接受率、候选内实际hits/NDC、全H精确top3落在C8的比例和已知部分效用；后者明确条件子集，不能外推未知集合。全部模型在新开发查询前冻结。

## 3. 漂移匹配

两份原生导出W分别量D=mean_h||W_h−P_h||²；共同目标min(D_single,D_multi)。仅由fit模型/锚点确定，在改动较大者的normalize(P+t(W−P)), t∈[0,1]上二分80次，导出float32并核验目标误差。改动较小者保持原始字节，matched身份alias原模型，不制造第二次独立实验。一般每集3份唯一W：single、multi、较大者matched。控制匹配全H均方弦长，不匹配逐hub漂移分布/梯度/入口变化；缩放后W是可部署静态画像，但不声称仍由同一A精确产生。

只有不可分辨的原生漂移时不创建冗余控制；最终manifest记录canonical aliases。不得根据cal/audit或QPS选择t。除该固定漂移控制外不增加优化步骤或候选。

## 4. 数学与实现验收

训练前独立小域枚举验证损失、非负性、C内错误上界、单/多集合、全接受、分数平移不变性、并列与有限差分梯度。训练后独立NumPy读取state dict复算A/P/W、单位化、两种损失和全量最终训练统计。独立复算漂移控制系数/导出与alias。保留模型及输入hash。

新评测器复制E29源码，只将reps合同的3替换为5，原timing循环/Policy/kernel不变；使用原编译参数和已保护依赖独立编译。源码差异必须逐字核验。真实结果的plain/count/旧wrapper、重复五轮和旧方法回归提供部署验收。

## 5. 依次真实检索与停止位置

开发方法为GT10 hard、E29 cost_margin和所有本轮唯一W（通常共5）。fit20k×L128；cal1024×L64/128；audit1024×L64/128，另全部方法L128 exact3诊断。诊断没有QPS。读取GT在raw输出完成之后；最终全量输出独立GT评分，实际入口与C8标签逐query核对，不只报告已知子集。

事先锁定研究推进条件：multi相对GT10 hard须两集fit L128净Recall各≥+0.20pp，且平均graph NDC增幅≤1%；相对共同漂移single在两集fit净Recall均>0；cal/audit两个split各自平均L64/128的Recall变化在两集均>0。任何不满足就停止进一步优化/容量扩展，报告发生在哪层。这是本轮有前作信息的资源门，不是普适统计定理。独立bootstrap区间另报，不能借区间/小样本替换预设条件。

用户明确要求最终画图择优，因此不论上述门是否通过，已冻结有效模型与指定基线仍完成本轮最终曲线；不借负结果扩模型或反复试到通过。

## 6. 正式Recall–QPS与最佳方法选择

validation2000。同批比较NSG、Fast30K、GT1 hard、GT10 hard、原冻结GT1 soft/GT10 soft、E28 MLP_r10、E29 cost_ce/cost_margin，以及本轮最多3份唯一W：最多12方法×L64/128/256/400/800×两集=120点。每点5次完整独立warm/plain单线程wall，预定顺序轮换，所有轮次保留。GT10 hard及本轮W的L128另测route/graph组件，不能相加作端到端wall。GT10 hard+E29 margin+本轮W作主图，全部12方法另图。

每次一个方法，正式CPU15/实际进程与OMP线程1，OMP/BLAS/MKL1，不与训练或重分析并发。timer含raw query→一份Micro-HNSW direct3→真实ID排序→原NSG→预分配输出写入；GT、count、I/O、hash、建图在外。matched模型HNSW M16/efConstruction200/efSearch10、seed20260828、真实ID升序，Fast30K保留seed100/legacy heap。五L入口及微型图身份一致。

预设召回参照WebVid .75/.80/.85、Yandex .90/.95/.98。只在实测非支配曲线上插值Recall–logQPS，不外推，不称精确等Recall实测。分别报告每dataset：所有方法相对原冻结默认（WebVid GT10 soft、Yandex GT10 hard）的各目标速度比/几何均值，描述性最快方法，及有证据支持的推荐方法。默认替换要求三目标共同覆盖，其中至少两个目标中位QPS≥+3%，所有五轮对应插值比均>1，且其余目标无≥3%退化；多个符合者依几何平均速度比、较小最大退化、预定方法名字序择优。无符合者保留默认，不把几千分之一速度排序包装成赢家。补充每L非支配集合及用户可据目标Recall选择的区间。这里的选择是历史validation上的探索性比较，不是独立盲测确认。

## 7. 预算与产物

诊断点2N+16，五轮正式点11N+16，组件额外2N。最多fit400160、cal41280、audit61920、validation2641920+32000，总正常上限3,177,280原NSG调用；只在唯一W不足3时按实际矩阵减少。实现修复另留10000，总硬3,187,280；失败job全预留计入，不借历史余量。无新训练标签/合成NSG。训练4次；目录≤1GiB，free≥10GiB，RSS40GiB，单job2000s，总query进程5400s。

产物：协议/方法研究、标签等效分析、4次训练/漂移控制、原始结果/五轮wall、分组损失与收益、开发门、候选内与部署差距、Recall–QPS主图/全图/选择参照、PNG/SVG/CSV/XLSX、明确最佳方法及不确定性、独立最终验收。同步历史19和s-experiment，再更新summary/spec/s-target，保留旧文件与全部旧产物。

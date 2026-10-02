# E52：完整反馈有限候选择优提交连续对照

2026-09-12。E50双集通过预锁接续门：E47原RL有净正候选却确定均值命中全空的比例WebVid86%/Yandex96%。本轮大胆假设：将已经真实测到的有效候选直接提交，能把部分局部机会转成连续静态画像收益。必须连续运行真实新状态和监控，不能累加旧反事实冒充训练。该方法明确是贪心局部搜索对照，不称新的RL；它隔离原梯度/Adam均值转化算子，用户提出的离线构造静态画像方向仍保持。

两个原dataset×原RL的两seed20260921/22，共4run；每run200步×8候选，原GT无关hub日程与逐seed Gaussian ε逐位沿用E47 RL，σ.3、原P/B/scale/H×16局部表示、H815/821、raw IP、HNSW普通builder/seed/ef、排序三真实入口、原NSG/L128/K10不变。每步action=当前该hub系数+.3ε；与原RL一样真实评测全部八候选，候选系数可越界，但提交候选必须全部系数在±2内，不动永远合法。以原完整J=mean U−mean画像漂移，在合法候选+不动中最大者提交，平分先不动再原候选序。不增加未知半径、不依monitor选动作；无Adam/动量，提交系数即已测action。

完整train4096为唯一每步反馈。所有候选真实普通build/route4096，按同query/完整排序三入口/原NSG/IP/L/K精确缓存返回，不变者复用、变化者新原NSG；每次route NDC真实刷新。提交后当前W/系数/完整缓存全部替换为该候选（不动则原C），再真实build一次提交W，拓扑SHA必须恢复相应已测身份，不额外route均值。新状态下下一候选全部重新route，绝不用E47分岔后标签。逐步J不减；实际命中可有正负，全部gain/loss保留。

每run冷启动实际4096并恢复原基线。step0/20/…/200各1024monitor真实查询，固定同E47选择规则：非零checkpoint中graph NDC≤+1%者monitor平均U最大（相同值较早步），无可行则用非零最高U并标记不可行。train512只从当前全4096缓存提取作兼容展示。全checkpoint保存W/系数/更新计数和train4096+monitor1024返回；selected与last普通HNSW/W导出，各32train+32monitor三路parity。0 cal/audit/原validation/held-out训练反馈，0新GT。原query/GT输入文件物理含历史monitor，只有上述固定监控调用使用该部分。

## 预算和核验

每run普通build=1冷+1600候选+200提交身份恢复+2导出=1803；HNSW=6553600候选+4096冷+11264monitor+256导出parity=6569216。NSG固定15744+实际候选变化query；每run完整预留100000，4run总硬限400000，失败不释放、不自动重试；native每dataset cap200000/HNSW14000000。合计6400候选、800决策步、7212普通构图、26276864 HNSW，固定NSG62976加实际候选变化query；结束按原生计数精确记账。

CPU15实际进程/OMP/BLAS/MKL1，dataset/seed串行。每dataset≤1800s、RSS<32GiB；artifact≤256MiB、free≥8GiB。新阶段资源合同独立，未删除原资产或调整文件系统保留空间。启动前以E47同RL两seed的实测时长之和×1.5+300s估算双集，必须能在21:10前结束；21:15后不启动新训练，21:35硬停止训练、21:40停止新查询，22:00收口，保留用户最终比较窗口。

保存6400候选W/拓扑/完整route NDC与变化patch、原J/合法mask/choice/提交身份、完整状态hash和44checkpoint/8导出。独立重建全部缓存、集合评分变化返回、原J择优/no-op/tie/边界与候选Gaussian/画像公式、逐query提交命中差守恒，提交图hash恢复和三路parity，源/输入/E37–E51全SHA保持。0原梯度更新，决策步与实际非空提交分开记账。

## 结果与接续

保留每run所有checkpoint，报告fulltrain/monitor的gain/loss、Recall/失败、U/成本和J曲线。连续提交是否优于原均值以新真实轨迹和独立query为准，不能把E50反事实1207/409当预期最终净增。至少每dataset一个可行selected monitor Recall正值才称具备双集候选信号；这不等于性能GO，也不因单seed/单点正值宣称稳定RL优势。无论结果正负，最终按用户要求冻结最佳候选并与NSG、Fast、FastGT10-hard同批比较QPS/Recall/失败率，候选按cal预锁规则选择，不用最终audit改选或回流训练。若原GT10仍更好，照实报告。

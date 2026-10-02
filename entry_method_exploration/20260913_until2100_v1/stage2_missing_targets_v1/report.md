# E61：遗漏GT10成员驱动画像重构

2026-09-13，`COMPLETE_MISSING_TARGET_DEVELOPMENT_NO_CAL_GO`。新画像有广泛作用，但预锁cal门双集失败，固定选择均为原GT10起点。audit的局部正值保留，不回流改选；默认没有替换，也没有正式QPS结论。

## 实际方法与控制

由完整P-fit20K的冻结基线真实返回识别未命中的GT10成员。每query将原GT10归属与遗漏成员平均归属各混合一半，再按原unit-query聚合和raw-hub先验重建画像。每query总质量仍1，lambda只固定0.5。WebVid沿原soft、Yandex沿原hard归属；H815/821、三个真实入口、原NSG/base/GT/IP不变。另建同query相同遗漏数量、随机目标身份的sham对照，sham不参与部署选型。

它与E08全H单入口赢家、E09 signed单入口效用残差/难度权重、E22自由slot映射有实质区别，但属于现有画像聚合方向，没有新颖性结论。E09原WebVid微弱正信号保留。本轮不把“实际遗漏”误称为可搜索入口的无偏教师。

原A0 assignment SHA及P字节恢复全部通过；原P、missing、sham六画像在新查询前冻结。E33全部40K fit缓存与E60开发基线44096行被明确复用，当前原生全量路由及64行/图三路parity验证。旧fit、cal、audit均历史使用且E60刚查询过后两组；没有盲集声明，也没有读取E34最终validation作为输入或选择反馈。

## 同L128实测

下面均相对当前匹配GT10起点。失败为top10与exact GT10交集为0，hits=1不算失败。

| 数据集 | 分组 | missing ΔRecall pp | 增益/损伤命中 | 零命中数 | totalNDC变化 | sham ΔRecall pp |
|---|---|---:|---:|---:|---:|---:|
| WebVid | fit | -0.1020 | 1050/1254 | 348→377 | +0.253% | -0.0885 |
| WebVid | cal | -0.3906 | 49/89 | 22→25 | +0.235% | -0.0098 |
| WebVid | audit | +0.0195 | 53/51 | 11→12 | +0.037% | -0.1367 |
| Yandex | fit | -0.0260 | 504/556 | 311→315 | +0.001% | -0.0160 |
| Yandex | cal | -0.1465 | 13/28 | 16→19 | -0.199% | -0.2344 |
| Yandex | audit | +0.0684 | 24/17 | 19→19 | -0.048% | -0.0488 |

cal按净命中>0、失败数不增加、totalNDC≤+1%预锁选择。两数据集均因前两项失败而保留原P。audit的+0.0195/+0.0684 pp不改变这一选择。所有历史开发的paired bootstrap只作描述，见points.csv，不构成项目盲测显著性或正式方法GO。

真实遗漏相对sham：WebVid fit/cal/audit为−0.0135/−0.3809/+0.1563 pp，Yandex为−0.0100/+0.0879/+0.1172 pp。目标身份没有产生一致增益；sham与真实模型的画像位移不同（WebVid均值0.0351/0.0507，Yandex0.0506/0.0602），这个对照不能排除位移尺度影响，但不据此追加强度网格。

## 收益为何仍被抵消

本次已改变全部815/821画像，missing的fit入口变化8284/20000和5602/20000，cal入口变化417/1024和295/1024；作用不再局限于少数随机动作。但fit净Recall已为负，不能把全部问题归于跨split迁移。

按原基线命中分组：WebVid全命中5540条损失191命中、部分遗漏14112条净−235、原零命中348条增222；Yandex为全命中12506条损失224、部分遗漏7183条净−105、原零命中311条增277。原全命中query中有14/20条变成零命中，分别贡献140/200个损失，少量灾难性损伤仍很关键。

当m=0或10时，该query自身的归属按公式未改变，但共享画像及新HNSW仍改变其入口。原零命中群确有45/32条救回，不能抹掉这部分收益；同时它们并未得到独有的遗漏身份重权。部分遗漏群的新找回/丢失GT成员为WebVid1211/1446、Yandex385/490。成员周转与逐query净gain/loss是两个口径，仅净值恒等；分组本身尚不能区分画像评分与拓扑改变的责任。

## 成本、验收和接续

新增 28,484 NSG、133056 HNSW、6次物理小图构建，双集原生阶段含加载 34.190s；新画像聚合/assignment阶段8.617s，独立数值验证15.799s，身份hash与数据准备另计。历史40K fit标签生成成本不能当零，原专门标签wall未在本轮重测。0新GT/梯度更新/正式QPS。完整构建、route、NSG、缓存、评分及I/O成本见cost/build/verification；NDC和缓存比例不代QPS。

132288新输出及GT10 mask独立重评分、44096基线路由逐位恢复、完整缓存键、6物理图所有画像/拓扑、384三路parity通过。独立逐rank流式聚合复算六画像，最大误差≤2.99e−8；随机mask逐query重放、质量守恒与80000行成员差分恒等通过。原生均CPU15实际线程1，全部进程退出。

停止同公式lambda扫描。若继续，最小有依据的控制是固定当前missing画像与其新图，补S=(W_missing,G0)、T=(P,G_missing)两个交叉状态，检查原全命中群的关键损伤主要来自评分还是邻接；这是新的有限反事实版本，不是E61已完成结果，更不能由统计分组直接给因果归因。之后才考虑与归因一致的保护或表示修改，复查E48/E54避免重复结论。今日最终QPS–Recall/失败率交付仍留在冻结候选之后，整日目标未完成。

[协议](protocol.md)、[缓存与数据身份](reviews/input_audit.json)、[六模型构建](results/build.json)、[全部指标](results/points.csv)、[目标身份控制](results/target_identity_contrast.csv)、[query群组损益](results/fit_cohorts.csv)、[固定cal选择](results/selection.json)、[原生成本](results/cost.json)、[独立画像验收](reviews/profile_verification.json)、[输出验收](reviews/verification.json)、[三指标图](figures/development_metrics.svg)。

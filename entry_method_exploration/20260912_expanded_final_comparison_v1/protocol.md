# E57 加入纯构图RL后的最终候选比较（E56训练前固定）

2026-09-12，用户最终NSG/Fast/FastGT三指标要求的接续，原E55完整结果保留。E56协议已约定原17候选加本次2seed全部selected，故每集19候选，固定序为原E55池顺序后接E56 seed21、22，默认第一。不据E56monitor正负删候选，不据E55/E57最终validation改算法、seed、checkpoint。

所有19个冻结模型先独立fit128恢复，再同一既有cal1024原U/低totalNDC/固定序选best_all和best_new。保持完整38fit/38cal，新增88768 NSG；原17个cal返回/NDC必须与E55逐位恢复，新纯构图模型使用导出恒定P/实际G，不加载construction_W进入查询。

选择和最终矩阵冻结后，若某dataset的best_new源模型身份改变，则对该集全部基线和新候选重新同批测五L五轮；若选择身份未变，其整组最终矩阵完整复用E55已验结果及五轮原始时间，不重复测速，不在同一dataset内拼接不同批次方法。最终仍为WebVid五方法/Yandex四方法、45点和225已有或新增wall轮；每一组明确source-run，新的NSG总计88768+[受影响集25或20点]×14016，最大719488<750000。若两集都未改选，只新增fit/cal而0新性能点，最终比较仍由E55同组证据支撑。

方法身份、L64/128/256/400/800、单线程CPU15、GT全部raw后评分、完整plain/count/16原kernelparity、五轮wall范围、零GT10命中失败率、source namespace与向量隔离等继承E55合同；历史validation2000，不称新盲测。0新GT、0训练/held-out访问、0原完整validation访问；E56算法/超参在读取E55最终结果前已经留档，资源投影修正另存，不以最终表现再调。

原E55/E56/native/model/数据全SHA保护，原17模型/源split不重建。每job≤1200秒/RSS32GiB、新artifact384MiB/free7GiB，方法和dataset串行，分析CPU8不与native并行。21:15前准备最终比较，21:40停止新查询、22:00收口。独立全部现有/新增返回集合评分、命中mask/失败/收益损伤、cal选择/冻结、来源组一致、线程计时计数和CSV/曲线。新实际计数与继承历史计数分开，默认配置不自动替换。

# E67 多画像方法与容量控制的完整开发wall（前瞻协议）

2026-09-13，会话3；E66已完成并封存，在本阶段查询前冻结全部方法/图/输入/矩阵。E66 mode3P相对P：Web fit−496、aux−106且失败+13；Y fit+164、aux+49且失败−4，但aux两半−14/+63。两集原开发门都失败，保持该状态。模态相对重复P有改善，原容量/近似路由损伤仍需区分。本阶段测完整成本和失败曲线，不训练/调参，不借最终反馈制造通过。

## 固定矩阵

复用E66已验收同SHA evaluator，无新编译。真实新方法固定mode3P，两数据集均展示；duplicate3P仅同容量控制，不推荐。WebVid六方法=NSG、Fast30K、GT10-hard20K、匹配GT10-soft20K、duplicate3P、mode3P；Yandex五方法=NSG、Fast30K、GT10-hard20K、duplicate3P、mode3P。每方法L64/128/256/400/800、五轮，共55点275wall。

原NSG/Fast/GT10沿E65冻结模型与图；新/duplicate直接加载E66预检序列化图，禁止按W重新普通构建。H815/821、base/raw-IP/NSG/GT固定。multi physical3H=2445/2463、ef10、一次searchKnn7slot去重3hub，最终real-ID升序；Fast legacy规则不改。配置best_new仅为固定新方法展示标签，非选型通过/推荐；best_all仍baseline。当前候选容量/权重/seed/ef均不变化。

数据逐字复用E65 source router_train[2048:4096]历史开发2048，属于E66辅助7952的子集，已用于历史开发与选型，全部反馈按训练/开发暴露披露，不称独立泛化。原fit20K含历史train/monitor，cal/audit历史使用。E34最终validation2000及held-out不进入任何新读取/评测/选择；晚间最终冻结对照仍待完成。

## 计时、结果与判断

全部ANN单线程CPU15，OMP/OpenBLAS/MKL/NumExpr/BLIS1。只运行一个被测方法；不并发训练、标签、ANN、重分析或大hash。一次完整warmup，五轮按dataset/repeat/L轮换；每轮独立整批wall包含raw-query路由、去重/映射、原NSG及预分配输出，GT/count/hash/JSON/build/load在外。plain/count/五轮返回bits以及每点16query原kernelparity独立验收；GT所有raw后读取。计数/加载操作秒不当QPS，未单测route/graph wall为null+原因。

全部aligned返回独立集合评分；失败严格zero GT10，保存救回/新增、GT成员增损和逐query净命中正负的区别。图含QPS–Recall、QPS–零命中率、按L三指标及失败query全五L；重复L/计时不当独立样本。slot候选/真实入口/物理图跨L保持，原基线全部五L恢复E65，mode/duplicate和匹配P的L128恢复E66相同query前2048。

本批只描述局部完整开发前沿；E66门失败不回写，不据中位小差/同LRecall/NDC/有限oracle给性能GO。全部实测曲线同批，不拼其它批次。报告相对matched P和duplicate两套比较；插值仅共同范围内明示描述性log-QPS。未改善照实展示实际候选损伤，最终选择不得回流E34反馈。

## 预算与截止

NSG=55*(7*2048+16)=789360，HNSW=645120（NSG方法无HNSW，880原kernelreference单列）。45非NSG图加载/复制、90 plain/count加载，0新建图/GT/模型训练。失败全额预留，NSG硬限800000，不自动重试大job。每dataset最长900秒；11:40后不启动新dataset，12:00硬停新增查询；12:13:18前安全封存/交接，不将会话完成写成全天完成。

阶段预算192MiB（45物理图副本占主要空间），free>=7GiB，RSS<=32GiB；实际累计输出检查，预留晚间空间。E66当前约108MiB已保留，禁止删除历史。主环境CPU-only，无并行CLI/子代理/外发/发布/推送/Codex配置改动。原始查询工具全部terminal退出后才评分；root source_before、代码/输入/模型/图SHA、实际线程/费用及root_after均保存。主要阶段后读supervisor_notes，结果更新history/s-experiment/summary/s-target，必要接口说明同步spec。

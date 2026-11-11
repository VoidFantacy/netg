# E191：七数据集、两K的来源与评分综合测试

2026-10-28用户要求“测试的全一点，给出详细的结论”，此前明确无要求不做PDF，随后明确授权本轮完成后制作PDF。本轮按后续授权交付详细中文PDF。七集真实K1/K100：原矩阵448点/1344完整T1轮；另一次密集控制541点/1623轮。112个SQ来源/预算点中，原网格66个通过探索筛选，密集同窗口后12个仍通过；默认E99 GT10保持。

保留密集控制后通过的对应数据/K/L/来源候选，先看实际费用、救损和跨点一致性；不等于全局默认替换。

覆盖COCO/Flickr/WebVid/Yandex/Deep/SIFT/GIST，原图/metric/GT10/GT保持。GT10、旧B32、REUSE-PQ/SQ、MAIN-SQ真实K1/K100；K1只一个主返回，固定K100教师前12K入口块表跨K共享。共享强弱沿E185旧观测，不构成人工因果分组。

REUSE-PQ/SQ逐query pool/扫描块一致，≤2048码/96追加原metric精算。MAIN-SQ无训练遗漏表，实际访问量也不同。SQ8全base无query/GT训练；新global PQ通常M16，Yandex适配M20。原矩阵不选超参，对表面阳性按协议一次冻结密集GT10控制并同窗口重测，原筛选/窗口保留，不混拼绝对速度。

全量actual timed包三轮bits/SHA、主包补全oracle、预算、源外/源内救损/严格失败和stdlib复算通过。140资格点、56历史前缀、训练表行及编码另核验。旧E190 seal保持；同执行者不同实现，非独立人员/新盲确认。大产物/root/acsg-e191-storage独立目录，实际timed返回原始字节无损tar+zstd归档，逐文件SHA往返通过，支持精确还原；trace无损gzip保留原SHA。

[完整文字报告](../entry_method_exploration/20261028_seven_dataset_scoring_v1/report_zh.md) · [全部原点](../entry_method_exploration/20261028_seven_dataset_scoring_v1/analysis/all_primary_points.csv) · [密集点](../entry_method_exploration/20261028_seven_dataset_scoring_v1/analysis/all_dense_points.csv) · [确认筛选](../entry_method_exploration/20261028_seven_dataset_scoring_v1/analysis/confirmed_screens.csv) · [协议](../entry_method_exploration/20261028_seven_dataset_scoring_v1/protocol.md) · [冻结](../entry_method_exploration/20261028_seven_dataset_scoring_v1/freeze.json) · [密集冻结](../entry_method_exploration/20261028_seven_dataset_scoring_v1/dense_freeze.json)。

[本轮详细PDF](../entry_method_exploration/20261028_seven_dataset_scoring_v1/E191_七数据集_K1_K100_综合测试报告.pdf)（用户后续明确授权）。

## 2026-10-29完成时的详细判断

结论是保留具体场景，暂不替换默认。七集真实K1/K100共989个计时点、2967轮完整T1测量，另有140资格点；覆盖较强共享观测的COCO/Flickr，也覆盖Deep/SIFT等弱覆盖情形。这里没有人为构造零共享因果组，新块表12K与旧B32的16K监督角色分别保留。

固定扫描下，SQ显著减少PQ筛选损失：K100/L200的COCO短名单覆盖2131→18747，WebVid为6320→22639。SQ保住99%以上扫描内遗漏，但不代表覆盖全部遗漏。Deep的168个短名单到返回损失均有相同向量的其他ID；严格GT-ID、并列规则和原metric均未改写。

弱覆盖场景确实能救回旧残差源外目标，但代价不能略去。Deep/SIFT在K100/L200分别救回913/808个成员，其中旧源外904/794；Recall仅增0.0913/0.0808pp，完整平均查询耗时增21.32%/18.63%，扫描仅覆盖原遗漏3.73%/4.42%。源外不等于从未受任何监督。

66个表面阳性经一次密集GT10控制，50个被覆盖、4个未过门、12个保留：COCO4、Flickr3、WebVid3、Deep1、GIST1。COCO的K1/SQ在L100/200/400有21.50%/32.64%/31.23%阈值速度优势；这是有限网格参照。Deep只多4个K1命中，GIST仅预算门通过，Flickr高Recall点也须看小计数。

再比较已有补全，12点中5点被覆盖：WebVid三点和COCO的K100/L800被B32覆盖，GIST点被PQ覆盖。其余7点未被已测方法覆盖，但B32仅有原四档L，尚无同样密集的费用匹配控制；不能宣称7点已经优于充分调节预算的B32，更不能称通用最佳。

严重失败修复有限。K100/L200的SQ使WebVid严格0–9命中查询53→40，Yandex为86→82；完整耗时分别增42.63%和81.94%。COCO虽Recall增1.8747pp，原1个严重失败仍未修复。MAIN-SQ有源外救回，但来源信息与访问量同时改变，不能当纯共享因果消融。

默认E99 GT10保持，本轮固定矩阵收口。后续先补已有B32密集费用控制，再用合法新查询/图确认；不自动追加实验。当前是一套图/画像、历史曝光测试，三轮只重复计时；无分段时间归因或总NDC。已复核的一处0.05pp浮点边界不改变选点及最终判断。

相对密集GT10保留的12点中，5点被同窗口已有B32/PQ的实测Recall与中位QPS共同覆盖；7点未被当前已测方法网格覆盖。B32仅有原四档补全L，没有密集费用匹配的中间L；未覆盖不能写成优于充分调节预算的B32或全局最优。

[全部已有方法覆盖核对](../entry_method_exploration/20261028_seven_dataset_scoring_v1/analysis/candidate_assessment.csv) · [存储合同](../entry_method_exploration/20261028_seven_dataset_scoring_v1/storage_format_update.md)。

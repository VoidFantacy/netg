# Fast 诊断：输入身份和源码独立审计

2026-09-08。用户当前已经授权实际诊断“Fast 为什么拿不到最好入口”，不开发新 reranker。本审计员仅完成只读源码、输入元数据与训练侧小文件身份核查，并写本审计和 `inputs/source_paths.json`；没有运行 ANN、训练模型、重建 prototype、构图或性能实验，没有打开原始 validation/held-out，也没有打开大 base/graph。当前 summary/spec 的 DESIGN_ONLY 是上一轮调研记录，不能覆盖本轮用户的新诊断授权；旧夜间状态仍不改变。

已重新依序完整阅读 AGENTS.md、summary.md、spec.md。本文所有路径相对 `/data/netg/ACSG`，机器可消费的绝对路径、格式、行维度、当前小文件 SHA 和大文件待核 SHA 见 [source_paths.json](../inputs/source_paths.json)。

## 1. 结论与尚未排除的问题

**当前只读审计没有定位到足以解释 oracle 差距的明确实现错误。** 现有 20K paired prototype、hub IDs、raw hubs、QGT 和 router_train query/GT 的完整 SHA 均匹配已有 P0/paired manifest；builder 源码也匹配生成这些 prototype 时的 SHA。还没有独立重算 20K 原型值，也没有在本审计中复测 ANN 或实际搜索结果，因此不能把这句话写成“实现已全部证明正确”。

已明确存在的代理目标差异是：Fast 拟合 top-1 GT 节点的几何 basin 查询平均方向；实际目标是原 directed NSG 的有限 L 搜索 Recall/NDC。它没有直接拟合真实搜索效用或 top-10 多目标，也没有训练图路径或有限 beam 行为。这是设计事实，不是源码写错的证据；它是否主导损失需由本轮实验分开验证。

## 2. 输入与已验证身份

既有审计根为 `hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/`。`p0/full_audit/audit.json` 当前 SHA 为 `7da975cbb0e045265f405b08e230abb6442eba51621064699a4ad449c90ae58b`，与两份 paired manifest 绑定相符。

| 输入 | WebVid | Yandex official first10M |
| --- | --- | --- |
| dataset | webvid2_5m_light_v1 | yandex_t2i_official10M_ip_v1 |
| base目录 | benches/datasets/WebVid2.5M_light_v1 | benches/datasets/YandexT2I_official10M_ip_v1 |
| base文件 | base.webvid2_5m.fvecs | base.official_first10M.fvecs |
| base形状 | 2,505,000×512 | 10,000,000×200 |
| router_train query | query.router_train.seed20260826.fvecs | query.router_train.fvecs |
| router_train GT | gt.router_train.seed20260826.ip.ivecs | gt.router_train.ip.ivecs |
| train形状 | query 30,000×512；GT 30,000×100 | query 30,000×200；GT 30,000×100 |
| QGT query / GT | query.aco_train.seed20260826.fvecs / gt.aco_train.seed20260826.ip.ivecs | query.aco_train.fvecs / gt.aco_train.ip.ivecs |
| QGT形状 | query 5,000×512；GT 5,000×100 | query 5,000×200；GT 5,000×100 |
| raw-IP口径 | source_unit_norm_no_additional | none |
| fit /历史pilot | router_train [10000,30000) / [0,10000) | 同左；不是原learn文件的绝对行号 |
| hub数 / 有20K分配数 | 815 / 802 | 821 / 821 |

以上小型 query/GT 文件都已经重算完整 SHA，并核查首行 int32 维度与总长度。fvecs/ivecs 每行均为 int32_le 维度头＋d个4字节值；GT payload为int32，DataLoader会转为int64，不能将文件直接当int64矩阵。

paired模型为 `p1/paired_fast20k/<dataset>/prototype.f32`，headerless float32、shape H×d；hub IDs来自 `fast_entry_variants/<dataset>_seed20260828/qgt_cover_hub_ids.bin`，headerless int32、shape H；raw hubs为同目录 `qgt_cover_hubs.bin`，headerless float32、shape H×d。三者完整SHA均已当前复核匹配。WebVid paired prototype SHA为`1d6481e5d8abdeb23634b3565bce840873a9a12cff0553b26138ce77c53bf5ae`；Yandex为`39c539d28c8a40c879a37dfeccc72a2a99b99ef26e4d38b35ed5e349e83c28f8`。

大文件仅记录当前stat和继承期望SHA，**本审计没有重新hash，也没有打开内容**：

| 大输入 | 期望SHA，继承P0 |
| --- | --- |
| WebVid base | 6fb5b5510b29504de38271be7c343bd5e85a029f5755c7b3d74177cbf1ebbb18 |
| WebVid graph `indices/webvid2_5m_light_v1_index/acosp_nsg.json` | 0a95d309b4980e0f0b73b7ad1222ec611db1f97c32ba2b69f070f5a952b9129a |
| Yandex base | 56d1baa271c79ea280d57ee1c7a8359438ffffc98a75cac799051b13fbdbe0ff |
| Yandex graph `indices/yandex_t2i_official10M_ip_v1_index/acosp_nsg.json` | fa6eb7dd4e8d9dc95d696947fc18bd167880fb336212cb7bd073e7acddd4bf2e |

root负责统一单IO身份核查。两个graph.info当前SHA匹配P0，不能用info匹配代替graph完整SHA。graph虽后缀.json，实际是原生little-endian二进制，内嵌base向量；偏移和格式头已从P0元数据收入source_paths。正式内存搜索只需loadACPG读取这个冻结索引，避免另外重复加载全部base。若提取hub/GT目标向量做代理诊断，再通过预定base或图内向量偏移只读，完整记录身份。

## 3. 原型公式与实际路由

`benches/run/build_fast_entry_variants.py:100–102,144–164,288–311` 的实际公式为：

```text
q_i^n = normalize(q_i)
t_i^n = normalize(base[GT_i[0]])
h_e^n = normalize(raw_hub_e)
z_i = argmax_e <t_i^n, h_e^n>
p_e = normalize(1.0 * h_e^n + sum_{i:z_i=e} q_i^n)
```

`gt`形参主要参与shape检查，实际目标向量在调用前用`router_gt[:,0]`取得。20K wrapper从router_train文件取`[10000:30000)`，见旧 `p0/build_paired_fast.py:48–61`。它复用独立QGT raw hubs；没有复用旧30K prototype。wrapper现在有已结束的deadline guard，不运行它来验证新诊断；独立数值重算如有必要写新审计逻辑，旧输出只读。

该公式没有明显的“漏除查询数”错误：最终还要单位归一化，整体除以相同正标量不会改变方向；prior与样本数量的相对权重为当前设计。没有被分配查询的入口保留raw-hub prior方向。WebVid 13个入口没有20K分配、最大242条/最小1条；Yandex全部有分配、最大82条/最小1条。稀疏画像或单均值是否不够表达，不是由这些计数单独证明的。

**paired Fast 在线没有显式归一化query。** `benches/bench_hierarchical_eval.cpp:198–204`直接将raw query交给FastRouter；`:214–217`的归一化只在非Fast的区域模型分支。FastRouter在`:131–145`用单位prototype、InnerProductSpace、M16/efConstruction200/ef10，真实base ID作为HNSW label。HNSW空间为`1−dot`（`benches/hnswlib/space_ip.h:17–18`等），对固定非零q，在实数下raw q·p与cosine具有相同排名。不能把“训练时单位query、在线raw query”直接判为bug；零范数、浮点舍入和同分行为另测。

设置文件中的`ef_search=200`并没有被这个Micro-HNSW路径读取；当前实际值为代码的ef10。测试时应分别记录模型seed、HNSW构建seed、M、efConstruction、ef，而不是照抄settings字段。

## 4. 搜索metric、入口消费和已知实现风险

| 检查项 | 源码事实 | 本轮判断 |
| --- | --- | --- |
| IP符号 | `ACSG/ACSG.cpp:33–42`对相似度metric用NegativeDistanceComputer；`faiss/faiss/impl/DistanceComputer.h:65–78`返回负IP | 搜索按距离升序与最大IP一致，未发现反号错误 |
| 原始向量 | `ACSG/IndexACSG.cpp:1297–1327,1355–1365` loadACPG按已存metric构造IndexFlat并直接恢复向量payload | 未发现该链对base再归一化；实际嵌入身份仍由root本轮核验 |
| HNSW顺序 | 旧`test.cpp:353–357`直接弹maxheap；paired `bench_hierarchical_eval.cpp:145`倒序写入 | 老路径有远到近输出；同三个唯一ID且无真实距离tie，kernel再排序，不能据此断言既有Recall差距由它造成 |
| 实际m | `ACSG.cpp:1517–1537`先截前三再visited去重，不从后续候选补齐 | 合法Fast3不受截断损失；m>3必须警惕静默丢入口；诊断需记requested/consumed ID |
| 同分 | `ACSG.h:35–37`Neighbor仅按distance比较；`ACSG.cpp:1565`排初始化种子 | 初始顺序/浮点tie可影响路线；新诊断应保留并核验排序，不改tie定义 |
| 非法种子 | 同mode2路径在vt.get前未完整验证ID范围 | 是包装层可防护的真实风险；目前没有证据说有效hub文件触发了它 |
| K>L | `search_new`取max(search_L,topk) | 旧非法K100/L64行不能用作L64结果；新诊断显式拒绝K>L |
| 邻接padding | loadACPG抽样日志把负邻居都叫invalid；实际搜索`:1581–1588`跳过负ID | P0记录的−1是padding，不应把warning当作图损坏或先修图 |
| 默认split | `bench_entry_oracle.cpp:296`默认validation；DataLoader在显式key存在时读取对应文件 | 绝不默认调用。当前训练数据key存在，显式drl_train可避开自动split fallback |

HNSW精确对照建议先使用同一个`InnerProductSpace`距离函数对全部prototype打分，以区分近似检索误差与SIMD/scalar/float64差异。另列scalar或float64参考很有用，但不能把边界同分/累加顺序差异直接认定为ANN算法bug。`hnswalg.h:1308–1326`先搜max(ef,k)再截断；ef10的top3/top8用同规模搜索池，是C8成本设计依据，不是C8效用覆盖证明。

## 5. 需区分的代理偏差假设

1. GT1→最近raw hub采用cosine，尤其Yandex的hub范数被消除；这与原始IP目标不完全同构。raw-IP GT正确并不保证该basin代理最合适。
2. 每个query仅用top1 GT定basin；Recall@10可能依赖多个GT目标及其在图上的可达性。
3. 每hub一个均值画像可能平均掉不同query模式；低样本或无样本hub依赖prior。不能从均值形式直接推出不可学习或必须多模态。
4. 即使exact prototype排名完全正确，分数仍优化几何画像相似度，未必优化有限L实际search；这种代理差异与HNSW近似误差必须分开。
5. 旧single oracle对Fast3同时混入入口数量/共享beam竞争；新诊断须先做同single策略比较，再解释single与triple差别。

这些项是待证的原因，不是建议立即替换损失、增加reranker或重启旧分支。没有一个既有结果能单独证明Fast rank0可靠、C8充分覆盖、或稍慢筛选能换来完整Recall–QPS收益。

## 6. 隔离编译与复用建议

新诊断可以链接现有静态库，避免修改CMake、旧源码或旧binary：

- `build/ACSG/libACSG.a`
- `build/MRNN_Descent/libmrnndescent.a`
- `build/faiss/faiss/libfaiss.a`

以上三库当前SHA/大小已记录于source_paths的link_reuse；mtime不作为源码一致性证明。原目标精确recipe在`build/build.ninja:4590–4615`：GNU C++17、O3、march=native、OpenMP；include根项目、faiss、benches及build内json/argparse；链接ACSG/MRNN/faiss、openblas/gomp/pthread/m/dl。可用静态库link group解决循环依赖，新编译产物只写`fast_router_diagnosis/20260908_v1`的专有目录。不要在此shell引入RoarGraph MKL/OpenMP环境。

新exe先`--help`，然后以受限训练query做plain/count与同kernel结果验收。`bench_entry_oracle`现成程序只适合参考已有graph-only诊断逻辑，不应把它的默认split或计时边界直接照搬。新实验需要完整路由wall时，使用新评测层的独立pure timer；query→oracle入口ID和GT必须留在离线诊断层。

本审计结束时：两份新文件已保存；小文件身份PASS；大base/graph SHA由root统一待核；没有打开原始validation/held-out、没有修改任何旧文件。

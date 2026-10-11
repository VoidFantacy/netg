# E176 实现与合同交接草稿

**SOURCE/CONTRACT ONLY；实测 Recall、QPS、费用终值、完整执行与最终独审结论均待填入。** 本稿只读取冻结协议和源码，不读取运行输出或质量、计时值，不能作为已完成实验、观察到双升或默认替换的证明。最终 spec/history 应由根代理在全部实际审计后补入结果与收据。

本轮保留 E175 的 base、原 NSG 主图、GT10 画像/Micro-HNSW、三入口 heap-pop 路由次序与原 M5 posting 身份。主搜索仍调用原 scalar `search_new(...,mode=2)`；NSG 用原单入口，GT10 及所有 M5 继承方法用原三入口。搜索、原完整 C 和最终合并均使用原 raw-IP 距离与原返回优先级，不改 GT、归一化、图边或 visited 行为。原 M5 的每行≤8、三行合并去原 R/重复后 C≤24，以及原 fresh R/C 评分版本，仍作为显式对照保留。[协议:7–13](../protocol.md:7)、[原 Posting](../src/runtime.hpp:28)、[原主搜索接线](../src/benchmark.cpp:460)。

| 固定方法 | 冻结实现与作用 |
|---|---|
| NSG | 原单入口主搜索，无 posting。 |
| GT | 原 GT10 三入口主搜索，无 posting；当前默认基线。 |
| M5 | 原完整 posting、fresh R/C、严格 Top-K 合并。 |
| M5OPT | 复用本次刚结束的原主搜索 R 分数字词，保存 posting 行→C 索引；最终包须逐位等于原 M5。 |
| M5REG96 | 原 M5 后，以原 C 的每行赢家作种子，按原 slot-major/route-minor 次序读取一跳原图，额外评分≤96。 |
| REGOPT96 | 原区域算法的费用优化：复用 R/行→C 映射，并截去已绑定种子图行的无效尾部槽；不压缩内部槽或改变候选次序；最终包须逐位等于 M5REG96。 |
| WIDE12 | 同剩余遗漏监督的 route-only 补全控制；每键≤4，额外候选总数≤12。 |
| M5RES12 | 以 `(route,原已评分 C winner)` 查新剩余遗漏表；每键≤4，额外候选总数≤12。 |

M5OPT/REGOPT96 的等价要求是 ID、距离字词、入口和 profile 字词完整一致。不能只凭内积公式声称 native 分数可无损复用：本次独立 untimed DC 必须对完整窗口每个 valid 主 R 字词再评分核准，且与本 K/L 的新鲜 GT 主包逐位对照；原版与优化版最终 full plain 包再分别逐位对照。失败停止版本。资格评分、trace、oracle 不进入暖机、正式 timed 或 count 调用；这些费用单列。REGOPT 元数据是非学习预处理，startup 与 resident 均披露。[优化缓存合同](../src/optimized.hpp:4)、[完整 R 核验](../src/benchmark.cpp:533)、[原版参考包门](../src/benchmark.cpp:1013)。

新监督为 `D(q,K,L)=GT_K(q)−原 M5 最终返回(q,K,L)`，继承旧合法 TRAIN/FIT20K 的 query、行号与既有 GT100；不是沿原 GT10 主包遗漏重新加宽旧 M5。每个真实 K1/K100 与五个 L 都实际生成原 GT10 和未优化原 M5 响应。原 C 先排除原 R、按三 posting 行的首次出现去重；每 route 赢家只从已实际评分 C 中选，距离相同时沿原 C arrival 优先级；三 route 的赢家不去重，可重复或稀疏缺失。[FIT 原 M5 调用](../src/fit.cpp:177)、[赢家审计](../src/fit.cpp:51)。

M5RES12/WIDE12 各 K/L 分表，仅用原 M5 成功提交 C 的训练响应（`fit_status=2`）；零残差但成功提交的 query 仍计键支持。每键至少两个 distinct TRAIN query，采用相同单位 `(query,target)` 残差 token 与确定性整数 greedy；覆盖状态在该 query 的实际三个 route 键之间共享。pair 键未命中纯空，无 route-only fallback。模型为排序的 little-endian i32 `N×7`：`route,winner,count,target0..3`，WIDE 的 winner 恒为 −1，空位 −1。在线原 C 为空即不扩展；否则保留完整原 C，按 route/新表行次序排除原 R、全 C 和先前 X 重复，支付每次实际新评分与严格晚到优先级合并。X 非有限时返回完整原 M5 包，已花成本保留。[编译器资格与联合覆盖](../src/compile_residual.py:124)、[格式/监督声明](../src/compile_residual.py:308)、[在线补全](../src/residual.hpp:63)、[独立 BANK oracle](../src/benchmark.cpp:295)。

WIDE12 是在线候选上限、单键容量、监督与拟合规则匹配的 route-only 残差控制。pair 可以有更多键，因而**总离线目标槽数、总表容量和 resident 并未配平**；pair 对 WIDE 的差异不能直接全部归因于条件键本身。最终须公开实际键/目标数、resident、lookup 命中和 C/X 开销；未加总容量配平控制时，不声称已隔离容量优势。表外候选、U 外救回或较大 TRAIN 覆盖，也不直接证明跨模态独有机制或未见语义泛化。[两类键与 greedy](../src/compile_residual.py:118)、[完整 resident 接线](../src/benchmark.cpp:912)。

用户明确允许本次每数据集额外≤900 秒，覆盖训练窗响应生成、加载/绑定、教师核验、标签解码、哈希、编表和保存等整个新增 FIT 生命周期；原 Web/Y 跨方法训练债务保留，不清零、不拆 K/L 重置，也不把编表称 0 TRAIN。外层完整进程实际费用是预算权威，内部阶段 elapsed 是其嵌套分项，不能重复相加。超时/异常保留 partial，未全量完成的模型不具资格。工程源码构建、资格烟雾、正式查询及后续审计另列，不恢复旧 runner。[明确授权和旧债](../protocol.md:3)、[FIT 上限](../protocol.md:21)。

冻结评测为两 dataset ×两真实 K×五 L×八方法，共 **160 点/480 timed 批次**；各点使用与 E175 相同、已曝光的公共前 10000 query，只有 `public_test` 一个角色，没有新确认集。每 K/L 先生成完整 GT plain，并完成各方法单次完整 native plain 和独立 fresh-word/linear oracle、主包与优化参考包核验，随后 warmup256、三轮固定旋转，最后固定均匀256的独立 count/plain 核验。原 REG96 全128-word trace；两 BANK 为20-word轻 trace，其赢家按原 route 对齐且允许重复；REGOPT 不另存 full trace。[矩阵与顺序](../protocol.md:17)、[single full plain](../src/benchmark.cpp:970)。

完整查询 wall 包含 normal Batch 分配、初始化、路由、DC/vt、原主搜索、所有 lookup/赢家/筛重/新评分/合并、输出及释放。加载、live 身份、资格核验、oracle、计数、序列化、GT 评价不计入 QPS 分母，但全部按实际阶段成本披露。正式 CPU15、实际线程1、同一时刻一个方法；NDC 只来自256样本。没有第二整批 native replay，不保存 timed 输出，不能继承 E175 的 full second replay 声明。[wall 合同](../protocol.md:23)、[证据范围](../protocol.md:25)、[输出字段](../src/benchmark.cpp:1095)。

最终交付仍待实际 160/480、800 离散比较、独立整数/费用/机制审计和曲线报告闭合。bootstrap 仅为描述区间；同 L 比较须将质量增量与完整 wall 费用分开，小 L 对大 L 只用真实预算点，不能插值推断。当前默认仍 GT10，本轮公共已曝光窗口的观察不授权默认替换或新确认。旧 E173/E174/E175、旧科学源/锁与停止范围原样保全。[分析与终点](../protocol.md:31)。

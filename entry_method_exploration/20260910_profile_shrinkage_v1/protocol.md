# E26：把新画像向旧画像收缩的单路对照

2026-09-10夜间。来源为用户在E25阶段的明确授权：详细深入分析，9月11日北京时间07:00开始汇总，提前完成可适当探索。E25已按原协议完成并封存，本版本独立回应其“少量质量修复不足以抵消双路成本”的观察。以下内容在任何新alpha画像、新cal/audit输入与搜索结果生成前冻结。

## 1. 问题、已有证据与区别

E25 WebVid DualGate相对A1的五L Recall有+0.025～+0.090pp，但QPS中位数下降约1%～6.5%；Yandex校准选择不稳定。最小追问是：能否在离线构建时减小改动，使在线仍只用一份W和一个Micro-HNSW，同时保留E24已有有效改道并减少受损？不继续加门控模型、特征或阈值。

固定A0=E24 matched Fast20K/GT1硬，A1=E24冻结主画像：WebVid GT10软T0.016201138496398926，Yandex GT10硬。对每个同一真实hub，构建

`W_alpha,h = normalize((1-alpha) W0,h + alpha W1,h)`，alpha仅为`{0.25,0.50,0.75}`。

输入直接使用既有float32 W的数值，内部float64线性组合与L2归一化，最终float32；不先重新归一化端点。恢复alpha0/1直接逐位复制W0/W1，避免归一化舍入改变端点。中间向量范数必须finite且>1e-12，不能悄悄回退或加新规则。

这是简单的画像插值/收缩控制，不主张通用插值机制新颖。旧E09 utility residual已由top32真实single Recall/NDC优势聚合signed query残差，并与旧Fast30K组合；已读历史04、原manifest、builder和原validation结果。本版本不使用那些标签/残差、模型或runner，只在E24两个几何画像间缩小位移。也不重启旧probe/C、多view、2A全H效用分组或E25门控。

原WebVid/Yandex base、raw-IP、NSG、QGT seed20260828、H815/821固定；同一hub一个画像、三个互异真实ID；M16/efConstruction200/ef10、seed20260828、真实ID升序固定。原Fast30K对照保留旧30K输入、seed100与heap顺序，不能混为matched A0。

## 2. 几何解释和不能假设的性质

对实际储存的W，混合向量平方范数等于`(1-a)^2||W0||^2+a^2||W1||^2+2a(1-a)W0·W1`；理想单位端点时为`1-2a(1-a)(1-cos)`。只记录画像位移/范数及每hub变化，不把混合画像的支持数或ESS伪造成新的独立样本。

连续缩小画像角位移不保证三个入口集合、有限beam命中或graph NDC单调。每份W重建其Micro-HNSW，原NSG不变。中间alpha产生第三套三入口，可能新增好query也可能新增坏query；不能复用E25二选一公式假定损失只是A1损失的子集。也不能将原A1命中差乘alpha当标签。

## 3. 数据访问与冻结

W只复用E24的fit20K画像，不训练新参数、不生成fit或全H/single标签。新的cal为原router_train[6144,8192)，2048条；audit为[8192,10000)，1808条，避开E25的cal/audit分段且均不参与E24画像fit。这些池在全项目仍有历史开发使用，不称新盲测。

端点恢复使用E24原cal前32条，仅用于身份回归。原query/GT100列宽、fvecs/ivecs header、原行与导出row IDs核验；cal/audit disjoint，且均<10000，不落入画像fit[10000,30000)。所有新画像及其输入/代码/binary身份先冻结，再读新cal标签；cal选定alpha与候选表全局冻结后才导出audit。audit只报告，所有3alpha及两端点都保留，不据audit更换。

之后才读取原历史validation前2000，五L和所有必要基线。E24/E25已看过该validation且启发本追问，明确披露；本版本只用于受限反证和端到端对照，不能升级为新盲测。held-out文件不打开、不hash、不评测。

## 4. 配对结果、收益与新增损失

cal/audit在L64/128真实搜索全部五份画像（A0、A1、三alpha），保留返回ID、距离bits、三入口、hits/mask、route/graph NDC。每point全批plain/count一致，前16条原kernel wrapper复核；全部raw搜索完成后才打开GT评分。

令`d1=hits_A1-hits_A0`、`da=hits_alpha-hits_A0`，合并两L为query×L事件，全部query保留分母：

- `R`：原d1>0事件中，da>0的比例。
- `Rh`：`sum min(max(da,0),max(d1,0)) / sum max(d1,0)`，只承认保留的原正命中，新增收益不替代丢失的原收益。
- `A_all`：`1-count(da<0)/count(d1<0)`，包括新产生的受损事件；可为负数。
- `Ah_all`：`1-sum max(-da,0)/sum max(-d1,0)`，包括新的或加重的损失；可为负数。

目标为`R>=0.75,Rh>=0.75,A_all>=0.25,Ah_all>=0.25`且`sum da>=max(0,sum d1)`。这与E25在纯A0/A1二选一时的四项比例一致，但现在对新增损失收费。另报告原受损事件被完全避免比例、原损失被削减幅度、原好query变坏、原中性query变坏/变好、原坏query被改善/加重及所有幅度；新收益与新损失不混在“保留”名下。某分母为0记undefined，目标不假定通过。

## 5. 三候选选择及停止规则

每数据集在cal独立选一个alpha：优先达标候选中总命中最高，其次受损事件更少、负命中损失更少、相对A0的入口集合变更更少、更小alpha。若全不达标，选最接近的alpha用于反证：最大`S=min(R/.75,Rh/.75,A_all/.25,Ah_all/.25)`，然后沿同一tie次序；记录`CAL_TARGET_NOT_MET`，不能说通过。

只有三alpha，无额外细网格、hub自适应强度、按query门控、按L选alpha、温度重选或模型融合。两个端点只作控制，不用全回退冒充选择成功。选择后两数据集全部W/候选表/alpha/hash全局冻结，再生成audit。无论cal/audit是否通过，按原计划完成冻结主alpha与四基线的小validation，以检验实际代价；不增加候选或样本来修饰负点。

## 6. 恢复、正式计时与所有成本

先合成fixture检查端点bit复制、中间画像数值/范数、零query、三个唯一ID、非法线程拒绝、plain/count/原kernel和三次wall一致；合成单独上限4096调用。真实端点恢复：2数据集×2端点×5L×32query，ID/距离bits/入口/命中/mask/route/graph NDC对照E25已恢复的相同行。通过前不生成cal搜索。

validation比较NSG、原Fast30K、matched Fast20K、E24、cal选定Shrink五方法，2数据集×5L={64,128,256,400,800}，共50点。每点三次独立整批warm/plain，按固定dataset/L/repeat轮换方法；全批count和前16条原wrapper均在timer外。原四条曲线必须与E25相同行逐位回归。每份画像五L选择及图身份相同。

L128每方法单独测route-only与graph-only，各自整批warm和wall，不把分项相加代替端到端。总wall包含raw query一次Micro-HNSW、三个入口升序、原NSG及预分配结果写入；画像读取/构建、GT、hash、计数、I/O在timer外。新方法线上没有第二份画像、特征网络或门控；实际路由搜索访问变化仍计入NDC/wall。记录新画像构建、微型图文件/构建、输入准备、完整子进程时间与RSS；原GT/QGT/NSG/E24从零成本未新测则null说明。

所有查询显式threads=1，OMP/OPENBLAS/MKL=1、dynamic=false，taskset CPU15；核验实际OpenMP team及/proc线程。单次只测一个方法，不并发编译/训练/其它性能工作。固定warm-cache，不进行cold-cache清除。三次wall不是三个构建，也不增加Recall样本数。

## 7. 真实调用和资源硬上限

诊断point收费2N+16；正式三次wall点7N+16；L128分项额外2N。所有失败job按完整预留收费，原输出保留，不借重启扩预算。

| 阶段 | 正常NSG调用 |
|---|---:|
| 真实端点恢复，2数据集×10点×(2×32+16) | 1600 |
| cal，2数据集×10点×(2×2048+16) | 82240 |
| audit，2数据集×10点×(2×1808+16) | 72640 |
| validation，50点×(7×2000+16) | 700800 |
| validation L128分项，10点×2×2000 | 40000 |
| 正常总计 | 897280 |
| 仅身份/parity修复预留 | 16384 |
| 全版本真实硬上限 | 913664 |

单job≤1800s，真实查询进程总计≤7200s，RSS≤40GiB，E26新产物≤1GiB，/data空闲≥10GiB。触任一硬上限即保留已完成点并收口；身份、非法ID、非finite或parity问题先停依赖阶段，修复也不能改变协议目标/网格。E25已用预算完全独立，不抵扣或转移。

## 8. 交付与边界

保留所有三alpha开发正负点与冻结选择，最终五L两端点/原Fast30K/NSG/新画像的完整Recall–QPS、三次原值及范围、原收益保留/全体损失减少/新增受损分解、逐query结果、成本和修复日志。使用seed20260910的2000次配对query bootstrap作描述性区间，同query各L一起重采样，不用于回改选择。

首先按冻结目标检验cal/audit/validation的保留与损失减少，再分别报告同L双升、实际非支配点与三轮计时一致性。降低改道比例、只在cal好看、只提高Recall或减NDC都不构成完整方法GO。一个构建、历史validation和受限插值网格仅支持探索结论。

最后核对正常/修复/合成调用、线程、原资产/端点回归、冻结先后、GT后评分、五L不变，形成独立历史15和根四文档接续。E26收口后不继续自动展开alpha/模型/候选队列。整体夜间报告按用户指定于2026-09-11北京时间07:00开始汇总。

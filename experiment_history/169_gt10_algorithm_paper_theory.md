# 169 GT10具体算法与CCF B论文理论

2026-10-02，用户在16:00阶段收口后新要求“补齐一个具体的算法和创新点吧，或者完善gt10的理论，足以支撑发表B刊”，并确认B刊为CCF B类期刊。本次从17:00（UTC+8）另立独立文档版本；继承“先完善理论，不开始实验”和不以训练省时为主目标，不回改167/168封存稿。

## 决策与方法

选择完善现行GT10的完整算法与理论，而不是给旧RL/入口效用/投影过滤分支换名称。算法仍为QGT选真实hub、GT10 target–hub归属反向累加query画像、Micro-HNSW三个真实入口、原raw-IP有限pool NSG。温度、质量守恒、prior、初始化/visited、metric与数值路径及完整收费合同均按静态代码和原协议核对；没有新增实现或模型。

论文主线定为**多rank的query方向与真实有限搜索服务对齐**。完整伪代码与中文稿见[主稿](../entry_method_exploration/20261002_gt10_paper_theory_v1/paper_manuscript.md)，不把“小图架构/球面均值/十倍训练样本”报创新。

## 专门理论增量

[rank核心](../entry_method_exploration/20261002_gt10_paper_theory_v1/gt10_theorem_core.md)给同一有限raw-IP base、真实前100目标、六个hub和相同GT1/GT10画像的两个强连通图：真实三入口共用pool的Recall@1/@100增量分别为+1/2、−1/2。hard与按现行fit GT1 gap中位数确定的数学soft-t1均成立，有限平衡样本/prior和小扰动保留。它证明收益不能仅从GT/rank/profile统计识别；不证明实际NSG/QGT生成该图/H或真实Web符合模型。

[算法理论](../entry_method_exploration/20261002_gt10_paper_theory_v1/algorithm_and_falsifier.md)补高分可达组件容量发现、GTK/native分离下返回保证及|C|=L的完整工作集合；native不一致用potential/safe区间条件。相关rank切向/径向风险、actual top3误差与joint Γ链将画像接到搜索。现行同fit软温度用uniform网格分析，不偷偷改split；界可能空泛。组件lemma为ordered traversal适配，概率/方差/margin为标准或本地已有工具。

[综合费用条件](../entry_method_exploration/20261002_gt10_paper_theory_v1/joint_gain_conditions.md)给两个闭合组件的精确Recall与首次评分/物理槽，和支付全部route/pool/cache/output费用的条件。非空结构例使Recall提高且评分数2L→L+1、扫描槽同为2L；不是GT10 rank构造，也没有QPS结果，两例不拼成端到端证明。

## 前作、期刊与已有证据

[前作/期刊审查](../entry_method_exploration/20261002_gt10_paper_theory_v1/novelty_and_publication_audit.md)原文对照GATE、Learning to Route、RoarGraph、entry/beam及2026近作；GATE已有固定底图/真实hub/query-aware表示/小图top3架构。TODS2025正文仍未获得，未声称全领域排除。CCF2026第七版官方PDF第33页确认KAIS、IS、DMKD、DSE为B；仅核相关页，不冒称读完72页。

E24局部固定H证据、E103完整五集曲线、E134方向稳定性作为既有基础，保留负点/不同L与实际Recall/历史数据曝光限制；没有为新理论重算数组或追加统计。最近真实性能仍166，当前默认Web GT10-soft-t1/Yandex GT10-hard与生产E99保持。

完整算法、条件证明、反例和工作稿已补齐；**CCF B投稿充分性仍缺重要方法区分、真实rank–图机制解释力和独立来源/完整费用证据**，不是录用承诺。下一证据清单见[否证门](../entry_method_exploration/20261002_gt10_paper_theory_v1/evidence_gate.md)，本轮不执行。

## 审查与执行边界

root与三个分工agent对真实rank/归属/三入口pool、hard/median-t1 soft、Cantelli/actual概率、组件/native区间及主稿贡献交叉手审，修正下界小数、弱norm坏事件和物理槽计数。详见[审查台账](../entry_method_exploration/20261002_gt10_paper_theory_v1/proof_review.md)。手审不是形式验证或真实前件PASS。

0真实/合成实验、数学程序、枚举、旧数组新统计、向量读取、GT、训练、画像、图和性能；只读论文/官方目录、静态源码/封存文字、手推与文档。行政JSON/hash/本地链接检查仅验证交付身份。167/168原目录和新root修订前快照保持，未启动旧runner或后台实验。

[主报告](../entry_method_exploration/20261002_gt10_paper_theory_v1/report.md) · [协议](../entry_method_exploration/20261002_gt10_paper_theory_v1/protocol.md) · [状态](../entry_method_exploration/20261002_gt10_paper_theory_v1/state.json)。

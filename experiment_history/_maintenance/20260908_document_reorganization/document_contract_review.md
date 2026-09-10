# 四主文档与历史复盘契约审查

状态：`PASS_DOCUMENT_CONTRACT_WITH_RECORDED_IO_EXCEPTION`。时间：2026-09-08T07:25:04.784722+00:00。限定范围内无阻断文档契约问题；另如实记录本次整理前一子任务发生的一次二进制索引误作文本读取。该例外不被“没有新实验”掩盖，也不冒称整个整理轮完全未碰大型图字节。

## 审查范围和独立性

审阅当前AGENTS、spec、summary、s-target、s-experiment、experiment_history/README、09设计记录及07/08两份历史卡，并对照整理前spec的小文本中artifact、评测与重跑合同。只新增本审查文件，未改主文档。四主文档和09不是此审查者撰写；本审查者此前撰写07/08及B专题，因此07/08只作一致性检查，不称全新独立重算实验或独立查新。此前07/08撰写已直接读原protocol/state/gate/实测分析和审查；本次没有重跑原始矩阵、源码测试或统计。

本次复核工具仅打开指定小文本，单文件均小于100KB；链接目标只检查存在性，不读取其内容。没有打开大型索引、原始向量/GT，也没有训练、ANN或安装。这个“本次复核”范围须与下节记录的**同轮前一子任务I/O异常**明确区分。

## 用户文档契约逐项核对

| 条目 | 判定 | 证据与实际边界 |
|---|---|---|
| 四文件同目录与命名 | PASS | spec.md、summary.md、s-target.md、s-experiment.md均为/data/netg/ACSG根目录下的实际文件；experiment拼写正确，沿用用户指定单数文件名。AGENTS与history目录是附属约定/详细层，不冒充第五主文件。 |
| spec只维护架构合同 | PASS | 主体为Fast真实调用链、已实现模块/API、正式dataset/metric、原NSG、入口与pool语义、artifact/计量/环境/变更依赖。研究方向仅标为尚未实现并外链，无实测结果流水账或把B/A/C/D写成既有API。 |
| 必要旧实现合同保留 | PASS，限文档迁移审查 | 保留unit-query求和加weight1 raw-hub prior、20K/30K分离、raw-IP与LAION unit特例、图R64/Lbuild100/C512/padding、mode2前三输入位置再去重、真实ID与heap映射、L≥K、原retset top-K与RegionalSearch独立global-topK区分。artifact schema、checksum缺口/覆盖风险、GT-inclusive离线成本、aligned配对、计数与纯wall边界、失效产物/重跑表及query/entry/L/K/kernel效用复用键也在正文；历史队列完整参数链接07及旧spec快照，不丢失原件。没有声称重新验明全部源码实现。 |
| summary对应最近真实实验 | PASS | 以COMPLETE_FAST_ROUTER_DIAGNOSIS及2,770,770次实测为中心，保存六问题中的主要结果、analysis/costs v2修正和统计/成本边界；v4/v5明示研究设计，未训练/无新性能GO。没有继续让夜间P3或v5查新充当最近方法实验。 |
| s-target先细评再探索前三 | PASS | 首先B/A/C各自R0，分别有技术问题、近作与旧失败、可评审算法/数据/预算交付，再按B→A→C有界探索；D暂缓、树作共同静态参照。原位C单独kernel验收，原分支no-go不因换名解除。 |
| 计划与实现不混淆 | PASS | R0待开展、B/A/C未实现未运行；目录名与状态流明确是未来约定，不写伪可执行训练命令。v4搜索4h/拟合8h是旧预算而非新自动额度/ETA；先固定协议、变量和边界才执行对应阶段，不构造额外审批流程。 |
| s-experiment为概览索引 | PASS | E01–E20按家族列主要内容、限定判断和对应详细卡，另将依赖准备/文献/设计分区。没有只给NO_GO结论而缺复盘入口，也没有把准备/设计冒充方法性能实验。 |
| 详细历史具有实质内容 | PASS，07/08/09范围 | 07含动机、区域/门户/目标、split、验收、P2/P3数字、三诊断、23trace、局部ΔS/ΔC范围、计时/成本/资源/停止；08含样本/动作、执行、六问题、ties/组合/迁移、v2修正、未知成本和原证据；09独立区分研究设计、实际未做与后来纠正。其余01–06内容由其他专题审查负责，本次只确认索引链接存在，不声称逐原件重审。 |
| 不确定必须深入复盘 | PASS | AGENTS、spec、s-target、s-experiment和history/README均要求从概览进入详细卡，再读原protocol/config/state/gate/结果/修正；缺证据明确未确认，禁止只据摘要/记忆或新名称恢复旧方案。 |
| 旧输入访问不被重写 | PASS | s-experiment与07明确夜间P0读取validation字节做完整性检查、未用于拟合/选择/ANN性能；08及summary明确Fast诊断未打开原始validation/held-out。P2原gate16/23与后续460trace/276配对完成分开，原件不覆写；没有扩成全项目从未用validation。 |
| 停止/未知/修正 | PASS | P3是完整NOPASS而非截止打断；v2统计修正不等于重跑搜索；未知HNSW/route/历史GT等成本为null，instrumented秒数不作QPS；oracle、同L、训练/实现成功均不代替端到端GO。 |
| 链接与历史身份 | PASS | 当前所审九文本共194个本地Markdown链接，全部存在；外部URL未联网重审，目标存在不等于其内容真实性已重新验证。旧spec/summary快照与旧版本SHA明确只代表当时身份，旧章节号/历史下一步不覆盖当前主文件。 |

## 同轮前一子任务的I/O异常：必须保留

07/08撰写末尾核查图参数时，本审查者从已保存runner_config取得索引路径，误按`.json`后缀将`indices/webvid2_5m_light_v1_index/acosp_nsg.json`当文本metadata，执行Python `Path.read_text()`。该文件实际是含base向量的原生二进制NSG，发生UTF-8解码错误（位置25的0xb3），命令exit code=1，报告wall约4.892秒；循环在第一个WebVid文件失败，未继续读取Yandex索引。

这次调用**实际打开并读取了二进制图文件字节**；不能写成“没有访问图”或“只检查了文件元数据”，也不能把解码失败解释为没有I/O。未保存独立字节计数，故不宣称精确读取量。没有成功解析索引/向量对象、运行搜索或评分，也没有写回文件；未打开原始query/GT文件、未安装依赖。失败后立即停止该途径并告知root，没有重试大文件；随后仅以小文本审计记录确认该后缀为二进制。该约4.9秒是失败I/O进程wall，不计作新方法训练、ANN或性能测量。

因此本轮可以陈述“没有新实验、没有改代码/数据、没有打开原始query/GT”，但如概括输入范围，必须带上这一次大型二进制索引读取例外；不能将维护轮描述为完全未碰图字节。本次document_contract复核严格只读小文本，与该已记录例外分开。

非阻断建议：在spec第5节明确`acosp_nsg.json`实际为原生二进制并内嵌base向量，不能按后缀调用JSON解析或无界文本读取。此信息已在既有input_source_audit中确认，无需为补文案重读大索引；本审查未修改主文件。

## 所审输入身份

以下固定本次审阅版本；后续root若修改正文需重核受影响条目。没有对旧大型数据或图重新hash。

| 文件 | bytes | SHA256 |
|---|---:|---|
| `AGENTS.md` | 3081 | `00965edb051ca09705a34c2ecd63bc200b54da86e2be907ce58e9b35d94dad9e` |
| `spec.md` | 16329 | `e380193005f4e6f51d32eb49c0cd089052733136acdad51772c85e26c85b3162` |
| `summary.md` | 5518 | `6aea190b3a1270ec279c6147344f4219a38d256203ec45e430690df4cab6fde9` |
| `s-target.md` | 11990 | `7e1b61c291af1164ffe2165ff348e13f436f9beb8e67970db8ef2a1f63f00deb` |
| `s-experiment.md` | 9002 | `9c490b9e415bfb6a649da16ff1dd8a41b95fcc3bc144d87fbbaf372dd38cb8f9` |
| `experiment_history/README.md` | 3458 | `81d545723a7e86a536d827071672c056be101c5c3c7f917e735e1e206d155c25` |
| `experiment_history/09_research_designs_not_experiments.md` | 6494 | `0acf81e63161baeda6c050c82db24b0bc368ae6634785884126430ed3ae4b1a8` |
| `experiment_history/07_hierarchical_p2_p3.md` | 19845 | `daa5301349e6e2921edf96405be1228d03964721fb62d983ad6b0a7794cb29ab` |
| `experiment_history/08_fast_router_diagnosis.md` | 17286 | `3d8af25b60492041fc57cb43b252d174e7b2f0ba89c09ea53c33b7c641e8a4cb` |

结论为限定范围文档契约PASS并带已披露I/O例外；不是实验复现通过、全历史逐源码独立审计、方法GO或新颖性证明。最终维护state/保护清单由root封账。

# E68后接续：完整画像前三的真实NSG诊断（设计，尚未运行）

2026-09-13，会话3完成E66/E67/E68。本文替代初稿中的“先做排序诊断”接续状态，旧初稿保留历史身份。E66双集门失败、Y局部正信号和E67完整wall结论都不回写。本设计不是新实验的冻结协议，下一会话另建独立stage10版本、source_before及可执行预算；不要重跑stage1–9。

## 已有事实与未解决问题

1. 固定原P+两模态，E66 Y fit+164/aux+49命中、aux失败−4，但两半−14/+63。Web fit−496/aux−106、失败+13。E67 Y五L有4个Recall正点，低L明显慢；Web质量混合且QPS中位全负。当前未找到稳定整体改进，不能把局部信号抹成多画像完全无效。
2. E68完整评分参照相同的原P/duplicate在aux三入口完全一致率为Web86.38%/59.09%、Y93.61%/72.75%。duplicate七个返回slot全部仅3个hub。mode一致率Web77.73%、Y86.38%。这是物理图/近似路由组合的明确缺口；未唯一归因构图、停止条件或槽占用。
3. mode已与自身完整前三一致的aux组Web净−1、Y+108；不一致组Web−105、Y−59。事后分组不是精确入口NSG反事实。Y source3846已选中mode完整前三仍五L10→0；Web3849与完整前三0重合却五L0→10。更准的画像排序可能改变已有救回，不保证搜索质量。

## 优先检验完整排序的真实检索结果

结合E68两条相反案例和11:54监督只读复核，先解决完整画像前三是否具有真实NSG收益，优先于直接增加ef。冻结E68已经计算的aux P/mode完整前三（排序参照不含GT），以canonical真实ID顺序输入原NSG。再加入原approx P逐query三入口回放作为注入接口回归控制，全部恢复E66原始baseline返回；E66原approx mode/duplicate作为既有同query L128质量参照。这里只做结果/NDC诊断，复用旧返回不能当同批QPS曲线。

固定aux7952、L128、已有两半，不重训/构图；三条输入流是原approx P replay、完整P、完整mode。两集各128预检+7952主批、每流plain/count各一批和16条原kernelparity，候选预算2×(128+7952)×3×2+4×3×16=97152 NSG、0 HNSW；在下一冻结协议对实际runner逐项核对。建议输出<=32MiB，输入大query/图均按SHA引用，free>=7GiB。当前evaluator没有逐query入口注入接口，须隔离实现并验证ID范围/唯一性/行对齐/canonical顺序/原kernel/plain-count和baseline全返回回归；不能只把已有数组当作已经完成评估。

11:58监督新增只读覆盖核验提供更省成本的优先执行方式，记录已保存为[coverage副本](reviews/supervisor_cache_coverage_readonly.json)：31808条逻辑完整P/mode路由中28102条已有完全相同query×canonical三入口的E66结果；逻辑缺3706条，经P/mode同key alias后仅3535个未测key（Web2308/Y1227）。15986处现有key碰撞的ids/distances/graph NDC/hits/mask逐字一致，未填任何未测结果。本会话只读该监督报告及history35→E46 cache_environment.cpp/config，未独立重算其覆盖计数，也未新查询；下一协议必须自行验收完整key/源SHA后锁实际缺口。

因此优先使用精确反馈复用，97152为全量回放方案的候选上界，非必须支付的实际预算。若覆盖复核一致，3535新key的plain/count各一次需7070 NSG，另前瞻计缓存回放/原kernelparity/预检；不能把7070写成含全部验收的总成本。逻辑输出、旧返回复用、P/mode alias、新调用分别记账，不复用route NDC。E46显式合法三入口NSG接口可作为隔离适配参照，但其旧environment查询容器/行数和历史协议不同，不能直接重启旧runner或载入错误train4096；先检查aux接口与原kernel身份并验证空增量/非法输入。缓存仅用于离线反事实诊断，正式QPS仍独立整批全在线。

预锁完整aux/固定两半的净命中、严格zero失败救回/新增、逐query/成员损益及NSG工作量，分别比较mode-exact与P-exact、原approx mode、匹配approx P。精确模式比精确P好可说明固定三入口下这一评分表示的局部效用；只比approx mode好而不胜匹配P不足以支持新方法。若精确mode仍无净质量方向，停止“只需修正近似遍历”的解释，不扫ef补阳性。若出现净收益，再锁下一项可部署近似修正并收费完整路由；完整扫描3H的成本不会被这项离线回放测到，不能称已部署改进、oracle上界或QPS GO。

下一会话只选择这一完整反事实诊断作为首阶段，不同时启动下面备选。所有辅助结果若影响动作选择仍计训练反馈，E34最终与held-out隔离。

## 后继备选：单个物理搜索宽度干预

若上述真实NSG诊断支持，再检验固定物理图上ef10→ef30的单个干预，不重新聚类、训练、构图，不扫其它ef/模式数/支持阈值/seed。原P、duplicate3P、mode3P分别保留ef10与ef30，共六个预定policy。原P ef30控制一般增加搜索宽度的收益；duplicate控制多slot无新评分的近似误差；mode测试新增画像能否在修正近似后保留实际净收益。ef30与原ef10并非等工作量，也不能称固定“等10真实hub”。

建议先只用历史aux7952、固定L128，不必重跑fit20K闭式构建；aux反馈用于选择就明确计训练/开发。双集同矩阵、同CPU15单线程串行，先128预检再7952主评测。若沿E66每点plain/count各一批、每点16条原kernelparity，四个native任务（两预检+两aux）、每任务六policy，则前瞻搜索预算为：2×(128+7952)×6×2=193920普通/计数NSG与HNSW，另4×6×16=384原kernel NSG，合计194304 NSG、193920 HNSW。预算只是下一协议的候选算式，需对照实际runner确认；没有本阶段实际调用。

复用现有frozen图和W，禁止把setEf改变误当新图。建议新输出上限96MiB并现场核对free≥7GiB及晚间累计预留，保留所有旧原物；如果源图复制成本超预算，前瞻改成按SHA引用而非查询后删副本，接口变化先验收。沿E66/E67已验证多slotbinary可用配置ef修改；原E34binary不支持3H的unique slot标签，不能直接使用。七slot按distance/slot排序、去重前三真实ID、canonical ID排序、plain/count/parity/graph bytes及原ef10返回回归保持。

在新查询前锁结果门和后续范围：至少比较mode30相对匹配原P10、mode10和P30的命中/零失败、完整aux固定两半、新增与救回、路由及总NDC。恢复更高画像排名一致率或只优于mode10不算方法改善。若没有可迁移净质量信号或只把原mode损伤换成另一批损伤，停止这一次width干预，不接着扫更大ef。若支持完整wall，另冻结同批NSG/Fast/GT10/P30/实际mode候选五L五轮，完整在线费用包含额外路由；是否改善只从同批Recall–QPS/失败前沿判定。不能拼E67或其它批次凑曲线。

## 其它备选仅保留，不并行实施

按真实hub而非物理slot维护搜索候选宽度是可能的实现方向，但不是新概念。本地`benches/hnswlib/stop_condition.h`已有MultiVectorSearchStopCondition；其MultiVectorInnerProductSpace在float向量后追加docID，不能直接载入目前float-only冻结图。若以后选择自定义slot→hub callback，必须另读`hnswalg.h`的add/remove/stop与结果语义，验证internal ID→external slot→真实hub，且重新完整wall。当前不要求同时实现该方向和ef控制。

完整画像前三的真实NSG诊断现为上述优先项，但仍未运行；不能从E68组差虚构其结果。

## 晚间仍需交付

candidate_inventory_v3共18候选，E64旧选择身份保留，E67 best_new只是固定多画像分支展示，未做全局重新选型。最终best_all与今天实际best_new须先按已公开开发数据冻结规则和图/W/mapping/版本，再一次性E34历史validation2000同批对照；最终反馈不回流训练/改候选/阈值。held-out不自动打开。

20:00停新训练、20:40停新增查询、21:00完整报告。若始终没有稳定改善，仍展示真实新候选和损伤。全部历史fit/cal/audit/aux暴露保持，不能把余行称新盲集。会话3安全退出不是整日目标完成。

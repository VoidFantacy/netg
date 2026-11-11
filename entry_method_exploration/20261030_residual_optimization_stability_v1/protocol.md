# E194 残差后端等价省费与查询稳定性

2026-10-30，用户明确授权“先优化和稳定方法，开始实验”。本轮以已有有效的COCO/WebVid配置为起点；默认E99 GT10不变。旧E191/E193代码、科学产物、PDF及seal只读。交付文字报告、CSV、必要图表，不生成PDF。

## 问题与实现冻结

1. OPT-B32用固定512槽开放寻址表替换候选plan中的线性主返回/重复ID查找；严格保持三行读取次序、候选到达次序、原metric、全部候选精算及严格小于才替换的合并。K1单独用相同严格比较简化堆。异常输入回原apply。原B32独立保留。
2. OPT-SQ保持原候选pool、块顺序、2048码访问上限、SQ8评分、最多96原metric精算及合并，只将逐候选Top96堆改为连续数组nth_element再排序。Less(distance,arrival)为全序；每条query的候选ID/评分/精算数和最终六数组须与REUSE-SQ一致。
3. 补齐相同query窗口、相同完整费用合同下的GT10与B32预算曲线。不是新的门控或主图/入口学习；不修改图、画像、训练表、SQ/PQ码、搜索kernel或metric。

## 数据与结束边界（读取本轮结果前固定）

两集COCO、WebVid；真实K1/K100。每集两个固定2048-query窗口：public从原test用PCG64 seed19420261030抽样；confirmation另用seed19420261031。

COCO确认从原E181 row_assignment的unused_unique_query_candidate、group_query_role=null中抽取，与旧qgt/profile/residual/test身份组分离。WebVid确认从原始2.5M训练query源抽取，与已登记ACO/router-train/validation/public-test及原GT10全部fit/cal/audit/validation/recovery逐向量SHA去重。所有确认query另与原两种补全训练角色去重。记录源行与向量SHA；不冒称全历史从未曝光或语义独立。确认GT在模型和矩阵冻结后按同一全base/raw-IP精确生成，另用float64分块暴力核查固定8条及并列边界。不以新确认结果选方法、L或实现。

每个数据/窗口/K，GT10与B32共同测L=[100,128,160,200,256,320,400,512,640,800,1000]；OPT-B32测[100,200,400,800]。COCO的REUSE-SQ/OPT-SQ测[100,200,400]，WebVid测[200,400,800]。每组32点，共256正式点×3轮=768完整T1批次。公共和确认窗口均完成固定矩阵，无根据阳性继续细分或追加。资格每集128公共query、K1/K100、L200、五方法共20点单轮，正式前检查全包、SQ候选/访问、B32候选一致。

查询期CPU15、实际threads=1、OMP/BLAS/MKL/NUMEXPR=1、单方法串行；离线GT生成8线程单列且不与正式性能并行。每点warm256、三轮方法轮转。完整wall包括正常Batch创建/初始化、路由、主搜索、补全、六数组复制和正常销毁；加载/GT/hash/输出/审计在外。保存真实第一轮四数组和三轮全六数组hash，后两轮bit一致。额外计数不是总NDC；B32的真实候选/精算数在wall外重构，禁止把未插桩0当作零访问。

## 判定

等价资格要求所有查询ID/距离/入口/画像分数以及未插桩计数数组逐字节相同；SQ候选/访问一致，B32 plan候选次序一致；主包scalar/全排序补全oracle通过。失败保留日志，修正需新版本或明确qualification修订，不得继续将不等价方法称等价。

每点报告Recall、救损、严格K100 0–9命中失败率、完整wall中位QPS/三轮范围、码扫描/精算量。比较OPT对原方法同L的三轮配对速度、跨L前沿，以及相同窗口更强GT10/B32。质量阈值参照不冒称精确等Recall；同时报告同费用内最好Recall。优化可保留条件性配置，不要求所有探索点同时通过；性能采用>=2%中位QPS且三轮配对同向为预定探索筛选，三轮非独立质量样本/置信区间。跨查询稳定性分别报告public/confirmation，不跨窗混拼QPS。查询bootstrap仅对质量/救回不确定性，不能替代新图复现。

## 来源、存储与交付

源码/库/binary/配置/模型/确认源行/输入SHA在正式前冻结。大base/图继承旧身份并核stat；本轮新数据及所有实际返回独立存放/root/acsg-e194-storage，经storage链接。/data至少保留0.65GiB，/root至少0.7GiB；预计新增<0.8GiB。旧seal可变根文档使用修改前快照/SHA映射，旧seal原件不回写。完成256点、审计、报告和四根文档/历史同步后收口；无新门拟合、无自动默认替换。

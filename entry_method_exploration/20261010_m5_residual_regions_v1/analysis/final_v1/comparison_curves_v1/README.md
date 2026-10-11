# E174：新区域扩展与原方法的同条件曲线

本目录是用户在结果完成后新增的展示需求，只读取已独审的预计算metrics字段；没有新实验、训练、GT、统计重采样或策略门。现有report、README、history、科学源/锁、metrics/CSV/raw与首版图均未修改。

- [pilot图](pilot.png)（[SVG](pilot.svg)）：confirm_a，每点4096query，24个已存点。
- [confirm图](confirm.png)（[SVG](confirm.svg)）：confirm_b，每点4096query，24个已存点。
- [相对原M5的独立增量](increment_vs_m5.png)（[SVG](increment_vs_m5.svg)）：16条已存same-L比较，每panel是a/b×两L共4点。
- [48点字段摘录](points48.csv)、[16比较字段摘录](saved_comparisons16.csv)、[原最终报告](../report.md)、[独立结果审计](../../../reviews/independent_result_audit/report.json)、[本次绘图执行收据](../../../reviews/comparison_curves_execution.json)。

GT图例写作GT10（WebVid为GT10-soft-t1，Yandex为GT10-hard）；蓝色原M5，红色新M5REG96。这里的“之前方法”都是在本轮同角色、同K/L、同计时条件下重跑的matched对照，未拼接E173旧公共test 10K角色。pilot与confirm分别展示，不合并两角色。

每张主图为WebVid/Yandex×K1/K100四panel；WebVid仅L800/1000，Yandex仅L1000/1200。圆为小L，方为大L，线段只连接同方法的两档真实实测点：**Connecting measured points only; no intermediate-L performance implied.** 没有jitter、曲线拟合、中间L性能、预算插值或新Recall区间。主图横坐标使用原`qps_median`，横误差条是原`qps_min`/`qps_max`三轮范围；纵坐标是原`recall_pct`。

差值图直接使用已有`comparisons.paired_qps_change_pct`和`recall_delta_pp`。ΔQPS是三轮按序速度比的中位数变化，**不能理解为主曲线两个QPS中位数的比**；ΔRecall单位为百分点。蓝色pilot a、橙色confirm b，零轴为原M5参照，圆/方仍对应各dataset的小/大L。没有重新计算ratio、CI或门。

本轮已报告的主M5REG96/原M5同L16点是14点Recall增、2点平，配对QPS中位变化全部下降；差值图让小质量增量及其速度代价更容易看清。WebVid K1确认b跨L有观测双升，但pilot a对应Recall差为负，且b原M5在同一小L已具备对大L GT的观测双升；整个跨档速度优势不能归给区域扩展。原协议主双升门与更严格报告门均0：停止本冻结区域版，保留原M5研究与GT10默认，具体值和归因见原报告。

图只展示已测离散点及保存的描述量，不是总体/同时显著性检验。仅连接两端也不证明中间曲线、单调性或其它budget收益。表外候选/救回不直接证明跨模态泛化；NDC仅固定256query，与full4096返回/trace范围分开。各审计范围、CI未独立重生、监控partial-speed与callback UNRESOLVED限制继续以原报告/历史说明为准。

实际metrics身份来自独审登记：SHA256 `1b6decb1c3218b7eb14330392c4650270dab8db5b128dd3d7fe8bfeb2b6a1b91`，stat4 `[66305, 8423176, 769558, 1791607999876873334]`。本脚本要求当前metrics的绝对路径与stat4匹配该登记，复用已审SHA，不重新hashGT、raw、base、图或模型。执行前后对所有1193个独审登记文件、109项原注册输入的并集及当前交付文档/旧图做metadata保全检查，具体覆盖范围与费用以执行收据为准；不把metadata检查扩大为重新全内容hash。

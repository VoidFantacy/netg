# E65 冻结今日候选的历史开发集完整wall比较

2026-09-13会话2。此协议在E64两集辅助结果完整生成/选择前建立，选型规则只引用E64原锁定best_new，不打开最终validation。目标是尽早交付今日真实候选的同机QPS–Recall/zero-hit曲线并检查线上成本；晚间E34最终对照仍未完成。

## 模型与输入

每集固定NSG原入口、Fast30K/GT1/legacy seed100、FastGT10-hard20K/seed20260828，以及E64固定best_new；WebVid另加当前匹配GT10-soft-t1起点。Yandex hard即匹配起点。best_all身份单列，不用baseline对自身替代实际新方法。best_new即使未过开发门仍如实显示，sham不参加推荐。配置和W/graph/mapping/原binary身份必须在本阶段查询前冻结；S/T必须加载冻结物理图，画像字节全量校验。

使用E64已预定router_train source[2048:4096]共2048 query，每集同一批全方法全部L。来自已历史暴露及E64用于选型的开发数据，不是独立泛化检验；E64选型不能由本次速度改动，最终validation没有读取。P-fit/cal/audit/auxiliary反馈角色仍依各协议；本轮没有训练/新GT/参数/seed选择。

## 正式计量合同，开发数据证据范围

L64/128/256/400/800，每点一次完整warmup+五轮独立plain整批wall，方法顺序按dataset/repeat/L轮换；计时包含在线路由/映射/原NSG/预分配输出，排除GT/count/hash/JSON/图构建加载。使用E34同SHA无hook evaluator；全部方法计时后才做full count与前16原kernel parity，再读取GT集合评分。QPS=N/wall，记录五轮全值/中位数/范围，不能以NDC或分项之和换算。对所有方法保留aligned ids/distances/entry IDs、GT10 mask、两NDC、零命中失败及救回/新增；失败严格hits=0。

单native CPU15、OMP/OpenBLAS/MKL/NumExpr/BLIS=1，实际进程/OMP team核验，启动前在child preexec绑核以消除taskset继承竞态。每次只有一个被测方法，无训练/标签/评分/其它性能任务并发；控制器仅轻量/proc监控，每2秒。两集native工具terminal全部实际exit后才独立分析。独立验收原始集合/mask、QPS恒等、五轮/plain/count/reference、五L同模型同图同入口、L128重现E64相同query输出。

## 成本与停止

WebVid25点、Yandex20点，共45点225wall；每点7×2048+16=14352原NSG，共645840，预算650000。HNSW501760；35源图加载/副本、plain/count70次load，0新小图构建、0训练更新/GT。未测分项wall为null+reason，不加额外查询。每集最长900秒，10:40后不启动，11:00停止新增查询，11:14:29前安全交接；失败完整预留、无自动重试/扩大预算。free≥7GiB、阶段≤160MiB、RSS≤32GiB。

输出QPS–Recall、QPS–失败率、按L三指标PNG/SVG/PDF和CSV，保留原始测量点，不跨旧批次拼曲线。非支配曲线之间的共同Recall区间log-QPS插值明确为描述性估计，不作实测同Recall点或最终GO。当前历史开发可支持局部信号/成本判断，不能替代本日最终冻结后E34数据的同批独立wall。整日21:00目标依然未完成。

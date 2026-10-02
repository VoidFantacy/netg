"""Render all predeclared endpoint and information-control results."""
from common import RUN, read, dump

response = read(RUN/'analysis/response.json')
information = read(RUN/'analysis/information.json')
audit = read(RUN/'reviews/independent_audit.json')
stats = read(RUN/'reviews/statistics_audit.json')
jobs = read(RUN/'reviews/jobs_v2.json')
search = read(RUN/'reviews/search_complete.json')
assert audit['status'] == stats['status'] == 'PASS'
assert response['information_control_eligible'] and not information['pass_all']
assert not (RUN/'report.md').exists()
short = lambda ds: 'WebVid' if ds.startswith('web') else 'Yandex'
ci = lambda v: f'[{v[0]:+.4f}, {v[1]:+.4f}]'
lines = ['# E120 目标预算响应与查询信息审查', '',
    '日期：2026-09-22。状态 `STOP_TARGET_LOCAL_INFORMATION`。用户授权的下一阶段已按冻结停止分支完成；没有新可部署收益，默认 Web GT10-soft-t1 / Yandex GT10-hard 与生产 E99 不变。', '',
    '## 本轮解决的问题', '',
    '不能将全部失败归因为评分器不够强，也不能把 L128 事后最优视为高召回预算的正确标签。本轮先检查有限动作的预算响应迁移，再按冻结门检查这些差异能否由查询局部几何预测。仅补 E107 缺失的五个预算点，未重做全 H 扫描。', '',
    '固定原八策略、每集 4096 条历史曝光 E105 query、真实 K1/K100 返回及 GT、图、raw-IP、搜索核和入口顺序。选择族为默认加六个原精确策略；NSGFixed1 仅作控制，不用于增大 oracle。所有点的 L 固定，未引入查询自适应预算。', '',
    '## 预算迁移', '',
    '下面的 oracle 是看过真实结果后在七种策略中选出的有限族质量上界，不是全 H 上界，也不是在线方法。迁移动作同样使用该查询在 L128 的真实结果，不能部署。带 * 的点是预锁主点；全部预算在 analysis/response.json 和 metrics.csv 中保留。百分点记为 pp。', '',
    '| 数据 | K / L | 默认 Recall % | oracle 增益 pp | L128 选择迁移增益 pp | 收益保留率 | 最优集合有交集 % |',
    '|---|---:|---:|---:|---:|---:|---:|']
for r in response['all_transfers']:
    if r['target_endpoint']:
        mark = '*' if r['primary_upper'] else ''
        lines.append(f"| {short(r['dataset'])} | {r['K']} / {r['L']}{mark} | {100*r['baseline_recall']:.4f} | {r['oracle_gain_pp']:.4f} | {r['transferred_gain_pp']:.4f} | {100*r['retention']:.2f}% | {100*r['optimal_set_overlap']:.2f} |")
lines += ['',
    '四主点 oracle 增益均超过预锁 0.25pp；K100 的 L128 选择在 Web L1250 / Y L256 只保留 43.31% / 70.49%，低于 80% 门，因而触发唯一信息对照。对应质量遗憾为 0.2422 / 0.2397pp。K1 Web 保留 91.67%；Y 主点本身就是 L128，其 100% 是恒等关系，不是迁移证据。Y K1 下端 L96 反向迁移只保留 74.79%，也完整报告。', '',
    'K100 主点存在正转负的 query/action 对 Web178 / Y161；迁移动作造成净损伤的 query 为 70 / 62。最优集合仍分别有 94.41% / 96.80% 交集，说明 winner ID 不同不能全算成决策冲突，但少数响应差异仍足以损失收益。', '',
    '**目标区域限制：** 预算来自 E103 另一批查询的 90% 区域。这里 Web K1 L800 默认只有 89.1846%，所以不能声称本轮四格都验证了严格 90% 工作点，也不事后补 L。其他三主点默认为 90.5815% / 90.6250% / 91.0444%。本轮是目标区域响应诊断，不是新 90% QPS 曲线。', '',
    '## 条件信息对照', '',
    '四折，每折 fit3072 / outer1024；单位 raw-query 余弦的 55 个最近 fit query，float64，相同邻居与动作族。TargetKNN 用目标预算响应，LowKNN 只换为 L128 响应；TargetFixed 为 fit 全局均值，ShuffleKNN 为一次预锁 fit 标签行置换。默认优先打破效用同分。无外折标签参与邻居选择或拟合；有标签驱动的非参数估计，不是零学习成本。', '',
    '| 数据 | 规则 | R1 增益 pp | R100 增益 pp | 等 K 均值 pp | 描述性 95% 区间 pp |',
    '|---|---|---:|---:|---:|---|']
for ds, result in information['results'].items():
    for name, m in result['methods'].items():
        lines.append(f"| {short(ds)} | {name} | {m['K_mean_gain_pp'][0]:+.4f} | {m['K_mean_gain_pp'][1]:+.4f} | {m['mean_gain_pp']:+.4f} | {ci(m['CI95_pp'])} |")
lines += ['', '| 数据 | TargetKNN 减对照 | 等 K 差值 pp | 描述性 95% 区间 pp |', '|---|---|---:|---|']
for ds, result in information['results'].items():
    for name, c in result['contrasts'].items():
        lines.append(f"| {short(ds)} | {name} | {c['gain_pp']:+.4f} | {ci(c['CI95_pp'])} |")
lines += ['',
    '**信息门两集均失败。** Web 主规则相对默认的均值和区间虽正，但对全局均值和置换控制均未建立正差值区间，且均值低于 LowKNN。Y 主规则自身区间跨零，对两个控制的差值区间也跨零，均值亦低于 LowKNN。没有用表现更好的控制替换预先提名的主规则。停止本版目标预算加 raw-query 局部均值路线，不调邻居数、表示、seed、动作池或门槛。', '',
    '预算错配是真实现象，却不是本轮已证实的可学习收益来源。没有证据把更强 MLP/双塔/RL 或批量高预算重标注列为下一执行步骤；也没有证明所有表示、高预算入口或全 H 选择均不可能。未触发廉价实现及完整成本阶段，不是遗漏已通过的任务。', '',
    '## 理论与论文边界', '',
    '理论对象为 m_L(x,a)=E[Recall_L(q,a)-Recall_L(q,default)|x]，区分事后空间、预算迁移误差与跨查询预测误差。低预算最优动作的高预算遗憾至多为两倍最大动作响应漂移；这是简单不等式，不是新定理或有效性保证。6000 个合成检查及单调响应仍可反转偏好的抽象反例通过，未冒充真实 NSG 构造。', '',
    '[PAC 算法选择](https://arxiv.org/abs/1511.07147)用于明确输入分布和动作族；[ICML2020 图搜索理论](https://proceedings.mlr.press/v119/prokhorenkova20a.html)与[ICLR2026 随机游走和动态更新](https://proceedings.iclr.cc/paper_files/paper/2026/hash/dd5d65bf0c81b539f00f57850c1774ad-Abstract-Conference.html)的条件不能直接搬到当前确定性有限 beam。没有从这些论文得到可保证改善本系统的评分器。细节见[理论](theory.md)和[全文核查补充](literature_addendum.md)。kNN 或预算条件化本身不构成论文新颖性。', '',
    '## 成本、修正与核验', '',
    f"复用 144 点，新增 40 点，真实 NSG {search['calls']:,} 次，其中完整样本 327680 次、smoke 3456 次；未使用修复搜索额度。查询作业 {search['query_job_seconds']:.2f} 秒（含加载/路由/诊断），成功构建 {jobs[0]['seconds']:.2f} 秒；原生峰值 {max(j['observed_max_rss_kib'] for j in jobs)/1048576:.3f} GiB。实际 CPU15、1线程、串行。", '',
    f"响应分析 {response['seconds']:.2f} 秒，条件非参数对照 {information['seconds']:.2f} 秒（双集共8个外折、四规则、0优化器步骤）。独立原始返回审计 {audit['seconds']:.2f} 秒；统计区间复核 {stats['seconds']:.2f} 秒。上述都是研究作业成本，不能换算成候选端到端 QPS。0新GT/画像/图/K10/新鲜测试载荷；有新的预算响应标签。", '',
    '初次构建遗漏原 .h 依赖，0搜索退出；失败日志与初版冻结保留，再按原字节补齐8个头文件。未改变方法或搜索核。完整输出 count/plain 逐位一致，smoke 另对链接 E99；新默认全部恢复 E105、入口恢复 E107。', '',
    f"独立 Python 成员循环重算全部 {audit['points']} 点 / {audit['query_outputs']:,} 条 query 输出，核验 {audit['budget_transfers']} 个预算迁移、全部信息动作/收益及 {audit['neighbor_boundary_checks']} 条邻居边界，另重算 {stats['intervals']} 个配对描述区间。690 个旧消费文件和8个原头文件身份、冻结源码/协议/二进制均通过。base 全 SHA 在准备时复验；大图沿用 stat 加嵌入向量抽验，不声称新全图 hash。", '',
    '审计为同会话独立数值实现，不是独立人员审查。4096 query 全部历史曝光，bootstrap5000 仅描述性；两个 K 成对、信息对照按折重采样，训练折重叠和多预算依赖不构成新独立样本。未发现足以解释当前结果的实现错误，但这不是所有潜在问题均不存在的证明。', '',
    '## 收口与后续边界', '',
    '本阶段完成，当前无后继训练或搜索队列。保留目标预算监督的诊断结论，不将它包装成新方法。后继立项必须先提出当前 raw-query 局部均值之外的、在线廉价且可检验的收益信息，证明与 E117/E118/E119 及既有算法选择工作的实质区别，并冻结同监督简单控制；没有这种依据就停止该分支。通过独立信息门后才考虑低成本实现与完整固定 L 曲线。', '',
    '默认和生产 E99 不变；最近完整五数据集前沿仍 E103，最近候选完整性能曲线仍 E118。此次既没有新端到端 QPS，也没有可宣布的 GT10 替换。', '',
    '原始证据：[协议](protocol.md)、[配置](config.locked.json)、[全部响应](analysis/response.json)、[方法全表](analysis/metrics.csv)、[信息门](analysis/information.json)、[作业账](reviews/jobs_v2.json)、[数值审计](reviews/independent_audit.json)、[统计审计](reviews/statistics_audit.json)、[状态](state.json)。', '']
(RUN/'report.md').write_text('\n'.join(lines))
dump(RUN/'reviews/cost.json', dict(NSG_calls=search['calls'], query_job_seconds=search['query_job_seconds'],
    successful_build_seconds=jobs[0]['seconds'], failed_prebuild_seconds=read(RUN/'reviews/failed_prebuild/jobs.json')[0]['seconds'],
    analysis_seconds=response['seconds'], information_seconds=information['seconds'],
    raw_audit_seconds=audit['seconds'], statistics_audit_seconds=stats['seconds'],
    original_inputs_preserved=690, original_headers_preserved=8,
    formal_QPS=False, default_changed=False, label_based_outer_folds=8, optimizer_steps=0))
print('REPORT_WRITTEN', flush=True)

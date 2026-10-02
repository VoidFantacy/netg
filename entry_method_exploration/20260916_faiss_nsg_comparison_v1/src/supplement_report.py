"""Close the disclosed batch-counter limitation after the real forwarding audit."""
import datetime
import json
import pathlib
import shutil

D = pathlib.Path(__file__).resolve().parent.parent
read = lambda p: json.loads(p.read_text())
a = read(D / 'reviews/actual_batch4_count_audit.json')
p = read(D / 'results/actual_batch4_count/progress.json')
assert a['status'] == 'PASS' and a['actual_batch4_forwarded'] and a['search_calls'] == 80000
assert len(p) == 8 and all(x['status'] == 'PASS' and x['actual_batch4_forwarded'] for x in p)
compat = read(D / 'compatibility/analysis.json')
assert compat['search_calls'] == 496000
compat_note = '四集一致性通过与WebVid四点提速分别成立' if compat['status'] == 'PASS' else '四集一致性存在差异，WebVid四点提速仅限本轮条件'
s = read(D / 'results/summary.json')
def row(v):
    return next(x for x in s['metrics'] if (x['variant'], x['K'], x['L']) == (v, 100, 1250))
def gain(v):
    return next(x['speedup_percent'] for x in s['paired_speedups']
                if (x['variant'], x['baseline'], x['K'], x['L']) == (v, 'GT10-current', 100, 1250))
cur, best, h = [row(v) for v in ['GT10-current', 'GT10-span-batch4', 'HNSW']]
report = D / 'report.md'
text = report.read_text()
assert '## 真实 batch4 计数核验与最终建议' not in text
before = D / 'reviews' / ('report_before_batch4_supplement_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.md')
shutil.copy2(report, before)
old = '主矩阵的batch4计数包装默认使用四次scalar，完整批量NDC结论还须由[80000次直接转发核验](actual_batch4_count_protocol.md)收口；最终状态见报告末尾补充。'
assert old in text
text = text.replace(old, '主矩阵的batch4计数包装默认使用四次scalar；现已补做[80000次真实batch4转发核验](actual_batch4_count_protocol.md)，8个配置的输出与逐query NDC全部通过。原plain计时保留，核验细节见报告末尾。', 1)
text += f'''
## 真实 batch4 计数核验与最终建议

主矩阵plain实际使用Faiss批量接口，但旧CountDC继承的默认batch4会拆成四次scalar，所以旧count本身不足以证明真实批量路径的逐query NDC。本补充直接转发底层`distances_batch_4`，每组按4次逻辑距离记数；原WebVid完整10K query、原四点、batch4及span+batch4共8配置、80000次搜索，返回ID、距离bits、入口、route NDC、graph NDC均与E99一致。补充没有新plain轮或QPS点，不改变原120轮计时。

补充含编译及运行{a['compile_and_run_seconds']/60:.3f}分钟，查询程序含加载{a['seconds_including_load']/60:.3f}分钟。主比较2000000次、四集兼容性496000次、本核验80000次，合计 **2576000次真实搜索**；普通和sanitizer合成回归另计25920次。完整检查见[8配置记录](results/actual_batch4_count/progress.json)、[计数验收](reviews/actual_batch4_count_audit.json)、[补充协议](actual_batch4_count_protocol.md)。

按本轮证据，后续投入顺序为：

1. **优先接入批量距离，并配合跳过尾部空槽。** 保留GT10原三入口和搜索结果，复用Faiss现有batch4接口。K100/L1250上batch4单独相对current为{gain('GT10-batch4'):+.2f}%，span+batch4为{gain('GT10-span-batch4'):+.2f}%；组合达到{best['qps_mean']:.2f} QPS、{best['recall']*100:.4f}% Recall@100，同轮HNSW为{h['qps_mean']:.2f} QPS、{h['recall']*100:.4f}%。这里包含邻居聚合、预取和批量执行的共同影响，尚未分别量化硬件缓存等待和算术收益。
2. **span是成本小、收益较小的独立选项。** 每节点一个字节，WebVid新增{s['layout']['span_bytes']:,}字节，初始化后复用；高预算点单独提升{gain('GT10-span'):+.2f}%。它保留边顺序和内部空洞，适合与batch4分别保留开关作回归。
3. **过滤visited预取与精简历史分支暂不优先。** 本轮没有显示它们相对现有实现的稳定正收益；小范围波动不能支撑重构。候选池或向量布局的大改仍缺针对性证据，不在本轮自动扩展。
4. **不因库身份直接替换线上搜索。** Faiss 1.9.0原生初始化与项目不同，个别固定入口点的Recall略高，但本轮同图计时更慢；最新版库只核查源码、未测性能。更有证据的路径是保留多入口能力、使用已有库的距离组件，并吸收有效的遍历组织改进。

这是独立研究候选的结论。{compat_note}，不等于五集都已测得加速；默认、生产源码和模型保持E99。后续接入须补全原API/trace及特殊值和未知DistanceComputer回退，再公平计时所有共享NSG入口方法。
'''
report.write_text(text)
print('Closed actual batch4 count limitation and added ranked recommendations')

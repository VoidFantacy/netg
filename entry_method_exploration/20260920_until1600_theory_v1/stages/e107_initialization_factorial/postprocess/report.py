import sys,csv
from pathlib import Path
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'src'))
from common import *
assert read(RUN/'reviews/analysis_complete.json')['status']=='PASS'
assert not (RUN/'report.md').exists()
m=list(csv.DictReader((RUN/'results/metrics.csv').open()));p=list(csv.DictReader((RUN/'results/paired.csv').open()))
names={'NSGFixed1':'固定NSG入口','UnitHub1':'单位hub / 1','UnitHub3':'单位hub / 3','GT11':'GT1 / 1','GT13':'GT1 / 3','GT101':'GT10 / 1','GT103':'GT10 / 3','DefaultANN':'当前默认ANN / 3'}
lines=['# E107：GT10系统收益究竟来自哪一环','',
'2026-09-20，用户16:00限时理论研究中的一个完整机制阶段。两集各4096条E105已曝光query，固定底库/raw-IP/NSG/H；真实K1五L64/128/256/400/800，K100四L128/256/400/800。共144个方法点，所有输出独立重算、count/plain逐位一致、对应E105/E106基线恢复通过。**本轮没有在线QPS，也没有新训练、GT或图。**','',
'主要发现需要修正此前直觉：在这批query与精确路由下，按query从原H中选择单位hub，已获得相对固定NSG入口的大部分均值收益；WebVid的query画像并未稳定超过这个简单对照。原H本身由QGT与GT候选选择，因此这不是完全无监督的随机hub方法。不能把系统总收益都解释成GT10画像聚合的贡献。','',
'其次，多入口的作用取决于表示：单位hub从1增至3的18个均值变化均为正，GT10则17个负、1个正；这18点共用query且预算相关，不是18次独立试验。GT10的18个区间仅1个排除0，不能把均值符号写成逐点显著结论。真实逐query收益与损害并存。','',
'## 1. 固定L128的完整方法对照','',
'下表Recall为百分数，括号内为零命中query数；NDC为图距离计算均值。单位hub、GT1、GT10均全H exact；默认ANN单列。Web GT10是soft-t1而GT1是hard，两者差值还包含软归属，不能只归因于目标数。Yandex两者均hard。','',
'| 数据 | 方法 | Recall@1（失败） | Recall@100（失败） | 图NDC |','|---|---|---:|---:|---:|']
for ds in LOCK['datasets']:
 for name in names:
  a=next(x for x in m if x['dataset']==ds and x['method']==name and x['K']=='1' and x['L']=='128')
  b=next(x for x in m if x['dataset']==ds and x['method']==name and x['K']=='100' and x['L']=='128')
  lines.append(f"| {'WebVid' if ds.startswith('webvid') else 'Yandex'} | {names[name]} | {float(a['recall'])*100:.4f}（{a['failed']}） | {float(b['recall'])*100:.4f}（{b['failed']}） | {float(a['graph_ndc']):.2f} |")
lines += ['', '## 2. 先区分选入口、画像和GT10增量','',
'相对固定入口，单位hub单入口在L128已取得Web R1/R100 +4.5898/+1.3228pp、Yandex +1.3672/+1.0408pp。当前默认ANN对应为+4.2725/+1.3127pp、+1.6113/+1.2871pp。这个对照说明自适应选入口是重要部分；不是对任意数据集的因果百分比分摊。','',
'GT1画像相对单位hub单入口，Web L128 R1−0.2441pp、R100+0.0481pp，两个95%区间均跨0；Yandex为+0.5371/+0.3567pp，前者跨0、后者描述性区间为[+0.0110,+0.7093]pp。改用三入口后，Web GT1在全部9个预算均值低于单位hub3；Yandex呈混合结果。不能维持“query画像普遍比原hub好”的无条件故事。','',
'GT10相对GT1的完整18点仍为混合小增量，没有形成所有预算/指标均优的规律。全部配对与交互保存在CSV；这里不挑一个较好的预算代替完整结果。','',
'## 3. 多入口的完整真实效果','',
'每格为同表示从1变3的Recall差（pp）；保留全部预算。','',
'| 数据 | K | L | 单位hub 3−1 | GT1 3−1 | GT10 3−1 |','|---|---:|---:|---:|---:|---:|']
for ds in LOCK['datasets']:
 for ks,ls in LOCK['K_L'].items():
  for L in ls:
   vals=[next(x for x in p if x['dataset']==ds and x['K']==ks and int(x['L'])==L and x['baseline']==r+'1' and x['method']==r+'3') for r in ['UnitHub','GT1','GT10']]
   lines.append(f"| {'WebVid' if ds.startswith('webvid') else 'Yandex'} | {ks} | {L} | "+' | '.join(f"{float(x['delta_recall_pp']):+.4f}" for x in vals)+' |')
lines += ['', 'GT10的L128增损更具体：Web K1救回58、损害67个query；Yandex为28/40。K100的实际GT成员新增/丢失分别为4903/5117、2897/3513；这是实际目标集合变化，区别于逐query命中数差的正负部。即使入口增多，原来能命中的目标也可能丢失。','',
'[质量与搜索量图](figures/factorial_quality_cost.png) · [入口数效应图](figures/entry_count_effect.png)。两张PNG已实际查看，PDF由相同图对象导出。图中的NDC不能替代路由及NSG的完整线上wall。','',
'## 4. 理论解释与下一步边界','',
'已在当前内核核验强连通五节点反例：q=1，a=0、b=.1、t=1、d=.9、e=.8，有向环a→b→t→d→e→a。L2/K1，仅a可找到t；加入更近的d，先扩展d后e挤出未展开a，最终漏掉t。固定beam搜索对入口集合没有一般单调性。反例不证明真实NSG总是通过相同局部结构致损；真实矩阵只确认入口扩展的实际增损与表示交互。','',
'当前事实支持先补强简单对照的实际部署证据：UnitHub3精确路由的Web结果值得检查，但精确全H扫描并非现有小图成本；必须另锁普通Micro-HNSW版本及匹配GT10完整单线程wall。它不是已经胜出或可直接替换的默认方法，更不构成新的神经网络贡献。','',
'对于后续学习，另外两份理论草案把目标均值/区域后验的代理最优与真实搜索误差分开，并提出训练前的完美代理信息检查。E107没有证明query画像是主要瓶颈，也未授权把旧QMLP换名继续训练。原E104真实三元组监督及E105/E106停止边界保留。','',
'## 5. 成本、验证与证据','',
'真实NSG调用1,181,184，另2次合成反例；原ANN路由16,448次。两集完整搜索约1203.26秒，编译/身份/编排总约1221.61秒；独立评分约30.53秒。CPU15、实际线程1、数据集及方法串行；两个最大图保持原stat身份，旧输入/模型SHA保持。完整144点K1/K100同L首返回、距离bits与NDC一致，三个表示top1均属于top3，所有相同入口控制返回相同。','',
'Web soft/Yandex hard默认与生产E99保持。E103仍是最新完整五集性能证据。本阶段状态为COMPLETE_INITIALIZATION_FACTORIAL，16:00限时研究继续；完成机制阶段不等于找到稳定替换或完成GT10因果解释。','',
'[冻结协议](protocol.md) · [冻结推导](research.md) · [解释口径](reviews/interpretation_notes.md) · [144点指标](results/metrics.csv) · [270配对](results/paired.csv) · [36交互](results/interactions.csv) · [搜索完成](reviews/search_complete.json) · [数字核验](reviews/numeric_verification.json) · [阶段验收](reviews/completion_audit.json)。']
(RUN/'report.md').write_text('\n'.join(lines)+'\n')
dump(RUN/'reviews/report_source.json',dict(source=identity(Path(__file__)),report=identity(RUN/'report.md')))
print('REPORT_WRITTEN')

"""Publish the completed E26 evidence into the existing four-document contract."""
import shutil
from common import ROOT,RUN,DATASETS,read,dump,identity
from analyze import LABELS
from write_report import STATUS,pct,table


def main():
    assert read(RUN/'reviews/immutable_integrity.json')['status']=='PASS'
    assert not (ROOT/'experiment_history/15_profile_shrinkage.md').exists()
    originals={}
    for name in ['summary.md','spec.md','s-target.md','s-experiment.md']:
        p=ROOT/name;assert p.read_bytes()==(RUN/'source_before'/name).read_bytes(),name
        originals[name]=p.read_text()
    shutil.copy2(ROOT/'experiment_history/README.md',RUN/'source_before/history_README.md')
    before=[identity(ROOT/p) for p in [*originals,'experiment_history/README.md']]
    a=read(RUN/'results/analysis.json');cost=read(RUN/'results/costs.json');b='entry_method_exploration/20260910_profile_shrinkage_v1'
    stages=[];validation=[];delta=[];decomposition=[]
    for ds,d in a['datasets'].items():
        for stage in ['cal','audit','validation']:
            s=d['validation']['pooled_L64_L128']['stats'] if stage=='validation' else d['development'][stage]['selected']['pooled']
            row=[LABELS[ds],stage,*[pct(s[k]) for k in ['R','Rh','A_all','Ah_all']],f"{s['net_delta_hits']:+d} / {s['always_A1_net_delta_hits']:+d}"]
            stages.append(row)
            if stage=='validation':
                validation.append(row[:1]+row[2:])
                decomposition.append(f"{LABELS[ds]}：原正命中{s['original_positive_hits']}保留{s['original_positive_hits_retained']}，另产生{s['new_or_amplified_positive_hits']}新/放大正命中；原负命中{s['original_negative_hits']}避免{s['original_negative_hits_avoided']}，但新增/加重{s['total_new_or_amplified_negative_hits']}，最终损失{s['total_negative_hits']}。")
    for c in a['comparisons']:
        if c['method']=='shrink' and c['reference']=='e24':delta.append([LABELS[c['dataset']],c['L'],f"{c['delta_recall_pp']:+.3f}",f"{c['qps_percent_change_medians']:+.2f}"])
    costline=f"E26真实调用897280、修复0、合成2268；8个真实job一次完成。搜索进程总计{cost['search_process_wall_seconds']:.2f}s、最高RSS{cost['max_observed_RSS_bytes']/2**30:.3f}GiB，包含加载/构建/预热/计数/I/O，不能换算QPS。"
    history=['# E26：单路画像收缩与损失迁移','',f'2026-09-10夜间，状态`{STATUS}`；全部预定阶段完成，无正式性能GO。独立版本`20260910_profile_shrinkage_v1`，不覆盖E25或旧E09。','',
        '## 动机、区别与固定方法','',
        '用户要求保留有效改道并减少受损查询，授权详细分析和直接相关的小探索。E25门控在WebVid有少量质量修复，但双路成本使QPS下降；Yandex收益保留不足。E26追问能否离线缩小画像位移，使在线仍是一份W/一个Micro-HNSW/一次原NSG。用户随后要求接近结束则当晚给短结论、明天继续，因此本轮完成后收口，不等待原07:00时间自动扩实验。','',
        '固定A0=E24 matched Fast20K/GT1硬，A1=E24冻结WebVid GT10软T0.016201138496398926、Yandex GT10硬；`Wα=normalize((1−α)W0+αW1)`，只有α0.25/0.50/0.75。float64混合归一化、float32导出，0/1端点bit复制。固定原base/raw-IP/NSG、seed20260828、H815/821、Micro-HNSW M16/efC200/ef10，三个唯一真实ID升序。Fast30K仍保留其旧30K/seed100/heap身份。','',
        '旧E09已使用top32真实single效用来聚合signed query残差；本轮仅插值E24既有几何画像，无新监督或训练，不复用旧residual/probe/C runner，不主张插值本身新颖。历史04及其原manifest/builder/结果已核对。','',
        '## 数据、冻结和统计合同','',
        '原E24 fit20K不变；新cal原router_train[6144,8192)共2048，audit[8192,10000)共1808，避开E25 cal/audit且不进入E24 fit。W、代码和cal输入先冻结，cal选定两数据集alpha及全部候选后再次全局冻结，再导出audit；audit只报告。随后原历史validation前2000，held-out不读取或hash。开发池有历史使用，validation已被E24/E25使用并启发本追问，不称盲测。','',
        'cal/audit每query配对A0/A1/三alpha，在L64/128真实运行原kernel。连续画像会产生第三套入口，故R/Rh只承认原收益保留，A_all/Ah_all计算包括新损伤的全部负事件/幅度减少。目标R/Rh≥75%、A_all/Ah_all≥25%，且净命中≥max(0,A1净命中)。cal若均不达标，按四项最差归一化比率S及净命中/受损/入口变化/小alpha ties选最接近者作反证；不把它升级为通过。','',
        '## 实际结果','',
        '两个数据集都选择alpha0.75，但三个候选在cal均未达联合目标；冻结主选择在audit和validation也未达标。合并L64/128的完整主结果：','',
        *table(['数据集','分段','R','Rh','A_all','Ah_all','净命中 vs A0 / A1原净命中'],stages),'',
        *decomposition,'',
        '损失恒等式逐query核对：原损失−避免原损失+新增/加重损失=新总损失。WebVid validation若只看“旧损失避免”可报28.98%，算上104个新增/加重损失后实际总损失只减少9.28%；Yandex从47.03%降至24.32%。不能只挑救回的旧坏query来称成功。','',
        '五L相对本轮同时重测A1/E24，Recall pp与QPS中位数变化：','',
        *table(['数据集','L','ΔRecall pp','ΔQPS %'],delta),'',
        '十点九个Recall下降，唯一正值WebVid L800仅+0.005pp且QPS下降；没有同L Recall与三轮QPS都正。WebVid L64为−0.495pp，描述性配对query95%区间[−0.940,−0.085]，其余九点跨0；未经多重比较校正。相对matched Fast20K仍保留少数局部正值，但不能替代与A1的对照。所有基线、三次计时、每轮实测非支配点和三alpha开发负点完整保存。','',
        '## 机制与成本','',
        '插值保持画像连续，并不保证HNSW前三入口、主搜索命中或NDC单调。结果按same_both/A0_only/A1_only/third_entry_set分组；实际三入口相同的所有query，其返回ID/距离bits/命中和graph NDC均一致。第三套入口既会带来新收益也会制造新损伤；尚未分离精确排序变化和HNSW近似路径的因果贡献。','',
        'validation按任一L受损去重，WebVid原144→124条、Yandex45→33条；原有效query保留分别103/158、33/47。query跨L可同时有正负效应，这组诊断不替换协议事件口径。E25/E26只在相同原query/GT/A0/A1结果上连接质量分解，不跨轮混QPS或重新挑模型。','',
        'L128 A1→Shrink route-only：WebVid6.432→6.562μs/query、Yandex4.410→4.375；独立端到端wall约502.631→504.577、515.266→517.249μs/query。分项不相加作QPS。新三alpha及两端点复制产物构建WebVid0.0733s、Yandex0.0263s；部署一W一微型图，无门控/双路/额外特征。', '',costline,'',
        '正常调用分解：恢复1600、cal82240、audit72640、validation700800、L128分项40000。修复预留16384未用；单job1800s、查询进程合计7200s、RSS40GiB、新产物1GiB、free10GiB上限均满足。原GT/QGT/NSG/E24从零成本未重测，保留null，不把复用说成零。','',
        '## 验收、解释范围与接续','',
        '110点177760输出独立GT10评分；四条原validation曲线80000输出与E25的ID/距离bits/入口/route和graph NDC逐位回归。三次plain、count、前16query原wrapper、非法线程拒绝、实际CPU15/线程1、五L同图同入口、W数值/端点、选择ties及冻结先后均通过。115项原资产全hash验证保留，包括E25封存交付。','',
        '这是受限全局收缩反证，不是所有选择性路由不可行。尚无稳定低成本规则同时保留75%收益、减少25%损失并改善Recall–QPS。今晚不加密alpha/阈值、不加模型、不复跑旧队列；明日先判断正负改道是否有可区分证据，再决定是否新机制。长期2A/联合评分/效率等未执行分支保留在s-target。','',
        '## 原始证据','',
        f'- [报告](../{b}/report.md)、[所有原值](../{b}/results/tables.md)、[分析](../{b}/results/analysis.json)、[成本](../{b}/results/costs.json)。',
        f'- [协议](../{b}/protocol.md)、[用户时间更新](../{b}/authorization_update.md)、[commands](../{b}/commands.md)、[状态](../{b}/state.json)。',
        f'- [cal前冻结](../{b}/models/frozen_before_cal.json)、[audit前冻结](../{b}/models/frozen_before_audit.json)、[完整性](../{b}/reviews/immutable_integrity.json)、[最终验收](../{b}/reviews/final_audit.json)。',
        f'- [收益和损失图](../{b}/figures/gain_loss_decomposition.svg)、[Recall–QPS](../{b}/figures/recall_qps.svg)、[损失迁移](../{b}/reviews/validation_entry_transitions.json)、[跨版本质量](../{b}/results/cross_experiment_quality_only.json)。']
    (ROOT/'experiment_history/15_profile_shrinkage.md').write_text('\n'.join(history)+'\n')
    p=ROOT/'experiment_history/README.md';text=p.read_text();marker='\n## 写入规则'
    assert text.count(marker)==1;text=text.replace(marker,'| [15 单路画像收缩](15_profile_shrinkage.md) | E26：三alpha、全体新损伤收费、50点三次单线程wall；未稳定保留收益并减少损失 |\n'+marker);p.write_text(text)
    text=originals['s-experiment.md'];marker='| E25 两固定画像的选择性改道 |'
    assert text.count(marker)==1;text=text.replace(marker,f'| E26 单路画像收缩 | E24两端点间三alpha；新cal/audit、冻结alpha0.75、validation50点三次单线程wall及新增损失分解 | `{STATUS}`；损伤减少伴随收益流失和新损伤，十点九个Recall低于E24；本版本收口 | [15 画像收缩](experiment_history/15_profile_shrinkage.md) |\n'+marker)
    text=text.replace('当前最近实验已为E25','当前最近实验已为E26').replace('十四份详细卡片','十五份详细卡片');(ROOT/'s-experiment.md').write_text(text)
    summary=['# ACSG 当前实验总结','',f'> 更新至2026-09-10夜间。最近E26已完成；本轮E25/E26共同检验选择性保留改道。实现见[spec.md](spec.md)，接续见[s-target.md](s-target.md)，历史见[s-experiment.md](s-experiment.md)。','',
        '## 当前结论','',
        f'**尚未得到稳定保留有效改道、减少受损查询并改善端到端性能的方法。** E25门控在WebVid小幅修复质量但增加时间，在Yandex丢掉大多数收益；E26单路画像收缩消除了双路结构成本，却同时损失有效改道并产生新损伤。E26状态`{STATUS}`，全部预定阶段收口。','',
        '## E26实际方法与选择','',
        '固定A0=E24 matched Fast20K/GT1硬，A1=E24按旧cal选定WebVid GT10软、Yandex GT10硬。只测试`normalize((1−α)W0+αW1)`的α0.25/0.50/0.75，在线一份画像图、一次路由、一次原NSG；H/base/raw-IP/NSG不变，没有新训练或全H标签。两数据集均按cal规则冻结α0.75，但三个候选在cal都未达目标，audit与validation也未达标。','',
        '## 收益保留与损失迁移','',
        'validation合并L64/128，单位query×L事件。R/Rh分别为原正事件/正命中保留；A_all/Ah_all为包含新增损伤的全部受损事件/负命中净减少。目标前两项≥75%、后两项≥25%，且净命中≥max(0,A1净命中)。','',
        *table(['数据集','R','Rh','A_all','Ah_all','净命中 vs A0 / A1原净命中'],validation),'',
        *decomposition,'',
        '按两个L任一受损去重，WebVid144→124条、Yandex45→33条，但原有效query仅保留103/158、33/47。事件数、幅度和独立query口径分开，不能只报“受损更少”。新画像可产生第三套入口；相同实际三入口的所有结果bits和graph NDC相同已验收。','',
        '## 单线程五点性能','',
        '相对本轮同时重测的A1/E24；QPS为三次独立warm/plain中位数。','',
        *table(['数据集','L','ΔRecall pp','ΔQPS %'],delta),'',
        '十点九个Recall下降，唯一正值WebVid L800仅+0.005pp且QPS下降；无稳定同L双升。WebVid L64描述性95%配对query区间[−0.940,−0.085]pp，其余九点跨0；未多重校正，单构建历史validation不足以正式GO。NSG/Fast30K/Fast20K和全部原值、每轮前沿均保留，不用粗网格连线宣称等Recall加速。','',
        '## 与E25合看','',
        'E25状态`SELECTIVITY_NOT_GENERALIZED_NO_FORMAL_GO`。WebVid主DualGate在validation保留80.66%有效事件、避免24.77%受损事件，相对A1五L质量+0.025～+0.090pp，但QPS−1.01%～−6.50%。Yandex主BaseGate避免62.90%受损事件，却只保留31.08%有效事件。E25全部20个门控vsA1 Recall差区间跨0，无三轮一致同L双升。两版本质量用同query/A0/A1连接，计时仍各自独立。','',
        '## 执行、成本和证据边界','',
        'E26 cal为router_train[6144,8192)2048，audit[8192,10000)1808，均不参与E24 fit20K；W先冻结，cal选择后全局冻结，再audit，最后历史validation前2000。cal/audit有历史开发使用，validation已用于E24/E25并启发本追问；held-out未打开。所有三alpha开发点及冻结选择保留。','',
        'E26五方法×五L×两数据集50点，各三次计时；110点177760输出独立评分，四条原曲线80000输出与E25逐位回归，115项上游hash与数值/选择/入口/图/线程均通过。'+costline,'',
        'L128 A1→Shrink路由单测WebVid6.432→6.562μs、Yandex4.410→4.375μs；分项不能相加为QPS。新三alpha及端点产物构建0.0733/0.0263s。原GT/QGT/NSG/E24从零成本未新测。E25真实调用1089152、合成5144、修复0；原结果完整封存。','',
        '## 权威交付与接续','',
        f'- [E26完整报告]({b}/report.md)、[全部原值]({b}/results/tables.md)、[Recall–QPS]({b}/figures/recall_qps.svg)、[损失分解]({b}/figures/gain_loss_decomposition.svg)、[最终验收]({b}/reviews/final_audit.json)、[历史15](experiment_history/15_profile_shrinkage.md)。',
        '- [E25完整报告](entry_method_exploration/20260910_selective_profile_gate_v1/report.md)、[历史14](experiment_history/14_selective_profile_gate.md)；E24局部正信号见[历史13](experiment_history/13_gt_topk_profiles.md)。','',
        f'用户最新要求接近结束则当晚给短结论、明天继续，见[时间更新]({b}/authorization_update.md)。今晚收口，不继续等待原07:00或扩alpha/模型。明日先判断正负改道是否存在稳定可区分信号，再决定新机制；长期分支保留在s-target，未自动启动。']
    (ROOT/'summary.md').write_text('\n'.join(summary)+'\n')
    spec=originals['spec.md'].replace('E25两固定画像的搜索前选择、真实配对监督及60点三次单线程计时已验收','E26单路画像收缩、全体新增损伤统计及50点三次单线程计时已验收')
    spec+=f'''

## 单路画像收缩 v1（2026-09-10夜间）

独立[E26协议]({b}/protocol.md)复用E24 A0/A1，不修改原builder、kernel、E25门控或其封存产物。在线接口仍为单份GT-free `Policy`，没有学习门控或在线插值。

- [build_profiles.py]({b}/src/build_profiles.py)：同hub的既有float32端点数值作float64 `(1−α)W0+αW1`和L2归一化后导出float32，固定α0.25/0.50/0.75；0/1端点直接bit复制，混合范数finite且>1e−12，否则拒绝。保存W/hash、几何变化和构建成本，不新增fit或GT训练标签。
- [evaluate.cpp]({b}/src/evaluate.cpp)：薄封装原单路Policy，支持NSG/Fast30K/Fast20K/E24及alpha画像；原NSG不改。matched三真实ID升序，一画像一微型图，原Fast30K legacy顺序保留。每point三次独立warm/plain总wall，全批count及16条原wrapper在timer外；L128 route/graph分项不相加为总wall，所有raw输出完成后才读取GT评分。
- [effect_stats.py]({b}/src/effect_stats.py)：`d1=hA1−hA0, da=hα−hA0`；R按原正事件保留，Rh用`sum min(da+,d1+)/sum d1+`；A_all=`1−count(da<0)/count(d1<0)`，Ah_all=`1−sum da−/sum d1−`。总损失包含新产生/加重损伤，可为负比例；另保存原损失避免、新损失、丢失原收益、新收益的逐query恒等式，分母0为undefined。辅助unique query统计不参与选择。
- [select_alpha.py]({b}/src/select_alpha.py)：只用新cal L64/128，先选达标者，否则以最差四项归一化比率S选最接近反证项，再依净命中/受损事件/负幅度/入口变化/小α打破ties。cal失败状态保留，不能用audit/validation更换。W/cal输入与源码先冻结，再冻结全部cal候选和主α；audit后才准备历史validation。
- [verify_outputs.py]({b}/src/verify_outputs.py)、[check_transitions.py]({b}/src/check_transitions.py)：独立GT评分/合法ID/三入口、plain/count和原wrapper；四条原曲线回归E25，五L入口不变。新α入口相同于某端点时，结果ID/距离bits/hits/mask/graph NDC须相同；第三套入口分组只解释，不成为新选择特征。
- [jobs.py]({b}/src/jobs.py)：继承CPU15/实际线程1、失败完整预留、identity/RSS/时间/磁盘与调用硬限制；正常897280、修复16384、合成≤4096。仅固定新cal2048/audit1808及历史validation2000，无新fit/全H标签或held-out访问。

W、H映射、Micro-HNSW参数/seed/顺序、原NSG/kernel、query/GT、L或metric改变均须按依赖重建相应结果/选择/计时；不能复用旧命中差模拟新alpha。只读跨E25质量连接须先验证相同query/GT/A0/A1结果，QPS仍来自各自独立轮次，不跨轮拼接。

实现验收完成110点177760输出、四基线80000输出bit回归、115项上游hash、六份中间W独立标量参考及cal选择ties复核。全部8真实job完成，50正式点各三次单线程wall；数值/计量验收不构成性能GO。结果见[summary](summary.md)及[E26报告]({b}/report.md)。
'''
    (ROOT/'spec.md').write_text(spec)
    target=f'''# ACSG 下一阶段方向与实验接续

2026-09-10夜间。E25/E26均完整收口；最近E26状态`{STATUS}`。用户最新要求接近结束则当晚给短结论、明天继续，见[时间更新]({b}/authorization_update.md)。今晚不继续等待原07:00、不新开实验；原protocol/E25授权文本保留当时历史。全部长期分支在第4节，不是一张自动执行队列。

## 1. 最近结果给出的判断

E25两类门控与E26单路收缩都未建立跨数据集稳定的收益保留/损失减少与端到端改善。E25 WebVid保留较多收益但路由成本抵消小幅质量修复，Yandex减少损伤时失去大多数有效改道。E26两数据集cal冻结α0.75，cal/audit/validation均未达联合目标；validation有效事件保留64.62%/68.92%、全部受损事件净减少14.02%/22.58%，十点九个Recall低于E24，无稳定同L双升。

这些结果不支持继续仅加密当前门控阈值或全局alpha，也不能证明效用普遍不可学习。连续缩小画像会产生第三套入口，旧损失被避免与新增损伤必须同时记录。完整事实分别见[E25报告](entry_method_exploration/20260910_selective_profile_gate_v1/report.md)、[E26报告]({b}/report.md)、[历史15](experiment_history/15_profile_shrinkage.md)；summary保持当前精简结论。

## 2. 当前冻结资产与继续时的对照

- E24画像、E25门控和E26三个alpha/两端点均封存；E26两数据集统一冻结alpha0.75不是默认部署推荐。原base/raw-IP/NSG、QGT seed20260828、H815/821和三个唯一真实入口不变。
- E26未训练或生成全H/single/triple新标签；cal[6144,8192)2048/audit[8192,10000)1808不参与E24 fit20K，但具有历史开发使用。历史validation前2000已用于E24/E25/E26；下一方法须披露该历史，不能称新盲测，held-out仍不自动打开。
- E26正常897280真实调用、修复0、合成2268，全部阶段结束；E25正常1089152、E24正常543296均已独立用完并收口。任何旧预算、未使用修复额度或时间授权都不是新队列预算。
- 后续新方法保留matched Fast20K、E24按旧cal冻结的主画像及相关GT10硬/软对照；Fast30K另列30K/seed100/顺序身份。E25/E26可作对应机制参照，不按旧validation重新挑主规则。

## 3. 明日建议与进入边界

明日先围绕已有正负改道分解和真实效用标签，判断收益与损伤是否有稳定、低成本的可区分信号，再决定下一独立方法。E25与E26原query级输出、损失迁移、案例、冻结模型和计时已保存，不必复跑整轮来找回事实；不能先增加门控容量或alpha网格再解释结果。

长期优先级仍是第4.1的2A：固定H，以真实finite-L作用组织可预测分组，并保留旧single赢家centroid和E24几何画像对照。E08已有single赢家重聚合，E23已有真实三入口标签/排序；若选择2A，先说明软/可预测分组或条件联合作用的实质区别与旧标签兼容性。single只能提供分组/候选，三个入口的结果必须真实联合搜索，不能以命中并集代理。

若更适合研究联合集合评分、微型图效率、聚类、rank或范数消融，按第4节对应分支另定小协议，避免同时改变监督、H、画像和搜索器。E24 audit exact−HNSW主候选仅WebVid+0.146pp/Yandex−0.020pp，路由单测约占总wall的1%，当前没有微型图是主要瓶颈的证据。

所有新正式查询继续单线程、每次一个方法、独立端到端plain wall，全部路由计算收费。新模型/参数在使用其评估数据前冻结。今晚E25/E26收口不自动启动2A、新H、C/probe、标签或其它长队列。

## 4.'''+originals['s-target.md'].split('## 4.',1)[1]
    target=target.replace('- 最近完成E25：','- 已完成E25：')
    marker='- 已完成E25：';target=target.replace(marker,f'- 最近完成E26：[报告]({b}/report.md)、[协议]({b}/protocol.md)、[固定选择]({b}/models/frozen_before_audit.json)、[历史15](experiment_history/15_profile_shrinkage.md)、[用户收口更新]({b}/authorization_update.md)。\n'+marker)
    target=target.replace('再读E24完整报告、四问题调研以及历史04/05/08/12/13指向的相关原始证据。','再读E24/E25/E26完整报告、四问题调研及历史04/05/08/12/13/14/15的相关原件。')
    (ROOT/'s-target.md').write_text(target)
    dump(RUN/'reviews/document_update.json',{'status':'PASS','before':before,
        'after':[identity(ROOT/p) for p in [*originals,'experiment_history/README.md','experiment_history/15_profile_shrinkage.md']],
        'order':'history15 and indexes, then current summary/spec/target','long_term_target_section4_and_later_preserved_with_new_evidence_links':True,
        'original_E25_root_docs_preserved_in_source_before':True})
    print('E26_ROOT_DOCUMENTS_AND_HISTORY_UPDATED',flush=True)


if __name__=='__main__':main()

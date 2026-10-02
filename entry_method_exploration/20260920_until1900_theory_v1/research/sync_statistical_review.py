from pathlib import Path
import json,csv,hashlib,shutil,time,re
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
review=TB/'reviews/statistical_review_complete.json';assert not review.exists()
notes=['prior_work_and_representation_exclusions.md','weighted_mean_statistical_scope.md','terminal_closure_implications.md',
       'missing_target_mass.md','score_anchor_geometry.md','objective_quantization_v1/report.md','score_anchor_geometry_v1/report.md']
files=[TB/'research'/p for p in notes]
for name in ['objective_quantization_v1','score_anchor_geometry_v1']:
    r=TB/'research'/name;c=read(r/'config.locked.json');done=read(r/'complete.json');assert done['status']=='PASS'
    for x in c['source_files']+done['outputs']:
        assert ident(x['path'])==x,x['path']
    files.extend([r/'config.locked.json',r/'complete.json',r/'analyze.py',r/'protocol.md']);files.extend(Path(x['path']) for x in done['outputs'])
source=TB/'research/source_support_v1';target=list(csv.DictReader((source/'target_support.csv').open()));overlap=list(csv.DictReader((source/'source_target_overlap.csv').open()))
missing_rows=[]
for x in overlap:
    t=next(t for t in target if t['dataset']==x['dataset'] and t['role']==x['source'])
    estimate=100*int(t['GT1_singleton_IDs'])/int(t['n']);observed=100-float(x['target_GT1_in_source_GT1_pct'])
    missing_rows.append(dict(dataset=x['dataset'],source=x['source'],target=x['target'],source_n=int(t['n']),
        Good_Turing_IID_reference_pct=estimate,observed_unseen_GT1_pct=observed,observed_minus_reference_pp=observed-estimate,
        strict_confidence_or_IID_claim=False))
dump(TB/'reviews/missing_mass_numeric_table.json',dict(status='RECOMPUTED_FROM_SEALED_CSV',source_files=[ident(source/p) for p in ['target_support.csv','source_target_overlap.csv']],rows=missing_rows,new_payload_access=False))
files.append(TB/'reviews/missing_mass_numeric_table.json')
hist=ROOT/'experiment_history/112_statistical_objective_review.md';assert not hist.exists()
hist.write_text('''# 112｜统计目标、教师量化与锚定几何审查

2026-09-20，纯理论/历史复核及两项只读缓存分析；不是新的性能候选。E114完成后，继续明确GT10的统计意义与学习器失败的解释边界。0新NSG/ANN/GT/图/训练；默认Web soft/Y hard、生产E99保持。

GT10归一化加权平均不需要vMF假设即可给出单位query均值的方差恒等式与总体亲和风险界；须条件于固定H和IID query，GT10的十个目标不是十个独立样本。方向一致性和支持量共同影响估计，仍无真实搜索效用保证。Good–Turing单例统计与旧未见GT1比例数量级相符，表明精确目标ID记忆很稀疏；这不是GT10/图搜索的Recall上界或IID验证。

5120条旧fit/cal、56动作整数审查确认原等K最大值teacher等价于先最大K1再最大K100。两集cal的单独K100 oracle相对原teacher只多0.185547/0.064453pp；原teacher的更大收益本已存在，不能用按K拆模型解释学生未迁移。全部旧oracle/teacher harm比例恢复，0.128秒。

旧WFree分数锚定的矩阵形式及监督支持核验：cal/E105平均平方漂移相对fit为Web0.9356/0.9314、Y0.9752/0.9759，没有整体放大。最坏方向协方差界与实际模型漂移分开；每hub非恒定C8教师支持中位数13/10，全部少于参数维度，但全H锚定仍约束模型，未作失败因果定论。10,889,216个旧模型分数残差坐标，0.411秒，原fit漂移与矩阵恒等式恢复。

源码回查确认全H集合CE、结构化margin、保留teacher、多teacher、延长优化、精确期望真实收益及query二阶矩构图均已有实测版本；固定线性图特征/线性双塔还需排除评分折叠等价。不能把换损失、网络名称或统计量当成新的方法贡献。终点闭合的后处理无变化结论明确依赖边界tie保留；不同ID并列可带来不同后续出边。

[统计推导](../entry_method_exploration/20260920_until1900_theory_v1/research/weighted_mean_statistical_scope.md) · [缺失目标质量](../entry_method_exploration/20260920_until1900_theory_v1/research/missing_target_mass.md) · [教师审查](../entry_method_exploration/20260920_until1900_theory_v1/research/objective_quantization_v1/report.md) · [锚定审查](../entry_method_exploration/20260920_until1900_theory_v1/research/score_anchor_geometry_v1/report.md) · [前作排除](../entry_method_exploration/20260920_until1900_theory_v1/research/prior_work_and_representation_exclusions.md) · [终点后处理边界](../entry_method_exploration/20260920_until1900_theory_v1/research/terminal_closure_implications.md)。
''')
docs=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md'];before=TB/'reviews/statistical_review_documents_before';before.mkdir()
for rel in docs:
    p=ROOT/rel;dest=before/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
def prepend(rel,txt):
    p=ROOT/rel;head,rest=p.read_text().split('\n\n',1);p.write_text(head+'\n\n'+txt+'\n\n'+rest)
prepend('summary.md','2026-09-20 **统计与学习目标审查完成**：GT10的条件均值解释扩展到无需vMF的IID亲和风险界，但未得到真实Recall保证；精确GT1目标的缺失质量与旧支持统计相符。原等K teacher按query等价于K1优先，cal分K最多额外0.186/0.064pp K100，解释不了学生主要迁移缺口；旧WFree后续query平均分数漂移未放大，每hub潜在有效教师支持中位数13/10。两项缓存统计0.128/0.411秒、0新搜索/训练。已有全H CE、结构化loss及二阶矩构图等不重复启动；默认保持。[记录112](experiment_history/112_statistical_objective_review.md)。')
prepend('spec.md','2026-09-20 新增两项独立只读研究审查：[教师整数统计](entry_method_exploration/20260920_until1900_theory_v1/research/objective_quantization_v1/complete.json)核验5120条query的字典序teacher及旧oracle；[锚定矩阵统计](entry_method_exploration/20260920_until1900_theory_v1/research/score_anchor_geometry_v1/complete.json)核验全H平方分数漂移、二阶矩trace与候选支持。均锁定旧输入/源码SHA，E105仅用已曝光query，不新增GT/图/搜索/训练或生产API。结果解释见summary/记录112。')
prepend('s-experiment.md','2026-09-20 **统计/目标审查（非性能实验）**：无需vMF的亲和风险、缺失目标质量、原teacher K1优先性质、WFree锚定与支持；两项缓存审查0新搜索/训练，未找到重开旧模型的依据。[记录112](experiment_history/112_statistical_objective_review.md)。')
p=ROOT/'experiment_history/README.md';s=p.read_text().replace('|---|---|\n','|---|---|\n| [112 统计与学习目标审查](112_statistical_objective_review.md) | 条件均值/缺失质量、教师量化和锚定几何，0新搜索/训练 |\n',1);p.write_text(s)
p=ROOT/'s-target.md';s=p.read_text().replace('后继归纳真实终点迁移、统计共享与既有损失/构图前作，无新模型队列；','统计/teacher/锚定审查与前作排除完成，后继整理真实终点迁移及跨query共享的证据缺口，无新模型队列；',1);p.write_text(s)
links=0
for p in files+[hist]+[ROOT/x for x in docs]:
    if p.suffix!='.md':continue
    for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if '://' in dest or dest.startswith('#'):continue
        assert (p.parent/dest.split('#')[0]).resolve().exists(),(p,dest);links+=1
dump(review,dict(status='PASS',created_unix=time.time(),files=[ident(p) for p in files]+[ident(hist)],
    documents_after=[ident(ROOT/x) for x in docs],local_links_checked=links,new_NSG=0,new_ANN=0,new_GT=0,new_graphs=0,new_training=0,
    analytic_seconds=[read(TB/'research'/x/'complete.json')['seconds'] for x in ['objective_quantization_v1','score_anchor_geometry_v1']],
    default_changed=False,overall_goal_complete=False))
state=read(TB/'state.json');state['stage']='Statistical and loss review complete; consolidate theory and remaining method gap';dump(TB/'state.json',state)
print(json.dumps(dict(status='PASS',local_links=links,files=len(files)),indent=2))

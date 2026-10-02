from pathlib import Path
import json,csv,hashlib,shutil,time,re
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1];R=TB/'stages/e114_terminal_peaks'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
assert not (R/'complete.json').exists();job=read(R/'reviews/job.json');v=read(R/'reviews/numeric_verification.json')
assert job['exit_code']==0 and not Path('/proc',str(job['pid'])).exists() and v['status']=='PASS'
checked={}
for rows in [read(R/'reviews/input_sources.json')['files'],read(R/'reviews/source_freeze.json')['files'],read(R/'reviews/protected_before.json'),v['result_files']]:
    for x in rows:assert sha(x['path'])==x['sha256'],x['path'];checked[x['path']]=x['sha256']
for c in read(R/'config.locked.json')['datasets'].values():
    st=Path(c['index']).stat();assert st.st_size==c['index_stat']['bytes'] and st.st_mtime_ns==c['index_stat']['mtime_ns']
s=(R/'report.md').read_text();s=s.replace('figures/terminal_peaks.png','figures/terminal_peaks.v2.png').replace('figures/terminal_peaks.pdf','figures/terminal_peaks.v2.pdf')
(R/'report.md').write_text(s)
dump(R/'reviews/figure_visual_review.json',dict(status='PASS',reviewer='root visual inspection',
    initial_issue='Initial legend overlapped x-axis label',initial_preserved=True,
    revised_source=ident(TB/'research/plot_e114_v2.py'),figures=[ident(R/'figures'/p) for p in ['terminal_peaks.v2.png','terminal_peaks.v2.pdf']],
    actual_png_viewed=True,labels_legends_axes_readable=True,no_numeric_change=True,
    report_before=ident(R/'reviews/report_before_figure_v2.md')))
hist=ROOT/'experiment_history/111_terminal_local_optima.md';assert not hist.exists()
hist.write_text('''# 111｜E114搜索终点的局部最优性质

2026-09-20。**TERMINAL_LOCAL_OPTIMA_VERIFIED**。先从当前kernel的池维护/完整展开/游标终止推导：固定得分下，返回topK的出邻居不存在可严格改善topK得分的外部节点；K1返回点是局部最优。该性质依赖完整展开，无附加提前停止；不是当前NSG全局单调图的证明。

仅复用E107两集全部4096条曝光query、8方法、真实K1/L128返回。按query去重5059/4516个终点，扫描60877/129232条出邻接；全部非同向量边得分差由保守float64误差界确认为正，0违反。预定32query共818条边独立fsum一致，16原R1/失败点完全恢复。Web保留同向量不同GT1 ID的原评分。

八方法在Web79.6875%、Y90.6006%的query落到同一ID；默认失败中532/1011、202/384八方法都落到同一错误终点。默认相对固定单入口恢复/损伤query为278/103、144/78，对应旧R1净+4.2725/+1.6113pp。八种有限策略的特权联合可额外恢复269/133条，非部署、非全H上界。相同K1终点不推断K100/路径/NDC/wall相同。

0新NSG/ANN/GT/图/训练/QPS；分析4.843秒、外层4.971秒，RSS5.288GiB。初始内积计数字段重复计了缓存GT引用，单独核算说明更正，原源码/JSON保留且无重跑。首版图例重叠已保存并修为v2，数据不变。默认Web soft/Y hard、生产E99保持；整体任务继续至19:00。

[完整报告](../entry_method_exploration/20260920_until1900_theory_v1/stages/e114_terminal_peaks/report.md) · [理论](../entry_method_exploration/20260920_until1900_theory_v1/stages/e114_terminal_peaks/research.md) · [全部方法对](../entry_method_exploration/20260920_until1900_theory_v1/stages/e114_terminal_peaks/results/pairs.csv) · [计数澄清](../entry_method_exploration/20260920_until1900_theory_v1/stages/e114_terminal_peaks/reviews/distance_count_clarification.json)。
''')
docs=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']
before=R/'reviews/closeout_documents_before';before.mkdir()
for rel in docs:
    p=ROOT/rel;dest=before/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
def prepend(rel,text,replace=False):
    p=ROOT/rel;head,rest=p.read_text().split('\n\n',1)
    if replace:rest=rest.split('\n\n',1)[1]
    p.write_text(head+'\n\n'+text+'\n\n'+rest)
prepend('summary.md','2026-09-20 **E114终点局部最优核验完成**：全部9575个query/终点、190109条原图出邻接支持条件推导，0新搜索。Web/Y八种旧入口策略在79.6875%/90.6006%的query落到同一节点；默认失败中532/1011与202/384都落到同一错误节点。它解释入口改变常未改变终点，但不证明其他入口无效，也不替代K100/wall。E112首行H、E113具体比较对字典均已按门停止；默认和生产E99保持，继续理论归纳与既有方案排除。[报告](entry_method_exploration/20260920_until1900_theory_v1/stages/e114_terminal_peaks/report.md) · [记录111](experiment_history/111_terminal_local_optima.md)。',True)
prepend('spec.md','2026-09-20 E114独立[只读终点审查器](entry_method_exploration/20260920_until1900_theory_v1/stages/e114_terminal_peaks/src/analyze.py)完成：解析原native NSG的图/向量mmap，复用E107真实K1/L128返回，按query去重终点后核验邻接得分/误差界/局部半径及方法对关系；16原指标和预定独立fsum恢复。0新搜索/图/模型，计数缓存引用单独澄清，未改生产API。[契约与结果](entry_method_exploration/20260920_until1900_theory_v1/stages/e114_terminal_peaks/report.md)。',True)
prepend('s-experiment.md','2026-09-20 **E114终点审查完成**：9575个query/终点无更高分出邻居，八策略约79.7%/90.6%同终点；有限方法范围的终点关系，不是全入口不可能性。0新搜索/训练、分析4.843秒，默认保持。[记录111](experiment_history/111_terminal_local_optima.md)。')
p=ROOT/'experiment_history/README.md';text=p.read_text().replace('|---|---|\n','|---|---|\n| [111 搜索终点局部最优](111_terminal_local_optima.md) | E114：旧返回邻接核验，终点一致与增损，0新搜索 |\n',1);p.write_text(text)
p=ROOT/'s-target.md';text=p.read_text().replace('后继只审查更抽象的共享机制与既有损失/构图前作，无新模型队列；','E114终点必要性质及全部旧K1返回邻接已核验；后继归纳真实终点迁移、统计共享与既有损失/构图前作，无新模型队列；',1);p.write_text(text)
links=0
for p in [R/'report.md',R/'protocol.md',R/'research.md',hist]+[ROOT/x for x in docs]:
    for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if '://' in dest or dest.startswith('#'):continue
        assert (p.parent/dest.split('#')[0]).resolve().exists(),(p,dest);links+=1
dump(R/'reviews/documents_after.json',[ident(ROOT/x) for x in docs]+[ident(hist)])
dump(R/'reviews/completion_audit.json',dict(status='PASS',source_input_result_files=len(checked),job_closed=True,
    local_links_checked=links,report=ident(R/'report.md'),numeric_verified=True,figure_v2_visually_verified=True,
    count_correction_preserves_original=True,NSG_calls=0,ANN_calls=0,new_GT=0,new_graphs=0,new_training=0,
    default_changed=False,overall_goal_complete=False))
dump(R/'state.json',dict(status='COMPLETE',decision='TERMINAL_LOCAL_OPTIMA_VERIFIED',pending=[],NSG_calls=0))
dump(R/'complete.json',dict(status='COMPLETE',completed_unix=time.time(),decision='TERMINAL_LOCAL_OPTIMA_VERIFIED',
    NSG_calls=0,ANN_calls=0,new_GT=0,new_graphs=0,new_training=0,report=ident(R/'report.md'),audit=ident(R/'reviews/completion_audit.json')))
state=read(TB/'state.json');state['stage']='E114 closed; statistical theory and prior-work synthesis';dump(TB/'state.json',state)
print(json.dumps(read(R/'reviews/completion_audit.json'),indent=2))

import pathlib,json,hashlib,datetime,statistics,shutil,difflib
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent;E=D.parent/'20260915_gate_l2_r1_r100_v1'
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
state=json.loads((D/'state.json').read_text());assert state['search_calls']==550000
calls=0;rounds=0;rss=[]
for v in ['original','prefetch','active_pool','combined','original_only']:
 c=json.loads((D/f'results/{v}/complete.json').read_text());assert c['status']=='PASS' and c['threads']==1 and c['cpu']==15 and c['e97_bit_parity'];calls+=c['search_calls'];rounds+=len(c['timings']);rss.append(c['maxrss_kib'])
for v in ['prefetch','active_pool','combined']:
 c=json.loads((D/f'results/counts.{v}/complete.json').read_text());assert c['status']=='PASS' and c['threads']==1 and c['per_query_ndc_bit_output_parity'];calls+=c['search_calls']
 for name in ['route_ndc.u64','graph_ndc.u64']:assert (D/f'results/counts.{v}/{name}').read_bytes()==(E/f'results/webvid2_5m_light_v1/k100/GT10-soft-t1_L1250/{name}').read_bytes()
assert calls==550000 and rounds==36
rows=json.loads((D/'results/summary.json').read_text())['timing'];assert len(rows)==12
for r in rows:
 assert len(r['seconds'])==3 and abs(statistics.mean(10000/x for x in r['seconds'])-r['mean_qps'])<1e-9
check={name:pathlib.Path(name).stat().st_size==a['bytes'] and sha(pathlib.Path(name))==a['sha256'] for name,a in json.loads((D/'reviews/protected.json').read_text()).items()};assert all(check.values());save(D/'reviews/protection_check.json',check)
build=json.loads((D/'reviews/build.json').read_text());diffs=[p for p,h in build['files'].items() if sha(D/p)!=h];assert diffs==['src/build.py'],diffs
save(D/'reviews/build_manifest_amendment.json',{'unchanged_compiled_sources_and_native_binaries':True,'changed_script':diffs,'reason':'build.py made idempotent by reading the frozen E97 evaluator before patching; compiled translation units and binaries unchanged','current_script_sha256':sha(D/'src/build.py')})
patch=[]
a=(D/'src/ACSG.original.cpp').read_text().splitlines(True)
for v in ['prefetch','active_pool','combined']:patch+=list(difflib.unified_diff(a,(D/f'src/ACSG.{v}.cpp').read_text().splitlines(True),fromfile='ACSG.original.cpp',tofile=f'ACSG.{v}.cpp'))
(D/'reviews/kernel_diffs.patch').write_text(''.join(patch));assert sha(D/'src/ACSG.original.cpp')==sha(R/'ACSG/ACSG.cpp')
headline=(D/'reviews/headline.txt').read_text().strip();link='entry_method_exploration/'+D.name
card=R/'experiment_history/91_webvid_search_cost_diagnosis.md';assert not card.exists()
card.write_text(f'''# E98：WebVid GT10与完整HNSW搜索成本诊断

{headline}

## 动机与边界

用户问少算距离为何仍较慢，以及是否有实现未优化。以E97已有WebVid公开10K、完整2.505M/512d raw-IP底库、默认GT10-soft画像和冻结NSG/HNSW诊断；不训练、不改图、不更新默认。该公开测试已曝光，本轮不是新的泛化评估。主源码/库/E97历史结果保护SHA全部不变。

## 实际证据

K100/L1250每query约21.6us用于路由、4565us用于NSG搜索。GT10距离段含访存等待占77.31%采样；候选维护与libc复制合计7.66%，不能用候选队列解释全部差距。两种内积均AVX-512；相同随机地址流直接内积微基准约237.39/233.35ns，未见Faiss算术显著落后。

同加载方式原版223.74 QPS，预取241.22、有效候选池225.87、组合253.16。候选池单项0.95%在波动范围内；组合与预取有局部正值。三个控制完整10K返回ID/距离bits/三入口与逐query route/graph NDC均对齐E97，未减少搜索工作或损失召回。

原双方法进程中的HNSW参考267.38 QPS、Recall@100 90.3718%；GT10原/控制Recall@100均90.6868%。这只是单工作点成本诊断，不是优化后完整前沿，更不能外推跨五集。

## 计量修订、成本与后续

先运行双方法基础L100/400/1250与K1/L1250、分项/采样和三局部控制。发现基础与控制的存活内存不同后，追加同一original二进制的NSG-only匹配基线，并独立补全三个count一致性检查；两项修订记录在原协议，未扩方法/预算网格。共550000次search、36轮plain，另1600万次直接距离调用；主调度25.20分钟，匹配基线3.06分钟，编译/计数另记。进程/库1线程、CPU15串行。

优先优化NSG的邻居数据预取；候选维护属于次要工程项。尚未直接测硬件cache miss、TLB或隔离全部数据布局，剩余差距未完整解释。若正式采用，应先补等距/边界回归，再公平重测NSG/GT10/GATE等共用内核的方法，指标仍只Recall@1/100；本轮没有实施生产替换或重启旧研究分支。

[完整报告](../{link}/report.md) · [图](../{link}/figures/cost_diagnosis.png) · [协议与修订](../{link}/protocol.md) · [CSV](../{link}/results/timing_summary.csv) · [一致性验收](../{link}/reviews/completion_audit.json)
''')
updates={
 'summary.md':headline+f' [诊断报告]({link}/report.md) · [诊断图]({link}/figures/cost_diagnosis.png)。单独候选池控制不构成稳定加速结论；后续正式采用应公平重测所有共享NSG内核的方法。',
 'spec.md':f'E98已实现独立搜索成本诊断，位于`{link}/src/`：`diagnose.cpp`复用E97调用链，Router直接加载原小图；原ACSG源码复制编译为original/prefetch/active_pool/combined，原代码和库不改。所有plain按CPU15/线程1、warmup+3轮计完整wall，分项/SIGPROF/count独立；控制仅K100/L1250，追加同加载方式original_only基线。550000次search、36轮计时；返回ID/距离bits/入口及三个控制逐query NDC对齐E97。计时CSV与符号采样是独立诊断产物，不能回填E97正式QPS；主内核尚未部署这些优化。[合同与计量修订]({link}/protocol.md)、[验收]({link}/reviews/completion_audit.json)、[报告]({link}/report.md)。',
 's-target.md':f'E98性能归因任务已完成：[报告]({link}/report.md)。优先级转为共享NSG内核的预取与候选维护工程验证；路由仅0.47%，不以本次速度差距为由重训GT10。组合控制在WebVid K100/L1250局部提升13.15%，尚未部署或验证完整前沿；候选池单项约0.95%在波动范围内。若接续正式落地，先补等距/边界一致性回归，再按原单线程Recall@1/100协议公平重测全部受影响的NSG/GT10/GATE。当前没有待恢复的训练/评测进程，旧默认和E97封存不变。',
 's-experiment.md':f'E98（2026-09-16完成）：WebVid GT10-soft/完整HNSW成本诊断，550000次search、36轮plain。路由0.47%；预取+7.81%、组合+13.15%，单独候选池+0.95%在波动范围内；逐query NDC/输出一致，主代码与默认未改。[详细复盘](experiment_history/91_webvid_search_cost_diagnosis.md) · [报告]({link}/report.md)。'
}
for name,note in updates.items():
 p=R/name;old=p.read_text();head,rest=old.split('\n',1);p.write_text(head+'\n\n'+note+'\n'+rest)
p=R/'experiment_history/README.md';shutil.copy2(p,D/'source_before/experiment_history_README.md');t=p.read_text();t=t.replace('|---|---|','|---|---|\n| [91 WebVid搜索成本诊断](91_webvid_search_cost_diagnosis.md) | E98路由/图/采样与三个局部控制；550000search/36轮plain，预取与组合局部正值，主内核和默认未替换 |',1);p.write_text(t)
bytes_total=sum(p.stat().st_size for p in D.rglob('*') if p.is_file());assert bytes_total<1024**3
save(D/'reviews/completion_audit.json',{'status':'PASS','search_calls':calls,'plain_rounds':rounds,'plain_points':12,'output_bit_parity':'all warmup/timed/staged/sampled/count runs checked in native code','independent_per_query_ndc_bytes':'all 3 variants match E97','actual_threads':1,'cpu':15,'peak_rss_gib':max(rss)/1024**2,'new_bytes_before_final_manifests':bytes_total,'protected_unchanged':True,'compiled_original_matches_protected_source':True,'sample_counts':{'GT10-soft-t1':11690,'HNSW':9332},'defaults_unchanged':True,'no_training_or_new_graph':True,'root_docs_updated':list(updates),'history_card':str(card)})
state.update(status='COMPLETE_IMPLEMENTATION_DIAGNOSIS_NO_DEFAULT_CHANGE',analysis_completed_at=datetime.datetime.now().isoformat(),plain_rounds=rounds,report='report.md',maxrss_gib=max(rss)/1024**2);save(D/'state.json',state)
save(D/'figures/manifest.json',{p.name:sha(p) for p in (D/'figures').glob('*') if p.suffix in ['.png','.pdf']})
save(D/'complete.json',{'status':'PASS','search_calls':calls,'plain_rounds':rounds,'report_sha256':sha(D/'report.md'),'summary_sha256':sha(D/'results/summary.json'),'audit_sha256':sha(D/'reviews/completion_audit.json'),'defaults_unchanged':True,'completed_at':state['analysis_completed_at']})
print(json.dumps(json.loads((D/'reviews/completion_audit.json').read_text()),ensure_ascii=False,indent=2))

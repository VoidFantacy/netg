"""Synchronize current document roles, then validate and seal the new evidence."""
import csv,datetime,hashlib,json,os,re,shutil,struct,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];OLD=R.parent/'20261028_seven_dataset_scoring_v1';REL='entry_method_exploration/'+R.name
ROOTS=['summary.md','spec.md','s-target.md','s-experiment.md','LOCAL_CODEX_START.md','experiment_history/README.md','experiment_history/192_sharing_necessity_v1.md']
def read(p):return json.loads(Path(p).read_text())
def dump(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def rows(p):return list(csv.DictReader(Path(p).open()))
def docs():
 rec=read(R/'reviews/report_build.json');ip=read(R/'reviews/interpretation.json');text='\n\n'.join(ip['conclusions'])
 summary=f'''# ACSG 当前结论

更新于2026-10-29。用户要求证明“相似查询不共享邻域时是否无用”，E192已完成三集真实K100同窗口39点/117完整T1轮、36资格点，以及七集真实两K/L200旧实际包上的32次冻结重配诊断。默认E99 GT10保持：WebVid GT10-soft-t1、Yandex GT10-hard。

{text}

本轮把候选支持集的必要条件、表行对应关系的受控效应、已有方法的完整费用分别处理；没有把重配训练块表称为构造完全零共享数据集，也没有把旧源外救回等同于系统未用监督。集合上界与固定配置实测不外推所有ANN或GT10主搜索。

[证明与详细报告]({REL}/report_zh.md) · [严格推导]({REL}/theory.md) · [当前池理想上限的费用证书]({REL}/analysis/oracle_cost_certificates.csv) · [全部新计时点]({REL}/analysis/all_native_points.csv) · [七集支持上界]({REL}/analysis/support_bounds.csv)。

E191七集989点/2967轮及33页PDF保留原件；其7个有限网格未覆盖探索点仍不等于默认替换。完整当时根文档见[E192修改前快照]({REL}/source_before/summary.md)，原科学报告仍见[E191](entry_method_exploration/20261028_seven_dataset_scoring_v1/report_zh.md)。E191 seal中可变根文档原字节由本轮迁移收据保存，旧seal不回写。

本轮固定范围收口，无待恢复矩阵。共享基线/图/metric/监督不改，公共query历史曝光、一套图/画像，同执行者不同实现核验，非独立人员/新盲确认。新增产物/root/acsg-e192-storage经storage链接；原E191 PDF不改，E192交付文字证明与CSV。下一问题见[s-target](s-target.md)。
'''
 (REPO/'summary.md').write_text(summary)
 p=REPO/'spec.md';s=p.read_text().replace('### 4.7 E192共享必要条件与重配对照（执行中）','### 4.7 E192共享必要条件与重配对照（已完成）');needle='当前实现/配置身份见[冻结]('+REL+'/freeze.json)。';s=s.replace(needle,needle+'全部39点/117轮与36资格点通过；七集448组query/重配组合的全部池覆盖另由stdlib复算。费用排除证书以整数命中数、当前实测完整QPS和同窗口GT10判断，不是未来实现的时间下界。结果见[报告]('+REL+'/report_zh.md)。');p.write_text(s)
 target=f'''# ACSG 后续研究问题

2026-10-29。E192证明与受控实验已完成，默认E99 GT10保持，无未完成矩阵。用户本次授权的固定范围已收口。

{text}

## 后续门（提案，未启动）

1. 任何固定ID源补全先算合法开发query的遗漏源覆盖上界；源支持近零时，不把改善排序当突破来源的办法。按新源/新训练量评估，不把数据集贴成永久无用。
2. 当前池oracle在当前费用下被GT10覆盖的点，后续必须实质降低完整费用或改变候选来源，不能只报告更好的池内分数。若改候选源，先在合法开发query审计廉价块支持，再冻结完整T1实验。
3. E191保留点仍需已有B32的密集费用匹配与合法新查询/图确认；本轮没有自动启动该矩阵。若研究共享的分布因果，应另冻结生成/采样机制，控制规模、metric、维数、图与标签角色，不能把hub表重配改名为零共享数据集。

[E192完整报告]({REL}/report_zh.md) · [理论]({REL}/theory.md) · [全部费用证书]({REL}/analysis/oracle_cost_certificates.csv)。历史科学文件/seal不回改，未测方向不写成已实现。
''';(REPO/'s-target.md').write_text(target)
 p=REPO/'s-experiment.md';s=p.read_text().replace('E192共享必要条件研究执行中；最新完成E191七集两K综合矩阵；','最新完成E192共享必要条件与受控重配；E191保留此前七集两K综合矩阵身份；');old=next(x for x in s.splitlines() if x.startswith('| E192 |'));s=s.replace(old,'| E192 | 共享必要条件、支持上界与重配对照 | 三集39点/117T1＋七集32重配诊断完成；条件定理成立，普遍不共享无用命题不成立，默认不变 | [卡片](experiment_history/192_sharing_necessity_v1.md) |');p.write_text(s)
 card=f'''# E192：邻域共享的必要条件与受控重配

2026-10-29用户要求“想办法证明一下吧”。新版本冻结协议、39点/117T1正式范围和32次重配，主动检查反例，不预设原判断必须成立。

{text}

三集COCO/Deep/SIFT，真实K100/L200正常SQ、打乱SQ、PQ、B32、MAIN与GT10同窗口；GT10八档L固定。资格36点真实K1/K100，各128query。七集两K/L200原E191实际包只用于支持上界与32次表行重配诊断，不包装成新在线性能。模型/图/metric/旧科学文件不改，新的C++分支仅切换同长度分组内重配的hub-block表；全局表内容、每hub行长和访问上限保持，实际去重/扫描量另报。

集合证明只需F⊆R∪C；固定ID表另有C⊆训练遗漏源S。块法可访问S外目标，给出实际ID反例及一维L2可执行反例。当前候选池理想救回上限与当前实测费用对照GT10，不当成免费方法或未来实现速度下界。重配干预表对应关系，不使整个数据几何/监督零共享。

全部实际包SHA、三轮bits、原生全量合并oracle、预算和历史返回一致性通过；stdlib复算新质量/覆盖/预算控制及七集全部query的32次重配计数。同一执行者不同实现，公开test历史曝光，无新盲确认。费用suite/峰RSS/实际T1单列，不清零旧构建债、不从次数归因阶段耗时。新数据在/root/acsg-e192-storage。E191原PDF、科学产物和seal原件不动；其可变根文档旧字节通过本轮source_before与迁移收据关联旧SHA。

[完整报告](../{REL}/report_zh.md) · [严格推导](../{REL}/theory.md) · [协议](../{REL}/protocol.md) · [冻结](../{REL}/freeze.json) · [oracle费用证书](../{REL}/analysis/oracle_cost_certificates.csv) · [实际反例](../{REL}/analysis/actual_counterexamples.json)。
''';(REPO/'experiment_history/192_sharing_necessity_v1.md').write_text(card)
 p=REPO/'experiment_history/README.md';s=p.read_text().replace('最新正式实验是[E191](191_seven_dataset_scoring_v1.md)七集两K来源与评分综合测试','最新正式实验是[E192](192_sharing_necessity_v1.md)共享必要条件与受控重配，E191保留七集两K综合测试身份');needle='| [191_seven_dataset_scoring_v1.md]';idx=s.index(needle);s=s[:idx]+'| [192_sharing_necessity_v1.md](192_sharing_necessity_v1.md) | E192：共享必要条件、候选支持上界与受控重配 |\n'+s[idx:];p.write_text(s)
 (REPO/'LOCAL_CODEX_START.md').write_text(f'''# ACSG 当前接续入口

2026-10-29，/data/netg/ACSG。E192证明与受控实验已完成，默认E99 GT10保持，无待恢复矩阵。分支/HEAD以git实际值为准，近期成果主要未提交。

先读AGENTS、summary、spec、s-target、s-experiment，再读[E192报告]({REL}/report_zh.md)、[推导]({REL}/theory.md)、[费用上界证书]({REL}/analysis/oracle_cost_certificates.csv)、[冻结]({REL}/freeze.json)、[state]({REL}/state.json)。

{text}

三集新39点/117轮为真实K100；36资格点另计。七集两K/L200旧实际包的32次固定重配诊断不是新QPS。不能把固定源必要条件扩大到所有块法/GT10，不能把重配hub表说成零共享数据集。旧E191 PDF/科学产物/seal保留，旧可变根文档原字节在本轮source_before，新增数据/root/acsg-e192-storage。当前授权收口，不自动新测、换默认或生成新PDF。
''')
 dump(R/'reviews/document_sync.json',dict(status='PASS_E192_CURRENT_DOCUMENT_ROLES_SYNCHRONIZED',documents=ROOTS))
 print('PASS E192 current documentation and history synchronized',flush=True)
def ownfiles(root):
 for d,dirs,names in os.walk(root,followlinks=False):
  dirs[:]=[x for x in dirs if x!='__pycache__' and not (Path(d)/x).is_symlink()]
  for name in names:
   p=Path(d)/name
   if not p.is_symlink():yield p
def seal():
 t=time.perf_counter();assert not (R/'delivery_manifest.json').exists();assert read(R/'reviews/report_build.json')['formal_points']==39;assert read(R/'reviews/diagnostic_audit.json')['status'].startswith('PASS');assert read(R/'reviews/qualification_complete.json')['points']==36
 for name in ['freeze.json','postprocessing_binding.json']:
  for x in read(R/name)['files']:assert sha(x['path'])==x['sha256'],(name,x['path'])
 for x in read(R/'freeze.json')['large_assets']:
  st=Path(x['path']).stat();assert (st.st_size,st.st_mtime_ns,st.st_ino)==(x['bytes'],x['mtime_ns'],x['inode'])
 anchors=['coco','deep10m_l2_v1','sift10m_bigann_l2_v1'];threads=[]
 for ds in anchors:
  for mode,folder,repeats in [('formal','results',3),('qualification','qualification',1)]:
   receipt=read(R/f'reviews/{mode}_{ds}.receipt.json');assert receipt['returncode']==0 and receipt['max_observed_threads']==1;threads.append(receipt);assert read(R/f'reviews/audit_{folder}_{ds}.json')['status'].startswith('PASS')
   done=read(R/f'storage/{folder}/{ds}/complete.json');assert done['points']==(13 if mode=='formal' else 12)
   for rr in done['results']:
    h=hashlib.sha256(struct.pack('<QQ',done['n'],rr['K']))
    for name in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update((Path(rr['result_dir'])/'raw'/name).read_bytes())
    h.update(bytes(done['n']*16));assert len(rr['rounds'])==repeats and all(x['packet_sha256']==h.hexdigest() for x in rr['rounds'])
 old=read(OLD/'delivery_manifest.json');before=read(R/'reviews/E191_before.json');assert sha(OLD/'delivery_manifest.json')==before['seal_sha256'];bridges={x['original_path']:x for x in before['mutable_document_bridge']};oldchecked=0
 for x in old['files']:
  p=bridges[x['path']]['snapshot_path'] if x['path'] in bridges else x['path'];assert sha(p)==x['sha256'],x['path'];oldchecked+=1
 assert sha(REPO/'AGENTS.md')==bridges[str(REPO/'AGENTS.md')]['sha256']
 checkedlinks=0
 for p in [R/'report_zh.md',R/'theory.md',R/'protocol.md']+[REPO/x for x in ROOTS]:
  for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if '://' in target or target.startswith('#'):continue
   target=target.split('#')[0].strip('<>');assert (p.parent/target).exists(),(str(p),target);checkedlinks+=1
 check=subprocess.run(['git','diff','--check','--',*ROOTS,'AGENTS.md'],cwd=REPO,text=True,capture_output=True);assert check.returncode==0,check.stdout+check.stderr
 assert shutil.disk_usage('/root').free>.7*2**30 and shutil.disk_usage('/data').free>.65*2**30
 state=dict(status='COMPLETED_CONDITIONAL_PROOF_NO_DEFAULT_CHANGE',formal_points=39,formal_batches=117,qualification_points=36,diagnostic_support_rows=14,diagnostic_permutation_rows=448,all_query_permutation_cases=read(R/'reviews/diagnostic_audit.json')['query_mapping_cases'],default_changed=False,remaining_required_work=False,new_PDF=False,conclusion=read(R/'reviews/interpretation.json')['principal_conclusion'],completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat());dump(R/'state.json',state)
 dump(R/'delivery_validation.json',dict(status='PASS_E192_COMPLETE_PROOF_AND_CONTROL_DELIVERY',old_E191_files_preserved_with_original_document_bridge=oldchecked,old_E191_seal_unchanged=True,current_document_bridge=list(bridges.values()),timing_receipts=threads,local_links_checked=checkedlinks,root_documents=ROOTS,formal_points=39,formal_batches=117,default_changed=False))
 files=list(ownfiles(R))+list(ownfiles((R/'storage').resolve()))+[REPO/x for x in ROOTS]+[REPO/'AGENTS.md'];records=[dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(set(files)) if p!=R/'delivery_manifest.json'];dump(R/'delivery_manifest.json',dict(status='SEALED_E192_COMPLETE_PROOF_AND_CONTROL_DELIVERY',files=records,formal_points=39,formal_batches=117,default_changed=False,seconds=time.perf_counter()-t));print(json.dumps(dict(status='SEALED_E192_COMPLETE_PROOF_AND_CONTROL_DELIVERY',files=len(records),seconds=time.perf_counter()-t)),flush=True)
if __name__=='__main__':docs() if sys.argv[1]=='docs' else seal()

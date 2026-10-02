import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import json,sys,time,shutil,hashlib,subprocess,signal
from pathlib import Path
R=Path(__file__).resolve().parents[1];TB=R.parents[1];ROOT=TB.parents[1];E=R.parent/'e107_initialization_factorial';E110=R.parent/'e110_first_expansion_intervention'
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
assert not (R/'config.locked.json').exists() and read(E110/'complete.json')['status']=='COMPLETE'
started=time.time();lock=dict(version='E111_rank_core_certificate_v1',created_unix=started,m=[64,100],n=4096,threads=1,cpu=15,deadline_unix=1789890600,job_seconds_cap=300,expected_NSG_calls=0,expected_ANN_calls=0,new_training=0,new_GT=0,new_graphs=0,max_new_bytes=100000000,max_rss_gib=40,fit_or_heldout_access=False,query_role='E105 fully exposed development; structural diagnosis only',information_gate='First require zero certificate member violations in all measured outputs. Then sufficient future-supervision signal requires >=1pp certified GT1 rescue lower bound against GT10 exact3 at L128 in BOTH datasets and certificate coverage of >=25% of current successful GT1 queries. No training automatically authorized by this gate; no m/core/entry tuning.',reference_E107=str(E),reference_E110=str(E110))
dump(R/'config.locked.json',lock)
protocol='''# E111：排名核心内的可保留路径证书

2026-09-20，用户16:00理论研究目标内的图派生标签诊断。先完整完成E110，再执行本阶段。依据[保留引理与边界](../../research/retained_target_reachability.md)，固定m=64/100，原E105全4096曝光query/GT100、原NSG与H；无新GT、NSG/ANN搜索、构图或训练。仅从原图计算query特定GT核心闭包，生成新的诊断标签，不称零标签。

对每个原H入口计算：首行邻居（含入口自身）进入核心后能沿核心子图到达哪些目标。另对E107全部8方法及E110PrimaryFirst3，以实际首展开节点和初始种子∩核心构造证书。K1/L64使用m64，其余K1和全部K100使用m100。逐项核验所有证书成员均在相应真实返回中（K1只核验GT1），并全量保留不覆盖query。每256行对全部核心节点用独立BFS复核位集Floyd闭包。

数学保证以GT排名/并列规则匹配为条件；m64有已有第65分数可查，m100没有第101分数，不能声称本轮新证实外部严格间隔或重新验证全部GT。实际零违例是实现与本样本的证据，未提升成任意浮点输入证明。没有证书不等于搜索失败；max certificate不是实际Recall oracle上界。

报告当前首节点证书覆盖、全H可证入口存在率、GT10 exact3现有失败中全H证书可保证恢复的GT1比例，以及max证书相对现有K100命中的正差下界。这些均使用GT特权信息，不是可部署选择器或成本比较。

未来监督信息门：先要求全部真实输出零成员违例；随后两集L128相对GT10 exact3均至少1pp的GT1保证恢复量，且证书覆盖至少25%的当前成功GT1查询。失败停止该证书监督投入，不增加m/路径前缀/新hub或训练模型；通过也需另锁不使用GT的预测与成本协议。

单CPU15、实际线程1、数据串行；每子进程300秒（编译120秒）硬超时/独立PGID，15:50截止，阶段100MB/RSS40GiB/free4GiB、父2GiB约束。预计0真实NSG/ANN；读取旧图和计算邻接/闭包的成本单列。保护E110/E107旧输入/源码/结果，四根文档前后快照、源码冻结、原始位集/全部标签、评分与状态保存。
'''
(R/'protocol.md').write_text(protocol);shutil.copy2(TB/'research/retained_target_reachability.md',R/'theory_snapshot.md')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
 p=R/'source_before'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
configs=[];protected=read(E110/'reviews/protected_before.json');datasets=list(read(E/'config.locked.json')['datasets'])
for ds in datasets:
 c=read(E/'reviews'/('main_'+ds+'.json'));methods=[]
 for m in c['methods']:
  methods.append(dict(name=m['name'],entry_count=m['entry_count'],forced=False,entries=str(E/'results'/('main_'+ds)/m['name']/'entries.i32'),reference_results=str(E/'results'/('main_'+ds)/m['name'])))
 methods.append(dict(name='PrimaryFirst3',entry_count=3,forced=True,entries=str(E110/'results'/('main_'+ds)/'PrimaryFirst3/entries.i32'),primary=str(E110/'results'/('main_'+ds)/'PrimaryFirst3/primary.i32'),reference_results=str(E110/'results'/('main_'+ds)/'PrimaryFirst3')))
 c={k:c[k] for k in ['dataset','dimension','H','n','queries','GT','hub_ids','index','base_n','base','K_L']};c.update(methods=methods,GT_IP=str(Path(c['GT']).with_name('gt_ip.f32')),deadline_unix=lock['deadline_unix'],seconds_cap=300)
 for p in [c['queries'],c['GT'],c['GT_IP'],c['hub_ids']]+[m['entries'] for m in methods]+[methods[-1]['primary']]:protected.append(ident(p))
 cfg=R/'reviews'/(ds+'.json');dump(cfg,c);configs.append(cfg)
dump(R/'reviews/protected_before.json',protected)
argv=read(E/'reviews/jobs.json')[0]['argv'];argv=[str(R/'src/certify.cpp') if x==str(E/'src/evaluate.cpp') else str(R/'bin/certify') if x==str(E/'bin/evaluate') else x for x in argv]
source=[ident(R/'src/run.py'),ident(R/'src/certify.cpp'),ident(R/'config.locked.json'),ident(R/'protocol.md'),ident(R/'theory_snapshot.md')]+[ident(p) for p in configs]+[ident(p) for p in (E/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[ident(x) for x in argv if x.endswith('.a')]
dump(R/'reviews/source_freeze.json',dict(created_unix=time.time(),files=source));jobs=[]
def execute(argv,log,timeout,kind):
 assert time.time()+timeout+5<lock['deadline_unix'] and shutil.disk_usage(R).free>=4*1024**3
 j=dict(argv=argv,kind=kind,started_unix=time.time(),timeout_seconds=timeout,NSG_calls=0);jobs.append(j)
 with (R/'logs'/log).open('x') as f:
  p=subprocess.Popen(argv,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_DYNAMIC='FALSE'),start_new_session=True);j.update(pid=p.pid,pgid=os.getpgid(p.pid));dump(R/'reviews/jobs.json',jobs)
  try:p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:
   assert os.getpgid(p.pid)==p.pid;os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   j['timeout']=True
 j.update(exit_code=p.returncode,finished_unix=time.time(),seconds=time.time()-j['started_unix']);dump(R/'reviews/jobs.json',jobs);assert p.returncode==0,j
 return j
try:
 for r in protected:assert sha(r['path'])==r['sha256']
 execute(argv,'build.log',120,'compile');dump(R/'reviews/binary_freeze.json',ident(R/'bin/certify'))
 for cfg in configs:
  ds=read(cfg)['dataset'];dump(R/'state.json',dict(status='RUNNING_TOPOLOGY_DIAGNOSIS',dataset=ds));j=execute(['taskset','-c','15',str(R/'bin/certify'),str(cfg),str(R/'results'/ds)],ds+'.log',300,'topology');j['complete']=read(R/'results'/ds/'complete.json');assert j['complete']['NSG_calls']==j['complete']['ANN_calls']==0;dump(R/'reviews/jobs.json',jobs)
  assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<lock['max_new_bytes'];assert sum(p.stat().st_size for p in TB.rglob('*') if p.is_file())<read(TB/'config.locked.json')['resources']['max_new_bytes'];print(ds,'topology complete',round(j['seconds'],2),flush=True)
 for r in protected+source:assert sha(r['path'])==r['sha256']
 dump(R/'reviews/topology_complete.json',dict(status='PASS',seconds=time.time()-started,NSG_calls=0,ANN_calls=0,new_training=0,new_GT=0,new_graphs=0,new_graph_derived_labels=True));dump(R/'state.json',dict(status='TOPOLOGY_COMPLETE',pending=['certificate inclusion checks','information gate','report']))
except Exception as e:dump(R/'state.json',dict(status='STOP_TOPOLOGY_ERROR',error=repr(e)));raise

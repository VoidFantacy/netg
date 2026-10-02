"""Read only configuration/model metadata; never open final query/GT/row payloads."""
from pathlib import Path
import json,hashlib,time
R=Path('/data/netg/ACSG');C=R/'entry_method_exploration/20260913_until2100_v1';O=C/'session9_final_preparation';E34=R/'entry_method_exploration/20260911_hnsw_rl_benchmark_v1';E74=C/'stage15_compact_wall_v1';E73=C/'stage14_compact_modes_v1'
def read(p):return json.loads(Path(p).read_text())
def identity(p):
 p=Path(p);s=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=h.hexdigest())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not O.exists();O.mkdir();draft={};sources=[]
for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
 old=read(E34/'inputs'/ds/'config.json');dev=read(E74/'inputs'/ds/'config.json');assert old['num_queries']==2000 and old['dim']==dev['dim'] and old['index_path']==dev['index_path'];inputs={}
 for k,w in [('queries_file',old['dim']*4),('gt_file',100*8),('row_ids',8)]:
  p=Path(old[k]);st=p.stat();assert st.st_size==2000*w;inputs[k]=dict(path=str(p),bytes=st.st_size,mtime_ns=st.st_mtime_ns,access='stat only; payload not opened or hashed')
 bases=[dict(m) for m in dev['methods'] if m['L']==64 and m['model_name'] not in ['mode10','best_new']];assert len(bases)==(4 if old['dim']==512 else 3)
 for m in bases:
  if m['family']=='nsg':continue
  m['reference_graph']=True
  for key in ['W','mapping','tie_ids','graph_file']:sources.append(identity(m[key]))
  # Exact identity against one original E34 baseline configuration, independent of display alias.
  assert any(all(Path(x[k]).read_bytes()==Path(m[k]).read_bytes() for k in ['W','mapping','tie_ids','graph_file']) for x in old['methods'] if x['family']!='nsg' and x['L']==64)
 draft[ds]=dict(num_queries=2000,dim=old['dim'],gt_k=100,index_path=old['index_path'],base_count=dev['base_count'],query_cpu=15,threads=1,timing_repeats=5,Ls=[64,128,256,400,800],inputs=inputs,required_baselines=bases,unfilled_roles=['best_all','best_new'],final_selection_frozen=False,execution_ready=False)
 sources += [identity(E34/'inputs'/ds/'config.json'),identity(E74/'inputs'/ds/'config.json')]
est=[]
for distinct_new in [1,2]:
 points=(7+2*distinct_new)*5;n=2000;nsg=points*(7*n+16);hnsw=(points-10)*7*n;raw=points*n*115+(2*distinct_new*5)*n*56
 est.append(dict(distinct_added_configurations_per_dataset=distinct_new,points=points,NSG=nsg,HNSW=hnsw,whole_wall_batches=points*5,raw_array_bytes_if_all_added_models_multi_profile=raw,output_reserve_MiB=64,scope='Examples, not frozen final matrix; aliases and actual supported configurations determine exact totals.'))
assert [(x['points'],x['NSG'],x['HNSW'],x['raw_array_bytes_if_all_added_models_multi_profile']) for x in est]==[(45,630720,490000,11470000),(55,770880,630000,14890000)]
dump(O/'matrix_metadata_draft.json',dict(status='PREPARATION_ONLY_NO_SELECTION_NO_FINAL_PAYLOAD',created_at=time.time(),datasets=draft,estimates=est,NSG_calls=0,HNSW_calls=0,final_payload_opened=False))
sources += [identity(E73/'bin/evaluate'),identity(E73/'src/evaluate.cpp'),identity(E73/'src/benchmark_with_nsg.cpp'),identity(Path(__file__))];dump(O/'source_identity.json',dict(files=sources))
(O/'readme.md').write_text('''# 晚间最终矩阵：第9会话准备件

这里只完成配置/模型身份与预算核对，没有最终模型选择、ANN或最终query/GT/row载荷读取。matrix_metadata_draft.json不是可直接执行配置，不能把草稿的未填角色当已冻结best。

七条规定基线（Web4、Y3）的W/mapping/tie/graph与E34原配置逐字对应。source_identity.json仅hash配置、模型和源码/binary；最终输入只stat形状2000×d/2000×100/2000，不读/hash载荷。查历史23卡片仅了解旧计时合同及历史汇总，没有回流本会话训练或选择。

最终唯一写入者先用已暴露开发反馈选实际best_all/best_new，保存候选池资格、规则、得分、ties、W/graph/mapping/ef/variable及完整源码身份；同配置角色可显式alias，不能把Y零更新当新方法。全部身份/规则冻结后，才准备和读取E34历史validation2000。不得从最终结果换模型、L、图或阈值。

使用E73的bin/evaluate与src/evaluate.cpp真实入口：一次warmup+5轮轮换整批plain wall+一次count+16原kernel/点，因此每2000query点14016 NSG；路由每非NSG点14000 HNSW。component_wall=false。一个实际新增配置/集为45点630720 NSG/490000 HNSW/225 wall；两个实际新增配置/集为55点770880 NSG/630000 HNSW/275 wall。按实际aliases重新算cap，禁止沿旧2048配置收费。

E73支持原NSG/单画像/variable1–3画像、ef10/30；不支持E72 distinct_hub_width回调。若最终选择这种候选，必须先建立兼容同批评测器并验收，不能用E73静默忽略字段，也不能为赶时间将它当同一方法执行。新增方式另立final protocol，不绕过原E86/E87停止门。

控制器逐dataset串行、preexec CPU15后exec、实际/proc与各库threads=1；每job全额预留，失败原件保留。提前检查全matrix时间/磁盘预算，20:40为所有新增query硬止，21:00交图和报告。E74的1101.761s只是同规模旧native操作的规划参考，不是新测量承诺。

分析必须把n=2000及方法数/L数参数化：独立GT集合/mask/合法ID评分；qps=2000/wall；五轮顺序逐event核验；同模型跨五L完整route/7slot/图身份；同三入口graph返回一致；原kernel/plain/count/repeat证据和原E34兼容控制回归。旧开发2048前缀回归不适用于最终不同query，不能套8192/112640等旧硬编码。GT/count/hash/JSON/load/build在wall之外。

输出完整原点/各轮、QPS–Recall、QPS–失败率、按L Recall/QPS/失败三图及所有零命中query全GT/入口/返回、救回/新增失败和旧收益丢失。插值限共同实测前沿区间并标描述性；不跨批拼曲线、不将五轮当五份Recall样本。64MiB晚间空间已在session9资源中单列预留。

下一步是冻结实际候选和独立final协议后实现最终控制器/分析器；本准备件没有执行器，不应运行旧E74 prepare/run/analyze。
''')
print(json.dumps(dict(status='FINAL_METADATA_PREPARATION_COMPLETE',model_identities=len(sources),examples=est,final_payload_access=False),ensure_ascii=False))

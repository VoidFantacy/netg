from pathlib import Path
import json,time,shutil,hashlib
TB=Path(__file__).resolve().parents[1];ROOT=TB.parents[1];OLD=TB/'stages/e107_initialization_factorial';R=TB/'stages/e110_first_expansion_intervention';assert not R.exists()
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
for n in ['src','bin','reviews','results','logs','figures','postprocess','source_before']: (R/n).mkdir(parents=True,exist_ok=True)
for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
 p=R/'source_before'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p)
shutil.copytree(OLD/'src/common',R/'src/common')
for n in ['common.py','search_core.hpp','kernels.hpp','evaluate.cpp']:shutil.copy2(OLD/'src'/n,R/'src'/n)
oldcfg=read(OLD/'config.locked.json');cfg=dict(version='E110_primary_first_intervention_v1',created_unix=time.time(),reference_E107=str(OLD),reference_initial_order=str(TB/'research/initial_seed_order_v1'),datasets=oldcfg['datasets'],K_L={'1':[64,128,256,400,800],'100':[128,256,400,800]},methods=['GT101','GT103','PrimaryFirst3'],n=4096,threads=1,cpu=15,expected_NSG_calls=442880,max_NSG_calls=450000,max_new_bytes=180000000,min_free_gib=4,max_rss_gib=40,job_seconds_cap=600,deadline_unix=1789890600,bootstrap_seed=20260920,bootstrap_replicates=10000,primary_CI_level=.9875,primary_summary='Equal mean over the two K means; each K averages its frozen L values',promotion_gate='Both datasets: mean over L of each K nonnegative versus both exact controls; equal-K aggregate >=0.10pp and 98.75% paired interval lower>0 versus both controls; average graph NDC<=1.01 of GT103. Otherwise stop intervention candidate, no online/QPS or anchor/step tuning.',new_GT=0,new_training=0,new_graphs=0,new_formal_QPS=False)
dump(R/'config.locked.json',cfg)
protected=read(OLD/'reviews/protected_before.json')
for ds in cfg['datasets']:
 for name in ['GT101','GT103']:
  for p in (OLD/'results'/('main_'+ds)/name).rglob('*'):
   if p.is_file():protected.append(ident(p))
dump(R/'reviews/protected_before.json',protected)
protocol='''# E110：固定三入口，只干预首个展开节点

2026-09-20，在用户16:00目标内由E107及独立首节点诊断推导。GT10从1入口到3入口时，Web47.85%、Y42.41%查询首节点改变；这一关联不能证明改变首节点导致损失。全4096既有曝光开发query、原H/GT10/NSG/raw-IP保持，预锁K1五L与K100四L。

三方法为GT10Exact1、GT10Exact3、PrimaryFirst3。第三个方法与Exact3使用同一组三个节点、同一初始visited和候选池，只先展开GT10分数最高的那个真实入口一次，然后游标回0，执行原有限beam循环。不是让三个入口各自独立搜，不增加入口/扩大L，不在失败子集启用。首个节点是原画像精确top1，不是真实GT。选择入口和终止规则的其他部分不变；新增干预能改变后续轨迹和实际NDC，不声称同L等成本。

kernel在新版本新增编译期ForcePrimary参数（默认false）与实际首展开记录；原控制路径逐位恢复E107，两个控制smoke对链接E99。每个方法全量count/plain一致；干预的实际首展开逐query等于画像top1；原首节点已是画像top1的全部query应与原3入口输出/距离bits/NDC相同。复制原kernel前件及新源码diff保留。

正常真实NSG442880次：两集主批4096×3方法×9点×2次=442368，smoke各16×2点×(3×2+2原库控制)=256。单CPU15/实际1线程/方法数据串行；无新GT/图/训练/K10/正式QPS。600秒每搜索进程硬超时，独立PGID；阶段450000调用/180MB、全时段4M/2GiB与15:50硬截止同时满足。

分析先报告完整54点及对两控制的36配对，固定首节点改变/保留两组全部保留，不筛选query。主要机制效应是同三入口干预的真实命中变化；即使有影响也只识别这个干预，不能声称解释所有入口交互。

进一步方法投入门预锁为：每个数据集、每K跨全部L平均对两控制均非负；每数据集等权平均两个K的改善对两控制均>=0.10pp且98.75%配对bootstrap下端>0；平均graph NDC不超过原3入口1.01倍。四主汇总用固定10000次bootstrap/seed20260920；单点95%区间仅描述性。若失败则停止此干预候选，不训练anchor选择器、不追加强制步数/L/seed。不自动测ANN或QPS；通过时另锁实际普通ANN及完整wall协议。当前已有曝光数据不称盲验证。

来源：[E107](../e107_initialization_factorial/report.md) · [首节点诊断](../../research/initial_seed_order_v1/initial_order.csv) · [配置](config.locked.json)。
'''
(R/'protocol.md').write_text(protocol)
(R/'research.md').write_text('# 首节点假设的边界\n\n单位hub按cosine排序，原NSG按raw-IP排序。全部hub等范数时，单位hub top1一定是其top3中原NSG首展开；Web原hub范数约1，现场全部4096行确实保持。GT画像排名没有这个恒等关系，三个入口的原始距离重新排序常改变第一条路径。Yandex单位hub原范数不完全相同，因此也有7.37%改变。\n\n保留首节点不是单调性的充分条件：Web单位hub虽全部保持首节点，L128仍有54个K1由命中变漏失，说明后续竞争仍会损伤。E110不把首节点假设当完整解释，而是全量同集合直接干预。若不转化为跨数据净收益，不能因此训练更复杂网络。\n')
p=R/'src/kernels.hpp';s=p.read_text();s=s.replace('std::vector<acsg::Neighbor> pool;','std::vector<acsg::Neighbor> pool;\n    int first_expanded=-1;')
s=s.replace('bool Compact=true>','bool Compact=true,bool ForcePrimary=false>');s=s.replace('faiss::idx_t* ids,float* distances) {','faiss::idx_t* ids,float* distances,int primary=-1) {');s=s.replace('int k=0;','int k=0; first_expanded=-1; bool first_iteration=true;\n        if constexpr(ForcePrimary){while(k<live&&pool[k].id!=primary)++k;if(k==live)throw std::runtime_error("primary absent");}')
s=s.replace('const int node=pool[k].id;','const int node=pool[k].id;\n                if(first_expanded<0)first_expanded=node;');s=s.replace('k=updated<=k?updated:k+1;','if constexpr(ForcePrimary){if(first_iteration){k=0;first_iteration=false;}else k=updated<=k?updated:k+1;}\n            else k=updated<=k?updated:k+1;');p.write_text(s)
p=R/'src/evaluate.cpp';s=p.read_text();a=s.index('void counterexample(');b=s.index('int main(',a);s=s[:a]+s[b:];s=s.replace('threads();if(argc==3&&std::string(argv[1])=="counterexample"){require(!fs::exists(argv[2]),"preserve fixture");counterexample(argv[2]);return 0;}','threads();')
s=s.replace('int count=m["entry_count"];','int count=m["entry_count"];bool force=name=="PrimaryFirst3";')
s=s.replace('std::vector<int32_t> entries(n*3,-1);','std::vector<int32_t> entries(n*3,-1),primary(n),actual_first(n);')
s=s.replace('std::partial_sort(scores.begin(),scores.begin()+4,scores.end());','std::partial_sort(scores.begin(),scores.begin()+4,scores.end());primary[i]=scores[0].second;')
s=s.replace('write_raw(sub/"entries.i32",entries);','write_raw(sub/"entries.i32",entries);write_raw(sub/"primary.i32",primary);')
s=s.replace('kernel.search<true,false,true>(dc,vt,ep,L,K,answer.data(),ad.data());','if(force)kernel.search<true,false,true,true,true,true>(dc,vt,ep,L,K,answer.data(),ad.data(),primary[i]);else kernel.search<true,false,true>(dc,vt,ep,L,K,answer.data(),ad.data());actual_first[i]=kernel.first_expanded;require(!force||actual_first[i]==primary[i],"forced first expansion");')
s=s.replace('kernel.search<true,false,true>(*plain,pvt,ep,L,K,other.data(),od.data());','if(force)kernel.search<true,false,true,true,true,true>(*plain,pvt,ep,L,K,other.data(),od.data(),primary[i]);else kernel.search<true,false,true>(*plain,pvt,ep,L,K,other.data(),od.data());require(kernel.first_expanded==actual_first[i],"first expansion count/plain");')
s=s.replace('if(smoke){lvt.advance();','if(smoke&&!force){lvt.advance();')
s=s.replace('write_raw(point/"ids.i32",ids);','write_raw(point/"first_expanded.i32",actual_first);write_raw(point/"ids.i32",ids);')
insert='''    {
     auto ref=fs::path(c["reference_E107"].get<std::string>())/"results"/("main_"+c["dataset"].get<std::string>())/(force?"GT103":name)/("k"+std::to_string(K)+"_L"+std::to_string(L));
     auto ri=read_raw<int32_t>(ref/"ids.i32");auto rd=read_raw<float>(ref/"distances.f32");auto rn=read_raw<uint64_t>(ref/"ndc.u64");
     auto first=read_raw<int32_t>(fs::path(c["reference_initial_order"].get<std::string>())/c["dataset"].get<std::string>()/"GT103"/"first.i32");
     for(size_t i=0;i<n;++i)if(!force||first[i]==primary[i])require(!memcmp(ids.data()+i*K,ri.data()+i*K,K*4)&&!memcmp(dist.data()+i*K,rd.data()+i*K,K*4)&&ndc[i]==rn[i],"original output or same-first no-op parity");
    }
'''
s=s.replace('    if(route=="ann"){',insert+'    if(route=="ann"){');s=s.replace('{"legacy_checked",smoke}','{"legacy_checked",smoke&&!force},{"forced_primary",force}')
p.write_text(s)
dump(R/'reviews/setup_freeze.json',dict(created_unix=time.time(),files=[ident(p) for p in (R/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[ident(R/n) for n in ['config.locked.json','protocol.md','research.md']]))
parent=read(TB/'state.json');assert parent['completed_NSG_calls']==2354176;parent.update(stage='E110 fixed-entry first-expansion intervention locked',active_stage_reserved_NSG_calls=442880);dump(TB/'state.json',parent)
print(R)

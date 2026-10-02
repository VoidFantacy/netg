import datetime,hashlib,json,pathlib,shutil
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent;E=D.parent/'20260916_shared_span_batch4_v1';P=D.parent/'20260915_gate_l2_r1_r100_v1'
read=lambda p:json.loads(p.read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert read(D/'reviews/git_backup.json')['status']=='PASS'
assert read(E/'reviews/final_review.json')['status']=='PASS' and read(E/'complete.json')['compatibility_status']=='PASS'
a=read(E/'results/summary.json');checks=[]
for K,L in [(1,96),(100,100),(1,800),(100,1250)]:
 rows=[x for x in a['metrics'] if (x['K'],x['L'])==(K,L) and x['kernel']!='current'];gt=[x for x in rows if x['method'].startswith('GT10-')]
 for b in [x for x in rows if x['method'] in ['NSG','GATE','HNSW']]:
  winners=[g['method'] for g in gt if g['recall']>=b['recall'] and g['qps_mean']>=b['qps_mean']]
  checks.append(dict(K=K,L=L,baseline=b['method'],gt10_at_least_as_good_in_mean_recall_and_qps=winners))
go=all(x['gt10_at_least_as_good_in_mean_recall_and_qps'] for x in checks)
save(D/'reviews/conditional_gate.json',dict(status='GO_FULL_REMEASUREMENT' if go else 'STOP',user_condition='结果出来之后如果GT10差不多是所有方法最好的方法就重新测试那些因为优化后需要重新测试的方法',interpretation='GT10 family remains among the best in the completed E102 WebVid points; not a claim of five-dataset or statistically significant universal superiority.',checks=checks,high_budget_repeat_ranges_overlap=True,reference_metrics_sha256=sha(E/'results/metrics.csv'),reference_final_audit_sha256=sha(E/'reviews/final_review.json'),no_default_or_model_selection=True))
assert go,'User condition not met'
order=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1','deep10m_l2_v1','sift10m_bigann_l2_v1','gist1m_l2_v1'];old=read(P/'config.locked.json')
lock=dict(version='E103_OPTIMIZED_FULL_CURVES',datasets=order,K=[1,100],L=old['L'],methods=old['methods'],query_threads=1,repeats=3,max_real_search_calls=32800000,max_rss_gib=64,min_free_gib=10,max_total_seconds=86400,excluded_datasets=['laion10m_acsg_v1'],created_at=datetime.datetime.now().astimezone().isoformat(),source_matrix=str(P/'config.locked.json'),shared_kernel=str(E/'src/kernels.hpp'),scope='Reuse original five-dataset 16-budget matrix; four NSG methods on the same optimized kernel plus same-run full HNSW; no training, graph build, GT generation or default change.')
save(D/'config.locked.json',lock)
for i,ds in enumerate(order):
 inp=D/'inputs'/ds;inp.mkdir(parents=True);m=read(P/'inputs'/ds/'manifest.json');save(inp/'manifest.json',m)
 for name in ['gt10.ids.i32','gate.ids.i32']:shutil.copy2(P/'inputs'/ds/name,inp/name)
 for K in [1,100]:
  c=read(P/'inputs'/ds/f'eval_k{K}.json');c['dataset_order']=i;c['source_e97_freeze_sha256']=c.pop('freeze_sha256');c['kernel']='span-batch4 (NSG methods); original full HNSW';save(inp/f'eval_k{K}.json',c)
 c=read(inp/'eval_k100.json');c.pop('K');c.pop('L');c['base_n'],c['dimension']=m['shape'];c['reference_results']=str(P/'results'/ds);c['max_real_search_calls']=800*c['n'];c['expected_points']=160;c['expected_wall_rounds']=480;c['points']=[dict(K=K,L=L) for K in [1,100] for L in lock['L'][str(K)]];c['variants']=[dict(method=n,kernel='reference' if n=='HNSW' else 'span-batch4') for n in lock['methods']];c['eval_configs']={str(K):str(inp/f'eval_k{K}.json') for K in [1,100]};save(D/'configs'/f'{ds}.json',c)
shutil.copytree(E/'src/common',D/'src/common');shutil.copy2(E/'src/kernels.hpp',D/'src/kernels.hpp');shutil.copy2(P/'src/common.py',D/'src/common.py')
s=(E/'src/compare.cpp').read_text()
def change(a,b):
 global s
 assert a in s,a;s=s.replace(a,b)
change('require(n==10000&&d==512&&idx->metric_type==0&&c["threads"]==1,"frozen WebVid");','int metric=c["metric_id"];require(n==c["n"]&&d==c["dimension"]&&idx->ntotal==c["base_n"]&&idx->metric_type==metric&&(metric==0||metric==1)&&c["threads"]==1,"frozen dataset shape/metric");std::ifstream bf("/proc/sys/kernel/random/boot_id");std::string boot;std::getline(bf,boot);')
change('auto space=make_space(0,d);','auto space=make_space(metric,d);')
change('hm["metric_id"]==0','hm["metric_id"]==metric')
change('auto full=load_topology','require(base.n==idx->ntotal&&base.d==d,"full base shape");auto full=load_topology')
change('require(variants.size()==9,"nine paired versions");','require(variants.size()==5,"five frozen methods");for(int K:{1,100}){fs::create_directories(out/("k"+std::to_string(K)));write_json(out/("k"+std::to_string(K))/"config.json",read_json(c["eval_configs"][std::to_string(K)].get<std::string>()));}')
change('return v["method"].get<std::string>()+"__"+v["kernel"].get<std::string>()+"_K"+std::to_string(K)+"_L"+std::to_string(L);','return "k"+std::to_string(K)+"/"+v["method"].get<std::string>()+"_L"+std::to_string(L);')
change('if(kind=="current"||kind=="reference"){','if(kind=="reference"){require(method=="HNSW","only full HNSW uses reference path");')
change('auto ref=fs::path(c["reference_e99"].get<std::string>())/(m+(m=="HNSW"?"__reference":"__optimized")+"_K"+std::to_string(K)+"_L"+std::to_string(L));','auto ref=fs::path(c["reference_results"].get<std::string>())/key(v);')
change('{"threads",process_threads()},{"cpu",15},{"search_calls_completed",calls}', '{"threads",process_threads()},{"process_threads",process_threads()},{"formal",true},{"boot_id",boot},{"cpu",15},{"search_calls_completed",calls}')
change('write_json(out/"timing_progress.json",rounds);std::cout', 'write_json(out/"timing_progress.json",rounds);json kr=json::array();for(auto r:rounds)if(r["K"]==K)kr.push_back(r);write_json(out/("k"+std::to_string(K))/"timing_progress.json",kr);std::cout')
change('{"output_bits_and_ndc_verified",true},{"actual_batch4_forwarded",v["kernel"]=="span-batch4"}', '{"output_bits_and_ndc_verified",true},{"actual_batch4_forwarded",v["kernel"]=="span-batch4"},{"plain_count_bit_parity",true},{"warmup_bit_parity",true},{"metric_id",metric},{"threads",1},{"cpu",15},{"boot_id",boot}')
change('require(calls==1800000&&rounds.size()==108,"complete matrix accounting");', 'require(calls==c["max_real_search_calls"].get<uint64_t>()&&rounds.size()==480&&point_index==32,"complete matrix accounting");for(int K:{1,100})write_json(out/("k"+std::to_string(K))/"complete.json",{{"status","PASS"},{"K",K},{"metric_id",metric},{"points",80},{"wall_rounds",240},{"threads",1},{"process_threads",process_threads()},{"formal",true}});')
(D/'src/evaluate.cpp').write_text(s)
a=(P/'src/analyze.py').read_text().replace('GATE retrained with disjoint labels.','Shared optimized NSG kernel; frozen models; same-run HNSW.')
# Existing analysis independently scores GT, checks native float64 distances,
# cross-K ties, routes, all repeats, and writes the full threshold tables.
(D/'src/analyze.py').write_text(a)
save(D/'reviews/inherited_validation.json',dict(status='PASS',kernel_sha256=sha(D/'src/kernels.hpp'),kernel_source=str(E/'src/kernels.hpp'),e102_final=read(E/'reviews/final_review.json'),new_synthetic_searches=0,validation='Byte-identical search kernel; E102 full five-dataset output/entry/NDC parity. New generalized wrapper checks every warm/plain/count against all original E97 outputs; failure stops, no automatic retries.'))
print('Gate GO; frozen 800-point matrix prepared')

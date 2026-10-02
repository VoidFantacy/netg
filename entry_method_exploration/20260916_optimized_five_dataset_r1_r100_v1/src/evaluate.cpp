#define main unused_common_main
#include "common/evaluate.cpp"
#undef main
#include "kernels.hpp"

struct ActualBatchCount:CountDC{
 explicit ActualBatchCount(faiss::DistanceComputer* p):CountDC(p){}
 void distances_batch_4(faiss::idx_t a,faiss::idx_t b,faiss::idx_t c,faiss::idx_t d,float& x,float& y,float& z,float& w)override{
  for(auto id:{a,b,c,d}){if(count<3)first[count]=id;++count;}
  dc->distances_batch_4(a,b,c,d,x,y,z,w);
 }
};
static void reference(const Batch& b,const fs::path& root,bool counts){
 require(b.ids==read_raw<int32_t>(root/"ids.i32"),"reference IDs "+root.string());
 auto d=read_raw<float>(root/"distances.f32");require(d.size()==b.dist.size()&&!memcmp(d.data(),b.dist.data(),d.size()*4),"reference distance bits "+root.string());
 require(b.entries==read_raw<int32_t>(root/"entry_ids.i32"),"reference entries "+root.string());
 if(counts){require(b.route_ndc==read_raw<uint64_t>(root/"route_ndc.u64"),"route NDC");require(b.graph_ndc==read_raw<uint64_t>(root/"graph_ndc.u64"),"graph NDC");}
}
int main(int argc,char** argv){try{
 require(argc==3,"compare config new-output");threads();auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"new output required");fs::create_directories(out);write_json(out/"config.json",c);auto load_start=Clock::now();
 auto idx=load_nsg(c["index"]);size_t n=c["n"],d=idx->d;int metric=c["metric_id"];require(n==c["n"]&&d==c["dimension"]&&idx->ntotal==c["base_n"]&&idx->metric_type==metric&&(metric==0||metric==1)&&c["threads"]==1,"frozen dataset shape/metric");std::ifstream bf("/proc/sys/kernel/random/boot_id");std::string boot;std::getline(bf,boot);Fvecs fq(c["queries"]);require(fq.n==n&&fq.d==d,"query shape");std::vector<float> q(n*d);for(size_t i=0;i<n;++i)std::copy(fq.row(i),fq.row(i)+d,q.data()+i*d);for(float v:q)require(std::isfinite(v),"finite query");
 std::map<std::string,std::unique_ptr<Router>> routers;
 for(auto m:c["methods"]){std::string name=m["name"];if(name!="NSG"&&name!="HNSW")routers[name]=std::make_unique<Router>(m,d,fs::path(c["reference_results"].get<std::string>())/"k100"/(name+".hnsw"));}
 auto space=make_space(metric,d);CountParam hc{space->get_dist_func(),space->get_dist_func_param(),0};Fvecs base(c["base"]);auto hm=read_json(c["hnsw_complete"].get<std::string>());require(hm["status"]=="PASS"&&hm["metric_id"]==metric,"verified HNSW");require(base.n==idx->ntotal&&base.d==d,"full base shape");auto full=load_topology(c["hnsw_topology"].get<std::string>(),base,space.get());Worker current(*idx);
 auto ts=Clock::now();auto spans=make_spans(*idx->acsg.final_graph,idx->ntotal);double span_seconds=seconds(ts);ResearchKernel kernel(*idx->acsg.final_graph,spans,idx->ntotal);
 auto plain=std::unique_ptr<faiss::DistanceComputer>(acsg::storage_distance_computer(idx->storage));ActualBatchCount counter(acsg::storage_distance_computer(idx->storage));faiss::VisitedTable vt(idx->ntotal);std::vector<acsg::EnterPoint> ep;ep.reserve(3);std::array<faiss::idx_t,100> ids;
 write_json(out/"layout.json",{{"same_graph_storage_memory",true},{"graph_n",idx->ntotal},{"graph_R",idx->acsg.final_graph->K},{"span_bytes",spans.size()},{"span_build_seconds",span_seconds},{"load_seconds",seconds(load_start)},{"new_kernel","E101 identical span-batch4"}});
 std::vector<json> variants=c["variants"];require(variants.size()==5,"five frozen methods");for(int K:{1,100}){fs::create_directories(out/("k"+std::to_string(K)));write_json(out/("k"+std::to_string(K))/"config.json",read_json(c["eval_configs"][std::to_string(K)].get<std::string>()));}json rounds=json::array();uint64_t calls=0;auto started=Clock::now();int point_index=0;
 for(auto point:c["points"]){int K=point["K"],L=point["L"];require((K==1||K==100)&&L>=K&&L<=1500,"K/L");idx->acsg.search_L=L;full->setEf(L);
  auto key=[&](const json& v){return "k"+std::to_string(K)+"/"+v["method"].get<std::string>()+"_L"+std::to_string(L);};
  auto run=[&](const json& v,Batch& b,bool count){
   std::string method=v["method"],kind=v["kernel"];Router* router=routers.count(method)?routers.at(method).get():nullptr;if(router)router->counting(count);
   if(kind=="reference"){require(method=="HNSW","only full HNSW uses reference path");
    full->fstdistfunc_=count?counted:space->get_dist_func();full->dist_func_param_=count?(void*)&hc:space->get_dist_func_param();current.run(method,router,full.get(),hc,q,d,b,count);
   }else{
    require(kind=="span-batch4"&&method!="HNSW","shared optimized kernel");auto& dc=count?static_cast<faiss::DistanceComputer&>(counter):*plain;
    for(size_t i=0;i<n;++i){auto query=q.data()+i*d;std::array<int32_t,3> entries{-1,-1,-1};size_t ne=1;if(router){entries=router->route(query);ne=3;}else entries[0]=idx->acsg.enterpoint;
     std::copy(entries.begin(),entries.end(),b.entries.begin()+i*3);ep.clear();for(size_t j=0;j<ne;++j)ep.emplace_back(entries[j],1);vt.advance();dc.set_query(query);kernel.search<true,false,true>(dc,vt,ep,L,K,ids.data(),b.dist.data()+i*K);for(int j=0;j<K;++j)b.ids[i*K+j]=ids[j];
     if(count){b.graph_ndc[i]=counter.count;b.route_ndc[i]=router?router->counter.n:0;for(size_t j=0;j<ne;++j)require(counter.first[j]==entries[j],"entry injection order");}
    }
   }
   calls+=n;require(calls<=c["max_real_search_calls"].get<uint64_t>(),"query cap");
  };
  auto verify=[&](const json& v,const Batch& b,bool count){std::string m=v["method"];auto ref=fs::path(c["reference_results"].get<std::string>())/key(v);try{reference(b,ref,count);}catch(...){save_batch(out/"failures"/key(v),b,false);save_batch(out/"failures"/key(v),b,true);throw;}};
  std::map<std::string,std::vector<double>> times;auto ordered=variants;std::rotate(ordered.begin(),ordered.begin()+point_index%ordered.size(),ordered.end());
  for(int rep=0;rep<3;++rep){auto order=ordered;if(rep%2)std::reverse(order.begin(),order.end());for(const auto& v:order){Batch b(n,K);if(rep==0){Batch warm(n,K);run(v,warm,false);verify(v,warm,false);}threads();auto t=Clock::now();run(v,b,false);double sec=seconds(t);verify(v,b,false);if(rep==0)save_batch(out/key(v),b,false);times[key(v)].push_back(sec);
   json row={{"method",v["method"]},{"kernel",v["kernel"]},{"K",K},{"L",L},{"repeat",rep},{"seconds",sec},{"qps",n/sec},{"n",n},{"threads",process_threads()},{"process_threads",process_threads()},{"formal",true},{"boot_id",boot},{"cpu",15},{"search_calls_completed",calls}};rounds.push_back(row);write_json(out/"timing_progress.json",rounds);json kr=json::array();for(auto r:rounds)if(r["K"]==K)kr.push_back(r);write_json(out/("k"+std::to_string(K))/"timing_progress.json",kr);std::cout<<row.dump()<<std::endl;
  }}
  for(const auto& v:ordered){Batch b(n,K);run(v,b,true);verify(v,b,true);save_batch(out/key(v),b,true);write_json(out/key(v)/"complete.json",{{"status","PASS"},{"method",v["method"]},{"kernel",v["kernel"]},{"K",K},{"L",L},{"n",n},{"seconds",times[key(v)]},{"output_bits_and_ndc_verified",true},{"actual_batch4_forwarded",v["kernel"]=="span-batch4"},{"plain_count_bit_parity",true},{"warmup_bit_parity",true},{"metric_id",metric},{"threads",1},{"cpu",15},{"boot_id",boot}});std::cout<<"COUNT_PASS "<<key(v)<<std::endl;}
  ++point_index;struct rusage r;getrusage(RUSAGE_SELF,&r);require(r.ru_maxrss<64LL*1024*1024,"RSS cap");write_json(out/"progress.json",{{"completed_points",point_index},{"search_calls",calls},{"seconds",seconds(started)}});
 }
 require(calls==c["max_real_search_calls"].get<uint64_t>()&&rounds.size()==480&&point_index==32,"complete matrix accounting");for(int K:{1,100})write_json(out/("k"+std::to_string(K))/"complete.json",{{"status","PASS"},{"K",K},{"metric_id",metric},{"points",80},{"wall_rounds",240},{"threads",1},{"process_threads",process_threads()},{"formal",true}});struct rusage r;getrusage(RUSAGE_SELF,&r);write_json(out/"complete.json",{{"status","PASS"},{"search_calls",calls},{"wall_rounds",rounds.size()},{"seconds_excluding_load",seconds(started)},{"seconds_including_load",seconds(load_start)},{"maxrss_kib",r.ru_maxrss},{"threads",process_threads()},{"cpu",15},{"same_graph_and_storage",true},{"actual_batch4_count",true}});return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

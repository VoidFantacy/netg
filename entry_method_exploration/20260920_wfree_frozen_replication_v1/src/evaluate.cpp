#define main unused_common_main
#include "common/evaluate.cpp"
#undef main
#include "kernels.hpp"
struct ActualCount:CountDC{
 explicit ActualCount(faiss::DistanceComputer*p):CountDC(p){}
 void distances_batch_4(faiss::idx_t a,faiss::idx_t b,faiss::idx_t c,faiss::idx_t d,float&x,float&y,float&z,float&w)override{
  for(auto id:{a,b,c,d}){if(count<3)first[count]=id;++count;}dc->distances_batch_4(a,b,c,d,x,y,z,w);
 }
};
int main(int argc,char**argv){try{
 require(argc==3,"evaluate config new_output");threads();auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"preserve existing output");fs::create_directories(out);write_json(out/"config.json",c);
 const bool formal=c["formal"];size_t n=c["n"],d=c["dimension"];auto load_start=Clock::now();auto idx=load_nsg(c["index"]);require(idx->d==d&&idx->ntotal==c["base_n"]&&idx->metric_type==0&&c["threads"]==1,"dataset contract");
 auto q=read_raw<float>(c["queries"].get<std::string>());require(q.size()==n*d,"query shape");for(float x:q)require(std::isfinite(x),"finite query");
 if(c.contains("base")){Fvecs base(c["base"]);require(base.n==idx->ntotal&&base.d==d,"GT base shape");std::vector<float>b(d);for(size_t i=0;i<16;++i){size_t j=i*(base.n/16);idx->storage->reconstruct(j,b.data());require(!memcmp(b.data(),base.row(j),d*4),"NSG and GT base sample bytes");}}
 std::vector<std::unique_ptr<Router>> routers;std::vector<std::string> names;
 for(auto m:c["methods"]){names.push_back(m["name"]);routers.push_back(std::make_unique<Router>(m,d,m["graph"].get<std::string>()));require(routers.back()->graph->M_==16&&routers.back()->graph->ef_construction_==200&&routers.back()->graph->ef_==10,"fixed micro graph parameters");}
 require(names.size()==2&&names[1]=="WFree","two frozen methods");auto spans=make_spans(*idx->acsg.final_graph,idx->ntotal);ResearchKernel kernel(*idx->acsg.final_graph,spans,idx->ntotal);
 auto plain=std::unique_ptr<faiss::DistanceComputer>(acsg::storage_distance_computer(idx->storage));ActualCount counter(acsg::storage_distance_computer(idx->storage));faiss::VisitedTable vt(idx->ntotal);std::vector<acsg::EnterPoint>ep;ep.reserve(3);std::array<faiss::idx_t,100> ids;std::vector<float>norm(d);
 std::ifstream bf("/proc/sys/kernel/random/boot_id");std::string boot;std::getline(bf,boot);json timing=json::array();uint64_t calls=0;int ordinal=0,reps=c["repeats"];auto started=Clock::now();double load_seconds=seconds(load_start);
 for(auto point:c["points"]){int K=point["K"],L=point["L"];require((K==1||K==100)&&L>=K&&L<=1500,"K/L contract");std::array<std::unique_ptr<Batch>,2> reference;
  auto run=[&](int m,Batch&b,bool count){auto&router=*routers[m];router.counting(count);auto&dc=count?static_cast<faiss::DistanceComputer&>(counter):*plain;
   for(size_t i=0;i<n;++i){auto query=q.data()+i*d;const float* routeq=query;if(m==1||c.value("normalize_anchor",false)){std::copy(query,query+d,norm.begin());normalize(norm.data(),d);routeq=norm.data();}
    auto entries=router.route(routeq);std::copy(entries.begin(),entries.end(),b.entries.begin()+3*i);ep.clear();for(int e:entries)ep.emplace_back(e,1);vt.advance();dc.set_query(query);
    kernel.search<true,false,true>(dc,vt,ep,L,K,ids.data(),b.dist.data()+i*K);for(int k=0;k<K;++k)b.ids[i*K+k]=ids[k];
    if(count){b.route_ndc[i]=router.counter.n;b.graph_ndc[i]=counter.count;for(int k=0;k<3;++k)require(counter.first[k]==entries[k],"ordered real entry injection");}
   }calls+=n;require(calls<=c["max_search_calls"].get<uint64_t>(),"search call cap");
  };
  auto key=[&](int m){return "k"+std::to_string(K)+"/"+names[m]+"_L"+std::to_string(L);};
  std::array<std::vector<double>,2> wall;
  for(int rep=0;rep<reps;++rep){int first=(ordinal+rep+c.value("dataset_order",0))%2;for(int z=0;z<2;++z){int m=(first+z)%2;Batch b(n,K);
   if(rep==0){reference[m]=std::make_unique<Batch>(n,K);run(m,*reference[m],false);}threads();auto t=Clock::now();run(m,b,false);double sec=seconds(t);same(*reference[m],b);if(rep==0)save_batch(out/key(m),b,false);wall[m].push_back(sec);
   json row={{"method",names[m]},{"K",K},{"L",L},{"repeat",rep},{"seconds",sec},{"qps",n/sec},{"n",n},{"threads",process_threads()},{"cpu",15},{"formal",formal},{"boot_id",boot},{"search_calls_completed",calls}};timing.push_back(row);write_json(out/"timing_progress.json",timing);std::cout<<row.dump()<<std::endl;
  }}
  for(int m=0;m<2;++m){Batch b(n,K);run(m,b,true);same(*reference[m],b);save_batch(out/key(m),b,true);
   if(c.contains("pilot_reference")){
    auto old=fs::path(c["pilot_reference"].get<std::string>());std::string family=m==1?"WFree":"Identity";auto p=old/(family+"ANN");auto oi=read_raw<int32_t>(p/("k"+std::to_string(K)+".ids.i32"));auto od=read_raw<float>(p/("k"+std::to_string(K)+".distances.f32"));auto oe=read_raw<int32_t>(p/"entries.i32");auto on=read_raw<uint64_t>(p/("k"+std::to_string(K)+".ndc.u64"));auto orn=read_raw<uint64_t>(old/(family+".route_ndc.u64"));std::vector<size_t>rows=c["pilot_rows"];
    require(rows.size()==n,"reference rows");for(size_t i=0;i<n;++i){size_t j=rows[i];require(!memcmp(b.ids.data()+i*K,oi.data()+j*K,K*4)&&!memcmp(b.dist.data()+i*K,od.data()+j*K,K*4)&&!memcmp(b.entries.data()+i*3,oe.data()+j*3,12)&&b.graph_ndc[i]==on[j]&&b.route_ndc[i]==orn[j],"E104 exact output and cost recovery");}
   }
   write_json(out/key(m)/"complete.json",{{"status","PASS"},{"K",K},{"L",L},{"n",n},{"method",names[m]},{"seconds",wall[m]},{"warm_plain_count_bit_parity",true},{"threads",1},{"formal",formal},{"boot_id",boot}});
  }
  ++ordinal;struct rusage ru;getrusage(RUSAGE_SELF,&ru);require(ru.ru_maxrss<=40LL*1024*1024,"40GiB RSS cap");struct statvfs disk;require(statvfs(out.c_str(),&disk)==0&&uint64_t(disk.f_bavail)*disk.f_frsize>=4ULL*1024*1024*1024,"4GiB free required");require(seconds(started)<c["seconds_cap"].get<double>(),"search time cap");write_json(out/"progress.json",{{"points",ordinal},{"search_calls",calls},{"seconds",seconds(started)}});
 }
 require(calls==n*2*c["points"].size()*(reps+2),"exact call accounting");struct rusage ru;getrusage(RUSAGE_SELF,&ru);threads();write_json(out/"complete.json",{{"status","PASS"},{"search_calls",calls},{"router_calls",calls},{"wall_rounds",timing.size()},{"points",ordinal*2},{"seconds_excluding_load",seconds(started)},{"load_seconds",load_seconds},{"seconds_including_load",seconds(load_start)},{"maxrss_kib",ru.ru_maxrss},{"threads",process_threads()},{"cpu",15},{"formal",formal},{"boot_id",boot},{"graph_builds",0}});return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

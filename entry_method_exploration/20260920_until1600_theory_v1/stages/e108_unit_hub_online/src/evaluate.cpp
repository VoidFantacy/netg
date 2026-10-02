#include "search_core.hpp"

void build_graphs(const json& c,const fs::path& out){
 require(!fs::exists(out),"preserve graph build result");json records=json::array();
 for(auto ds:c["configs"]){size_t d=ds["dimension"],h=ds["H"];hnswlib::InnerProductSpace space(d);
  for(auto m:ds["methods"]){
   if(!m["new_graph"].get<bool>())continue;
   auto w=read_raw<float>(m["W"].get<std::string>());auto ids=read_raw<int32_t>(m["ids"].get<std::string>());fs::path path=m["graph"].get<std::string>();
   require(w.size()==h*d&&ids.size()==h&&std::is_sorted(ids.begin(),ids.end())&&!fs::exists(path),"frozen graph input and fresh output");fs::create_directories(path.parent_path());
   auto start=Clock::now();HNSW graph(&space,h,c["M"],c["efConstruction"],c["graph_seed"]);
   for(size_t i=0;i<h;++i)graph.addPoint(w.data()+i*d,ids[i]);graph.saveIndex(path.string());
   Router verify(m,d,path);require(verify.graph->M_==16&&verify.graph->ef_construction_==200&&verify.graph->ef_==10,"graph settings");
   for(size_t i=0;i<h;++i)for(int l=0;l<=verify.graph->element_levels_[i];++l){
    auto* list=l==0?verify.graph->get_linklist0(i):verify.graph->get_linklist(i,l);size_t n=verify.graph->getListCount(list);require(n<=size_t(l?verify.graph->maxM_:verify.graph->maxM0_),"degree cap");std::set<unsigned> unique;auto* neighbors=(hnswlib::tableint*)(list+1);
    for(size_t j=0;j<n;++j)require(neighbors[j]<h&&neighbors[j]!=i&&unique.insert(neighbors[j]).second,"legal unique graph edges");
   }
   records.push_back({{"dataset",ds["dataset"]},{"method",m["name"]},{"graph",path.string()},{"seconds",seconds(start)},{"H",h},{"dimension",d},{"seed",c["graph_seed"]},{"vector_label_topology_verified",true}});threads();
  }
 }
 require(records.size()==4,"exactly four graph builds");write_json(out,{{"status","PASS"},{"graphs",records},{"new_graphs",4},{"query_payload_access",false},{"threads",1}});
}

int main(int argc,char** argv){try{
 threads();if(argc==4&&std::string(argv[1])=="build"){build_graphs(read_json(argv[2]),argv[3]);return 0;}
 require(argc==3,"evaluate config output");auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"preserve output");fs::create_directories(out);write_json(out/"config.json",c);
 bool smoke=c["smoke"],formal=!smoke;size_t n=c["n"],d=c["dimension"],h=c["H"];int reps=smoke?1:3;require(c["threads"]==1&&((smoke&&n==16)||(!smoke&&n==4096)),"query/thread contract");
 auto total=Clock::now();auto idx=load_nsg(c["index"]);require(idx->d==d&&idx->ntotal==c["base_n"]&&idx->metric_type==0,"fixed NSG raw-IP");
 auto q=read_raw<float>(c["queries"].get<std::string>());require(q.size()==4096*d,"original full query matrix");for(float x:q)require(std::isfinite(x),"finite query");
 Fvecs base(c["base"]);require(base.d==d&&base.n==idx->ntotal,"base shape");std::vector<float> sample(d);
 for(size_t i=0;i<16;++i){size_t id=i*(base.n/16);idx->storage->reconstruct(id,sample.data());require(!memcmp(sample.data(),base.row(id),d*4),"original embedded base");}
 std::vector<std::unique_ptr<Router>> routers;std::vector<std::string> names;
 for(auto m:c["methods"]){names.push_back(m["name"]);routers.push_back(std::make_unique<Router>(m,d,m["graph"].get<std::string>()));auto& g=*routers.back()->graph;require(g.M_==16&&g.ef_construction_==200&&g.ef_==10&&g.cur_element_count==h,"router settings");}
 require(names==std::vector<std::string>{"GT10Default","GT10Rebuilt","UnitHub"},"frozen three methods");
 auto spans=make_spans(*idx->acsg.final_graph,idx->ntotal);ResearchKernel kernel(*idx->acsg.final_graph,spans,idx->ntotal);
 std::unique_ptr<faiss::DistanceComputer> plain(acsg::storage_distance_computer(idx->storage));ActualCount count(acsg::storage_distance_computer(idx->storage)),legacy(acsg::storage_distance_computer(idx->storage));
 faiss::VisitedTable vt(idx->ntotal),lvt(idx->ntotal);std::vector<acsg::EnterPoint> ep;ep.reserve(3);std::vector<acsg::Neighbor> scratch;scratch.reserve(801);std::array<faiss::idx_t,100> ids,other;std::array<float,100> od;
 uint64_t calls=0,routecalls=0;int ordinal=0;json timing=json::array();auto started=Clock::now();double load=seconds(total);std::ifstream bf("/proc/sys/kernel/random/boot_id");std::string boot;std::getline(bf,boot);
 auto check=[&](){require(std::time(nullptr)<c["deadline_unix"].get<double>()&&seconds(started)<c["seconds_cap"].get<double>(),"deadline");threads();};
 for(auto point:c["points"]){int K=point["K"],L=point["L"];require((K==1||K==100)&&L>=K&&L<=800,"real K/L");idx->acsg.search_L=L;check();
  std::array<std::unique_ptr<Batch>,3> reference;std::array<std::vector<double>,3> wall;
  auto key=[&](int m){return "k"+std::to_string(K)+"/"+names[m]+"_L"+std::to_string(L);};
  auto run=[&](int m,Batch& b,bool counting){auto& r=*routers[m];r.counting(counting);auto& dc=counting?static_cast<faiss::DistanceComputer&>(count):*plain;
   for(size_t i=0;i<n;++i){auto query=q.data()+i*d;auto e=r.route(query);std::copy(e.begin(),e.end(),b.entries.begin()+3*i);ep.clear();for(int id:e)ep.emplace_back(id,1);vt.advance();dc.set_query(query);kernel.search<true,false,true>(dc,vt,ep,L,K,ids.data(),b.dist.data()+i*K);for(int j=0;j<K;++j)b.ids[i*K+j]=ids[j];
    if(counting){b.route_ndc[i]=r.counter.n;b.graph_ndc[i]=count.count;for(int j=0;j<3;++j)require(count.first[j]==e[j],"original ordered entries");}
   }calls+=n;routecalls+=n;require(calls<=c["max_search_calls"].get<uint64_t>(),"call cap");
  };
  for(int rep=0;rep<reps;++rep){int first=(ordinal+rep+c["dataset_order"].get<int>())%3;
   for(int z=0;z<3;++z){int m=(first+z)%3;Batch b(n,K);if(rep==0){reference[m]=std::make_unique<Batch>(n,K);run(m,*reference[m],false);}check();auto t=Clock::now();run(m,b,false);double sec=seconds(t);same(*reference[m],b);if(rep==0)save_batch(out/key(m),b,false);wall[m].push_back(sec);
    json row={{"method",names[m]},{"K",K},{"L",L},{"repeat",rep},{"seconds",sec},{"qps",n/sec},{"n",n},{"threads",process_threads()},{"cpu",sched_getcpu()},{"formal",formal},{"boot_id",boot}};timing.push_back(row);write_json(out/"timing_progress.json",timing);std::cout<<row.dump()<<std::endl;
   }
  }
  for(int m=0;m<3;++m){Batch b(n,K);run(m,b,true);same(*reference[m],b);save_batch(out/key(m),b,true);
   if(smoke)for(size_t i=0;i<n;++i){ep.clear();for(int j=0;j<3;++j)ep.emplace_back(b.entries[i*3+j],1);lvt.advance();legacy.set_query(q.data()+i*d);idx->acsg.search_new(legacy,K,other.data(),od.data(),lvt,2,ep,&scratch);++calls;require(legacy.count==b.graph_ndc[i],"legacy graph NDC");for(int j=0;j<K;++j)require(other[j]==b.ids[i*K+j]&&!memcmp(od.data()+j,b.dist.data()+i*K+j,4),"linked E99 bit parity");}
   if(m==0){auto p=fs::path(c["reference"].get<std::string>())/("k"+std::to_string(K))/(c["reference_method"].get<std::string>()+"_L"+std::to_string(L));auto oi=read_raw<int32_t>(p/"ids.i32"),oe=read_raw<int32_t>(p/"entry_ids.i32");auto odist=read_raw<float>(p/"distances.f32");auto on=read_raw<uint64_t>(p/"graph_ndc.u64"),orn=read_raw<uint64_t>(p/"route_ndc.u64");require(oi.size()==4096ULL*K&&oe.size()==4096*3&&odist.size()==oi.size()&&on.size()==4096&&orn.size()==4096,"E105 reference shapes");require(!memcmp(b.ids.data(),oi.data(),n*K*4)&&!memcmp(b.entries.data(),oe.data(),n*12)&&!memcmp(b.dist.data(),odist.data(),n*K*4)&&!memcmp(b.graph_ndc.data(),on.data(),n*8)&&!memcmp(b.route_ndc.data(),orn.data(),n*8),"E105 full default restoration");}
   write_json(out/key(m)/"complete.json",{{"status","PASS"},{"method",names[m]},{"K",K},{"L",L},{"n",n},{"seconds",wall[m]},{"warm_plain_count_bit_parity",true},{"legacy_bit_parity",smoke},{"formal",formal},{"threads",1},{"boot_id",boot}});
  }
  ++ordinal;check();struct rusage ru;getrusage(RUSAGE_SELF,&ru);require(ru.ru_maxrss<=40LL*1024*1024,"40GiB RSS");struct statvfs disk;require(statvfs(out.c_str(),&disk)==0&&uint64_t(disk.f_bavail)*disk.f_frsize>=4ULL*1024*1024*1024,"4GiB free");write_json(out/"progress.json",{{"points",ordinal},{"NSG_calls",calls},{"router_calls",routecalls},{"seconds",seconds(started)}});
 }
 require(calls==c["expected_search_calls"].get<uint64_t>()&&routecalls==n*3*c["points"].size()*(reps+2),"exact accounting");struct rusage ru;getrusage(RUSAGE_SELF,&ru);write_json(out/"complete.json",{{"status","PASS"},{"NSG_calls",calls},{"router_calls",routecalls},{"points",ordinal*3},{"wall_rounds",timing.size()},{"formal",formal},{"seconds_including_load",seconds(total)},{"load_seconds",load},{"maxrss_kib",ru.ru_maxrss},{"threads",process_threads()},{"cpu",sched_getcpu()},{"boot_id",boot}});return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

#include "search_core.hpp"

void prepare(const json& c,const fs::path& out){
 require(!fs::exists(out),"fresh prepare result");json records=json::array();
 for(auto ds:c["datasets"]){size_t d=ds["dimension"],h=ds["H"];
  for(auto m:ds["methods"]){
   if(!m["hybrid"].get<bool>())continue;
   json src={{"name",m["name"]},{"ids",m["ids"]},{"W",m["source_W"]}};
   Router r(src,d,m["source_graph"].get<std::string>());
   auto w=read_raw<float>(m["W"].get<std::string>());require(w.size()==h*d,"target W shape");
   fs::path before=m["before"].get<std::string>(),after=m["graph"].get<std::string>();
   require(!fs::exists(before)&&!fs::exists(after),"preserve model copies");fs::create_directories(before.parent_path());fs::create_directories(after.parent_path());
   r.graph->saveIndex(before.string());
   for(size_t i=0;i<h;++i)std::memcpy(r.graph->getDataByInternalId(i),w.data()+i*d,d*4);
   r.graph->saveIndex(after.string());Router check(m,d,after);
   records.push_back({{"dataset",ds["dataset"]},{"method",m["name"]},{"before",before.string()},{"after",after.string()},{"H",h},{"d",d},{"vector_bits_verified",true}});
  }
 }
 require(records.size()==4,"four hybrid copies");write_json(out,{{"status","PASS"},{"records",records},{"ordinary_graph_builds",0},{"hybrid_index_copies",4},{"before_serializations",4},{"NSG_calls",0},{"ANN_calls",0},{"threads",1}});
}

int main(int argc,char**argv){try{
 threads();require(argc==4||argc==3,"prepare or evaluate");
 if(argc==4){require(std::string(argv[1])=="prepare","prepare command");prepare(read_json(argv[2]),argv[3]);return 0;}
 auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"fresh diagnostic output");fs::create_directories(out);write_json(out/"config.json",c);
 auto total=Clock::now();bool smoke=c["smoke"];size_t n=c["n"],d=c["dimension"],h=c["H"];require((smoke&&n==16)||(!smoke&&n==4096),"fixed query counts");
 auto guard=[&](){threads();require(std::time(nullptr)<c["deadline_unix"].get<double>()&&seconds(total)<c["seconds_cap"].get<double>(),"deadline");struct rusage ru;getrusage(RUSAGE_SELF,&ru);require(ru.ru_maxrss<=40LL*1024*1024,"RSS cap");struct statvfs v;require(statvfs(out.c_str(),&v)==0&&uint64_t(v.f_bavail)*v.f_frsize>=4ULL*1024*1024*1024,"free disk");};
 auto idx=load_nsg(c["index"]);require(idx->d==d&&idx->ntotal==c["base_n"]&&idx->metric_type==0,"original raw IP NSG");
 Fvecs base(c["base"]);require(base.d==d&&base.n==idx->ntotal,"base identity dimensions");std::vector<float> sample(d);
 for(size_t z=0;z<16;++z){size_t id=z*(base.n/16);idx->storage->reconstruct(id,sample.data());require(!std::memcmp(sample.data(),base.row(id),d*4),"embedded original base");}
 auto q=read_raw<float>(c["queries"].get<std::string>());require(q.size()==4096*d,"full original query shape");for(float x:q)require(std::isfinite(x),"finite queries");
 std::vector<std::unique_ptr<Router>> routers;std::vector<std::string> names;uint64_t calls=0,ann=0;
 std::vector<std::vector<std::array<int32_t,3>>> entries;std::vector<std::vector<uint64_t>> route_ndc;
 for(auto m:c["methods"]){
  names.push_back(m["name"]);routers.push_back(std::make_unique<Router>(m,d,m["graph"].get<std::string>()));auto&r=*routers.back();
  require(r.graph->cur_element_count==h&&r.graph->M_==16&&r.graph->ef_construction_==200&&r.graph->ef_==10,"router contract");
  entries.emplace_back(n);route_ndc.emplace_back(n);r.counting(true);
  for(size_t i=0;i<n;++i){entries.back()[i]=r.route(q.data()+i*d);route_ndc.back()[i]=r.counter.n;++ann;}
  if(smoke){r.counting(false);for(size_t i=0;i<n;++i){require(r.route(q.data()+i*d)==entries.back()[i],"plain count router parity");++ann;}}
 }
 require(names==std::vector<std::string>{"A_P_GP","B_U_GP","C_P_GU","D_U_GU"},"fixed four cells");
 auto spans=make_spans(*idx->acsg.final_graph,idx->ntotal);ResearchKernel kernel(*idx->acsg.final_graph,spans,idx->ntotal);
 ActualCount dc(acsg::storage_distance_computer(idx->storage)),legacy(acsg::storage_distance_computer(idx->storage));std::unique_ptr<faiss::DistanceComputer> plain(acsg::storage_distance_computer(idx->storage));
 faiss::VisitedTable vt(idx->ntotal),lvt(idx->ntotal);std::vector<acsg::EnterPoint> ep;ep.reserve(3);std::vector<acsg::Neighbor> scratch;scratch.reserve(801);std::array<faiss::idx_t,100> ids,other;std::array<float,100> od;
 int points=0;
 for(auto point:c["points"]){int K=point["K"],L=point["L"];require((K==1||K==100)&&L>=K&&L<=800,"true K L");idx->acsg.search_L=L;
  for(size_t m=0;m<4;++m){guard();auto start=Clock::now();Batch b(n,K);
   for(size_t i=0;i<n;++i){if(i%64==0)guard();ep.clear();for(int e:entries[m][i])ep.emplace_back(e,1);std::copy(entries[m][i].begin(),entries[m][i].end(),b.entries.begin()+3*i);vt.advance();dc.set_query(q.data()+i*d);kernel.search<true,false,true>(dc,vt,ep,L,K,ids.data(),b.dist.data()+i*K);++calls;
    for(int j=0;j<K;++j){require(ids[j]>=0&&ids[j]<idx->ntotal&&std::isfinite(b.dist[i*K+j]),"valid outputs");b.ids[i*K+j]=ids[j];}for(int j=0;j<3;++j)require(dc.first[j]==entries[m][i][j],"entry order");b.graph_ndc[i]=dc.count;b.route_ndc[i]=route_ndc[m][i];
    if(smoke){vt.advance();plain->set_query(q.data()+i*d);kernel.search<true,false,true>(*plain,vt,ep,L,K,other.data(),od.data());++calls;for(int j=0;j<K;++j)require(ids[j]==other[j]&&!std::memcmp(od.data()+j,b.dist.data()+i*K+j,4),"plain count kernel parity");lvt.advance();legacy.set_query(q.data()+i*d);idx->acsg.search_new(legacy,K,other.data(),od.data(),lvt,2,ep,&scratch);++calls;require(legacy.count==b.graph_ndc[i],"linked NDC parity");for(int j=0;j<K;++j)require(ids[j]==other[j]&&!std::memcmp(od.data()+j,b.dist.data()+i*K+j,4),"linked output parity");}
   }
   auto path=out/("k"+std::to_string(K))/(names[m]+"_L"+std::to_string(L));save_batch(path,b,false);save_batch(path,b,true);
   if(m==0||m==3){auto ref=fs::path(c["reference_E108"].get<std::string>())/("k"+std::to_string(K))/((m==0?std::string("GT10Default"):std::string("UnitHub"))+"_L"+std::to_string(L));auto oi=read_raw<int32_t>(ref/"ids.i32"),oe=read_raw<int32_t>(ref/"entry_ids.i32");auto odist=read_raw<float>(ref/"distances.f32");auto og=read_raw<uint64_t>(ref/"graph_ndc.u64"),orn=read_raw<uint64_t>(ref/"route_ndc.u64");require(oi.size()==4096ULL*K&&oe.size()==4096*3&&og.size()==4096&&orn.size()==4096,"E108 shape");require(!std::memcmp(oi.data(),b.ids.data(),n*K*4)&&!std::memcmp(oe.data(),b.entries.data(),n*12)&&!std::memcmp(odist.data(),b.dist.data(),n*K*4)&&!std::memcmp(og.data(),b.graph_ndc.data(),n*8)&&!std::memcmp(orn.data(),b.route_ndc.data(),n*8),"E108 all-field restoration");}
   require(calls<=c["expected_NSG_calls"].get<uint64_t>(),"call budget");++points;write_json(path/"complete.json",{{"status","PASS"},{"n",n},{"K",K},{"L",L},{"method",names[m]},{"diagnostic_seconds",seconds(start)},{"formal_QPS",false},{"threads",1}});write_json(out/"progress.json",{{"points",points},{"NSG_calls",calls},{"ANN_calls",ann},{"seconds",seconds(total)}});std::cout<<names[m]<<" K="<<K<<" L="<<L<<" complete"<<std::endl;
  }
 }
 guard();require(calls==c["expected_NSG_calls"].get<uint64_t>()&&ann==c["expected_ANN_calls"].get<uint64_t>(),"exact total calls");struct rusage ru;getrusage(RUSAGE_SELF,&ru);write_json(out/"complete.json",{{"status","PASS"},{"NSG_calls",calls},{"ANN_calls",ann},{"points",points},{"seconds",seconds(total)},{"maxrss_kib",ru.ru_maxrss},{"threads",process_threads()},{"cpu",sched_getcpu()},{"ordinary_graph_builds",0},{"formal_QPS",false}});return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

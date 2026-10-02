#include "search_core.hpp"
#include <faiss/IndexFlat.h>

void counterexample(const fs::path& out){
 faiss::IndexFlatIP storage(1);float vals[]={0,.1f,1,.9f,.8f},q=1;storage.add(5,vals);
 acsg::Graph<int32_t> graph(5,1);int next[]={1,2,3,4,0};for(int i=0;i<5;++i)graph.at(i,0)=next[i];
 std::vector<uint8_t> spans(5,1);ResearchKernel kernel(graph,spans,5);faiss::VisitedTable vt(5);
 std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(&storage));
 faiss::idx_t id;float distance;json observations=json::array();
 for(auto ids:std::vector<std::vector<int>>{{0},{0,3}}){std::vector<acsg::EnterPoint> ep;for(int e:ids)ep.emplace_back(e,1);vt.advance();dc->set_query(&q);kernel.search<true,false,true>(*dc,vt,ep,2,1,&id,&distance);observations.push_back({{"entries",ids},{"returned",id},{"distance",distance}});require(id==(ids.size()==1?2:3),"nonmonotone entry counterexample");}
 write_json(out,{{"status","PASS"},{"synthetic_searches",2},{"strongly_connected_cycle",true},{"L",2},{"K",1},{"observations",observations}});
}
int main(int argc,char** argv){try{
 threads();if(argc==3&&std::string(argv[1])=="counterexample"){require(!fs::exists(argv[2]),"preserve fixture");counterexample(argv[2]);return 0;}
 require(argc==3,"factorial config output");auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"preserve output");fs::create_directories(out);write_json(out/"config.json",c);
 auto start=Clock::now();size_t n=c["n"],d=c["dimension"],h=c["H"];bool smoke=c["smoke"];require(c["threads"]==1&&(n==16||n==4096),"query/thread contract");
 auto q=read_raw<float>(c["queries"].get<std::string>());require(q.size()>=n*d,"query size");for(float x:q)require(std::isfinite(x),"finite query");
 auto hubids=read_raw<int32_t>(c["hub_ids"].get<std::string>());require(hubids.size()==h&&std::is_sorted(hubids.begin(),hubids.end()),"real hub IDs");
 auto idx=load_nsg(c["index"]);require(idx->d==d&&idx->ntotal==c["base_n"]&&idx->metric_type==0,"fixed raw-IP graph");
 Fvecs base(c["base"].get<std::string>());require(base.d==d&&base.n==idx->ntotal,"base dimensions");std::vector<float> sample(d);
 for(size_t j=0;j<16;++j){size_t id=j*(base.n/16);idx->storage->reconstruct(id,sample.data());require(!memcmp(sample.data(),base.row(id),d*4),"embedded base byte parity");}
 auto spans=make_spans(*idx->acsg.final_graph,idx->ntotal);ResearchKernel kernel(*idx->acsg.final_graph,spans,idx->ntotal);
 ActualCount dc(acsg::storage_distance_computer(idx->storage)),legacy(acsg::storage_distance_computer(idx->storage));
 std::unique_ptr<faiss::DistanceComputer> plain(acsg::storage_distance_computer(idx->storage));
 faiss::VisitedTable vt(idx->ntotal),pvt(idx->ntotal),lvt(idx->ntotal);std::vector<acsg::Neighbor> scratch;scratch.reserve(1501);
 std::vector<acsg::EnterPoint> ep;ep.reserve(3);std::array<faiss::idx_t,100> answer,other;std::array<float,100> ad,od;
 hnswlib::InnerProductSpace space(d);auto fn=space.get_dist_func();auto param=space.get_dist_func_param();uint64_t calls=0,anncalls=0,exactdist=0;
 auto checktime=[&](){require(std::time(nullptr)<c["deadline_unix"].get<double>()&&seconds(start)<c["seconds_cap"].get<double>(),"deadline");};
 for(auto m:c["methods"]){
  checktime();std::string name=m["name"],route=m["route"];int count=m["entry_count"];require(count==1||count==3,"entry count");fs::path sub=out/name;fs::create_directories(sub);
  std::vector<float> w;if(route!="fixed"){w=read_raw<float>(m["W"].get<std::string>());require(w.size()==h*d,"profile shape");for(float x:w)require(std::isfinite(x),"profile finite");}
  std::unique_ptr<Router> router;if(route=="ann")router=std::make_unique<Router>(m,d,m["graph"].get<std::string>());
  std::vector<int32_t> entries(n*3,-1);std::vector<uint64_t> route_ndc(n);std::vector<float> margin(n);
  for(size_t i=0;i<n;++i){
   if(route=="fixed"){entries[i*3]=idx->acsg.enterpoint;continue;}
   if(router){router->counting(true);auto e=router->route(q.data()+i*d);route_ndc[i]=router->counter.n;router->counting(false);require(e==router->route(q.data()+i*d),"ANN count/plain route parity");anncalls+=2;std::copy(e.begin(),e.end(),entries.begin()+i*3);continue;}
   require(route=="exact","route kind");std::vector<std::pair<float,int32_t>> scores;scores.reserve(h);for(size_t j=0;j<h;++j)scores.emplace_back(fn(q.data()+i*d,w.data()+j*d,param),hubids[j]);exactdist+=h;route_ndc[i]=h;
   std::partial_sort(scores.begin(),scores.begin()+4,scores.end());margin[i]=scores[count].first-scores[count-1].first;
   for(int j=0;j<count;++j)entries[i*3+j]=scores[j].second;std::sort(entries.begin()+i*3,entries.begin()+i*3+count);
  }
  write_raw(sub/"entries.i32",entries);write_raw(sub/"route_ndc.u64",route_ndc);if(route=="exact")write_raw(sub/"exact_margin.f32",margin);
  for(auto it=c["K_L"].begin();it!=c["K_L"].end();++it){int K=std::stoi(it.key());require(K==1||K==100,"real K");
   for(int L:it.value()){
    require(L>=K&&L<=800,"valid L");idx->acsg.search_L=L;auto point=sub/("k"+std::to_string(K)+"_L"+std::to_string(L));fs::create_directories(point);
    std::vector<int32_t> ids(n*K);std::vector<float> dist(n*K);std::vector<uint64_t> ndc(n);
    for(size_t i=0;i<n;++i){
     if(i%128==0)checktime();ep.clear();for(int j=0;j<count;++j)ep.emplace_back(entries[i*3+j],1);vt.advance();dc.set_query(q.data()+i*d);
     kernel.search<true,false,true>(dc,vt,ep,L,K,answer.data(),ad.data());++calls;ndc[i]=dc.count;
     for(int j=0;j<count;++j)require(dc.first[j]==entries[i*3+j],"injected entry order");
     std::set<faiss::idx_t> unique;for(int j=0;j<K;++j){require(answer[j]>=0&&answer[j]<idx->ntotal&&std::isfinite(ad[j]),"valid output");unique.insert(answer[j]);ids[i*K+j]=answer[j];dist[i*K+j]=ad[j];}require(unique.size()==size_t(K),"unique output");
     pvt.advance();plain->set_query(q.data()+i*d);kernel.search<true,false,true>(*plain,pvt,ep,L,K,other.data(),od.data());++calls;
     require(!memcmp(answer.data(),other.data(),K*sizeof(faiss::idx_t))&&!memcmp(ad.data(),od.data(),K*4),"full count/plain output parity");
     if(smoke){lvt.advance();legacy.set_query(q.data()+i*d);idx->acsg.search_new(legacy,K,other.data(),od.data(),lvt,2,ep,&scratch);++calls;require(!memcmp(answer.data(),other.data(),K*sizeof(faiss::idx_t))&&!memcmp(ad.data(),od.data(),K*4)&&legacy.count==dc.count,"linked E99 baseline parity");}
    }
    write_raw(point/"ids.i32",ids);write_raw(point/"distances.f32",dist);write_raw(point/"ndc.u64",ndc);
    if(route=="ann"){
     auto ref=fs::path(c["reference"].get<std::string>())/("k"+std::to_string(K))/(c["reference_method"].get<std::string>()+"_L"+std::to_string(L));
     auto ri=read_raw<int32_t>(ref/"ids.i32"),re=read_raw<int32_t>(ref/"entry_ids.i32");auto rd=read_raw<float>(ref/"distances.f32");auto rn=read_raw<uint64_t>(ref/"graph_ndc.u64"),rr=read_raw<uint64_t>(ref/"route_ndc.u64");
     require(ri.size()==4096ULL*K&&re.size()==4096*3&&rd.size()==ri.size()&&rn.size()==4096&&rr.size()==4096,"E105 reference dimensions");
     require(!memcmp(ids.data(),ri.data(),n*K*4)&&!memcmp(dist.data(),rd.data(),n*K*4)&&!memcmp(entries.data(),re.data(),n*3*4)&&!memcmp(ndc.data(),rn.data(),n*8)&&!memcmp(route_ndc.data(),rr.data(),n*8),"full E105 default restoration");
    }
    if(L==128&&(name=="GT13"||name=="GT103")){
     std::string oldname=name=="GT13"?"GT1Exact":c["E106_family"].get<std::string>()+"OriginalExact";
     auto ref=fs::path(c["reference_E106"].get<std::string>())/"results"/c["dataset"].get<std::string>()/oldname;
     auto ri=read_raw<int32_t>(ref/("k"+std::to_string(K)+".ids.i32")),re=read_raw<int32_t>(ref/"entries.i32");auto rd=read_raw<float>(ref/("k"+std::to_string(K)+".distances.f32"));auto rn=read_raw<uint64_t>(ref/("k"+std::to_string(K)+".ndc.u64"));
     require(ri.size()==4096ULL*K&&rd.size()==ri.size()&&re.size()==4096*3&&rn.size()==4096,"E106 dimensions");require(!memcmp(ids.data(),ri.data(),n*K*4)&&!memcmp(dist.data(),rd.data(),n*K*4)&&!memcmp(entries.data(),re.data(),n*3*4)&&!memcmp(ndc.data(),rn.data(),n*8),"E106 exact restoration");
    }
    write_json(point/"complete.json",{{"status","PASS"},{"K",K},{"L",L},{"n",n},{"method",name},{"entry_count",count},{"plain_count_bit_parity",true},{"legacy_checked",smoke},{"formal_QPS",false}});
    write_json(out/"progress.json",{{"method",name},{"K",K},{"L",L},{"calls",calls},{"seconds",seconds(start)}});std::cout<<name<<" K="<<K<<" L="<<L<<" calls="<<calls<<std::endl;
   }
  }
  threads();resources(out);struct rusage ru;getrusage(RUSAGE_SELF,&ru);require(ru.ru_maxrss<=40LL*1024*1024&&calls<=c["max_search_calls"].get<uint64_t>(),"bounded resources");
 }
 require(calls==c["expected_search_calls"].get<uint64_t>(),"total call accounting");struct rusage ru;getrusage(RUSAGE_SELF,&ru);
 write_json(out/"complete.json",{{"status","PASS"},{"calls",calls},{"ann_calls",anncalls},{"exact_profile_distances",exactdist},{"seconds",seconds(start)},{"maxrss_kib",ru.ru_maxrss},{"threads",1},{"cpu",15},{"formal_QPS",false}});return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

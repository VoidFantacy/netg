#include "base_engine.hpp"

void resource_guard(const json&c,const fs::path&out,Clock::time_point started){
 threads();struct statvfs v;require(!statvfs(out.c_str(),&v),"statvfs");require(uint64_t(v.f_bavail)*v.f_frsize>=c["min_free_bytes"].get<uint64_t>(),"disk reserve");
 struct rusage u;getrusage(RUSAGE_SELF,&u);require(uint64_t(u.ru_maxrss)*1024<=c["maxrss_bytes"].get<uint64_t>(),"RSS cap");require(seconds(started)<=c["seconds_cap"].get<double>(),"native deadline");
}
void structure(HNSW&g,size_t n){
 require(g.cur_element_count==n&&g.max_elements_==n&&g.M_==16&&g.ef_construction_==200,"new graph contract");
 require(g.enterpoint_node_<n&&g.maxlevel_>=0,"graph entry");
 for(size_t i=0;i<n;++i){require(g.getExternalLabel(i)==i&&g.element_levels_[i]>=0,"slot label/level");
  for(int l=0;l<=g.element_levels_[i];++l){auto*ll=g.get_linklist_at_level(i,l);size_t degree=g.getListCount(ll);require(degree<=(l?g.maxM_:g.maxM0_),"degree cap");auto*nb=(hnswlib::tableint*)(ll+1);
   for(size_t j=0;j<degree;++j)require(nb[j]<n&&g.element_levels_[nb[j]]>=l,"valid neighbor/level");
  }
 }
}
struct CaseRoute{
 hnswlib::InnerProductSpace space;std::unique_ptr<HNSW>graph;CountParam counter;uint64_t calls=0;
 CaseRoute(const fs::path&p,size_t d,size_t n):space(d),graph(std::make_unique<HNSW>(&space,p.string(),false,n)),counter{space.get_dist_func(),space.get_dist_func_param(),0}{graph->setEf(10);structure(*graph,n);}
 void counting(bool yes){graph->fstdistfunc_=yes?counted:space.get_dist_func();graph->dist_func_param_=yes?(void*)&counter:space.get_dist_func_param();}
 int slot(const float*q){++calls;counter.n=0;auto heap=graph->searchKnn(q,1);require(heap.size()==1,"one case slot");return int(heap.top().second);}
};
void measure(const json&c){
 threads();auto started=Clock::now();size_t n=c["n"],d=c["dimension"],tn=c["train_n"];require(n==4096&&tn==20000,"fixed roles");
 fs::path out=fs::path(c["root"].get<std::string>())/"results"/c["dataset"].get<std::string>();require(!fs::exists(out),"preserve results");fs::create_directories(out);write_json(out/"config.json",c);
 auto q=read_raw<float>(c["queries"].get<std::string>());require(q.size()==n*d,"query shape");for(float x:q)require(std::isfinite(x),"finite query");
 auto target=read_raw<int32_t>(c["targets"].get<std::string>());require(target.size()==tn,"target mapping shape");for(int x:target)require(x>=0&&x<c["base_n"].get<int32_t>(),"mapping range");
 Route router(c["anchor"],d);CaseRoute tr(c["target_graph"].get<std::string>(),d,tn);
 Fvecs base(c["base"]);require(base.d==d,"native base dimension");std::vector<float>v(d);
 for(size_t i=0;i<tn;++i)require(!memcmp(base.row(target[i]),tr.graph->getDataByInternalId(i),4*d),"frozen target vector bits");
 auto idx=load_nsg(c["index"]);require(idx->d==int(d)&&idx->ntotal==c["base_n"].get<int64_t>()&&idx->metric_type==0,"fixed base/index");
 for(size_t j=0;j<16;++j){size_t i=j*(base.n/16);idx->storage->reconstruct(i,v.data());require(!memcmp(v.data(),base.row(i),4*d),"embedded base bytes");}
 Engine engine(*idx,router);std::array<faiss::idx_t,100>I,legacy;std::array<float,100>legacyD;
 std::array<std::string,3>names={"Default3","DefaultRank1","TargetBank1"};for(int m=0;m<3;++m)require(c["methods"][m]==names[m],"method order");
 auto set_counting=[&](bool yes){router.counting(yes);tr.counting(yes);};
 auto once=[&](size_t qi,int m,int K,int L,Batch&b,size_t bi,int32_t&slot,bool counting){
  const float* query=q.data()+qi*d;std::array<int32_t,3>entries{-1,-1,-1};slot=-1;uint64_t rndc=0;
  if(m==0){entries=router.original(query);rndc=router.counter.n;}
  else if(m==1){entries[0]=router.ranked(query).ids[0];rndc=router.counter.n;}
  else{require(m==2,"target method");slot=tr.slot(query);require(slot>=0&&size_t(slot)<tn,"target slot range");entries[0]=target[slot];rndc=tr.counter.n;}
  std::copy(entries.begin(),entries.end(),b.entries.begin()+bi*3);engine.search(query,entries,K,L,I.data(),b.dist.data()+bi*K,counting);for(int j=0;j<K;++j)b.ids[bi*K+j]=I[j];
  if(counting){b.graph_ndc[bi]=engine.count.count;b.route_ndc[bi]=rndc;}
 };
 json timings=json::array();uint64_t smoke=0;int ordinal=0;
 write_json(out/"model_identity_gate.json",{{"status","PASS"},{"frozen_target_graph_vectors_labels_structure",true},{"train_cases",tn},{"no_GT_read_in_native",true}});
 for(auto pt:c["points"]){int K=pt["K"],L=pt["L"];require((K==1||K==100)&&L>=K&&L<=1400,"K L");auto point=out/("k"+std::to_string(K)+"_L"+std::to_string(L));fs::create_directories(point);
  for(int m=0;m<3;++m)for(size_t i=0;i<16;++i){Batch plain(1,K),count(1,K);int32_t a,b;set_counting(false);once(i,m,K,L,plain,0,a,false);set_counting(true);once(i,m,K,L,count,0,b,true);same(plain,count);require(a==b,"case slot plain/count");auto ndc=engine.count.count;
   std::array<int32_t,3>e;std::copy(count.entries.begin(),count.entries.end(),e.begin());engine.search(q.data()+i*d,e,K,L,legacy.data(),legacyD.data(),true,true);
   for(int j=0;j<K;++j)require(legacy[j]==plain.ids[j],"E99 return ID");require(!memcmp(legacyD.data(),plain.dist.data(),4*K)&&engine.count.count==ndc,"E99 distance and NDC");smoke+=3;
  }
  set_counting(false);std::array<std::unique_ptr<Batch>,3>reference;std::array<std::vector<int32_t>,3>refslots;
  for(int rep=0;rep<3;++rep)for(int offset=0;offset<3;++offset){int m=(ordinal+rep+offset)%3;
   if(rep==0){Batch warm(128,K);for(size_t i=0;i<128;++i){int32_t slot;once(i,m,K,L,warm,i,slot,false);}}
   Batch b(n,K);std::vector<int32_t>slots(n);threads();auto start=Clock::now();for(size_t i=0;i<n;++i)once(i,m,K,L,b,i,slots[i],false);double elapsed=seconds(start);threads();
   if(rep==0){reference[m]=std::make_unique<Batch>(b);refslots[m]=slots;save_batch(point/names[m],b,false);write_raw(point/names[m]/"route_slots.i32",slots);}else{same(*reference[m],b);require(slots==refslots[m],"repeat case slots");}
   json row={{"method",names[m]},{"K",K},{"L",L},{"repeat",rep},{"n",n},{"seconds",elapsed},{"qps",n/elapsed},{"threads",1}};timings.push_back(row);write_json(out/"timings.json",timings);std::cout<<row.dump()<<std::endl;resource_guard(c,out,started);require(engine.calls<=c["max_search_calls"].get<uint64_t>(),"search cap");
  }
  set_counting(true);
  for(int m=0;m<3;++m){Batch count(n,K);std::vector<int32_t>slots(n);for(size_t i=0;i<n;++i)once(i,m,K,L,count,i,slots[i],true);same(*reference[m],count);require(slots==refslots[m],"full count case slots");save_batch(point/names[m],count,true);
   if(m==0){auto old=fs::path(c["old_results"].get<std::string>())/("k"+std::to_string(K))/(c["anchor"]["name"].get<std::string>()+"_L"+std::to_string(L));
    require(count.ids==read_raw<int32_t>(old/"ids.i32")&&count.entries==read_raw<int32_t>(old/"entry_ids.i32"),"original default historical ID/entry parity");auto dist=read_raw<float>(old/"distances.f32");require(dist.size()==count.dist.size()&&!memcmp(dist.data(),count.dist.data(),4*dist.size()),"default historical distance bits");
    require(count.graph_ndc==read_raw<uint64_t>(old/"graph_ndc.u64")&&count.route_ndc==read_raw<uint64_t>(old/"route_ndc.u64"),"default historical NDC");
   }
   auto center=fs::path(c["previous_results"].get<std::string>())/("k"+std::to_string(K)+"_L"+std::to_string(L))/names[m];
   if(fs::exists(center)){
    require(count.ids==read_raw<int32_t>(center/"ids.i32")&&count.entries==read_raw<int32_t>(center/"entry_ids.i32"),"165 center IDs/entries");
    auto dd=read_raw<float>(center/"distances.f32");require(dd.size()==count.dist.size()&&!memcmp(dd.data(),count.dist.data(),dd.size()*4),"165 center distances");
    require(count.graph_ndc==read_raw<uint64_t>(center/"graph_ndc.u64")&&count.route_ndc==read_raw<uint64_t>(center/"route_ndc.u64")&&slots==read_raw<int32_t>(center/"route_slots.i32"),"165 center NDC/slot");
   }
   resource_guard(c,out,started);
  }
  write_json(point/"complete.json",{{"status","PASS"},{"n",n},{"K",K},{"L",L},{"all_plain_count_repeat_bits",true},{"Default3_historical_all_fields",true},{"center_165_parity_when_available",true}});++ordinal;
 }
 struct rusage u;getrusage(RUSAGE_SELF,&u);resource_guard(c,out,started);require(engine.calls==298080&&router.calls+tr.calls==297792,"planned query counts");
 write_json(out/"complete.json",{{"status","PASS"},{"seconds",seconds(started)},{"n",n},{"new_NSG",engine.calls},{"new_ANN",router.calls+tr.calls},{"route_calls",{{"GT10",router.calls},{"TargetIndex",tr.calls}}},{"smoke_NSG",smoke},{"threads",1},{"cpu",15},{"maxrss_kib",u.ru_maxrss}});std::cout<<"MEASURE_PASS "<<c["dataset"]<<" NSG "<<engine.calls<<std::endl;
}
int main(int argc,char**argv){try{require(argc==2,"experiment native_config");measure(read_json(argv[1]));return 0;}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

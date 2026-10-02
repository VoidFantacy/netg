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
struct Engine{
 acsg::IndexACSGFlat& idx;std::vector<uint8_t> spans;ResearchKernel kernel;std::unique_ptr<faiss::DistanceComputer> dc;ActualCount count;faiss::VisitedTable vt;std::vector<acsg::EnterPoint> ep;std::vector<acsg::Neighbor> legacy;uint64_t calls=0;
 Engine(acsg::IndexACSGFlat& x):idx(x),spans(make_spans(*x.acsg.final_graph,x.ntotal)),kernel(*x.acsg.final_graph,spans,x.ntotal),dc(acsg::storage_distance_computer(x.storage)),count(acsg::storage_distance_computer(x.storage)),vt(x.ntotal){ep.reserve(3);legacy.reserve(1501);}
 void search(const float*q,std::array<int32_t,3> e,int L,int K,faiss::idx_t* I,float*D,bool counting=false,bool original=false){
  require(e[0]<e[1]&&e[1]<e[2]&&e[0]>=0&&e[2]<idx.ntotal,"unique sorted real entries");
  ep.clear();for(int h:e)ep.emplace_back(h,1);vt.advance();auto&dis=counting?static_cast<faiss::DistanceComputer&>(count):*dc;dis.set_query(q);
  if(original){idx.acsg.search_L=L;idx.acsg.search_new(dis,K,I,D,vt,2,ep,&legacy);}else kernel.search<true,false,true>(dis,vt,ep,L,K,I,D);
  if(counting)for(int j=0;j<3;++j)require(count.first[j]==e[j],"entry consumption");++calls;
 }
};
struct Action{int old_id,new_id;std::array<int32_t,3> entries;};
std::array<int32_t,3> remap(std::array<int32_t,3> e,const std::vector<std::pair<int,int>>& edits){
 for(auto& h:e){auto p=std::lower_bound(edits.begin(),edits.end(),std::make_pair(h,-1));if(p!=edits.end()&&p->first==h)h=p->second;}std::sort(e.begin(),e.end());require(e[0]<e[1]&&e[1]<e[2],"remap collision");return e;
}
int main(int argc,char**argv){try{
 require(argc==3,"experiment config new_output");threads();auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"preserve output");fs::create_directories(out);write_json(out/"config.json",c);auto start=Clock::now();
 size_t n=c["n"],d=c["dimension"];auto q=read_raw<float>(c["queries"].get<std::string>());require(q.size()==n*d,"query shape");for(float v:q)require(std::isfinite(v),"finite query");
 Router router(c["anchor"],d,c["anchor"]["graph"].get<std::string>());require(router.graph->M_==16&&router.graph->ef_construction_==200&&router.graph->ef_==10,"frozen routing params");
 std::string mode=c["mode"];std::vector<int32_t> entries(n*3);std::vector<uint64_t> routes(n);
 if(mode=="route"){
  for(size_t i=0;i<n;++i){router.counting(false);auto a=router.route(q.data()+i*d);router.counting(true);auto b=router.route(q.data()+i*d);require(a==b,"route plain/count parity");std::copy(a.begin(),a.end(),entries.begin()+3*i);routes[i]=router.counter.n;}
  write_raw(out/"entries.i32",entries);write_raw(out/"route_ndc.u64",routes);write_json(out/"complete.json",{{"status","PASS"},{"router_calls",2*n},{"search_calls",0},{"seconds",seconds(start)},{"threads",process_threads()}});return 0;
 }
 auto idx=load_nsg(c["index"]);require(idx->d==d&&idx->ntotal==c["base_n"]&&idx->metric_type==0,"dataset identity");
 Fvecs base(c["base"]);require(base.n==idx->ntotal&&base.d==d,"base shape");std::vector<float> vec(d);for(size_t j=0;j<16;++j){size_t id=j*(base.n/16);idx->storage->reconstruct(id,vec.data());require(!memcmp(vec.data(),base.row(id),4*d),"base/NSG bytes");}
 Engine engine(*idx);auto load_seconds=seconds(start);std::set<int> hubs(router.ids.begin(),router.ids.end());
 if(mode=="labels"){
  auto cached=read_raw<int32_t>(c["routes"].get<std::string>());require(cached.size()==3*n,"route cache shape");auto gt=read_raw<int64_t>(c["gt"].get<std::string>());require(gt.size()==100*n,"GT100 shape");auto srcrows=read_raw<int64_t>(c["row_ids"].get<std::string>());require(srcrows.size()==n,"source rows");
  auto candidate_document=read_json(c["candidates"].get<std::string>());std::map<int,std::vector<int>> candidates;for(auto a:candidate_document["slots"]){int h=a["old_id"];require(hubs.count(h),"known slot");for(int e:a["candidates"]){require(!hubs.count(e)&&e>=0&&e<idx->ntotal,"H outside");candidates[h].push_back(e);}}
  std::vector<int32_t> meta,all_entries,all_ids;std::vector<float>all_dist;std::vector<uint16_t>hits;std::vector<uint64_t>ndc;std::vector<double>times;size_t parity=0;
  for(size_t i=0;i<n;++i){auto query=q.data()+i*d;router.counting(false);auto original=router.route(query);require(!memcmp(original.data(),cached.data()+3*i,12),"actual route restoration");std::vector<Action> actions{{-1,-1,original}};
   for(int h:original)for(int e:candidates[h]){auto a=original;*std::find(a.begin(),a.end(),h)=e;std::sort(a.begin(),a.end());actions.push_back({h,e,a});}
   size_t m=actions.size();std::vector<std::array<faiss::idx_t,100>> reference(m);std::vector<std::array<float,100>> distances(m);std::vector<std::array<double,2>> timing(m);std::array<faiss::idx_t,100>I;std::array<float,100>D;
   for(int rep=0;rep<2;++rep)for(size_t z=0;z<m;++z){size_t a=rep==0?(z+i)%m:(i+m-1-z)%m;auto t=Clock::now();engine.search(query,actions[a].entries,128,100,I.data(),D.data());timing[a][rep]=seconds(t);
    if(rep==0){reference[a]=I;distances[a]=D;}else require(I==reference[a]&&!memcmp(D.data(),distances[a].data(),400),"label plain repeat");}
   std::set<int64_t> truth(gt.begin()+i*100,gt.begin()+(i+1)*100);require(truth.size()==100,"GT unique");
   for(size_t a=0;a<m;++a){engine.search(query,actions[a].entries,128,100,I.data(),D.data(),true);require(I==reference[a]&&!memcmp(D.data(),distances[a].data(),400),"label count parity");uint64_t work=engine.count.count;
    if(i%std::max<size_t>(1,n/16)==0&&parity<32&&a<2){std::array<faiss::idx_t,100>oldI;std::array<float,100>oldD;engine.search(query,actions[a].entries,128,100,oldI.data(),oldD.data(),true,true);require(oldI==I&&!memcmp(oldD.data(),D.data(),400)&&engine.count.count==work,"linked E99 parity");engine.search(query,actions[a].entries,128,1,oldI.data(),oldD.data(),true);require(oldI[0]==I[0]&&!memcmp(oldD.data(),D.data(),4)&&engine.count.count==work,"actual K1 prefix parity");++parity;}
    meta.insert(meta.end(),{int(i),actions[a].old_id,actions[a].new_id,int(srcrows[i]%2)});all_entries.insert(all_entries.end(),actions[a].entries.begin(),actions[a].entries.end());for(auto x:I)all_ids.push_back(x);all_dist.insert(all_dist.end(),D.begin(),D.end());uint16_t hit=0;for(auto x:I)hit+=truth.count(x);hits.push_back(I[0]==gt[i*100]);hits.push_back(hit);ndc.push_back(work);times.push_back(timing[a][0]);times.push_back(timing[a][1]);
   }
   if(i%128==0){resources(out);require(engine.calls<=c["max_search_calls"].get<uint64_t>()&&seconds(start)<c["seconds_cap"].get<double>(),"runtime budget");json p={{"query",i},{"n",n},{"actions",ndc.size()},{"search_calls",engine.calls},{"seconds",seconds(start)}};write_json(out/"progress.json",p);std::cout<<p.dump()<<std::endl;}
  }
  write_raw(out/"meta.i32",meta);write_raw(out/"entries.i32",all_entries);write_raw(out/"ids.i32",all_ids);write_raw(out/"distances.f32",all_dist);write_raw(out/"hits.u16",hits);write_raw(out/"ndc.u64",ndc);write_raw(out/"seconds.f64",times);
  write_json(out/"complete.json",{{"status","PASS"},{"n",n},{"actions",ndc.size()},{"search_calls",engine.calls},{"linked_E99_and_actual_K1_checks",parity},{"plain_repeat_count_bit_parity",true},{"seconds",seconds(start)},{"load_seconds",load_seconds},{"threads",process_threads()}});return 0;
 }
 require(mode=="evaluate","known mode");std::vector<std::string>names;std::vector<std::vector<std::pair<int,int>>>maps;
 for(auto m:c["models"]){names.push_back(m["name"]);std::vector<std::pair<int,int>> edits;std::set<int>old,newids;for(auto a:m["edits"]){int h=a[0],e=a[1];require(hubs.count(h)&&!hubs.count(e)&&old.insert(h).second&&newids.insert(e).second,"mapping identities");edits.emplace_back(h,e);}std::sort(edits.begin(),edits.end());maps.push_back(edits);}
 json timing=json::array();int ordinal=0,reps=c["repeats"];uint64_t smoke_calls=0;std::ifstream bf("/proc/sys/kernel/random/boot_id");std::string boot;std::getline(bf,boot);
 for(auto pt:c["points"]){int K=pt["K"],L=pt["L"];require((K==1||K==100)&&L>=K,"metric contract");size_t M=names.size();std::vector<std::unique_ptr<Batch>>reference(M);std::vector<std::vector<double>>wall(M);
  auto run=[&](size_t m,Batch&b,bool count){router.counting(count);std::array<faiss::idx_t,100>I;for(size_t i=0;i<n;++i){auto query=q.data()+i*d;auto old=router.route(query);auto e=maps[m].empty()?old:remap(old,maps[m]);std::copy(e.begin(),e.end(),b.entries.begin()+3*i);engine.search(query,e,L,K,I.data(),b.dist.data()+K*i,count);for(int j=0;j<K;++j)b.ids[i*K+j]=I[j];if(count){b.graph_ndc[i]=engine.count.count;b.route_ndc[i]=router.counter.n;}}};
  for(int rep=0;rep<reps;++rep)for(size_t z=0;z<M;++z){size_t m=(z+rep+ordinal+c.value("dataset_order",0))%M;Batch b(n,K);if(rep==0){reference[m]=std::make_unique<Batch>(n,K);run(m,*reference[m],false);}threads();auto t=Clock::now();run(m,b,false);double sec=seconds(t);same(*reference[m],b);if(rep==0)save_batch(out/(names[m]+"_K"+std::to_string(K)+"_L"+std::to_string(L)),b,false);wall[m].push_back(sec);json p={{"method",names[m]},{"K",K},{"L",L},{"repeat",rep},{"seconds",sec},{"qps",n/sec},{"threads",process_threads()},{"boot_id",boot},{"search_calls",engine.calls}};timing.push_back(p);write_json(out/"timing.json",timing);std::cout<<p.dump()<<std::endl;}
  for(size_t m=0;m<M;++m){Batch b(n,K);run(m,b,true);same(*reference[m],b);auto path=out/(names[m]+"_K"+std::to_string(K)+"_L"+std::to_string(L));save_batch(path,b,true);
   if(m==0&&c.contains("audit_reference")){auto old=fs::path(c["audit_reference"].get<std::string>())/("k"+std::to_string(K))/(router.method+"_L"+std::to_string(L));auto I=read_raw<int32_t>(old/"ids.i32"),E=read_raw<int32_t>(old/"entry_ids.i32");auto D=read_raw<float>(old/"distances.f32");auto N=read_raw<uint64_t>(old/"graph_ndc.u64"),R=read_raw<uint64_t>(old/"route_ndc.u64");require(I==b.ids&&E==b.entries&&D.size()==b.dist.size()&&!memcmp(D.data(),b.dist.data(),D.size()*4)&&N==b.graph_ndc&&R==b.route_ndc,"E105 full baseline recovery");}
   for(size_t i=0;i<std::min<size_t>(16,n);++i){std::array<int32_t,3>e;std::copy(b.entries.begin()+3*i,b.entries.begin()+3*i+3,e.begin());std::array<faiss::idx_t,100>I;std::array<float,100>D;engine.search(q.data()+i*d,e,L,K,I.data(),D.data(),true,true);for(int j=0;j<K;++j)require(I[j]==b.ids[i*K+j],"audit linked IDs");require(!memcmp(D.data(),b.dist.data()+i*K,K*4)&&engine.count.count==b.graph_ndc[i],"audit linked bits/count");++smoke_calls;}
   write_json(path/"complete.json",{{"status","PASS"},{"method",names[m]},{"n",n},{"K",K},{"L",L},{"seconds",wall[m]},{"threads",1},{"warm_plain_count_bit_parity",true}});
  }++ordinal;resources(out);require(engine.calls<=c["max_search_calls"].get<uint64_t>()&&seconds(start)<c["seconds_cap"].get<double>(),"budget");
 }
 threads();write_json(out/"complete.json",{{"status","PASS"},{"points",ordinal*names.size()},{"wall_rounds",timing.size()},{"search_calls",engine.calls},{"smoke_calls",smoke_calls},{"seconds",seconds(start)},{"load_seconds",load_seconds},{"threads",process_threads()},{"baseline_recovered",true},{"graph_builds",0}});return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

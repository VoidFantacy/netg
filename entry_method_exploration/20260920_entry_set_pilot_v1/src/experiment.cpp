#define main inherited_main_unused
#include "common/evaluate.cpp"
#undef main
#include "kernels.hpp"

struct ActualCount:CountDC{
 explicit ActualCount(faiss::DistanceComputer*p):CountDC(p){}
 void distances_batch_4(faiss::idx_t a,faiss::idx_t b,faiss::idx_t c,faiss::idx_t d,float&x,float&y,float&z,float&w)override{
  for(auto id:{a,b,c,d}){if(count<3)first[count]=id;++count;}dc->distances_batch_4(a,b,c,d,x,y,z,w);
 }
};
struct Ranked{std::array<int32_t,3> ids;std::array<float,3> scores;};
struct Route:Router{
 uint64_t calls=0;
 Route(const json&c,size_t d):Router(c,d,c["graph"].get<std::string>()){}
 Ranked ranked(const float*q){
  ++calls;counter.n=0;auto heap=graph->searchKnn(q,3);require(heap.size()==3,"three candidates");
  std::array<std::pair<float,int32_t>,3> z;for(auto&v:z){v={heap.top().first,heap.top().second};heap.pop();}std::sort(z.begin(),z.end());
  Ranked r;for(int j=0;j<3;++j){r.ids[j]=z[j].second;r.scores[j]=1-z[j].first;}return r;
 }
 std::array<int32_t,3> original(const float*q){++calls;return Router::route(q);}
};
struct Node{int feature=-1,left=-1,right=-1,action=0;double threshold=0;};
struct Method{
 std::string name;int action=0;bool feature=false;std::vector<Node> nodes;
 explicit Method(const json&j):name(j["name"]),action(j.value("action",0)),feature(j.value("features",false)){
  if(j.contains("tree")){feature=true;for(auto n:j["tree"]){Node x;x.feature=n.value("feature",-1);x.action=n.value("action",0);x.threshold=n.value("threshold",0.0);x.left=n.value("left",-1);x.right=n.value("right",-1);nodes.push_back(x);}}
 }
 int select(const std::array<double,6>&x)const{if(nodes.empty())return action;int j=0;for(int depth=0;depth<3;++depth){const auto&n=nodes.at(j);if(n.feature<0)return n.action;j=x[n.feature]<=n.threshold?n.left:n.right;}throw std::runtime_error("tree too deep");}
};
struct Engine{
 acsg::IndexACSGFlat&idx;Route&router;std::vector<uint8_t>spans;ResearchKernel kernel;std::unique_ptr<faiss::DistanceComputer>plain,featuredc;ActualCount count;faiss::VisitedTable vt;std::vector<acsg::EnterPoint>ep;std::vector<acsg::Neighbor>legacy;
 uint64_t calls=0,feature_calls=0;std::array<int32_t,3>last_entries;int last_action=0;std::array<double,6>last_features{};
 Engine(acsg::IndexACSGFlat&i,Route&r):idx(i),router(r),spans(make_spans(*i.acsg.final_graph,i.ntotal)),kernel(*i.acsg.final_graph,spans,i.ntotal),plain(acsg::storage_distance_computer(i.storage)),featuredc(acsg::storage_distance_computer(i.storage)),count(acsg::storage_distance_computer(i.storage)),vt(i.ntotal){ep.reserve(3);legacy.reserve(1501);}
 std::array<double,6> features(const float*q,const Ranked&r,std::array<float,3>*raw=nullptr){
  featuredc->set_query(q);std::array<float,3>b;double ps=0,bs=0;
  for(int j=0;j<3;++j){b[j]=-(*featuredc)(r.ids[j]);ps+=double(r.scores[j])*r.scores[j];bs+=double(b[j])*b[j];}feature_calls+=3;
  ps=std::sqrt(ps)+1e-12;bs=std::sqrt(bs)+1e-12;int best=0;for(int j=1;j<3;++j)if(b[j]>b[best]||(b[j]==b[best]&&r.ids[j]<r.ids[best]))best=j;
  if(raw)*raw=b;return {(double(r.scores[0])-r.scores[1])/ps,(double(r.scores[1])-r.scores[2])/ps,(double(b[0])-b[1])/bs,(double(b[0])-b[2])/bs,(double(b[1])-b[2])/bs,double(best)};
 }
 void search(const float*q,const std::array<int32_t,3>&e,int K,int L,faiss::idx_t*I,float*D,bool counting,bool original=false){
  ep.clear();int last=-1;for(int h:e)if(h>=0){require(h>last&&h<idx.ntotal,"valid ordered entries");ep.emplace_back(h,1);last=h;}require(ep.size()==1||ep.size()==3,"one or three entries");
  vt.advance();auto&dis=counting?static_cast<faiss::DistanceComputer&>(count):*plain;dis.set_query(q);
  if(original){idx.acsg.search_L=L;idx.acsg.search_new(dis,K,I,D,vt,2,ep,&legacy);}else kernel.search<true,false,true>(dis,vt,ep,L,K,I,D);++calls;
  if(counting)for(size_t j=0;j<ep.size();++j)require(count.first[j]==ep[j].id,"actual entry consumption");
 }
 void once(const float*q,const Method&m,int K,int L,faiss::idx_t*I,float*D,bool counting){
  if(!m.feature&&m.nodes.empty()&&m.action==0){last_entries=router.original(q);last_action=0;}
  else{auto r=router.ranked(q);if(m.feature)last_features=features(q,r);last_action=m.select(last_features);require(last_action>=0&&last_action<4,"valid action");last_entries={-1,-1,-1};if(last_action==0){last_entries=r.ids;std::sort(last_entries.begin(),last_entries.end());}else last_entries[0]=r.ids[last_action-1];}
  search(q,last_entries,K,L,I,D,counting);
 }
};
int main(int argc,char**argv){try{
 require(argc==3,"experiment config new_output");threads();auto c=read_json(argv[1]);require(c["threads"]==1,"threads config");fs::path out=argv[2];require(!fs::exists(out),"preserve output");fs::create_directories(out);write_json(out/"config.json",c);auto start=Clock::now();
 size_t n=c["n"],d=c["dimension"];auto q=read_raw<float>(c["queries"].get<std::string>());require(q.size()==n*d,"query dimensions");for(float x:q)require(std::isfinite(x),"finite input");
 Route router(c["anchor"],d);auto idx=load_nsg(c["index"]);require(idx->d==d&&idx->ntotal==c["base_n"]&&idx->metric_type==0,"data identity");Fvecs base(c["base"]);require(base.d==d&&base.n==idx->ntotal,"base dimensions");std::vector<float>v(d);for(size_t j=0;j<16;++j){size_t id=j*(base.n/16);idx->storage->reconstruct(id,v.data());require(!memcmp(v.data(),base.row(id),4*d),"base bytes");}
 Engine e(*idx,router);std::array<faiss::idx_t,100>I;std::array<float,100>D;std::string mode=c["mode"];uint64_t parity=0;auto guard=[&](){resources(out);require(e.calls<=c["max_search_calls"].get<uint64_t>()&&seconds(start)<c["seconds_cap"].get<double>(),"runtime budget");};
 if(mode=="labels"){
  std::vector<int32_t>ranked(n*3);std::vector<float>profile(n*3),raw(n*3);std::vector<double>x(n*6);router.counting(false);
  for(size_t i=0;i<n;++i){auto r=router.ranked(q.data()+i*d);std::array<float,3>b;auto f=e.features(q.data()+i*d,r,&b);std::copy(r.ids.begin(),r.ids.end(),ranked.begin()+3*i);std::copy(r.scores.begin(),r.scores.end(),profile.begin()+3*i);std::copy(b.begin(),b.end(),raw.begin()+3*i);std::copy(f.begin(),f.end(),x.begin()+6*i);
   auto old=router.original(q.data()+i*d);auto sorted=r.ids;std::sort(sorted.begin(),sorted.end());require(old==sorted,"ranked/original membership");}
  auto previous=read_raw<int32_t>(c["route_reference"].get<std::string>());require(previous.size()==3*n,"previous route size");for(size_t i=0;i<n;++i){std::array<int32_t,3>a;std::copy(ranked.begin()+3*i,ranked.begin()+3*i+3,a.begin());std::sort(a.begin(),a.end());require(!memcmp(a.data(),previous.data()+3*i,12),"E116 route restoration");}
  write_raw(out/"ranked_entries.i32",ranked);write_raw(out/"profile_scores.f32",profile);write_raw(out/"base_scores.f32",raw);write_raw(out/"features.f64",x);
  std::vector<Method>methods;methods.emplace_back(json{{"name","GT10"},{"action",0}});for(int a=0;a<4;++a)methods.emplace_back(json{{"name","action"+std::to_string(a)},{"action",a},{"features",true}});
  std::vector<std::unique_ptr<Batch>>ref;for(int j=0;j<5;++j)ref.push_back(std::make_unique<Batch>(n,100));int reps=c["label_repeats"],block=c["label_block_size"];std::vector<double>t(n*5*reps);json schedule=json::array();
  for(int rep=0;rep<reps;++rep)for(size_t lo=0;lo<n;lo+=block){size_t hi=std::min(n,lo+block);for(int z=0;z<5;++z){int a=(z+rep+int(lo/block))%5;auto bt=Clock::now();for(size_t i=lo;i<hi;++i){auto begin=Clock::now();e.once(q.data()+i*d,methods[a],100,128,I.data(),D.data(),false);t[(i*5+a)*reps+rep]=seconds(begin);
    if(rep==0){for(int k=0;k<100;++k)ref[a]->ids[i*100+k]=I[k];std::copy(D.begin(),D.end(),ref[a]->dist.begin()+i*100);std::copy(e.last_entries.begin(),e.last_entries.end(),ref[a]->entries.begin()+3*i);}else{for(int k=0;k<100;++k)require(ref[a]->ids[i*100+k]==I[k],"label repeat IDs");require(!memcmp(ref[a]->dist.data()+100*i,D.data(),400),"label repeat distance bits");}}
   schedule.push_back({{"rep",rep},{"block_start",lo},{"block_end",hi},{"variant",a},{"seconds",seconds(bt)}});}
   guard();write_json(out/"progress.json",{{"rep",rep},{"queries",hi},{"search_calls",e.calls},{"router_calls",router.calls},{"seconds",seconds(start)}});
  }
  router.counting(true);for(int a=0;a<5;++a){Batch b(n,100);for(size_t i=0;i<n;++i){e.once(q.data()+i*d,methods[a],100,128,I.data(),D.data(),true);for(int k=0;k<100;++k)b.ids[i*100+k]=I[k];std::copy(D.begin(),D.end(),b.dist.begin()+i*100);std::copy(e.last_entries.begin(),e.last_entries.end(),b.entries.begin()+3*i);b.graph_ndc[i]=e.count.count;b.route_ndc[i]=router.counter.n;
    if(i%625==0&&a!=1){std::array<faiss::idx_t,100>oldI;std::array<float,100>oldD;e.search(q.data()+i*d,e.last_entries,100,128,oldI.data(),oldD.data(),true,true);require(I==oldI&&!memcmp(D.data(),oldD.data(),400)&&e.count.count==b.graph_ndc[i],"linked E99 parity");e.search(q.data()+i*d,e.last_entries,1,128,oldI.data(),oldD.data(),true);require(I[0]==oldI[0]&&!memcmp(D.data(),oldD.data(),4)&&e.count.count==b.graph_ndc[i],"K1 prefix parity");++parity;}}
   same(*ref[a],b);if(a==1)same(*ref[0],b);auto p=out/("variant"+std::to_string(a));save_batch(p,b,false);save_batch(p,b,true);}
  write_raw(out/"seconds.f64",t);write_json(out/"timing_schedule.json",schedule);
 }else{
  require(mode=="evaluate","known mode");std::vector<Method>methods;for(auto m:c["methods"])methods.emplace_back(m);json timings=json::array();int ordinal=0;std::ifstream bf("/proc/sys/kernel/random/boot_id");std::string boot;std::getline(bf,boot);
  std::vector<int32_t>ranking(n*3);std::vector<float>ps(n*3),bs(n*3);std::vector<double>xx(n*6);router.counting(false);
  for(size_t i=0;i<n;++i){auto r=router.ranked(q.data()+i*d);std::array<float,3>b;auto f=e.features(q.data()+i*d,r,&b);std::copy(r.ids.begin(),r.ids.end(),ranking.begin()+3*i);std::copy(r.scores.begin(),r.scores.end(),ps.begin()+3*i);std::copy(b.begin(),b.end(),bs.begin()+3*i);std::copy(f.begin(),f.end(),xx.begin()+6*i);auto sorted=r.ids;std::sort(sorted.begin(),sorted.end());require(sorted==router.original(q.data()+i*d),"accept ranked/original membership");}
  write_raw(out/"ranked_entries.i32",ranking);write_raw(out/"profile_scores.f32",ps);write_raw(out/"base_scores.f32",bs);write_raw(out/"features.f64",xx);
  for(auto pt:c["points"]){int K=pt["K"],L=pt["L"];require((K==1||K==100)&&L>=K,"metric contract");std::vector<std::unique_ptr<Batch>>ref(methods.size());std::vector<std::vector<double>>wall(methods.size());std::vector<std::vector<int32_t>>actions(methods.size());
   auto run=[&](int a,Batch&b,bool count,std::vector<int32_t>&choices){router.counting(count);choices.resize(n);for(size_t i=0;i<n;++i){e.once(q.data()+i*d,methods[a],K,L,I.data(),b.dist.data()+i*K,count);for(int k=0;k<K;++k)b.ids[i*K+k]=I[k];std::copy(e.last_entries.begin(),e.last_entries.end(),b.entries.begin()+3*i);choices[i]=e.last_action;if(count){b.graph_ndc[i]=e.count.count;b.route_ndc[i]=router.counter.n;}}};
   for(int rep=0;rep<c["repeats"].get<int>();++rep)for(size_t z=0;z<methods.size();++z){int a=(z+rep+ordinal+c.value("dataset_order",0))%methods.size();if(rep==0){ref[a]=std::make_unique<Batch>(n,K);run(a,*ref[a],false,actions[a]);}Batch b(n,K);std::vector<int32_t>choices;threads();auto begin=Clock::now();run(a,b,false,choices);double sec=seconds(begin);same(*ref[a],b);require(choices==actions[a],"repeat actions");wall[a].push_back(sec);timings.push_back({{"method",methods[a].name},{"K",K},{"L",L},{"repeat",rep},{"seconds",sec},{"qps",n/sec},{"threads",process_threads()},{"boot_id",boot}});write_json(out/"timing.json",timings);write_json(out/"progress.json",{{"method",methods[a].name},{"K",K},{"L",L},{"repeat",rep},{"search_calls",e.calls},{"seconds",seconds(start)}});guard();}
   for(size_t a=0;a<methods.size();++a){Batch b(n,K);std::vector<int32_t>choices;run(a,b,true,choices);same(*ref[a],b);require(choices==actions[a],"count actions");auto p=out/(methods[a].name+"_K"+std::to_string(K)+"_L"+std::to_string(L));save_batch(p,b,false);save_batch(p,b,true);write_raw(p/"actions.i32",choices);std::vector<uint64_t>fn(n,methods[a].feature?3:0);write_raw(p/"feature_ndc.u64",fn);
    for(size_t i=0;i<std::min<size_t>(32,n);++i){std::array<int32_t,3>entry;std::copy(b.entries.begin()+3*i,b.entries.begin()+3*i+3,entry.begin());e.search(q.data()+i*d,entry,K,L,I.data(),D.data(),true,true);for(int k=0;k<K;++k)require(I[k]==b.ids[i*K+k],"accept linked IDs");require(!memcmp(D.data(),b.dist.data()+i*K,4*K)&&e.count.count==b.graph_ndc[i],"accept linked bits/count");++parity;}
    write_json(p/"complete.json",{{"status","PASS"},{"n",n},{"K",K},{"L",L},{"method",methods[a].name},{"seconds",wall[a]},{"threads",1},{"warm_plain_count_bit_parity",true}});
   }++ordinal;guard();
  }
 }
 guard();threads();write_json(out/"complete.json",{{"status","PASS"},{"n",n},{"mode",mode},{"seconds",seconds(start)},{"search_calls",e.calls},{"router_calls",router.calls},{"feature_distance_calls",e.feature_calls},{"linked_parity_queries",parity},{"threads",process_threads()}});return 0;
 }catch(const std::exception&x){std::cerr<<x.what()<<std::endl;return 1;}}

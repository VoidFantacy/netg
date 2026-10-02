#include "base_engine.hpp"
#include <iomanip>

struct SeenRank {Ranked rank;hnswlib::tableint upper=~hnswlib::tableint(0);};
struct ObservedRoute:Route {
 explicit ObservedRoute(const json&c,size_t d):Route(c,d){}
 SeenRank detailed(const float*q,bool observe){
  ++calls;counter.n=0;SeenRank r;
  auto heap=observe?graph->searchKnnObserved(q,3,r.upper):graph->searchKnn(q,3);
  require(heap.size()==3,"rank heap shape");std::array<std::pair<float,int32_t>,3> pairs;
  for(auto&v:pairs){v={heap.top().first,int32_t(heap.top().second)};heap.pop();}
  std::sort(pairs.begin(),pairs.end());
  for(int j=0;j<3;++j){r.rank.ids[j]=pairs[j].second;r.rank.scores[j]=1-pairs[j].first;}
  if(observe)require(r.upper<ids.size()&&graph->element_levels_[r.upper]>0,"upper node");
  return r;
 }
};
struct Rule {
 int kind=0,constant=0;std::vector<uint8_t>table;std::vector<Node>nodes;
 int tree(const std::array<double,6>&x)const{
  int j=0;for(int depth=0;depth<=2;++depth){const auto& n=nodes.at(j);if(n.feature<0)return n.action;j=x[n.feature]<=n.threshold?n.left:n.right;}
  throw std::runtime_error("tree depth contract");
 }
};
Rule fixed_state(size_t h,int action){Rule r;r.kind=2;r.table.assign(h,uint8_t(action));return r;}
Rule parse_rule(const std::string&name,const json&j,size_t h){
 Rule r;
 if(name=="GlobalPareto"){r.kind=1;r.constant=j["action"];}
 else if(name=="FeaturePareto"){
  r.kind=3;for(auto v:j["nodes"]){Node x;x.feature=v.value("feature",-1);x.action=v.value("action",0);x.left=v.value("left",-1);x.right=v.value("right",-1);x.threshold=v.value("threshold",0.);r.nodes.push_back(x);}
 }else{r.kind=2;for(int x:j["table"]){require(x>=0&&x<4,"table action bounds");r.table.push_back(uint8_t(x));}require(r.table.size()==h,"table H binding");}
 return r;
}

int main(int argc,char**argv){try{
 require(argc==4,"measure native_config mode new_output");threads();json c=read_json(argv[1]);std::string mode=argv[2];fs::path out=argv[3];
 require(mode=="gate"||mode=="labels"||mode=="wall","mode");require(!fs::exists(out),"preserve output");fs::create_directories(out);write_json(out/"config.json",c);
 auto started=Clock::now();size_t n=c["n"],d=c["dimension"],H=c["H"];require(n==4096,"fixed query count");
 auto q=read_raw<float>(c["queries"].get<std::string>());auto folds=read_raw<int32_t>(c["folds"].get<std::string>());
 auto old_rank=read_raw<int32_t>(c["ranked_reference"].get<std::string>());auto old_z=read_raw<int32_t>(c["state_reference"].get<std::string>());
 auto old_features=read_raw<double>(c["feature_reference"].get<std::string>());auto old_scores=read_raw<float>(c["profile_reference"].get<std::string>());
 require(q.size()==n*d&&folds.size()==n&&old_rank.size()==n*3&&old_z.size()==n&&old_features.size()==n*6&&old_scores.size()==n*3,"input shape");
 for(float v:q)require(std::isfinite(v),"finite query");for(int f:folds)require(f>=0&&f<4,"fold bounds");
 ObservedRoute router(c["anchor"],d);require(router.ids.size()==H,"hub count");auto idx=load_nsg(c["index"]);
 require(idx->d==int(d)&&idx->ntotal==c["base_n"].get<int64_t>()&&idx->metric_type==0,"fixed base graph metric");
 Fvecs base(c["base"]);std::vector<float> rv(d);for(size_t j=0;j<16;++j){size_t id=j*(base.n/16);idx->storage->reconstruct(id,rv.data());require(!memcmp(rv.data(),base.row(id),4*d),"base embedded bytes");}
 Engine engine(*idx,router);std::array<faiss::idx_t,100>I,legacy;std::array<float,100>D,legacyD;
 uint64_t smoke_calls=0;json timing=json::array();auto guard=[&](){
  threads();struct statvfs v;require(!statvfs(out.c_str(),&v),"statvfs");require(uint64_t(v.f_bavail)*v.f_frsize>=c["min_free_bytes"].get<uint64_t>(),"disk reserve");
  struct rusage u;getrusage(RUSAGE_SELF,&u);require(uint64_t(u.ru_maxrss)*1024<=c["maxrss_bytes"].get<uint64_t>(),"RSS cap");
  require(engine.calls<=c["max_search_calls"].get<uint64_t>()&&seconds(started)<=c["seconds_cap"].get<double>(),"job budget");
 };
 auto once=[&](const float*query,const Rule&rule,int K,int L,Batch&b,size_t i,int& action,bool counting){
  std::array<int32_t,3> entries{-1,-1,-1};action=0;
  if(rule.kind==0||(rule.kind==1&&rule.constant==0)){entries=router.original(query);}
  else{
   auto r=router.detailed(query,rule.kind==2);
   if(rule.kind==1)action=rule.constant;
   else if(rule.kind==2)action=rule.table[r.upper];
   else action=rule.tree(engine.features(query,r.rank));
   require(action>=0&&action<4,"legal action");
   if(action==0){entries=r.rank.ids;std::sort(entries.begin(),entries.end());}else entries[0]=r.rank.ids[action-1];
  }
  std::copy(entries.begin(),entries.end(),b.entries.begin()+3*i);
  engine.search(query,entries,K,L,I.data(),b.dist.data()+i*K,counting);
  for(int j=0;j<K;++j)b.ids[i*K+j]=I[j];
 };
 if(mode=="gate"){
  router.counting(true);
  for(size_t i=0;i<n;++i){
   const float*query=q.data()+i*d;router.counter.n=0;++router.calls;auto a=router.graph->searchKnn(query,3);uint64_t ndc=router.counter.n;
   hnswlib::tableint z=~hnswlib::tableint(0);router.counter.n=0;++router.calls;auto b=router.graph->searchKnnObserved(query,3,z);
   require(a.size()==3&&b.size()==3&&router.counter.n==ndc&&int32_t(z)==old_z[i],"full observed native parity");
   std::array<std::pair<float,int32_t>,3> p;for(auto&v:p){auto x=a.top(),y=b.top();a.pop();b.pop();require(x.second==y.second&&!memcmp(&x.first,&y.first,4),"heap bits");v={x.first,int32_t(x.second)};}
   std::sort(p.begin(),p.end());Ranked r;for(int j=0;j<3;++j){r.ids[j]=p[j].second;r.scores[j]=1-p[j].first;}
   require(!memcmp(r.ids.data(),old_rank.data()+3*i,12)&&!memcmp(r.scores.data(),old_scores.data()+3*i,12),"E117 ranking and score restoration");
   auto f=engine.features(query,r);require(!memcmp(f.data(),old_features.data()+6*i,48),"E117 six feature bits");
  }
  write_json(out/"observer_parity.json",{{"status","PASS"},{"n",n},{"heap_bits",true},{"NDC",true},{"states",true},{"ranked_ID_and_profile_score_bits",true},{"six_feature_bits",true}});
  router.counting(false);
 }
 std::array<Rule,4> forced;for(int a=0;a<4;++a)forced[a]=fixed_state(H,a);Rule baseline;
 std::array<std::array<std::array<Rule,6>,2>,4> policies;json models;
 if(mode=="wall"){
  models=read_json(fs::path(c["root"].get<std::string>())/"models"/c["dataset"].get<std::string>()/"models.json");
  require(models["H"]==H&&models["n"]==n&&models["folds"].size()==4,"frozen model contract");
  std::array<std::string,4> learned={"StatePareto","GlobalPareto","ShufflePareto","FeaturePareto"};
  for(int f=0;f<4;++f)for(int k=0;k<2;++k){policies[f][k][0]=baseline;policies[f][k][1]=forced[0];
   std::string K=k==0?"1":"100";for(int m=0;m<4;++m)policies[f][k][m+2]=parse_rule(learned[m],models["folds"][f]["K"][K][learned[m]],H);
  }
 }
 int ordinal=0;
 for(auto pt:c["points"]){
  int K=pt["K"],L=pt["L"];require((K==1||K==100)&&L>=K&&L<=1250,"K L contract");int ki=K==1?0:1;auto point=out/("k"+std::to_string(K)+"_L"+std::to_string(L));fs::create_directories(point);
  if(mode=="gate"){
   for(int a=0;a<4;++a)for(size_t i=0;i<16;++i){
    Batch plain(1,K),counted(1,K);int ac;router.counting(false);once(q.data()+i*d,forced[a],K,L,plain,0,ac,false);
    router.counting(true);once(q.data()+i*d,forced[a],K,L,counted,0,ac,true);same(plain,counted);uint64_t ndc=engine.count.count;
    std::array<int32_t,3> entries;std::copy(counted.entries.begin(),counted.entries.end(),entries.begin());
    engine.search(q.data()+i*d,entries,K,L,legacy.data(),legacyD.data(),true,true);
    for(int j=0;j<K;++j)require(legacy[j]==plain.ids[j],"E99 return ID parity");require(!memcmp(legacyD.data(),plain.dist.data(),4*K)&&engine.count.count==ndc,"E99 distance/NDC parity");smoke_calls+=3;
   }
   router.counting(false);std::unique_ptr<Batch> reference;std::array<std::string,2>names={"Default","ForcedDefault"};
   for(int rep=0;rep<3;++rep)for(int offset=0;offset<2;++offset){int m=(ordinal+rep+offset)%2;const Rule&r=m==0?baseline:forced[0];
    if(rep==0){Batch warm(128,K);for(size_t i=0;i<128;++i){int a;once(q.data()+i*d,r,K,L,warm,i,a,false);}}
    Batch b(n,K);threads();auto start=Clock::now();for(size_t i=0;i<n;++i){int a;once(q.data()+i*d,r,K,L,b,i,a,false);}double elapsed=seconds(start);threads();
    if(!reference)reference=std::make_unique<Batch>(b);else same(*reference,b);
    json row={{"method",names[m]},{"K",K},{"L",L},{"repeat",rep},{"n",n},{"seconds",elapsed},{"qps",n/elapsed},{"threads",1}};timing.push_back(row);write_json(out/"timings.json",timing);std::cout<<row.dump()<<std::endl;guard();
   }
   save_batch(point/"reference",*reference,false);write_json(point/"complete.json",{{"status","PASS"},{"all_six_full_wall_outputs_identical",true},{"n",n},{"K",K},{"L",L}});
  }else if(mode=="labels"){
   router.counting(false);std::array<std::unique_ptr<Batch>,4>ref;for(auto&p:ref)p=std::make_unique<Batch>(n,K);Batch temporary(n,K);std::vector<double>t(n*4*3);
   for(int rep=0;rep<3;++rep)for(size_t lo=0;lo<n;lo+=128){size_t hi=std::min(n,lo+128);
    for(int offset=0;offset<4;++offset){int a=(offset+rep+int(lo/128)+ordinal)%4;
     for(size_t i=lo;i<hi;++i){int chosen;Batch& b=rep==0?*ref[a]:temporary;auto start=Clock::now();
      once(q.data()+i*d,forced[a],K,L,b,i,chosen,false);t[(i*4+a)*3+rep]=seconds(start);
      if(rep>0)require(std::equal(b.ids.begin()+i*K,b.ids.begin()+(i+1)*K,ref[a]->ids.begin()+i*K)&&!memcmp(b.dist.data()+i*K,ref[a]->dist.data()+i*K,4*K)&&!memcmp(b.entries.data()+3*i,ref[a]->entries.data()+3*i,12),"label repeated bits");
      require(chosen==a,"forced action");
     }
    }
    write_json(out/"progress.json",{{"K",K},{"L",L},{"rep",rep},{"queries",hi},{"calls",engine.calls},{"seconds",seconds(started)}});guard();
   }
   for(int a=0;a<4;++a)save_batch(point/("action"+std::to_string(a)),*ref[a],false);
   auto gate=fs::path(c["root"].get<std::string>())/"results"/c["dataset"].get<std::string>()/"gate"/("k"+std::to_string(K)+"_L"+std::to_string(L))/"reference";
   require(ref[0]->ids==read_raw<int32_t>(gate/"ids.i32"),"label default gate restoration");auto gd=read_raw<float>(gate/"distances.f32");require(!memcmp(gd.data(),ref[0]->dist.data(),4*gd.size()),"label default distance restoration");
   write_raw(point/"seconds.f64",t);write_json(point/"complete.json",{{"status","PASS"},{"n",n},{"K",K},{"L",L},{"actions",4},{"repeats",3},{"all_repeated_output_bits",true},{"time_is_instrumented_proxy",true}});
   std::cout<<"LABELS_COMPLETE "<<K<<" "<<engine.calls<<std::endl;
  }else{
   router.counting(false);std::array<std::string,6>names={"Default","ForcedDefault","StatePareto","GlobalPareto","ShufflePareto","FeaturePareto"};
   auto lp=fs::path(c["root"].get<std::string>())/"results"/c["dataset"].get<std::string>()/"labels"/("k"+std::to_string(K)+"_L"+std::to_string(L));
   std::array<std::unique_ptr<Batch>,4>response;
   for(int a=0;a<4;++a){auto p=lp/("action"+std::to_string(a));response[a]=std::make_unique<Batch>(n,K);response[a]->ids=read_raw<int32_t>(p/"ids.i32");response[a]->dist=read_raw<float>(p/"distances.f32");response[a]->entries=read_raw<int32_t>(p/"entry_ids.i32");}
   auto expected=read_raw<int32_t>(fs::path(c["root"].get<std::string>())/"models"/c["dataset"].get<std::string>()/("expected_actions_K"+std::to_string(K)+".i32"));require(expected.size()==n*6,"OOF action matrix shape");
   for(int rep=0;rep<3;++rep)for(int offset=0;offset<6;++offset){int m=(ordinal+rep+offset)%6;
    if(rep==0){Batch warm(128,K);for(size_t i=0;i<128;++i){int a;once(q.data()+i*d,policies[folds[i]][ki][m],K,L,warm,i,a,false);}}
    Batch b(n,K);std::vector<int32_t>acts(n);threads();auto start=Clock::now();for(size_t i=0;i<n;++i)once(q.data()+i*d,policies[folds[i]][ki][m],K,L,b,i,acts[i],false);double elapsed=seconds(start);threads();
    for(size_t i=0;i<n;++i){int a=acts[i];require(a==expected[i*6+m],"online vs frozen OOF action");
     require(std::equal(b.ids.begin()+i*K,b.ids.begin()+(i+1)*K,response[a]->ids.begin()+i*K)&&!memcmp(b.dist.data()+i*K,response[a]->dist.data()+i*K,4*K)&&!memcmp(b.entries.data()+3*i,response[a]->entries.data()+3*i,12),"online output vs selected action label bits");
    }
    if(rep==0)write_raw(point/(names[m]+".actions.i32"),acts);
    json row={{"method",names[m]},{"K",K},{"L",L},{"repeat",rep},{"n",n},{"seconds",elapsed},{"qps",n/elapsed},{"threads",1},{"all_actions_and_output_bits_match",true}};timing.push_back(row);write_json(out/"timings.json",timing);std::cout<<row.dump()<<std::endl;guard();
   }
   write_json(point/"complete.json",{{"status","PASS"},{"n",n},{"K",K},{"L",L},{"methods",6},{"repeats",3},{"all_online_action_and_return_bits",true},{"actual_model_inference_in_wall",true}});
  }
  ++ordinal;guard();
 }
 struct rusage usage;getrusage(RUSAGE_SELF,&usage);guard();write_json(out/"complete.json",{{"status","PASS"},{"mode",mode},{"n",n},{"seconds",seconds(started)},
  {"new_NSG",engine.calls},{"new_ANN",router.calls},{"extra_base_feature_distances",engine.feature_calls},{"smoke_NSG",smoke_calls},{"threads",1},{"cpu",15},{"maxrss_kib",usage.ru_maxrss}});
 std::cout<<"COMPLETE "<<mode<<" NSG="<<engine.calls<<" ANN="<<router.calls<<std::endl;return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

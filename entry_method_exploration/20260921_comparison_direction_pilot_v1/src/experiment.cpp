#include "base_engine.hpp"
#include "comparison_recorder.hpp"
#include "trace_kernel.hpp"
#include <faiss/utils/distances.h>
#include <random>
#include <numeric>

static volatile double prediction_sink=0;
uint64_t mix(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
uint64_t result_hash(const faiss::idx_t*I,const float*D,int K){uint64_t h=1469598103934665603ULL;for(int k=0;k<K;++k){uint32_t b;memcpy(&b,D+k,4);h^=uint64_t(I[k]);h*=1099511628211ULL;h^=b;h*=1099511628211ULL;}return h;}
std::string bootid(){std::ifstream f("/proc/sys/kernel/random/boot_id");std::string s;std::getline(f,s);return s;}

struct Features{
 std::string kind;size_t d,m,F;std::vector<float>directions,values;
 Features(const json&j,size_t dim):kind(j["kind"]),d(dim),m(j.value("m",32)),F(kind=="raw"?d:(kind=="linear"?m:2*m)){
  require(kind=="raw"||kind=="linear"||kind=="relu","known features");
  if(kind!="raw"){directions=read_raw<float>(j["directions"].get<std::string>());require(directions.size()==m*d,"dictionary shape");for(float x:directions)require(std::isfinite(x),"finite directions");}values.resize(F);
 }
 const std::vector<float>&run(const float*q){double ss=0;for(size_t j=0;j<d;++j)ss+=double(q[j])*q[j];require(ss>0&&std::isfinite(ss),"nonzero finite norm");double norm=std::sqrt(ss);
  if(kind=="raw"){for(size_t j=0;j<d;++j)values[j]=float(q[j]/norm);}
  else for(size_t j=0;j<m;++j){float x=float(faiss::fvec_inner_product(q,directions.data()+j*d,d)/norm);if(kind=="linear")values[j]=x;else{values[j]=std::max(x,0.f);values[m+j]=std::max(-x,0.f);}}return values;
 }
};
struct Predictor{
 Features features;size_t H;std::array<std::vector<float>,2>w,b;float last_score=0;
 Predictor(const json&j,size_t d,size_t h):features(j["features"],d),H(h){for(int k=0;k<2;++k){std::string key=k==0?"1":"100";auto z=j["heads"][key];w[k]=read_raw<float>(z["weights"].get<std::string>());b[k]=read_raw<float>(z["bias"].get<std::string>());require(w[k].size()==H*features.F&&b[k].size()==H,"head shape");for(float v:w[k])require(std::isfinite(v),"finite weights");for(float v:b[k])require(std::isfinite(v),"finite biases");}}
 int choose(const float*q,int K,const std::vector<int32_t>&ids,std::vector<float>*scores=nullptr){const auto&x=features.run(q);int k=K==1?0:1,best=-1;float val=0;if(scores)scores->resize(H);
  for(size_t h=0;h<H;++h){float s=b[k][h]+faiss::fvec_inner_product(w[k].data()+h*features.F,x.data(),features.F);if(scores)(*scores)[h]=s;
   if(s>val||(best>=0&&s==val&&ids[h]<ids[best])){val=s;best=int(h);}}
  last_score=val;prediction_sink=val;return best;
 }
};
struct EvalMethod{
 std::string name,type;std::unique_ptr<Predictor>model;std::array<int,2>fixed{{-1,-1}};
 EvalMethod(const json&j,size_t d,size_t H):name(j["name"]),type(j["type"]){if(j.contains("model"))model=std::make_unique<Predictor>(read_json(j["model"].get<std::string>()),d,H);if(j.contains("fixed")){fixed[0]=j["fixed"]["1"];fixed[1]=j["fixed"]["100"];}}
};
struct Online{
 Engine&e;std::vector<int32_t>hubs;int choice=0;float score=0;uint64_t route_count=0;std::array<int32_t,3>entries;
 explicit Online(Engine&engine):e(engine),hubs(e.router.ids){}
 void run(const float*q,EvalMethod&m,int K,int L,faiss::idx_t*I,float*D,bool count){route_count=0;score=0;choice=0;entries={-1,-1,-1};
  if(m.type=="nsg"){entries[0]=e.idx.acsg.enterpoint;choice=-2;}
  else if(m.type=="fixed"&&m.fixed[K==1?0:1]>=0){int h=m.fixed[K==1?0:1];require(h<int(hubs.size()),"fixed hub range");entries[0]=hubs[h];choice=h+1;}
  else if(m.type=="single1"){auto r=e.router.ranked(q);entries[0]=r.ids[0];route_count=e.router.counter.n;auto it=std::find(hubs.begin(),hubs.end(),r.ids[0]);require(it!=hubs.end(),"rank1 real hub");choice=1+int(it-hubs.begin());}
  else{entries=e.router.original(q);route_count=e.router.counter.n;
   if(m.model){int h=m.model->choose(q,K,hubs);score=m.model->last_score;if(m.type!="feature_default"&&h>=0){entries={hubs[h],-1,-1};choice=h+1;}}
   else require(m.type=="gt10"||m.type=="fixed","known online type");
  }
  e.search(q,entries,K,L,I,D,count);
 }
};

void features_only(const json&c,const fs::path&out,const std::vector<float>&q,size_t n,size_t d){
 for(auto j:c["features"]){Features f(j,d);std::vector<float>x(n*f.F);for(size_t i=0;i<n;++i){const auto&v=f.run(q.data()+i*d);std::copy(v.begin(),v.end(),x.begin()+i*f.F);}write_raw(out/(j["name"].get<std::string>()+".features.f32"),x);}
 write_json(out/"complete.json",{{"status","PASS"},{"mode","features"},{"n",n},{"search_calls",0},{"threads",process_threads()}});
}

void predict_only(const json&c,const fs::path&out,const std::vector<float>&q,size_t n,size_t d){
 auto hubs=read_raw<int32_t>(c["hub_ids"].get<std::string>());size_t H=hubs.size();
 for(auto j:c["models"]){Predictor p(read_json(j["model"].get<std::string>()),d,H);for(int K:{1,100}){std::vector<int32_t>a(n);std::vector<float>s(n*H),row;for(size_t i=0;i<n;++i){a[i]=p.choose(q.data()+i*d,K,hubs,&row)+1;std::copy(row.begin(),row.end(),s.begin()+i*H);}auto prefix=j["name"].get<std::string>()+"_K"+std::to_string(K);write_raw(out/(prefix+".actions.i32"),a);if(c.value("save_all_scores",false))write_raw(out/(prefix+".scores.f32"),s);}}
 write_json(out/"complete.json",{{"status","PASS"},{"mode","predict"},{"n",n},{"search_calls",0},{"threads",process_threads()}});
}

void trace(const json&c,const fs::path&out,Engine&e,const std::vector<float>&q,size_t n,size_t d){
 TraceKernel tk(*e.idx.acsg.final_graph,e.spans,e.idx.ntotal);int singles=c["trace_single_actions"],samples=c["direction_samples_per_query"],A=singles+1;size_t H=e.router.ids.size();
 std::vector<int32_t>actions(n*A),ret(n*A*100),entries(n*A*3,-1);std::vector<float>dist(n*A*100),directions(n*samples*d,0);std::vector<uint64_t>ndc(n*A),keys(n*samples,0),totals(n);std::vector<uint8_t>codes(n*samples,0);std::vector<uint32_t>sizes(n,0);std::vector<float>x(d),y(d);auto start=Clock::now();
 std::array<faiss::idx_t,100>I,J;std::array<float,100>D,E;
 for(size_t i=0;i<n;++i){tk.recorder.clear();auto baseline=e.router.original(q.data()+i*d);std::vector<int>hs(H);std::iota(hs.begin(),hs.end(),0);std::sort(hs.begin(),hs.end(),[&](int a,int b){return std::make_pair(mix((i+1)*65537ULL+e.router.ids[a]),a)<std::make_pair(mix((i+1)*65537ULL+e.router.ids[b]),b);});
  for(int a=0;a<A;++a){std::array<int32_t,3>en=baseline;int h=-1;if(a){h=hs[a-1];en={e.router.ids[h],-1,-1};}actions[i*A+a]=h+1;
   e.search(q.data()+i*d,en,100,128,I.data(),D.data(),true);uint64_t dc=e.count.count;
   e.vt.advance();e.count.set_query(q.data()+i*d);tk.search<true,false,true>(e.count,e.vt,e.ep,128,100,J.data(),E.data());++e.calls;
   require(I==J&&!memcmp(D.data(),E.data(),400)&&e.count.count==dc,"trace/plain-count bit parity");
   if(i<8){e.search(q.data()+i*d,en,100,128,J.data(),E.data(),true,true);require(I==J&&!memcmp(D.data(),E.data(),400)&&e.count.count==dc,"trace linked E99 parity");}
   for(int k=0;k<100;++k){ret[(i*A+a)*100+k]=I[k];dist[(i*A+a)*100+k]=D[k];}std::copy(en.begin(),en.end(),entries.begin()+(i*A+a)*3);ndc[i*A+a]=dc;
  }
  auto pairs=tk.recorder.sorted();totals[i]=pairs.size();std::sort(pairs.begin(),pairs.end(),[&](auto a,auto b){return std::make_pair(mix(a.first^mix(i+20260921)),a.first)<std::make_pair(mix(b.first^mix(i+20260921)),b.first);});
  for(auto [key,code]:pairs){if(sizes[i]>=uint32_t(samples))break;uint32_t a=key>>32,b=uint32_t(key);e.idx.storage->reconstruct(a,x.data());e.idx.storage->reconstruct(b,y.data());double norm=0;int largest=0;for(size_t j=0;j<d;++j){double v=double(x[j])-y[j];norm+=v*v;if(std::abs(v)>std::abs(double(x[largest])-y[largest]))largest=j;}if(norm<1e-24)continue;double scale=(x[largest]<y[largest]?-1.:1.)/std::sqrt(norm);size_t ix=i*samples+sizes[i]++;keys[ix]=key;codes[ix]=code;for(size_t j=0;j<d;++j)directions[ix*d+j]=float((double(x[j])-y[j])*scale);}
  require(sizes[i]>0,"query has nonzero sampled comparisons");if((i+1)%32==0){resources(out);write_json(out/"progress.json",{{"queries",i+1},{"search_calls",e.calls},{"seconds",seconds(start)}});}
 }
 write_raw(out/"actions.i32",actions);write_raw(out/"ids.i32",ret);write_raw(out/"distances.f32",dist);write_raw(out/"entries.i32",entries);write_raw(out/"ndc.u64",ndc);write_raw(out/"pair_keys.u64",keys);write_raw(out/"pair_codes.u8",codes);write_raw(out/"sample_sizes.u32",sizes);write_raw(out/"query_pair_counts.u64",totals);write_raw(out/"sample_directions.f32",directions);
 write_json(out/"complete.json",{{"status","PASS"},{"n",n},{"actions",A},{"samples",samples},{"search_calls",e.calls},{"router_calls",e.router.calls},{"seconds",seconds(start)},{"threads",process_threads()},{"trace_bit_parity",true}});
}

void labels(const json&c,const fs::path&out,Engine&e,const std::vector<float>&q,size_t n,size_t d){
 const size_t H=e.router.ids.size(),A=H+1;int block=c["label_block"],reps=c["label_repeats"];auto gt=read_raw<int64_t>(c["gt"].get<std::string>());require(gt.size()==n*100,"GT shape");
 std::vector<std::array<int32_t,3>>routes(n);e.router.counting(false);for(size_t i=0;i<n;++i)routes[i]=e.router.original(q.data()+i*d);
 std::array<faiss::idx_t,100>I,J;std::array<float,100>D,E;auto start=Clock::now();uint64_t inherited_calls=0;json completed=json::array();
 for(size_t lo=0;lo<n;lo+=block){size_t nb=std::min<size_t>(block,n-lo);fs::path bp=out/("block_"+std::to_string(lo));
  if(fs::exists(bp/"complete.json")){auto z=read_json(bp/"complete.json");require(z["status"]=="PASS"&&z["start"]==lo&&z["n"]==nb&&z["A"]==A,"complete block identity");inherited_calls+=z["search_calls"].get<uint64_t>();completed.push_back(z);continue;}
  if(fs::exists(bp)){auto archive=out/"incomplete_attempts"/(bootid()+"_"+std::to_string(std::time(nullptr)));fs::create_directories(archive);fs::rename(bp,archive/bp.filename());}fs::create_directories(bp);
  uint64_t before=e.calls;size_t count=nb*A;std::vector<int32_t>ref(count*100),top1(count),bids(nb*100),bentries(nb*3);std::vector<float>rd(count*100),bd(nb*100);std::vector<uint64_t>ndc(count),masks(count*2),hashes(count);std::vector<uint8_t>hits1(count),hits100(count);std::vector<double>times(count*2*reps);json schedule=json::array();
  auto entry=[&](size_t qi,size_t a){return a?std::array<int32_t,3>{e.router.ids[a-1],-1,-1}:routes[qi];};
  // The full reference block remains in memory for exact checks of every repeat.
  for(size_t j=0;j<nb;++j){size_t qi=lo+j;std::unordered_map<int64_t,int>ranks;for(int k=0;k<100;++k)require(ranks.emplace(gt[qi*100+k],k).second,"unique GT100");
   for(size_t a=0;a<A;++a){size_t ix=j*A+a;auto en=entry(qi,a);e.search(q.data()+qi*d,en,100,128,I.data(),D.data(),true);ndc[ix]=e.count.count;top1[ix]=I[0];hits1[ix]=I[0]==gt[qi*100];hashes[ix]=result_hash(I.data(),D.data(),100);
    std::set<faiss::idx_t>unique;for(int k=0;k<100;++k){ref[ix*100+k]=I[k];rd[ix*100+k]=D[k];require(I[k]>=0&&I[k]<e.idx.ntotal&&unique.insert(I[k]).second,"valid unique return");auto it=ranks.find(I[k]);if(it!=ranks.end()){++hits100[ix];masks[ix*2+it->second/64]|=uint64_t(1)<<(it->second%64);}}
    if(a==0){for(int k=0;k<100;++k){bids[j*100+k]=I[k];bd[j*100+k]=D[k];}std::copy(en.begin(),en.end(),bentries.begin()+j*3);}
    if(j==0&&(a==0||a==1||a==H)){uint64_t dc=e.count.count;e.search(q.data()+qi*d,en,100,128,J.data(),E.data(),true,true);require(I==J&&!memcmp(D.data(),E.data(),400)&&e.count.count==dc,"label linked E99 parity");}
   }
  }
  for(int rep=0;rep<reps;++rep){std::vector<size_t>order(A);std::iota(order.begin(),order.end(),0);std::mt19937_64 gen(mix(20260921+lo*17+rep));std::shuffle(order.begin(),order.end(),gen);
   for(int kk=0;kk<2;++kk){int ki=(kk+rep+lo/block)%2,K=ki==0?1:100;auto ps=Clock::now();
    for(size_t a:order)for(size_t j=0;j<nb;++j){size_t qi=lo+j,ix=j*A+a;auto en=entry(qi,a);auto t=Clock::now();e.search(q.data()+qi*d,en,K,128,I.data(),D.data(),false);times[(ix*2+ki)*reps+rep]=seconds(t);for(int k=0;k<K;++k)require(I[k]==ref[ix*100+k],"all-action K/repeat IDs");require(!memcmp(D.data(),rd.data()+ix*100,4*K),"all-action K/repeat distance bits");}
    schedule.push_back({{"repeat",rep},{"K",K},{"seconds",seconds(ps)},{"order",order}});write_json(out/"progress.json",{{"block_start",lo},{"block_n",nb},{"repeat",rep},{"K",K},{"search_calls",e.calls},{"seconds",seconds(start)}});resources(out);require(seconds(start)<c["seconds_cap"].get<double>(),"label time guard");
   }
  }
  write_raw(bp/"top1_ids.i32",top1);write_raw(bp/"hits1.u8",hits1);write_raw(bp/"hits100.u8",hits100);write_raw(bp/"masks.u64",masks);write_raw(bp/"ndc.u64",ndc);write_raw(bp/"return_hashes.u64",hashes);write_raw(bp/"seconds.f64",times);write_raw(bp/"baseline_ids.i32",bids);write_raw(bp/"baseline_distances.f32",bd);write_raw(bp/"baseline_entries.i32",bentries);
  // Full returns for the first query in every block and all actions are retained.
  std::vector<int32_t>sampleI(ref.begin(),ref.begin()+A*100);std::vector<float>sampleD(rd.begin(),rd.begin()+A*100);write_raw(bp/"sample_ids.i32",sampleI);write_raw(bp/"sample_distances.f32",sampleD);write_json(bp/"timing_schedule.json",schedule);
  json done={{"status","PASS"},{"start",lo},{"n",nb},{"A",A},{"repeats",reps},{"actual_K",{1,100}},{"search_calls",e.calls-before},{"boot_id",bootid()},{"full_bit_parity",true}};write_json(bp/"complete.json",done);completed.push_back(done);threads();
 }
 write_json(out/"complete.json",{{"status","PASS"},{"mode","labels"},{"n",n},{"A",A},{"blocks",completed},{"new_search_calls",e.calls},{"inherited_search_calls",inherited_calls},{"search_calls",e.calls+inherited_calls},{"router_calls",e.router.calls},{"seconds",seconds(start)},{"threads",process_threads()}});
}

void evaluate(const json&c,const fs::path&out,Engine&e,const std::vector<float>&q,size_t n,size_t d){
 std::vector<std::unique_ptr<EvalMethod>>methods;for(auto j:c["methods"])methods.push_back(std::make_unique<EvalMethod>(j,d,e.router.ids.size()));Online online(e);std::array<faiss::idx_t,100>I;std::array<float,100>D;json timings=json::array();auto start=Clock::now();int ordinal=0;uint64_t parity=0;
 for(auto point:c["points"]){int K=point["K"],L=point["L"];require((K==1||K==100)&&L>=K,"real K/L");std::vector<std::unique_ptr<Batch>>refs(methods.size());std::vector<std::vector<int32_t>>acts(methods.size());std::vector<std::vector<double>>walls(methods.size());
  auto run=[&](size_t a,Batch&b,bool count,std::vector<int32_t>&choices,std::vector<float>*scores=nullptr){e.router.counting(count);choices.resize(n);if(scores)scores->resize(n);for(size_t i=0;i<n;++i){online.run(q.data()+i*d,*methods[a],K,L,I.data(),b.dist.data()+i*K,count);for(int k=0;k<K;++k)b.ids[i*K+k]=I[k];std::copy(online.entries.begin(),online.entries.end(),b.entries.begin()+3*i);choices[i]=online.choice;if(scores)(*scores)[i]=online.score;if(count){b.route_ndc[i]=online.route_count;b.graph_ndc[i]=e.count.count;}}};
  for(int rep=0;rep<c["repeats"].get<int>();++rep)for(size_t z=0;z<methods.size();++z){size_t a=(z+rep+ordinal+c.value("dataset_order",0))%methods.size();if(rep==0){refs[a]=std::make_unique<Batch>(n,K);run(a,*refs[a],false,acts[a]);}Batch b(n,K);std::vector<int32_t>choice(n);threads();auto t=Clock::now();run(a,b,false,choice);double sec=seconds(t);same(*refs[a],b);require(choice==acts[a],"formal repeat decisions");walls[a].push_back(sec);timings.push_back({{"method",methods[a]->name},{"K",K},{"L",L},{"repeat",rep},{"seconds",sec},{"qps",n/sec},{"threads",process_threads()},{"boot_id",bootid()}});write_json(out/"timing.json",timings);write_json(out/"progress.json",{{"method",methods[a]->name},{"K",K},{"L",L},{"repeat",rep},{"search_calls",e.calls},{"seconds",seconds(start)}});resources(out);}
  for(size_t a=0;a<methods.size();++a){Batch b(n,K);std::vector<int32_t>choices;std::vector<float>scores;run(a,b,true,choices,&scores);same(*refs[a],b);require(choices==acts[a],"formal count decisions");auto p=out/(methods[a]->name+"_K"+std::to_string(K)+"_L"+std::to_string(L));save_batch(p,b,false);save_batch(p,b,true);write_raw(p/"actions.i32",choices);write_raw(p/"chosen_scores.f32",scores);
   for(size_t i=0;i<std::min<size_t>(16,n);++i){std::array<int32_t,3>en;std::copy(b.entries.begin()+i*3,b.entries.begin()+i*3+3,en.begin());e.search(q.data()+i*d,en,K,L,I.data(),D.data(),true,true);for(int k=0;k<K;++k)require(I[k]==b.ids[i*K+k],"formal linked IDs");require(!memcmp(D.data(),b.dist.data()+i*K,4*K)&&e.count.count==b.graph_ndc[i],"formal linked bits/NDC");++parity;}
   write_json(p/"complete.json",{{"status","PASS"},{"n",n},{"K",K},{"L",L},{"method",methods[a]->name},{"seconds",walls[a]},{"threads",1},{"boot_id",bootid()},{"warm_plain_count_bit_parity",true}});
  }++ordinal;threads();require(seconds(start)<c["seconds_cap"].get<double>(),"evaluation time guard");
 }
 write_json(out/"complete.json",{{"status","PASS"},{"mode","evaluate"},{"n",n},{"search_calls",e.calls},{"router_calls",e.router.calls},{"linked_parity_queries",parity},{"seconds",seconds(start)},{"threads",process_threads()}});
}

int main(int argc,char**argv){try{require(argc==3,"experiment config output");threads();auto c=read_json(argv[1]);require(c["threads"]==1,"configured single thread");fs::path out=argv[2];std::string mode=c["mode"];
 if(fs::exists(out)){require(mode=="labels"&&read_json(out/"config.json")==c,"only identical label blocks may resume");require(!fs::exists(out/"complete.json"),"completed job cannot rerun");}else{fs::create_directories(out);write_json(out/"config.json",c);}
 size_t n=c["n"],d=c["dimension"];auto q=read_raw<float>(c["queries"].get<std::string>());require(q.size()==n*d,"input dimensions");for(float x:q)require(std::isfinite(x),"finite query");
 if(mode=="features"){features_only(c,out,q,n,d);return 0;}
 if(mode=="predict"){predict_only(c,out,q,n,d);return 0;}
 Route router(c["anchor"],d);auto idx=load_nsg(c["index"]);require(idx->d==d&&idx->ntotal==c["base_n"]&&idx->metric_type==0,"index contract");Fvecs base(c["base"]);require(base.n==idx->ntotal&&base.d==d,"base shape");std::vector<float>v(d);for(int j=0;j<32;++j){size_t id=(base.n-1)*j/31;idx->storage->reconstruct(id,v.data());require(!memcmp(v.data(),base.row(id),4*d),"graph/base bytes");}Engine engine(*idx,router);
 if(mode=="trace")trace(c,out,engine,q,n,d);else if(mode=="labels")labels(c,out,engine,q,n,d);else if(mode=="evaluate")evaluate(c,out,engine,q,n,d);else throw std::runtime_error("unknown mode");
 require(engine.calls<=c["max_search_calls"].get<uint64_t>(),"search call guard");return 0;
 }catch(const std::exception&err){std::cerr<<err.what()<<std::endl;return 1;}}

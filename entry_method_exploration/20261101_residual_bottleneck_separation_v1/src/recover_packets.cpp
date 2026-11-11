#include "decision_base.inc"
// Recovery only. Original timed six-array hashes must match; replay time is not QPS evidence.
int main(int argc,char**argv){try{
 using namespace e197;
 require(argc==2,"recovery config");auto c=read_json(argv[1]);check_threads(c);
 auto before=Clock::now();auto original=read_json(c.at("recovery_expected"));
 fs::path root=c.at("output_dir");fresh_dir(root);fresh_json(root/"config.json",c);
 Context x(c);e194::FastBackend aux(c);Matrix qm(c.at("queries"));auto Q=qm.copy();
 std::map<std::pair<int,int>,std::unique_ptr<Batch>>gt;
 uint64_t points=0,linear=0;json hashes=json::array();
 for(auto p:original.at("results")){
  int K=p.at("K"),L=p.at("L");std::string m=p.at("method");
  fs::path path=root/("k"+std::to_string(K))/(m+"_L"+std::to_string(L));
  fs::create_directories(path);Batch b(qm.n,K);std::vector<Work>work(qm.n);std::vector<int32_t>chosen(qm.n*3,-1);
  if(m=="GT10"||m=="REUSE-SQ"){
   run_actual(x,aux,Q,c,K,L,m,b,work,chosen);
   if(m=="GT10")gt[{K,L}]=std::make_unique<Batch>(b);
   else{require(gt.count({K,L}),"SQ actual GT available");audit_sq(*x.idx,Q,aux,*gt.at({K,L}),b,path);}
  }else{
   std::vector<RouteData>routes;for(size_t i=0;i<qm.n;++i){auto r=x.router->route(Q.data()+i*x.idx->d);routes.push_back(r);for(int z=0;z<3;++z){b.entries[i*3+z]=r.ids[z];b.profile_distances[i*3+z]=r.distances[z];}}
   fs::create_directories(path);gzFile f=gzopen((path/"witness.bin.gz").c_str(),"wb1");require(f,"recovery witness");
   Runner runner(x,c,m,qm.n);
   for(size_t i=0;i<qm.n;++i){
    QueryDetail detail;detail.capture=true;
    auto v=runner.query(Q.data()+i*x.idx->d,routes[i],K,L,m,i,&detail);
    std::copy(v.ids.begin(),v.ids.end(),b.ids.begin()+i*K);std::copy(v.values.begin(),v.values.end(),b.distances.begin()+i*K);
    if(m!="OPT-B32"&&m!="Q8-B32")work[i]=v.work;
    if(p.at("seed_ids_in_separate_file_collected").get<bool>())for(size_t z=0;z<detail.seeds.size();++z)chosen[i*3+z]=detail.seeds[z];
    std::vector<int32_t>I;std::vector<float>V;merge_linear(detail.main.data(),detail.dist.data(),K,detail.events,I,V);
    require(I==v.ids&&V.size()==v.values.size()&&!std::memcmp(V.data(),v.values.data(),K*4),"restored full linear witness");++linear;
    uint32_t h[4]={uint32_t(i),uint32_t(K),uint32_t(detail.events.size()),uint32_t(detail.seeds.size())};gzwrite(f,h,sizeof(h));
    for(int z=0;z<K;++z){gzwrite(f,&detail.main[z],4);gzwrite(f,&detail.dist[z],4);}
    for(auto ev:detail.events){gzwrite(f,&ev.id,4);gzwrite(f,&ev.value,4);}
    if(!detail.seeds.empty())gzwrite(f,detail.seeds.data(),detail.seeds.size()*4);
   }
   require(gzclose(f)==Z_OK,"restored witness closed");
   fresh_json(path/"oracle.json",{{"status","PASS_RESTORED_QUERY_LINEAR_ORACLE"},{"queries",qm.n},{"replayed_not_original_witness",true}});
  }
  validate(b,x.idx->ntotal);auto hash=packet_sha(b);
  for(auto round:p.at("rounds"))require(round.at("packet_sha256")==hash,"REPLAY MUST MATCH ORIGINAL TIMED SIX ARRAY SHA");
  b.save(path/"raw",false);std::vector<uint64_t>flat;for(auto row:work)flat.insert(flat.end(),row.begin(),row.end());
  write_raw(path/"work.u64",flat);write_raw(path/"seeds.i32",chosen);
  for(auto round:p.at("rounds"))fresh_json(path/("round"+std::to_string(round.at("round").get<int>())+".json"),round);
  fresh_json(path/"result.json",p);hashes.push_back({{"K",K},{"L",L},{"method",m},{"original_timed_packet_sha256",hash}});
  ++points;std::cout<<json{{"stage","restore_packet"},{"dataset",c.at("dataset")},{"window",c.at("window")},{"points",points},{"total",original.at("points")},{"K",K},{"L",L},{"method",m},{"six_array_hash_equal",true}}.dump()<<std::endl;
 }
 require(points==original.at("points"),"all expected points restored");
 fresh_json(root/"environment.json",{{"threads",process_threads()},{"cpu",15},{"recovery_only",true},{"original_timing_in_complete_json",true},{"new_replay_seconds_not_query_QPS",true}});
 fresh_json(root/"recovery_complete.json",{{"status","PASS_ALL_ORIGINAL_TIMED_SIX_ARRAY_SHA_RESTORED"},{"points",points},{"query_linear_witnesses",linear},{"packet_hashes",hashes},{"seconds",seconds(before)},{"timings_from_original_persistent_native_log",true},{"work_seeds_and_witnesses_replayed_not_individually_original_hashed",true}});
 fresh_json(root/"complete.json",original);return 0;
 }catch(const std::exception&e){std::cerr<<"FATAL PACKET RECOVERY "<<e.what()<<std::endl;return 2;}}

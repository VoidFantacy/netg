json inference_audit(const json&c){
 const auto t=Clock::now();fs::path root=c.at("experiment_root"),dir=fs::path(c.at("q8_table")).parent_path();auto j=read_json(dir/"selected.json");auto info=read_json(fs::path(c.at("output_dir"))/"complete.json");size_t rows=info.at("rows");
 std::ifstream x(fs::path(c.at("scratch"))/"features.f32",std::ios::binary);gzFile met=gzopen((fs::path(c.at("output_dir"))/"labels.i32.gz").c_str(),"rb");require(bool(x)&&met,"audit source streams");
 std::map<int,Model>model;std::map<int,gzFile>expected;for(int K:{1,100}){model.emplace(K,Model(j.at("K").at(std::to_string(K))));expected[K]=gzopen((dir/("inference.k"+std::to_string(K)+".f64.gz")).c_str(),"rb");require(expected[K],"model reference predictions");}
 double maximum=0;uint64_t checked=0;for(size_t i=0;i<rows;++i){int32_t h[META];std::array<float,F>f;require(gzread(met,h,sizeof(h))==sizeof(h),"metadata full record");x.read((char*)f.data(),sizeof(f));require(bool(x),"feature full record");double ref[2];require(gzread(expected.at(h[1]),ref,sizeof(ref))==sizeof(ref)&&ref[0]==double(i),"aligned Python prediction index");double p=model.at(h[1]).predict(f.data());double err=std::abs(p-ref[1]);maximum=std::max(maximum,err);require(err<=1e-8*(1+std::abs(ref[1])),"native/Python numerical inference parity");++checked;}
 gzclose(met);for(auto a:expected)gzclose(a.second);json result={{"status","PASS_ALL_LABEL_ROW_NATIVE_MODEL_INFERENCE"},{"rows",checked},{"max_absolute_error",maximum},{"seconds",seconds(t)},{"source","actual native feature stream and Python model predictions"}};fresh_json(root/"reviews"/(c.at("dataset").get<std::string>()+".inference.json"),result);return result;
}
struct QueryDetail {std::vector<int32_t>main,seeds;std::vector<float>dist;std::vector<Event>events;Work work{};bool capture=false;};
struct Runner {
 Context&x;VisitedTable vt;std::unique_ptr<DistanceComputer>dc;std::vector<Neighbor>ret;std::vector<float>cache;Replay rec;size_t n;
 Runner(Context&xx,const json&c,const std::string&m,size_t nn):x(xx),vt(xx.idx->ntotal),dc(acsg::storage_distance_computer(xx.idx->storage)),n(c.at("queries").at("n")){
  if(m.rfind("SHARED",0)==0||m=="ORACLE-S1")cache.resize(xx.idx->ntotal);
  if(m.rfind("MODEL",0)==0)require(x.models.size()==2,"frozen models loaded before timer");
  if(m.rfind("ORACLE",0)==0)require(x.teacher_masks.size()==4*n,"explicit diagnostic teacher mask shape");
 }
 Outcome query(const float*q,const RouteData&route,int K,int L,const std::string&m,size_t qi,QueryDetail*detail=nullptr){
  bool shared=m.rfind("SHARED",0)==0||m=="ORACLE-S1";bool early=m.rfind("EARLY",0)==0;std::vector<int32_t>R,C;std::vector<float>D,cv;RouteData mainroute=route;std::vector<Node>seeds;Work extra{};
  Posting&p=(m=="OPT-B32"||m=="REF-DIST384"||m.find("-FULL")!=std::string::npos)?*x.reference:*x.post;
  if(early){dc->set_query(q);std::vector<int32_t>empty;candidates(p,route,empty,*dc,C,cv);auto rank=ranks(cv);extra[0]=C.size();
   if(!rank.empty()){
    if(m.rfind("EARLY-MIX",0)==0){std::array<int,3>ri{0,1,2};std::stable_sort(ri.begin(),ri.end(),[&](int a,int b){return route.distances[a]<route.distances[b];});mainroute.ids={route.ids[ri[0]],route.ids[ri[1]],C[rank[0]]};}
    else{for(int j=0;j<3;++j)mainroute.ids[j]=C[rank[std::min<size_t>(j,rank.size()-1)]];}
   }
  }
  main_search(x,q,K,L,mainroute,vt,R,D,ret,*dc,shared?&rec:nullptr,shared?&cache:nullptr);
  if(!early)candidates(p,route,R,*dc,C,cv);
  else{std::vector<int32_t>a;std::vector<float>b;for(size_t j=0;j<C.size();++j)if(std::find(R.begin(),R.end(),C[j])==R.end()){a.push_back(C[j]);b.push_back(cv[j]);}C.swap(a);cv.swap(b);}
  auto rank=ranks(cv);int mode=0,cap=m.find("96")!=std::string::npos?96:384;
  if(m.rfind("MODEL",0)==0){const auto&model=x.models.at(K);bool gated=m.find("GATE")!=std::string::npos;int best=-1;double value=-std::numeric_limits<double>::infinity();if(!gated||!model.off)for(size_t j=0;j<rank.size();++j){int pos=rank[j];auto f=x.features->row(q,route,vt,C,cv,j,pos,D.data(),K,L,model.count>24,&p);double v=model.predict(f.data());if(best<0||v>value){best=pos;value=v;}}
   if(best>=0&&(!gated||(!model.off&&value>=model.threshold)))seeds.push_back({cv[best],uint32_t(best),C[best]});
  }else if(m=="DIST1"||m=="DIST1-FULL"){
   if(!rank.empty()){int pos=rank[0];seeds.push_back({cv[pos],uint32_t(pos),C[pos]});}
  }else if(m.rfind("ORACLE",0)==0){int id=x.teacher_masks[(K==1?0:2)*n+(m=="ORACLE-S1"?n:0)+qi];if(id>=0){auto it=std::find(C.begin(),C.end(),id);float value=it!=C.end()?cv[it-C.begin()]:cache.at(id);seeds.push_back({value,0,id});}if(m=="ORACLE-S1")mode=2;
  }else if(m.rfind("SHARED-CAPTURE",0)==0){
   mode=2; // Capture the actual main state, return direct completion, expand no seed.
  }else if(m=="SHARED-FRONT3"){
   std::unordered_set<int>expanded(rec.expanded.begin(),rec.expanded.end());std::vector<Node>boundary;for(int id:rec.scored)if(!expanded.count(id))boundary.push_back({cache[id],uint32_t(boundary.size()),id});std::sort(boundary.begin(),boundary.end(),[](auto a,auto b){return a.value<b.value||(a.value==b.value&&a.order<b.order);});for(size_t j=0;j<std::min<size_t>(3,boundary.size());++j)seeds.push_back(boundary[j]);mode=2;
  }else if(m.rfind("AUX",0)==0||m.rfind("CBRIDGE",0)==0||m.rfind("SHARED",0)==0||m=="REF-DIST384"){
   seeds=distance_seeds(p,route,C,cv);mode=m.rfind("SHARED",0)==0?2:m.rfind("CBRIDGE",0)==0?1:0;
  }
  Outcome result;
  if(early||m=="Q8-B32"||m=="OPT-B32"||m.rfind("SHARED-CAPTURE",0)==0){
   for(size_t j=0;j<C.size();++j)result.events.push_back({C[j],cv[j],0});merge_heap(R.data(),D.data(),K,result.events,result.ids,result.values);result.work[0]=early?extra[0]:C.size();
   if(early)for(int id:mainroute.ids)seeds.push_back({0.f,uint32_t(seeds.size()),id});result.work[6]=seeds.size();
  }else result=expand(x,*dc,vt,R,D,C,cv,seeds,mode,cap,shared?&rec:nullptr,shared?&cache:nullptr);
  if(detail){if(detail->capture){detail->main=R;detail->dist=D;detail->events=result.events;}detail->work=result.work;for(auto s:seeds)detail->seeds.push_back(s.id);}return result;
 }
};
void run_actual(Context&x,Backend&aux,const std::vector<float>&Q,const json&c,int K,int L,const std::string&m,Batch&out,std::vector<Work>&work,std::vector<int32_t>&chosen){
 work.assign(out.n,Work{});chosen.assign(out.n*3,-1);
 if(m=="GT10"){Method a;a.route=x.router.get();a.family="GT10";run_batch(*x.idx,Q,L,a,out);return;}
 if(m=="REUSE-SQ"){Stats a;e191::run(*x.idx,Q,L,m,*x.router,*x.reference,aux,out,a);for(size_t i=0;i<out.n;++i){work[i][2]=a.per_query[i*5+2];work[i][7]=a.per_query[i*5];}return;}
 if(m=="REF-DIST384"||m=="AUX96"||m=="AUX384"){
  Meter meter;e195::run(*x.idx,Q,L,m=="REF-DIST384"?"DIST384":m=="AUX96"?"DIST96":"DIST384",*x.router,m=="REF-DIST384"?*x.reference:*x.post,aux,*x.meta,out,meter);work=meter.work;return;
 }
 if(m=="OPT-B32"||m=="Q8-B32"){
  // Same native E194 optimized direct path; Backend object is unused for this branch.
  Stats st;e194::run_opt(*x.idx,Q,L,"OPT-B32",*x.router,m=="OPT-B32"?*x.reference:*x.post,static_cast<e194::FastBackend&>(aux),out,st);return;
 }
 std::vector<RouteData>routes;routes.reserve(out.n);for(size_t i=0;i<out.n;++i){auto r=x.router->route(Q.data()+i*x.idx->d);routes.push_back(r);for(int j=0;j<3;++j){out.entries[i*3+j]=r.ids[j];out.profile_distances[i*3+j]=r.distances[j];}}
 Runner runner(x,c,m,out.n);for(size_t i=0;i<out.n;++i){QueryDetail detail;auto value=runner.query(Q.data()+i*x.idx->d,routes[i],K,L,m,i,&detail);std::copy(value.ids.begin(),value.ids.end(),out.ids.begin()+i*K);std::copy(value.values.begin(),value.values.end(),out.distances.begin()+i*K);work[i]=value.work;for(size_t j=0;j<std::min<size_t>(3,detail.seeds.size());++j)chosen[i*3+j]=detail.seeds[j];}
}
__attribute__((noinline)) double full_timed(Context&x,Backend&aux,const std::vector<float>&Q,const json&c,int K,int L,const std::string&m,Batch&dest,std::vector<Work>&work,std::vector<int32_t>&chosen){
 const auto t=Clock::now();{Batch b(dest.n,K);run_actual(x,aux,Q,c,K,L,m,b,work,chosen);copy_packet(b,dest);asm volatile(""::"g"(dest.ids.data()),"g"(b.ids.data()):"memory");}return seconds(t);
}
void audit_actual(Context&x,const std::vector<float>&Q,const json&c,int K,int L,const std::string&m,const Batch&b,const std::vector<Work>&work,const fs::path&path){
 if(m=="GT10"||m=="REUSE-SQ")return;
 auto t=Clock::now();Runner runner(x,c,m,b.n);gzFile f=gzopen((path/"witness.bin.gz").c_str(),"wb1");require(f,"witness output");
 for(size_t i=0;i<b.n;++i){const float*q=Q.data()+i*x.idx->d;auto route=x.router->route(q);QueryDetail detail;detail.capture=true;auto value=runner.query(q,route,K,L,m,i,&detail);std::vector<int32_t>I;std::vector<float>V;merge_linear(detail.main.data(),detail.dist.data(),K,detail.events,I,V);for(int j=0;j<K;++j)require(I[j]==b.ids[i*K+j]&&value.ids[j]==I[j]&&equal_float(V[j],b.distances[i*K+j])&&equal_float(V[j],value.values[j]),"all-query replay/linear oracle actual timed output");
  if(m!="OPT-B32"&&m!="Q8-B32")require(detail.work==work[i],"all-query action work parity");uint32_t h[4]={uint32_t(i),uint32_t(K),uint32_t(detail.events.size()),uint32_t(detail.seeds.size())};gzwrite(f,h,sizeof(h));for(int j=0;j<K;++j){gzwrite(f,&detail.main[j],4);gzwrite(f,&detail.dist[j],4);}for(auto a:detail.events){gzwrite(f,&a.id,4);gzwrite(f,&a.value,4);}if(!detail.seeds.empty())gzwrite(f,detail.seeds.data(),detail.seeds.size()*4);
 }require(gzclose(f)==Z_OK,"witness close");fresh_json(path/"oracle.json",{{"status","PASS_ALL_QUERY_ACTUAL_TIMED_LINEAR_ORACLE"},{"queries",b.n},{"seconds",seconds(t)}});
}
json matrix(const json&c,bool calibration){
 check_threads(c);auto started=Clock::now();fs::path root=c.at("output_dir");fresh_dir(root);fresh_json(root/"config.json",c);Context x(c);e194::FastBackend aux(c);Matrix qm(c.at("queries"));auto Q=qm.copy();json results=json::array();int ordinal=0,batches=0;std::map<std::pair<int,int>,std::vector<std::string>>groups;
 for(auto point:c.at("points"))groups[{point.at("K"),point.at("L")}].push_back(point.at("method"));
 fresh_json(root/"environment.json",{{"threads",process_threads()},{"cpu",15},{"binding",x.binding},{"shared_backend_bytes",aux.bytes()},{"timer","complete normal batch plus actual route/search/features/model/state/action/merge/copy/destruction"},{"calibration",calibration},{"online_GT",false},{"entry_ids_semantics","original GT10 router IDs; changed early search seeds retained separately"}});
 for(auto&group:groups){int K=group.first.first,L=group.first.second;auto ms=group.second;size_t count=ms.size();std::vector<std::unique_ptr<Batch>>first(count);std::vector<std::vector<Work>>meters(count);std::vector<std::vector<int32_t>>seed_ids(count);std::vector<json>rounds(count,json::array());Batch dest(qm.n,K);
  for(int rep=0;rep<3;++rep)for(size_t off=0;off<count;++off){size_t mi=(ordinal+rep+off)%count;auto m=ms[mi];check_threads(c);auto path=root/("k"+std::to_string(K))/(m+"_L"+std::to_string(L));if(rep==0){Batch warm(std::min<size_t>(128,qm.n),K);std::vector<Work>w;std::vector<int32_t>s;run_actual(x,aux,Q,c,K,L,m,warm,w,s);}std::vector<Work>w;std::vector<int32_t>s;double wall=full_timed(x,aux,Q,c,K,L,m,dest,w,s);check_threads(c);validate(dest,x.idx->ntotal);auto hash=packet_sha(dest);
   if(rep==0){first[mi]=std::make_unique<Batch>(dest);meters[mi]=w;seed_ids[mi]=s;dest.save(path/"raw",false);std::vector<uint64_t>flat;for(auto a:w)flat.insert(flat.end(),a.begin(),a.end());write_raw(path/"work.u64",flat);write_raw(path/"seeds.i32",s);}else{all_same(*first[mi],dest);require(w==meters[mi]&&s==seed_ids[mi],"three-round action/selection equality");}
   json rec={{"round",rep},{"wall_seconds",wall},{"qps",qm.n/wall},{"packet_sha256",hash},{"threads",1}};rounds[mi].push_back(rec);fresh_json(path/("round"+std::to_string(rep)+".json"),rec);++batches;std::cout<<json{{"dataset",c.at("dataset")},{"window",c.value("window","cal")},{"K",K},{"L",L},{"method",m},{"round",rep},{"qps",qm.n/wall}}.dump()<<std::endl;
  }
  for(size_t mi=0;mi<count;++mi){auto path=root/("k"+std::to_string(K))/(ms[mi]+"_L"+std::to_string(L));if(!calibration)audit_actual(x,Q,c,K,L,ms[mi],*first[mi],meters[mi],path);if(!calibration&&ms[mi]=="REUSE-SQ"){auto gt=std::find(ms.begin(),ms.end(),"GT10");require(gt!=ms.end(),"actual main for SQ audit");audit_sq(*x.idx,Q,aux,*first[gt-ms.begin()],*first[mi],path);}std::vector<double>w;for(auto a:rounds[mi])w.push_back(a.at("wall_seconds"));std::sort(w.begin(),w.end());json rec={{"dataset",c.at("dataset")},{"window",c.value("window","cal")},{"method",ms[mi]},{"K",K},{"L",L},{"n",qm.n},{"qps",qm.n/w[1]},{"rounds",rounds[mi]},{"result_dir",path.string()},{"all_round_bits_and_work_equal",true},{"seed_ids_in_separate_file_collected",ms[mi]!="GT10"&&ms[mi]!="REUSE-SQ"&&ms[mi]!="REF-DIST384"&&ms[mi]!="AUX96"&&ms[mi]!="AUX384"&&ms[mi]!="OPT-B32"&&ms[mi]!="Q8-B32"},{"direct_counts_reconstructed_from_witness",ms[mi]=="OPT-B32"||ms[mi]=="Q8-B32"}};results.push_back(rec);fresh_json(path/"result.json",rec);}
  ++ordinal;
 }
 json result={{"status",calibration?"PASS_COMPLETE_WALL_CALIBRATION":"PASS_FORMAL_BOTTLENECK_MATRIX"},{"points",results.size()},{"batches",batches},{"results",results},{"native_process_seconds",seconds(started)},{"GT_read",false}};fresh_json(root/"complete.json",result);return result;
}

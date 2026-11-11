std::vector<double> flat(const json&j){std::vector<double>v;if(j.size()&&j[0].is_array()){for(auto&r:j)for(auto&a:r)v.push_back(a.get<double>());}else for(auto&a:j)v.push_back(a.get<double>());return v;}
struct Student {
 std::vector<double>qm,qs,cm,cs,w1,b1,w2,b2,cw,cb;std::unordered_map<int,std::array<double,32>>nodes;
 Model t0,t1,gate;double lambda;
 Student(const json&j):qm(flat(j.at("q_mean"))),qs(flat(j.at("q_scale"))),cm(flat(j.at("c_mean"))),cs(flat(j.at("c_scale"))),w1(flat(j.at("qw1"))),b1(flat(j.at("qb1"))),w2(flat(j.at("qw2"))),b2(flat(j.at("qb2"))),cw(flat(j.at("cw"))),cb(flat(j.at("cb"))),t0(j.at("teacher")[0]),t1(j.at("teacher")[1]),gate(j.at("gate")),lambda(j.at("lam")){
  auto ids=read_raw<int32_t>(j.at("node_ids"));auto values=read_raw<double>(j.at("node_embeddings"));require(values.size()==ids.size()*32,"node embedding shape");for(size_t i=0;i<ids.size();++i){std::array<double,32>a;std::copy(values.begin()+i*32,values.begin()+(i+1)*32,a.begin());nodes.emplace(ids[i],a);}
 }
 std::array<double,64> encode(const float*q)const{double input[25],hidden[64];for(int j=0;j<25;++j)input[j]=(double(q[j])-qm[j])/qs[j];for(int i=0;i<64;++i){double s=b1[i];for(int j=0;j<25;++j)s+=w1[i*25+j]*input[j];hidden[i]=std::max(0.,s);}std::array<double,64>v;for(int i=0;i<64;++i){double s=b2[i];for(int j=0;j<64;++j)s+=w2[i*64+j]*hidden[j];v[i]=s;}return v;}
 std::array<double,2>predict(int id,const float*f,const std::array<double,64>&q)const{auto&v=nodes.at(id);std::array<double,2>p;for(int b=0;b<2;++b){double a=0;for(int j=0;j<32;++j)a+=q[b*32+j]*v[j];a/=std::sqrt(32.);a+=cb[b];int n=0;for(int j=0;j<24;++j)if(j!=14){a+=cw[b*23+n]*(double(f[j])-cm[n])/cs[n];++n;}p[b]=a;}return p;}
};
using Models=std::map<std::pair<int,int>,std::unique_ptr<Student>>;
Models load_models(const json&c){Models m;for(auto&j:c.at("model_files")){int K=j.at("K"),L=j.at("L");m[{K,L}]=std::make_unique<Student>(read_json(j.at("path")));}return m;}
struct Decision {std::array<int32_t,4>v{{-1,0,0,0}};double gate_score=0;};
struct PolicyRunner {
 Context&x;Student&s;VisitedTable vt;std::unique_ptr<DistanceComputer>dc;std::vector<Neighbor>ret;
 PolicyRunner(Context&xx,Student&ss):x(xx),s(ss),vt(xx.idx->ntotal),dc(acsg::storage_distance_computer(xx.idx->storage)){}
 Outcome query(const float*q,const RouteData&r,int K,int L,const std::string&m,Decision&choice,QueryDetail*detail=nullptr){
  std::vector<int32_t>R,C;std::vector<float>D,cv;main_search(x,q,K,L,r,vt,R,D,ret,*dc);candidates(*x.post,r,R,*dc,C,cv);std::vector<Node>seeds;int cap=0;
  if(!C.empty()){
   bool usegate=m=="POLICY"||m=="POLICY-OFF";Cached cache(x,q,r,vt,C,cv,D,K,L,false);
   bool enter=true;if(usegate){choice.gate_score=s.gate.predict(cache.gate.data());enter=!s.gate.off&&choice.gate_score>=s.gate.threshold;if(m=="POLICY-OFF")enter=false;}choice.v[2]=enter;
   if(enter){auto rank=ranks(cv);int best=-1;cap=m.find("96")!=std::string::npos?96:384;
    if(m=="DIST96"||m=="DIST384"){best=rank[0];}
    else{
     cache.project_query();if(m=="TEACHER384"||m=="OLD-CACHED384"){
      const Model&model=m=="TEACHER384"?s.t1:x.models.at(K);double high=-std::numeric_limits<double>::infinity();for(size_t j=0;j<rank.size();++j){auto f=cache.row(j,rank[j]);double v=model.predict(f.data());if(best<0||v>high){best=rank[j];high=v;}}choice.v[3]=C.size();
     }else{
      auto eq=s.encode(cache.query.data());std::vector<std::array<double,2>>pred(C.size());std::vector<int>positions(C.size());for(size_t j=0;j<rank.size();++j){int pos=rank[j];positions[pos]=j;auto f=cache.row(j,pos,false);pred[pos]=s.predict(C[pos],f.data(),eq);}
      bool adaptive=m=="ADAPT"||m=="POLICY";int required=cap==96?0:1;std::array<int,2>picked{{-1,-1}};std::array<double,2>values{{-1e30,-1e30}};
      for(int b=0;b<2;++b){if(!adaptive&&b!=required)continue;auto sorted=rank;std::stable_sort(sorted.begin(),sorted.end(),[&](int a,int z){return pred[a][b]>pred[z][b];});
       if(m=="FAST96"||m=="FAST384"){picked[b]=sorted[0];values[b]=pred[sorted[0]][b];}
       else{std::vector<int>shortlist{rank[0]};for(size_t j=0;j<std::min<size_t>(5,sorted.size());++j)if(std::find(shortlist.begin(),shortlist.end(),sorted[j])==shortlist.end())shortlist.push_back(sorted[j]);std::sort(shortlist.begin(),shortlist.end(),[&](int a,int z){return positions[a]<positions[z];});choice.v[3]+=shortlist.size();
        for(int pos:shortlist){auto f=cache.row(positions[pos],pos);double v=(b?s.t1:s.t0).predict(f.data());if(picked[b]<0||v>values[b]){picked[b]=pos;values[b]=v;}}
       }
      }
      if(adaptive){values[0]-=s.lambda*.25;values[1]-=s.lambda;required=values[1]>values[0]?1:0;if(values[required]<=0){best=-1;cap=0;}else{best=picked[required];cap=required?384:96;}}
      else best=picked[required];
     }
    }
    if(best>=0){seeds.push_back({cv[best],uint32_t(best),C[best]});choice.v[0]=C[best];choice.v[1]=cap;}
   }
  }
  auto result=expand(x,*dc,vt,R,D,C,cv,seeds,0,cap);if(detail){detail->main=R;detail->dist=D;detail->events=result.events;detail->work=result.work;for(auto&a:seeds)detail->seeds.push_back(a.id);}return result;
 }
};
bool custom(const std::string&m){return m=="DIST96"||m=="DIST384"||m=="FAST96"||m=="FAST384"||m=="CASCADE96"||m=="CASCADE384"||m=="ADAPT"||m=="POLICY"||m=="POLICY-OFF"||m=="TEACHER384"||m=="OLD-CACHED384";}
void run198(Context&x,Backend&aux,Models&models,const std::vector<float>&Q,const json&c,int K,int L,const std::string&m,Batch&out,std::vector<Work>&work,std::vector<int32_t>&decisions){
 if(!custom(m)){std::vector<int32_t>seeds;run_actual(x,aux,Q,c,K,L,m,out,work,seeds);decisions.assign(out.n*4,0);return;}
 work.assign(out.n,Work{});decisions.assign(out.n*4,0);std::vector<RouteData>routes;routes.reserve(out.n);for(size_t i=0;i<out.n;++i){auto r=x.router->route(Q.data()+i*x.idx->d);routes.push_back(r);for(int j=0;j<3;++j){out.entries[i*3+j]=r.ids[j];out.profile_distances[i*3+j]=r.distances[j];}}
 PolicyRunner runner(x,*models.at({K,L}));for(size_t i=0;i<out.n;++i){Decision choice;auto result=runner.query(Q.data()+i*x.idx->d,routes[i],K,L,m,choice);std::copy(result.ids.begin(),result.ids.end(),out.ids.begin()+i*K);std::copy(result.values.begin(),result.values.end(),out.distances.begin()+i*K);work[i]=result.work;std::copy(choice.v.begin(),choice.v.end(),decisions.begin()+i*4);}
}
__attribute__((noinline))double timed198(Context&x,Backend&aux,Models&models,const std::vector<float>&Q,const json&c,int K,int L,const std::string&m,Batch&dest,std::vector<Work>&work,std::vector<int32_t>&decisions){auto t=Clock::now();{Batch out(dest.n,K);run198(x,aux,models,Q,c,K,L,m,out,work,decisions);copy_packet(out,dest);asm volatile(""::"g"(out.ids.data()),"g"(dest.ids.data()):"memory");}return seconds(t);}
void audit198(Context&x,Models&models,const std::vector<float>&Q,const json&c,int K,int L,const std::string&m,const Batch&b,const std::vector<Work>&work,const std::vector<int32_t>&decisions,const fs::path&path){
 if(!custom(m)){audit_actual(x,Q,c,K,L,m,b,work,path);return;}
 PolicyRunner runner(x,*models.at({K,L}));gzFile f=gzopen((path/"witness.bin.gz").c_str(),"wb3");require(f,"witness output");gzFile sf=nullptr;if(m=="POLICY")sf=gzopen((path/"selection.bin.gz").c_str(),"wb3");
 for(size_t i=0;i<b.n;++i){auto*q=Q.data()+i*x.idx->d;auto route=x.router->route(q);Decision choice;QueryDetail detail;auto result=runner.query(q,route,K,L,m,choice,&detail);std::vector<int32_t>I;std::vector<float>V;merge_linear(detail.main.data(),detail.dist.data(),K,detail.events,I,V);require(I==result.ids&&!std::memcmp(V.data(),result.values.data(),K*4),"independent linear merged IDs and values");for(int j=0;j<K;++j)require(I[j]==b.ids[i*K+j]&&equal_float(V[j],b.distances[i*K+j]),"timed output witness equality");require(result.work==work[i]&&std::equal(choice.v.begin(),choice.v.end(),decisions.begin()+i*4),"timed decision and work witness equality");uint32_t h[4]={uint32_t(i),uint32_t(K),uint32_t(detail.events.size()),uint32_t(detail.seeds.size())};gzwrite(f,h,sizeof(h));for(int j=0;j<K;++j){gzwrite(f,&detail.main[j],4);gzwrite(f,&detail.dist[j],4);}for(auto&a:detail.events){gzwrite(f,&a.id,4);gzwrite(f,&a.value,4);}if(!detail.seeds.empty())gzwrite(f,detail.seeds.data(),4*detail.seeds.size());
  if(sf){std::vector<int32_t>C;std::vector<float>cv;for(size_t j=0;j<result.work[0];++j){C.push_back(detail.events[j].id);cv.push_back(detail.events[j].value);}Cached cache(x,q,route,runner.vt,C,cv,detail.dist,K,L);uint32_t h[2]={uint32_t(i),uint32_t(C.size())};gzwrite(sf,h,sizeof(h));gzwrite(sf,cache.gate.data(),48);auto rank=ranks(cv);for(size_t j=0;j<rank.size();++j){int32_t id=C[rank[j]];auto row=cache.row(j,rank[j]);gzwrite(sf,&id,4);gzwrite(sf,row.data(),F*4);}}
 }require(gzclose(f)==Z_OK,"witness close");if(sf)require(gzclose(sf)==Z_OK,"selection close");fresh_json(path/"oracle.json",{{"status","PASS_ALL_QUERY_TIMED_LINEAR_ORACLE_AND_DECISION"},{"queries",b.n}});
}
json inference(const json&c){
 auto start=Clock::now();auto model=read_json(c.at("model_file"));Student s(model);fs::path labels=c.at("labels_dir"),path=c.at("model_file");gzFile f=gzopen((labels/"labels.bin.gz").c_str(),"rb"),pred=gzopen((path.parent_path()/"prediction_reference.f64.gz").c_str(),"rb");require(f&&pred,"inference reference streams");int32_t m[MI];float a[XF];double expected[4];size_t rows=0;double maxerr=0;int indices[9]={5,6,7,8,9,10,15,16,17};
 while(gzread(f,m,sizeof(m))==sizeof(m)){require(gzread(f,a,sizeof(a))==sizeof(a)&&gzread(pred,expected,sizeof(expected))==sizeof(expected),"full aligned inference row");float q[25];for(int j=0;j<16;++j)q[j]=a[24+j];for(int j=0;j<9;++j)q[16+j]=a[indices[j]];auto eq=s.encode(q);auto v=s.predict(m[1],a,eq);double got[4]={v[0],v[1],s.t0.predict(a),s.t1.predict(a)};for(int j=0;j<4;++j){double err=std::abs(got[j]-expected[j]);maxerr=std::max(maxerr,err);require(err<1e-8*(1+std::abs(expected[j])),"native exported-model prediction parity");}++rows;}
 require(gzread(pred,expected,1)==0,"no extra reference rows");gzclose(f);gzclose(pred);return json{{"status","PASS_NATIVE_NUMPY_ALL_LABEL_PREDICTIONS"},{"rows",rows},{"max_absolute_error",maxerr},{"seconds",seconds(start)}};
}
json matrix198(const json&c){
 check_threads(c);auto start=Clock::now();fs::path root=c.at("output_dir");fresh_dir(root);fresh_json(root/"config.json",c);Context x(c);e194::FastBackend aux(c);auto models=load_models(c);Matrix qm(c.at("queries"));auto Q=qm.copy();json results=json::array();int ordinal=0,batches=0;std::map<std::pair<int,int>,std::vector<std::string>>groups;for(auto p:c.at("points"))groups[{p.at("K"),p.at("L")}].push_back(p.at("method"));
 fresh_json(root/"environment.json",{{"actual_threads",process_threads()},{"cpu",15},{"binding",x.binding},{"online_GT",false},{"timer","complete Batch creation, route, search, direct C, policy, expansion, merge, six-array copy and destruction"},{"shared_backend_bytes",aux.bytes()}});
 for(auto&group:groups){int K=group.first.first,L=group.first.second;auto ms=group.second;size_t n=ms.size();std::vector<std::unique_ptr<Batch>>first(n);std::vector<std::vector<Work>>meters(n);std::vector<std::vector<int32_t>>decisions(n);std::vector<json>rounds(n,json::array());Batch dest(qm.n,K);
  for(int rep=0;rep<3;++rep)for(size_t off=0;off<n;++off){size_t j=(ordinal+rep+off)%n;auto m=ms[j];auto path=root/("k"+std::to_string(K))/(m+"_L"+std::to_string(L));if(rep==0){Batch warm(std::min<size_t>(128,qm.n),K);std::vector<Work>w;std::vector<int32_t>d;run198(x,aux,models,Q,c,K,L,m,warm,w,d);}std::vector<Work>w;std::vector<int32_t>d;check_threads(c);double wall=timed198(x,aux,models,Q,c,K,L,m,dest,w,d);check_threads(c);validate(dest,x.idx->ntotal);auto hash=packet_sha(dest);
   if(rep==0){first[j]=std::make_unique<Batch>(dest);meters[j]=w;decisions[j]=d;dest.save(path/"raw",false);std::vector<uint64_t>flatwork;for(auto&a:w)flatwork.insert(flatwork.end(),a.begin(),a.end());write_raw(path/"work.u64",flatwork);write_raw(path/"decisions.i32",d);}else{all_same(*first[j],dest);require(w==meters[j]&&d==decisions[j],"three-round work and decisions parity");}
   json rec={{"round",rep},{"wall_seconds",wall},{"qps",qm.n/wall},{"packet_sha256",hash},{"threads",1}};rounds[j].push_back(rec);fresh_json(path/("round"+std::to_string(rep)+".json"),rec);++batches;std::cout<<json{{"dataset",c.at("dataset")},{"window",c.value("window","cal")},{"K",K},{"L",L},{"method",m},{"round",rep},{"qps",qm.n/wall}}.dump()<<std::endl;
  }
  for(size_t j=0;j<n;++j){auto path=root/("k"+std::to_string(K))/(ms[j]+"_L"+std::to_string(L));if(c.value("audit",true))audit198(x,models,Q,c,K,L,ms[j],*first[j],meters[j],decisions[j],path);
   if(ms[j]=="REUSE-SQ"&&c.value("audit",true)){auto it=std::find(ms.begin(),ms.end(),"GT10");require(it!=ms.end(),"actual main SQ control");audit_sq(*x.idx,Q,aux,*first[it-ms.begin()],*first[j],path);}
   std::vector<double>w;for(auto&a:rounds[j])w.push_back(a.at("wall_seconds"));std::sort(w.begin(),w.end());json rec={{"dataset",c.at("dataset")},{"window",c.value("window","cal")},{"method",ms[j]},{"K",K},{"L",L},{"n",qm.n},{"qps",qm.n/w[1]},{"rounds",rounds[j]},{"result_dir",path.string()},{"all_round_bits_and_work_equal",true}};results.push_back(rec);fresh_json(path/"result.json",rec);
  }
  // Verify exact cache optimization and forced-off fallback in every applicable group.
  for(auto pair:{std::pair<std::string,std::string>{"OLD-CACHED384","MODEL1"},{"POLICY-OFF","Q8-B32"}}){auto a=std::find(ms.begin(),ms.end(),pair.first),b=std::find(ms.begin(),ms.end(),pair.second);if(a!=ms.end()&&b!=ms.end())all_same(*first[a-ms.begin()],*first[b-ms.begin()]);}
  ++ordinal;
 }
 json result={{"status","PASS_E198_COMPLETE_WALL_MATRIX"},{"points",results.size()},{"batches",batches},{"results",results},{"native_process_seconds",seconds(start)},{"GT_read",false}};fresh_json(root/"complete.json",result);return result;
}

namespace e199 {
using namespace e198;
constexpr int NS=11, ND=7;
const std::array<const char*,NS> stage_names={"route","main_search","gate_features","gate_predict","candidate_C","student_shortlist","rerank_features","rerank_predict","expansion","merge","query_total_excluding_route"};
std::array<float,22> pre_features(Context&x,const float*q,const RouteData&r,int K,int L){
 std::array<float,22>a{};x.features->project(q,a.data());float norm=0;for(int j=0;j<x.idx->d;++j)norm+=q[j]*q[j];auto p=r.distances;std::sort(p.begin(),p.end());a[16]=norm;a[17]=p[0];a[18]=p[1]-p[0];a[19]=p[2]-p[0];a[20]=K/100.f;a[21]=L/400.f;return a;
}
std::array<float,28> post_features(const std::array<float,22>&p,const std::vector<float>&D){
 std::array<float,28>a{};std::copy(p.begin(),p.end(),a.begin());double mean=std::accumulate(D.begin(),D.end(),0.)/D.size(),var=0;float gap=0;for(size_t j=0;j<D.size();++j){var+=(D[j]-mean)*(D[j]-mean);if(j)gap=std::max(gap,D[j]-D[j-1]);}a[22]=D.front();a[23]=D.back();a[24]=D.back()-D.front();a[25]=mean;a[26]=std::sqrt(var/D.size());a[27]=gap;return a;
}
struct GateTree{Model model;double t75,t90;GateTree(const json&j):model(j.at("model")),t75(j.at("threshold75")),t90(j.at("threshold90")){}bool enabled(const float*f,int target)const{return !model.off&&model.predict(f)>=(target==75?t75:t90);}};
struct GateSet{std::map<std::string,std::unique_ptr<GateTree>>trees;bool full_static=false,nav_static=false;GateSet(const json&j){full_static=j.at("static_full");nav_static=j.at("static_nav");for(auto&v:j.at("gates").items())trees[v.key()]=std::make_unique<GateTree>(v.value());}};
using GateSets=std::map<int,std::unique_ptr<GateSet>>;
GateSets load_gates(const json&c){GateSets a;if(c.contains("gate_files"))for(auto j:c.at("gate_files"))a[j.at("K")]=std::make_unique<GateSet>(read_json(j.at("path")));return a;}
struct Detail199{std::vector<int32_t>main,C,direct;std::vector<float>D,cv;std::vector<Event>events;std::array<float,22>pre{};std::array<float,28>post{};std::array<float,12>cpost{};std::vector<std::array<float,F>>features;};
struct Result199{Outcome outcome;std::array<int32_t,ND>decision{{0,-1,0,0,0,0}};std::array<double,NS>us{};};
struct Runner199{
 Context&x;Student&s;GateSet*g;VisitedTable vt;std::unique_ptr<DistanceComputer>dc;std::vector<Neighbor>ret;
 Runner199(Context&xx,Student&ss,GateSet*gg):x(xx),s(ss),g(gg),vt(xx.idx->ntotal),dc(acsg::storage_distance_computer(xx.idx->storage)){}
 template<bool P>Result199 query(const float*q,const RouteData&r,int K,int L,const std::string&m,Detail199*detail=nullptr,bool all_features=false){
  Result199 z;Clock::time_point begin;if constexpr(P)begin=Clock::now();
  auto measured=[&](int phase,auto fn){if constexpr(P){auto t=Clock::now();fn();z.us[phase]+=seconds(t)*1e6;}else fn();};
  bool Fgate=m.rfind("F-",0)==0,Ngate=m.rfind("N-",0)==0,gated=Fgate||Ngate;
  bool stat=m.find("STATIC")!=std::string::npos,pre=m.find("PRE")!=std::string::npos,late=m.find("LATE")!=std::string::npos,cpost=m.find("CPOST")!=std::string::npos;
  bool force_off=m.find("FORCE-OFF")!=std::string::npos,force_on=m.find("FORCE-ON")!=std::string::npos;
  int target=m.find("75")!=std::string::npos?75:90;bool enabled=true,have_pre=false;std::array<float,22>pf{};std::array<float,28>mf{};
  auto prep_pre=[&](){if(!have_pre){measured(2,[&]{pf=pre_features(x,q,r,K,L);});have_pre=true;}};
  auto evaluate=[&](const float*f,const std::string&kind){measured(3,[&]{require(g,"gates loaded");enabled=g->trees.at((Fgate?"F_":"N_")+kind)->enabled(f,target);});};
  if(gated&&(stat||force_off||force_on)){require(g,"static gates loaded");enabled=force_off?false:force_on?true:Fgate?g->full_static:g->nav_static;}
  if(gated&&pre&&!late){prep_pre();evaluate(pf.data(),"PRE");z.decision[5]=1;}
  std::vector<int32_t>R,C;std::vector<float>D,cv;measured(1,[&]{main_search(x,q,K,L,r,vt,R,D,ret,*dc);});
  if(gated&&!stat&&!force_off&&!force_on&&!cpost&&(!pre||late)){
   prep_pre();if(pre){evaluate(pf.data(),"PRE");z.decision[5]=2;}else{measured(2,[&]{mf=post_features(pf,D);});evaluate(mf.data(),"POST");z.decision[5]=3;}
  }
  bool main_only=m=="MAIN"||(Fgate&&!enabled);
  if(!main_only)measured(4,[&]{candidates(m=="FULL-DIRECT"?*x.reference:*x.post,r,R,*dc,C,cv);});
  std::unique_ptr<Cached>cache;
  if(!main_only&&!C.empty()){
   if(cpost){measured(2,[&]{cache=std::make_unique<Cached>(x,q,r,vt,C,cv,D,K,L,false);});evaluate(cache->gate.data(),"CPOST");z.decision[5]=4;}
   bool action=m!="DIRECT"&&m!="FULL-DIRECT"&&enabled;
   if(action){
    std::vector<int>rank;measured(5,[&]{rank=ranks(cv);if(m!="DIST384"){if(!cache)cache=std::make_unique<Cached>(x,q,r,vt,C,cv,D,K,L,false);if(have_pre){for(int j=0;j<16;++j){cache->shared[24+j]=pf[j];cache->query[j]=pf[j];}}else cache->project_query();}});
    int best=-1;
    if(m=="DIST384")best=rank.front();
    else if(m=="TEACHER384"){
     double high=-1e100;for(size_t j=0;j<rank.size();++j){std::array<float,F>f;measured(6,[&]{f=cache->row(j,rank[j]);});z.decision[4]+=x.idx->acsg.final_graph->K;double value;measured(7,[&]{value=s.t1.predict(f.data());});if(best<0||value>high){best=rank[j];high=value;}++z.decision[3];}
    }else{
     std::vector<int>positions(C.size()),order;std::vector<std::array<double,2>>pred(C.size());
     measured(5,[&]{auto eq=s.encode(cache->query.data());for(size_t j=0;j<rank.size();++j){positions[rank[j]]=j;auto f=cache->row(j,rank[j],false);pred[rank[j]]=s.predict(C[rank[j]],f.data(),eq);}order=rank;std::stable_sort(order.begin(),order.end(),[&](int a,int b){return pred[a][1]>pred[b][1];});});
     if(m=="FAST384")best=order.front();
     else{
      std::vector<int>sl;measured(5,[&]{sl={rank.front()};for(size_t j=0;j<std::min<size_t>(5,order.size());++j)if(std::find(sl.begin(),sl.end(),order[j])==sl.end())sl.push_back(order[j]);std::sort(sl.begin(),sl.end(),[&](int a,int b){return positions[a]<positions[b];});});
      double high=-1e100;for(int pos:sl){std::array<float,F>f;measured(6,[&]{f=cache->row(positions[pos],pos);});z.decision[4]+=x.idx->acsg.final_graph->K;double value;measured(7,[&]{value=s.t1.predict(f.data());});if(best<0||value>high){best=pos;high=value;}++z.decision[3];}
     }
    }
    if(best>=0){z.decision[0]=1;z.decision[1]=C[best];z.decision[2]=384;}
   }
  }
  z.decision[6]=enabled;
  z.outcome.events.reserve(C.size()+(z.decision[0]?384:0));for(size_t j=0;j<C.size();++j)z.outcome.events.push_back({C[j],cv[j],0});z.outcome.work[0]=C.size();z.outcome.work[6]=z.decision[0];
  if(z.decision[0]){auto it=std::find(C.begin(),C.end(),z.decision[1]);int pos=it-C.begin();std::vector<Node>seeds{{cv[pos],uint32_t(pos),C[pos]}};measured(8,[&]{expansion(*dc,*x.idx->acsg.final_graph,vt,C,cv,seeds,false,384,0,z.outcome.events,z.outcome.work);});}
  measured(9,[&]{if(z.outcome.events.empty()){z.outcome.ids=R;z.outcome.values=D;}else merge_heap(R.data(),D.data(),K,z.outcome.events,z.outcome.ids,z.outcome.values);});
  require(z.outcome.work[2]<=384&&z.outcome.work[4]<=64*384,"fixed auxiliary budget");
  if constexpr(P)z.us[10]=seconds(begin)*1e6;
  if(detail){detail->main=R;detail->D=D;detail->C=C;detail->cv=cv;detail->events=z.outcome.events;
   if(all_features){detail->pre=have_pre?pf:pre_features(x,q,r,K,L);detail->post=post_features(detail->pre,D);Cached ca(x,q,r,vt,C,cv,D,K,L);detail->cpost=ca.gate;auto rank=ranks(cv);for(size_t j=0;j<rank.size();++j)detail->features.push_back(ca.row(j,rank[j]));std::vector<Event>direct;for(size_t j=0;j<C.size();++j)direct.push_back({C[j],cv[j],0});std::vector<float>values;merge_heap(R.data(),D.data(),K,direct,detail->direct,values);}
  }
  return z;
 }
};
bool ours(const std::string&m){return m=="ALWAYS"||m=="DIST384"||m=="FAST384"||m=="TEACHER384"||m.rfind("F-",0)==0||m.rfind("N-",0)==0;}
std::string old_method(const std::string&m){return m=="ALWAYS"?"CASCADE384":m;}
}

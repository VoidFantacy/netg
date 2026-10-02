#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
#include <sched.h>

namespace swap36 {
constexpr size_t F=76;
uint64_t hcalls=0,ncalls=0;
std::vector<std::array<int32_t,3>> triples;
std::array<std::array<int32_t,16>,56> next;
void states() {
 for(int a=0;a<8;++a)for(int b=a+1;b<8;++b)for(int c=b+1;c<8;++c)triples.push_back({a,b,c});
 for(int i=0;i<56;++i){next[i][0]=i;size_t pos=1;auto s=triples[i];
  for(int a:s)for(int b=0;b<8;++b)if(std::find(s.begin(),s.end(),b)==s.end()){
   auto t=s;*std::find(t.begin(),t.end(),a)=b;std::sort(t.begin(),t.end());next[i][pos++]=std::find(triples.begin(),triples.end(),t)-triples.begin();}
  require(pos==16,"state graph");
 }
}
struct Pool {std::array<int32_t,8> local;std::array<float,8> distance;uint32_t ndc=0;};
class Router {
 bool count;size_t h;std::unique_ptr<hnswlib::SpaceInterface<float>> space;std::unique_ptr<hnswlib::HierarchicalNSW<float>> g;std::unordered_map<int32_t,int32_t> local;
 public:Router(const json& c,bool counted):count(counted),h(c.at("hub_count")) {
  size_t d=c.at("dim");if(count)space=std::make_unique<CountSpace>(d);else space=std::make_unique<hnswlib::InnerProductSpace>(d);
  g=std::make_unique<hnswlib::HierarchicalNSW<float>>(space.get(),c.at("graph_file").get<std::string>(),false,h);g->setEf(10);
  auto hubs=read_raw<int32_t>(c.at("hub_ids"));auto w=read_raw<float>(c.at("W"));require(hubs.size()==h && w.size()==h*d,"router shape");
  for(size_t j=0;j<h;++j){require(g->getExternalLabel(j)==size_t(hubs[j]),"mapping");require(std::memcmp(g->getDataByInternalId(j),w.data()+j*d,d*4)==0,"profile bytes");local.emplace(hubs[j],j);}
 }
 Pool route(const float* q){uint64_t ct=0;route_counter=count?&ct:nullptr;auto heap=g->searchKnn(q,8);route_counter=nullptr;++hcalls;require(heap.size()==8,"pool size");Pool p;p.ndc=ct;for(size_t j=8;j-->0;){p.local[j]=local.at(heap.top().second);p.distance[j]=heap.top().first;heap.pop();}return p;}
};
struct Features {
 size_t d,h;std::vector<double> projection,hproj;std::vector<float> pairs;
 explicit Features(const json& c):d(c.at("dim")),h(c.at("hub_count")),projection(read_raw<double>(c.at("projection"))),hproj(read_raw<double>(c.at("hub_projection"))),pairs(read_raw<float>(c.at("pair_cosine"))) {
  require(projection.size()==16*d && hproj.size()==h*16 && pairs.size()==h*h,"feature source shape");
 }
 std::array<float,56*F> compute(const float* q,const Pool& p)const {
  std::array<double,16> qp{};double norm=0;for(size_t j=0;j<d;++j)norm+=double(q[j])*q[j];norm=std::sqrt(norm);require(norm>0 && std::isfinite(norm),"query norm");
  for(size_t a=0;a<16;++a){double v=0;for(size_t j=0;j<d;++j)v+=(double(q[j])/norm)*projection[a*d+j];qp[a]=v;}
  std::array<double,8> cos{};for(size_t i=0;i<8;++i)cos[i]=(1.-double(p.distance[i]))/norm;
  std::array<float,56*F> result{};
  for(size_t s=0;s<56;++s){size_t j=s*F;auto t=triples[s];for(int k:t){result[j++]=double(k)/7.;result[j++]=cos[k];result[j++]=cos[k]-cos[0];for(size_t a=0;a<16;++a)result[j++]=qp[a]*hproj[size_t(p.local[k])*16+a];}
   for(int a=0;a<3;++a)for(int b=a+1;b<3;++b)result[j++]=pairs[size_t(p.local[t[a]])*h+p.local[t[b]]];for(double x:qp)result[j++]=x;require(j==(s+1)*F,"feature count");}
  return result;
 }
};
struct Model {
 std::vector<double> mean,scale,b1,b2,b3;std::vector<std::vector<double>> w1,w2,w3;
 explicit Model(const std::string& path){std::ifstream f(path);json c;f>>c;mean=c.at("mean").get<std::vector<double>>();scale=c.at("scale").get<std::vector<double>>();auto p=c.at("parameters");
  w1=p.at("net.0.weight").get<std::vector<std::vector<double>>>();b1=p.at("net.0.bias").get<std::vector<double>>();w2=p.at("net.2.weight").get<std::vector<std::vector<double>>>();b2=p.at("net.2.bias").get<std::vector<double>>();w3=p.at("net.4.weight").get<std::vector<std::vector<double>>>();b3=p.at("net.4.bias").get<std::vector<double>>();
  require(mean.size()==F && scale.size()==F && w1.size()==16 && w1[0].size()==F && w2.size()==16 && w2[0].size()==16 && w3.size()==1 && w3[0].size()==16,"model shape");}
 std::array<double,56> score(const std::array<float,56*F>& x)const {
  std::array<double,56> result{};
  for(size_t s=0;s<56;++s){std::array<double,F> z{};for(size_t j=0;j<F;++j)z[j]=std::clamp((double(x[s*F+j])-mean[j])/scale[j],-8.,8.);
   std::array<double,16> a{},b{};for(size_t j=0;j<16;++j){double v=b1[j];for(size_t k=0;k<F;++k)v+=w1[j][k]*z[k];a[j]=std::max(0.,v);}
   for(size_t j=0;j<16;++j){double v=b2[j];for(size_t k=0;k<16;++k)v+=w2[j][k]*a[k];b[j]=std::max(0.,v);}
   double v=b3[0];for(size_t k=0;k<16;++k)v+=w3[0][k]*b[k];auto t=triples[s];result[s]=v-.25*(t[0]+t[1]+t[2]-3);require(std::isfinite(result[s]),"nonfinite model");}
  return result;
 }
};
uint64_t mix(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}
struct Output {
 Decision dec;Search search;std::array<int32_t,8> pool;std::array<int32_t,4> states{0,0,0,0};std::array<int32_t,3> actions{-1,-1,-1};std::array<double,56> scores{};int32_t length=0;
};
struct Method {std::string name,kind;std::unique_ptr<Model> model;explicit Method(const json& c):name(c.at("name")),kind(c.at("kind")){if(kind=="model")model=std::make_unique<Model>(c.at("model"));}};
struct Engine {
 json c;size_t n,d,h;std::vector<float> queries;std::vector<int64_t> rows;std::vector<int32_t> hubs;Router pc,pp;Policy bc,bp;Features features;
 std::unique_ptr<acsg::IndexACSGFlat> index;std::unique_ptr<NativeWork> wc,wp;std::unique_ptr<Work> reference;
 explicit Engine(const json& config):c(config),n(c.at("num_queries")),d(c.at("dim")),h(c.at("hub_count")),queries(read_raw<float>(c.at("queries_file"))),rows(read_raw<int64_t>(c.at("row_ids"))),hubs(read_raw<int32_t>(c.at("hub_ids"))),pc(c,true),pp(c,false),bc(c.at("policy"),c.at("graph_file"),true,true),bp(c.at("policy"),c.at("graph_file"),false,true),features(c) {
  require(queries.size()==n*d && rows.size()==n && hubs.size()==h,"input shape");index=std::make_unique<acsg::IndexACSGFlat>();index->loadACPG(c.at("index_path").get<std::string>().c_str());
  std::vector<float>().swap(index->acsg.pheromone);std::vector<float>().swap(index->acsg.weight);require(index->d==int(d) && index->metric_type==faiss::METRIC_INNER_PRODUCT,"native metric");index->acsg.search_L=128;
  wc=std::make_unique<NativeWork>(*index,true);wp=std::make_unique<NativeWork>(*index,false);reference=std::make_unique<Work>(*index,true);
 }
 Decision decision(const Pool& pool,int s){Decision out;for(size_t k=0;k<3;++k)out.ids[k]=hubs[pool.local[triples[s][k]]];std::sort(out.ids.begin(),out.ids.end());out.labels=out.ids;out.ndc=pool.ndc;return out;}
 Output one(const Method& m,size_t i,bool counted) {
  const float* q=queries.data()+i*d;Output o;o.pool.fill(-1);
  if(m.kind=="base"){o.dec=(counted?bc:bp).route(q);++hcalls;}
  else {auto p=(counted?pc:pp).route(q);o.pool=p.local;if(m.model)o.scores=m.model->score(features.compute(q,p));int s=0;
   for(int step=0;step<3;++step){int a=0;if(m.kind=="random")a=mix(uint64_t(rows[i])^uint64_t(2026091719)^uint64_t(step)*0xd1b54a32d192ed03ULL)%16;
    else {double best=o.scores[s];for(int j=1;j<16;++j)if(o.scores[next[s][j]]>best+1e-9){best=o.scores[next[s][j]];a=j;}}
    o.actions[step]=a;++o.length;s=next[s][a];o.states[step+1]=s;if(a==0){for(int k=step+2;k<4;++k)o.states[k]=s;break;}}
   o.dec=decision(p,s);
  }
  o.search=(counted?wc:wp)->search(*index,q,o.dec,3);++ncalls;return o;
 }
};
void compare(const std::vector<Output>& a,const std::vector<Output>& b) {
 require(a.size()==b.size(),"parity shape");for(size_t i=0;i<a.size();++i)require(a[i].dec.ids==b[i].dec.ids && a[i].pool==b[i].pool && a[i].states==b[i].states && a[i].actions==b[i].actions && a[i].length==b[i].length && a[i].search.ids==b[i].search.ids && std::memcmp(a[i].search.distances.data(),b[i].search.distances.data(),40)==0,"count/plain output parity");
}
void save(const fs::path& out,const std::vector<Output>& a){fs::create_directories(out);std::vector<int32_t> ids,entries,pool,ss,aa,ll;std::vector<float> distances;std::vector<uint32_t> route,graph;std::vector<double> ff;
 for(auto& o:a){ids.insert(ids.end(),o.search.ids.begin(),o.search.ids.end());distances.insert(distances.end(),o.search.distances.begin(),o.search.distances.end());entries.insert(entries.end(),o.dec.ids.begin(),o.dec.ids.end());pool.insert(pool.end(),o.pool.begin(),o.pool.end());ss.insert(ss.end(),o.states.begin(),o.states.end());aa.insert(aa.end(),o.actions.begin(),o.actions.end());ll.push_back(o.length);route.push_back(o.dec.ndc);graph.push_back(o.search.ndc);ff.insert(ff.end(),o.scores.begin(),o.scores.end());}
 write_raw(out/"ids.i32",ids);write_raw(out/"distances.f32",distances);write_raw(out/"entries.i32",entries);write_raw(out/"pool.i32",pool);write_raw(out/"states.i32",ss);write_raw(out/"actions.i32",aa);write_raw(out/"lengths.i32",ll);write_raw(out/"route_ndc.u32",route);write_raw(out/"graph_ndc.u32",graph);write_raw(out/"scores.f64",ff);
}
int execute(const json& c,const fs::path& out) {
 states();require(!fs::exists(out),"refuse existing output");fs::create_directories(out);require(c.at("threads")==1,"single thread");omp_set_num_threads(1);cpu_set_t cp;CPU_ZERO(&cp);CPU_SET(15,&cp);require(sched_setaffinity(0,sizeof(cp),&cp)==0,"CPU affinity");Engine e(c);write_json(out/"config.json",c);
 if(c.at("mode")=="labels") {
  std::vector<int32_t> pools,ids,entries;std::vector<float> distances,feat,pdist;std::vector<uint32_t> route,ndc;
  for(size_t i=0;i<e.n;++i){const float* q=e.queries.data()+i*e.d;auto p=e.pc.route(q),plain=e.pp.route(q);require(p.local==plain.local && std::memcmp(p.distance.data(),plain.distance.data(),32)==0,"route float bit parity");auto base=e.bc.route(q);++hcalls;auto dec=e.decision(p,0);require(base.ids==dec.ids && base.ndc==p.ndc,"direct3 vs top8 prefix");auto f=e.features.compute(q,p);
   pools.insert(pools.end(),p.local.begin(),p.local.end());pdist.insert(pdist.end(),p.distance.begin(),p.distance.end());feat.insert(feat.end(),f.begin(),f.end());route.push_back(p.ndc);
   for(int s=0;s<56;++s){auto d=e.decision(p,s);auto x=e.wc->search(*e.index,q,d,3);++ncalls;ids.insert(ids.end(),x.ids.begin(),x.ids.end());distances.insert(distances.end(),x.distances.begin(),x.distances.end());entries.insert(entries.end(),d.ids.begin(),d.ids.end());ndc.push_back(x.ndc);
    if(i<16 && (s==0 || s==27 || s==55)){auto y=e.wp->search(*e.index,q,d,3);std::vector<int32_t> given(d.ids.begin(),d.ids.end());auto z=e.reference->run(*e.index,q,given,{0,1,2},3);ncalls+=2;require(x.ids==y.ids && x.ids==z.ids && std::memcmp(x.distances.data(),y.distances.data(),40)==0 && std::memcmp(x.distances.data(),z.distances.data(),40)==0 && x.ndc==z.ndc,"label kernel parity");}}
   if((i+1)%256==0)std::cout<<"LABEL_PROGRESS "<<i+1<<" "<<ncalls<<std::endl;
  }
  write_raw(out/"pool.i32",pools);write_raw(out/"pool_distance.f32",pdist);write_raw(out/"features.f32",feat);write_raw(out/"route_ndc.u32",route);write_raw(out/"ids.i32",ids);write_raw(out/"distances.f32",distances);write_raw(out/"entries.i32",entries);write_raw(out/"graph_ndc.u32",ndc);
  require(ncalls==e.n*56+96,"label budget");
 }else {
  auto methods=c.at("methods").get<std::vector<json>>();std::vector<std::unique_ptr<Method>> policies;std::vector<std::vector<Output>> counted;json stats=json::array();
  for(auto& mc:methods){policies.push_back(std::make_unique<Method>(mc));auto& m=*policies.back();std::vector<Output> a(e.n),b(e.n);for(size_t i=0;i<e.n;++i)a[i]=e.one(m,i,true);for(size_t i=0;i<e.n;++i)b[i]=e.one(m,i,false);compare(a,b);
   for(size_t i=0;i<std::min(e.n,size_t(16));++i){std::vector<int32_t> given(a[i].dec.ids.begin(),a[i].dec.ids.end());auto z=e.reference->run(*e.index,e.queries.data()+i*e.d,given,{0,1,2},3);++ncalls;require(z.ids==a[i].search.ids && std::memcmp(z.distances.data(),a[i].search.distances.data(),40)==0 && z.ndc==a[i].search.ndc,"deployment original kernel parity");}
   save(out/m.name,a);stats.push_back({{"name",m.name},{"kind",m.kind},{"timings",json::array()}});counted.push_back(std::move(a));std::cout<<"COUNT_PARITY_PASS "<<m.name<<std::endl;
  }
  if(c.value("measure_wall",false)){
   std::vector<Output> raw(e.n);for(size_t j=0;j<policies.size();++j){for(size_t i=0;i<e.n;++i)raw[i]=e.one(*policies[j],i,false);compare(counted[j],raw);}
   for(int rep=0;rep<5;++rep)for(size_t pos=0;pos<policies.size();++pos){size_t j=(pos+rep)%policies.size();auto start=Clock::now();for(size_t i=0;i<e.n;++i)raw[i]=e.one(*policies[j],i,false);double wall=std::chrono::duration<double>(Clock::now()-start).count();compare(counted[j],raw);stats[j]["timings"].push_back({{"repeat",rep},{"order_position",pos},{"wall_seconds",wall},{"QPS",e.n/wall}});std::cout<<"WALL "<<rep<<" "<<policies[j]->name<<" "<<wall<<std::endl;}
  }
  write_json(out/"methods.json",stats);require(ncalls==methods.size()*((c.value("measure_wall",false)?8:2)*e.n+std::min(e.n,size_t(16))),"eval budget");
 }
 write_json(out/"complete.json",{{"status","COMPLETE"},{"NSG_calls",ncalls},{"HNSW_calls",hcalls},{"queries",e.n},{"threads",1},{"GT_read",false}});std::cout<<"COMPLETE "<<ncalls<<std::endl;return 0;
}
}
int main(int argc,char** argv){try{require(argc==3,"runner config new_output");std::ifstream f(argv[1]);json c;f>>c;return swap36::execute(c,argv[2]);}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

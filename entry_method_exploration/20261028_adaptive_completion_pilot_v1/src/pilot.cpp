#define E183_EMBED_COMMON
#include "../../20261017_gt10_residual_comprehensive_v1/src/residual_tools.cpp"
#include <faiss/utils/distances.h>

namespace e187 {
using namespace e183;
constexpr size_t NF=10;
struct Backend {
 size_t N,d,nlist=1024,M=16,sub;int metric;
 std::vector<float> cent,book;std::vector<int32_t> ids,id_region;std::vector<uint64_t> offsets;
 std::vector<uint8_t> codes;json models;
 Backend(const json& c,bool weights=true):N(c.at("base").at("n")),d(c.at("base").at("d")),sub(d/M),metric(c.at("metric_id")){
  fs::path p=c.at("backend");cent=read_raw<float>((p/"centroids.f32").string());book=read_raw<float>((p/"codebooks.f32").string());
  ids=read_raw<int32_t>((p/"region_ids.i32").string());id_region=read_raw<int32_t>((p/"id_region.i32").string());
  offsets=read_raw<uint64_t>((p/"offsets.u64").string());codes=read_raw<uint8_t>((p/"codes.u8").string());
  require(cent.size()==nlist*d&&book.size()==M*256*sub&&ids.size()==N&&id_region.size()==N&&offsets.size()==nlist+1&&codes.size()==N*M,"backend exact layout");
  require(offsets[0]==0&&offsets.back()==N,"backend offsets domain");
  if(weights)models=read_json(p/"models.json");
 }
 float score(const float* q,const float* x,size_t dim)const{return metric==1?faiss::fvec_L2sqr(q,x,dim):-faiss::fvec_inner_product(q,x,dim);}
 std::vector<std::pair<float,int>> coarse(const float* q)const{
  std::vector<std::pair<float,int>> s(nlist);for(size_t r=0;r<nlist;++r)s[r]={score(q,cent.data()+r*d,d),int(r)};
  std::partial_sort(s.begin(),s.begin()+8,s.end());s.resize(8);return s;
 }
 std::array<double,NF> features(const float* q,const std::vector<std::pair<float,int>>& s,size_t rank,
       const int32_t* R,const float* D,size_t K,bool useR)const{
  std::array<double,NF> x{};int r=s[rank].second;double scale=std::max(1e-6,std::abs(double(s[0].first)));
  double norm=0;for(size_t j=0;j<d;++j)norm+=double(q[j])*q[j];
  x[0]=double(rank)/7;x[1]=(s[rank].first-s[0].first)/scale;
  x[2]=std::log1p(double(offsets[r+1]-offsets[r]))/std::log1p(double(N));x[3]=std::sqrt(norm);x[4]=(s[7].first-s[0].first)/scale;
  if(useR){double count=0,top=0,sum=0;for(size_t j=0;j<K;++j)if(id_region[R[j]]==r){++count;top+=j<std::min<size_t>(10,K);sum+=D[j];}
   double z=std::max(1e-6,std::abs(double(D[K-1])));x[5]=count/K;x[6]=top/std::min<size_t>(10,K);
   x[7]=count?(sum/count-D[K-1])/z:0;x[8]=(D[K-1]-D[0])/z;x[9]=(D[K-1]-s[rank].first)/z;}
  return x;
 }
 double predict(const std::string& key,const std::array<double,NF>& x)const{
  const auto& m=models.at(key);double v=m.at("intercept");size_t nf=m.at("n_features");
  for(size_t j=0;j<nf;++j)v+=(x[j]-m.at("mean")[j].get<double>())/m.at("scale")[j].get<double>()*m.at("coef")[j].get<double>();
  return std::max(0.,v);
 }
 std::array<int,2> select(const float* q,const int32_t* R,const float* D,size_t K,const std::string& method)const{
  auto s=coarse(q);if(method=="REG-NN")return {{s[0].second,s[1].second}};
  std::vector<std::pair<double,size_t>> ranks;for(size_t k=0;k<8;++k){auto x=features(q,s,k,R,D,K,method=="REG-R");ranks.emplace_back(-predict(method,x),k);}
  std::sort(ranks.begin(),ranks.end());return {{s[ranks[0].second].second,s[ranks[1].second].second}};
 }
 struct Approx {float distance;uint64_t arrival;int32_t id;};
 static bool approx_less(const Approx& a,const Approx& b){return a.distance<b.distance||(a.distance==b.distance&&a.arrival<b.arrival);}
 struct Less {bool operator()(const Approx& a,const Approx& b)const{return approx_less(a,b);}};
 std::vector<int32_t> candidates(const float* q,const int32_t* R,size_t K,const std::array<int,2>& regions,
       uint64_t& scanned,bool oracle=false)const{
  float lut[16][256];for(size_t m=0;m<M;++m)for(size_t z=0;z<256;++z)lut[m][z]=score(q+m*sub,book.data()+(m*256+z)*sub,sub);
  std::vector<int32_t> sorted(R,R+K);std::sort(sorted.begin(),sorted.end());uint64_t arrival=0;
  std::priority_queue<Approx,std::vector<Approx>,Less> heap;std::vector<Approx> all;
  for(int r:regions)for(size_t t=offsets[r];t<offsets[r+1];++t,++arrival){++scanned;int32_t id=ids[t];if(std::binary_search(sorted.begin(),sorted.end(),id))continue;
   float v=0;for(size_t m=0;m<M;++m)v+=lut[m][codes[t*M+m]];Approx z{v,arrival,id};
   if(oracle)all.push_back(z);else if(heap.size()<96)heap.push(z);else if(approx_less(z,heap.top())){heap.pop();heap.push(z);}}
  if(oracle){std::sort(all.begin(),all.end(),approx_less);if(all.size()>96)all.resize(96);}else {while(!heap.empty()){all.push_back(heap.top());heap.pop();}std::sort(all.begin(),all.end(),approx_less);}
  std::vector<int32_t> out;for(const auto& v:all)out.push_back(v.id);return out;
 }
 size_t bytes()const{return cent.size()*4+book.size()*4+ids.size()*4+id_region.size()*4+offsets.size()*8+codes.size();}
};
struct Stats {uint64_t scanned=0,scored=0,probed=0;};
void merge(faiss::DistanceComputer& dc,size_t K,int32_t* R,float* D,const std::vector<int32_t>& C,bool oracle=false){
 using Item=Posting::Record;std::vector<Item> out;for(size_t j=0;j<K;++j)out.push_back({R[j],D[j],uint32_t(j),false});
 if(oracle){for(size_t j=0;j<C.size();++j)out.push_back({C[j],dc(C[j]),uint32_t(K+j),false});std::stable_sort(out.begin(),out.end(),Posting::better);out.resize(K);}
 else {std::make_heap(out.begin(),out.end(),Posting::better);for(size_t j=0;j<C.size();++j){float value=dc(C[j]);if(value<out[0].distance){std::pop_heap(out.begin(),out.end(),Posting::better);out.back()={C[j],value,uint32_t(K+j),false};std::push_heap(out.begin(),out.end(),Posting::better);}}std::sort(out.begin(),out.end(),Posting::better);}
 for(size_t j=0;j<K;++j){R[j]=out[j].id;D[j]=out[j].distance;}
}
void run(acsg::IndexACSGFlat& idx,const std::vector<float>& q,int L,const std::string& method,Router& router,Posting& post,Backend& aux,Batch& b,Stats& stats){
 idx.acsg.search_L=L;std::vector<std::vector<acsg::EnterPoint>> eps(b.n);
 for(size_t i=0;i<b.n;++i){auto r=router.route(q.data()+i*idx.d);for(int j=0;j<3;++j){b.entries[3*i+j]=r.ids[j];b.profile_distances[3*i+j]=r.distances[j];eps[i].emplace_back(r.ids[j],1.f);}}
 faiss::VisitedTable vt(idx.ntotal);std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx.storage));std::vector<acsg::Neighbor> ret;std::vector<faiss::idx_t> ids(b.k);
 for(size_t i=0;i<b.n;++i){const float* qi=q.data()+i*idx.d;dc->set_query(qi);vt.advance();idx.acsg.search_new(*dc,b.k,ids.data(),b.distances.data()+i*b.k,vt,2,eps[i],&ret);
  if(method=="B32")exp180::cap::apply(*dc,*idx.acsg.final_graph,vt,{{b.entries[3*i],b.entries[3*i+1],b.entries[3*i+2]}},b.k,ids.data(),b.distances.data()+i*b.k,post);
  if(method.rfind("REG-",0)==0){std::vector<int32_t> current(b.k);for(size_t j=0;j<b.k;++j)current[j]=ids[j];
   auto regions=aux.select(qi,current.data(),b.distances.data()+i*b.k,b.k,method);auto cand=aux.candidates(qi,current.data(),b.k,regions,stats.scanned);
   stats.scored+=cand.size();stats.probed+=2;merge(*dc,b.k,current.data(),b.distances.data()+i*b.k,cand);for(size_t j=0;j<b.k;++j)ids[j]=current[j];}
  for(size_t j=0;j<b.k;++j)b.ids[i*b.k+j]=ids[j];
 }
}
__attribute__((noinline)) double timed(acsg::IndexACSGFlat& idx,const std::vector<float>& q,int L,const std::string& method,Router& r,Posting& post,Backend& aux,Batch& target,Stats& st){
 auto start=Clock::now();{Batch out(target.n,target.k);run(idx,q,L,method,r,post,aux,out,st);copy_packet(out,target);asm volatile("" : : "g"(out.ids.data()),"g"(target.ids.data()) : "memory");}return seconds(start);
}
json features_mode(const json& c){
 auto start=Clock::now();Backend aux(c,false);Matrix qmat(c.at("train_queries"));auto q=qmat.copy();size_t n=qmat.n;fs::path td=c.at("teacher_dir"),root=c.at("backend");
 auto ids=read_raw<int32_t>((td/"raw/ids.i32").string());auto dist=read_raw<float>((td/"raw/distances.f32").string());require(ids.size()==n*100&&dist.size()==n*100,"train packets");
 std::vector<double> f(n*8*NF);std::vector<int32_t> regions(n*8);
 for(size_t i=0;i<n;++i){const float* qi=q.data()+i*aux.d;auto s=aux.coarse(qi);for(size_t rank=0;rank<8;++rank){auto x=aux.features(qi,s,rank,ids.data()+i*100,dist.data()+i*100,100,true);regions[i*8+rank]=s[rank].second;std::copy(x.begin(),x.end(),f.begin()+(i*8+rank)*NF);}}
 write_raw(root/"features.f64",f);write_raw(root/"training_regions.i32",regions);
 return {{"status","PASS_E187_TRAIN_FEATURES"},{"n",n},{"features",NF},{"regions",8},{"seconds",seconds(start)},{"test_or_GT_read",false}};
}
json benchmark(const json& c,bool qualify){
 check_threads(c);const auto start=Clock::now();fs::path root=c.at("output_dir");fresh_dir(root);fresh_json(root/"config.json",c);
 json binding;auto idx=load_index(c,binding);Matrix qm(c.at("queries"));auto q=qm.copy();size_t n=qm.n;Router router(c.at("router"),idx->d,idx->ntotal);Posting post(c.at("table"),idx->ntotal);Backend aux(c);
 fresh_json(root/"environment.json",{{"threads",process_threads()},{"cpu",15},{"binding",binding},{"backend_resident_bytes",aux.bytes()},
  {"timer","complete Batch allocate/init + route/main/completion + six-array copy + normal destruction"},{"startup_seconds",seconds(start)}});
 std::vector<int> grid=c.at("main_L");std::set<int> cl;for(int L:c.at("completion_L"))cl.insert(L);
 json results=json::array(),progress=json::array();size_t ordinal=0,batches=0;int repeats=qualify?1:3;
 for(int L:grid){std::vector<std::string> methods={"GT10"};if(cl.count(L))for(std::string s:{"B32","REG-NN","REG-Q","REG-R"})methods.push_back(s);
  std::vector<std::unique_ptr<Batch>> first(methods.size());std::vector<json> rr(methods.size(),json::array());Batch archive(n,100);std::vector<Stats> stats(methods.size());
  for(int rep=0;rep<repeats;++rep)for(size_t off=0;off<methods.size();++off){size_t mi=(ordinal+rep+off)%methods.size();auto method=methods[mi];check_threads(c);
   fs::path point=root/(method+"_L"+std::to_string(L));
   if(rep==0){Batch warm(std::min<size_t>(n,256),100);Stats st;run(*idx,q,L,method,router,post,aux,warm,st);}
   Stats st;double wall=timed(*idx,q,L,method,router,post,aux,archive,st);++batches;check_threads(c);validate(archive,idx->ntotal);
   auto digest=packet_sha(archive);if(rep==0){first[mi]=std::make_unique<Batch>(archive);archive.save(point/"raw",false);stats[mi]=st;}else all_same(*first[mi],archive);
   json r={{"round",rep},{"wall_seconds",wall},{"qps",n/wall},{"packet_sha256",digest},{"threads",process_threads()},{"scanned_codes",st.scanned},{"extra_exact_scores",st.scored},{"probed_regions",st.probed}};
   if(rep)require(digest==rr[mi][0].at("packet_sha256"),"round bits/SHA stable");rr[mi].push_back(r);fresh_json(point/("round"+std::to_string(rep)+".json"),r);
   json event={{"dataset",c.at("dataset")},{"method",method},{"K",100},{"L",L},{"round",rep},{"qps",n/wall}};progress.push_back(event);write_json(root/"progress.json",progress);std::cout<<event.dump()<<std::endl;
  }
  if(cl.count(L)){
   Method bm;bm.route=&router;bm.family="POST";bm.table=&post;audit_merge(*idx,q,*first[0],*first[1],post);
   std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx->storage));
   for(size_t mi=2;mi<methods.size();++mi)for(size_t i=0;i<n;++i){const float* qi=q.data()+i*idx->d;auto& main=*first[0];std::vector<int32_t> ids(main.ids.begin()+i*100,main.ids.begin()+(i+1)*100);std::vector<float> dist(main.distances.begin()+i*100,main.distances.begin()+(i+1)*100);
    dc->set_query(qi);auto regions=aux.select(qi,ids.data(),dist.data(),100,methods[mi]);uint64_t scans=0;auto cand=aux.candidates(qi,ids.data(),100,regions,scans,true);merge(*dc,100,ids.data(),dist.data(),cand,true);
    for(size_t j=0;j<100;++j)require(ids[j]==first[mi]->ids[i*100+j]&&equal_float(dist[j],first[mi]->distances[i*100+j]),"region exhaustive-PQ/full-sort merge oracle");}
  }
  for(size_t mi=0;mi<methods.size();++mi){std::vector<double> walls;for(auto r:rr[mi])walls.push_back(r.at("wall_seconds"));std::sort(walls.begin(),walls.end());
   fs::path point=root/(methods[mi]+"_L"+std::to_string(L));json r={{"status","PASS_E187_POINT"},{"dataset",c.at("dataset")},{"method",methods[mi]},{"K",100},{"L",L},{"n",n},
    {"qps",n/walls[walls.size()/2]},{"rounds",rr[mi]},{"timed_output_retained",true},{"all_round_bits_equal",true},{"merge_oracle_passed",true},
    {"scanned_codes_per_query",double(stats[mi].scanned)/n},{"extra_exact_scores_per_query",double(stats[mi].scored)/n},{"result_dir",point.string()}};
   fresh_json(point/"result.json",r);results.push_back(r);}
  ++ordinal;
 }
 json result={{"status",qualify?"PASS_E187_QUALIFICATION":"PASS_E187_FORMAL"},{"dataset",c.at("dataset")},{"points",results.size()},{"batches",batches},{"n",n},
  {"results",results},{"outer_seconds",seconds(start)},{"evaluation_GT_read",false},{"threads",1},{"cpu",15},{"actual_timed_packets_saved",true}};fresh_json(root/"complete.json",result);return result;
}
}
int main(int argc,char** argv){try{using namespace e187;require(argc==3,"mode config");auto c=read_json(argv[2]);std::string mode=argv[1];json r;
 if(mode=="features")r=features_mode(c);else r=benchmark(c,mode=="qualification");std::cout<<r.dump()<<std::endl;return 0;
}catch(const std::exception& e){std::cerr<<"FATAL E187 "<<e.what()<<std::endl;return 2;}}

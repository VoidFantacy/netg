#include "search_core.hpp"

struct Encoder{
 std::string family;size_t d,r;std::vector<float> U,V,q0,hidden,z;
 Encoder(const json& c,size_t dim):family(c["family"]),d(dim),r(c.value("rank",16)),q0(d),hidden(r),z(d){
  if(family=="QLinear"||family=="QMLP"){
   U=read_raw<float>(c["U"].get<std::string>());V=read_raw<float>(c["V"].get<std::string>());
   require(U.size()==d*r&&V.size()==r*d,"encoder shape");
  }
 }
 const float* encode(const float* query){
  std::copy(query,query+d,q0.begin());normalize(q0.data(),d);z=q0;
  if(family=="QLinear"||family=="QMLP"){
   for(size_t j=0;j<r;++j){float s=0;for(size_t k=0;k<d;++k)s+=V[j*d+k]*q0[k];hidden[j]=family=="QMLP"?std::max(0.f,s):s;}
   for(size_t k=0;k<d;++k){float s=0;for(size_t j=0;j<r;++j)s+=U[k*r+j]*hidden[j];z[k]+=s;}
  }
  for(float v:z)require(std::isfinite(v),"finite encoder");return z.data();
 }
};
int main(int argc,char**argv){try{
 require(argc==3,"quality config new_output");threads();auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"preserve quality output");fs::create_directories(out);write_json(out/"config.json",c);
 auto started=Clock::now();size_t d=c["dimension"],h=c["hub_count"],n=0;std::vector<float> q;
 for(auto split:c["splits"]){auto v=read_raw<float>(split["queries"].get<std::string>());require(v.size()==split["n"].get<size_t>()*d,"split shape");n+=split["n"].get<size_t>();q.insert(q.end(),v.begin(),v.end());}
 require(n==2560,"frozen fit+cal size");
 auto idx=load_nsg(c["index"]);require(idx->ntotal==c["base_n"]&&idx->d==d&&idx->metric_type==0,"fixed graph");Searcher search(*idx);
 auto anchor_cfg=c["routers"][0];Router anchor(anchor_cfg,d,anchor_cfg["graph"].get<std::string>());json details=json::array();uint64_t route_calls=0,exact_distances=0;int builds=0;
 for(auto m:c["models"]){
  std::string family=m["family"];Encoder encoder(m,d);auto rc=anchor_cfg;rc["name"]=family;rc["W"]=m["W"];
  fs::path graph_path=anchor_cfg["graph"].get<std::string>();double build_seconds=0;
  if(family=="WFree"){
   graph_path=out/"WFree.hnsw";auto weights=read_raw<float>(m["W"].get<std::string>());require(weights.size()==h*d,"WFree shape");
   auto t=Clock::now();HNSW graph(&anchor.space,h,anchor.graph->M_,anchor.graph->ef_construction_,20260920);
   for(size_t j=0;j<h;++j)graph.addPoint(weights.data()+j*d,anchor.ids[j]);graph.saveIndex(graph_path.string());build_seconds=seconds(t);++builds;
  }
  Router router(rc,d,graph_path);router.counting(true);std::vector<int32_t> ann(n*3),exact(n*3);std::vector<float> encoded(n*d);std::vector<uint64_t> routing_ndc(n);
  auto fn=router.space.get_dist_func();auto param=router.space.get_dist_func_param();
  for(size_t i=0;i<n;++i){
   auto z=encoder.encode(q.data()+i*d);std::copy(z,z+d,encoded.begin()+i*d);
   auto entries=router.route(z);++route_calls;routing_ndc[i]=router.counter.n;std::copy(entries.begin(),entries.end(),ann.begin()+i*3);
   std::vector<std::pair<float,int32_t>> ranked;ranked.reserve(h);
   for(size_t j=0;j<h;++j)ranked.emplace_back(fn(z,router.w.data()+j*d,param),router.ids[j]);
   std::partial_sort(ranked.begin(),ranked.begin()+3,ranked.end());exact_distances+=h;
   std::array<int32_t,3> selected{ranked[0].second,ranked[1].second,ranked[2].second};std::sort(selected.begin(),selected.end());std::copy(selected.begin(),selected.end(),exact.begin()+i*3);
  }
  write_raw(out/(family+".encoded.f32"),encoded);write_raw(out/(family+".route_ndc.u64"),routing_ndc);
  for(std::string route:{"ANN","Exact"}){
   auto& entries=route=="ANN"?ann:exact;auto sub=out/(family+route);fs::create_directories(sub);write_raw(sub/"entries.i32",entries);
   for(int K:{1,100}){
    std::vector<int32_t> ids(n*K);std::vector<float> distances(n*K);std::vector<uint64_t> ndc(n);
    for(size_t i=0;i<n;++i){
     std::array<int32_t,3> e;std::copy_n(entries.data()+i*3,3,e.begin());search.run(q.data()+i*d,e,K);ndc[i]=search.dc.count;
     for(int j=0;j<K;++j){ids[i*K+j]=search.ids[j];distances[i*K+j]=search.distances[j];}
    }
    write_raw(sub/("k"+std::to_string(K)+".ids.i32"),ids);write_raw(sub/("k"+std::to_string(K)+".distances.f32"),distances);write_raw(sub/("k"+std::to_string(K)+".ndc.u64"),ndc);
   }
   write_json(sub/"complete.json",{{"status","PASS"},{"method",family+route},{"n",n},{"K",{1,100}},{"L",128},{"main_search_calls",n*2},{"formal",false}});
  }
  details.push_back({{"family",family},{"graph",graph_path.string()},{"graph_build_seconds",build_seconds},{"M",router.graph->M_},{"ef_construction",router.graph->ef_construction_},{"ef",router.graph->ef_},{"graph_seed",family=="WFree"?20260920:0},{"graph_seed_note",family=="WFree"?"new frozen seed":"inherited original graph"}});
  resources(out);threads();std::cout<<family<<" complete; main calls "<<search.calls<<std::endl;
 }
 require(search.calls==n*4*2*2&&builds==1,"quality accounting");struct rusage ru;getrusage(RUSAGE_SELF,&ru);require(ru.ru_maxrss<=40LL*1024*1024,"40GiB cap");
 write_json(out/"complete.json",{{"status","PASS"},{"n",n},{"main_search_calls",search.calls},{"router_calls",route_calls},{"exact_profile_distances",exact_distances},{"graph_builds",builds},{"models",details},{"wall_seconds",seconds(started)},{"maxrss_kib",ru.ru_maxrss},{"threads",process_threads()},{"formal",false},{"note","Encodings/routes cached for quality diagnostics only; not an online timing result."}});
 return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

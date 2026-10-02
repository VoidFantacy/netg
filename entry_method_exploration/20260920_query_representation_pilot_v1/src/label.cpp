#define main unused_inherited_main
#include "common/evaluate.cpp"
#undef main
#include "kernels.hpp"
#include <unordered_set>

struct ActualCount:CountDC{
 explicit ActualCount(faiss::DistanceComputer* p):CountDC(p){}
 void distances_batch_4(faiss::idx_t a,faiss::idx_t b,faiss::idx_t c,faiss::idx_t d,float& x,float& y,float& z,float& w)override{
  for(auto id:{a,b,c,d}){if(count<3)first[count]=id;++count;}
  dc->distances_batch_4(a,b,c,d,x,y,z,w);
 }
};
struct Searcher{
 acsg::IndexACSGFlat& idx;std::vector<uint8_t> spans;ResearchKernel kernel;
 ActualCount dc;faiss::VisitedTable vt;std::vector<acsg::EnterPoint> ep;
 std::array<faiss::idx_t,100> ids;std::array<float,100> distances;uint64_t calls=0;
 explicit Searcher(acsg::IndexACSGFlat& i):idx(i),spans(make_spans(*i.acsg.final_graph,i.ntotal)),
  kernel(*i.acsg.final_graph,spans,i.ntotal),dc(acsg::storage_distance_computer(i.storage)),vt(i.ntotal){ep.reserve(3);}
 void run(const float* q,const std::array<int32_t,3>& entries,int K){
  ep.clear();for(int e:entries)ep.emplace_back(e,1);vt.advance();dc.set_query(q);
  kernel.search<true,false,true>(dc,vt,ep,128,K,ids.data(),distances.data());++calls;
  for(int j=0;j<3;++j)require(dc.first[j]==entries[j],"entry order injection");
  std::set<faiss::idx_t> unique;
  for(int j=0;j<K;++j){require(ids[j]>=0&&ids[j]<idx.ntotal&&std::isfinite(distances[j]),"valid result");unique.insert(ids[j]);}
  require(unique.size()==size_t(K),"unique result IDs");
 }
};
static void guard(const json& c,const fs::path& out){
 threads();resources(out);struct statvfs v;require(statvfs(out.c_str(),&v)==0,"statvfs");
 require(uint64_t(v.f_bavail)*v.f_frsize>=4ULL*1024*1024*1024,"4GiB disk floor");
 struct rusage r;getrusage(RUSAGE_SELF,&r);require(r.ru_maxrss<=40LL*1024*1024,"40GiB search RSS cap");
 require(double(std::time(nullptr))<c["deadline_unix"].get<double>(),"preparation deadline");
}
int main(int argc,char**argv){try{
 require(argc==4,"label parity|labels config new_output");threads();std::string mode=argv[1];require(mode=="parity"||mode=="labels","mode");
 auto c=read_json(argv[2]);fs::path out=argv[3];require(!fs::exists(out),"preserve output");fs::create_directories(out);write_json(out/"config.json",c);
 auto start=Clock::now();size_t n=c["n"],d=c["dimension"],h=c["hub_count"];
 auto q=read_raw<float>(c["queries"].get<std::string>());auto gt=read_raw<int64_t>(c["gt"].get<std::string>());auto hubs=read_raw<int32_t>(c["hub_ids"].get<std::string>());
 require(q.size()==n*d&&gt.size()==n*100&&hubs.size()==h,"input shape");
 auto idx=load_nsg(c["index"]);require(idx->ntotal==c["base_n"]&&idx->d==d&&idx->metric_type==0,"frozen graph identity");idx->acsg.search_L=128;
 auto ac=c["routers"][0],bc=c["routers"][1];Router anchor(ac,d,ac["graph"].get<std::string>()),alternate(bc,d,bc["graph"].get<std::string>());
 require(anchor.ids==hubs&&alternate.ids==hubs,"shared hub mapping");Searcher search(*idx);guard(c,out);
 std::map<int32_t,int32_t> local;for(size_t j=0;j<h;++j)local[hubs[j]]=j;
 std::vector<int32_t> candidates(n*8,-1),triples(n*56*3,-1),baseline(n*2,-1),anchor_entries(n*3,-1),other_entries(n*3,-1),unit_entries(n*3,-1);
 uint64_t routes=0,unit_differences=0;auto score_fn=anchor.space.get_dist_func();auto score_param=anchor.space.get_dist_func_param();
 std::vector<size_t> rows;if(mode=="parity")for(int i:c["parity_rows"])rows.push_back(i);else{rows.resize(n);std::iota(rows.begin(),rows.end(),0);}
 for(size_t i:rows){
  auto a=anchor.route(q.data()+i*d),b=alternate.route(q.data()+i*d);routes+=2;
  std::vector<float> un(q.begin()+i*d,q.begin()+(i+1)*d);normalize(un.data(),d);auto u=anchor.route(un.data());++routes;
  unit_differences+=(a!=u);std::copy(a.begin(),a.end(),anchor_entries.begin()+i*3);std::copy(b.begin(),b.end(),other_entries.begin()+i*3);std::copy(u.begin(),u.end(),unit_entries.begin()+i*3);
  std::set<int32_t> chosen;for(int v:a)chosen.insert(local.at(v));for(int v:b)chosen.insert(local.at(v));
  std::vector<std::pair<float,int32_t>> ranked;ranked.reserve(h);
  for(size_t j=0;j<h;++j)ranked.emplace_back(score_fn(q.data()+i*d,anchor.w.data()+j*d,score_param),j);
  std::sort(ranked.begin(),ranked.end(),[&](auto x,auto y){return x.first<y.first||(x.first==y.first&&hubs[x.second]<hubs[y.second]);});
  for(auto x:ranked){if(chosen.size()==8)break;chosen.insert(x.second);}
  require(chosen.size()==8,"C8");std::vector<int32_t> cc(chosen.begin(),chosen.end());std::sort(cc.begin(),cc.end(),[&](int x,int y){return hubs[x]<hubs[y];});
  std::copy(cc.begin(),cc.end(),candidates.begin()+i*8);int t=0;
  for(int j=0;j<8;++j)for(int k=j+1;k<8;++k)for(int l=k+1;l<8;++l){
   std::array<int32_t,3> slots{cc[j],cc[k],cc[l]},real{hubs[cc[j]],hubs[cc[k]],hubs[cc[l]]};
   std::copy(slots.begin(),slots.end(),triples.begin()+(i*56+t)*3);
   if(real==a)baseline[i*2]=t;if(real==b)baseline[i*2+1]=t;++t;
  }
  require(t==56&&baseline[i*2]>=0&&baseline[i*2+1]>=0,"both actual baselines included");
 }
 uint64_t references=0;json parity_failures=json::array();json kernel_failures=json::array();
 if(mode=="parity"){
  Worker reference(*idx);auto dummy_space=make_space(0,d);CountParam dummy{dummy_space->get_dist_func(),dummy_space->get_dist_func_param(),0};
  for(int K:{1,100}){
   std::vector<int32_t> all_ids,ref_ids;std::vector<float> all_dist,ref_dist;std::vector<uint64_t> all_ndc,ref_ndc;
   for(size_t i:rows){
    std::array<int32_t,3> p;std::copy_n(anchor_entries.data()+i*3,3,p.begin());auto original=p;
    std::vector<int32_t> expected;std::vector<float> expected_d;uint64_t expected_ndc=0;int permutation=0;
    do{
     search.run(q.data()+i*d,p,K);std::vector<int32_t> got(search.ids.begin(),search.ids.begin()+K);std::vector<float> dist(search.distances.begin(),search.distances.begin()+K);
     if(!permutation){expected=got;expected_d=dist;expected_ndc=search.dc.count;}
     else if(got!=expected||memcmp(dist.data(),expected_d.data(),K*4)||search.dc.count!=expected_ndc)parity_failures.push_back({{"row",i},{"K",K},{"permutation",permutation},{"entries",p}});
     all_ids.insert(all_ids.end(),got.begin(),got.end());all_dist.insert(all_dist.end(),dist.begin(),dist.end());all_ndc.push_back(search.dc.count);++permutation;
    }while(std::next_permutation(p.begin(),p.end()));require(permutation==6,"all permutations");
    Batch batch(1,K);std::vector<float> one(q.begin()+i*d,q.begin()+(i+1)*d);anchor.counting(true);
    reference.run(ac["name"],&anchor,nullptr,dummy,one,d,batch,true);++references;++routes;anchor.counting(false);
    if(batch.ids!=expected||memcmp(batch.dist.data(),expected_d.data(),K*4)||batch.graph_ndc[0]!=expected_ndc)kernel_failures.push_back({{"row",i},{"K",K}});
    require(std::equal(original.begin(),original.end(),batch.entries.begin()),"reference same entry input");
    ref_ids.insert(ref_ids.end(),batch.ids.begin(),batch.ids.end());ref_dist.insert(ref_dist.end(),batch.dist.begin(),batch.dist.end());ref_ndc.push_back(batch.graph_ndc[0]);
   }
   write_raw(out/("k"+std::to_string(K)+".ids.i32"),all_ids);write_raw(out/("k"+std::to_string(K)+".distances.f32"),all_dist);write_raw(out/("k"+std::to_string(K)+".ndc.u64"),all_ndc);
   write_raw(out/("reference.k"+std::to_string(K)+".ids.i32"),ref_ids);write_raw(out/("reference.k"+std::to_string(K)+".distances.f32"),ref_dist);write_raw(out/("reference.k"+std::to_string(K)+".ndc.u64"),ref_ndc);
  }
 }else{
  write_raw(out/"candidates.i32",candidates);write_raw(out/"triples.i32",triples);write_raw(out/"baseline_slots.i32",baseline);
  write_raw(out/"anchor_entries.i32",anchor_entries);write_raw(out/"alternate_entries.i32",other_entries);write_raw(out/"unit_identity_entries.i32",unit_entries);
  for(int K:{1,100}){
   std::vector<int32_t> ids(n*56*K);std::vector<float> distances(n*56*K);std::vector<uint64_t> ndc(n*56);std::vector<uint8_t> hits(n*56);
   auto begin=Clock::now();
   for(size_t i=0;i<n;++i){
    std::unordered_set<int64_t> truth(gt.begin()+i*100,gt.begin()+i*100+K);
    for(int t=0;t<56;++t){
     size_t at=i*56+t;std::array<int32_t,3> entries;for(int j=0;j<3;++j)entries[j]=hubs[triples[at*3+j]];
     search.run(q.data()+i*d,entries,K);ndc[at]=search.dc.count;
     for(int j=0;j<K;++j){ids[at*K+j]=search.ids[j];distances[at*K+j]=search.distances[j];hits[at]+=truth.count(search.ids[j]);}
    }
    if((i+1)%128==0){guard(c,out);auto elapsed=seconds(begin);double remaining=(n-i-1)*elapsed/(i+1);
     require(double(std::time(nullptr))+remaining<c["deadline_unix"].get<double>(),"refuse stage beyond deadline estimate");
     json progress={{"K",K},{"rows",i+1},{"main_search_calls",search.calls},{"router_calls",routes},{"seconds",seconds(start)}};write_json(out/"progress.json",progress);std::cout<<progress.dump()<<std::endl;}
   }
   auto prefix="k"+std::to_string(K);write_raw(out/(prefix+".ids.i32"),ids);write_raw(out/(prefix+".distances.f32"),distances);write_raw(out/(prefix+".ndc.u64"),ndc);write_raw(out/(prefix+".hits.u8"),hits);
  }
 }
 guard(c,out);struct rusage ru;getrusage(RUSAGE_SELF,&ru);std::string status=parity_failures.empty()&&kernel_failures.empty()?"PASS":"STOP_PARITY";
 json result={{"status",status},{"mode",mode},{"dataset",c["dataset"]},{"split",c["split"]},{"n",n},{"rows_executed",rows.size()},{"main_search_calls",search.calls+references},{"reference_calls",references},{"router_calls",routes},{"raw_unit_route_differences",unit_differences},{"order_failures",parity_failures},{"kernel_failures",kernel_failures},{"wall_seconds",seconds(start)},{"maxrss_kib",ru.ru_maxrss},{"threads",process_threads()},{"cpu",15},{"K",{1,100}},{"L",128}};
 write_json(out/"complete.json",result);std::cout<<result.dump()<<std::endl;return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

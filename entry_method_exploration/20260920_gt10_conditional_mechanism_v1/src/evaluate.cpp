#include "search_core.hpp"

int main(int argc,char**argv){try{
 require(argc==3,"mechanism config new_output");threads();auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"preserve mechanism output");fs::create_directories(out);write_json(out/"config.json",c);
 const auto start=Clock::now();size_t n=c["n"],d=c["dimension"],h=c["H"];require(c["threads"]==1&&(n==16||n==4096),"fixed query/thread contract");
 auto q=read_raw<float>(c["queries"].get<std::string>());require(q.size()==n*d,"query dimensions");for(float x:q)require(std::isfinite(x),"finite query");
 auto hubids=read_raw<int32_t>(c["hub_ids"].get<std::string>());require(hubids.size()==h&&std::is_sorted(hubids.begin(),hubids.end()),"real hub identity");
 auto idx=load_nsg(c["index"]);require(idx->d==d&&idx->ntotal==c["base_n"]&&idx->metric_type==0,"frozen graph/base/raw-IP");
 Fvecs base(c["base"].get<std::string>());require(base.d==d&&base.n==idx->ntotal,"GT base shape");std::vector<float>checkbase(d);
 for(size_t j=0;j<16;++j){size_t id=j*(base.n/16);idx->storage->reconstruct(id,checkbase.data());require(!memcmp(checkbase.data(),base.row(id),4*d),"NSG embedded base sample parity");}
 Searcher search(*idx);std::unique_ptr<faiss::DistanceComputer>plain(acsg::storage_distance_computer(idx->storage));faiss::VisitedTable plainvt(idx->ntotal);
 std::vector<acsg::EnterPoint>ep;ep.reserve(3);std::array<faiss::idx_t,100>plainids;std::array<float,100>plaindist;
 hnswlib::InnerProductSpace space(d);auto fn=space.get_dist_func();auto param=space.get_dist_func_param();
 std::ifstream bf("/proc/sys/kernel/random/boot_id");std::string boot;std::getline(bf,boot);
 uint64_t maincalls=0,anncalls=0,exactdist=0;int done=0;
 for(auto method:c["methods"]){
  std::string name=method["name"],route=method["route"];fs::path sub=out/name;fs::create_directories(sub);
  auto w=read_raw<float>(method["W"].get<std::string>());require(w.size()==h*d,"profile shape");for(float x:w)require(std::isfinite(x),"finite profile");
  std::unique_ptr<Router>router;if(route=="ann"){router=std::make_unique<Router>(method,d,method["graph"].get<std::string>());require(router->graph->M_==16&&router->graph->ef_construction_==200&&router->graph->ef_==10,"original small graph contract");}
  std::vector<int32_t>entries(n*3);std::vector<uint64_t>routecounts(n);std::vector<float>margins(n);
  for(size_t i=0;i<n;++i){const float*query=q.data()+i*d;std::array<int32_t,3>selected;
   if(router){router->counting(true);selected=router->route(query);routecounts[i]=router->counter.n;++anncalls;router->counting(false);require(selected==router->route(query),"ANN count/plain entry equality");++anncalls;}
   else{require(route=="exact","legal routing kind");std::vector<std::pair<float,int32_t>>ranked;ranked.reserve(h);
    for(size_t j=0;j<h;++j)ranked.emplace_back(fn(query,w.data()+j*d,param),hubids[j]);exactdist+=h;
    std::partial_sort(ranked.begin(),ranked.begin()+4,ranked.end());selected={ranked[0].second,ranked[1].second,ranked[2].second};std::sort(selected.begin(),selected.end());margins[i]=ranked[3].first-ranked[2].first;routecounts[i]=h;
   }
   require(selected[0]<selected[1]&&selected[1]<selected[2],"three unique ascending entries");std::copy(selected.begin(),selected.end(),entries.begin()+i*3);
  }
  write_raw(sub/"entries.i32",entries);write_raw(sub/"route_ndc.u64",routecounts);if(!router)write_raw(sub/"exact_margin.f32",margins);
  for(int K:{1,100}){
   std::vector<int32_t>ids(n*K);std::vector<float>dist(n*K);std::vector<uint64_t>ndc(n);
   for(size_t i=0;i<n;++i){std::array<int32_t,3>e;std::copy_n(entries.data()+i*3,3,e.begin());auto query=q.data()+i*d;
    search.run(query,e,K);++maincalls;ndc[i]=search.dc.count;
    for(int j=0;j<K;++j){ids[i*K+j]=search.ids[j];dist[i*K+j]=search.distances[j];}
    ep.clear();for(int id:e)ep.emplace_back(id,1);plainvt.advance();plain->set_query(query);
    search.kernel.search<true,false,true>(*plain,plainvt,ep,128,K,plainids.data(),plaindist.data());++maincalls;
    for(int j=0;j<K;++j)require(plainids[j]==search.ids[j]&&!memcmp(&plaindist[j],&search.distances[j],4),"full plain/count ID and distance parity");
   }
   auto prefix="k"+std::to_string(K);write_raw(sub/(prefix+".ids.i32"),ids);write_raw(sub/(prefix+".distances.f32"),dist);write_raw(sub/(prefix+".ndc.u64"),ndc);
   if(router){auto old=fs::path(c["reference"].get<std::string>())/prefix/(c["reference_method"].get<std::string>()+"_L128");
    auto oi=read_raw<int32_t>(old/"ids.i32");auto od=read_raw<float>(old/"distances.f32");auto oe=read_raw<int32_t>(old/"entry_ids.i32");auto on=read_raw<uint64_t>(old/"graph_ndc.u64");auto orn=read_raw<uint64_t>(old/"route_ndc.u64");
    require(oi.size()==4096ULL*K&&od.size()==oi.size()&&oe.size()==4096*3&&on.size()==4096&&orn.size()==4096,"E105 reference shapes");
    require(!memcmp(ids.data(),oi.data(),n*K*4)&&!memcmp(dist.data(),od.data(),n*K*4)&&!memcmp(entries.data(),oe.data(),n*3*4)&&!memcmp(ndc.data(),on.data(),n*8)&&!memcmp(routecounts.data(),orn.data(),n*8),"E105 default full output and NDC restoration");
   }
  }
  ++done;threads();resources(out);struct rusage ru;getrusage(RUSAGE_SELF,&ru);require(ru.ru_maxrss<=40LL*1024*1024,"40GiB RSS cap");
  require(maincalls<=c["max_search_calls"].get<uint64_t>()&&seconds(start)<c["seconds_cap"].get<double>(),"search resources");
  struct statvfs disk;require(statvfs(out.c_str(),&disk)==0&&uint64_t(disk.f_bavail)*disk.f_frsize>=4ULL*1024*1024*1024,"4GiB disk floor");
  write_json(sub/"complete.json",{{"status","PASS"},{"method",name},{"n",n},{"K",{1,100}},{"L",128},{"search_calls",n*4},{"plain_count_bit_parity",true},{"formal",false}});
  write_json(out/"progress.json",{{"methods",done},{"search_calls",maincalls},{"seconds",seconds(start)}});std::cout<<name<<" complete, calls="<<maincalls<<std::endl;
 }
 require(maincalls==n*c["methods"].size()*4&&maincalls==2*search.calls,"exact search accounting");struct rusage ru;getrusage(RUSAGE_SELF,&ru);
 write_json(out/"complete.json",{{"status","PASS"},{"n",n},{"methods",done},{"search_calls",maincalls},{"ann_calls",anncalls},{"exact_profile_distances",exactdist},{"graph_builds",0},{"seconds",seconds(start)},{"maxrss_kib",ru.ru_maxrss},{"threads",process_threads()},{"cpu",15},{"boot_id",boot},{"formal",false},{"timing_note","Cached routes for mechanism diagnostics; not online QPS."}});
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

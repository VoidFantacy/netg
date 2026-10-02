#include "search_core.hpp"
#include <tuple>
int main(int argc,char** argv){try{
 require(argc==3,"proxy config output");threads();auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"preserve output");fs::create_directories(out);write_json(out/"config.json",c);
 auto started=Clock::now();size_t n=c["n"],d=c["dimension"],h=c["H"];bool smoke=c["smoke"];require(c["threads"]==1&&((smoke&&n==16)||(!smoke&&n==2048)),"fixed query/thread contract");
 auto q=read_raw<float>(c["queries"].get<std::string>()),mean=read_raw<float>(c["target_mean"].get<std::string>()),u=read_raw<float>(c["unit_W"].get<std::string>()),p=read_raw<float>(c["GT10_W"].get<std::string>());
 auto mass=read_raw<int32_t>(c["coverage_counts"].get<std::string>()),hids=read_raw<int32_t>(c["hub_ids"].get<std::string>());
 require(q.size()==2048*d&&mean.size()==q.size()&&mass.size()==2048*h&&hids.size()==h&&u.size()==h*d&&p.size()==u.size()&&std::is_sorted(hids.begin(),hids.end()),"original fit and model dimensions");
 for(float x:q)require(std::isfinite(x),"finite original query");for(float x:mean)require(std::isfinite(x),"finite target mean");
 for(size_t i=0;i<2048;++i){int sum=0;for(size_t j=0;j<h;++j){int v=mass[i*h+j];require(v>=0&&v<=10,"integer target counts");sum+=v;}require(sum==10,"target mass conserved");}
 auto idx=load_nsg(c["index"]);require(idx->d==d&&idx->ntotal==c["base_n"]&&idx->metric_type==0,"fixed original raw-IP NSG");idx->acsg.search_L=128;
 Fvecs base(c["base"]);require(base.d==d&&base.n==idx->ntotal,"base identity shape");std::vector<float> sample(d);for(size_t i=0;i<16;++i){size_t j=i*(base.n/16);idx->storage->reconstruct(j,sample.data());require(!memcmp(sample.data(),base.row(j),d*4),"embedded base bytes");}
 auto spans=make_spans(*idx->acsg.final_graph,idx->ntotal);ResearchKernel kernel(*idx->acsg.final_graph,spans,idx->ntotal);
 ActualCount count(acsg::storage_distance_computer(idx->storage)),legacy(acsg::storage_distance_computer(idx->storage));std::unique_ptr<faiss::DistanceComputer> plain(acsg::storage_distance_computer(idx->storage));faiss::VisitedTable vt(idx->ntotal),pvt(idx->ntotal),lvt(idx->ntotal);
 std::vector<acsg::EnterPoint> ep;ep.reserve(3);std::vector<acsg::Neighbor> scratch;scratch.reserve(129);std::array<faiss::idx_t,100> ids,other;std::array<float,100> distances,od;
 hnswlib::InnerProductSpace space(d);auto fn=space.get_dist_func();auto param=space.get_dist_func_param();uint64_t calls=0,profile_distances=0,aux_distances=0;
 auto check=[&](){threads();require(std::time(nullptr)<c["deadline_unix"].get<double>()&&seconds(started)<c["seconds_cap"].get<double>(),"deadline");};
 for(std::string name:c["methods"]){
  check();require(name=="GT10Exact"||name=="UnitHubExact"||name=="TargetMean"||name=="Coverage","frozen route");fs::path sub=out/name;fs::create_directories(sub);std::vector<int32_t> entries(n*3);std::vector<float> coverage(n),affinity(n);
  for(size_t i=0;i<n;++i){
   const float* query=(name=="TargetMean"?mean.data():q.data())+i*d;const float* w=(name=="GT10Exact"||name=="Coverage")?p.data():u.data();std::vector<std::tuple<int,float,int32_t,size_t>> rank;rank.reserve(h);
   for(size_t j=0;j<h;++j)rank.emplace_back(name=="Coverage"?-mass[i*h+j]:0,fn(query,w+j*d,param),hids[j],j);profile_distances+=h;std::partial_sort(rank.begin(),rank.begin()+3,rank.end());
   int covered=0;double average=0;for(int j=0;j<3;++j){size_t col=std::get<3>(rank[j]);entries[i*3+j]=hids[col];covered+=mass[i*h+col];average+=1.-fn(mean.data()+i*d,u.data()+col*d,param);++aux_distances;}
   coverage[i]=covered/10.f;affinity[i]=average/3;std::sort(entries.begin()+i*3,entries.begin()+i*3+3);
   if(name=="Coverage"){std::vector<int> v(mass.begin()+i*h,mass.begin()+(i+1)*h);std::partial_sort(v.begin(),v.begin()+3,v.end(),std::greater<int>());require(covered==v[0]+v[1]+v[2],"exact optimal coverage");}
  }
  write_raw(sub/"entries.i32",entries);write_raw(sub/"proxy_GT10_coverage.f32",coverage);write_raw(sub/"proxy_mean_affinity.f32",affinity);
  for(int K:{1,100}){
   std::vector<int32_t> output(n*K);std::vector<float> dist(n*K);std::vector<uint64_t> ndc(n);
   for(size_t i=0;i<n;++i){if(i%128==0)check();ep.clear();for(int j=0;j<3;++j)ep.emplace_back(entries[i*3+j],1);const float* raw_query=q.data()+i*d;vt.advance();count.set_query(raw_query);kernel.search<true,false,true>(count,vt,ep,128,K,ids.data(),distances.data());++calls;ndc[i]=count.count;
    for(int j=0;j<3;++j)require(count.first[j]==entries[i*3+j],"ordered real IDs");std::set<int32_t> unique;
    for(int j=0;j<K;++j){require(ids[j]>=0&&ids[j]<idx->ntotal&&std::isfinite(distances[j]),"valid result");unique.insert(ids[j]);output[i*K+j]=ids[j];dist[i*K+j]=distances[j];}require(unique.size()==size_t(K),"unique result");
    pvt.advance();plain->set_query(raw_query);kernel.search<true,false,true>(*plain,pvt,ep,128,K,other.data(),od.data());++calls;require(!memcmp(ids.data(),other.data(),K*sizeof(faiss::idx_t))&&!memcmp(distances.data(),od.data(),K*4),"count/plain bit parity");
    if(smoke){lvt.advance();legacy.set_query(raw_query);idx->acsg.search_new(legacy,K,other.data(),od.data(),lvt,2,ep,&scratch);++calls;require(!memcmp(ids.data(),other.data(),K*sizeof(faiss::idx_t))&&!memcmp(distances.data(),od.data(),K*4)&&legacy.count==count.count,"linked E99 parity");}
   }
   write_raw(sub/("k"+std::to_string(K)+".ids.i32"),output);write_raw(sub/("k"+std::to_string(K)+".distances.f32"),dist);write_raw(sub/("k"+std::to_string(K)+".ndc.u64"),ndc);std::cout<<name<<" K="<<K<<" calls="<<calls<<std::endl;
  }
  check();struct rusage ru;getrusage(RUSAGE_SELF,&ru);require(ru.ru_maxrss<=40LL*1024*1024&&calls<=c["max_search_calls"].get<uint64_t>(),"resource/call cap");write_json(sub/"complete.json",{{"status","PASS"},{"n",n},{"method",name},{"K",{1,100}},{"L",128},{"count_plain_bit_parity",true},{"linked_E99_checked",smoke},{"formal_QPS",false},{"privileged_fit_proxy",name=="TargetMean"||name=="Coverage"}});
 }
 require(calls==c["expected_search_calls"].get<uint64_t>(),"exact calls");struct rusage ru;getrusage(RUSAGE_SELF,&ru);write_json(out/"complete.json",{{"status","PASS"},{"NSG_calls",calls},{"exact_profile_distances",profile_distances},{"auxiliary_profile_distances",aux_distances},{"seconds",seconds(started)},{"maxrss_kib",ru.ru_maxrss},{"threads",process_threads()},{"cpu",sched_getcpu()},{"formal_QPS",false}});return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

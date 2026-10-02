#include "/data/netg/ACSG/entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/src/search_core.hpp"
#include "comparison_recorder.hpp"
#include "trace_kernel.hpp"
uint64_t diagnostic_calls=0;fs::path diagnostic_output;
int main(int argc,char**argv){try{
 threads();require(argc==3,"config output");auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"preserve output");fs::create_directories(out);diagnostic_output=out;auto started=Clock::now();
 int n=c["n"],d=c["dimension"];require(n==2048&&omp_get_max_threads()==1&&sched_getcpu()==15,"fixed fit and CPU");auto q=read_raw<float>(c["queries"]);auto epids=read_raw<int32_t>(c["entries"]);require(q.size()==size_t(n)*d&&epids.size()==size_t(n)*2*3,"input shape");
 auto idx=load_nsg(c["index"]);require(idx->d==d&&idx->ntotal==c["base_n"]&&idx->metric_type==0,"fixed raw IP index");auto spans=make_spans(*idx->acsg.final_graph,idx->ntotal);ResearchKernel control(*idx->acsg.final_graph,spans,idx->ntotal);TraceKernel trace(*idx->acsg.final_graph,spans,idx->ntotal);ActualCount dc(acsg::storage_distance_computer(idx->storage));faiss::VisitedTable vt(idx->ntotal);
 std::map<int,std::vector<int32_t>> expected_ids,result_ids;std::map<int,std::vector<float>> expected_dist,result_dist;std::map<int,std::vector<uint64_t>> expected_ndc,result_ndc;
 for(int K:{1,100}){std::string k=std::to_string(K);expected_ids[K]=read_raw<int32_t>(c["expected"][k]["ids"]);expected_dist[K]=read_raw<float>(c["expected"][k]["distances"]);expected_ndc[K]=read_raw<uint64_t>(c["expected"][k]["ndc"]);require(expected_ids[K].size()==size_t(n)*2*K&&expected_dist[K].size()==size_t(n)*2*K&&expected_ndc[K].size()==size_t(n)*2,"cached shape");}
 std::vector<uint64_t> offsets{0},keys,totals,valids;std::vector<uint8_t> codes;std::array<faiss::idx_t,100> ids;std::array<float,100> distances;uint64_t& calls=diagnostic_calls;
 auto check_time=[&](){require(std::time(nullptr)<c["deadline_unix"].get<double>()&&seconds(started)<c["seconds_cap"].get<double>(),"time bound");struct rusage ru;getrusage(RUSAGE_SELF,&ru);require(ru.ru_maxrss<40LL*1024*1024,"RSS bound");require(keys.size()<=c["max_pairs"].get<uint64_t>(),"pair cap");};
 for(int i=0;i<n;++i){if(i%16==0){check_time();write_json(out/"progress.json",{{"query",i},{"n",n},{"NSG_calls",calls},{"pairs",keys.size()},{"seconds",seconds(started)}});}
  for(int action=0;action<2;++action){size_t row=size_t(i)*2+action;std::vector<acsg::EnterPoint> entries;for(int j=0;j<3;++j)entries.emplace_back(epids[row*3+j],1);std::vector<std::pair<uint64_t,uint8_t>> previous;uint64_t previous_total=0,previous_valid=0;
   for(int K:{1,100}){
    for(int traced=0;traced<2;++traced){vt.advance();dc.set_query(q.data()+size_t(i)*d);trace.recorder.clear();
     if(traced)trace.search<true,false,true>(dc,vt,entries,128,K,ids.data(),distances.data());else control.search<true,false,true>(dc,vt,entries,128,K,ids.data(),distances.data());++calls;
     require(dc.count==expected_ndc[K][row],"NDC restored to historical action");for(int j=0;j<K;++j){require(ids[j]==expected_ids[K][row*K+j],"historical ID parity");require(std::memcmp(&distances[j],&expected_dist[K][row*K+j],sizeof(float))==0,"historical distance bits");}
     if(traced){for(int j=0;j<K;++j){result_ids[K].push_back(ids[j]);result_dist[K].push_back(distances[j]);}result_ndc[K].push_back(dc.count);
      auto current=trace.recorder.sorted();if(K==1){previous=std::move(current);previous_total=trace.recorder.total_calls;previous_valid=trace.recorder.valid_calls;}else{require(current==previous&&trace.recorder.total_calls==previous_total&&trace.recorder.valid_calls==previous_valid,"K1 K100 comparison parity");for(auto item:current){keys.push_back(item.first);codes.push_back(item.second);}offsets.push_back(keys.size());totals.push_back(previous_total);valids.push_back(previous_valid);}
     }
    }
   }
  }
 }
 check_time();require(calls==uint64_t(n)*2*2*2&&offsets.size()==size_t(n)*2+1&&keys.size()==codes.size(),"complete call count");
 write_raw(out/"pair_offsets.u64",offsets);write_raw(out/"pair_keys.u64",keys);write_raw(out/"pair_codes.u8",codes);write_raw(out/"total_comparisons.u64",totals);write_raw(out/"valid_comparisons.u64",valids);
 for(int K:{1,100}){auto k="k"+std::to_string(K);write_raw(out/(k+".ids.i32"),result_ids[K]);write_raw(out/(k+".distances.f32"),result_dist[K]);write_raw(out/(k+".ndc.u64"),result_ndc[K]);}
 struct rusage ru;getrusage(RUSAGE_SELF,&ru);write_json(out/"complete.json",{{"status","PASS"},{"n",n},{"actions",2},{"NSG_calls",calls},{"ANN_calls",0},{"unique_query_action_pairs",keys.size()},{"all_historical_outputs_restored",true},{"trace_control_parity",true},{"K1_K100_comparison_parity",true},{"threads",omp_get_max_threads()},{"cpu",sched_getcpu()},{"seconds",seconds(started)},{"maxrss_kib",ru.ru_maxrss}});return 0;
}catch(const std::exception&e){if(!diagnostic_output.empty())write_json(diagnostic_output/"error.json",{{"error",e.what()},{"NSG_calls",diagnostic_calls}});std::cerr<<e.what()<<std::endl;return 1;}}

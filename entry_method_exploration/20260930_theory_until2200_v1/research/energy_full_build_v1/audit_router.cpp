#define main unused_common_main
#include "../hybrid_temperature_factorial_v1/src/common/evaluate.cpp"
#undef main
int main(int argc,char**argv){try{
 require(argc==3,"audit config new_output");threads();auto c=read_json(argv[1]);require(!fs::exists(argv[2]),"fresh audit output");size_t d=c["dimension"];
 Router r(c["model"],d,c["model"]["graph"].get<std::string>());auto& g=*r.graph;
 auto q=read_raw<float>(c["queries"].get<std::string>());require(q.size()==20000*d,"fit shape");
 std::map<size_t,size_t> slot;for(size_t i=0;i<r.ids.size();++i)slot[r.ids[i]]=i;
 json returned=json::array();double maxerr=0;uint64_t total_ndc=0;
 for(size_t i=0;i<256;++i){r.counting(false);auto a=g.searchKnn(q.data()+i*d,3);r.counting(true);r.counter.n=0;auto b=g.searchKnn(q.data()+i*d,3);
  require(a.size()==3&&b.size()==3&&r.counter.n>0,"three returns and positive NDC");total_ndc+=r.counter.n;json row=json::array();
  while(!a.empty()){auto x=a.top(),y=b.top();require(x.second==y.second&&!memcmp(&x.first,&y.first,4),"plain/count ID and score bits");
   require(slot.count(x.second),"returned real hub");size_t s=slot.at(x.second);double dot=0,absdot=0;
   for(size_t j=0;j<d;++j){double z=double(q[i*d+j])*r.w[s*d+j];dot+=z;absdot+=std::abs(z);}
   double err=std::abs((1.-dot)-double(x.first));double bound=8.*std::numeric_limits<float>::epsilon()*(1.+double(d)*absdot);
   require(err<=bound,"returned score float64 check");maxerr=std::max(maxerr,err);row.push_back({{"id",x.second},{"distance",x.first},{"float64_distance",1.-dot},{"round_bound",bound}});a.pop();b.pop();}
  returned.push_back(row);
 }
 threads();write_json(argv[2],{{"status","PASS"},{"query_pairs",256},{"new_ANN_calls",512},{"threads",process_threads()},{"cpu",15},
  {"plain_count_bit_parity",true},{"all_node_vector_label_checks",r.ids.size()},{"total_counted_NDC",total_ndc},{"max_score_error",maxerr},{"returns",returned}});return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

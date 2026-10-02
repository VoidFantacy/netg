#define main unused_common_main
#include "../hybrid_temperature_factorial_v1/src/common/evaluate.cpp"
#undef main
int main(int argc,char**argv){try{
 require(argc==3,"audit_router config new_output");threads();auto c=read_json(argv[1]);require(!fs::exists(argv[2]),"fresh audit output");size_t d=c["dimension"];
 auto q=read_raw<float>(c["queries"].get<std::string>());require(q.size()==20000*d,"fit shape");json records=json::object();
 for(auto m:c["methods"]){Router router(m,d,m["graph"].get<std::string>());auto&g=*router.graph;uint64_t lists=0,edges=0;
  for(size_t i=0;i<g.cur_element_count;++i){for(int l=0;l<=g.element_levels_[i];++l){auto*x=g.get_linklist_at_level(i,l);size_t n=g.getListCount(x);auto*p=(hnswlib::tableint*)(x+1);for(size_t j=0;j<n;++j)require(p[j]<g.cur_element_count,"edge bounds");++lists;edges+=n;}}
  std::vector<uint64_t> ndc;for(int i=0;i<256;++i){router.counting(false);auto a=g.searchKnn(q.data()+i*d,3);router.counting(true);router.counter.n=0;auto b=g.searchKnn(q.data()+i*d,3);require(a.size()==3&&b.size()==3&&router.counter.n>0,"three routes with count");ndc.push_back(router.counter.n);
   while(!a.empty()){auto x=a.top(),y=b.top();require(x.second==y.second&&!memcmp(&x.first,&y.first,4),"plain/count score bits");a.pop();b.pop();}}
  records[m["name"].get<std::string>()]={{"status","PASS"},{"query_pairs",256},{"new_ANN_calls",512},{"lists",lists},{"edges",edges},{"route_ndc",ndc}};
 }
 write_json(argv[2],{{"status","PASS"},{"methods",records},{"new_ANN_calls",1024},{"threads",process_threads()},{"cpu",15}});return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

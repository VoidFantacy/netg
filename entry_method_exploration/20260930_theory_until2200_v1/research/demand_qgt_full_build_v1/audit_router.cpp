#define main unused_common_main
#include "../hybrid_temperature_factorial_v1/src/common/evaluate.cpp"
#undef main
int main(int argc,char**argv){try{
 require(argc==3,"audit_router config new_output");threads();auto c=read_json(argv[1]);require(!fs::exists(argv[2]),"fresh audit output");size_t d=c["dimension"];
 Router old(c["old"],d,c["old"]["graph"].get<std::string>()),fresh(c["new"],d,c["new"]["graph"].get<std::string>());
 require(old.ids==fresh.ids&&old.w.size()==fresh.w.size()&&!memcmp(old.w.data(),fresh.w.data(),4*old.w.size()),"all H/W bytes");
 auto&a=*old.graph;auto&b=*fresh.graph;require(a.cur_element_count==b.cur_element_count&&a.maxlevel_==b.maxlevel_&&a.enterpoint_node_==b.enterpoint_node_,"levels and root");
 uint64_t lists=0,edges=0;
 for(size_t i=0;i<a.cur_element_count;++i){require(a.element_levels_[i]==b.element_levels_[i]&&a.getExternalLabel(i)==b.getExternalLabel(i),"node levels labels");
  require(!memcmp(a.getDataByInternalId(i),b.getDataByInternalId(i),4*d),"node vectors");
  for(int l=0;l<=a.element_levels_[i];++l){auto*x=a.get_linklist_at_level(i,l);auto*y=b.get_linklist_at_level(i,l);size_t n=a.getListCount(x);require(n==b.getListCount(y)&&!memcmp(x+1,y+1,n*sizeof(hnswlib::tableint)),"ordered edges");++lists;edges+=n;}}
 old.counting(true);fresh.counting(true);auto q=read_raw<float>(c["queries"].get<std::string>());require(q.size()==20000*d,"fit shape");
 for(int i=0;i<256;++i){old.counter.n=0;fresh.counter.n=0;
  auto ah=a.searchKnn(q.data()+i*d,3),bh=b.searchKnn(q.data()+i*d,3);require(old.counter.n==fresh.counter.n&&ah.size()==3&&bh.size()==3,"route NDC and count");
  while(!ah.empty()){auto av=ah.top(),bv=bh.top();require(av.second==bv.second&&!memcmp(&av.first,&bv.first,4),"score bits");ah.pop();bh.pop();}}
 write_json(argv[2],{{"status","PASS"},{"query_pairs",256},{"new_ANN_calls",512},{"lists",lists},{"edges",edges},{"threads",process_threads()},{"cpu",15}});return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

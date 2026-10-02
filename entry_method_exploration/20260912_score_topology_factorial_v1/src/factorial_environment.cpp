#include "/data/netg/ACSG/entry_method_exploration/20260912_exact_feedback_cache_v1/src/cache_environment.cpp"

namespace e48 {
uint64_t installations=0;
struct Row {size_t node;int level;std::vector<hnswlib::tableint> neighbors;};
void install(e37::Environment& e,const int32_t* values,size_t length) {
 require(bool(e.graph) && length>=4,"missing graph or topology header");
 require(values[0]==int32_t(e.h) && values[1]==int32_t(e.d),"topology shape mismatch");
 require(values[2]==int32_t(e.graph->enterpoint_node_) && values[3]==e.graph->maxlevel_,"topology entry or maxlevel mismatch");
 size_t cursor=4;std::vector<Row> parsed;
 // Complete validation precedes every mutation.
 for(size_t node=0;node<e.h;++node) {
  require(cursor+2<=length,"truncated topology node");
  require(values[cursor++]==e.mapping[node],"topology external ID mismatch");
  int level=values[cursor++];require(level==e.graph->element_levels_[node],"topology node levels mismatch");
  for(int l=0;l<=level;++l) {
   require(cursor<length,"truncated topology degree");int degree=values[cursor++];size_t capacity=l?e.graph->maxM_:e.graph->maxM0_;
   require(degree>=0 && size_t(degree)<=capacity && cursor+size_t(degree)<=length,"invalid topology degree");
   Row row{node,l,{}};std::set<int32_t> seen;
   for(int j=0;j<degree;++j) {
    int32_t id=values[cursor++];require(id>=0 && size_t(id)<e.h && size_t(id)!=node && seen.insert(id).second,"invalid topology neighbor");row.neighbors.push_back(hnswlib::tableint(id));
   }
   parsed.push_back(std::move(row));
  }
 }
 require(cursor==length,"trailing topology data");
 for(const auto& row:parsed) {
  auto* links=e.graph->get_linklist_at_level(row.node,row.level);auto* adj=reinterpret_cast<hnswlib::tableint*>(links+1);
  size_t capacity=row.level?e.graph->maxM_:e.graph->maxM0_;std::fill(adj,adj+capacity,hnswlib::tableint(0));
  e.graph->setListCount(links,row.neighbors.size());std::copy(row.neighbors.begin(),row.neighbors.end(),adj);
 }
 e.inspect();require(e.topology.size()==length && std::equal(e.topology.begin(),e.topology.end(),values),"installed topology identity mismatch");++installations;
}
}
extern "C" {
int e48_install(void* ptr,const int32_t* values,size_t length) {
 try {e48::install(*static_cast<e37::Environment*>(ptr),values,length);return 0;}
 catch(const std::exception& ex){e37::error=ex.what();return -1;}
}
uint64_t e48_installations(){return e48::installations;}
int e48_verify_vectors(void* ptr,const float* values,size_t count) {
 try {
  auto& e=*static_cast<e37::Environment*>(ptr);require(bool(e.graph) && count==e.h*e.d,"vector identity shape");
  for(size_t i=0;i<e.h;++i)require(std::memcmp(e.graph->getDataByInternalId(i),values+i*e.d,e.d*sizeof(float))==0,"actual graph scoring vectors differ");
  return 0;
 }catch(const std::exception& ex){e37::error=ex.what();return -1;}
}
}

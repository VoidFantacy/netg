#include "/data/netg/ACSG/entry_method_exploration/20260912_offline_profile_rl_v1/src/environment.cpp"

extern "C" {
int e46_route(void* ptr,const int32_t* rows,size_t count) {
 try {
  auto& e=*static_cast<e37::Environment*>(ptr);
  require(bool(e.graph),"route-only requires graph");
  require(e.hcalls+count<=e.c.at("native_hnsw_cap").get<uint64_t>(),"HNSW call cap");
  for(size_t i=0;i<count;++i)require(rows[i]>=0 && size_t(rows[i])<e.n,"route query row invalid");
  e.entries.resize(count*3);e.route_ndc.resize(count);
  for(size_t i=0;i<count;++i) {
   auto dec=e.route(*e.graph,e.q.data()+size_t(rows[i])*e.d,true);
   std::copy(dec.ids.begin(),dec.ids.end(),e.entries.begin()+3*i);e.route_ndc[i]=dec.ndc;
  }
  return 0;
 } catch(const std::exception& ex) {e37::error=ex.what();return -1;}
}
int e46_search(void* ptr,const int32_t* rows,const int32_t* entries,size_t count) {
 try {
  auto& e=*static_cast<e37::Environment*>(ptr);
  require(e.calls+count<=e.cap,"explicit NSG call cap");
  // Validate the entire batch before executing any search.
  for(size_t i=0;i<count;++i) {
   require(rows[i]>=0 && size_t(rows[i])<e.n,"explicit query row invalid");
   for(size_t j=0;j<3;++j) {
    int32_t id=entries[3*i+j];require(id>=0 && id<e.index->ntotal,"explicit entry out of range");
    require(std::find(e.mapping.begin(),e.mapping.end(),id)!=e.mapping.end(),"explicit entry not in frozen H");
    if(j)require(entries[3*i+j-1]<id,"explicit entries must be sorted and distinct");
   }
  }
  e.ids.resize(count*K);e.distances.resize(count*K);e.graph_ndc.resize(count);e.index->acsg.search_L=128;
  for(size_t i=0;i<count;++i) {
   Decision dec;for(size_t j=0;j<3;++j)dec.ids[j]=entries[3*i+j];dec.labels=dec.ids;dec.ndc=0;
   auto s=e.worker->search(*e.index,e.q.data()+size_t(rows[i])*e.d,dec,3);++e.calls;
   std::copy(s.ids.begin(),s.ids.end(),e.ids.begin()+K*i);std::copy(s.distances.begin(),s.distances.end(),e.distances.begin()+K*i);e.graph_ndc[i]=s.ndc;
  }
  return 0;
 } catch(const std::exception& ex) {e37::error=ex.what();return -1;}
}
}

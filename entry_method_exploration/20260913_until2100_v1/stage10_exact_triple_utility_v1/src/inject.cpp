#include "/data/netg/ACSG/entry_method_exploration/20260912_exact_feedback_cache_v1/src/cache_environment.cpp"

// Uses the same supplied triples for plain and independent reference searches.
// The whole batch is validated before a call, including an invalid last row.
extern "C" int e69_search(void* ptr,const int32_t* rows,const int32_t* entries,size_t count,int reference) {
 try {
  auto& e=*static_cast<e37::Environment*>(ptr);
  require(reference==0 || reference==1,"invalid search mode");
  require(e.calls+count<=e.cap,"injected NSG call cap");
  for(size_t i=0;i<count;++i) {
   require(rows[i]>=0 && size_t(rows[i])<e.n,"injected query row invalid");
   for(size_t j=0;j<3;++j) {
    auto id=entries[3*i+j];require(id>=0 && id<e.index->ntotal,"entry out of range");
    require(std::find(e.mapping.begin(),e.mapping.end(),id)!=e.mapping.end(),"entry not in H");
    if(j)require(entries[3*i+j-1]<id,"entries must be sorted distinct");
   }
  }
  e.ids.resize(count*K);e.distances.resize(count*K);e.graph_ndc.resize(count);e.index->acsg.search_L=128;
  NativeWork plain(*e.index,false);Work original(*e.index,true);
  for(size_t i=0;i<count;++i) {
   Decision dec;std::copy(entries+3*i,entries+3*i+3,dec.ids.begin());dec.labels=dec.ids;
   const float* q=e.q.data()+size_t(rows[i])*e.d;
   Search s;
   if(reference) {std::vector<int32_t> ent(dec.ids.begin(),dec.ids.end());s=original.run(*e.index,q,ent,{0,1,2},3);}
   else s=plain.search(*e.index,q,dec,3);
   ++e.calls;std::copy(s.ids.begin(),s.ids.end(),e.ids.begin()+K*i);
   std::copy(s.distances.begin(),s.distances.end(),e.distances.begin()+K*i);e.graph_ndc[i]=s.ndc;
  }
  return 0;
 } catch(const std::exception& ex) {e37::error=ex.what();return -1;}
}

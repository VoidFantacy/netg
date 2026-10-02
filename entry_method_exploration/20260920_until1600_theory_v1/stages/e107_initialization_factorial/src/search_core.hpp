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

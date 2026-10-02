#pragma once
#define main inherited_main_unused
#include "common/evaluate.cpp"
#undef main
#include "kernels.hpp"

struct ActualCount:CountDC{
 explicit ActualCount(faiss::DistanceComputer*p):CountDC(p){}
 void distances_batch_4(faiss::idx_t a,faiss::idx_t b,faiss::idx_t c,faiss::idx_t d,float&x,float&y,float&z,float&w)override{
  for(auto id:{a,b,c,d}){if(count<3)first[count]=id;++count;}dc->distances_batch_4(a,b,c,d,x,y,z,w);
 }
};
struct Ranked{std::array<int32_t,3> ids;std::array<float,3> scores;};
struct Route:Router{
 uint64_t calls=0;
 Route(const json&c,size_t d):Router(c,d,c["graph"].get<std::string>()){}
 Ranked ranked(const float*q){
  ++calls;counter.n=0;auto heap=graph->searchKnn(q,3);require(heap.size()==3,"three candidates");
  std::array<std::pair<float,int32_t>,3> z;for(auto&v:z){v={heap.top().first,heap.top().second};heap.pop();}std::sort(z.begin(),z.end());
  Ranked r;for(int j=0;j<3;++j){r.ids[j]=z[j].second;r.scores[j]=1-z[j].first;}return r;
 }
 std::array<int32_t,3> original(const float*q){++calls;return Router::route(q);}
};
struct Node{int feature=-1,left=-1,right=-1,action=0;double threshold=0;};
struct Method{
 std::string name;int action=0;bool feature=false;std::vector<Node> nodes;
 explicit Method(const json&j):name(j["name"]),action(j.value("action",0)),feature(j.value("features",false)){
  if(j.contains("tree")){feature=true;for(auto n:j["tree"]){Node x;x.feature=n.value("feature",-1);x.action=n.value("action",0);x.threshold=n.value("threshold",0.0);x.left=n.value("left",-1);x.right=n.value("right",-1);nodes.push_back(x);}}
 }
 int select(const std::array<double,6>&x)const{if(nodes.empty())return action;int j=0;for(int depth=0;depth<3;++depth){const auto&n=nodes.at(j);if(n.feature<0)return n.action;j=x[n.feature]<=n.threshold?n.left:n.right;}throw std::runtime_error("tree too deep");}
};
struct Engine{
 acsg::IndexACSGFlat&idx;Route&router;std::vector<uint8_t>spans;ResearchKernel kernel;std::unique_ptr<faiss::DistanceComputer>plain,featuredc;ActualCount count;faiss::VisitedTable vt;std::vector<acsg::EnterPoint>ep;std::vector<acsg::Neighbor>legacy;
 uint64_t calls=0,feature_calls=0;std::array<int32_t,3>last_entries;int last_action=0;std::array<double,6>last_features{};
 Engine(acsg::IndexACSGFlat&i,Route&r):idx(i),router(r),spans(make_spans(*i.acsg.final_graph,i.ntotal)),kernel(*i.acsg.final_graph,spans,i.ntotal),plain(acsg::storage_distance_computer(i.storage)),featuredc(acsg::storage_distance_computer(i.storage)),count(acsg::storage_distance_computer(i.storage)),vt(i.ntotal){ep.reserve(3);legacy.reserve(1501);}
 std::array<double,6> features(const float*q,const Ranked&r,std::array<float,3>*raw=nullptr){
  featuredc->set_query(q);std::array<float,3>b;double ps=0,bs=0;
  for(int j=0;j<3;++j){b[j]=-(*featuredc)(r.ids[j]);ps+=double(r.scores[j])*r.scores[j];bs+=double(b[j])*b[j];}feature_calls+=3;
  ps=std::sqrt(ps)+1e-12;bs=std::sqrt(bs)+1e-12;int best=0;for(int j=1;j<3;++j)if(b[j]>b[best]||(b[j]==b[best]&&r.ids[j]<r.ids[best]))best=j;
  if(raw)*raw=b;return {(double(r.scores[0])-r.scores[1])/ps,(double(r.scores[1])-r.scores[2])/ps,(double(b[0])-b[1])/bs,(double(b[0])-b[2])/bs,(double(b[1])-b[2])/bs,double(best)};
 }
 void search(const float*q,const std::array<int32_t,3>&e,int K,int L,faiss::idx_t*I,float*D,bool counting,bool original=false){
  ep.clear();int last=-1;for(int h:e)if(h>=0){require(h>last&&h<idx.ntotal,"valid ordered entries");ep.emplace_back(h,1);last=h;}require(ep.size()==1||ep.size()==3,"one or three entries");
  vt.advance();auto&dis=counting?static_cast<faiss::DistanceComputer&>(count):*plain;dis.set_query(q);
  if(original){idx.acsg.search_L=L;idx.acsg.search_new(dis,K,I,D,vt,2,ep,&legacy);}else kernel.search<true,false,true>(dis,vt,ep,L,K,I,D);++calls;
  if(counting)for(size_t j=0;j<ep.size();++j)require(count.first[j]==ep[j].id,"actual entry consumption");
 }
 void once(const float*q,const Method&m,int K,int L,faiss::idx_t*I,float*D,bool counting){
  if(!m.feature&&m.nodes.empty()&&m.action==0){last_entries=router.original(q);last_action=0;}
  else{auto r=router.ranked(q);if(m.feature)last_features=features(q,r);last_action=m.select(last_features);require(last_action>=0&&last_action<4,"valid action");last_entries={-1,-1,-1};if(last_action==0){last_entries=r.ids;std::sort(last_entries.begin(),last_entries.end());}else last_entries[0]=r.ids[last_action-1];}
  search(q,last_entries,K,L,I,D,counting);
 }
};

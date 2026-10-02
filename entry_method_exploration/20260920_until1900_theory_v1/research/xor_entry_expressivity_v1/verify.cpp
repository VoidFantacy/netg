#include "/data/netg/ACSG/entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/src/search_core.hpp"
#include <faiss/IndexFlat.h>
int main(int argc,char**argv){try{
 threads();require(argc==2&&!fs::exists(argv[1]),"fresh synthetic output");
 const float vectors[15][3]={{0,0,0},{0,0,0},{1,0,10},{-1,0,10},{1,0,10},{-1,0,10},{0,1,20},{0,-1,20},{0,-1,20},{0,1,20},{0,-1,20},{0,1,20},{0,1,20},{0,-1,20},{0,0,100}};
 const int edges[15][2]={{2,3},{4,5},{6,7},{8,9},{10,11},{12,13},{14,-1},{0,1},{14,-1},{0,1},{14,-1},{0,1},{14,-1},{0,1},{0,1}};
 faiss::IndexFlatIP storage(3);storage.add(15,&vectors[0][0]);acsg::Graph<int32_t> graph(15,2);std::vector<uint8_t> spans(15);
 for(int i=0;i<15;++i)for(int j=0;j<2;++j){graph.at(i,j)=edges[i][j];if(edges[i][j]>=0)spans[i]=j+1;}
 for(int seed=0;seed<15;++seed){std::set<int>seen{seed};std::vector<int>todo{seed};for(size_t i=0;i<todo.size();++i)for(int v:edges[todo[i]])if(v>=0&&seen.insert(v).second)todo.push_back(v);require(seen.size()==15,"strong connectivity");}
 ResearchKernel kernel(graph,spans,15);faiss::VisitedTable vt(15);ActualCount dc(acsg::storage_distance_computer(&storage));json observations=json::array();int calls=0;
 for(int x:{-1,1})for(int y:{-1,1}){float q[]={float(x),float(y),1};dc.set_query(q);float target=dc(14),runner=std::numeric_limits<float>::max();for(int i=0;i<14;++i)runner=std::min(runner,dc(i));require(target<runner&&target==-100,"unique common GT1");int optimum=x==y?0:1;
  int best_score=-100,best_method=-1;for(int u:{-1,1})for(int v:{-1,1}){int s=u*x+v*y;if(s>best_score){best_score=s;best_method=u==v?0:1;}}require(best_score==2&&best_method==optimum,"four linear profiles exact");require((std::abs(x+y)>std::abs(x-y)?0:1)==optimum,"nonlinear two-feature exact");
  for(int seed:{0,1}){vt.advance();dc.set_query(q);std::vector<acsg::EnterPoint> ep{acsg::EnterPoint(seed,1)};faiss::idx_t id=-1;float dist=0;kernel.search<true,false,true>(dc,vt,ep,1,1,&id,&dist);++calls;require((id==14)==(seed==optimum),"XOR predicted success");require(dist==(seed==optimum?-100:-21),"terminal score");observations.push_back({{"query",{x,y,1}},{"seed",seed},{"GT1",14},{"GT1_margin",runner-target},{"returned",id},{"distance",dist},{"hit",id==14},{"distance_calls",dc.count},{"optimal_entry",optimum}});}
 }
 require(calls==8,"exact call count");write_json(argv[1],{{"status","PASS"},{"synthetic_calls",calls},{"real_NSG_calls",0},{"ANN_calls",0},{"synthetic_graphs",1},{"K",1},{"L",1},{"same_unique_GT1",true},{"strongly_connected",true},{"threads",process_threads()},{"cpu",sched_getcpu()},{"four_profiles_match_optimal",true},{"nonlinear_features_match_optimal",true},{"base",vectors},{"edges",edges},{"observations",observations},{"scope","Artificial directed graph; two fixed one-entry actions only; not an impossibility result for current multi-entry WFree"}});return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

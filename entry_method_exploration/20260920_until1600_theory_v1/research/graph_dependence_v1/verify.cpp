#include "../../stages/e107_initialization_factorial/src/search_core.hpp"
#include <faiss/IndexFlat.h>

int main(int argc,char** argv){try{
  threads();require(argc==2,"output path required");require(!fs::exists(argv[1]),"preserve output");
  faiss::IndexFlatIP storage(1);float vals[]={0,.1f,1,.9f,.8f},q=1;storage.add(5,vals);
  const int next[2][5]={{1,2,3,4,0},{4,2,0,1,3}};
  json observations=json::array();
  for(int g=0;g<2;++g){
    acsg::Graph<int32_t> graph(5,1);for(int i=0;i<5;++i)graph.at(i,0)=next[g][i];
    for(int s=0;s<5;++s){std::set<int> seen;int v=s;for(int j=0;j<5;++j){seen.insert(v);v=next[g][v];}require(seen.size()==5&&v==s,"strongly connected directed cycle");}
    std::vector<uint8_t> spans(5,1);ResearchKernel kernel(graph,spans,5);faiss::VisitedTable vt(5);
    ActualCount dc(acsg::storage_distance_computer(&storage));
    for(int seed:{0,3}){
      vt.advance();dc.set_query(&q);std::vector<acsg::EnterPoint> ep{acsg::EnterPoint(seed,1)};
      faiss::idx_t id=-1;float distance=0;kernel.search<true,false,true>(dc,vt,ep,2,1,&id,&distance);
      int expected=((g==0&&seed==0)||(g==1&&seed==3))?2:3;
      require(id==expected,"graph-dependent utility reversal");
      observations.push_back({{"graph",g+1},{"seed",seed},{"returned",id},{"distance",distance},{"GT1_hit",id==2},{"distance_calls",dc.count}});
    }
  }
  write_json(argv[1],{{"status","PASS"},{"synthetic_searches",4},{"real_NSG_calls",0},{"threads",omp_get_max_threads()},{"cpu",sched_getcpu()},{"K",1},{"L",2},{"query",1},{"GT1",2},{"base_values",{0,.1,1,.9,.8}},{"G1_successor",{1,2,3,4,0}},{"G2_successor",{4,2,0,1,3}},{"both_strongly_connected",true},{"observations",observations},{"scope","Arbitrary connected directed graphs under the frozen kernel; not claimed to be NSG-built proximity graphs."}});
  return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

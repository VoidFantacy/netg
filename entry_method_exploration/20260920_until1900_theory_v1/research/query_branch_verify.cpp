#include "/data/netg/ACSG/entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/src/search_core.hpp"
#include <faiss/IndexFlat.h>
int main(int argc,char**argv){try{
 threads();require(argc==2&&!fs::exists(argv[1]),"new output required");
 float base[]={-.2f,0,1,1,1,-1,1.5f,0,1.25f,0,2,0,-.3f,0,1,1,1,-1};
 const int edges[9][2]={{1,2},{5,-1},{3,-1},{4,-1},{0,6},{4,-1},{7,8},{3,-1},{5,-1}};
 faiss::IndexFlatIP storage(2);storage.add(9,base);acsg::Graph<int32_t> graph(9,2);std::vector<uint8_t> spans(9);
 for(int i=0;i<9;++i)for(int j=0;j<2;++j){graph.at(i,j)=edges[i][j];if(edges[i][j]>=0)spans[i]=j+1;}
 for(int seed=0;seed<9;++seed){std::set<int> seen{seed};std::vector<int> todo{seed};for(size_t p=0;p<todo.size();++p)for(int v:edges[todo[p]])if(v>=0&&seen.insert(v).second)todo.push_back(v);require(seen.size()==9,"strong connectivity");}
 ResearchKernel kernel(graph,spans,9);faiss::VisitedTable vt(9);ActualCount dc(acsg::storage_distance_computer(&storage));json observations=json::array();
 for(int sign:{1,-1}){
  float q[]={1,sign/16.f};std::unique_ptr<faiss::DistanceComputer> gt_dc(acsg::storage_distance_computer(&storage));gt_dc->set_query(q);float target=(*gt_dc)(5),runner=std::numeric_limits<float>::max();
  for(int id=0;id<9;++id)if(id!=5)runner=std::min(runner,(*gt_dc)(id));require(target<runner,"unique GT1 unchanged");
  for(int seed:{0,6}){vt.advance();dc.set_query(q);std::vector<acsg::EnterPoint> entries{acsg::EnterPoint(seed,1)};faiss::idx_t id=-1;float distance=0;kernel.search<true,false,true>(dc,vt,entries,2,1,&id,&distance);int expected=((sign==1&&seed==0)||(sign==-1&&seed==6))?5:3;require(id==expected,"query dependent utility reversal");
   observations.push_back({{"query_sign",sign},{"query",{q[0],q[1]}},{"seed",seed},{"GT1",5},{"GT1_distance",target},{"GT1_margin",runner-target},{"returned",id},{"distance",distance},{"GT1_hit",id==5},{"distance_calls",dc.count}});
  }
 }
 write_json(argv[1],{{"status","PASS"},{"synthetic_calls",4},{"real_NSG_calls",0},{"K",1},{"L",2},{"epsilon",1/16.},{"same_graph",true},{"same_unique_GT1",true},{"strongly_connected",true},{"threads",omp_get_max_threads()},{"cpu",sched_getcpu()},{"observations",observations},{"scope","Fixed arbitrary directed graph; not claimed to be NSG-built or representative of real query sensitivity"}});return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

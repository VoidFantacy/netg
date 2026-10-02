#include "../hybrid_temperature_factorial_v1/src/kernels.hpp"
struct ToyDistance final:faiss::DistanceComputer{
 const std::vector<float>& x;bool ip;float q;std::vector<int> visited;
 ToyDistance(const std::vector<float>& a,bool b):x(a),ip(b),q(b?1.f:10.f){}
 void set_query(const float* a)override{q=*a;visited.clear();}
 float operator()(faiss::idx_t id)override{visited.push_back(id);return ip?-q*x[id]:(q-x[id])*(q-x[id]);}
 float symmetric_dis(faiss::idx_t a,faiss::idx_t b)override{return ip?-x[a]*x[b]:(x[a]-x[b])*(x[a]-x[b]);}
};
int main(int argc,char**argv){try{
 require(argc==2,"toy new_output_json");require(!fs::exists(argv[1]),"preserve output");json results=json::array();
 for(int L:{2,128})for(bool ip:{false,true}){
  int n=L+5;std::vector<float>x(n);x[0]=1;x[1]=2;x[2]=10;x[3]=9;
  for(int j=0;j<L;++j)x[j+4]=9.1f+.8f*j/(L-1);x[n-1]=-1;
  acsg::Graph<int32_t> graph(n,1);for(int i=0;i<n;++i)graph.at(i,0)=(i+1)%n;
  auto spans=make_spans(graph,n);ResearchKernel kernel(graph,spans,n);
  for(auto start:std::vector<std::vector<int>>{{0},{3},{0,3}}){
   std::vector<acsg::EnterPoint> entries;for(int e:start)entries.emplace_back(e,1);
   ToyDistance dc(x,ip);faiss::VisitedTable vt(n);faiss::idx_t id=-1;float distance=0;
   kernel.search<true,false,true>(dc,vt,entries,L,1,&id,&distance);
   bool expected=start.size()==1&&start[0]==0;
   results.push_back({{"L",L},{"metric",ip?"negative_ip":"squared_l2"},{"entries",start},{"returned_id",id},{"distance",distance},
    {"expected_hit",expected},{"actual_hit",id==2},{"evaluated_ids",dc.visited},{"coordinates",x},{"strong_cycle_edges",n}});
  }
 }
 write_json(argv[1],{{"calls",12},{"results",results}});
 for(auto& r:results)require(r["expected_hit"]==r["actual_hit"],"frozen counterexample prediction failed; output retained");
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

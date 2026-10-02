#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
#include <sched.h>
namespace e89 {
std::string error;
void threadcheck(){
 cpu_set_t cp;CPU_ZERO(&cp);require(sched_getaffinity(0,sizeof(cp),&cp)==0&&CPU_COUNT(&cp)==1&&CPU_ISSET(15,&cp),"CPU15");
 for(auto k:{"OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","BLIS_NUM_THREADS"})require(std::getenv(k)&&std::string(std::getenv(k))=="1","thread env");
 std::ifstream f("/proc/self/status");std::string s;int n=0;while(std::getline(f,s))if(s.rfind("Threads:",0)==0)n=std::stoi(s.substr(8));require(n==1,"actual threads");
}
struct Routes {
 size_t n,d;uint64_t calls=0;std::vector<float> q,distances;std::vector<int32_t> entries,slots;std::vector<uint32_t> ndc;
 std::unique_ptr<Policy> p,c;
 Routes(const json& x):n(x.at("num_queries")),d(x.at("dim")){
  threadcheck();require(x.at("threads")==1,"threads");require(n<=x.at("input_total_rows").get<size_t>(),"rows");
  require(fs::file_size(x.at("queries_file").get<std::string>())==x.at("input_total_rows").get<size_t>()*d*4,"query shape");q.resize(n*d);std::ifstream f(x.at("queries_file").get<std::string>(),std::ios::binary);f.read(reinterpret_cast<char*>(q.data()),q.size()*4);require(bool(f),"query prefix");finite_matrix(q,"query");
  auto m=x.at("method");require(m.at("reference_graph")==true&&m.at("ef_search")==10&&m.at("variable_profiles")==true,"fixed compact contract");p=std::make_unique<Policy>(m,m.at("graph_file"),false,false);c=std::make_unique<Policy>(m,m.at("graph_file"),true,true);entries.resize(n*3);slots.resize(n*7);distances.resize(n*7);ndc.resize(n);
 }
 void run(int hub,size_t rows){
  threadcheck();require(rows>0 && rows<=n,"row subset");Policy* ps[2]={p.get(),c.get()};
  std::vector<size_t> changed;std::vector<float> original[2];
  if(hub>=0){
   std::vector<size_t> group;for(size_t j=0;j<p->mapping.size();++j)if(p->mapping[j]==hub)group.push_back(j);
   require(group.size()==3,"parent restoration needs exactly two children");changed={group[1],group[2]};
   for(int t=0;t<2;++t){auto& g=*ps[t]->graph;original[t].resize(2*d);for(size_t j=0;j<2;++j){
    auto ptr=g.getDataByInternalId(changed[j]);std::memcpy(original[t].data()+j*d,ptr,d*4);
    std::memcpy(ptr,ps[t]->w.data()+group[0]*d,d*4);
    require(std::memcmp(ptr,ps[t]->w.data()+group[0]*d,d*4)==0,"parent install bytes");
   }}
  }else require(hub==-1,"invalid no-op");
  auto restore=[&](){for(int t=0;t<2;++t)for(size_t j=0;j<changed.size();++j){
   auto ptr=ps[t]->graph->getDataByInternalId(changed[j]);std::memcpy(ptr,original[t].data()+j*d,d*4);
   require(std::memcmp(ptr,ps[t]->w.data()+changed[j]*d,d*4)==0,"restore original row bytes");
  }};
  try{
   for(size_t i=0;i<rows;++i){auto a=p->route(q.data()+i*d),b=c->route(q.data()+i*d);calls+=2;
    require(a.ids==b.ids&&a.labels==b.labels&&a.candidate_slots==b.candidate_slots&&std::memcmp(a.candidate_distances.data(),b.candidate_distances.data(),28)==0,"full route parity");
    std::copy(a.ids.begin(),a.ids.end(),entries.begin()+3*i);std::copy(a.candidate_slots.begin(),a.candidate_slots.end(),slots.begin()+7*i);std::copy(a.candidate_distances.begin(),a.candidate_distances.end(),distances.begin()+7*i);ndc[i]=b.ndc;
   }
  }catch(...){restore();throw;}
  restore();threadcheck();
 }

};
}
extern "C" const char* e89_error(){return e89::error.c_str();}
extern "C" void* e89_create(const char* s){try{return new e89::Routes(json::parse(s));}catch(const std::exception& x){e89::error=x.what();return nullptr;}}
extern "C" void e89_destroy(void* p){delete static_cast<e89::Routes*>(p);}
extern "C" int e89_run(void* p,int hub,size_t n){try{static_cast<e89::Routes*>(p)->run(hub,n);return 0;}catch(const std::exception& x){e89::error=x.what();return -1;}}
extern "C" const void* e89_data(void* p,int field,size_t* n){auto& e=*static_cast<e89::Routes*>(p);switch(field){case 0:*n=e.entries.size();return e.entries.data();case 1:*n=e.slots.size();return e.slots.data();case 2:*n=e.distances.size();return e.distances.data();case 3:*n=e.ndc.size();return e.ndc.data();}*n=0;return nullptr;}
extern "C" uint64_t e89_calls(void* p){return static_cast<e89::Routes*>(p)->calls;}

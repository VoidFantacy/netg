#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
#include <sched.h>
namespace e86 {
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
 void run(int source,int target){
  threadcheck();std::vector<char> orig[2];Policy* ps[2]={p.get(),c.get()};
  if(source>=0)for(int i=0;i<2;++i){auto& g=*ps[i]->graph;require(size_t(source)<g.cur_element_count&&target>=0&&size_t(target)<g.cur_element_count&&source!=target,"edge IDs");auto at=g.get_linklist0(source);orig[i].assign(reinterpret_cast<char*>(at),reinterpret_cast<char*>(at)+g.size_links_level0_);auto deg=g.getListCount(at);require(deg<g.maxM0_,"full degree");auto row=reinterpret_cast<hnswlib::tableint*>(at+1);for(size_t j=0;j<deg;++j)require(row[j]!=unsigned(target),"existing edge");require(ps[i]->mapping[source]!=ps[i]->mapping[target],"same hub");row[deg]=target;g.setListCount(at,deg+1);}
  else require(target==-1,"baseline target");
  for(size_t i=0;i<n;++i){auto a=p->route(q.data()+i*d),b=c->route(q.data()+i*d);calls+=2;require(a.ids==b.ids&&a.labels==b.labels&&a.candidate_slots==b.candidate_slots&&std::memcmp(a.candidate_distances.data(),b.candidate_distances.data(),28)==0,"full route parity");std::copy(a.ids.begin(),a.ids.end(),entries.begin()+3*i);std::copy(a.candidate_slots.begin(),a.candidate_slots.end(),slots.begin()+7*i);std::copy(a.candidate_distances.begin(),a.candidate_distances.end(),distances.begin()+7*i);ndc[i]=b.ndc;}
  if(source>=0)for(int i=0;i<2;++i){auto at=ps[i]->graph->get_linklist0(source);std::memcpy(at,orig[i].data(),orig[i].size());require(std::memcmp(at,orig[i].data(),orig[i].size())==0,"edge restore bytes");}
  threadcheck();
 }
};
}
extern "C" const char* e86_error(){return e86::error.c_str();}
extern "C" void* e86_create(const char* s){try{return new e86::Routes(json::parse(s));}catch(const std::exception& x){e86::error=x.what();return nullptr;}}
extern "C" void e86_destroy(void* p){delete static_cast<e86::Routes*>(p);}
extern "C" int e86_run(void* p,int s,int t){try{static_cast<e86::Routes*>(p)->run(s,t);return 0;}catch(const std::exception& x){e86::error=x.what();return -1;}}
extern "C" const void* e86_data(void* p,int field,size_t* n){auto& e=*static_cast<e86::Routes*>(p);switch(field){case 0:*n=e.entries.size();return e.entries.data();case 1:*n=e.slots.size();return e.slots.data();case 2:*n=e.distances.size();return e.distances.data();case 3:*n=e.ndc.size();return e.ndc.data();}*n=0;return nullptr;}
extern "C" uint64_t e86_calls(void* p){return static_cast<e86::Routes*>(p)->calls;}

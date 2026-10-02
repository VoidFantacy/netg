#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
#include <sched.h>
#include <cstdlib>

namespace e37 {
using Graph=hnswlib::HierarchicalNSW<float>;
thread_local std::string error;
int threads() {
 std::ifstream f("/proc/self/status");std::string line;
 while(std::getline(f,line))if(line.rfind("Threads:",0)==0)return std::stoi(line.substr(8));
 throw std::runtime_error("cannot read actual process threads");
}
void thread_contract(const json& c) {
 require(c.at("threads")==1,"explicit threads=1 required");
 for(auto key:{"OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"}) {
  auto value=std::getenv(key);require(value && std::string(value)=="1","library thread contract");
 }
 omp_set_dynamic(0);omp_set_num_threads(1);require(threads()==1,"actual threads !=1");
 cpu_set_t cpus;CPU_ZERO(&cpus);require(sched_getaffinity(0,sizeof(cpus),&cpus)==0,"affinity read failed");
 require(CPU_COUNT(&cpus)==1 && CPU_ISSET(15,&cpus),"CPU15 required");
}
struct Environment {
 json c;size_t d,h,n;std::vector<float> q,w;std::vector<int32_t> mapping;
 CountSpace counted_space;hnswlib::InnerProductSpace plain_space;
 std::unique_ptr<Graph> graph;std::unique_ptr<acsg::IndexACSGFlat> index;
 std::unique_ptr<NativeWork> worker;
 std::vector<int32_t> ids,entries,topology;std::vector<float> distances;
 std::vector<uint32_t> route_ndc,graph_ndc;
 uint64_t calls=0,hcalls=0,builds=0,cap;double build_seconds=0;
 Environment(const json& config):c(config),d(c.at("dim")),h(c.at("hub_count")),n(c.at("num_queries")),
 q(read_raw<float>(c.at("queries_file"))),mapping(read_raw<int32_t>(c.at("hub_ids"))),
 counted_space(d),plain_space(d),cap(c.at("native_call_cap")) {
  thread_contract(c);require(d>0 && h>=3 && q.size()==n*d && mapping.size()==h,"environment shapes");finite_matrix(q,"query");
  require(std::set<int32_t>(mapping.begin(),mapping.end()).size()==h,"duplicate mapping");
  index=std::make_unique<acsg::IndexACSGFlat>();index->loadACPG(c.at("index_path").get<std::string>().c_str());
  std::vector<float>().swap(index->acsg.pheromone);std::vector<float>().swap(index->acsg.weight);
  require(index->d==int(d) && index->metric_type==faiss::METRIC_INNER_PRODUCT,"native metric/dimension");
  for(int32_t id:mapping)require(id>=0 && id<index->ntotal,"hub out of range");
  worker=std::make_unique<NativeWork>(*index,true);worker->retset.reserve(801);index->acsg.search_L=128;
 }
 void inspect() {
  require(graph->cur_element_count==h,"HNSW size");topology={int32_t(h),int32_t(d),int32_t(graph->enterpoint_node_),graph->maxlevel_};
  for(size_t i=0;i<h;++i) {
   require(graph->getExternalLabel(i)==size_t(mapping[i]),"external ID changed");
   require(std::memcmp(graph->getDataByInternalId(i),w.data()+i*d,d*sizeof(float))==0,"profile bytes changed");
   topology.push_back(mapping[i]);topology.push_back(graph->element_levels_[i]);
   for(int level=0;level<=graph->element_levels_[i];++level) {
    auto* row=graph->get_linklist_at_level(i,level);auto* adj=(hnswlib::tableint*)(row+1);size_t degree=graph->getListCount(row);
    require(degree<=(level?16:32),"degree budget exceeded");topology.push_back(int32_t(degree));std::set<uint32_t> seen;
    for(size_t j=0;j<degree;++j) {require(adj[j]<h && adj[j]!=i && seen.insert(adj[j]).second,"invalid edge");topology.push_back(int32_t(adj[j]));}
   }
  }
 }
 void build(const float* data,size_t count) {
  require(count==h*d,"W shape");w.assign(data,data+count);finite_matrix(w,"profile");
  for(size_t i=0;i<h;++i) {double norm=0;for(size_t j=0;j<d;++j)norm+=double(w[i*d+j])*w[i*d+j];require(std::abs(norm-1)<1e-4,"profile not unit");}
  require(builds<7500,"per-dataset build cap");auto start=Clock::now();route_counter=nullptr;
  graph=std::make_unique<Graph>(&counted_space,h,16,200,20260828);
  for(size_t i=0;i<h;++i)graph->addPoint(w.data()+i*d,size_t(mapping[i]));graph->setEf(10);
  build_seconds+=std::chrono::duration<double>(Clock::now()-start).count();++builds;inspect();
 }
 Decision route(Graph& g,const float* query,bool counted) {
  uint64_t value=0;route_counter=counted?&value:nullptr;auto heap=g.searchKnn(query,3);route_counter=nullptr;++hcalls;
  require(heap.size()==3,"incomplete top3");Decision result;
  for(int k=0;k<3;++k){result.ids[k]=int32_t(heap.top().second);heap.pop();}
  std::sort(result.ids.begin(),result.ids.end());require(result.ids[0]!=result.ids[1] && result.ids[1]!=result.ids[2],"duplicate entry");
  result.labels=result.ids;result.ndc=uint32_t(value);return result;
 }
 void run(const int32_t* rows,size_t count,int L) {
  require(bool(graph) && std::set<int>{64,128,256,400,800}.count(L),"graph or L invalid");require(calls+count<=cap,"native call cap");
  for(size_t i=0;i<count;++i)require(rows[i]>=0 && size_t(rows[i])<n,"query row invalid");
  ids.resize(count*K);distances.resize(count*K);entries.resize(count*3);route_ndc.resize(count);graph_ndc.resize(count);index->acsg.search_L=L;
  for(size_t i=0;i<count;++i) {
   auto* query=q.data()+size_t(rows[i])*d;auto dec=route(*graph,query,true);auto s=worker->search(*index,query,dec,3);++calls;
   std::copy(s.ids.begin(),s.ids.end(),ids.begin()+i*K);std::copy(s.distances.begin(),s.distances.end(),distances.begin()+i*K);
   std::copy(dec.ids.begin(),dec.ids.end(),entries.begin()+i*3);route_ndc[i]=dec.ndc;graph_ndc[i]=s.ndc;
  }
 }
 void save(const std::string& path) {require(bool(graph) && !fs::exists(path),"refuse graph overwrite");graph->saveIndex(path);}
 void verify(const std::string& path,const int32_t* rows,size_t count) {
  require(calls+3*count<=cap,"parity call cap");run(rows,count,128);
  Graph plain(&plain_space,path,false,h);plain.setEf(10);NativeWork pw(*index,false);Work ref(*index,true);
  for(size_t i=0;i<count;++i) {
   auto* query=q.data()+size_t(rows[i])*d;auto dec=route(plain,query,false);
   require(std::equal(dec.ids.begin(),dec.ids.end(),entries.begin()+3*i),"serialized/plain route mismatch");
   auto s=pw.search(*index,query,dec,3);++calls;std::vector<int32_t> ent(dec.ids.begin(),dec.ids.end());auto a=ref.run(*index,query,ent,{0,1,2},3);++calls;
   require(std::equal(s.ids.begin(),s.ids.end(),ids.begin()+K*i) && std::equal(a.ids.begin(),a.ids.end(),ids.begin()+K*i),"native IDs mismatch");
   require(std::memcmp(s.distances.data(),distances.data()+i*K,K*sizeof(float))==0 && std::memcmp(a.distances.data(),distances.data()+i*K,K*sizeof(float))==0,"native distance bits mismatch");
   require(a.ndc==graph_ndc[i],"native NDC mismatch");
  }
 }
};
}
extern "C" {
const char* e37_error(){return e37::error.c_str();}
void* e37_create(const char* config){try{return new e37::Environment(json::parse(config));}catch(const std::exception& e){e37::error=e.what();return nullptr;}}
void e37_destroy(void* p){delete static_cast<e37::Environment*>(p);}
int e37_build(void* p,const float* w,size_t n){try{static_cast<e37::Environment*>(p)->build(w,n);return 0;}catch(const std::exception& e){e37::error=e.what();return -1;}}
int e37_run(void* p,const int32_t* rows,size_t n,int L){try{static_cast<e37::Environment*>(p)->run(rows,n,L);return 0;}catch(const std::exception& e){e37::error=e.what();return -1;}}
int e37_save(void* p,const char* path){try{static_cast<e37::Environment*>(p)->save(path);return 0;}catch(const std::exception& e){e37::error=e.what();return -1;}}
int e37_verify(void* p,const char* path,const int32_t* rows,size_t n){try{static_cast<e37::Environment*>(p)->verify(path,rows,n);return 0;}catch(const std::exception& e){e37::error=e.what();return -1;}}
void* e37_data(void* p,int field,size_t* n){auto& e=*static_cast<e37::Environment*>(p);switch(field){
 case 0:*n=e.ids.size();return e.ids.data();case 1:*n=e.distances.size();return e.distances.data();case 2:*n=e.entries.size();return e.entries.data();
 case 3:*n=e.route_ndc.size();return e.route_ndc.data();case 4:*n=e.graph_ndc.size();return e.graph_ndc.data();case 5:*n=e.topology.size();return e.topology.data();default:*n=0;return nullptr;}}
uint64_t e37_stat(void* p,int field){auto& e=*static_cast<e37::Environment*>(p);if(field==0)return e.calls;if(field==1)return e.hcalls;if(field==2)return e.builds;return uint64_t(e37::threads());}
double e37_build_seconds(void* p){return static_cast<e37::Environment*>(p)->build_seconds;}
}

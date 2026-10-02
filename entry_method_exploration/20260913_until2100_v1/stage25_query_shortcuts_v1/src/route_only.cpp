#define AB_BENCHMARK_LIBRARY
#include "/data/netg/ACSG/entry_method_exploration/20260913_until2100_v1/stage14_compact_modes_v1/src/benchmark_with_nsg.cpp"
#include <sched.h>
template<class T> void output(const fs::path& p,const std::vector<T>& v){require(!fs::exists(p),"existing route output");std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<const char*>(v.data()),v.size()*sizeof(T));require(bool(f),"route output failed");}
int main(int argc,char**argv){
 try{
  require(argc==3,"route_only input.json new_output");std::ifstream f(argv[1]);json c;f>>c;fs::path out=argv[2];require(!fs::exists(out),"output exists");
  cpu_set_t cpus;CPU_ZERO(&cpus);require(sched_getaffinity(0,sizeof(cpus),&cpus)==0&&CPU_COUNT(&cpus)==1&&CPU_ISSET(15,&cpus),"CPU15 required");
  for(const auto* key:{"OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS","BLIS_NUM_THREADS"})require(std::getenv(key)&&std::string(std::getenv(key))=="1","thread env");
  require(c.at("threads")==1,"threads=1 required");const size_t n=c.at("num_queries"),d=c.at("dim"),total=c.at("input_total_rows");require(fs::file_size(c.at("queries_file").get<std::string>())==total*d*4&&n<=total,"query shape");
  std::vector<float> q(n*d);std::ifstream qf(c.at("queries_file").get<std::string>(),std::ios::binary);qf.read(reinterpret_cast<char*>(q.data()),q.size()*4);require(bool(qf),"query read");finite_matrix(q,"query");
  auto start=Clock::now();auto m=c.at("method");Policy p(m,m.at("graph_file").get<std::string>(),false,false),count(m,m.at("graph_file").get<std::string>(),true,true);
  std::vector<int32_t> entries(n*3),slots(n*7);std::vector<float> distances(n*7);std::vector<uint32_t> ndc(n);
  for(size_t i=0;i<n;++i){auto a=p.route(q.data()+i*d),b=count.route(q.data()+i*d);require(a.ids==b.ids&&a.labels==b.labels&&a.candidate_slots==b.candidate_slots&&std::memcmp(a.candidate_distances.data(),b.candidate_distances.data(),7*sizeof(float))==0,"route parity");std::copy(a.ids.begin(),a.ids.end(),entries.begin()+i*3);std::copy(a.candidate_slots.begin(),a.candidate_slots.end(),slots.begin()+i*7);std::copy(a.candidate_distances.begin(),a.candidate_distances.end(),distances.begin()+i*7);ndc[i]=b.ndc;}
  int nt=0;std::ifstream status("/proc/self/status");std::string line;while(std::getline(status,line))if(line.rfind("Threads:",0)==0)nt=std::stoi(line.substr(8));require(nt==1,"actual process threads");fs::create_directories(out);output(out/"entries.i32",entries);output(out/"slots.i32",slots);output(out/"distances.f32",distances);output(out/"route_ndc.u32",ndc);
  json j={{"status","COMPLETE"},{"HNSW",2*n},{"NSG",0},{"builds",0},{"plain_count_parity",n},{"CPU",15},{"actual_threads",nt},{"operation_seconds",std::chrono::duration<double>(Clock::now()-start).count()}};std::ofstream(out/"cost.json")<<j.dump(2)<<std::endl;std::cout<<j.dump()<<std::endl;return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}
}

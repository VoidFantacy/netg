#include <algorithm>
#include <array>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <vector>
#include <sched.h>
#include <nlohmann/json.hpp>
#include "hnswlib/hnswlib.h"
using json=nlohmann::json;namespace fs=std::filesystem;
void require(bool v,const std::string& s){if(!v)throw std::runtime_error(s);}
template<class T>std::vector<T> raw(const fs::path& p){std::ifstream f(p,std::ios::binary|std::ios::ate);require(bool(f),p.string());auto z=f.tellg();require(z>=0&&size_t(z)%sizeof(T)==0,"shape");std::vector<T> a(size_t(z)/sizeof(T));f.seekg(0);f.read(reinterpret_cast<char*>(a.data()),z);require(bool(f),"read");return a;}
template<class T>void save(const fs::path&p,const std::vector<T>&a){std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<const char*>(a.data()),a.size()*sizeof(T));require(bool(f),"write");}
json readj(const fs::path&p){std::ifstream f(p);json j;f>>j;return j;}
struct Counter{hnswlib::DISTFUNC<float> fn;void* param;uint64_t n=0;};
float counted(const void*a,const void*b,const void*p){auto*c=(Counter*)p;++c->n;return c->fn(a,b,c->param);}
void threads(){for(auto key:{"OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"})require(getenv(key)&&std::string(getenv(key))=="1","thread environment");cpu_set_t set;CPU_ZERO(&set);require(!sched_getaffinity(0,sizeof(set),&set)&&CPU_COUNT(&set)==1&&CPU_ISSET(15,&set),"CPU15");std::ifstream f("/proc/self/status");std::string s;bool seen=false;while(std::getline(f,s))if(s.rfind("Threads:",0)==0){require(std::stoi(s.substr(8))==1,"one real thread");seen=true;}require(seen,"thread field");}
int main(int argc,char**argv){try{
 require(argc==3,"observe config output");threads();auto c=readj(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"output exists");fs::create_directories(out);
 size_t n=c["n"],d=c["dimension"];auto q=raw<float>(c["queries"].get<std::string>());auto ids=raw<int32_t>(c["anchor"]["ids"].get<std::string>());auto w=raw<float>(c["anchor"]["W"].get<std::string>());
 require(q.size()==n*d&&w.size()==ids.size()*d,"query/profile shape");for(float v:q)require(std::isfinite(v),"finite q");
 hnswlib::InnerProductSpace space(d);Counter cnt{space.get_dist_func(),space.get_dist_func_param(),0};
 hnswlib::HierarchicalNSW<float> graph(&space,c["anchor"]["graph"].get<std::string>(),false,ids.size());graph.setEf(10);
 require(graph.maxlevel_>0,"upper layers present");size_t upper_nodes=0;
 for(size_t i=0;i<ids.size();++i){require(graph.getExternalLabel(i)==size_t(ids[i]),"frozen labels");require(!memcmp(graph.getDataByInternalId(i),w.data()+i*d,4*d),"frozen vectors");upper_nodes+=graph.element_levels_[i]>=1;}
 graph.fstdistfunc_=counted;graph.dist_func_param_=&cnt;
 std::vector<int32_t> reference;for(auto p:c["reference_entries"]){auto part=raw<int32_t>(p.get<std::string>());reference.insert(reference.end(),part.begin(),part.end());}require(reference.size()==n*3,"reference shape");
 std::vector<int32_t> states(n),entries(n*3);std::vector<float> distances(n*3);std::vector<uint64_t> ndc(n);std::map<int,size_t> counts;auto start=std::chrono::steady_clock::now();
 for(size_t i=0;i<n;++i){
   cnt.n=0;auto original=graph.searchKnn(q.data()+i*d,3);uint64_t original_count=cnt.n;
   hnswlib::tableint upper=~hnswlib::tableint(0);cnt.n=0;auto observed=graph.searchKnnObserved(q.data()+i*d,3,upper);
   require(original_count==cnt.n,"distance count parity");require(original.size()==3&&observed.size()==3,"heap sizes");
   require(upper<ids.size()&&graph.element_levels_[upper]>=1,"upper state valid");states[i]=upper;counts[int(upper)]++;ndc[i]=cnt.n;
   std::array<int32_t,3> sorted;
   for(int j=0;j<3;++j){auto a=original.top(),b=observed.top();original.pop();observed.pop();require(a.second==b.second&&!memcmp(&a.first,&b.first,4),"heap ID/distance bits");sorted[j]=a.second;distances[i*3+j]=a.first;}
   std::sort(sorted.begin(),sorted.end());for(int j=0;j<3;++j){entries[i*3+j]=sorted[j];require(sorted[j]==reference[i*3+j],"historical default route parity");}
 }
 threads();save(out/"upper_states.i32",states);save(out/"entries.i32",entries);save(out/"heap_distances.f32",distances);save(out/"route_ndc.u64",ndc);
 json occupancy=json::array();for(auto[z,count]:counts)occupancy.push_back({{"internal_node",z},{"real_id",ids[z]},{"queries",count}});
 json result={{"status","PASS"},{"n",n},{"H",ids.size()},{"upper_nodes",upper_nodes},{"observed_states",counts.size()},{"occupancy",occupancy},{"router_calls",2*n},{"nsg_calls",0},{"heap_bit_parity",true},{"distance_count_parity",true},{"historical_entries_parity",true},{"threads",1},{"cpu",15},{"seconds",std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()}};
 std::ofstream f(out/"complete.json");f<<result.dump(2)<<'\n';std::cout<<result.dump()<<std::endl;return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

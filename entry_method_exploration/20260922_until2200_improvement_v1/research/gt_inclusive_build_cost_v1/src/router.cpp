#include <hnswlib/hnswlib.h>
#include <nlohmann/json.hpp>
#include <fstream>
#include <filesystem>
#include <chrono>
#include <cstring>
#include <stdexcept>
#include <iostream>
using json=nlohmann::json;namespace fs=std::filesystem;using G=hnswlib::HierarchicalNSW<float>;using Clock=std::chrono::steady_clock;
void require(bool x,const char*s){if(!x)throw std::runtime_error(s);}
template<class T>std::vector<T> raw(const fs::path&p){std::ifstream f(p,std::ios::binary|std::ios::ate);require(bool(f),"input open");size_t n=f.tellg();require(n%sizeof(T)==0,"input size");std::vector<T>x(n/sizeof(T));f.seekg(0);f.read((char*)x.data(),n);require(bool(f),"input read");return x;}
double elapsed(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
struct Counter{hnswlib::DISTFUNC<float> fn;void*arg;uint64_t n=0;};
float counted(const void*a,const void*b,const void*p){auto*c=(Counter*)p;++c->n;return c->fn(a,b,c->arg);}
int main(int argc,char**argv){try{
 require(argc==3,"router config output");std::ifstream f(argv[1]);json c;f>>c;fs::path out=argv[2];require(!fs::exists(out),"fresh output");fs::create_directories(out);size_t d=c["dimension"];auto loadstart=Clock::now();auto w=raw<float>(c["W"].get<std::string>());auto ids=raw<int32_t>(c["ids"].get<std::string>());size_t H=ids.size();require(w.size()==H*d,"shape");double input_seconds=elapsed(loadstart);
 hnswlib::InnerProductSpace space(d);auto t=Clock::now();G rebuilt(&space,H,16,200,20260828);for(size_t i=0;i<H;++i)rebuilt.addPoint(w.data()+i*d,ids[i]);rebuilt.setEf(10);double build_seconds=elapsed(t);
 t=Clock::now();rebuilt.saveIndex((out/"router.hnsw").string());double save_seconds=elapsed(t);G old(&space,c["old_graph"].get<std::string>(),false,H);old.setEf(10);auto auditstart=Clock::now();
 require(old.cur_element_count==rebuilt.cur_element_count&&old.maxlevel_==rebuilt.maxlevel_&&old.enterpoint_node_==rebuilt.enterpoint_node_,"router levels/entrypoint");uint64_t lists=0,edges=0;
 for(size_t i=0;i<H;++i){require(old.element_levels_[i]==rebuilt.element_levels_[i],"node levels");require(old.getExternalLabel(i)==rebuilt.getExternalLabel(i),"node labels");require(!std::memcmp(old.getDataByInternalId(i),rebuilt.getDataByInternalId(i),4*d),"profile bytes");
  for(int level=0;level<=old.element_levels_[i];++level){auto*a=old.get_linklist_at_level(i,level);auto*b=rebuilt.get_linklist_at_level(i,level);size_t n=old.getListCount(a);require(n==rebuilt.getListCount(b),"link count");require(!std::memcmp((hnswlib::tableint*)(a+1),(hnswlib::tableint*)(b+1),n*sizeof(hnswlib::tableint)),"ordered link list");++lists;edges+=n;}}
 Counter counter{space.get_dist_func(),space.get_dist_func_param(),0};old.fstdistfunc_=counted;rebuilt.fstdistfunc_=counted;old.dist_func_param_=&counter;rebuilt.dist_func_param_=&counter;size_t queries=0;
 for(const auto&j:c["query_inputs"]){auto q=raw<float>(j["path"].get<std::string>());bool fvec=j["fvecs"];size_t stride=d+(fvec?1:0);require(q.size()%stride==0,"query shape");size_t n=q.size()/stride;
  for(size_t i=0;i<n;++i){const float*x=q.data()+i*stride+(fvec?1:0);counter.n=0;auto a=old.searchKnn(x,3);auto na=counter.n;counter.n=0;auto b=rebuilt.searchKnn(x,3);require(na==counter.n&&a.size()==3&&b.size()==3,"query counts");while(!a.empty()){auto av=a.top(),bv=b.top();require(av.second==bv.second&&!std::memcmp(&av.first,&bv.first,4),"route labels/distance bits");a.pop();b.pop();}++queries;}}
 json result={{"status","PASS"},{"H",H},{"dimension",d},{"input_load_seconds",input_seconds},{"router_build_seconds",build_seconds},{"router_save_seconds",save_seconds},{"audit_seconds",elapsed(auditstart)},{"ordered_lists_checked",lists},{"ordered_edges_checked",edges},{"query_parity_pairs",queries},{"new_ANN_calls",2*queries},{"new_NSG_calls",0},{"graph_semantic_identity",true},{"graph_file_bytes",fs::file_size(out/"router.hnsw")},{"method","serial original hnswlib insertion M16 efConstruction200 seed20260828 ef10"},{"full_query_QPS_measured",false}};
 std::ofstream o(out/"complete.json");o<<result.dump(2)<<'\n';std::cout<<result.dump(2)<<std::endl;return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

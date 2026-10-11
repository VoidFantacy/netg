#pragma once
// IO/loading conventions derived from the preserved ACSG E118/E166 harness.
// This campaign routes in the actual benches/test.cpp heap-pop order.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <memory>
#include <set>
#include <stdexcept>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <sys/resource.h>
#include <sched.h>
#include <unistd.h>
#include <dlfcn.h>
#include <xmmintrin.h>
#include <omp.h>
#include <nlohmann/json.hpp>
#include <ACSG/IndexACSG.h>
#include <hnswlib/hnswlib.h>
namespace exp172 {
using json=nlohmann::json; namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
inline void require(bool ok,const std::string&s){if(!ok)throw std::runtime_error(s);}
inline double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
inline json read_json(const fs::path&p){std::ifstream f(p);require(bool(f),"open JSON "+p.string());json j;f>>j;return j;}
inline void write_json(const fs::path&p,const json&j){fs::create_directories(p.parent_path());auto tmp=p;tmp+=".tmp";{std::ofstream f(tmp);f<<j.dump(2)<<'\n';require(bool(f),"write JSON");}fs::rename(tmp,p);}
template<class T>std::vector<T> read_raw(const fs::path&p){std::ifstream f(p,std::ios::binary|std::ios::ate);require(bool(f),"open raw "+p.string());auto z=f.tellg();require(z>=0&&size_t(z)%sizeof(T)==0,"raw size");std::vector<T>a(size_t(z)/sizeof(T));f.seekg(0);f.read((char*)a.data(),z);require(bool(f),"read raw");return a;}
template<class T>void write_raw(const fs::path&p,const std::vector<T>&a){fs::create_directories(p.parent_path());require(!fs::exists(p),"preserve raw "+p.string());std::ofstream f(p,std::ios::binary);f.write((const char*)a.data(),a.size()*sizeof(T));require(bool(f),"write raw");}
inline int process_threads(){std::ifstream f("/proc/self/status");std::string l;while(std::getline(f,l))if(l.rfind("Threads:",0)==0)return std::stoi(l.substr(8));throw std::runtime_error("thread count");}
inline void threads(){for(auto key:{"OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"}){const char*v=getenv(key);require(v&&std::string(v)=="1",std::string(key)+"=1 required");}omp_set_dynamic(0);omp_set_num_threads(1);require(process_threads()==1,"actual one thread required");cpu_set_t set;CPU_ZERO(&set);require(!sched_getaffinity(0,sizeof(set),&set)&&CPU_COUNT(&set)==1&&CPU_ISSET(15,&set),"CPU15 required");}
inline void resource_guard(const json&c,const fs::path&p){struct statvfs v;require(!statvfs(p.c_str(),&v),"statvfs");require(uint64_t(v.f_bavail)*v.f_frsize>=c["min_free_bytes"].get<uint64_t>(),"free bytes reserve");struct rusage u;getrusage(RUSAGE_SELF,&u);require(uint64_t(u.ru_maxrss)*1024<=c["maxrss_bytes"].get<uint64_t>(),"RSS cap");threads();}
struct Fvecs{int fd;size_t bytes,n,d;void*ptr;explicit Fvecs(const std::string&p){fd=open(p.c_str(),O_RDONLY);require(fd>=0,"open fvecs");struct stat s;require(!fstat(fd,&s),"stat fvecs");bytes=s.st_size;ptr=mmap(nullptr,bytes,PROT_READ,MAP_SHARED,fd,0);require(ptr!=MAP_FAILED,"mmap");d=*(int32_t*)ptr;require(d>0&&bytes%((d+1)*4)==0,"fvecs shape");n=bytes/((d+1)*4);}const float*row(size_t i)const{require(i<n,"base bounds");return (float*)ptr+i*(d+1)+1;}~Fvecs(){munmap(ptr,bytes);close(fd);}};
inline json bind_loaded_base(acsg::IndexACSGFlat&idx,const json&c){
 const fs::path receipt=c.contains("embedded_domain")?fs::path(c["embedded_domain"].get<std::string>()):fs::path(c.at("data_domain").get<std::string>()).parent_path()/(c.at("dataset").get<std::string>()+".embedded_base_domain.json");
 const auto r=read_json(receipt);require(r.at("status")=="FULL_EMBEDDED_BASE_WORDS_EQUAL_REGISTERED_BASE"&&r.at("exact_float_words_equal").get<bool>()&&r.at("actual_codes_full_finite").get<bool>(),"complete actual embedded domain dependency");
 require(r.at("N")==idx.ntotal&&r.at("dimension")==idx.d,"embedded loaded dimensions");std::string base;bool index_bound=false;
 for(auto it=r.at("source_stats_after").begin();it!=r.at("source_stats_after").end();++it){struct stat s;require(!::stat(it.key().c_str(),&s),"bound source stat");const auto&expected=it.value();require(expected.at("bytes")==s.st_size&&expected.at("mtime_ns")==uint64_t(s.st_mtim.tv_sec)*1000000000ULL+uint64_t(s.st_mtim.tv_nsec)&&expected.at("device")==s.st_dev&&expected.at("inode")==s.st_ino,"full-word/hash bound file identity changed");if(it.key()==c.at("index").get<std::string>())index_bound=true;else base=it.key();}
 require(index_bound&&!base.empty(),"loaded original index exact receipt identity");auto*flat=dynamic_cast<faiss::IndexFlat*>(idx.storage);require(flat,"original Flat codes actual type");const auto before=Clock::now();
 {Fvecs registered(base);require(registered.n==size_t(idx.ntotal)&&registered.d==size_t(idx.d),"registered loaded dimensions");const float*codes=flat->get_xb();for(size_t i=0;i<registered.n;++i)require(!memcmp(codes+i*idx.d,registered.row(i),idx.d*4),"ACTUAL loaded code word differs from bound registered base");}
 const auto registered=read_json(r.at("registered_domain_receipt").get<std::string>());const auto layout=registered.at("index_layout");require(idx.acsg.final_graph&&idx.acsg.final_graph->N==idx.ntotal&&idx.acsg.final_graph->K==layout.at("degree"),"actual loaded graph dimensions");
 const std::string source=c.at("index");int fd=open(source.c_str(),O_RDONLY);require(fd>=0,"loaded graph binding file");struct stat stat_graph;require(!fstat(fd,&stat_graph),"graph binding stat");void*image=mmap(nullptr,stat_graph.st_size,PROT_READ,MAP_SHARED,fd,0);require(image!=MAP_FAILED,"graph binding mmap");const size_t graph_bytes=layout.at("graph_bytes");const bool graph_equal=!memcmp(static_cast<const uint8_t*>(image)+layout.at("graph_offset").get<size_t>(),idx.acsg.final_graph->data,graph_bytes);munmap(image,stat_graph.st_size);close(fd);require(graph_equal,"ACTUAL loaded graph words/order differ from source proof graph");
 return {{"status","FULL_LIVE_LOADED_CODES_WORD_BOUND"},{"embedded_receipt",receipt.string()},{"live_words_compared",uint64_t(idx.ntotal)*idx.d},{"loaded_code_address",reinterpret_cast<uintptr_t>(flat->get_xb())},{"live_graph_words_equal",graph_equal},{"live_graph_words_compared",graph_bytes/4},{"loaded_graph_address",reinterpret_cast<uintptr_t>(idx.acsg.final_graph->data)},{"startup_seconds",seconds(before)},{"source_sha256",r.at("source_sha256")},{"scope","all actual loaded code and ordered graph pointer contents, not only source path or serialized identity"}};
}
inline std::unique_ptr<acsg::IndexACSGFlat> load_nsg(const std::string&p){auto i=std::make_unique<acsg::IndexACSGFlat>();i->loadACPG(p.c_str());std::vector<float>().swap(i->acsg.pheromone);std::vector<float>().swap(i->acsg.weight);require(i->metric_type==faiss::METRIC_INNER_PRODUCT,"raw IP only");return i;}
using HNSW=hnswlib::HierarchicalNSW<float>;
struct RouteData{std::array<int32_t,3>ids{};std::array<float,3>distances{};};
struct RouteCounter{hnswlib::DISTFUNC<float>fn;void*param;uint64_t calls=0;};
inline float route_counted(const void*a,const void*b,const void*p){auto*c=(RouteCounter*)p;++c->calls;return c->fn(a,b,c->param);}
struct NativeRouter{
 size_t d;std::vector<int32_t>ids;std::vector<float>profiles;hnswlib::InnerProductSpace space;std::unique_ptr<HNSW>graph;RouteCounter counter;
 NativeRouter(const json&c,size_t dim):d(dim),space(d),counter{space.get_dist_func(),space.get_dist_func_param(),0}{ids=read_raw<int32_t>(c["ids"].get<std::string>());profiles=read_raw<float>(c["W"].get<std::string>());require(profiles.size()==ids.size()*d,"profiles shape");require(std::set<int32_t>(ids.begin(),ids.end()).size()==ids.size(),"hub IDs distinct");graph=std::make_unique<HNSW>(&space,c["graph"].get<std::string>(),false,ids.size());graph->setEf(10);for(size_t i=0;i<ids.size();++i){require(graph->getExternalLabel(i)==size_t(ids[i]),"actual real labels");require(!memcmp(graph->getDataByInternalId(i),profiles.data()+i*d,d*4),"profile bytes");}}
 void counting(bool yes){graph->fstdistfunc_=yes?route_counted:counter.fn;graph->dist_func_param_=yes?(void*)&counter:space.get_dist_func_param();}
 RouteData route(const float*q){counter.calls=0;auto h=graph->searchKnn(q,3);require(h.size()==3,"actual top3");RouteData r;for(int j=0;j<3;++j){r.ids[j]=h.top().second;r.distances[j]=h.top().first;h.pop();}return r;}
 json binding()const{Dl_info i{};const void*p=reinterpret_cast<const void*>(counter.fn);dladdr(p,&i);const auto address=reinterpret_cast<uintptr_t>(p),base=reinterpret_cast<uintptr_t>(i.dli_fbase);return {{"dimension",d},{"callback_address",address},{"image_base_address",base},{"callback_image_offset",address-base},{"callback_symbol",i.dli_sname?i.dli_sname:"UNRESOLVED"},{"shared_object",i.dli_fname?i.dli_fname:"UNRESOLVED"},{"mxcsr",_mm_getcsr()},{"ef",10},{"label_order","actual maxheap pop; no resort"}};}
};
struct CounterDC:faiss::DistanceComputer{
 std::unique_ptr<faiss::DistanceComputer>inner;uint64_t count=0;std::array<int32_t,3>first{-1,-1,-1};
 explicit CounterDC(faiss::DistanceComputer*p):inner(p){}
 void set_query(const float*q)override{count=0;first={-1,-1,-1};inner->set_query(q);}
 float operator()(faiss::idx_t id)override{if(count<3)first[count]=id;++count;return (*inner)(id);}
 float symmetric_dis(faiss::idx_t a,faiss::idx_t b)override{return inner->symmetric_dis(a,b);}
};
struct Batch{
 size_t n,k;std::vector<int32_t>ids,entries;std::vector<float>distances,profile_distances;std::vector<uint64_t>route_ndc,graph_ndc;
 Batch(size_t nn,size_t kk):n(nn),k(kk),ids(n*k),entries(n*3),distances(n*k),profile_distances(n*3),route_ndc(n),graph_ndc(n){}
 void save(const fs::path&p,bool counting)const{fs::create_directories(p);if(!counting){write_raw(p/"ids.i32",ids);write_raw(p/"distances.f32",distances);write_raw(p/"entry_ids.i32",entries);write_raw(p/"profile_distances.f32",profile_distances);}else{write_raw(p/"route_ndc.u64",route_ndc);write_raw(p/"graph_ndc.u64",graph_ndc);}}
};
inline void same(const Batch&a,const Batch&b){require(a.n==b.n&&a.k==b.k&&a.ids==b.ids&&a.entries==b.entries&&!memcmp(a.distances.data(),b.distances.data(),a.distances.size()*4)&&!memcmp(a.profile_distances.data(),b.profile_distances.data(),a.profile_distances.size()*4),"ID/distance/entry/profile bits parity");}
inline void native_batch(acsg::IndexACSGFlat&idx,NativeRouter&r,const std::vector<float>&q,int L,Batch&b,bool counting){
 const size_t d=idx.d;idx.acsg.search_L=L;r.counting(counting);
 std::vector<std::vector<acsg::EnterPoint>> all_eps(b.n);
 for(size_t i=0;i<b.n;++i){auto route=r.route(q.data()+i*d);for(int j=0;j<3;++j){all_eps[i].emplace_back(route.ids[j],1.f);b.entries[i*3+j]=route.ids[j];b.profile_distances[i*3+j]=route.distances[j];}if(counting)b.route_ndc[i]=r.counter.calls;}
 faiss::VisitedTable vt(idx.ntotal);std::unique_ptr<faiss::DistanceComputer> computer;CounterDC* count=nullptr;if(counting){count=new CounterDC(acsg::storage_distance_computer(idx.storage));computer.reset(count);}else computer.reset(acsg::storage_distance_computer(idx.storage));auto&dc=*computer;
 std::vector<acsg::Neighbor>ret;std::vector<faiss::idx_t>out(b.k);
 for(size_t i=0;i<b.n;++i){dc.set_query(q.data()+i*d);vt.advance();idx.acsg.search_new(dc,b.k,out.data(),b.distances.data()+i*b.k,vt,2,all_eps[i],&ret);for(size_t j=0;j<b.k;++j)b.ids[i*b.k+j]=out[j];if(counting){b.graph_ndc[i]=count->count;require(count->first==std::array<int32_t,3>{b.entries[3*i],b.entries[3*i+1],b.entries[3*i+2]},"actual initial callback order");}}
}
}

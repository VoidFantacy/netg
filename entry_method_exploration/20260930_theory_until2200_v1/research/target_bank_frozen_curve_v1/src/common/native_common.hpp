#pragma once
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <numeric>
#include <set>
#include <stdexcept>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <sys/resource.h>
#include <unistd.h>
#include <omp.h>
#include <nlohmann/json.hpp>
#include <ACSG/IndexACSG.h>
#include <hnswlib/hnswlib.h>
using json=nlohmann::json;namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
inline double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
inline void require(bool ok,const std::string& s){if(!ok)throw std::runtime_error(s);}
inline json read_json(const fs::path& p){std::ifstream f(p);json j;f>>j;return j;}
inline void write_json(const fs::path& p,const json& j){auto tmp=p;tmp+=".tmp";{std::ofstream f(tmp);f<<j.dump(2)<<'\n';require(bool(f),"write "+tmp.string());}fs::rename(tmp,p);}
template<class T> std::vector<T> read_raw(const fs::path& p){std::ifstream f(p,std::ios::binary|std::ios::ate);require(bool(f),"open "+p.string());auto z=f.tellg();require(z>=0&&size_t(z)%sizeof(T)==0,"raw size");std::vector<T> a(size_t(z)/sizeof(T));f.seekg(0);f.read((char*)a.data(),z);require(bool(f),"read raw");return a;}
template<class T> void write_raw(const fs::path& p,const std::vector<T>& a){auto tmp=p;tmp+=".tmp";{std::ofstream f(tmp,std::ios::binary);f.write((const char*)a.data(),a.size()*sizeof(T));require(bool(f),"write raw");}fs::rename(tmp,p);}
struct Fvecs{
 int fd;size_t bytes,n,d;void* ptr;
 explicit Fvecs(const std::string& p){fd=open(p.c_str(),O_RDONLY);require(fd>=0,"open fvecs");struct stat s;fstat(fd,&s);bytes=s.st_size;ptr=mmap(nullptr,bytes,PROT_READ,MAP_SHARED,fd,0);require(ptr!=MAP_FAILED,"mmap fvecs");d=*(int32_t*)ptr;require(d>0&&bytes%((d+1)*4)==0,"fvecs shape");n=bytes/((d+1)*4);}
 const float* row(size_t i)const{return (float*)ptr+i*(d+1)+1;}
 ~Fvecs(){munmap(ptr,bytes);close(fd);}
};
inline void resources(const fs::path& out){struct statvfs v;require(statvfs(out.c_str(),&v)==0,"statvfs");require(uint64_t(v.f_bavail)*v.f_frsize>=2147483648ULL,"disk below 2GiB");struct rusage r;getrusage(RUSAGE_SELF,&r);require(uint64_t(r.ru_maxrss)*1024<=103079215104ULL,"RSS above 96GiB");}
inline std::unique_ptr<acsg::IndexACSGFlat> load_nsg(const std::string& p){auto idx=std::make_unique<acsg::IndexACSGFlat>();idx->loadACPG(p.c_str());std::vector<float>().swap(idx->acsg.pheromone);std::vector<float>().swap(idx->acsg.weight);require(idx->metric_type==faiss::METRIC_INNER_PRODUCT||idx->metric_type==faiss::METRIC_L2,"L2/IP graph required");return idx;}
inline void normalize(float* q,size_t d){double norm=0;for(size_t j=0;j<d;++j)norm+=double(q[j])*q[j];require(norm>0&&std::isfinite(norm),"query norm");double inv=1/std::sqrt(norm);for(size_t j=0;j<d;++j)q[j]=float(q[j]*inv);}

inline std::unique_ptr<hnswlib::SpaceInterface<float>> make_space(int metric,size_t d){require(metric==0||metric==1,"metric must be IP=0 or L2=1");if(metric==0)return std::make_unique<hnswlib::InnerProductSpace>(d);return std::make_unique<hnswlib::L2Space>(d);}

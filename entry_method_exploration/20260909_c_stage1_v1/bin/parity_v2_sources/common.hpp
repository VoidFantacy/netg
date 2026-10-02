#pragma once
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>
#include <nlohmann/json.hpp>
#include <omp.h>
#include <ACSG/IndexACSG.h>
#include <hnswlib/hnswlib.h>
using json = nlohmann::json;
using Clock = std::chrono::steady_clock;
namespace fs = std::filesystem;
inline void require(bool ok, const std::string& s) { if(!ok) throw std::runtime_error(s); }
inline double seconds(Clock::time_point t) { return std::chrono::duration<double>(Clock::now()-t).count(); }
inline json read_json(const fs::path& p) { std::ifstream f(p); require(bool(f),p.string()); json j; f>>j; return j; }
inline void write_json(const fs::path& p,const json& j) { std::ofstream f(p); f<<j.dump(2)<<'\n'; require(bool(f),p.string()); }
template<class T> std::vector<T> read_raw(const fs::path& p) {
    std::ifstream f(p,std::ios::binary|std::ios::ate); require(bool(f),p.string()); auto n=f.tellg();
    require(n>=0 && size_t(n)%sizeof(T)==0,"bad raw size"); std::vector<T> a(size_t(n)/sizeof(T));
    f.seekg(0);f.read(reinterpret_cast<char*>(a.data()),n);require(bool(f),"bad raw read");return a;
}
inline thread_local uint64_t* route_counter=nullptr;
struct SpaceParam { hnswlib::DISTFUNC<float> fn; void* p; };
inline float counted_ip(const void* a,const void* b,const void* p) {
    if(route_counter) ++*route_counter;
    auto x=static_cast<const SpaceParam*>(p);return x->fn(a,b,x->p);
}
struct CountSpace: hnswlib::SpaceInterface<float> {
    hnswlib::InnerProductSpace inner; SpaceParam param;
    explicit CountSpace(int d):inner(d),param{inner.get_dist_func(),inner.get_dist_func_param()}{}
    size_t get_data_size() override{return inner.get_data_size();}
    hnswlib::DISTFUNC<float> get_dist_func() override{return counted_ip;}
    void* get_dist_func_param() override{return &param;}
};
struct Route {std::vector<int> ids; std::vector<float> distances; uint64_t ndc=0; double wall=0;};
struct Router {
    CountSpace space; hnswlib::HierarchicalNSW<float> graph;
    Router(int d,const std::vector<float>& p,const std::vector<int>& ids):space(d),graph(&space,ids.size(),16,200,20260828) {
        require(p.size()==ids.size()*d,"prototype shape");
        for(size_t i=0;i<ids.size();++i) graph.addPoint(p.data()+i*d,ids[i]); graph.setEf(10);
    }
    Route run(const float* q,int k) {
        Route r; r.ids.resize(k);r.distances.resize(k);route_counter=&r.ndc;auto t=Clock::now();
        auto heap=graph.searchKnn(q,k);r.wall=seconds(t);route_counter=nullptr;
        require(heap.size()==size_t(k),"route short");
        for(int j=k;j-->0;){r.ids[j]=heap.top().second;r.distances[j]=heap.top().first;heap.pop();} return r;
    }
};
struct CountDC:faiss::DistanceComputer {
    std::unique_ptr<faiss::DistanceComputer> inner; uint64_t count=0;std::vector<int> order;bool trace=false;
    explicit CountDC(faiss::DistanceComputer* p,bool trace_=false):inner(p),trace(trace_){}
    void set_query(const float* q) override{inner->set_query(q);}
    float operator()(faiss::idx_t i) override{++count;if(trace)order.push_back(i);return (*inner)(i);}
    float symmetric_dis(faiss::idx_t i,faiss::idx_t j) override{return inner->symmetric_dis(i,j);}
};
struct Dataset {
    json c; std::vector<float> queries,prototypes;std::vector<int> hubs;std::vector<int64_t> row_ids;
    acsg::IndexACSGFlat index;std::unique_ptr<Router> router;
    explicit Dataset(const fs::path& config):c(read_json(config)) {
        require(c.at("query_split")=="drl_train","split restriction");
        queries=read_raw<float>(c.at("queries_file").get<std::string>());
        prototypes=read_raw<float>(c.at("prototypes").get<std::string>());
        hubs=read_raw<int>(c.at("hub_ids").get<std::string>());
        row_ids=read_raw<int64_t>(c.at("row_ids").get<std::string>());
        require(row_ids.size()==2000 && queries.size()==row_ids.size()*c.at("dim").get<size_t>(),"query shape");
        for(auto id:row_ids)require(id>=0 && id<10000,"sample out of scope");
        require(std::set<int64_t>(row_ids.begin(),row_ids.end()).size()==row_ids.size(),"duplicate query rows");
        index.loadACPG(c.at("index_path").get<std::string>().c_str());
        require(index.ntotal==c.at("base_count").get<int>() && index.d==c.at("dim").get<int>() && index.metric_type==faiss::METRIC_INNER_PRODUCT,"index identity");
        require(index.acsg.final_graph->K==64,"degree");
        for(auto id:hubs)require(id>=0 && id<index.ntotal,"hub invalid");
        router=std::make_unique<Router>(index.d,prototypes,hubs);
    }
    const float* query(size_t i)const{return queries.data()+i*index.d;}
};

// The only modified search operation is a training-only edge keep/remove hook.
#define E33_ENABLE_EDGE_HOOK
#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
#include <queue>
#include <random>
#include <sched.h>

namespace e33 {
using Graph=hnswlib::HierarchicalNSW<float>;
struct Environment;
thread_local Environment* active=nullptr;
thread_local std::string error;
bool decide(uint32_t,size_t,uint32_t);

struct Environment {
    json config;size_t dim,h,n;
    std::vector<float> q,w;
    std::vector<int32_t> mapping;
    CountSpace space;
    std::unique_ptr<Graph> graph;
    std::unique_ptr<acsg::IndexACSGFlat> index;
    std::unique_ptr<NativeWork> worker;
    std::vector<std::vector<int32_t>> adjacent;
    std::vector<int32_t> offsets,src,dst;
    std::vector<uint8_t> protected_edges;
    std::vector<int32_t> ids,entries,actions,action_offsets;
    std::vector<uint32_t> route_ndc,graph_ndc;
    std::vector<float> distances;
    uint64_t calls=0,route_calls=0;
    std::mt19937_64 rng;
    const double* probabilities=nullptr;
    const uint8_t* mask=nullptr;
    bool trace=false;
    Environment(const json& c,const fs::path& folder,bool load_nsg):config(c),dim(c.at("dim")),h(c.at("hub_count")),n(c.at("num_queries")),
        q(read_raw<float>(c.at("queries_file"))),w(read_raw<float>(c.at("policy").at("W"))),mapping(read_raw<int32_t>(c.at("hub_ids"))),space(dim) {
        require(q.size()==n*dim && w.size()==h*dim && mapping.size()==h,"environment shape mismatch");
        finite_matrix(q,"queries");finite_matrix(w,"profiles");fs::create_directories(folder);
        auto file=folder/"base.hnsw";
        if(fs::exists(file))graph=std::make_unique<Graph>(&space,file.string(),false,h);
        else {
            graph=std::make_unique<Graph>(&space,h,16,200,20260828);
            for(size_t i=0;i<h;++i)graph->addPoint(w.data()+i*dim,size_t(mapping[i]));
            graph->saveIndex(file.string());
        }
        graph->setEf(10);require(graph->cur_element_count==h,"base HNSW size mismatch");
        adjacent.resize(h);offsets.push_back(0);
        for(size_t i=0;i<h;++i) {
            require(graph->getExternalLabel(i)==size_t(mapping[i]),"HNSW external mapping mismatch");
            require(std::memcmp(graph->getDataByInternalId(i),w.data()+i*dim,dim*sizeof(float))==0,"HNSW vector mismatch");
            auto* row=graph->get_linklist0(i);size_t degree=graph->getListCount(row);auto* neighbours=(hnswlib::tableint*)(row+1);
            require(degree>=1,"base node has no outgoing neighbours");std::set<int32_t> unique;
            for(size_t j=0;j<degree;++j) {
                int32_t v=neighbours[j];require(v>=0 && size_t(v)<h && v!=int32_t(i) && unique.insert(v).second,"invalid base edge");
                adjacent[i].push_back(v);src.push_back(i);dst.push_back(v);
            }
            offsets.push_back(dst.size());
        }
        protected_edges.assign(dst.size(),0);std::vector<std::vector<int32_t>> reverse(h);
        for(size_t e=0;e<dst.size();++e)reverse[dst[e]].push_back(e);
        auto tree=[&](bool reversed) {
            std::vector<uint8_t> seen(h,0);std::queue<int32_t> todo;todo.push(graph->enterpoint_node_);seen[graph->enterpoint_node_]=1;
            while(!todo.empty()) {
                int32_t u=todo.front();todo.pop();std::vector<int32_t> row;
                if(reversed)row=reverse[u];else for(int32_t e=offsets[u];e<offsets[u+1];++e)row.push_back(e);
                for(int32_t e:row) {int32_t v=reversed?src[e]:dst[e];if(!seen[v]){seen[v]=1;todo.push(v);protected_edges[e]=1;}}
            }
            require(std::count(seen.begin(),seen.end(),uint8_t(1))==int(h),"base graph not strongly connected");
        };
        tree(false);tree(true);auto fn=space.get_dist_func();auto param=space.get_dist_func_param();
        for(size_t u=0;u<h;++u) {
            std::vector<std::pair<float,int32_t>> ranked;
            for(int32_t e=offsets[u];e<offsets[u+1];++e)ranked.push_back({fn(w.data()+u*dim,w.data()+size_t(dst[e])*dim,param),e});
            std::sort(ranked.begin(),ranked.end(),[&](auto a,auto b){return a.first<b.first || (a.first==b.first && mapping[dst[a.second]]<mapping[dst[b.second]]);});
            for(size_t j=0;j<std::min(size_t(2),ranked.size());++j)protected_edges[ranked[j].second]=1;
        }
        auto info=folder/"topology.json";
        json topology={{"nodes",h},{"edges",src.size()},{"protected_edges",std::count(protected_edges.begin(),protected_edges.end(),1)},
            {"start_internal_id",graph->enterpoint_node_},{"maxlevel",graph->maxlevel_},{"maxM0",graph->maxM0_},{"efSearch",10},{"strongly_connected",true},
            {"source",src},{"target",dst},{"offsets",offsets},{"protected",protected_edges}};
        if(fs::exists(info)){std::ifstream f(info);json previous;f>>previous;require(previous==topology,"topology metadata mismatch");}else write_json(info,topology);
        if(load_nsg) {
            index=std::make_unique<acsg::IndexACSGFlat>();index->loadACPG(c.at("index_path").get<std::string>().c_str());
            std::vector<float>().swap(index->acsg.pheromone);std::vector<float>().swap(index->acsg.weight);
            require(index->d==int(dim) && index->metric_type==faiss::METRIC_INNER_PRODUCT,"wrong native index");
            for(int32_t v:mapping)require(v>=0 && v<index->ntotal,"hub outside native index");
            index->acsg.search_L=128;worker=std::make_unique<NativeWork>(*index,true);worker->retset.reserve(801);
        }
    }
    bool edge(uint32_t u,size_t j,uint32_t v) {
        int32_t e=offsets.at(u)+j;require(src.at(e)==int32_t(u) && dst.at(e)==int32_t(v),"edge addressing mismatch");
        if(protected_edges[e])return true;
        bool keep=mask?bool(mask[e]):(std::generate_canonical<double,53>(rng)<probabilities[e]);
        if(trace)actions.push_back(e*2+int(keep));return keep;
    }
    Decision route(Graph& g,const float* query) {
        uint64_t count=0;route_counter=&count;auto heap=g.searchKnn(query,3);route_counter=nullptr;++route_calls;
        require(heap.size()==3,"HNSW returned fewer than three");Decision d;
        for(int j=0;j<3;++j){d.ids[j]=heap.top().second;heap.pop();}
        std::sort(d.ids.begin(),d.ids.end());require(d.ids[0]!=d.ids[1] && d.ids[1]!=d.ids[2],"duplicate entries");
        d.labels=d.ids;d.ndc=count;return d;
    }
    void run(const int32_t* rows,size_t count,const double* p,const uint8_t* fixed,uint64_t seed,bool search,bool record,bool gated=true) {
        require(!search || bool(index),"NSG not loaded");
        if(!fixed)for(size_t e=0;e<src.size();++e)require(std::isfinite(p[e]) && p[e]>=0 && p[e]<=1,"invalid probability");
        else for(size_t e=0;e<src.size();++e)require(fixed[e]<=1 && (!protected_edges[e] || fixed[e]),"invalid mask/protected edge removed");
        ids.assign(count*K,-1);entries.resize(count*3);distances.assign(count*K,0);route_ndc.resize(count);graph_ndc.assign(count,0);
        actions.clear();action_offsets.clear();action_offsets.push_back(0);probabilities=p;mask=fixed;trace=record;active=this;hnswlib::edge_hook=gated?decide:nullptr;
        for(size_t i=0;i<count;++i) {
            int32_t row=rows[i];require(row>=0 && size_t(row)<n,"query row out of range");rng.seed(seed+0x9e3779b97f4a7c15ULL*i);
            Decision d=route(*graph,q.data()+size_t(row)*dim);std::copy(d.ids.begin(),d.ids.end(),entries.begin()+3*i);route_ndc[i]=d.ndc;
            if(search) {Search s=worker->search(*index,q.data()+size_t(row)*dim,d,3);++calls;
                std::copy(s.ids.begin(),s.ids.end(),ids.begin()+i*K);std::copy(s.distances.begin(),s.distances.end(),distances.begin()+i*K);graph_ndc[i]=s.ndc;}
            action_offsets.push_back(actions.size());
        }
        hnswlib::edge_hook=nullptr;active=nullptr;probabilities=nullptr;mask=nullptr;
    }
    void run_static(const int32_t* rows,size_t count,const std::string& path) {
        auto original=std::move(graph);
        try {
            graph=std::make_unique<Graph>(&space,path,false,h);graph->setEf(10);
            std::vector<uint8_t> keep(src.size(),1);run(rows,count,nullptr,keep.data(),0,true,false,false);
        } catch(...) {graph=std::move(original);throw;}
        graph=std::move(original);
    }
    void physical(Graph& g,const uint8_t* fixed) {
        for(size_t u=0;u<h;++u) {
            auto* row=g.get_linklist0(u);auto* out=(hnswlib::tableint*)(row+1);size_t keep=0;
            for(int32_t e=offsets[u];e<offsets[u+1];++e) {require(fixed[e]<=1 && (!protected_edges[e] || fixed[e]),"protected edge removed on export");if(fixed[e])out[keep++]=dst[e];}
            require(keep>=std::min(size_t(2),adjacent[u].size()),"physical degree below original-compatible minimum");g.setListCount(row,keep);
            for(size_t j=keep;j<g.maxM0_;++j)out[j]=0;
        }
    }
    void export_graph(const uint8_t* fixed,const std::string& path) {
        require(!fs::exists(path),"refuse existing exported graph");Graph copy(&space,config.at("graph_file").get<std::string>(),false,h);physical(copy,fixed);copy.saveIndex(path);
    }
    void parity(const int32_t* rows,size_t count,const uint8_t* fixed,bool native) {
        Graph copy(&space,config.at("graph_file").get<std::string>(),false,h);copy.setEf(10);physical(copy,fixed);run(rows,count,nullptr,fixed,1,native,true);hnswlib::edge_hook=nullptr;
        std::unique_ptr<Work> reference;if(native)reference=std::make_unique<Work>(*index,true);
        for(size_t i=0;i<count;++i) {
            Decision d=route(copy,q.data()+size_t(rows[i])*dim);
            require(std::equal(d.ids.begin(),d.ids.end(),entries.begin()+i*3) && d.ndc==route_ndc[i],"hook/physical route mismatch");
            if(native) {std::vector<int32_t> e(d.ids.begin(),d.ids.end());Search s=reference->run(*index,q.data()+size_t(rows[i])*dim,e,{0,1,2},3);++calls;
                require(std::equal(s.ids.begin(),s.ids.end(),ids.begin()+i*K) && s.ndc==graph_ndc[i] && std::memcmp(s.distances.data(),distances.data()+i*K,K*sizeof(float))==0,"original NSG mismatch");}
        }
    }
};
bool decide(uint32_t u,size_t j,uint32_t v){return active->edge(u,j,v);}
}
extern "C" {
const char* e33_error(){return e33::error.c_str();}
void* e33_create(const char* cfg,const char* dir,int load) {try{return new e33::Environment(json::parse(cfg),dir,bool(load));}catch(const std::exception& e){e33::error=e.what();return nullptr;}}
void e33_destroy(void* env){delete static_cast<e33::Environment*>(env);}
int e33_run(void* ptr,const int32_t* rows,size_t n,const double* p,const uint8_t* mask,uint64_t seed,int search,int trace) {
    try{static_cast<e33::Environment*>(ptr)->run(rows,n,p,mask,seed,bool(search),bool(trace));return 0;}
    catch(const std::exception& e){hnswlib::edge_hook=nullptr;e33::active=nullptr;e33::error=e.what();return -1;}}
int e33_static(void* ptr,const int32_t* rows,size_t n,const char* path) {try{static_cast<e33::Environment*>(ptr)->run_static(rows,n,path);return 0;}catch(const std::exception& e){e33::error=e.what();return -1;}}
int e33_export(void* ptr,const uint8_t* mask,const char* path) {try{static_cast<e33::Environment*>(ptr)->export_graph(mask,path);return 0;}catch(const std::exception& e){e33::error=e.what();return -1;}}
int e33_parity(void* ptr,const int32_t* rows,size_t n,const uint8_t* mask,int native) {
    try{static_cast<e33::Environment*>(ptr)->parity(rows,n,mask,bool(native));return 0;}
    catch(const std::exception& e){hnswlib::edge_hook=nullptr;e33::active=nullptr;e33::error=e.what();return -1;}}
void* e33_data(void* ptr,int field,size_t* length) {
    auto& e=*static_cast<e33::Environment*>(ptr);
    switch(field) {
        case 0:*length=e.ids.size();return e.ids.data();case 1:*length=e.entries.size();return e.entries.data();
        case 2:*length=e.route_ndc.size();return e.route_ndc.data();case 3:*length=e.graph_ndc.size();return e.graph_ndc.data();
        case 4:*length=e.actions.size();return e.actions.data();case 5:*length=e.action_offsets.size();return e.action_offsets.data();
        case 6:*length=e.distances.size();return e.distances.data();default:*length=0;return nullptr;
    }
}
uint64_t e33_calls(void* ptr){return static_cast<e33::Environment*>(ptr)->calls;}
uint64_t e33_routes(void* ptr){return static_cast<e33::Environment*>(ptr)->route_calls;}
}

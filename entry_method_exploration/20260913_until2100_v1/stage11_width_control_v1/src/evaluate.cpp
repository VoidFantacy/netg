#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
#include <cstdlib>
#include <sched.h>

int process_threads() {
    std::ifstream f("/proc/self/status");std::string line;
    while(std::getline(f,line))if(line.rfind("Threads:",0)==0)return std::stoi(line.substr(8));
    throw std::runtime_error("cannot verify process threads");
}
void check_threads(const json& c) {
    require(c.contains("threads") && c.at("threads")==1,"explicit threads=1 required");
    for(const char* key:{"OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"}) {
        const char* v=std::getenv(key);require(v && std::string(v)=="1",std::string(key)+"=1 required");
    }
    omp_set_dynamic(0);omp_set_num_threads(1);int observed=0;
    #pragma omp parallel
    {
        #pragma omp single
        observed=omp_get_num_threads();
    }
    require(observed==1 && process_threads()==1,"actual threads are not one");
    cpu_set_t cpus;CPU_ZERO(&cpus);require(sched_getaffinity(0,sizeof(cpus),&cpus)==0,"cannot get CPU affinity");
    require(CPU_COUNT(&cpus)==1 && CPU_ISSET(c.at("query_cpu").get<int>(),&cpus),"wrong CPU affinity");
}
void plain(acsg::IndexACSGFlat& index,const Policy& p,const std::vector<float>& q,size_t d,NativeWork& worker,BatchOutput& out) {
    for(size_t i=0;i<out.routes.size();++i) {
        out.routes[i]=p.route(q.data()+i*d);
        out.searches[i]=worker.search(index,q.data()+i*d,out.routes[i],p.entry_count());
    }
}
void only_routes(const Policy& p,const std::vector<float>& q,size_t d,BatchOutput& out) {
    for(size_t i=0;i<out.routes.size();++i)out.routes[i]=p.route(q.data()+i*d);
}
void only_graph(acsg::IndexACSGFlat& index,const Policy& p,const std::vector<float>& q,size_t d,NativeWork& worker,BatchOutput& out) {
    for(size_t i=0;i<out.routes.size();++i)out.searches[i]=worker.search(index,q.data()+i*d,out.routes[i],p.entry_count());
}
void bit_compare(const BatchOutput& a,const BatchOutput& b) {
    compare(a,b);
    for(size_t i=0;i<a.routes.size();++i)
        require(std::memcmp(a.searches[i].distances.data(),b.searches[i].distances.data(),K*sizeof(float))==0,"distance bits differ");
}
void save_unscored(const BatchOutput& a,const fs::path& out) {
    fs::create_directories(out);std::vector<int32_t> ids(a.routes.size()*K),entries(a.routes.size()*3);
    std::vector<float> distances(a.routes.size()*K);
    for(size_t i=0;i<a.routes.size();++i) {
        std::copy(a.searches[i].ids.begin(),a.searches[i].ids.end(),ids.begin()+i*K);
        std::copy(a.searches[i].distances.begin(),a.searches[i].distances.end(),distances.begin()+i*K);
        std::copy(a.routes[i].ids.begin(),a.routes[i].ids.end(),entries.begin()+i*3);
    }
    write_raw(out/"ids.i32",ids);write_raw(out/"distances.f32",distances);write_raw(out/"entry_ids.i32",entries);
    if(a.routes.front().candidate_slots[0]>=0) {
        std::vector<int32_t> slots(a.routes.size()*7);std::vector<float> distances7(a.routes.size()*7);
        for(size_t i=0;i<a.routes.size();++i) {
            std::copy(a.routes[i].candidate_slots.begin(),a.routes[i].candidate_slots.end(),slots.begin()+i*7);
            std::copy(a.routes[i].candidate_distances.begin(),a.routes[i].candidate_distances.end(),distances7.begin()+i*7);
        }
        write_raw(out/"candidate_slots.i32",slots);write_raw(out/"candidate_distances.f32",distances7);
    }
}
struct Point {
    json config,record;std::unique_ptr<Policy> p,count;std::unique_ptr<BatchOutput> first,fullcount;
    std::vector<double> seconds;
};
int main(int argc,char** argv) {
    try {
        require(argc==3,"evaluate config.json new_output");std::ifstream f(argv[1]);json c;f>>c;check_threads(c);
        fs::path out=argv[2];require(!fs::exists(out),"refuse existing output");fs::create_directories(out);write_json(out/"config.json",c);
        write_json(out/"thread_contract.json",{{"status","PASS"},{"process_threads",process_threads()},{"actual_openmp_threads",1},{"cpu",c.at("query_cpu")}});
        const size_t n=c.at("num_queries"),d=c.at("dim"),gtk=c.at("gt_k");const int reps=c.value("timing_repeats",0);const bool measured=reps>0;
        require(n>=16 && gtk==100 && (reps==0 || reps==5),"wrong sample/GT/timing contract");
        auto q=read_raw<float>(c.at("queries_file"));auto rows=read_raw<int64_t>(c.at("row_ids"));
        if(c.contains("input_total_rows")) {
            size_t total=c.at("input_total_rows");require(total>=n && q.size()==total*d && rows.size()==total,"declared source shape mismatch");
            q.resize(n*d);rows.resize(n);
        }
        require(q.size()==n*d && rows.size()==n,"input shape mismatch");finite_matrix(q,"raw queries");write_raw(out/"row_ids.i64",rows);
        uint64_t planned=0,calls=0;
        for(const auto& m:c.at("methods"))planned+=(measured?reps+2:2)*n+16+(m.value("component_wall",false)?2*n:0);
        require(planned==c.at("real_call_cap").get<uint64_t>(),"call reservation does not match matrix");
        auto index=std::make_unique<acsg::IndexACSGFlat>();index->loadACPG(c.at("index_path").get<std::string>().c_str());
        std::vector<float>().swap(index->acsg.pheromone);std::vector<float>().swap(index->acsg.weight);
        require(index->d==int(d) && index->metric_type==faiss::METRIC_INNER_PRODUCT,"wrong graph dimension/metric");
        if(c.contains("base_count"))require(index->ntotal==c.at("base_count").get<int64_t>(),"wrong base count");
        NativeWork worker(*index,false),counter(*index,true);worker.retset.reserve(801);counter.retset.reserve(801);Work reference(*index,true);
        std::vector<Point> points;
        for(auto m:c.at("methods")) {
            const int L=m.at("L");require(std::set<int>{64,128,256,400,800}.count(L),"invalid L");
            const std::string name=m.at("name");require(!name.empty() && name.find('/')==std::string::npos,"invalid name");
            m["dim"]=d;
            if(m.at("family")=="nsg") {
                require(index->acsg.enterpoint>=0 && index->acsg.enterpoint<index->ntotal,"NSG entry outside base");
                m["fixed_entry"]=index->acsg.enterpoint;m["k"]=1;m["hub_count"]=0;
            } else {
                require(m.at("k")==3,"three-entry profile required (exact3 or HNSW3)");
                auto ids=read_raw<int32_t>(m.at("mapping"));require(ids.size()==m.at("hub_count").get<size_t>(),"wrong hub mapping size");
                for(auto id:ids)require(id>=0 && id<index->ntotal,"profile ID outside base");
            }
            Point p;p.config=m;p.record={{"name",name},{"family",m.at("family")},{"model_name",m.at("model_name")},{"L",L},{"configuration",m}};
            auto start=Clock::now();p.p=std::make_unique<Policy>(m,out/(name+".hnsw"),false,false);
            p.record["policy_build_seconds"]=std::chrono::duration<double>(Clock::now()-start).count();
            start=Clock::now();p.count=std::make_unique<Policy>(m,out/(name+".hnsw"),true,true);
            p.record["count_policy_load_seconds"]=std::chrono::duration<double>(Clock::now()-start).count();
            p.first=std::make_unique<BatchOutput>(n);p.fullcount=std::make_unique<BatchOutput>(n);points.push_back(std::move(p));
        }
        BatchOutput warm(n),timed(n);json progress=json::array();
        for(int rep=0;rep<(measured?reps:1);++rep) {
            size_t ordinal=0;
            for(int L:{64,128,256,400,800}) {
                std::vector<size_t> selected;for(size_t j=0;j<points.size();++j)if(points[j].config.at("L")==L)selected.push_back(j);
                if(selected.empty()){++ordinal;continue;}
                size_t offset=(c.value("dataset_order",0)+rep+ordinal)%selected.size();++ordinal;
                std::rotate(selected.begin(),selected.begin()+offset,selected.end());index->acsg.search_L=L;
                for(auto j:selected) {
                    auto& p=points[j];
                    if(measured && rep==0){plain(*index,*p.p,q,d,worker,warm);calls+=n;}
                    auto start=Clock::now();plain(*index,*p.p,q,d,worker,timed);calls+=n;
                    const double elapsed=std::chrono::duration<double>(Clock::now()-start).count();
                    if(measured && rep==0)bit_compare(warm,timed);
                    if(rep==0){*p.first=timed;save_unscored(timed,out/p.config.at("name").get<std::string>());}else bit_compare(*p.first,timed);
                    if(measured)p.seconds.push_back(elapsed);
                    json event={{"name",p.config.at("name")},{"repeat",rep},{"L",L},{"seconds",measured?json(elapsed):json(nullptr)}};
                    progress.push_back(event);write_json(out/"timing_progress.json",progress);std::cout<<event.dump()<<std::endl;
                }
            }
        }
        for(auto& p:points) {
            index->acsg.search_L=p.config.at("L");plain(*index,*p.count,q,d,counter,*p.fullcount);calls+=n;bit_compare(*p.first,*p.fullcount);
            const size_t k=p.count->entry_count();
            for(size_t i=0;i<n;++i)if(k==3)require(std::set<int32_t>(p.fullcount->routes[i].ids.begin(),p.fullcount->routes[i].ids.end()).size()==3,"duplicate real entries");
            for(size_t i=0;i<16;++i) {
                const auto& route=p.fullcount->routes[i];std::vector<int32_t> entries(route.ids.begin(),route.ids.begin()+k);
                const auto original=reference.run(*index,q.data()+i*d,entries,{0,1,2},k);++calls;
                const auto& current=p.fullcount->searches[i];
                require(original.ids==current.ids && original.ndc==current.ndc && std::memcmp(original.distances.data(),current.distances.data(),K*sizeof(float))==0,"original kernel parity failed");
            }
            p.record["route_only_seconds"]=nullptr;p.record["graph_only_seconds"]=nullptr;
            if(p.config.value("component_wall",false)) {
                require(measured && p.config.at("L")==128,"component schedule mismatch");BatchOutput separate(n);
                only_routes(*p.p,q,d,separate);auto start=Clock::now();only_routes(*p.p,q,d,separate);
                p.record["route_only_seconds"]=std::chrono::duration<double>(Clock::now()-start).count();
                only_graph(*index,*p.p,q,d,worker,separate);calls+=n;start=Clock::now();only_graph(*index,*p.p,q,d,worker,separate);calls+=n;
                p.record["graph_only_seconds"]=std::chrono::duration<double>(Clock::now()-start).count();bit_compare(separate,*p.first);
            }
        }
        auto gt=read_raw<int64_t>(c.at("gt_file"));
        if(c.contains("input_total_rows")){require(gt.size()==c.at("input_total_rows").get<size_t>()*gtk,"declared GT shape mismatch");gt.resize(n*gtk);}
        require(gt.size()==n*gtk,"GT shape mismatch");
        json result={{"status","COMPLETE"},{"dataset",c.at("dataset")},{"split",c.at("split")},{"queries",n},{"threads",1},
            {"timing_repeats",reps},{"physical_graph_calls",calls},{"GT_opened_after_all_raw_search",true},{"methods",json::array()}};
        for(auto& p:points) {
            auto scores=metrics(*p.fullcount,gt,gtk,out/p.config.at("name").get<std::string>());
            for(auto it=scores.begin();it!=scores.end();++it)p.record[it.key()]=it.value();
            p.record["end_to_end_seconds"]=p.seconds;std::vector<double> rates;
            for(double s:p.seconds)rates.push_back(n/s);p.record["qps_runs"]=rates;std::sort(rates.begin(),rates.end());
            p.record["qps"]=rates.empty()?json(nullptr):json(rates[rates.size()/2]);
            p.record["qps_min"]=rates.empty()?json(nullptr):json(rates.front());p.record["qps_max"]=rates.empty()?json(nullptr):json(rates.back());
            p.record["full_plain_count_parity_queries"]=n;p.record["original_kernel_parity_queries"]=16;p.record["repeated_output_parity"]=true;
            p.record["physical_graph_calls"]=(measured?reps+2:2)*n+16+(p.config.value("component_wall",false)?2*n:0);
            result["methods"].push_back(p.record);
        }
        require(calls==planned && process_threads()==1,"final call/thread mismatch");
        result["timing_contract"]="One raw-query profile route, mapping/canonicalization, original NSG, preallocated output; independent plain batch walls; no GT/count/I/O/load/build in timer";
        write_json(out/"results.json",result);write_json(out/"verification.json",{{"status","PASS"},{"physical_calls",calls},{"raw_count_original_and_repeat_bits",true}});
        return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}
}

#include "gate_policy.hpp"
#include <cstdlib>
#include <sched.h>

int process_threads() {
    std::ifstream f("/proc/self/status");std::string line;
    while(std::getline(f,line))if(line.rfind("Threads:",0)==0)return std::stoi(line.substr(8));
    throw std::runtime_error("cannot verify threads");
}
void thread_contract(const json& c) {
    require(c.contains("threads") && c.at("threads")==1,"explicit threads=1 required");
    for(const char* name:{"OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"}) {
        const char* v=std::getenv(name);require(v && std::string(v)=="1",std::string(name)+"=1 required");
    }
    omp_set_dynamic(0);omp_set_num_threads(1);int observed=0;
    #pragma omp parallel
    {
        #pragma omp single
        observed=omp_get_num_threads();
    }
    require(observed==1 && process_threads()==1,"actual thread count not one");
    cpu_set_t affinity;CPU_ZERO(&affinity);require(sched_getaffinity(0,sizeof(affinity),&affinity)==0,"affinity unavailable");
    require(CPU_COUNT(&affinity)==1 && CPU_ISSET(c.at("query_cpu").get<int>(),&affinity),"wrong CPU affinity");
}
struct Point {
    json config,record;
    std::unique_ptr<SelectivePolicy> plain,count;
    std::unique_ptr<AnnotatedBatch> first,fullcount;
    std::vector<double> seconds;
};
int main(int argc,char** argv) {
    try {
        require(argc==3,"evaluate config.json new_output");std::ifstream f(argv[1]);json c;f>>c;thread_contract(c);
        fs::path out=argv[2];require(!fs::exists(out),"refuse existing output");fs::create_directories(out);write_json(out/"config.json",c);
        write_json(out/"thread_contract.json",{{"status","PASS"},{"threads",1},{"actual_openmp_threads",1},{"process_threads",process_threads()},{"cpu",c.at("query_cpu")}});
        const size_t d=c.at("dim"),n=c.at("num_queries"),gtk=c.at("gt_k");const int repetitions=c.value("timing_repeats",0);const bool measured=repetitions>0;
        require(n>=16 && gtk==100 && (repetitions==0 || repetitions==3),"unexpected sample/GT/timing configuration");
        auto q=read_raw<float>(c.at("queries_file"));auto rows=read_raw<int64_t>(c.at("row_ids"));
        require(q.size()==n*d && rows.size()==n,"query/row shape mismatch");finite_matrix(q,"query");write_raw(out/"row_ids.i64",rows);
        uint64_t planned=0;for(const auto& m:c.at("methods"))planned+=(measured?2*repetitions+1:2)*n+16+(m.value("component_wall",false)?2*n:0);
        require(planned<=c.at("real_call_cap").get<uint64_t>(),"allocated call cap too small");
        auto index=std::make_unique<acsg::IndexACSGFlat>();index->loadACPG(c.at("index_path").get<std::string>().c_str());
        std::vector<float>().swap(index->acsg.pheromone);std::vector<float>().swap(index->acsg.weight);
        require(index->d==int(d) && index->metric_type==faiss::METRIC_INNER_PRODUCT,"graph/metric mismatch");
        if(c.contains("base_count"))require(index->ntotal==c.at("base_count").get<int64_t>(),"base row count mismatch");
        NativeWork worker(*index,false),counter(*index,true);worker.retset.reserve(801);counter.retset.reserve(801);Work reference(*index,true);
        auto shared=c.at("policies");
        for(const char* key:{"A0","A1"}) {
            require(shared.at(key).at("dim")==d,"router/query dimension mismatch");
            const auto ids=read_raw<int32_t>(shared.at(key).at("mapping"));
            require(ids.size()==shared.at(key).at("hub_count").get<size_t>(),"router ID count mismatch");
            for(auto id:ids)require(id>=0 && id<index->ntotal,"router ID outside frozen base");
        }
        std::vector<Point> points;uint64_t calls=0;json events=json::array();
        for(auto m:c.at("methods")) {
            const int L=m.at("L");require(std::set<int>{64,128,256,400,800}.count(L),"unexpected L");
            std::string name=m.at("name");require(name.find('/')==std::string::npos,"invalid method name");
            if(m.at("kind")=="nsg") {
                require(index->acsg.enterpoint>=0 && index->acsg.enterpoint<index->ntotal,"NSG entry outside base");
                m["direct"]={{"dim",d},{"fixed_entry",index->acsg.enterpoint},{"k",1}};
            }
            if(m.at("kind")=="fast30k")for(auto id:read_raw<int32_t>(m.at("direct").at("mapping")))require(id>=0 && id<index->ntotal,"Fast30K ID outside base");
            Point p;p.config=m;p.record={{"name",name},{"family",m.at("family")},{"kind",m.at("kind")},{"L",L},{"configuration",m}};
            auto start=Clock::now();p.plain=std::make_unique<SelectivePolicy>(shared,m,out/name,false,false);
            p.record["policy_build_seconds"]=std::chrono::duration<double>(Clock::now()-start).count();
            start=Clock::now();p.count=std::make_unique<SelectivePolicy>(shared,m,out/name,true,true);
            p.record["count_policy_load_seconds"]=std::chrono::duration<double>(Clock::now()-start).count();
            p.first=std::make_unique<AnnotatedBatch>(n);p.fullcount=std::make_unique<AnnotatedBatch>(n);points.push_back(std::move(p));
        }
        AnnotatedBatch warm(n),timed(n);
        for(int rep=0;rep<(measured?repetitions:1);++rep) {
            for(int L:{64,128,256,400,800}) {
                std::vector<size_t> ids;for(size_t i=0;i<points.size();++i)if(points[i].config.at("L")==L)ids.push_back(i);
                if(ids.empty())continue;
                // Rotation uses a stable L ordinal, independent of model outcomes.
                const size_t ordinal=L==64?0:L==128?1:L==256?2:L==400?3:4;
                const size_t offset=(c.value("dataset_order",0)+rep+ordinal)%ids.size();
                std::rotate(ids.begin(),ids.begin()+offset,ids.end());index->acsg.search_L=L;
                for(size_t id:ids) {
                    auto& p=points[id];const std::string name=p.config.at("name");
                    if(measured){run_plain(*index,*p.plain,q,d,worker,warm);calls+=n;}
                    auto started=Clock::now();run_plain(*index,*p.plain,q,d,worker,timed);
                    double seconds=std::chrono::duration<double>(Clock::now()-started).count();calls+=n;
                    if(measured)compare_annotated(warm,timed);
                    if(rep==0){*p.first=timed;save_unscored(timed,out/name);}else compare_annotated(*p.first,timed);
                    if(measured)p.seconds.push_back(seconds);
                    events.push_back({{"name",name},{"L",L},{"repeat",rep},{"plain_seconds",measured?json(seconds):json(nullptr)}});
                    write_json(out/"timing_progress.json",events);
                    std::cout<<json({{"stage","plain_complete"},{"name",name},{"repeat",rep},{"seconds",seconds}}).dump()<<std::endl;
                }
            }
        }
        for(auto& p:points) {
            index->acsg.search_L=p.config.at("L");const auto k=p.count->entry_count();
            run_plain(*index,*p.count,q,d,counter,*p.fullcount);calls+=n;compare_annotated(*p.first,*p.fullcount);
            for(size_t i=0;i<n;++i)if(k==3)require(std::set<int32_t>(p.fullcount->out.routes[i].ids.begin(),p.fullcount->out.routes[i].ids.end()).size()==3,"nonunique three entries");
            for(size_t i=0;i<16;++i) {
                const auto& route=p.fullcount->out.routes[i];std::vector<int32_t> e(route.ids.begin(),route.ids.begin()+k);
                auto r=reference.run(*index,q.data()+i*d,e,{0,1,2},k);++calls;const auto& a=p.fullcount->out.searches[i];
                require(r.ids==a.ids && r.ndc==a.ndc && std::memcmp(r.distances.data(),a.distances.data(),K*sizeof(float))==0,"native wrapper parity failed");
            }
            p.record["route_only_seconds"]=nullptr;p.record["graph_only_seconds"]=nullptr;
            if(p.config.value("component_wall",false)) {
                require(measured && p.config.at("L")==128,"component schedule violation");AnnotatedBatch separate(n);
                routes(*p.plain,q,d,separate);auto t=Clock::now();routes(*p.plain,q,d,separate);
                p.record["route_only_seconds"]=std::chrono::duration<double>(Clock::now()-t).count();
                run_graph(*index,*p.plain,q,d,worker,separate);calls+=n;t=Clock::now();run_graph(*index,*p.plain,q,d,worker,separate);calls+=n;
                p.record["graph_only_seconds"]=std::chrono::duration<double>(Clock::now()-t).count();compare_annotated(separate,*p.first);
            }
        }
        if(c.value("export_features",false)) {
            auto started=Clock::now();SelectivePolicy diagnostic(shared,{{"kind","features"}},out/"feature_router",false,false);
            std::vector<double> features(n*FEATURE_COUNT);std::vector<int32_t> a0(n*3),a1(n*3);
            for(size_t i=0;i<n;++i) {
                auto f=diagnostic.inspect(q.data()+i*d);std::copy(f.x.begin(),f.x.end(),features.begin()+i*FEATURE_COUNT);
                std::copy(f.base.ids.begin(),f.base.ids.end(),a0.begin()+i*3);std::copy(f.newer.ids.begin(),f.newer.ids.end(),a1.begin()+i*3);
                for(const auto& p:points) {
                    auto kind=p.config.at("kind");if(kind=="fast20k")require(p.first->out.routes[i].ids==f.base.ids,"feature/base routes differ");
                    if(kind=="e24")require(p.first->out.routes[i].ids==f.newer.ids,"feature/new routes differ");
                }
            }
            write_raw(out/"features.f64",features);write_raw(out/"feature_base_entries.i32",a0);write_raw(out/"feature_new_entries.i32",a1);
            write_json(out/"features.json",{{"rows",n},{"columns",FEATURE_COUNT},{"offline_export_seconds",std::chrono::duration<double>(Clock::now()-started).count()},{"GT_used",false},{"NSG_calls",0}});
        }
        // Ground truth is opened only after every raw search and timing has completed.
        auto gt=read_raw<int64_t>(c.at("gt_file"));require(gt.size()==n*gtk,"GT shape mismatch");
        json result={{"status","COMPLETE"},{"dataset",c.at("dataset")},{"split",c.at("split")},{"queries",n},{"threads",1},
                     {"timing_repeats",repetitions},{"physical_graph_calls",calls},{"methods",json::array()},{"GT_opened_after_all_raw_search",true}};
        for(auto& p:points) {
            auto stat=metrics(p.fullcount->out,gt,gtk,out/p.config.at("name").get<std::string>());
            for(auto it=stat.begin();it!=stat.end();++it)p.record[it.key()]=it.value();
            p.record["end_to_end_seconds"]=p.seconds;std::vector<double> qps;for(double s:p.seconds)qps.push_back(n/s);
            p.record["qps_runs"]=qps;std::sort(qps.begin(),qps.end());p.record["qps"]=qps.empty()?json(nullptr):json(qps[qps.size()/2]);
            p.record["qps_min"]=qps.empty()?json(nullptr):json(qps.front());p.record["qps_max"]=qps.empty()?json(nullptr):json(qps.back());
            p.record["choose_new_queries"]=std::accumulate(p.first->choices.begin(),p.first->choices.end(),uint64_t(0));
            p.record["mean_feature_dots"]=double(std::accumulate(p.first->feature_dots.begin(),p.first->feature_dots.end(),uint64_t(0)))/n;
            p.record["base_route_calls"]=std::accumulate(p.first->base_calls.begin(),p.first->base_calls.end(),uint64_t(0));
            p.record["new_route_calls"]=std::accumulate(p.first->new_calls.begin(),p.first->new_calls.end(),uint64_t(0));
            p.record["physical_graph_calls"]=(measured?2*repetitions+1:2)*n+16+(p.config.value("component_wall",false)?2*n:0);
            p.record["full_count_plain_parity_queries"]=n;p.record["original_kernel_parity_queries"]=16;p.record["repeated_output_parity"]=true;
            result["methods"].push_back(p.record);
        }
        require(calls==planned,"physical call accounting mismatch");require(process_threads()==1,"thread count changed");
        result["timing_contract"]="Single method, single thread, independent plain batch wall including all online routing/feature/gate/kernel/output costs; separate counting and GT; three repeated walls when measured";
        write_json(out/"results.json",result);write_json(out/"verification.json",{{"status","PASS"},{"threads",1},{"actual_calls",calls},{"planned_calls",planned},{"raw_count_native_and_repeat_parity",true}});
        return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}
}

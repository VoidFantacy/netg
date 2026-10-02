#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
#include <cstdlib>
#include <cstring>

json score_plain(const BatchOutput& output,const std::vector<int64_t>& gt,size_t gtk,const fs::path& folder) {
    fs::create_directories(folder);size_t n=output.searches.size();
    std::vector<uint8_t> hits(n);std::vector<uint16_t> masks(n);
    std::vector<int32_t> ids(n*K),entries(n*3),labels(n*3);std::vector<float> distances(n*K);
    uint64_t total=0,failed=0;
    for(size_t i=0;i<n;++i) {
        masks[i]=hitmask(output.searches[i].ids,gt.data()+i*gtk);hits[i]=__builtin_popcount(unsigned(masks[i]));
        total+=hits[i];failed+=hits[i]==0;
        std::copy(output.searches[i].ids.begin(),output.searches[i].ids.end(),ids.begin()+i*K);
        std::copy(output.searches[i].distances.begin(),output.searches[i].distances.end(),distances.begin()+i*K);
        std::copy(output.routes[i].ids.begin(),output.routes[i].ids.end(),entries.begin()+i*3);
        std::copy(output.routes[i].labels.begin(),output.routes[i].labels.end(),labels.begin()+i*3);
    }
    write_raw(folder/"hits.u8",hits);write_raw(folder/"hitmask.u16",masks);write_raw(folder/"ids.i32",ids);
    write_raw(folder/"distances.f32",distances);write_raw(folder/"entry_ids.i32",entries);write_raw(folder/"router_labels.i32",labels);
    return {{"queries",n},{"total_hits",total},{"recall_at_10",double(total)/(n*K)},
            {"failed_queries",failed},{"failure_rate",double(failed)/n}};
}

int main(int argc,char** argv) {
    try {
        require(argc==3,"quick config.json new_output");
        std::ifstream input(argv[1]);json config;input>>config;
        require(config.contains("threads") && config.at("threads")==1,"explicit threads=1 required");
        for(const char* name:{"OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"}) {
            const char* value=std::getenv(name);require(value && std::string(value)=="1",std::string(name)+"=1 required");
        }
        omp_set_dynamic(0);omp_set_num_threads(1);int observed=0;
        #pragma omp parallel
        {
            #pragma omp single
            observed=omp_get_num_threads();
        }
        require(observed==1 && omp_get_max_threads()==1,"single-thread runtime mismatch");
        fs::path out=argv[2];require(!fs::exists(out),"refuse existing output");fs::create_directories(out);
        write_json(out/"config.json",config);
        write_json(out/"thread_contract.json",{{"status","PASS"},{"threads",1},{"actual_openmp_threads",observed},
            {"OMP_NUM_THREADS","1"},{"OPENBLAS_NUM_THREADS","1"},{"MKL_NUM_THREADS","1"}});
        size_t d=config.at("dim"),n=config.at("num_queries"),gtk=config.at("gt_k");
        require(n>=16 && gtk>=10,"invalid query/GT shape");
        auto q=read_raw<float>(config.at("queries_file"));auto gt=read_raw<int64_t>(config.at("gt_file"));
        auto rows=read_raw<int64_t>(config.at("row_ids"));require(q.size()==n*d && gt.size()==n*gtk && rows.size()==n,"input shape mismatch");
        finite_matrix(q,"query");write_raw(out/"row_ids.i64",rows);
        auto index=std::make_unique<acsg::IndexACSGFlat>();index->loadACPG(config.at("index_path").get<std::string>().c_str());
        std::vector<float>().swap(index->acsg.pheromone);std::vector<float>().swap(index->acsg.weight);
        require(index->d==int(d) && index->metric_type==faiss::METRIC_INNER_PRODUCT,"frozen graph/metric mismatch");
        Workers workers;workers.push_back(std::make_unique<NativeWork>(*index,false));workers[0]->retset.reserve(801);
        NativeWork counted(*index,true);counted.retset.reserve(801);Work reference(*index,true);
        bool measure=config.value("measure_wall",true);
        BatchOutput warm(n),timed(n),fullcount(n);json result={{"status","RUNNING"},{"dataset",config.at("dataset")},
            {"split",config.at("split")},{"queries",n},{"threads",1},{"timing_repeats",measure?1:0},{"methods",json::array()}};
        json checks=json::array();size_t position=0;
        for(auto mc:config.at("methods")) {
            int L=mc.at("L");require(std::set<int>{64,128,256,400,800}.count(L),"unexpected exploration L");
            index->acsg.search_L=L;mc["dim"]=d;std::string name=mc.at("name");require(name.find('/')==std::string::npos,"invalid name");
            bool nsg=mc.at("family")=="nsg_medoid";
            if(nsg) {
                require(index->acsg.enterpoint>=0 && index->acsg.enterpoint<index->ntotal,"invalid NSG entry");
                mc["fixed_entry"]=index->acsg.enterpoint;mc["hub_count"]=0;mc["k"]=1;
            } else {
                auto mapping=read_raw<int32_t>(mc.at("mapping"));
                for(auto id:mapping)require(id>=0 && id<index->ntotal,"mapping outside base");
            }
            fs::path micro=out/(name+".hnsw");Policy plain(mc,micro,false,false),counter(mc,micro,true,true);
            std::array<Search,16> expected;
            for(size_t i=0;i<16;++i) {
                auto decision=plain.route(q.data()+i*d),count_decision=counter.route(q.data()+i*d);
                require(decision.ids==count_decision.ids && decision.labels==count_decision.labels,"count/plain routing mismatch");
                if(nsg)require(count_decision.ndc==0,"NSG has nonzero routing distance cost");
                size_t k=plain.entry_count();std::vector<int32_t> real(decision.ids.begin(),decision.ids.begin()+k);
                auto actual=counted.search(*index,q.data()+i*d,count_decision,k);
                auto native=reference.run(*index,q.data()+i*d,real,{0,1,2},k);
                require(actual.ids==native.ids && actual.ndc==native.ndc &&
                    std::memcmp(actual.distances.data(),native.distances.data(),K*sizeof(float))==0,"original kernel parity failed");
                expected[i]=actual;
            }
            // Formal points use one warmup and independent plain wall. Diagnostics report no QPS.
            if(measure)batch(*index,plain,q,d,workers,warm);
            auto started=Clock::now();batch(*index,plain,q,d,workers,timed);
            double seconds=std::chrono::duration<double>(Clock::now()-started).count();
            if(measure){
                compare(warm,timed);
                for(size_t i=0;i<n;++i)require(std::memcmp(warm.searches[i].distances.data(),timed.searches[i].distances.data(),K*sizeof(float))==0,"warm/timed float bits differ");
            }
            for(size_t i=0;i<16;++i)require(expected[i].ids==timed.searches[i].ids &&
                std::memcmp(expected[i].distances.data(),timed.searches[i].distances.data(),K*sizeof(float))==0,"timed/original kernel output differs");
            if(nsg)require(!fs::exists(micro),"NSG constructed a router");
            for(size_t i=0;i<n;++i){
                fullcount.routes[i]=counter.route(q.data()+i*d);
                if(!nsg){
                    require(std::set<int32_t>(fullcount.routes[i].ids.begin(),fullcount.routes[i].ids.end()).size()==3,"method did not select three unique entries");
                    if(mc.value("canonical_entry_order",false))require(std::is_sorted(fullcount.routes[i].ids.begin(),fullcount.routes[i].ids.end()),"entry canonical order failed");
                }
                fullcount.searches[i]=counted.search(*index,q.data()+i*d,fullcount.routes[i],counter.entry_count());
            }
            compare(fullcount,timed);
            for(size_t i=0;i<n;++i)require(std::memcmp(fullcount.searches[i].distances.data(),timed.searches[i].distances.data(),K*sizeof(float))==0,"full count/plain float bits mismatch");
            score_plain(timed,gt,gtk,out/name);
            auto metric=metrics(fullcount,gt,gtk,out/name);metric["name"]=name;metric["family"]=mc.at("family");metric["L"]=L;
            metric["configuration"]=mc;metric["end_to_end_seconds"]=measure?json(seconds):json(nullptr);metric["qps"]=measure?json(n/seconds):json(nullptr);
            metric["order_position"]=position++;metric["warmup_queries"]=measure?n:0;metric["timing_repeats"]=measure?1:0;
            metric["original_count_plain_checked_queries"]=16;metric["warm_timed_parity_queries"]=measure?n:0;metric["full_count_plain_parity_queries"]=n;
            result["methods"].push_back(metric);
            checks.push_back({{"name",name},{"L",L},{"original_kernel_queries",16},{"distance_bits",true},{"warm_timed_queries",n},{"status","PASS"}});
            write_json(out/"results.json",result);
            std::cout<<json({{"stage","point_complete"},{"name",name},{"L",L},{"wall_seconds",seconds}}).dump()<<std::endl;
        }
        result["status"]="COMPLETE";result["physical_graph_calls"]=result["methods"].size()*((measure?3:2)*n+32);
        result["timing_contract"]="Measured points: one single-thread full-batch warmup and one plain end-to-end wall, separate full count outside timer. Diagnostics: no QPS. GT/hash/JSON/load/build excluded.";
        write_json(out/"results.json",result);write_json(out/"verification.json",{{"status","PASS"},{"threads",1},{"checks",checks}});
        return 0;
    } catch(const std::exception& error) {std::cerr<<error.what()<<std::endl;return 1;}
}

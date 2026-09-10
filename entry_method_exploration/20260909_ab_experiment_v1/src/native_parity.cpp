// A bounded real-graph check of the NEW benchmark wrapper against the old wrapper.
#define AB_BENCHMARK_LIBRARY
#include "benchmark.cpp"
#undef AB_BENCHMARK_LIBRARY

int main(int argc,char** argv) {
    try {
        require(argc==3,"native_parity runner_config.json new_dir");
        fs::path out=argv[2];require(!fs::exists(out),"existing parity output");fs::create_directories(out);
        std::ifstream f(argv[1]);json c;f>>c;size_t d=c.at("dim");
        auto q=read_raw<float>(c.at("queries_file"));auto index=std::make_unique<acsg::IndexACSGFlat>();index->loadACPG(c.at("index_path").get<std::string>().c_str());
        std::vector<float>().swap(index->acsg.pheromone);std::vector<float>().swap(index->acsg.weight);
        NativeWork native(*index,true);Work old(*index,true);size_t checks=0;json counts=json::array();
        for(const auto& seed:c.at("seeds")) {
            auto ids=read_raw<int32_t>(seed.at("hub_ids"));std::vector<int32_t> duplicate(ids.size(),ids[0]);
            auto dup_path=out/("duplicate_"+std::to_string(seed.at("seed").get<int>())+".i32");write_raw(dup_path,duplicate);
            for(auto kind:{"fast1","fast3","identity_slot","duplicate_slot"}) {
                json p={{"dim",d},{"hub_count",ids.size()},{"seed",seed.at("seed")},{"W",seed.at("prototypes")},{"mapping",seed.at("hub_ids")},{"tie_ids",seed.at("hub_ids")},
                        {"k",std::string(kind)=="fast3"?3:1},{"slot_labels",std::string(kind).find("slot")!=std::string::npos},{"legacy_heap_order",true}};
                if(std::string(kind)=="duplicate_slot")p["mapping"]=dup_path.string();
                auto ip=out/(std::to_string(seed.at("seed").get<int>())+"_"+kind+".hnsw");Policy plain(p,ip,false,false);Policy policy(p,ip,true,true);
                for(int L:{64,128}) {
                    index->acsg.search_L=L;
                    for(size_t i=0;i<16;++i) {
                        auto r=policy.route(q.data()+i*d),plain_r=plain.route(q.data()+i*d);require(r.ids==plain_r.ids && r.labels==plain_r.labels,"real route count/plain difference");
                        size_t k=policy.entry_count();std::vector<int32_t> actual(r.ids.begin(),r.ids.begin()+k);
                        auto a=native.search(*index,q.data()+i*d,r,k),b=old.run(*index,q.data()+i*d,actual,{0,1,2},k);
                        require(a.ids==b.ids && a.distances==b.distances && a.ndc==b.ndc,"NEW/OLD real wrapper mismatch");++checks;
                        if(std::string(kind)=="duplicate_slot")require(r.ids[0]==ids[0],"duplicate mapping failed");
                    }
                }
            }
            counts.push_back({{"seed",seed.at("seed")},{"checks",128}});
        }
        write_json(out/"acceptance.json",{{"status","PASS"},{"dataset",c.at("dataset")},{"native_vs_original_checks",checks},{"physical_graph_calls",checks*2},
                   {"plain_count_route_checks",checks},{"builds",counts},{"real_queries",16},{"L",{64,128}},{"no_timing_measurements",true}});return 0;
    }catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}
}

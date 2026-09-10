// Independent fixed-entry reference call against the new NSG Policy path.
#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"

int main(int argc, char** argv) {
    try {
        require(argc==3,"nsg_native_parity config.json new_output");
        fs::path out=argv[2];require(!fs::exists(out),"existing parity output");fs::create_directories(out);
        std::ifstream input(argv[1]);json c;input>>c;size_t d=c.at("dim");
        auto q=read_raw<float>(c.at("queries_file"));require(q.size()>=16*d,"need 16 queries");
        omp_set_dynamic(0);omp_set_num_threads(1);
        auto index=std::make_unique<acsg::IndexACSGFlat>();index->loadACPG(c.at("index_path").get<std::string>().c_str());
        std::vector<float>().swap(index->acsg.pheromone);std::vector<float>().swap(index->acsg.weight);
        const int32_t entry=index->acsg.enterpoint;
        require(entry>=0 && entry<index->ntotal,"invalid medoid");
        json pc={{"dim",d},{"fixed_entry",entry},{"k",1}};
        Policy plain(pc,out/"must_not_build_hnsw",false,false),count(pc,out/"must_not_build_hnsw",true,true);
        NativeWork tested(*index,true);Work reference(*index,true);
        size_t checked=0;
        for(int L:{64,128}) {
            index->acsg.search_L=L;
            for(size_t i=0;i<16;++i) {
                auto a=plain.route(q.data()+i*d),b=count.route(q.data()+i*d);
                require(a.ids==b.ids && a.labels==b.labels && a.ids[0]==entry,"wrong fixed entry");
                require(a.ndc==0 && b.ndc==0,"NSG must not pay router distance");
                auto actual=tested.search(*index,q.data()+i*d,b,1);
                auto original=reference.run(*index,q.data()+i*d,{entry},{0,0,0},1);
                require(actual.ids==original.ids && actual.distances==original.distances && actual.ndc==original.ndc,"NSG/original fixed-entry mismatch");
                ++checked;
            }
        }
        require(!fs::exists(out/"must_not_build_hnsw"),"NSG unexpectedly built router");
        write_json(out/"acceptance.json",{{"status","PASS"},{"dataset",c.at("dataset")},{"entry_id",entry},
            {"queries",16},{"L",{64,128}},{"comparisons",checked},{"physical_graph_calls",checked*2},
            {"routing_ndc",0},{"threads",1},{"original_reference","Original kernel mode2 and index.acsg.enterpoint, matching project NSG_Medoid"}});
        return 0;
    } catch(const std::exception& error) {std::cerr<<error.what()<<std::endl;return 1;}
}

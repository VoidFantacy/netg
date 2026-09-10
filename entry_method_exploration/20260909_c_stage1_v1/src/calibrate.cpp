#include "common.hpp"
int main(int argc,char** argv) {try {
    if(argc!=3){std::cout<<"calibrate CONFIG NEW_OUTPUT_JSON (GT-free original Fast3)\n";return argc==2?0:2;}
    require(!fs::exists(argv[2]),"output exists");omp_set_num_threads(1);auto start=Clock::now();Dataset d(argv[1]);
    faiss::VisitedTable vt(d.index.ntotal); CountDC dc(acsg::storage_distance_computer(d.index.storage));
    json rows=json::array();
    for(int L:{64,128}) {
        d.index.acsg.search_L=L;
        for(int i=0;i<128;++i) {
            auto q=d.query(i);auto route=d.router->run(q,3);std::vector<acsg::EnterPoint> entries;
            for(int id:route.ids)entries.emplace_back(id,1.0);
            vt.advance();dc.count=0;dc.set_query(q);acsg::SearchTrace trace;std::array<faiss::idx_t,10> ids;std::array<float,10> distances;
            auto t=Clock::now();d.index.acsg.search_new_traced(dc,10,ids.data(),distances.data(),vt,2,entries,trace);
            auto wall=seconds(t); require(dc.count==trace.distance_evaluations,"native count/trace mismatch");
            rows.push_back({{"sample_index",i},{"row_id",d.row_ids[i]},{"L",L},{"ndc",dc.count},{"expansions",trace.expanded_count},{"wall",wall},{"route_ndc",route.ndc}});
        }
        std::cout<<"L="<<L<<" completed calibration wall="<<seconds(start)<<std::endl;
    }
    write_json(argv[2],{{"dataset",d.c["dataset"]},{"GT_accessed",false},{"rows",rows},{"total_wall",seconds(start)}});return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

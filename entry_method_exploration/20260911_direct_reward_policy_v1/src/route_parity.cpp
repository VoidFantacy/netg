#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
#include <cstdlib>
int main(int argc,char** argv) {try {
    require(argc==3,"route_parity config new_output");std::ifstream f(argv[1]);json c;f>>c;
    fs::path out=argv[2];require(!fs::exists(out),"existing parity output");fs::create_directories(out);
    require(c.at("threads")==1,"single thread required");omp_set_dynamic(0);omp_set_num_threads(1);
    for(const char* k:{"OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"})require(std::getenv(k)&&std::string(std::getenv(k))=="1","thread environment required");
    const size_t n=c.at("num_queries"),d=c.at("dim");auto q=read_raw<float>(c.at("queries_file"));
    auto candidate=read_raw<int32_t>(c.at("expected_candidates"));require(candidate.size()==n*8,"candidate shape");
    json results=json::array();
    for(auto m:c.at("methods")) {
        m["dim"]=d;std::string name=m.at("name");Policy plain(m,out/(name+".hnsw"),false,false),count(m,out/(name+".hnsw"),true,true);
        auto slots=read_raw<int32_t>(m.at("expected_slots"));auto entries=read_raw<int32_t>(m.at("expected_entries"));
        require(slots.size()==n && entries.size()==n*3,"reference shape");
        size_t mismatched_candidates=0,mismatched_slots=0,mismatched_entries=0;uint64_t ndc=0;
        for(size_t i=0;i<n;++i) {
            auto a=plain.route(q.data()+i*d),b=count.route(q.data()+i*d);
            require(a.ids==b.ids && a.labels==b.labels && a.action_slot==b.action_slot && a.candidates==b.candidates,"plain/count route parity");
            mismatched_candidates+=!std::equal(a.candidates.begin(),a.candidates.end(),candidate.begin()+i*8);
            mismatched_slots+=a.action_slot!=slots[i];mismatched_entries+=!std::equal(a.ids.begin(),a.ids.end(),entries.begin()+i*3);
            require(a.ndc==0 && b.ndc>=c.at("hub_count").get<size_t>()+8,"route count missing full H or model score");ndc+=b.ndc;
        }
        results.push_back({{"method",name},{"queries",n},{"candidate_mismatches",mismatched_candidates},{"slot_mismatches",mismatched_slots},
            {"entry_mismatches",mismatched_entries},{"mean_route_ndc",double(ndc)/n},{"physical_HNSW_queries",n*4},{"NSG_calls",0},{"GT_opened",false}});
    }
    bool pass=true;for(auto r:results)pass=pass&&r.at("candidate_mismatches")==0&&r.at("slot_mismatches")==0&&r.at("entry_mismatches")==0;
    write_json(out/"results.json",{{"status",pass?"PASS":"FAIL"},{"methods",results},{"NSG_calls",0},{"GT_opened",false}});
    require(pass,"C8 implementation differs from frozen cache; stop before real graph queries");return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

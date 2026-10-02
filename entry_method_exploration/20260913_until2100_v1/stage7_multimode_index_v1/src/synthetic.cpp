#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
int main(int argc,char** argv) {
 try {
    require(argc==2,"synthetic new directory");fs::path dir=argv[1];require(!fs::exists(dir),"refuse overwrite");fs::create_directories(dir);
    std::vector<int32_t> mapping{10,10,10,20,20,20,30,30,30};
    Decision a;unique_three(a,{{1,6},{0,2},{0,0},{0,1},{.5,3},{.5,4},{.5,5}},mapping);
    require(a.ids==std::array<int32_t,3>{10,20,30} && a.labels==std::array<int32_t,3>{0,3,6},"dedup/tie contract");
    int rejected=0;
    for(auto bad:std::vector<std::vector<std::pair<float,size_t>>>{{{0,0}},{{0,0},{0,0},{0,1},{0,2},{0,3},{0,4},{0,6}},{{0,0},{0,1},{0,2},{0,3},{0,4},{0,5},{0,99}}}) {
        try{Decision x;unique_three(x,bad,mapping);}catch(const std::exception&){++rejected;}
    }
    require(rejected==3,"invalid candidates not rejected");
    std::vector<float> w{1,0,0,0, 1,0,0,0, 1,0,0,0, 0,1,0,0, 0,1,0,0, 0,1,0,0, 0,0,1,0, 0,0,1,0, 0,0,1,0};
    std::vector<int32_t> tie(9);std::iota(tie.begin(),tie.end(),0);
    write_raw(dir/"W.f32",w);write_raw(dir/"mapping.i32",mapping);write_raw(dir/"tie_ids.i32",tie);
    json c={{"dim",4},{"hub_count",9},{"unique_hub_count",3},{"k",3},{"slot_labels",true},{"multi_profile",true},{"canonical_entry_order",true},{"seed",20260828},
        {"W",(dir/"W.f32").string()},{"mapping",(dir/"mapping.i32").string()},{"tie_ids",(dir/"tie_ids.i32").string()}};
    Policy built(c,dir/"built.hnsw",false,false),loaded(c,dir/"built.hnsw",true,true);
    c["graph_file"]=(dir/"built.hnsw").string();Policy sourced(c,dir/"copied.hnsw",false,false);
    size_t calls=0;
    for(const auto& q:std::vector<std::array<float,4>>{{1,0,0,0},{0,1,0,0},{0,0,1,0},{0,0,0,0},{1,1,1,1}}) {
        auto x=built.route(q.data()),y=loaded.route(q.data()),z=sourced.route(q.data());calls+=3;
        require(x.ids==y.ids && x.ids==z.ids && x.candidate_slots==y.candidate_slots && x.candidate_slots==z.candidate_slots,"serialization/count routing mismatch");
        require(x.ids==std::array<int32_t,3>{10,20,30} && y.ndc>0,"three unique real entries");
        require(x.candidate_distances==y.candidate_distances,"count distances mismatch");
    }
    c["unique_hub_count"]=4;bool bad=false;try{Policy invalid(c,dir/"invalid.hnsw",false,false);}catch(const std::exception&){bad=true;}
    require(bad,"invalid physical/unique mapping accepted");
    write_json(dir/"verification.json",{{"status","PASS"},{"HNSW_calls",calls},{"builds",1},{"loads",2},{"NSG_calls",0},{"rejected_contracts",4}});return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}
}

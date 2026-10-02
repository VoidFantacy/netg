#include "state_machine.hpp"
using namespace cstage1;
struct Branch {
    State state;Observer trace;std::string name,status,eligibility;int slot=-1,candidate=-1;
    double clone_seconds=0,plain_clone_seconds=0,count_wall_seconds=0,plain_wall_seconds=0;
    uint64_t suffix_ndc=0;
};
bool same_pool(const State& a,const State& b){
    if(a.num_ids!=b.num_ids || a.retset.size()!=b.retset.size())return false;
    for(size_t i=0;i<a.retset.size();++i)if(a.retset[i].id!=b.retset[i].id || a.retset[i].distance!=b.retset[i].distance || a.retset[i].flag!=b.retset[i].flag)return false;
    return true;
}
json branch_record(const Branch& b,const Branch& baseline) {
    bool trajectory=b.trace.expanded_order!=baseline.trace.expanded_order;
    bool retset=!same_pool(b.state,baseline.state);
    return {{"action",b.name},{"slot",b.slot},{"candidate",b.candidate},{"eligibility",b.eligibility},{"action_status",b.status},
        {"ids",b.state.top_ids()},{"distances",b.state.top_distances()},{"graph_ndc",b.state.ndc},{"prefix_graph_ndc",b.state.prefix_ndc},
        {"suffix_graph_ndc",b.suffix_ndc},{"remaining",b.state.remaining()},{"limit",b.state.limit},
        {"natural_finished",b.state.natural_finished},{"cap_exhausted",b.state.cap_exhausted},{"row_active",b.state.row_active},
        {"current_node",b.state.current_node},{"neighbor_offset",b.state.neighbor_offset},{"cursor",b.state.cursor},{"updated_pos",b.state.updated_pos},
        {"expanded_suffix",b.trace.expanded_order},{"expanded_count",b.state.started_expansions},{"completed_expansions",b.state.completed_expansions},
        {"visited_count",b.state.visited.size()},{"retset_changed",retset},{"trajectory_changed",trajectory},{"effective_action",trajectory||retset},
        {"result_changed",b.state.top_ids()!=baseline.state.top_ids() || b.state.top_distances()!=baseline.state.top_distances()},
        {"clone_seconds",b.clone_seconds},{"plain_clone_seconds",b.plain_clone_seconds},{"count_trace_wall_seconds",b.count_wall_seconds},
        {"plain_wall_seconds",b.plain_wall_seconds},{"timing_publishable_as_QPS",false}};
}
int main(int argc,char** argv){try{
    if(argc!=5){std::cout<<"c2 CONFIG LOCK NEW_OUTPUT_DIRECTORY N(4 smoke|2000 main); GT-free execution only\n";return argc==2?0:2;}
    auto start=Clock::now();omp_set_num_threads(1);int N=std::stoi(argv[4]);require(N==4 || N==2000,"query bound");
    fs::path output=argv[3],lockpath=argv[2];require(!fs::exists(output),"output exists");
    auto locked=read_json(lockpath);auto gate=read_json(lockpath.parent_path()/"results/c1_gate.json");require(gate["status"]=="PASS","C1 not accepted");
    Dataset d(argv[1]);auto ident=read_json(d.c.at("identity_file").get<std::string>());
    ident["state_machine_sha256"]=gate.at("state_machine_sha256");ident["kernel"]="cstage1_v1";
    Engine engine(*d.index.acsg.final_graph,d.index.ntotal,d.index.d,ident);
    fs::create_directories(output/"states");std::ofstream raw(output/"branches.jsonl"),progress(output/"progress.jsonl");
    write_json(output/"metadata.json",{{"status","RUNNING"},{"dataset",d.c["dataset"]},{"N",N},{"split","drl_train"},
        {"config",d.c},{"locked_config",locked},{"C1_gate",gate},{"GT_accessed",false},{"quality_scoring",false},
        {"schema_version",1},{"action_order",{"continue","natural_0","natural_1","natural_2","natural_3","force_0","force_1","force_2","force_3"}},
        {"count_plain_rule","each physical branch executed once with count+external trace, once with plain DC; exact complete state comparison"}});
    uint64_t rows=0,executions=0;const uint64_t B=locked.at("B");
    for(int i=0;i<N;++i){const float* q=d.query(i);auto route3=d.router->run(q,3),route7=d.router->run(q,7);
        std::array<int,4> candidates;std::array<std::string,4> candidate_reason;std::set<int> used(route3.ids.begin(),route3.ids.end());
        for(int j=0;j<4;++j){int e=route7.ids[j+3];candidate_reason[j]=used.count(e)?"initial_or_duplicate":"query_only_candidate";
            candidates[j]=used.insert(e).second?e:-1;}
        for(int L:{64,128}) {
            CountDC prefix_dc(acsg::storage_distance_computer(d.index.storage),true);Observer prefix_obs;
            uint64_t cp=locked["checkpoint_completed_expansions"][std::to_string(L)];
            auto tp=Clock::now();auto prefix=engine.initialize(q,L,10,route3.ids,d.row_ids[i],prefix_dc,&prefix_obs);engine.resume(prefix,prefix_dc,cp,&prefix_obs);
            double prefix_count_wall=seconds(tp);++executions;require(prefix.ndc==prefix_dc.count,"prefix NDC");
            std::unique_ptr<faiss::DistanceComputer> ppdc(acsg::storage_distance_computer(d.index.storage));
            auto ti=Clock::now();auto pp=engine.initialize(q,L,10,route3.ids,d.row_ids[i],*ppdc);double init_plain=seconds(ti);
            auto tr=Clock::now();engine.resume(pp,*ppdc,cp);double resume_plain=seconds(tr);++executions;
            require(prefix.to_json()==pp.to_json(),"prefix count/plain state mismatch");
            auto ts=Clock::now();auto prefix_json=prefix.to_json();std::string serialized=prefix_json.dump();double serialization=seconds(ts);
            auto td=Clock::now();auto restored=State::from_json(json::parse(serialized));double deserialization=seconds(td);
            require(restored.to_json()==prefix_json,"C2 prefix serialization");
            std::string state_file="states/q"+std::to_string(i)+"_L"+std::to_string(L)+".json";
            {std::ofstream sf(output/state_file);sf<<serialized<<'\n';require(bool(sf),"state write");}
            std::vector<Branch> branches;branches.reserve(9);
            for(int action=0;action<9;++action){int slot=action==0?-1:(action-1)%4;bool force=action>=5;int e=slot<0?-1:candidates[slot];
                Branch b;b.name=action==0?"continue":(force?"force_":"natural_")+std::to_string(slot);b.slot=slot;b.candidate=e;
                b.eligibility=action==0?"continue":engine.eligibility(prefix,e);
                // Ineligible actions are exact aliases of the native continuation, no additional physical execution.
                if(action && b.eligibility!="eligible"){
                    auto saved_name=b.name;auto why=b.eligibility;b=branches.front();b.name=saved_name;b.slot=slot;b.candidate=e;b.eligibility=why;b.status="no_op_alias_continue";
                    // This is the very same continue branch. Preserve its measured wall, explicitly mark alias below.
                    b.clone_seconds=0;b.plain_clone_seconds=0;
                    branches.push_back(std::move(b));continue;
                }
                auto tc=Clock::now();b.state=prefix;b.clone_seconds=seconds(tc);b.state.set_additional_cap(B);
                CountDC dc(acsg::storage_distance_computer(d.index.storage),true);
                auto tw=Clock::now();b.status=action?engine.inject(b.state,e,force,dc,&b.trace):"continued";
                engine.resume(b.state,dc,unlimited,&b.trace);b.count_wall_seconds=seconds(tw);++executions;
                b.suffix_ndc=dc.count;require(b.state.ndc==prefix.ndc+dc.count && dc.count<=B,"branch NDC envelope");
                // Entire plain branch including action is independently timed; DC allocation and clone are outside timer.
                auto tpc=Clock::now();auto plain=prefix;b.plain_clone_seconds=seconds(tpc);plain.set_additional_cap(B);
                std::unique_ptr<faiss::DistanceComputer> plain_dc(acsg::storage_distance_computer(d.index.storage));
                auto pw=Clock::now();if(action)engine.inject(plain,e,force,*plain_dc);engine.resume(plain,*plain_dc);b.plain_wall_seconds=seconds(pw);++executions;
                require(plain.to_json()==b.state.to_json(),"branch count/plain state mismatch");
                require(prefix.to_json()==prefix_json,"C2 branch contaminated prefix");
                if(action)require(!force || std::count(b.trace.expanded_order.begin(),b.trace.expanded_order.end(),e)==1,"force not exactly once");
                branches.push_back(std::move(b));
            }
            json records=json::array();for(auto& b:branches){auto rec=branch_record(b,branches.front());
                rec["physical_branch_executed"]=b.status!="no_op_alias_continue";
                rec["wall_source"]=b.status=="no_op_alias_continue"?"same_continue_branch_measurement":"independent_plain_branch";
                records.push_back(rec);}
            json row={{"sample_index",i},{"row_id",d.row_ids[i]},{"L",L},{"K",10},{"B",B},{"checkpoint",cp},
                {"initial_entries",route3.ids},{"candidate_ids",candidates},{"candidate_generation_status",candidate_reason},
                {"direct_top3_equals_top7_prefix",std::equal(route3.ids.begin(),route3.ids.end(),route7.ids.begin())},
                {"route3_ndc",route3.ndc},{"route7_candidate_ndc",route7.ndc},{"route3_wall_seconds",route3.wall},{"route7_wall_seconds",route7.wall},
                {"early_finished",prefix.natural_finished},{"prefix_state",state_file},{"prefix_ndc",prefix.ndc},
                {"prefix_completed_expansions",prefix.completed_expansions},{"prefix_count_trace_wall_seconds",prefix_count_wall},
                {"prefix_init_plain_seconds",init_plain},{"prefix_resume_plain_seconds",resume_plain},{"state_serialization_seconds",serialization},
                {"state_deserialization_seconds",deserialization},{"serialized_state_bytes",serialized.size()},{"branches",records}};
            raw<<row.dump()<<'\n';raw.flush();require(bool(raw),"raw output failed");++rows;
        }
        if((i+1)%16==0 || i+1==N){json pr={{"queries_completed",i+1},{"rows_completed",rows},{"executions",executions},{"wall_seconds",seconds(start)}};
            progress<<pr.dump()<<'\n';progress.flush();std::cout<<pr.dump()<<std::endl;}
        require(executions<=80000 && seconds(start)<=7200,"C2 invocation resource bound");
    }
    write_json(output/"complete.json",{{"status","COMPLETE"},{"dataset",d.c["dataset"]},{"queries",N},{"rows",rows},
        {"physical_search_executions",executions},{"GT_accessed",false},{"wall_seconds",seconds(start)},
        {"pure_wall_QPS",nullptr},{"reason","C2 single-thread branch diagnostics, no formal independent full-batch timing"}});
    auto meta=read_json(output/"metadata.json");meta["status"]="COMPLETE";write_json(output/"metadata.json",meta);return 0;
}catch(const std::exception& e){std::cerr<<"C2_FAIL "<<e.what()<<std::endl;return 1;}}

// E183 retained actual timed packets; complete normal lifecycle; IP and L2.
#define E183_EMBED_COMMON
#include "residual_tools.cpp"

namespace e183 {
__attribute__((noinline)) double timed_once(acsg::IndexACSGFlat& idx,const std::vector<float>& q,int L,const Method& method,Batch& destination){
    const auto started=Clock::now();
    {Batch output(destination.n,destination.k);run_batch(idx,q,L,method,output);copy_packet(output,destination);
        asm volatile("" : : "g"(output.ids.data()),"g"(destination.ids.data()) : "memory");}
    asm volatile("" : : : "memory");return seconds(started);
}
json benchmark(const json& c,bool qualification=false){check_threads(c);const auto started=Clock::now();const fs::path root=c.at("output_dir");
    const int repetitions=c.at("timing_repeats");require(repetitions==(qualification?1:3),"three formal rounds or one qualification round");fresh_dir(root);fresh_json(root/"config.json",c);
    json binding;auto idx=load_index(c,binding);Matrix query(c.at("queries"));require(query.d==size_t(idx->d),"benchmark query d");auto q=query.copy();
    const size_t n=query.n,warm_n=std::min(n,c.at("warmup_n").get<size_t>());require(warm_n>0&&c.at("warmup_n")==256,"registered warmup256");
    std::map<std::string,std::unique_ptr<Router>> routers;for(const auto& rc:c.at("routers")){auto r=std::make_unique<Router>(rc,idx->d,idx->ntotal);const std::string name=r->name;require(!routers.count(name),"unique router name");routers[name]=std::move(r);}
    std::map<std::string,size_t> method_index;std::vector<Method> methods;std::vector<std::unique_ptr<Posting>> tables;json model_bindings=json::array();
    for(const auto& mc:c.at("methods")){Method m;m.name=mc.at("name");m.family=mc.at("family");require(!m.name.empty()&&m.name.find('/')==std::string::npos&&m.name.find("..") == std::string::npos,"safe method component");
        require(method_index.emplace(m.name,methods.size()).second,"unique method");require(m.family=="NSG"||m.family=="GT10"||m.family=="POST","declared method family");
        if(m.family!="NSG"){m.router=mc.at("router");require(routers.count(m.router),"defined router");m.route=routers.at(m.router).get();}
        if(m.family=="POST"){m.baseline=mc.at("baseline");auto t=std::make_unique<Posting>(mc.at("table"),idx->ntotal);require(t->labels==m.route->ids,"table and router ordered labels identical");
            require(t->b==8||t->b==32,"formal JOINT8/32 only");m.table=t.get();model_bindings.push_back({{"method",m.name},{"H",t->H},{"B",t->b},{"file_bytes",t->file_bytes},{"runtime_plus_stack_bytes",t->resident_bytes()+Posting::AUXILIARY_STACK_RESERVE}});tables.push_back(std::move(t));}
        methods.push_back(m);}
    require(!methods.empty(),"nonempty finite method matrix");for(const auto& m:methods)if(m.table){require(method_index.count(m.baseline),"measured baseline required");const auto& b=methods[method_index.at(m.baseline)];require(b.family=="GT10"&&b.route==m.route,"POST baseline same actual router");}
    fresh_json(root/"environment.json",{{"threads",process_threads()},{"cpu",15},{"metric_id",c.at("metric_id")},{"loaded_index",binding},{"models",model_bindings},
        {"timer","normal Batch allocation/init + all route/main/post + uniform six-vector copy + actual normal Batch destruction"},{"startup_seconds",seconds(started)}});
    json results=json::array(),progress=json::array();size_t ordinal=0,oracle_queries=0,formal_batches=0,warmup_queries=0;
    if(qualification)require(n<=256,"qualification at most256 queries");
    for(int K:{1,100}){const std::string kk=std::to_string(K);if(qualification&&!c.at("K_L").contains(kk))continue;require(c.at("K_L").contains(kk),"both K tasks configured");std::set<int> unique_L;
        for(int L:c.at("K_L").at(kk)){require(L>=K&&L<=4096&&unique_L.insert(L).second,"unique valid L");
            std::vector<std::unique_ptr<Batch>> first(methods.size());std::vector<json> rounds(methods.size(),json::array());std::vector<double> warm_seconds(methods.size());
            Batch archive(n,K);
            for(int repeat=0;repeat<repetitions;++repeat){for(size_t offset=0;offset<methods.size();++offset){const size_t mi=(ordinal+repeat+c.value("dataset_order",size_t(0))+offset)%methods.size();const auto& m=methods[mi];
                const auto point=root/("k"+kk)/(m.name+"_L"+std::to_string(L));check_threads(c);
                if(repeat==0){const auto wt=Clock::now();{Batch warm(warm_n,K);run_batch(*idx,q,L,m,warm);}warm_seconds[mi]=seconds(wt);warmup_queries+=warm_n;}
                const double wall=timed_once(*idx,q,L,m,archive);++formal_batches;check_threads(c);require(wall>0&&std::isfinite(wall),"positive actual complete wall");validate(archive,idx->ntotal);
                const auto digest=packet_sha(archive);
                if(repeat==0){first[mi]=std::make_unique<Batch>(archive);first[mi]->save(point/"raw",false);}else {require(bool(first[mi]),"actual round0 archive");all_same(*first[mi],archive);require(digest==rounds[mi][0].at("packet_sha256"),"all actual round SHA equal");}
                json r={{"round",repeat},{"wall_seconds",wall},{"qps",n/wall},{"packet_sha256",digest},{"first_round_bits_equal",true},{"stored_round",0},{"raw_dir",(point/"raw").string()},
                        {"threads",process_threads()},{"cpu",15},{"measurement_order",formal_batches}};rounds[mi].push_back(r);fresh_json(point/("round"+std::to_string(repeat)+".json"),r);
                progress.push_back({{"K",K},{"L",L},{"method",m.name},{"round",repeat},{"wall_seconds",wall},{"qps",n/wall}});write_json(root/"timing_progress.json",progress);
                std::cout<<json{{"event",qualification?"qualification_round":"formal_round"},{"dataset",c.at("dataset")},{"method",m.name},{"K",K},{"L",L},{"round",repeat},{"qps",n/wall}}.dump()<<std::endl;
            }}
            // Independent reconstruction uses the measured same-K/L baseline.
            // It never repeats a graph traversal or uses evaluation GT labels.
            const auto audit_start=Clock::now();for(size_t mi=0;mi<methods.size();++mi){const auto& m=methods[mi];if(m.table){audit_merge(*idx,q,*first[method_index.at(m.baseline)],*first[mi],*m.table);oracle_queries+=n;}}
            const double audit_wall=seconds(audit_start);
            for(size_t mi=0;mi<methods.size();++mi){const auto& m=methods[mi];const auto point=root/("k"+kk)/(m.name+"_L"+std::to_string(L));std::vector<double> walls;for(const auto& r:rounds[mi])walls.push_back(r.at("wall_seconds"));std::sort(walls.begin(),walls.end());
                json r={{"status","PASS_E183_POINT"},{"dataset",c.at("dataset")},{"method",m.name},{"family",m.family},{"router",m.router},{"baseline",m.baseline},{"K",K},{"L",L},{"n",n},
                        {"metric_id",c.at("metric_id")},{"threads",1},{"cpu",15},{"timing_repeats",repetitions},{"rounds",rounds[mi]},{"wall_seconds",walls[repetitions/2]},{"qps",n/walls[repetitions/2]},
                        {"warmup_n",warm_n},{"warmup_seconds",warm_seconds[mi]},{"result_dir",point.string()},{"timed_output_retained",true},{"stored_round",0},{"all_round_bits_equal",true},
                        {"normal_output_destroyed_within_wall",true},{"uniform_packet_copy_inside_wall",true},{"second_full_ANN_traversal",false},{"full_merge_oracle_passed",true},
                        {"same_K_L_shared_oracle_seconds",audit_wall},{"separate_POST_pre_main_packet_retained",false},{"counts_collected",false},{"NDC",nullptr},{"formal_performance",!qualification}};
                if(m.table)r["table"]=c.at("methods")[mi].at("table");if(m.route)r["route_order"]=m.route->order;fresh_json(point/"result.json",r);results.push_back(r);}
            ++ordinal;
        }
    }
    check_threads(c);json result={{"status",qualification?"PASS_E183_QUALIFICATION":"PASS_E183_FORMAL_FULL_TIMED_OUTPUT_ORACLES"},{"dataset",c.at("dataset")},{"config",c},{"points",results.size()},{"formal_batches",qualification?0:formal_batches},
        {"formal_queries",qualification?0:formal_batches*n},{"qualification_queries",qualification?formal_batches*n:0},{"warmup_queries",warmup_queries},{"results",results},{"threads",1},{"cpu",15},{"full_merge_oracle_passed",true},{"full_merge_oracle_queries",oracle_queries},
        {"all_round_bits_equal",true},{"actual_round0_packets_saved",true},{"actual_later_rounds_bit_checked_and_hashed",!qualification},{"evaluation_GT_read",false},{"outer_seconds",seconds(started)},
        {"counts_collected",false},{"NDC",nullptr},{"formal_performance",!qualification},{"qualification_batches",qualification?formal_batches:0}};
    fresh_json(root/"complete.json",result);return result;
}
}
int main(int argc,char** argv){try{using namespace e183;require(argc==3&&(std::string(argv[1])=="benchmark"||std::string(argv[1])=="qualification"),"benchmark benchmark|qualification config.json");auto result=benchmark(read_json(argv[2]),std::string(argv[1])=="qualification");
    std::cout<<json{{"status",result.at("status")},{"points",result.at("points")}}.dump()<<std::endl;return 0;
}catch(const std::exception& e){std::cerr<<"FATAL E183 "<<e.what()<<std::endl;return 2;}}

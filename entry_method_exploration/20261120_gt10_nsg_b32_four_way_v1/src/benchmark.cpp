#define main e206_embedded_main
#include "../../20261120_residual_budget_matched_table_v1/src/common.inc"
#undef main

namespace e212 {
using namespace e183;

struct Case {
    const char* name;
    size_t method_index;
    bool span;
};
const std::array<Case,4> arms{{
    {"NSG",0,true},{"GT10-new",1,true},{"GT10-new-B32",2,true},{"GT10-old-B32",2,false}
}};

template<class Action>
double timed(Batch& dest,Action action) {
    const auto begin=Clock::now();
    {
        Batch received(dest.n,dest.k);
        action(received);
        copy_packet(received,dest);
        asm volatile("" :: "g"(dest.ids.data()),"g"(received.ids.data()) : "memory");
    }
    return seconds(begin);
}

struct State {int k,l;};
const std::array<State,14> matrix{{{1,64},{1,100},{1,160},{1,200},{1,320},{1,400},{1,800},
    {100,100},{100,160},{100,200},{100,320},{100,400},{100,640},{100,960}}};

void parity(const std::vector<std::unique_ptr<Batch>>& packets,const fs::path& failure) {
    try {
        all_same(*packets[2],*packets[3]);
    } catch (...) {
        packets[3]->save(failure/"scalar",false);
        packets[2]->save(failure/"span4",false);
        throw;
    }
}

json suite(const json& c) {
    check_threads(c);
    require(!c.contains("test_gt")&&!c.contains("train_gt"),"no GT timing binding");
    const std::string dataset=c.at("dataset");
    const fs::path root=c.at("output_dir");
    fresh_dir(root);
    json binding;
    auto idx=load_index(c,binding);
    Matrix input(c.at("queries"));
    require(input.n==3072,"fixed sample size");
    auto q=input.copy();
    Router router(c.at("router"),idx->d,idx->ntotal);
    Posting table(c.at("table"),idx->ntotal);
    require(!table.empty&&table.b==32,"exact full old B32");
    require(idx->metric_type==faiss::METRIC_INNER_PRODUCT,"formal IP dispatch");
    require(idx->acsg.enterpoint>=0&&idx->acsg.enterpoint<idx->ntotal,"real NSG fixed entry");
    const std::array<Method,3> methods{{
        {"NSG","NSG","","",nullptr,nullptr},
        {"GT10-new","GT10",router.name,"",&router,nullptr},
        {"B32","POST",router.name,"GT10",&router,&table}
    }};
    auto execute=[&](const Case& arm,int l,Batch& packet) {
        run_batch(*idx,q,l,methods[arm.method_index],packet);
    };
    auto select=[&](const Case& arm) {
        idx->acsg.set_flat_ip_batch4_enabled(arm.span);
    };
    fresh_json(root/"environment.json",{{"dataset",dataset},{"binding",binding},
        {"nsg_fixed_entry",idx->acsg.enterpoint},{"nsg_backend","SPAN4"},
        {"threads",process_threads()},{"cpu",sched_getcpu()}});
    json qual=json::array();
    for (auto [k,l]:matrix) {
        std::vector<std::unique_ptr<Batch>> packets;
        for (auto& arm:arms) {
            check_threads(c);
            auto packet=std::make_unique<Batch>(256,k);
            select(arm);
            execute(arm,l,*packet);
            validate(*packet,idx->ntotal);
            qual.push_back({{"method",arm.name},{"K",k},{"L",l},{"n",256},{"sha256",packet_sha(*packet)}});
            packets.push_back(std::move(packet));
        }
        parity(packets,root/"qualification_failures"/("K"+std::to_string(k)+"_L"+std::to_string(l)));
        idx->acsg.set_flat_ip_batch4_enabled(false);
        Batch scalar_nsg(256,k);
        execute(arms[0],l,scalar_nsg);
        all_same(*packets[0],scalar_nsg);
    }
    fresh_json(root/"qualification.json",qual);
    std::cout<<dataset<<" full-grid qualification passed"<<std::endl;

    json points=json::array();
    int ordinal=0;
    for (auto [k,l]:matrix) {
        const int total=arms.size();
        const auto state=root/("K"+std::to_string(k)+"_L"+std::to_string(l));
        fresh_dir(state);
        Batch warm(256,k),destination(input.n,k);
        std::vector<std::unique_ptr<Batch>> first(total);
        std::vector<json> rounds(total,json::array());
        int order=0;
        for (int rep=0; rep<2; ++rep) for (int offset=0; offset<total; ++offset) {
            const int i=(ordinal+(rep?total-1-offset:offset))%total;
            const auto& m=arms[i];
            check_threads(c);
            select(m);
            execute(m,l,warm);
            const auto wall=timed(destination,[&](Batch& packet){execute(m,l,packet);});
            check_threads(c);
            validate(destination,idx->ntotal);
            const auto hash=packet_sha(destination);
            if (!rep) {
                first[i]=std::make_unique<Batch>(destination);
                destination.save(state/m.name/"raw",false);
            } else {
                all_same(*first[i],destination);
            }
            auto row=json{{"method",m.name},{"K",k},{"L",l},{"n",input.n},{"rep",rep},
                {"seconds",wall},{"qps",input.n/wall},{"order",++order},{"sha256",hash},
                {"cpu",sched_getcpu()},{"threads",process_threads()}};
            rounds[i].push_back(row);
            fresh_json(state/m.name/("round"+std::to_string(rep)+".json"),row);
            std::cout<<dataset<<" "<<row.dump()<<std::endl;
        }
        parity(first,root/"formal_failures"/("K"+std::to_string(k)+"_L"+std::to_string(l)));
        audit_merge(*idx,q,*first[1],*first[2],table);
        for (int i=0;i<total;++i) {
            const auto& m=arms[i];
            json row={{"method",m.name},{"K",k},{"L",l},{"n",input.n},{"rounds",rounds[i]},
                {"backend",m.span?"SPAN4":"scalar"}};
            fresh_json(state/m.name/"complete.json",row);
            points.push_back(row);
        }
        ++ordinal;
    }
    return {{"status","PASS_E212_NATIVE"},{"dataset",dataset},{"points",points},{"formal_batches",points.size()*2},
            {"nsg_scalar_qualification",matrix.size()*256},{"independent_merge_queries",matrix.size()*input.n},{"public_GT_read",false}};
}
}

int main(int argc,char** argv) {
    try {
        e212::require(argc==2,"benchmark <config.json>");
        auto c=e212::read_json(argv[1]);
        auto result=e212::suite(c);
        e212::fresh_json(e212::fs::path(c.at("output_dir"))/"complete.json",result);
    } catch (const std::exception& e) {
        std::cerr<<"E212: "<<e.what()<<std::endl;
        return 1;
    }
}

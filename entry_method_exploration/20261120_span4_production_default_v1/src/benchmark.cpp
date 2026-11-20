#define main e206_embedded_main
#include "../../20261120_residual_budget_matched_table_v1/src/common.inc"
#undef main

namespace e211 {
using namespace e183;

struct Case {
    const char* name;
    bool span;
    bool residual;
};
const std::array<Case,4> arms{{{"GT10",false,false},{"B32",false,true},
    {"SPAN4-GT10",true,false},{"SPAN4-B32",true,true}}};

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

void compare_pool(const std::vector<acsg::Neighbor>& a,const std::vector<acsg::Neighbor>& b) {
    require(a.size()==b.size(),"pool shape");
    for (size_t j=0;j<a.size();++j) {
        require(a[j].id==b[j].id&&a[j].flag==b[j].flag&&equal_float(a[j].distance,b[j].distance),
                "pool slots, flags and scores");
    }
}

void compare_scratch(acsg::IndexACSGFlat& idx,const std::vector<float>& queries,
                     const Batch& main,int l,size_t n) {
    std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx.storage));
    std::array<faiss::VisitedTable,2> visits{faiss::VisitedTable(idx.ntotal),faiss::VisitedTable(idx.ntotal)};
    std::array<std::vector<acsg::Neighbor>,2> pools;
    std::vector<faiss::idx_t> ids(main.k);
    std::vector<float> distances(main.k);
    idx.acsg.search_L=l;
    for (size_t i=0;i<n;++i) {
        const auto* q=queries.data()+i*idx.d;
        const std::vector<acsg::EnterPoint> entries{
            {main.entries[3*i],1.f},{main.entries[3*i+1],1.f},{main.entries[3*i+2],1.f}};
        for (int backend=0;backend<2;++backend) {
            auto& vt=visits[backend];
            vt.advance();
            dc->set_query(q);
            idx.acsg.set_flat_ip_batch4_enabled(backend!=0);
            idx.acsg.search_new(*dc,main.k,ids.data(),distances.data(),vt,2,entries,&pools[backend]);
            require(std::equal(ids.begin(),ids.end(),main.ids.begin()+i*main.k)&&
                    !std::memcmp(distances.data(),main.distances.data()+i*main.k,main.k*sizeof(float)),
                    "scratch run matches the packet");
        }
        compare_pool(pools[0],pools[1]);
        require(visits[0].visno==visits[1].visno&&visits[0].visited==visits[1].visited,"visited state");
    }
}

struct State {int k,l;};
const std::array<State,14> matrix{{{1,64},{1,100},{1,160},{1,200},{1,320},{1,400},{1,800},
    {100,100},{100,160},{100,200},{100,320},{100,400},{100,640},{100,960}}};

void parity(const std::array<Case,4>& arms,const std::vector<std::unique_ptr<Batch>>& packets,
            const fs::path& failure) {
    for (size_t i=2; i<arms.size(); ++i) {
        try {
            all_same(*packets[arms[i].residual?1:0],*packets[i]);
        } catch (...) {
            packets[arms[i].residual?1:0]->save(failure/"reference",false);
            packets[i]->save(failure/arms[i].name,false);
            throw;
        }
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
    Method main{"GT10","GT10",router.name,"",&router,nullptr};
    Method b32{"B32","POST",router.name,"GT10",&router,&table};
    auto execute=[&](const Case& method,int l,Batch& packet) {
        run_batch(*idx,q,l,method.residual?b32:main,packet);
    };
    auto select=[&](const Case& method) {
        idx->acsg.set_flat_ip_batch4_enabled(method.span);
    };
    fresh_json(root/"environment.json",{{"dataset",dataset},{"binding",binding},{"span_bytes",0},
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
        parity(arms,packets,root/"qualification_failures"/("K"+std::to_string(k)+"_L"+std::to_string(l)));
        compare_scratch(*idx,q,*packets[0],l,64);
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
        parity(arms,first,root/"formal_failures"/("K"+std::to_string(k)+"_L"+std::to_string(l)));
        audit_merge(*idx,q,*first[0],*first[1],table);
        for (int i=0;i<total;++i) {
            const auto& m=arms[i];
            json row={{"method",m.name},{"K",k},{"L",l},{"n",input.n},{"rounds",rounds[i]},
                {"reference",m.residual?"B32":"GT10"}};
            fresh_json(state/m.name/"complete.json",row);
            points.push_back(row);
        }
        ++ordinal;
    }
    return {{"status","PASS_E211_NATIVE"},{"dataset",dataset},{"points",points},{"formal_batches",points.size()*2},
            {"scratch_pairs",matrix.size()*64},{"independent_merge_queries",matrix.size()*input.n},{"public_GT_read",false}};
}
}

int main(int argc,char** argv) {
    try {
        e211::require(argc==2,"benchmark <config.json>");
        auto c=e211::read_json(argv[1]);
        auto result=e211::suite(c);
        e211::fresh_json(e211::fs::path(c.at("output_dir"))/"complete.json",result);
    } catch (const std::exception& e) {
        std::cerr<<"E211: "<<e.what()<<std::endl;
        return 1;
    }
}

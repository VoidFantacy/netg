#define main e206_embedded_main
#include "../../20261120_residual_budget_matched_table_v1/src/common.inc"
#undef main
#include "residual.hpp"

namespace e216 {
enum class Method { main, full, fit, vote, cache };
struct Arm {const char* name; Method type;};
constexpr std::array<Arm,5> arms{{{"GT10",Method::main},{"B32",Method::full},{"B32-fit",Method::fit},
                                 {"VOTE",Method::vote},{"CACHE",Method::cache}}};

struct Trace {
    std::vector<uint8_t> scores,replaced;
    bool compare_scalar=false;
};

struct Engine {
    acsg::IndexACSGFlat& idx;
    Posting full,fit;
    Neighbors neighbors;
    Engine(acsg::IndexACSGFlat& idx,const json& cfg,const std::string& old_key,
           const std::string& fit_key="fit_table")
        :idx(idx),full(cfg.at(old_key),idx.ntotal),fit(cfg.at(fit_key),idx.ntotal),
         neighbors(cfg.at("model_dir").get<std::string>(),idx.d) {}

    void start(const Arm& arm) {
        if (arm.type==Method::vote || arm.type==Method::cache)
            neighbors.set_mode(arm.type==Method::cache);
    }

    void complete(const Arm& arm,const float* q,faiss::DistanceComputer& dc,const faiss::VisitedTable& vt,
                  const std::array<int32_t,3>& route,int k,faiss::idx_t* ids,float* d,Trace* trace) {
        if (arm.type==Method::main) return;
        auto& table=arm.type==Method::full?full:fit;
        for (int j=0;j<k;++j)
            if (ids[j]<0 || ids[j]>=idx.ntotal || !std::isfinite(d[j])) {
                exp180::cap::apply(dc,*idx.acsg.final_graph,vt,route,k,ids,d,table);
                if (trace) {trace->scores.push_back(0); trace->replaced.push_back(0);}
                return;
            }
        const int count=fast_plan(table,route,ids,k);
        require(count>=0,"valid B32 candidate plan");
        size_t n=0;
        if (count && (arm.type==Method::vote || arm.type==Method::cache))
            n=replace_tail(table,count,route,ids,k,neighbors,q,arm.type==Method::cache);
        if (trace) {
            trace->scores.push_back(count);
            trace->replaced.push_back(n);
        }
        if (count==0) return;
        if (trace && trace->compare_scalar) {
            std::vector<Posting::Record> ref;
            for (int j=0;j<k;++j) ref.push_back({ids[j],d[j],uint32_t(j),false});
            std::set<faiss::idx_t> unique(ids,ids+k);
            for (int j=0;j<count;++j) {
                auto id=table.candidate[j];
                require(id>=0 && id<idx.ntotal && unique.insert(id).second,"exact distinct budget qualification");
                ref.push_back({id,dc(id),uint32_t(k+j),false});
            }
            std::sort(ref.begin(),ref.end(),Posting::better);
            score_merge(table,dc,k,count,ids,d);
            for (int j=0;j<k;++j)
                require(ids[j]==ref[j].id && equal_float(d[j],ref[j].distance),"independent scalar full-order merge");
        } else {
            score_merge(table,dc,k,count,ids,d);
        }
    }
};

std::array<int32_t,3> route_at(const Batch& b,size_t i) {
    return {b.entries[3*i],b.entries[3*i+1],b.entries[3*i+2]};
}

void run_batch(Engine& e,const std::vector<float>& q,int l,Router& router,
               const Arm& arm,Batch& b,Trace* trace=nullptr) {
    auto& idx=e.idx;
    idx.acsg.search_L=l;
    std::vector<std::vector<acsg::EnterPoint>> route(b.n);
    for (size_t i=0;i<b.n;++i) {
        const auto r=router.route(q.data()+i*idx.d);
        for (size_t j=0;j<3;++j) {
            b.entries[3*i+j]=r.ids[j];
            b.profile_distances[3*i+j]=r.distances[j];
            route[i].emplace_back(r.ids[j],1.f);
        }
    }
    faiss::VisitedTable visited(idx.ntotal);
    std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx.storage));
    std::vector<acsg::Neighbor> pool;
    std::vector<faiss::idx_t> ids(b.k);
    for (size_t i=0;i<b.n;++i) {
        const auto* row=q.data()+i*idx.d;
        dc->set_query(row);
        visited.advance();
        auto* dis=b.distances.data()+i*b.k;
        idx.acsg.search_new(*dc,b.k,ids.data(),dis,visited,2,route[i],&pool);
        e.complete(arm,row,*dc,visited,route_at(b,i),b.k,ids.data(),dis,trace);
        std::copy(ids.begin(),ids.end(),b.ids.begin()+i*b.k);
    }
}

template<class Action>
double timed(Batch& destination,Action execute) {
    const auto begin=Clock::now();
    {
        Batch temporary(destination.n,destination.k);
        execute(temporary);
        copy_packet(temporary,destination);
        asm volatile("" :: "g"(destination.ids.data()),"g"(temporary.ids.data()) : "memory");
    }
    return seconds(begin);
}

void build_graph(const json& c) {
    check_threads(c);
    const auto begin=Clock::now();
    const fs::path model=c.at("model_dir");
    const auto x=read_raw<float>(model/"projected.f32");
    require(x.size()%projected_dim==0 && x.size()/projected_dim>=32,"valid projected fit");
    const size_t n=x.size()/projected_dim;
    hnswlib::InnerProductSpace space(projected_dim);
    HNSW graph(&space,n,16,100,100);
    for (size_t i=0;i<n;++i) graph.addPoint(x.data()+i*projected_dim,i);
    graph.saveIndex((model/"fit.hnsw").string());
    fresh_json(model/"graph_build.json",{{"nodes",n},{"M",16},{"ef_construction",100},{"seed",100},
                                        {"wall_seconds",seconds(begin)}});
}

Batch read_main(const fs::path& path,size_t n,int k) {
    Batch b(n,k);
    b.ids=read_raw<int32_t>(path/"ids.i32");
    b.distances=read_raw<float>(path/"distances.f32");
    b.entries=read_raw<int32_t>(path/"entry_ids.i32");
    b.profile_distances=read_raw<float>(path/"profile_distances.f32");
    require(b.ids.size()==n*k && b.distances.size()==n*k && b.entries.size()==n*3 &&
            b.profile_distances.size()==n*3,"training-role packet");
    return b;
}

void heldout(const json& c) {
    check_threads(c);
    require(!c.contains("queries") && !c.contains("test_gt"),"held-out training roles");
    const fs::path dir=c.at("output_dir");
    fresh_dir(dir);
    json binding;
    auto idx=load_index(c,binding);
    Engine e(*idx,c,"anchor_table","anchor_table");
    const Matrix q(c.at("train_queries"));
    const fs::path model=c.at("model_dir");
    const auto subset=read_raw<int32_t>(model/"held_rows.i32");
    const auto roles=read_raw<int8_t>(c.at("roles").get<std::string>());
    require(roles.size()==q.n,"held-out role shape");
    for (const int k:{1,100}) {
        const auto files=c.at("packets").at(std::to_string(k));
        const auto main=read_main(files.at("low").get<std::string>(),q.n,k);
        const auto scalar=read_main(files.at("anchor").get<std::string>(),q.n,k);
        const auto node=dir/("k"+std::to_string(k));
        const auto run=[&](const Arm& arm,Batch& out,size_t count,Trace* trace) {
            faiss::VisitedTable vt(idx->ntotal);
            std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx->storage));
            std::vector<faiss::idx_t> ids(k);
            for (size_t z=0;z<count;++z) {
                auto row=subset[z];
                require(row>=0 && row<int(q.n) && (roles[row]==1 || roles[row]==2),"explicit held-out role");
                const auto* v=q.row(row);
                dc->set_query(v);
                std::copy_n(main.ids.begin()+row*k,k,ids.begin());
                auto* d=out.distances.data()+z*k;
                std::copy_n(main.distances.begin()+row*k,k,d);
                std::copy_n(main.entries.begin()+row*3,3,out.entries.begin()+z*3);
                std::copy_n(main.profile_distances.begin()+row*3,3,out.profile_distances.begin()+z*3);
                e.complete(arm,v,*dc,vt,route_at(main,row),k,ids.data(),d,trace);
                std::copy(ids.begin(),ids.end(),out.ids.begin()+z*k);
            }
        };
        std::array<std::unique_ptr<Batch>,3> first;
        std::array<Trace,3> quals;
        for (int i=0;i<3;++i) {
            e.start(arms[i+2]);
            Batch out(128,k);
            quals[i].compare_scalar=true;
            run(arms[i+2],out,128,&quals[i]);
        }
        require(quals[0].scores==quals[1].scores && quals[0].scores==quals[2].scores,"same held-out actual score count");
        json timing=json::array();
        for (int rep=0;rep<2;++rep) for (int offset=0;offset<3;++offset) {
            const int i=rep?2-offset:offset;
            const auto& arm=arms[i+2];
            e.start(arm);
            Batch result(subset.size(),k),warm(256,k);
            run(arm,warm,256,nullptr);
            const auto begin=Clock::now();
            run(arm,result,subset.size(),nullptr);
            const auto wall=seconds(begin);
            check_threads(c);
            validate(result,idx->ntotal);
            if (!rep) {
                first[i]=std::make_unique<Batch>(result);
                result.save(node/arm.name/"raw",false);
            } else all_same(result,*first[i]);
            timing.push_back({{"arm",arm.name},{"rep",rep},{"seconds",wall}});
        }
        for (size_t i=0;i<subset.size();++i) {
            const int row=subset[i];
            for (int j=0;j<k;++j)
                require(first[0]->ids[i*k+j]==scalar.ids[row*k+j] &&
                        equal_float(first[0]->distances[i*k+j],scalar.distances[row*k+j]),"E206 fit-B32 score and ID parity");
        }
        fresh_json(node/"timing.json",timing);
        json qual=json::object();
        for (int i=0;i<3;++i)
            qual[arms[i+2].name]={{"actual_scores",quals[i].scores},{"replaced",quals[i].replaced}};
        fresh_json(node/"qualification.json",qual);
    }
    fresh_json(dir/"complete.json",{{"status","PASS_E216_HELDOUT"},{"queries",subset.size()},
                                   {"public_test_read",false}});
}

void formal(const json& c) {
    check_threads(c);
    require(!c.contains("test_gt") && !c.contains("train_gt"),"formal timing without GT");
    const fs::path out=c.at("output_dir");
    fresh_dir(out);
    json binding;
    auto idx=load_index(c,binding);
    idx->acsg.set_flat_ip_batch4_enabled(true);
    const Matrix input(c.at("queries"));
    require(input.n==3072 && input.start==0,"fixed formal window");
    const auto q=input.copy();
    Router router(c.at("router"),idx->d,idx->ntotal);
    Engine engine(*idx,c,"table");
    size_t ordinal=0;
    const int k=c.at("K"), focus=c.at("focus_L");
    const auto budgets=c.at("dense_L").get<std::vector<int>>();
    for (const int l:budgets) {
        std::vector<Arm> active{arms[0],arms[1],arms[2]};
        if (l==focus) active.push_back(arms[4]);
        const auto dir=out/("K"+std::to_string(k)+"_L"+std::to_string(l));
        fresh_dir(dir);
        std::array<Trace,3> quals;
        if (l==184) {
            for (size_t i=0;i<3;++i) {
                Batch result(256,k);
                const auto& arm=arms[i+2];
                engine.start(arm);
                quals[i].compare_scalar=true;
                run_batch(engine,q,l,router,arm,result,&quals[i]);
                validate(result,idx->ntotal);
            }
            require(quals[0].scores==quals[1].scores && quals[0].scores==quals[2].scores,"formal matched score counts");
            json evidence=json::object();
            for (size_t i=0;i<3;++i)
                evidence[arms[i+2].name]={{"scores",quals[i].scores},{"new_ids",quals[i].replaced}};
            fresh_json(dir/"qualification.json",evidence);
        }
        std::array<std::unique_ptr<Batch>,arms.size()> first;
        Batch warm(256,k),destination(input.n,k);
        int order=0;
        for (int rep=0;rep<2;++rep) for (size_t offset=0;offset<active.size();++offset) {
            const size_t i=(ordinal+(rep?active.size()-1-offset:offset))%active.size();
            const auto& arm=active[i];
            engine.start(arm);
            check_threads(c);
            run_batch(engine,q,l,router,arm,warm);
            const double seconds=timed(destination,[&](Batch& b){run_batch(engine,q,l,router,arm,b);});
            check_threads(c);
            validate(destination,idx->ntotal);
            if (!rep) {
                first[i]=std::make_unique<Batch>(destination);
                destination.save(dir/arm.name/"raw",false);
            } else all_same(*first[i],destination);
            const json row{{"method",arm.name},{"K",k},{"L",l},{"n",input.n},{"rep",rep},
                {"seconds",seconds},{"qps",input.n/seconds},{"order",++order},
                {"sha256",packet_sha(destination)},{"cpu",sched_getcpu()},{"threads",process_threads()}};
            fresh_json(dir/arm.name/("round"+std::to_string(rep)+".json"),row);
            std::cout<<row.dump()<<std::endl;
        }
        ++ordinal;
    }
    fresh_json(out/"complete.json",{{"status","PASS_E216_DENSE"},{"points",3*budgets.size()+1},
                                   {"batches",2*(3*budgets.size()+1)},{"public_GT_read",false},
                                   {"binding",binding}});
}
}

int main(int argc,char** argv) {
    try {
        e183::require(argc==3,"benchmark build|heldout|formal config.json");
        const auto cfg=e183::read_json(argv[2]);
        const std::string stage=argv[1];
        if (stage=="build") e216::build_graph(cfg);
        else if (stage=="heldout") e216::heldout(cfg);
        else if (stage=="formal") e216::formal(cfg);
        else throw std::runtime_error("unknown benchmark stage");
        return 0;
    } catch (const std::exception& e) {
        std::cerr<<"E216: "<<e.what()<<std::endl;
        return 1;
    }
}

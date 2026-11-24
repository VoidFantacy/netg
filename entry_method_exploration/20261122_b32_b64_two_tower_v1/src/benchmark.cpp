#define main e206_embedded_main
#include "../../20261120_residual_budget_matched_table_v1/src/common.inc"
#undef main
#include "../../20261121_neighbor_residual_online_v1/src/residual.hpp"

namespace e226 {
using namespace e183;
using e216::IdSet;
constexpr int K=100, D=512, code_dim=32, max_candidates=192;

void compile64(const json& cfg) {
    const auto start=Clock::now();
    const fs::path output=cfg.at("output_dir");
    fresh_dir(output);
    const size_t nbase=cfg.at("base_n");
    Posting b32(cfg.at("table"),nbase);
    require(b32.b==32,"original B32");
    const fs::path src=cfg.at("token_source");
    const fs::path teacher=cfg.at("teacher_root");
    const auto q=read_raw<int32_t>(src/"token_queries.i32");
    const auto t=read_raw<int32_t>(src/"token_targets.i32");
    const auto routes=read_raw<int32_t>(teacher/"raw/entry_ids.i32");
    require(q.size()==t.size() && routes.size()%3==0,"frozen token shapes");
    std::map<std::pair<int32_t,int32_t>,std::vector<uint32_t>> incidence;
    std::vector<std::array<int,3>> slots(routes.size()/3);
    for (size_t i=0;i<slots.size();++i) {
        for (int j=0;j<3;++j) {
            slots[i][j]=b32.lookup(routes[i*3+j],nullptr);
            require(slots[i][j]>=0,"teacher enters known table rows");
        }
    }
    for (uint32_t i=0;i<q.size();++i) {
        require(q[i]>=0 && size_t(q[i])<slots.size() && t[i]>=0 && size_t(t[i])<nbase,"token domain");
        for (auto row:slots[q[i]]) incidence[{row,t[i]}].push_back(i);
    }
    Rows rows(b32.H);
    for (size_t row=0;row<rows.size();++row)
        rows[row].assign(b32.targets.begin()+row*32,b32.targets.begin()+row*32+b32.counts[row]);
    const auto prefix=rows;
    std::vector<Edge> edges;
    edges.reserve(incidence.size());
    std::vector<uint8_t> covered(q.size());
    for (auto& item:incidence) {
        const auto [row,id]=item.first;
        const bool present=std::find(rows[row].begin(),rows[row].end(),id)!=rows[row].end();
        if (present) for (auto token:item.second) covered[token]=1;
        edges.push_back({row,id,std::move(item.second),present});
    }
    incidence.clear();
    const auto old_covered=std::accumulate(covered.begin(),covered.end(),uint64_t(0));
    require(old_covered==cfg.at("old_covered"),"retained original token coverage");
    const auto log=extend(edges,covered,rows,64);
    uint64_t all=0;
    size_t appended=0;
    for (size_t i=0;i<q.size();++i) {
        bool seen=false;
        for (const auto row:slots[q[i]])
            seen|=std::find(rows[row].begin(),rows[row].end(),t[i])!=rows[row].end();
        if (seen!=bool(covered[i])) throw std::runtime_error("independent E226 token coverage");
        all+=seen;
    }
    std::vector<int32_t> payload(rows.size()*64,-1);
    std::vector<uint8_t> count(rows.size());
    for (size_t i=0;i<rows.size();++i) {
        require(rows[i].size()<=64 && rows[i].size()>=prefix[i].size() &&
            std::equal(prefix[i].begin(),prefix[i].end(),rows[i].begin()),"B64 preserves ordered B32 prefix");
        count[i]=rows[i].size();
        appended+=rows[i].size()-prefix[i].size();
        std::copy(rows[i].begin(),rows[i].end(),payload.begin()+i*64);
    }
    write_raw(output/"B64.ids.i32",payload);
    write_raw(output/"B64.counts.i8",count);
    fresh_json(output/"growth.json",log);
    fresh_json(output/"complete.json",{{"status","PASS_E226_B64"},{"rows",rows.size()},{"teacher",slots.size()},
        {"tokens",t.size()},{"covered_B32",old_covered},{"covered_B64",all},
        {"appended_IDs",appended},{"seconds",seconds(start)}});
}

struct Arm226 { const char* name; int pool; int code; int cap; };
constexpr Arm226 raw32{"B32",32,-1,96},raw64{"B64",64,-1,192},
    pca32{"PCA-B32",32,0,48},pca64{"PCA-B64",64,0,48},
    twin32{"TT-B32",32,1,48},twin64{"TT-B64",64,2,48};
constexpr std::array<Arm226,6> arms{raw32,raw64,pca32,twin32,pca64,twin64};

struct Ledger {
    int candidates=0, exact=0;
    std::array<int32_t,max_candidates> ids;
};

struct Encoder {
    std::vector<float> weights,codes;
    explicit Encoder(const fs::path& path,size_t n)
        : weights(read_raw<float>(path/"query.f32")),codes(read_raw<float>(path/"codes.f32")) {
        require(weights.size()==D*code_dim && codes.size()==n*code_dim,"encoder dimensions");
    }

    void query(const float* q,float* result) const {
        for (int j=0;j<code_dim;++j) result[j]=faiss::fvec_inner_product(q,weights.data()+j*D,D);
    }

    float similarity(const float* q,int slot) const {
        if (slot<0) throw std::runtime_error("missing candidate short code");
        return faiss::fvec_inner_product(q,codes.data()+size_t(slot)*code_dim,code_dim);
    }
};

class Pools {
    Posting original;
    std::vector<int32_t> wide,slots;
    std::vector<uint8_t> wide_count;
    std::vector<Encoder> encoders;
public:
    Pools(const json& cfg,size_t nbase)
        :original(cfg.at("table"),nbase),
         wide(read_raw<int32_t>(fs::path(cfg.at("pool_dir"))/"B64.ids.i32")),
         slots(nbase,-1),wide_count(read_raw<uint8_t>(fs::path(cfg.at("pool_dir"))/"B64.counts.i8")) {
        require(wide.size()==size_t(original.H)*64 && wide_count.size()==original.H,"B64 configured shape");
        const fs::path model=cfg.at("model_dir");
        const auto ids=read_raw<int32_t>(model/"ids.i32");
        for (size_t i=0;i<ids.size();++i) {
            require(ids[i]>=0 && size_t(ids[i])<nbase && slots[ids[i]]<0,"unique code ID domain");
            slots[ids[i]]=i;
        }
        for (const auto* name:{"pca","twin32","twin64"})
            encoders.emplace_back(model/name,ids.size());
        for (size_t i=0;i<original.H;++i) {
            require(wide_count[i]>=original.counts[i] && wide_count[i]<=64 &&
                    std::equal(original.targets.begin()+i*32,original.targets.begin()+i*32+original.counts[i],
                               wide.begin()+i*64),"frozen B32 prefix");
            for (int j=0;j<wide_count[i];++j) {
                const auto id=wide[i*64+j];
                require(id>=0 && size_t(id)<nbase && slots[id]>=0,"every row ID coded");
            }
        }
    }

    void complete_full_b32(const std::array<int32_t,3>& route,faiss::DistanceComputer& dc,
                           faiss::idx_t* ids,float* distances) {
        const int count=fast_plan(original,route,ids,K);
        if (count<0) throw std::runtime_error("B32 missing row");
        if (count) e216::score_merge(original,dc,K,count,ids,distances);
    }

    Ledger select(const Arm226& arm,const float* q,const std::array<int32_t,3>& route,const faiss::idx_t* main) {
        Ledger r;
        if (arm.pool==32) {
            r.candidates=fast_plan(original,route,main,K);
            if (r.candidates<0) throw std::runtime_error("B32 missing row");
            std::copy_n(original.candidate.begin(),r.candidates,r.ids.begin());
        } else {
            IdSet<512> seen;
            for (int i=0;i<K;++i) seen.add(main[i]);
            for (const auto label:route) {
                const int slot=original.lookup(label,nullptr);
                if (slot<0) throw std::runtime_error("B64 missing row");
                for (int i=0;i<wide_count[slot];++i) {
                    const auto id=wide[size_t(slot)*64+i];
                    if (seen.has(id)) continue;
                    seen.add(id);
                    r.ids[r.candidates++]=id;
                }
            }
        }
        r.exact=std::min(arm.cap,r.candidates);
        if (arm.code<0 || r.exact==r.candidates) return r;
        const auto& encoder=encoders.at(arm.code);
        std::array<float,code_dim> qshort;
        encoder.query(q,qshort.data());
        using Ranked=std::pair<float,int>;
        std::array<Ranked,max_candidates> rank;
        for (int i=0;i<r.candidates;++i)
            rank[i]={-encoder.similarity(qshort.data(),slots[r.ids[i]]),i};
        const auto cutoff=rank.begin()+r.exact;
        std::nth_element(rank.begin(),cutoff,rank.begin()+r.candidates);
        std::sort(rank.begin(),cutoff,[](auto a,auto b){return a.second<b.second;});
        for (int i=0;i<r.exact;++i) r.ids[i]=r.ids[rank[i].second];
        return r;
    }

    void score(const Ledger& work,faiss::DistanceComputer& dc,faiss::idx_t* ids,float* d,bool audit) {
        using Record=Posting::Record;
        if (!work.exact) return;
        std::vector<Record> reference;
        if (audit) {
            std::set<faiss::idx_t> unique(ids,ids+K);
            for (int j=0;j<K;++j) reference.push_back({ids[j],d[j],uint32_t(j),false});
            for (int j=0;j<work.exact;++j) {
                require(unique.insert(work.ids[j]).second,"all scored IDs distinct and outside main");
                reference.push_back({work.ids[j],dc(work.ids[j]),uint32_t(K+j),false});
            }
            std::sort(reference.begin(),reference.end(),Posting::better);
        }
        if (work.exact<=96) {
            std::copy_n(work.ids.begin(),work.exact,original.candidate.begin());
            e216::score_merge(original,dc,K,work.exact,ids,d);
        } else {
            std::array<Record,K> heap;
            for (int j=0;j<K;++j) heap[j]={ids[j],d[j],uint32_t(j),false};
            std::make_heap(heap.begin(),heap.end(),Posting::better);
            auto add=[&](int pos,float value) {
                if (!std::isfinite(value)) throw std::runtime_error("non-finite original score");
                if (value>=heap.front().distance) return;
                std::pop_heap(heap.begin(),heap.end(),Posting::better);
                heap.back()={work.ids[pos],value,uint32_t(K+pos),false};
                std::push_heap(heap.begin(),heap.end(),Posting::better);
            };
            int pos=0;
            for (;pos+3<work.exact;pos+=4) {
                const auto* m=work.ids.data()+pos;
                float v[4];
                dc.distances_batch_4(m[0],m[1],m[2],m[3],v[0],v[1],v[2],v[3]);
                for (int j=0;j<4;++j) add(pos+j,v[j]);
            }
            for (;pos<work.exact;++pos) add(pos,dc(work.ids[pos]));
            std::sort(heap.begin(),heap.end(),Posting::better);
            for (int i=0;i<K;++i) {ids[i]=heap[i].id;d[i]=heap[i].distance;}
        }
        if (audit)
            for (int i=0;i<K;++i)
                require(ids[i]==reference[i].id && equal_float(d[i],reference[i].distance),"native scalar ranking parity");
    }
};

std::array<int32_t,3> route_at(const Batch& b,size_t i) {
    return {b.entries[i*3],b.entries[i*3+1],b.entries[i*3+2]};
}

Batch load_batch(const fs::path& path,size_t n) {
    Batch b(n,K);
    b.ids=read_raw<int32_t>(path/"ids.i32");
    b.distances=read_raw<float>(path/"distances.f32");
    b.entries=read_raw<int32_t>(path/"entry_ids.i32");
    b.profile_distances=read_raw<float>(path/"profile_distances.f32");
    require(b.ids.size()==n*K && b.distances.size()==n*K &&
        b.entries.size()==n*3 && b.profile_distances.size()==n*3,"cached query packets");
    return b;
}

void replay(const json& cfg) {
    check_threads(cfg);
    const fs::path root=cfg.at("output_dir");
    fresh_dir(root);
    json binding;
    auto idx=load_index(cfg,binding);
    Pools pools(cfg,idx->ntotal);
    const Matrix queries(cfg.at("queries"));
    require(queries.start==3072 && queries.n==3072 && queries.d==D,"public fit and calibration pack");
    const fs::path source=cfg.at("teacher_cache");
    const auto held=read_raw<int32_t>(cfg.at("cal_rows").get<std::string>());
    require(held.size()>=1000 && held.size()<=1024 && std::all_of(held.begin(),held.end(),[&](auto v){
        return v>=0 && size_t(v)<queries.n;}),"calibration rows only");
    std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx->storage));
    size_t points=0;
    for (int l:cfg.at("offline_L").get<std::vector<int>>()) {
        const auto key="K100_L"+std::to_string(l);
        const auto main=load_batch(source/key/"GT10/raw",queries.n);
        const auto old=load_batch(source/key/"B32/raw",queries.n);
        std::vector<Arm226> variants{raw32,raw64};
        for (Arm226 a:{pca32,twin32,pca64,twin64})
            for (int cap:{16,32,48}) {
                a.cap=cap;
                variants.push_back(a);
            }
        for (const auto& method:variants) {
            const auto dir=root/key/(std::string(method.name)+(method.code>=0?"-"+std::to_string(method.cap):""));
            fresh_dir(dir);
            Batch output(held.size(),K);
            std::array<faiss::idx_t,K> ids;
            std::vector<uint8_t> before,after;
            std::vector<int32_t> selected;
            for (size_t i=0;i<held.size();++i) {
                const auto row=held[i];
                const auto* q=queries.row(row);
                dc->set_query(q);
                std::copy_n(main.ids.begin()+row*K,K,ids.begin());
                auto* d=output.distances.data()+i*K;
                std::copy_n(main.distances.begin()+row*K,K,d);
                std::copy_n(main.entries.begin()+row*3,3,output.entries.begin()+i*3);
                std::copy_n(main.profile_distances.begin()+row*3,3,output.profile_distances.begin()+i*3);
                const auto chosen=pools.select(method,q,route_at(main,row),ids.data());
                pools.score(chosen,*dc,ids.data(),d,true);
                before.push_back(chosen.candidates);
                after.push_back(chosen.exact);
                selected.insert(selected.end(),chosen.ids.begin(),chosen.ids.begin()+chosen.exact);
                std::copy(ids.begin(),ids.end(),output.ids.begin()+i*K);
                if (method.pool==32 && method.code<0)
                    for (int j=0;j<K;++j)
                        require(ids[j]==old.ids[row*K+j] && equal_float(d[j],old.distances[row*K+j]),"E222 native full B32 parity");
            }
            validate(output,idx->ntotal);
            output.save(dir/"raw",false);
            write_raw(dir/"candidates.i8",before);
            write_raw(dir/"exact.i8",after);
            write_raw(dir/"selected.i32",selected);
            ++points;
        }
    }
    fresh_json(root/"complete.json",{{"status","PASS_E226_REPLAY"},{"points",points},
        {"query_merge_checks",points*held.size()},{"queries_per_point",held.size()},{"binding",binding}});
}

void search(Pools& pools,acsg::IndexACSGFlat& idx,Router& router,const std::vector<float>& q,
            Batch& b,const Arm226& method,int l,std::vector<uint8_t>* work=nullptr) {
    idx.acsg.search_L=l;
    std::vector<std::vector<acsg::EnterPoint>> entries(b.n);
    for (size_t i=0;i<b.n;++i) {
        const auto route=router.route(q.data()+i*D);
        for (int j=0;j<3;++j) {
            b.entries[i*3+j]=route.ids[j];
            b.profile_distances[i*3+j]=route.distances[j];
            entries[i].emplace_back(route.ids[j],1.f);
        }
    }
    faiss::VisitedTable visited(idx.ntotal);
    std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx.storage));
    std::vector<acsg::Neighbor> scratch;
    std::array<faiss::idx_t,K> ids;
    for (size_t i=0;i<b.n;++i) {
        const auto* row=q.data()+i*D;
        dc->set_query(row);
        visited.advance();
        auto* d=b.distances.data()+i*K;
        idx.acsg.search_new(*dc,K,ids.data(),d,visited,2,entries[i],&scratch);
        if (method.pool==32 && method.code<0 && !work) {
            pools.complete_full_b32(route_at(b,i),*dc,ids.data(),d);
        } else {
            const auto plan=pools.select(method,row,route_at(b,i),ids.data());
            pools.score(plan,*dc,ids.data(),d,work!=nullptr);
            if (work) {
                work->push_back(plan.candidates);
                work->push_back(plan.exact);
            }
        }
        std::copy(ids.begin(),ids.end(),b.ids.begin()+i*K);
    }
}

void formal(const json& cfg) {
    check_threads(cfg);
    const fs::path root=cfg.at("output_dir");
    fresh_dir(root);
    json binding;
    auto idx=load_index(cfg,binding);
    idx->acsg.set_flat_ip_batch4_enabled(true);
    const Matrix input(cfg.at("queries"));
    require(input.n==3072 && input.start==0 && input.d==D && cfg.at("K")==K,"fixed true K100 public holdout");
    Router router(cfg.at("router"),idx->d,idx->ntotal);
    const auto q=input.copy();
    Pools pools(cfg,idx->ntotal);
    size_t ordinal=0;
    for (const int l:cfg.at("dense_L").get<std::vector<int>>()) {
        const auto point=root/("K100_L"+std::to_string(l));
        fresh_dir(point);
        std::array<std::unique_ptr<Batch>,arms.size()> first;
        Batch warm(256,K),dest(input.n,K);
        int order=0;
        for (int rep=0;rep<2;++rep) for (size_t off=0;off<arms.size();++off) {
            const size_t i=(ordinal+(rep?arms.size()-1-off:off))%arms.size();
            const auto& arm=arms[i];
            check_threads(cfg);
            search(pools,*idx,router,q,warm,arm,l);
            const auto start=Clock::now();
            {
                Batch temporary(input.n,K);
                search(pools,*idx,router,q,temporary,arm,l);
                copy_packet(temporary,dest);
                asm volatile("" :: "g"(dest.ids.data()),"g"(temporary.ids.data()) : "memory");
            }
            const auto wall=seconds(start);
            check_threads(cfg);
            validate(dest,idx->ntotal);
            const auto path=point/arm.name;
            if (!rep) {
                first[i]=std::make_unique<Batch>(dest);
                dest.save(path/"raw",false);
            } else all_same(dest,*first[i]);
            json timing{{"method",arm.name},{"K",K},{"L",l},{"n",input.n},{"rep",rep},
                {"seconds",wall},{"qps",input.n/wall},{"order",++order},{"cpu",sched_getcpu()},
                {"threads",process_threads()},{"sha256",packet_sha(dest)}};
            fresh_json(path/("round"+std::to_string(rep)+".json"),timing);
            std::cout<<timing.dump()<<std::endl;
        }
        for (size_t i=0;i<arms.size();++i) {
            Batch verified(256,K);
            std::vector<uint8_t> work;
            search(pools,*idx,router,q,verified,arms[i],l,&work);
            if (!std::equal(verified.ids.begin(),verified.ids.end(),first[i]->ids.begin()) ||
                std::memcmp(verified.distances.data(),first[i]->distances.data(),verified.distances.size()*4))
                throw std::runtime_error("formal prefix scalar audit mismatch");
            write_raw(point/arms[i].name/"qualification.i8",work);
        }
        ++ordinal;
    }
    fresh_json(root/"complete.json",{{"status","PASS_E226_FORMAL"},{"points",ordinal*arms.size()},
        {"batches",2*ordinal*arms.size()},{"public_GT_read",false},{"binding",binding}});
}
}

int main(int argc,char** argv) {
    try {
        e183::require(argc==3,"benchmark compile64|replay|formal config.json");
        const auto cfg=e183::read_json(argv[2]);
        e183::require(!cfg.contains("train_gt")&&!cfg.contains("test_gt"),"GT excluded from native processes");
        const std::string stage=argv[1];
        if (stage=="compile64") e226::compile64(cfg);
        else if (stage=="replay") e226::replay(cfg);
        else if (stage=="formal") e226::formal(cfg);
        else throw std::runtime_error("unknown stage");
        return 0;
    } catch (const std::exception& error) {
        std::cerr<<"E226: "<<error.what()<<std::endl;
        return 1;
    }
}

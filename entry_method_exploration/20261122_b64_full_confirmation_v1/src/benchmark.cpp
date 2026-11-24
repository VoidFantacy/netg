#define main e206_embedded_main
#include "../../20261120_residual_budget_matched_table_v1/src/common.inc"
#undef main
#include "../../20261121_neighbor_residual_online_v1/src/residual.hpp"

namespace e228 {
using namespace e183;
using e216::IdSet;
constexpr int K=100,D=512,cap=192;
constexpr std::array<const char*,2> arms{"B32","B64"};

struct Ledger {
    int exact=0;
    std::array<int32_t,cap> ids;
};

class Pools {
    Posting original;
    std::vector<int32_t> wide;
    std::vector<uint8_t> wide_count;
public:
    Pools(const json& c,size_t nbase)
        :original(c.at("table"),nbase),
         wide(read_raw<int32_t>(fs::path(c.at("pool_dir"))/"B64.ids.i32")),
         wide_count(read_raw<uint8_t>(fs::path(c.at("pool_dir"))/"B64.counts.i8")) {
        require(original.b==32 && wide.size()==size_t(original.H)*64 && wide_count.size()==original.H,"frozen table shape");
        for (size_t i=0;i<original.H;++i) {
            const auto* row=wide.data()+i*64;
            require(wide_count[i]>=original.counts[i] && wide_count[i]<=64 &&
                    std::equal(original.targets.begin()+i*32,original.targets.begin()+i*32+original.counts[i],row),
                    "B64 preserves ordered B32 prefix");
            std::set<int32_t> seen;
            for (int j=0;j<wide_count[i];++j)
                require(row[j]>=0 && size_t(row[j])<nbase && seen.insert(row[j]).second,"valid B64 row");
        }
    }

    void complete_full_b32(const std::array<int32_t,3>& route,faiss::DistanceComputer& dc,
                           faiss::idx_t* ids,float* distances) {
        const int count=fast_plan(original,route,ids,K);
        if (count<0) throw std::runtime_error("B32 missing row");
        if (count) e216::score_merge(original,dc,K,count,ids,distances);
    }

    int select(bool extended,const std::array<int32_t,3>& route,const faiss::idx_t* main,Ledger& r) {
        if (!extended) {
            r.exact=fast_plan(original,route,main,K);
            if (r.exact<0) throw std::runtime_error("B32 missing row");
            std::copy_n(original.candidate.begin(),r.exact,r.ids.begin());
            return r.exact;
        }
        IdSet<512> seen;
        for (int i=0;i<K;++i) seen.add(main[i]);
        for (const auto label:route) {
            const int slot=original.lookup(label,nullptr);
            if (slot<0) throw std::runtime_error("B64 missing row");
            for (int i=0;i<wide_count[slot];++i) {
                const auto id=wide[size_t(slot)*64+i];
                if (seen.has(id)) continue;
                seen.add(id);
                r.ids[r.exact++]=id;
            }
        }
        return r.exact;
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

void search(Pools& pools,acsg::IndexACSGFlat& idx,Router& router,const std::vector<float>& q,
            Batch& b,int l,bool extended,std::vector<uint8_t>* work=nullptr) {
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
    auto dc=std::unique_ptr<faiss::DistanceComputer>(acsg::storage_distance_computer(idx.storage));
    std::vector<acsg::Neighbor> scratch;
    std::array<faiss::idx_t,K> ids;
    for (size_t i=0;i<b.n;++i) {
        const auto* row=q.data()+i*D;
        dc->set_query(row);
        visited.advance();
        auto* d=b.distances.data()+i*K;
        idx.acsg.search_new(*dc,K,ids.data(),d,visited,2,entries[i],&scratch);
        const auto route=route_at(b,i);
        if (!extended && !work) {
            pools.complete_full_b32(route,*dc,ids.data(),d);
        } else {
            Ledger plan;
            const int count=pools.select(extended,route,ids.data(),plan);
            if (work && extended) {
                Ledger prefix;
                pools.select(false,route,ids.data(),prefix);
                for (int j=0;j<prefix.exact;++j)
                    require(std::find(plan.ids.begin(),plan.ids.begin()+count,prefix.ids[j])!=plan.ids.begin()+count,
                            "per-query B64 candidate superset");
            }
            pools.score(plan,*dc,ids.data(),d,work!=nullptr);
            if (work) work->push_back(count);
        }
        std::copy(ids.begin(),ids.end(),b.ids.begin()+i*K);
    }
}

std::vector<float> select_queries(const json& c) {
    const Matrix input(c.at("queries"));
    require(input.n==10000 && input.d==D,"full physical query container");
    const auto numbers=read_raw<int32_t>(c.at("rows").get<std::string>());
    require(numbers.size()==3072 && std::is_sorted(numbers.begin(),numbers.end()) &&
            std::adjacent_find(numbers.begin(),numbers.end())==numbers.end(),"fixed distinct holdout physical rows");
    std::vector<float> result(numbers.size()*D);
    for (size_t i=0;i<numbers.size();++i) {
        require(numbers[i]>=6144 && size_t(numbers[i])<input.n,"sealed public holdout bounds");
        const auto* q=input.row(numbers[i]);
        require(std::all_of(q,q+D,[](float x){return std::isfinite(x);}),"finite selected queries");
        std::copy_n(q,D,result.begin()+i*D);
    }
    return result;
}

template<class T> void historic(const std::vector<T>& now,const fs::path& file) {
    const auto old=read_raw<T>(file);
    require(old.size()>=now.size() && !std::memcmp(old.data(),now.data(),now.size()*sizeof(T)),"E226 packet prefix parity");
}

void benchmark(const json& c) {
    check_threads(c);
    const fs::path root=c.at("output_dir");
    fresh_dir(root);
    json binding;
    auto index=load_index(c,binding);
    auto& idx=*index;
    idx.acsg.set_flat_ip_batch4_enabled(true);
    Pools pools(c,idx.ntotal);
    Router router(c.at("router"),idx.d,idx.ntotal);
    const auto queries=select_queries(c);
    const size_t n=queries.size()/D;
    const auto L=c.at("dense_L").get<std::vector<int>>();
    require(n==3072 && L.size()==20 && L.front()==168 && L.back()==244 && c.at("K")==K,"frozen matrix");
    int ordinal=0;
    for (const int l:L) {
        const auto point=root/("K100_L"+std::to_string(l));
        fresh_dir(point);
        std::array<std::unique_ptr<Batch>,2> first;
        Batch warm(256,K),dest(n,K);
        int order=0;
        for (int rep=0;rep<2;++rep) for (int i=0;i<2;++i) {
            const int arm=(i+rep+ordinal)%2;
            check_threads(c);
            search(pools,idx,router,queries,warm,l,arm==1);
            const auto start=Clock::now();
            {
                Batch temporary(n,K);
                search(pools,idx,router,queries,temporary,l,arm==1);
                copy_packet(temporary,dest);
                asm volatile("" :: "g"(dest.ids.data()),"g"(temporary.ids.data()) : "memory");
            }
            const double wall=seconds(start);
            check_threads(c);
            validate(dest,idx.ntotal);
            const auto p=point/arms[arm];
            if (!rep) {
                first[arm]=std::make_unique<Batch>(dest);
                dest.save(p/"raw",false);
            } else all_same(dest,*first[arm]);
            json timing{{"method",arms[arm]},{"K",K},{"L",l},{"n",n},{"rep",rep},
                {"seconds",wall},{"qps",n/wall},{"order",++order},{"cpu",sched_getcpu()},
                {"threads",process_threads()},{"sha256",packet_sha(dest)}};
            fresh_json(p/("round"+std::to_string(rep)+".json"),timing);
            std::cout<<timing.dump()<<std::endl;
        }
        for (int arm=0;arm<2;++arm) {
            Batch verify(256,K);
            std::vector<uint8_t> work;
            search(pools,idx,router,queries,verify,l,arm==1,&work);
            require(std::equal(verify.ids.begin(),verify.ids.end(),first[arm]->ids.begin()) &&
                    !std::memcmp(verify.distances.data(),first[arm]->distances.data(),verify.distances.size()*4),"qualifying prefix parity");
            write_raw(point/arms[arm]/"work.i8",work);
        }
        ++ordinal;
    }
    const Matrix prior(c.at("historical_queries"));
    const auto q=prior.copy();
    const fs::path history=c.at("historical_output");
    int proven=0;
    for (const int l:{176,200,244}) {
        const auto point=history/("K100_L"+std::to_string(l));
        for (int arm=0;arm<2;++arm) {
            Batch verify(256,K);
            search(pools,idx,router,q,verify,l,arm==1);
            const auto path=point/arms[arm]/"raw";
            historic(verify.ids,path/"ids.i32");
            historic(verify.distances,path/"distances.f32");
            historic(verify.entries,path/"entry_ids.i32");
            historic(verify.profile_distances,path/"profile_distances.f32");
            ++proven;
        }
    }
    fresh_json(root/"complete.json",{{"status","PASS_E228_FORMAL"},{"points",ordinal*2},
        {"batches",ordinal*4},{"E226_prefix_parity_points",proven},{"public_GT_read",false},{"binding",binding}});
}
}

int main(int argc,char** argv) {
    try {
        e183::require(argc==2,"benchmark config.json");
        const auto c=e183::read_json(argv[1]);
        e183::require(!c.contains("test_gt")&&!c.contains("train_gt"),"GT excluded from native timing");
        e228::benchmark(c);
        return 0;
    } catch (const std::exception& error) {
        std::cerr<<"E228: "<<error.what()<<std::endl;
        return 1;
    }
}

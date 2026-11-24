#define main e206_embedded_main
#include "../../20261120_residual_budget_matched_table_v1/src/common.inc"
#undef main
#include "../../20261121_neighbor_residual_online_v1/src/residual.hpp"
#include <sys/resource.h>

namespace e237 {
using namespace e183;
using e216::IdSet;
constexpr int max_K=100,cap=192;
enum class Mode { b32, old64, more64, mixed64, cutoff, far40 };
constexpr std::array<const char*,5> arms{"B32","B64-old","More64","Mixed64","CutoffGate"};

std::array<int,3> row_limits(Mode mode,const float* profile) {
    if (mode!=Mode::far40) return {64,64,64};
    int far=0;
    for (int j=1;j<3;++j) if (profile[j]>=profile[far]) far=j;
    std::array<int,3> result{64,64,64};
    result[far]=40;
    return result;
}

struct Ledger {
    int exact=0;
    std::array<int32_t,cap> ids;
};

struct Bank {
    std::vector<int32_t> ids;
    std::vector<uint8_t> count;

    Bank()=default;
    Bank(const fs::path& p,const Posting& original,size_t nbase)
        :ids(read_raw<int32_t>(p/"B64.ids.i32")),count(read_raw<uint8_t>(p/"B64.counts.i8")) {
        require(original.b==32 && ids.size()==size_t(original.H)*64 && count.size()==original.H,"frozen table shape");
        for (size_t i=0;i<original.H;++i) {
            const auto* row=ids.data()+i*64;
            require(count[i]>=original.counts[i] && count[i]<=64 &&
                    std::equal(original.targets.begin()+i*32,original.targets.begin()+i*32+original.counts[i],row),
                    "B64 preserves ordered B32 prefix");
            std::set<int32_t> seen;
            for (int j=0;j<count[i];++j)
                require(row[j]>=0 && size_t(row[j])<nbase && seen.insert(row[j]).second,"valid B64 row");
        }
    }
};

class Pools {
    Posting original;
    Bank wide, more, mixed;
public:
    Pools(const json& c,size_t nbase):original(c.at("table"),nbase),
        wide(fs::path(c.at("pool_dir")),original,nbase) {
        if (c.contains("more_pool")) more=Bank(fs::path(c.at("more_pool")),original,nbase);
        if (c.contains("mixed_pool")) mixed=Bank(fs::path(c.at("mixed_pool")),original,nbase);
    }

    void complete_full_b32(const std::array<int32_t,3>& route,faiss::DistanceComputer& dc,
                           faiss::idx_t* ids,float* distances,int k) {
        const int count=fast_plan(original,route,ids,k);
        if (count<0) throw std::runtime_error("B32 missing row");
        if (count) e216::score_merge(original,dc,k,count,ids,distances);
    }

    int select(Mode mode,const std::array<int32_t,3>& route,const float* profile,
               const faiss::idx_t* main,int k,Ledger& r) {
        if (mode==Mode::b32) {
            r.exact=fast_plan(original,route,main,k);
            if (r.exact<0) throw std::runtime_error("B32 missing row");
            std::copy_n(original.candidate.begin(),r.exact,r.ids.begin());
            return r.exact;
        }
        IdSet<512> seen;
        for (int i=0;i<k;++i) seen.add(main[i]);
        const auto limits=row_limits(mode,profile);
        const auto& bank=mode==Mode::more64?more:mode==Mode::mixed64?mixed:wide;
        for (int j=0;j<3;++j) {
            const int slot=original.lookup(route[j],nullptr);
            if (slot<0) throw std::runtime_error("B64 missing row");
            const int n=std::min(limits[j],int(bank.count[slot]));
            for (int i=0;i<n;++i) {
                const auto id=bank.ids[size_t(slot)*64+i];
                if (seen.has(id)) continue;
                seen.add(id);
                r.ids[r.exact++]=id;
            }
        }
        return r.exact;
    }

    void score(const Ledger& work,faiss::DistanceComputer& dc,faiss::idx_t* ids,float* d,int k,bool audit) {
        using Record=Posting::Record;
        if (!work.exact) return;
        std::vector<Record> reference;
        if (audit) {
            std::set<faiss::idx_t> unique(ids,ids+k);
            for (int j=0;j<k;++j) reference.push_back({ids[j],d[j],uint32_t(j),false});
            for (int j=0;j<work.exact;++j) {
                require(unique.insert(work.ids[j]).second,"all scored IDs distinct and outside main");
                reference.push_back({work.ids[j],dc(work.ids[j]),uint32_t(k+j),false});
            }
            std::sort(reference.begin(),reference.end(),Posting::better);
        }
        if (work.exact<=96) {
            std::copy_n(work.ids.begin(),work.exact,original.candidate.begin());
            e216::score_merge(original,dc,k,work.exact,ids,d);
        } else {
            std::array<Record,max_K> heap;
            const auto end=heap.begin()+k;
            for (int j=0;j<k;++j) heap[j]={ids[j],d[j],uint32_t(j),false};
            std::make_heap(heap.begin(),end,Posting::better);
            auto add=[&](int pos,float value) {
                if (!std::isfinite(value)) throw std::runtime_error("non-finite original score");
                if (value>=heap.front().distance) return;
                std::pop_heap(heap.begin(),end,Posting::better);
                heap[k-1]={work.ids[pos],value,uint32_t(k+pos),false};
                std::push_heap(heap.begin(),end,Posting::better);
            };
            int pos=0;
            for (;pos+3<work.exact;pos+=4) {
                const auto* m=work.ids.data()+pos;
                float v[4];
                dc.distances_batch_4(m[0],m[1],m[2],m[3],v[0],v[1],v[2],v[3]);
                for (int j=0;j<4;++j) add(pos+j,v[j]);
            }
            for (;pos<work.exact;++pos) add(pos,dc(work.ids[pos]));
            std::sort(heap.begin(),end,Posting::better);
            for (int i=0;i<k;++i) {ids[i]=heap[i].id;d[i]=heap[i].distance;}
        }
        if (audit)
            for (int i=0;i<k;++i)
                require(ids[i]==reference[i].id && equal_float(d[i],reference[i].distance),"native scalar ranking parity");
    }
};

std::array<int32_t,3> route_at(const Batch& b,size_t i) {
    return {b.entries[i*3],b.entries[i*3+1],b.entries[i*3+2]};
}

void search(Pools& pools,acsg::IndexACSGFlat& idx,Router& router,const std::vector<float>& q,
            Batch& b,int l,Mode mode,double threshold,std::vector<uint8_t>* work=nullptr) {
    const int k=b.k, d=idx.d;
    idx.acsg.search_L=l;
    std::vector<std::vector<acsg::EnterPoint>> entries(b.n);
    for (size_t i=0;i<b.n;++i) {
        const auto route=router.route(q.data()+i*d);
        for (int j=0;j<3;++j) {
            b.entries[i*3+j]=route.ids[j];
            b.profile_distances[i*3+j]=route.distances[j];
            entries[i].emplace_back(route.ids[j],1.f);
        }
    }
    faiss::VisitedTable visited(idx.ntotal);
    auto dc=std::unique_ptr<faiss::DistanceComputer>(acsg::storage_distance_computer(idx.storage));
    std::vector<acsg::Neighbor> scratch;
    std::array<faiss::idx_t,max_K> ids;
    for (size_t i=0;i<b.n;++i) {
        const auto* row=q.data()+i*d;
        dc->set_query(row);
        visited.advance();
        auto* distances=b.distances.data()+i*k;
        idx.acsg.search_new(*dc,k,ids.data(),distances,visited,2,entries[i],&scratch);
        const auto route=route_at(b,i);
        const auto* profile=b.profile_distances.data()+i*3;
        const Mode effective=mode!=Mode::cutoff?mode:(distances[99]>=threshold?Mode::old64:Mode::far40);
        if (mode==Mode::b32 && !work) {
            pools.complete_full_b32(route,*dc,ids.data(),distances,k);
        } else {
            Ledger plan;
            const int count=pools.select(effective,route,profile,ids.data(),k,plan);
            if (work && mode!=Mode::b32) {
                Ledger prefix;
                pools.select(Mode::b32,route,profile,ids.data(),k,prefix);
                for (int j=0;j<prefix.exact;++j)
                    require(std::find(plan.ids.begin(),plan.ids.begin()+count,prefix.ids[j])!=plan.ids.begin()+count,
                            "per-query subset retains original B32 candidates");
                if (mode==Mode::cutoff) {
                    Ledger full;
                    pools.select(Mode::old64,route,profile,ids.data(),k,full);
                    for (int j=0;j<count;++j)
                        require(std::find(full.ids.begin(),full.ids.begin()+full.exact,plan.ids[j])!=full.ids.begin()+full.exact,
                                "quota is a subset of its full ordered bank");
                }
            }
            pools.score(plan,*dc,ids.data(),distances,k,work!=nullptr);
            if (work) work->push_back(count);
        }
        std::copy_n(ids.begin(),k,b.ids.begin()+i*k);
    }
}

std::vector<float> select_queries(const json& c) {
    const Matrix input(c.at("queries"));
    const auto numbers=read_raw<int32_t>(c.at("rows").get<std::string>());
    require(numbers.size()==3072 && std::is_sorted(numbers.begin(),numbers.end()) &&
            std::adjacent_find(numbers.begin(),numbers.end())==numbers.end(),"fixed distinct holdout physical rows");
    std::vector<float> result(numbers.size()*input.d);
    for (size_t i=0;i<numbers.size();++i) {
        require(numbers[i]>=0 && size_t(numbers[i])<input.n,"sealed public holdout bounds");
        const auto* q=input.row(numbers[i]);
        require(std::all_of(q,q+input.d,[](float x){return std::isfinite(x);}),"finite selected queries");
        std::copy_n(q,input.d,result.begin()+i*input.d);
    }
    return result;
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
    const auto threshold=read_json(fs::path(c.at("cutoff_model"))).at("threshold").get<double>();
    const size_t n=queries.size()/idx.d;
    require(n==3072 && c.at("queries").at("d")==idx.d,"frozen formal shape");
    int ordinal=0,points=0;
    const int k=100;
    for (const int l:c.at("grid").get<std::vector<int>>()) {
        require(l>=k,"true K and L");
        const auto point=root/("K"+std::to_string(k)+"_L"+std::to_string(l));
        fresh_dir(point);
        const int modes=arms.size();
        std::array<std::unique_ptr<Batch>,arms.size()> first;
        Batch warm(256,k),dest(n,k);
        int order=0;
        for (int rep=0;rep<2;++rep) for (int i=0;i<modes;++i) {
            const int arm=(ordinal+(rep?modes-1-i:i))%modes;
            check_threads(c);
            search(pools,idx,router,queries,warm,l,static_cast<Mode>(arm),threshold);
            const auto start=Clock::now();
            {
                Batch temporary(n,k);
                search(pools,idx,router,queries,temporary,l,static_cast<Mode>(arm),threshold);
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
            json timing{{"method",arms[arm]},{"K",k},{"L",l},{"n",n},{"rep",rep},
                {"seconds",wall},{"qps",n/wall},{"order",++order},{"cpu",sched_getcpu()},
                {"threads",process_threads()},{"sha256",packet_sha(dest)}};
            fresh_json(p/("round"+std::to_string(rep)+".json"),timing);
            std::cout<<timing.dump()<<std::endl;
        }
        for (int arm=0;arm<modes;++arm) {
            Batch verify(256,k);
            std::vector<uint8_t> work;
            search(pools,idx,router,queries,verify,l,static_cast<Mode>(arm),threshold,&work);
            require(std::equal(verify.ids.begin(),verify.ids.end(),first[arm]->ids.begin()) &&
                    !std::memcmp(verify.distances.data(),first[arm]->distances.data(),verify.distances.size()*4),"qualifying prefix parity");
            write_raw(point/arms[arm]/"work.i8",work);
        }
        ++ordinal;
        points+=modes;
    }
    struct rusage usage{};
    require(getrusage(RUSAGE_SELF,&usage)==0 && usage.ru_maxrss>0,"native peak resident receipt");
    fresh_json(root/"complete.json",{{"status","PASS_E237_FORMAL"},{"points",points},
        {"batches",points*2},{"qualified_queries",points*256},{"peak_rss_kib",usage.ru_maxrss},
        {"public_GT_read",false},{"binding",binding}});
}
}

int main(int argc,char** argv) {
    try {
        e183::require(argc==2,"benchmark config.json");
        const auto c=e183::read_json(argv[1]);
        e183::require(!c.contains("test_gt")&&!c.contains("train_gt"),"GT excluded from native timing");
        e237::benchmark(c);
        return 0;
    } catch (const std::exception& error) {
        std::cerr<<"E237: "<<error.what()<<std::endl;
        return 1;
    }
}

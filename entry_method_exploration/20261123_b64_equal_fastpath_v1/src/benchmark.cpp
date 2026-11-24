#define main e206_embedded_main
#include "../../20261120_residual_budget_matched_table_v1/src/common.inc"
#undef main
#include "../../20261121_neighbor_residual_online_v1/src/residual.hpp"
#include <sys/resource.h>

namespace e244 {
using namespace e183;
using e216::IdSet;
constexpr int max_K=100,cap=192;
using Limits=std::array<int,3>;
enum class Mode { b32, old64, visited64, budget40, visited_budget40, mixed64, visited_mixed64 };
constexpr std::array<const char*,7> arms{"B32","B64-old","Visited64","Budget40","VisitedBudget40","Mixed64","VisitedMixed64"};
constexpr std::array<Limits,6> actions{Limits{32,32,32},Limits{48,48,36},Limits{56,56,40},
    Limits{64,64,40},Limits{64,64,52},Limits{64,64,64}};

bool reuses_visits(Mode m) {
    return m==Mode::visited64 || m==Mode::visited_budget40 || m==Mode::visited_mixed64;
}

bool uses_policy(Mode m) { return m==Mode::budget40 || m==Mode::visited_budget40; }

class Policy {
    enum Feature { cutoff, cutoff_minus_far, head_spread };
    Feature feature;
    std::vector<double> cuts;
    std::vector<int> levels;
public:
    explicit Policy(const json& j)
        :cuts(j.at("thresholds").get<std::vector<double>>()),levels(j.at("levels").get<std::vector<int>>()) {
        const auto kind=j.at("feature").get<std::string>();
        require(kind=="cutoff" || kind=="cutoff_minus_far" || kind=="head_spread","known policy score");
        feature=kind=="cutoff"?cutoff:kind=="cutoff_minus_far"?cutoff_minus_far:head_spread;
        require(cuts.size()<=11 && levels.size()==cuts.size()+1 && std::is_sorted(cuts.begin(),cuts.end()) &&
                std::is_sorted(levels.begin(),levels.end()),"bounded monotone policy");
        for (const auto v:levels) require(v>=0 && v<int(actions.size()),"rank budget choice");
    }

    Limits choose(const float* p,const float* d) const {
        double x=d[99];
        if (feature==cutoff_minus_far) x-=std::max({p[0],p[1],p[2]});
        if (feature==head_spread) x-=d[0];
        const auto level=levels[std::upper_bound(cuts.begin(),cuts.end(),x)-cuts.begin()];
        return actions[level];
    }
};

Limits route_order(const Limits& limits,const float* profile) {
    if (limits[0]==limits[2]) return limits;
    std::array<int,3> rank{0,1,2};
    std::sort(rank.begin(),rank.end(),[&](int i,int j) {
        return profile[i]!=profile[j]?profile[i]<profile[j]:i<j;
    });
    Limits ordered;
    for (int i=0;i<3;++i) ordered[rank[i]]=limits[i];
    return ordered;
}

class Seen512 {
    std::array<int32_t,512> slots;
public:
    Seen512() { slots.fill(-1); }
    bool insert(int32_t v) {
        unsigned pos=(uint32_t(v)*2654435761u)&511u;
        while (slots[pos]!=-1 && slots[pos]!=v) pos=(pos+1)&511u;
        if (slots[pos]==v) return false;
        slots[pos]=v;
        return true;
    }
};

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
    Bank wide, mixed;
public:
    Pools(const json& c,size_t nbase):original(c.at("table"),nbase),
        wide(fs::path(c.at("pool_dir")),original,nbase),mixed(fs::path(c.at("mixed_pool")),original,nbase) {}

    void complete_full_b32(const std::array<int32_t,3>& route,faiss::DistanceComputer& dc,
                           faiss::idx_t* ids,float* distances,int k) {
        const int count=fast_plan(original,route,ids,k);
        if (count<0) throw std::runtime_error("B32 missing row");
        if (count) e216::score_merge(original,dc,k,count,ids,distances);
    }

    int select(Mode mode,const std::array<int32_t,3>& route,const float* profile,
               const faiss::idx_t* main,int k,Ledger& r,
               const Limits& ordered,const faiss::VisitedTable* marks=nullptr) {
        if (mode==Mode::b32) {
            r.exact=fast_plan(original,route,main,k);
            if (r.exact<0) throw std::runtime_error("B32 missing row");
            std::copy_n(original.candidate.begin(),r.exact,r.ids.begin());
            return r.exact;
        }
        const auto limits=route_order(ordered,profile);
        const auto& bank=(mode==Mode::mixed64 || mode==Mode::visited_mixed64)?mixed:wide;
        if (marks) {
            Seen512 seen;
            for (int j=0;j<3;++j) {
                const int slot=original.lookup(route[j],nullptr);
                if (slot<0) throw std::runtime_error("B64 missing row");
                const int n=std::min(limits[j],int(bank.count[slot]));
                for (int i=0;i<n;++i) {
                    const auto id=bank.ids[size_t(slot)*64+i];
                    if (!marks->get(id) && seen.insert(id)) r.ids[r.exact++]=id;
                }
            }
            return r.exact;
        }
        IdSet<512> seen;
        for (int i=0;i<k;++i) seen.add(main[i]);
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
            Batch& b,int l,Mode mode,const Policy& policy,std::vector<uint8_t>* work=nullptr) {
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
        const Limits caps=uses_policy(mode)?policy.choose(profile,distances):actions.back();
        const auto* marks=reuses_visits(mode)?&visited:nullptr;
        if (mode==Mode::b32 && !work) {
            pools.complete_full_b32(route,*dc,ids.data(),distances,k);
        } else {
            Ledger plan;
            pools.select(mode,route,profile,ids.data(),k,plan,caps,marks);
            if (marks && work) {
                Ledger baseline;
                pools.select(mode,route,profile,ids.data(),k,baseline,caps);
                const float cutoff=distances[k-1];
                int skipped=0;
                for (int j=0;j<baseline.exact;++j) if (marks->get(baseline.ids[j])) {
                    require((*dc)(baseline.ids[j])>=cutoff,"visited score cannot beat main cutoff");
                    ++skipped;
                }
                require(baseline.exact-skipped==plan.exact,"visited filter accounts for all skipped candidates");
                auto expected=ids;
                std::array<float,max_K> d;
                std::copy_n(distances,k,d.begin());
                pools.score(baseline,*dc,expected.data(),d.data(),k,true);
                pools.score(plan,*dc,ids.data(),distances,k,true);
                require(std::equal(expected.begin(),expected.begin()+k,ids.begin()) &&
                        !std::memcmp(d.data(),distances,k*sizeof(float)),"visited preserves exact output");
            } else {
                pools.score(plan,*dc,ids.data(),distances,k,work!=nullptr);
            }
            if (work) work->push_back(plan.exact);
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
    const Policy policy(read_json(fs::path(c.at("model"))).at("Budget40"));
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
            search(pools,idx,router,queries,warm,l,static_cast<Mode>(arm),policy);
            const auto start=Clock::now();
            {
                Batch temporary(n,k);
                search(pools,idx,router,queries,temporary,l,static_cast<Mode>(arm),policy);
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
            search(pools,idx,router,queries,verify,l,static_cast<Mode>(arm),policy,&work);
            require(std::equal(verify.ids.begin(),verify.ids.end(),first[arm]->ids.begin()) &&
                    !std::memcmp(verify.distances.data(),first[arm]->distances.data(),verify.distances.size()*4),"qualifying prefix parity");
            write_raw(point/arms[arm]/"work.i8",work);
        }
        ++ordinal;
        points+=modes;
    }
    struct rusage usage{};
    require(getrusage(RUSAGE_SELF,&usage)==0 && usage.ru_maxrss>0,"native peak resident receipt");
    fresh_json(root/"complete.json",{{"status","PASS_E244_FORMAL"},{"points",points},
        {"batches",points*2},{"qualified_queries",points*256},{"peak_rss_kib",usage.ru_maxrss},
        {"public_GT_read",false},{"binding",binding}});
}
}

int main(int argc,char** argv) {
    try {
        e183::require(argc==2,"benchmark config.json");
        const auto c=e183::read_json(argv[1]);
        e183::require(!c.contains("test_gt")&&!c.contains("train_gt"),"GT excluded from native timing");
        e244::benchmark(c);
        return 0;
    } catch (const std::exception& error) {
        std::cerr<<"E244: "<<error.what()<<std::endl;
        return 1;
    }
}

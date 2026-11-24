#define main e206_embedded_main
#include "../../20261120_residual_budget_matched_table_v1/src/common.inc"
#undef main
#include "../../20261121_neighbor_residual_online_v1/src/residual.hpp"
#include <sys/resource.h>

namespace e252 {
using namespace e183;
using e216::IdSet;
constexpr int max_K=100,cap=192;
enum class Mode { b32, mixed64, main_only };
constexpr std::array<const char*,2> arms{"B32","Mixed64"};

struct Ledger {
    int exact=0;
    std::array<int32_t,cap> ids;
};

struct Bank {
    std::vector<int32_t> ids;
    std::vector<uint8_t> counts;

    Bank()=default;
    Bank(const fs::path& path,const Posting& original,size_t nbase)
        :ids(read_raw<int32_t>(path/"B64.ids.i32")),counts(read_raw<uint8_t>(path/"B64.counts.i8")) {
        require(original.b==32 && ids.size()==size_t(original.H)*64 && counts.size()==original.H,"frozen table shape");
        for (size_t slot=0;slot<original.H;++slot) {
            const auto* row=ids.data()+slot*64;
            const auto start=original.targets.begin()+slot*32;
            require(counts[slot]>=original.counts[slot] && counts[slot]<=64 &&
                    std::equal(start,start+original.counts[slot],row),"B64 preserves ordered B32 prefix");
            std::set<int32_t> seen;
            for (int j=0;j<counts[slot];++j)
                require(row[j]>=0 && size_t(row[j])<nbase && seen.insert(row[j]).second,"valid B64 row");
        }
    }
};

class Pools {
    Posting original;
    Bank mixed_bank;
public:
    Pools(const json& c,size_t nbase)
        :original(c.at("table"),nbase) {
        if (c.contains("mixed_pool")) mixed_bank=Bank(fs::path(c.at("mixed_pool")),original,nbase);
    }

    void complete_full_b32(const std::array<int32_t,3>& route,faiss::DistanceComputer& dc,
                           const acsg::Graph<int32_t>& graph,const faiss::VisitedTable& visited,
                           faiss::idx_t* ids,float* distances,int k) {
        fast_apply(dc,graph,visited,route,k,ids,distances,original);
    }

    int select(Mode mode,const std::array<int32_t,3>& route,const faiss::idx_t* main,int k,Ledger& r) {
        if (mode==Mode::b32) {
            r.exact=fast_plan(original,route,main,k);
            if (r.exact<0) throw std::runtime_error("B32 missing row");
            std::copy_n(original.candidate.begin(),r.exact,r.ids.begin());
            return r.exact;
        }
        const Bank& bank=mixed_bank;
        IdSet<512> seen;
        for (int i=0;i<k;++i) seen.add(main[i]);
        for (const auto label:route) {
            const int slot=original.lookup(label,nullptr);
            if (slot<0) throw std::runtime_error("B64 missing row");
            for (int i=0;i<bank.counts[slot];++i) {
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
        if (k==1) {
            for (int j=0;j<work.exact;++j) {
                const float value=dc(work.ids[j]);
                if (!std::isfinite(value)) throw std::runtime_error("non-finite native L2");
                if (value<d[0]) {ids[0]=work.ids[j];d[0]=value;}
            }
        } else {
            std::array<Record,max_K> heap;
            const auto end=heap.begin()+k;
            for (int j=0;j<k;++j) heap[j]={ids[j],d[j],uint32_t(j),false};
            std::make_heap(heap.begin(),end,Posting::better);
            for (int j=0;j<work.exact;++j) {
                const float value=dc(work.ids[j]);
                if (!std::isfinite(value)) throw std::runtime_error("non-finite native L2");
                if (value>=heap.front().distance) continue;
                std::pop_heap(heap.begin(),end,Posting::better);
                heap[k-1]={work.ids[j],value,uint32_t(k+j),false};
                std::push_heap(heap.begin(),end,Posting::better);
            }
            std::sort(heap.begin(),end,Posting::better);
            for (int j=0;j<k;++j) {ids[j]=heap[j].id;d[j]=heap[j].distance;}
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
            Batch& b,int l,Mode mode,std::vector<uint8_t>* work=nullptr) {
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
        if (mode==Mode::main_only) {
            std::copy_n(ids.begin(),k,b.ids.begin()+i*k);
            continue;
        }
        const auto route=route_at(b,i);
        if (mode==Mode::b32 && !work) {
            pools.complete_full_b32(route,*dc,*idx.acsg.final_graph,visited,ids.data(),distances,k);
        } else {
            Ledger plan;
            const int count=pools.select(mode,route,ids.data(),k,plan);
            if (work && mode!=Mode::b32) {
                Ledger prefix;
                pools.select(Mode::b32,route,ids.data(),k,prefix);
                for (int j=0;j<prefix.exact;++j)
                    require(std::find(plan.ids.begin(),plan.ids.begin()+count,prefix.ids[j])!=plan.ids.begin()+count,
                            "per-query B64 candidate superset");
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
    require(numbers.size()==c.at("eval_n") && numbers.size()>=256 && std::is_sorted(numbers.begin(),numbers.end()) &&
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

void teacher(const json& c) {
    check_threads(c);
    const fs::path root=c.at("output_dir");
    fresh_dir(root);
    json binding;
    auto index=load_index(c,binding);
    auto& idx=*index;
    require(idx.metric_type==faiss::METRIC_L2,"squared L2 only");
    idx.acsg.set_flat_ip_batch4_enabled(false);
    Pools pools(c,idx.ntotal);
    Router router(c.at("router"),idx.d,idx.ntotal);
    const auto q=read_raw<float>(fs::path(c.at("train_queries")));
    const size_t n=c.at("train_n");
    require(n>0 && q.size()==n*idx.d,"frozen teacher query shape");
    int points=0;
    for (const int l:c.at("grid").get<std::vector<int>>()) {
        check_threads(c);
        Batch out(n,100);
        const auto start=Clock::now();
        search(pools,idx,router,q,out,l,Mode::main_only);
        validate(out,idx.ntotal);
        out.save(root/("K100_L"+std::to_string(l))/"raw",false);
        std::cout<<json{{"L",l},{"n",n},{"seconds",seconds(start)},{"threads",process_threads()}}.dump()<<std::endl;
        ++points;
    }
    fresh_json(root/"complete.json",{{"status","PASS_E252_TRAIN_MAIN"},{"n",n},{"points",points},
        {"threads",process_threads()},{"GT_read",false},{"binding",binding}});
}

void benchmark(const json& c) {
    check_threads(c);
    const fs::path root=c.at("output_dir");
    fresh_dir(root);
    json binding;
    auto index=load_index(c,binding);
    auto& idx=*index;
    require(idx.metric_type==faiss::METRIC_L2,"squared L2 only");
    idx.acsg.set_flat_ip_batch4_enabled(false);
    Pools pools(c,idx.ntotal);
    Router router(c.at("router"),idx.d,idx.ntotal);
    const auto queries=select_queries(c);
    const size_t n=queries.size()/idx.d;
    require(n==c.at("eval_n") && c.at("queries").at("d")==idx.d,"frozen formal shape");
    constexpr int methods=arms.size();
    int ordinal=0;
    for (const int k:{1,100}) for (const int l:c.at("grids").at(std::to_string(k)).get<std::vector<int>>()) {
        require(l>=k,"true K and L");
        const auto point=root/("K"+std::to_string(k)+"_L"+std::to_string(l));
        fresh_dir(point);
        std::array<std::unique_ptr<Batch>,methods> first;
        Batch warm(256,k),dest(n,k);
        int order=0;
        for (int rep=0;rep<2;++rep) for (int i=0;i<methods;++i) {
            const int arm=(ordinal+(rep?methods-1-i:i))%methods;
            check_threads(c);
            search(pools,idx,router,queries,warm,l,static_cast<Mode>(arm));
            const auto start=Clock::now();
            {
                Batch temporary(n,k);
                search(pools,idx,router,queries,temporary,l,static_cast<Mode>(arm));
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
        for (int arm=0;arm<methods;++arm) {
            Batch verify(256,k);
            std::vector<uint8_t> work;
            search(pools,idx,router,queries,verify,l,static_cast<Mode>(arm),&work);
            require(std::equal(verify.ids.begin(),verify.ids.end(),first[arm]->ids.begin()) &&
                    !std::memcmp(verify.distances.data(),first[arm]->distances.data(),verify.distances.size()*4),"qualifying prefix parity");
            write_raw(point/arms[arm]/"work.i8",work);
        }
        ++ordinal;
    }
    struct rusage usage{};
    require(getrusage(RUSAGE_SELF,&usage)==0 && usage.ru_maxrss>0,"native peak resident receipt");
    fresh_json(root/"complete.json",{{"status","PASS_E252_FORMAL"},{"points",ordinal*methods},
        {"batches",ordinal*methods*2},{"qualified_queries",ordinal*methods*256},{"peak_rss_kib",usage.ru_maxrss},
        {"public_GT_read",false},{"binding",binding}});
}
}

int main(int argc,char** argv) {
    try {
        e183::require(argc==2,"benchmark config.json");
        const auto c=e183::read_json(argv[1]);
        e183::require(!c.contains("test_gt")&&!c.contains("train_gt"),"GT excluded from native timing");
        if (c.value("build_teacher",false)) e252::teacher(c);
        else e252::benchmark(c);
        return 0;
    } catch (const std::exception& error) {
        std::cerr<<"E252: "<<error.what()<<std::endl;
        return 1;
    }
}

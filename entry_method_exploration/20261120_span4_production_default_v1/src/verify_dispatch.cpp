#define main e206_embedded_main
#include "../../20261120_residual_budget_matched_table_v1/src/common.inc"
#undef main

#include <faiss/IndexFlat.h>
#include <thread>

namespace {
thread_local unsigned ip_batches=0;
thread_local unsigned l2_batches=0;
}

#define IP_BATCH_SYMBOL _ZN5faiss26fvec_inner_product_batch_4EPKfS1_S1_S1_S1_mRfS2_S2_S2_
#define L2_BATCH_SYMBOL _ZN5faiss18fvec_L2sqr_batch_4EPKfS1_S1_S1_S1_mRfS2_S2_S2_
#define CONCAT_IMPL(a,b) a ## b
#define CONCAT(a,b) CONCAT_IMPL(a,b)

#define WRAP_BATCH4(symbol, counter) \
extern "C" void CONCAT(__real_,symbol)(const float*,const float*,const float*, \
    const float*,const float*,size_t,float&,float&,float&,float&); \
extern "C" void CONCAT(__wrap_,symbol)(const float* q,const float* a,const float* b, \
    const float* c,const float* d,size_t n,float& w,float& x,float& y,float& z) { \
    ++counter; \
    CONCAT(__real_,symbol)(q,a,b,c,d,n,w,x,y,z); \
}

WRAP_BATCH4(IP_BATCH_SYMBOL,ip_batches)
WRAP_BATCH4(L2_BATCH_SYMBOL,l2_batches)

namespace {
using namespace e183;
constexpr int count=21, dim=17, k=8, budget=11;

struct Result {
    std::array<faiss::idx_t,k> ids{};
    std::array<float,k> distances{};
    std::vector<acsg::Neighbor> pool;
};
void same_result(const Result& a,const Result& b) {
    require(a.ids==b.ids&&!std::memcmp(a.distances.data(),b.distances.data(),sizeof(a.distances)),
            "identical returned ID and score bits");
    require(a.pool.size()==b.pool.size(),"identical scratch size");
    for (size_t j=0;j<a.pool.size();++j) {
        require(a.pool[j].id==b.pool[j].id&&a.pool[j].flag==b.pool[j].flag&&
            equal_float(a.pool[j].distance,b.pool[j].distance),"identical scratch fields");
    }
}
void search(acsg::ACSG& index,faiss::DistanceComputer& dc,const float* q,
            faiss::VisitedTable& visited,const std::vector<acsg::EnterPoint>& entries,
            Result& result,int mode=2,bool trace=false) {
    dc.set_query(q);
    if (trace) {
        acsg::SearchTrace diagnostic;
        index.search_new_traced(dc,k,result.ids.data(),result.distances.data(),visited,mode,
                                entries,diagnostic,nullptr,0,&result.pool);
        require(diagnostic.distance_evaluations>0,"scalar trace counts are live");
    } else {
        index.search_new(dc,k,result.ids.data(),result.distances.data(),visited,mode,
                         entries,&result.pool);
    }
}

struct CustomDistance : faiss::DistanceComputer {
    // Candidate IDs have tied scalar scores. This type must never run a batch.
    void set_query(const float*) override {}
    float operator()(faiss::idx_t id) override {return float(id%4);}
    float symmetric_dis(faiss::idx_t a,faiss::idx_t b) override {return float(a+b);}
    void distances_batch_4(faiss::idx_t,faiss::idx_t,faiss::idx_t,faiss::idx_t,
                           float&,float&,float&,float&) override {
        throw std::runtime_error("custom distance incorrectly batched");
    }
};

void fixture(bool candidate) {
    std::vector<float> base(count*dim);
    std::array<float,dim> query{};
    for (int j=0;j<dim;++j) query[j]=(j%5-2)*0.125f;
    for (int i=0;i<count;++i)
        for (int j=0;j<dim;++j) base[i*dim+j]=float((i%8*43+j*31)%32-16)*0.25f;
    for (int j=0;j<dim;++j) base[(count-1)*dim+j]=100.f*query[j];
    faiss::IndexFlat flat_ip(dim,faiss::METRIC_INNER_PRODUCT);
    faiss::IndexFlatIP flat_ip_alias(dim);
    faiss::IndexFlat flat_l2(dim,faiss::METRIC_L2);
    faiss::IndexFlatL2 flat_l2_cached(dim);
    for (faiss::Index* storage:std::array<faiss::Index*,4>{&flat_ip,&flat_ip_alias,&flat_l2,&flat_l2_cached})
        storage->add(count,base.data());
    flat_l2_cached.sync_l2norms();

    auto graph=std::make_shared<acsg::Graph<int32_t>>(count,10);
    std::fill_n(graph->data,count*graph->K,-1);
    const int neighbors[]={3,-1,4,4,5,count,6,7,8,-1};
    std::copy(std::begin(neighbors),std::end(neighbors),graph->data);
    for (int i=1;i<count;++i) {
        graph->at(i,0)=(i+3)%(count-1);
        graph->at(i,1)=(i+8)%(count-1);
    }
    const std::vector<acsg::EnterPoint> three{{0,1},{1,1},{2,1}};
    const std::vector<acsg::EnterPoint> repeated{{0,1},{0,1},{2,1},{3,1}};
    acsg::ACSG active,scalar;
    for (auto* index:{&active,&scalar}) {
        index->ntotal=count;
        index->is_built=true;
        index->search_L=budget;
        index->final_graph=graph;
        index->top_enterpoints=three;
    }
    if (candidate) active.set_flat_ip_batch4_enabled(true);
    scalar.set_flat_ip_batch4_enabled(false);

    auto pair=[&](faiss::DistanceComputer& a,faiss::DistanceComputer& b,const auto& entries,
                  bool expect_batch,int mode,bool traced,int reps,bool previsit=false) {
        faiss::VisitedTable av(count),bv(count);
        Result ax,bx;
        unsigned active_calls=0;
        for (int i=0;i<reps;++i) {
            av.advance();
            bv.advance();
            if (previsit) for (const auto& entry:entries) {
                av.set(entry.id);
                bv.set(entry.id);
            }
            ip_batches=l2_batches=0;
            search(active,a,query.data(),av,entries,ax,mode,traced);
            active_calls+=ip_batches;
            require(l2_batches==0,"L2 fallback");
            ip_batches=0;
            search(scalar,b,query.data(),bv,entries,bx,mode,traced);
            require(ip_batches==0&&l2_batches==0,"scalar route");
            same_result(ax,bx);
            require(av.visno==bv.visno&&av.visited==bv.visited,"identical visited table");
        }
        require((active_calls>0)==expect_batch,"expected native IP batch dispatch");
        return ax;
    };

    std::unique_ptr<faiss::DistanceComputer> a(acsg::storage_distance_computer(&flat_ip));
    std::unique_ptr<faiss::DistanceComputer> b(acsg::storage_distance_computer(&flat_ip));
    pair(*a,*b,three,true,2,false,260);  // Includes a visited generation rollover.
    pair(*a,*b,repeated,true,2,false,1);
    pair(*a,*b,std::vector<acsg::EnterPoint>{},false,2,false,1);
    pair(*a,*b,three,false,2,false,1,true);
    pair(*a,*b,three,false,1,false,1);
    pair(*a,*b,three,false,0,false,1);
    pair(*a,*b,three,false,2,true,1);

    // Change an existing row from no live tail to an edge at the last slot.
    const auto plus=pair(*a,*b,three,true,2,false,1);
    graph->at(0,graph->K-1)=20;
    const auto edited=pair(*a,*b,three,true,2,false,1);
    require(plus.ids!=edited.ids,"edge edit changes the answer in this fixture");

    for (faiss::Index* storage:std::array<faiss::Index*,3>{&flat_ip_alias,&flat_l2,&flat_l2_cached}) {
        a.reset(acsg::storage_distance_computer(storage));
        b.reset(acsg::storage_distance_computer(storage));
        pair(*a,*b,three,storage==&flat_ip_alias,2,false,1);
    }
    CustomDistance x,y;
    pair(x,y,three,false,2,false,1);

    std::exception_ptr errors[4];
    std::vector<std::thread> workers;
    for (int slot=0;slot<4;++slot) workers.emplace_back([&,slot] {
        try {
            std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(&flat_ip));
            faiss::VisitedTable vt(count);
            Result out;
            for (int round=0;round<300;++round) {
                vt.advance();
                ip_batches=0;
                search(active,*dc,query.data(),vt,three,out);
                require(ip_batches>0,"thread ran the native batch");
                same_result(out,edited);
            }
        } catch (...) {
            errors[slot]=std::current_exception();
        }
    });
    for (auto& worker:workers) worker.join();
    for (auto& error:errors) if (error) std::rethrow_exception(error);
    std::cout<<"fixture passed: native dispatch, candidate pool, tie order, visit rollover, "
        <<"fallback, edge edit and 1,200 shared-index concurrent queries\n";
}

void release(const json& c) {
    check_threads(c);
    json binding;
    auto index=load_index(c,binding);
    auto queries=Matrix(c.at("queries")).copy();
    Router router(c.at("router"),index->d,index->ntotal);
    Posting table(c.at("table"),index->ntotal);
    const bool expects_batch=c.at("metric_id")==0;
    const auto qualification=expects_batch
        ? read_json(fs::path(c.at("output_dir"))/"qualification.json") : json::array();
    std::vector<Batch> enabled;
    std::vector<unsigned> batch_counts;
    for (int K:{1,100}) {
        for (bool residual:{false,true}) {
            const std::string name=residual?"B32":"GT10";
            Method method{name,residual?"POST":"GT10",router.name,"",&router,residual?&table:nullptr};
            ip_batches=l2_batches=0;
            enabled.emplace_back(256,K);
            run_batch(*index,queries,200,method,enabled.back());
            require((ip_batches>0)==expects_batch&&l2_batches==0,"untouched release dispatch");
            batch_counts.push_back(ip_batches);
        }
    }
    index->acsg.set_flat_ip_batch4_enabled(false);
    size_t state=0;
    for (int K:{1,100}) {
        for (bool residual:{false,true}) {
            const std::string name=residual?"B32":"GT10";
            Method method{name,residual?"POST":"GT10",router.name,"",&router,residual?&table:nullptr};
            Batch scalar(256,K);
            ip_batches=l2_batches=0;
            run_batch(*index,queries,200,method,scalar);
            require(ip_batches==0&&l2_batches==0,"release rollback");
            all_same(enabled[state],scalar);
            const auto hash=packet_sha(enabled[state]);
            const auto expected=std::find_if(qualification.begin(),qualification.end(),[&](const auto& p) {
                return p["method"]==name&&p["K"]==K&&p["L"]==200;
            });
            require(!expects_batch||(expected!=qualification.end()&&(*expected)["sha256"]==hash),
                    "release output matches E211 timed binary qualification");
            std::cout<<c.at("dataset")<<" "<<name<<" K"<<K<<" L200 batches="<<batch_counts[state]
                     <<" "<<hash<<"\n";
            ++state;
        }
    }
}
}

int main(int argc,char** argv) {
    try {
        require(argc==2,"verify_dispatch --candidate|--default|config.json");
        const std::string value=argv[1];
        if (value=="--candidate"||value=="--default") fixture(value=="--candidate");
        else release(read_json(value));
    } catch (const std::exception& e) {
        std::cerr<<e.what()<<"\n";
        return 1;
    }
}

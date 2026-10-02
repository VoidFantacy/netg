#include "search_core.hpp"
#include <cblas.h>

struct FitModel {
    std::vector<double> q;
    std::vector<int16_t> labels;
    std::vector<int64_t> sources;
    std::vector<int32_t> rows;
};

struct Selector {
    int d;
    std::array<FitModel,4> fit;
    std::vector<double> unit, similarity;
    std::vector<int> order;
    explicit Selector(const fs::path& path, int dimension):d(dimension),unit(d),similarity(3072),order(3072) {
        for(int f=0;f<4;++f) {
            std::string suffix=std::to_string(f);
            auto& m=fit[f];
            m.q=read_raw<double>(path/("fit"+suffix+".f64"));
            m.labels=read_raw<int16_t>(path/("labels"+suffix+".i16"));
            m.sources=read_raw<int64_t>(path/("sources"+suffix+".i64"));
            m.rows=read_raw<int32_t>(path/("rows"+suffix+".i32"));
            require(m.q.size()==3072ULL*d&&m.labels.size()==3072*14&&m.sources.size()==3072&&m.rows.size()==3072,"fit dimensions");
        }
    }
    int predict(const float* q,int fold,int k) {
        double norm=0;
        for(int j=0;j<d;++j)norm+=double(q[j])*q[j];
        norm=std::sqrt(norm);
        for(int j=0;j<d;++j)unit[j]=double(q[j])/norm;
        const auto& m=fit[fold];
        cblas_dgemv(CblasRowMajor,CblasNoTrans,3072,d,1.,m.q.data(),d,unit.data(),1,0.,similarity.data(),1);
        std::iota(order.begin(),order.end(),0);
        auto less=[&](int a,int b){return similarity[a]!=similarity[b]?similarity[a]>similarity[b]:m.sources[a]<m.sources[b];};
        std::partial_sort(order.begin(),order.begin()+55,order.end(),less);
        std::array<int,7> sums{};
        for(int j=0;j<55;++j)for(int a=0;a<7;++a)sums[a]+=m.labels[order[j]*14+a*2+k];
        return std::max_element(sums.begin(),sums.end())-sums.begin();
    }
};

struct Routes {
    int d,h;
    std::vector<int32_t> ids;
    std::array<std::vector<float>,7> banks;
    std::array<int,7> counts{};
    std::unique_ptr<Router> original;
    hnswlib::InnerProductSpace space;
    std::vector<std::pair<float,int32_t>> scores;
    Routes(const json& c):d(c["native"]["dimension"]),h(c["native"]["H"]),space(d),scores(h) {
        ids=read_raw<int32_t>(c["native"]["hub_ids"].get<std::string>());
        require(ids.size()==size_t(h),"hub count");
        for(int a=0;a<7;++a) {
            const auto& m=c["actions"][a];
            counts[a]=m["entry_count"];
            if(a==0)original=std::make_unique<Router>(m,d,m["graph"].get<std::string>());
            else {
                banks[a]=read_raw<float>(m["W"].get<std::string>());
                require(banks[a].size()==size_t(h*d),"profile shape");
            }
        }
        original->counting(false);
    }
    std::array<int32_t,3> route(const float* q,int action) {
        if(action==0)return original->route(q);
        auto fn=space.get_dist_func();auto param=space.get_dist_func_param();
        for(int j=0;j<h;++j)scores[j]={fn(q,banks[action].data()+j*d,param),ids[j]};
        int count=counts[action];
        std::partial_sort(scores.begin(),scores.begin()+count,scores.end());
        std::array<int32_t,3> result{-1,-1,-1};
        for(int j=0;j<count;++j)result[j]=scores[j].second;
        std::sort(result.begin(),result.begin()+count);
        return result;
    }
};

int main(int argc,char** argv) {try {
    threads();require(argc==3,"benchmark config output");
    json c=read_json(argv[1]);fs::path out=argv[2];
    require(!fs::exists(out),"preserve previous output");fs::create_directories(out);
    write_json(out/"config.json",c);
    auto jobstart=Clock::now();const auto& native=c["native"];
    const size_t n=4096,d=native["dimension"];fs::path model=c["model"].get<std::string>();
    auto q=read_raw<float>(native["queries"].get<std::string>());
    auto folds=read_raw<int32_t>(model/"folds.i32");
    auto expected_actions=read_raw<int32_t>(model/"expected_actions.i32");
    auto expected_neighbors=read_raw<int32_t>(model/"expected_neighbors.i32");
    auto default_entries=read_raw<int32_t>(model/"default_entries.i32");
    require(q.size()==n*d&&folds.size()==n&&expected_actions.size()==n*2&&expected_neighbors.size()==n*55,"input dimensions");
    Selector selector(model,d);Routes routes(c);
    for(int k=0;k<2;++k) {
        int K=k==0?1:100;
        auto expected=read_raw<int32_t>(model/("expected_entries_k"+std::to_string(K)+".i32"));
        for(size_t i=0;i<n;++i) {
            require(folds[i]>=0&&folds[i]<4,"fold bounds");
            int action=selector.predict(q.data()+i*d,folds[i],k);
            require(action==expected_actions[i*2+k],"frozen action mismatch");
            std::vector<int32_t> actual(55), ref(expected_neighbors.begin()+i*55,expected_neighbors.begin()+(i+1)*55);
            for(int j=0;j<55;++j)actual[j]=selector.fit[folds[i]].rows[selector.order[j]];
            std::sort(actual.begin(),actual.end());std::sort(ref.begin(),ref.end());
            require(actual==ref,"frozen neighbor set mismatch");
            auto e=routes.route(q.data()+i*d,action);
            require(!memcmp(e.data(),expected.data()+i*3,12),"frozen selected entry mismatch");
            auto b=routes.route(q.data()+i*d,0);
            require(!memcmp(b.data(),default_entries.data()+i*3,12),"default entry mismatch");
        }
    }
    threads();write_json(out/"selector_parity.json",{{"status","PASS"},{"query_K_checks",8192},{"all_neighbors_actions_entries",true}});
    std::cout<<"SELECTOR_PARITY_PASS"<<std::endl;
    auto idx=load_nsg(native["index"]);require(idx->d==d&&idx->ntotal==native["base_n"]&&idx->metric_type==0,"fixed graph identity");
    Fvecs base(native["base"].get<std::string>());std::vector<float> reconstructed(d);
    for(size_t j=0;j<16;++j){size_t i=j*(base.n/16);idx->storage->reconstruct(i,reconstructed.data());require(!memcmp(reconstructed.data(),base.row(i),d*4),"base sample identity");}
    auto spans=make_spans(*idx->acsg.final_graph,idx->ntotal);ResearchKernel kernel(*idx->acsg.final_graph,spans,idx->ntotal);
    std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx->storage)), legacy(acsg::storage_distance_computer(idx->storage));
    faiss::VisitedTable vt(idx->ntotal), lvt(idx->ntotal);
    std::vector<acsg::EnterPoint> ep;ep.reserve(3);
    std::vector<acsg::Neighbor> scratch;scratch.reserve(1501);
    std::array<faiss::idx_t,100> answer,other;std::array<float,100> od;
    uint64_t calls=0;
    auto run=[&](bool learned,int K,int L,Batch& b) {
        for(size_t i=0;i<b.n;++i) {
            const float* query=q.data()+i*d;
            int action=learned?selector.predict(query,folds[i],K==1?0:1):0;
            auto entries=routes.route(query,action);
            std::copy(entries.begin(),entries.end(),b.entries.begin()+i*3);
            ep.clear();for(int id:entries)if(id>=0)ep.emplace_back(id,1);
            vt.advance();dc->set_query(query);
            kernel.search<true,false,true>(*dc,vt,ep,L,K,answer.data(),b.dist.data()+i*K);
            for(int j=0;j<K;++j)b.ids[i*K+j]=answer[j];
        }
        calls+=b.n;
    };
    int ordinal=0;json progress=json::array();
    for(int K:{1,100})for(int L:c["grid"][std::to_string(K)]) {
        require(L>=K&&L<=1250,"budget bounds");idx->acsg.search_L=L;
        std::array<std::unique_ptr<Batch>,2> reference;
        std::array<std::vector<double>,2> timing;
        for(int method=0;method<2;++method) {
            Batch smoke(16,K);run(method,K,L,smoke);
            for(size_t i=0;i<16;++i) {
                ep.clear();for(int j=0;j<3;++j){int id=smoke.entries[i*3+j];if(id>=0)ep.emplace_back(id,1);}
                lvt.advance();legacy->set_query(q.data()+i*d);
                idx->acsg.search_new(*legacy,K,other.data(),od.data(),lvt,2,ep,&scratch);++calls;
                for(int j=0;j<K;++j)require(other[j]==smoke.ids[i*K+j],"legacy ID parity");
                require(!memcmp(od.data(),smoke.dist.data()+i*K,K*4),"legacy distance parity");
            }
        }
        for(int rep=0;rep<3;++rep)for(int offset=0;offset<2;++offset) {
            int method=(ordinal+rep+offset)%2;std::string name=method?"TargetKNN":"DefaultGT10";
            if(rep==0){Batch warm(128,K);run(method,K,L,warm);}
            Batch batch(n,K);threads();
            auto start=Clock::now();run(method,K,L,batch);double elapsed=seconds(start);
            threads();timing[method].push_back(elapsed);
            auto point=out/(name+"_k"+std::to_string(K)+"_L"+std::to_string(L));
            if(rep==0){reference[method]=std::make_unique<Batch>(batch);save_batch(point,batch,false);}
            else same(*reference[method],batch);
            json row={{"method",name},{"K",K},{"L",L},{"repeat",rep},{"seconds",elapsed},{"qps",n/elapsed},{"threads",1}};
            progress.push_back(row);write_json(out/"timings.json",progress);std::cout<<row.dump()<<std::endl;
            require(seconds(jobstart)<1800,"job deadline");resources(out);
        }
        for(int method=0;method<2;++method) {
            std::string name=method?"TargetKNN":"DefaultGT10";
            auto point=out/(name+"_k"+std::to_string(K)+"_L"+std::to_string(L));
            if(method==0) {
                auto ref=fs::path(native["reference"].get<std::string>())/("k"+std::to_string(K))/(native["reference_method"].get<std::string>()+"_L"+std::to_string(L));
                auto ids=read_raw<int32_t>(ref/"ids.i32");auto dist=read_raw<float>(ref/"distances.f32");
                require(ids==reference[method]->ids&&!memcmp(dist.data(),reference[method]->dist.data(),dist.size()*4),"E105 default return parity");
            }
            write_json(point/"complete.json",{{"status","PASS"},{"K",K},{"L",L},{"n",n},{"method",name},{"seconds",timing[method]},
                {"threads",1},{"cpu",15},{"repeated_output_bit_parity",true},{"linked_E99_smoke",true},{"complete_query_wall",true},{"formal_evaluation",false}});
        }
        ++ordinal;
    }
    require(calls==149376,"exact search call accounting");threads();struct rusage usage;getrusage(RUSAGE_SELF,&usage);
    write_json(out/"complete.json",{{"status","PASS"},{"calls",calls},{"wall_rounds",36},{"points",12},{"threads",1},{"cpu",15},
        {"seconds",seconds(jobstart)},{"maxrss_kib",usage.ru_maxrss},{"complete_query_wall",true},{"formal_evaluation",false}});
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

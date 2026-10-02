#define main legacy_diagnostic_main
#include "legacy_reference.cpp"
#undef main

struct Decision {
    std::array<int32_t,3> ids{-1,-1,-1};
    std::array<int32_t,3> labels{-1,-1,-1};
    uint32_t ndc=0;
    std::array<int32_t,7> candidate_slots{-1,-1,-1,-1,-1,-1,-1};
    std::array<float,7> candidate_distances{};
};

// E66: seven unique slot labels, at most three slots per real hub.
void unique_three(Decision& result, std::vector<std::pair<float,size_t>> candidates,
                  const std::vector<int32_t>& mapping) {
    require(candidates.size()==7,"multi-profile requires exactly seven candidates");
    std::sort(candidates.begin(),candidates.end());
    std::set<size_t> slots;size_t selected=0;
    for(size_t j=0;j<7;++j) {
        const auto [distance,slot]=candidates[j];
        require(std::isfinite(distance) && slot<mapping.size() && slots.insert(slot).second,"invalid candidate slot/distance");
        result.candidate_slots[j]=int32_t(slot);result.candidate_distances[j]=distance;
        bool seen=false;for(size_t t=0;t<selected;++t)if(result.ids[t]==mapping[slot])seen=true;
        if(!seen && selected<3){result.ids[selected]=mapping[slot];result.labels[selected]=int32_t(slot);++selected;}
    }
    require(selected==3,"seven slots did not provide three unique real hubs");
}

class Policy {
    size_t dim,h,k;bool counted,exact,slot_labels,heap_order,canonical_order,multi_profile;
    int32_t fixed_entry;
    std::vector<float> w;
    std::vector<int32_t> mapping,tie_ids;
    std::unique_ptr<hnswlib::SpaceInterface<float>> space;
    std::unique_ptr<hnswlib::HierarchicalNSW<float>> graph;
    mutable hnswlib::InnerProductSpace exact_space;
public:
    Policy(const json& c,const fs::path& index_file,bool counting,bool load):
        dim(c.at("dim")),h(c.value("hub_count",size_t(0))),k(c.value("k",1)),counted(counting),
        exact(c.value("exact",false)),slot_labels(c.value("slot_labels",false)),heap_order(c.value("legacy_heap_order",false)),canonical_order(c.value("canonical_entry_order",false)),
        multi_profile(c.value("multi_profile",false)),
        fixed_entry(c.value("fixed_entry",int32_t(-1))),
        w(c.contains("fixed_entry") ? std::vector<float>{} : read_raw<float>(c.at("W"))),
        mapping(c.contains("fixed_entry") ? std::vector<int32_t>{} : read_raw<int32_t>(c.at("mapping"))),
        tie_ids(c.contains("fixed_entry") ? std::vector<int32_t>{} : read_raw<int32_t>(c.at("tie_ids"))),exact_space(dim) {
        if(c.contains("fixed_entry")) { require(fixed_entry>=0 && k==1,"invalid fixed NSG entry"); return; }
        require(w.size()==h*dim && mapping.size()==h && tie_ids.size()==h,"policy shape mismatch");
        require(k>=1 && k<=3,"invalid policy k");finite_matrix(w,"policy vectors");
        if(!slot_labels)require(std::set<int32_t>(mapping.begin(),mapping.end()).size()==h,"Fast real labels must be unique");
        require(std::set<int32_t>(tie_ids.begin(),tie_ids.end()).size()==h,"tie IDs must be unique");
        if(multi_profile) {
            require(slot_labels && !exact && !heap_order && canonical_order && k==3 && h>=9,"invalid multi-profile configuration");
            std::unordered_map<int32_t,size_t> multiplicity;
            for(size_t j=0;j<h;++j){require(mapping[j]>=0 && tie_ids[j]==int32_t(j),"multi-profile slot mapping/tie invalid");++multiplicity[mapping[j]];}
            require(multiplicity.size()==c.at("unique_hub_count").get<size_t>() && h==3*multiplicity.size(),"physical/unique profile count mismatch");
            for(const auto& item:multiplicity)require(item.second==3,"each real hub needs exactly three slots");
        }
        if(exact)return;
        if(counted)space=std::make_unique<CountSpace>(dim);else space=std::make_unique<hnswlib::InnerProductSpace>(dim);
        if(load)graph=std::make_unique<hnswlib::HierarchicalNSW<float>>(space.get(),c.value("reference_graph",false)?c.at("graph_file").get<std::string>():index_file.string(),false,h);
        else if(c.contains("graph_file")) {
            graph=std::make_unique<hnswlib::HierarchicalNSW<float>>(space.get(),c.at("graph_file").get<std::string>(),false,h);
            for(size_t j=0;j<h;++j) {
                require(graph->getExternalLabel(j)==(slot_labels?j:size_t(mapping[j])),"serialized graph mapping mismatch");
                require(std::memcmp(graph->getDataByInternalId(j),w.data()+j*dim,dim*sizeof(float))==0,"serialized graph vector mismatch");
            }
            if(!c.value("reference_graph",false))graph->saveIndex(index_file.string());
        }
        else {
            graph=std::make_unique<hnswlib::HierarchicalNSW<float>>(space.get(),h,16,200,c.value("hnsw_seed",c.at("seed").get<size_t>()));
            for(size_t j=0;j<h;++j)graph->addPoint(w.data()+j*dim,slot_labels ? j : size_t(mapping[j]));
            graph->saveIndex(index_file.string());
        }
        require(graph->cur_element_count==h,"duplicate external labels destroyed slot capacity");
        for(size_t j=0;j<h;++j) {
            require(graph->getExternalLabel(j)==(slot_labels?j:size_t(mapping[j])),"loaded graph label mismatch");
            require(std::memcmp(graph->getDataByInternalId(j),w.data()+j*dim,dim*sizeof(float))==0,"loaded graph vector mismatch");
        }
        const int ef=c.value("ef_search",10);require(ef==10 || ef==30,"E70 ef must be 10 or 30");
        graph->setEf(ef);
    }
    size_t entry_count()const{return k;}
    Decision route(const float* q)const {
        Decision result;
        auto canonicalize=[&](){
            if(canonical_order)for(size_t i=0;i<k;++i)for(size_t j=i+1;j<k;++j)
                if(result.ids[j]<result.ids[i]){std::swap(result.ids[i],result.ids[j]);std::swap(result.labels[i],result.labels[j]);}
        };
        if(fixed_entry>=0) { result.ids[0]=fixed_entry;result.labels[0]=fixed_entry;return result; }
        if(exact) {
            auto fn=exact_space.get_dist_func();void* param=exact_space.get_dist_func_param();
            std::vector<std::pair<float,size_t>> scores(h);
            for(size_t j=0;j<h;++j)scores[j]={fn(q,w.data()+j*dim,param),j};
            std::partial_sort(scores.begin(),scores.begin()+k,scores.end(),[&](const auto& a,const auto& b){
                return a.first<b.first || (a.first==b.first && tie_ids[a.second]<tie_ids[b.second]);});
            for(size_t j=0;j<k;++j){result.ids[j]=mapping[scores[j].second];result.labels[j]=int32_t(scores[j].second);}
            result.ndc=counted?h:0;canonicalize();return result;
        }
        uint64_t count=0;route_counter=counted?&count:nullptr;
        auto heap=graph->searchKnn(q,multi_profile?7:k);route_counter=nullptr;
        if(multi_profile) {
            std::vector<std::pair<float,size_t>> candidates;candidates.reserve(7);
            while(!heap.empty()){candidates.push_back(heap.top());heap.pop();}
            unique_three(result,std::move(candidates),mapping);result.ndc=uint32_t(count);canonicalize();return result;
        }
        for(size_t position=0;position<k;++position){size_t j=heap_order?position:k-1-position;int32_t label=heap.top().second;result.labels[j]=label;result.ids[j]=slot_labels?mapping[label]:label;heap.pop();}
        result.ndc=uint32_t(count);canonicalize();return result;
    }
};

struct NativeWork {
    std::unique_ptr<faiss::DistanceComputer> dc;CountDC* counted=nullptr;
    faiss::VisitedTable visited;std::vector<acsg::Neighbor> retset;std::vector<acsg::EnterPoint> entries;
    NativeWork(acsg::IndexACSGFlat& index,bool count):visited(index.ntotal) {
        if(count){counted=new CountDC(acsg::storage_distance_computer(index.storage));dc.reset(counted);}
        else dc.reset(acsg::storage_distance_computer(index.storage));
        retset.reserve(129);entries.reserve(3);
    }
    Search search(acsg::IndexACSGFlat& index,const float* q,const Decision& route,size_t k) {
        entries.clear();for(size_t j=0;j<k;++j)entries.emplace_back(route.ids[j],1.0);
        dc->set_query(q);visited.advance();if(counted)counted->count=0;
        Search result;std::array<faiss::idx_t,K> ids;
        index.acsg.search_new(*dc,K,ids.data(),result.distances.data(),visited,2,entries,&retset);
        for(size_t j=0;j<K;++j)result.ids[j]=int32_t(ids[j]);
        if(counted) {
            require(counted->count<=UINT32_MAX && counted->count>=k,"invalid graph count");result.ndc=counted->count;
            for(size_t j=0;j<k;++j)require(counted->first_ids[j]==route.ids[j],"entry injection mismatch");
        }
        return result;
    }
};

struct BatchOutput {std::vector<Decision> routes;std::vector<Search> searches;explicit BatchOutput(size_t n):routes(n),searches(n){}};
using Workers=std::vector<std::unique_ptr<NativeWork>>;
void batch(acsg::IndexACSGFlat& index,const Policy& policy,const std::vector<float>& q,size_t d,Workers& workers,BatchOutput& out) {
    const size_t n=out.routes.size();
    #pragma omp parallel for schedule(static)
    for(size_t i=0;i<n;++i) {
        out.routes[i]=policy.route(q.data()+i*d);
        out.searches[i]=workers[omp_get_thread_num()]->search(index,q.data()+i*d,out.routes[i],policy.entry_count());
    }
}
void route_batch(const Policy& policy,const std::vector<float>& q,size_t d,BatchOutput& out) {
    #pragma omp parallel for schedule(static)
    for(size_t i=0;i<out.routes.size();++i)out.routes[i]=policy.route(q.data()+i*d);
}
void graph_batch(acsg::IndexACSGFlat& index,const Policy& policy,const std::vector<float>& q,size_t d,Workers& workers,BatchOutput& out) {
    #pragma omp parallel for schedule(static)
    for(size_t i=0;i<out.routes.size();++i)out.searches[i]=workers[omp_get_thread_num()]->search(index,q.data()+i*d,out.routes[i],policy.entry_count());
}
void compare(const BatchOutput& a,const BatchOutput& b) {
    for(size_t i=0;i<a.routes.size();++i) {
        require(a.routes[i].ids==b.routes[i].ids && a.routes[i].labels==b.routes[i].labels,"plain/count route mismatch");
        require(a.routes[i].candidate_slots==b.routes[i].candidate_slots &&
            std::memcmp(a.routes[i].candidate_distances.data(),b.routes[i].candidate_distances.data(),7*sizeof(float))==0,"plain/count seven-slot mismatch");
        require(a.searches[i].ids==b.searches[i].ids && a.searches[i].distances==b.searches[i].distances,"plain/count kernel mismatch");
    }
}

json metrics(const BatchOutput& out,const std::vector<int64_t>& gt,size_t gtk,const fs::path& dest) {
    size_t n=out.routes.size();std::vector<uint8_t> hits(n);std::vector<uint16_t> masks(n);
    std::vector<uint32_t> route_ndc(n),graph_ndc(n);std::vector<int32_t> ids(n*K),entry_ids(n*3),labels(n*3);
    uint64_t sum=0,failed=0,rndc=0,gndc=0;
    for(size_t i=0;i<n;++i) {
        masks[i]=hitmask(out.searches[i].ids,gt.data()+i*gtk);hits[i]=__builtin_popcount(unsigned(masks[i]));
        sum+=hits[i];failed+=hits[i]==0;route_ndc[i]=out.routes[i].ndc;graph_ndc[i]=out.searches[i].ndc;
        rndc+=route_ndc[i];gndc+=graph_ndc[i];
        std::copy(out.searches[i].ids.begin(),out.searches[i].ids.end(),ids.begin()+i*K);
        std::copy(out.routes[i].ids.begin(),out.routes[i].ids.end(),entry_ids.begin()+i*3);
        std::copy(out.routes[i].labels.begin(),out.routes[i].labels.end(),labels.begin()+i*3);
    }
    fs::create_directories(dest);write_raw(dest/"hits.u8",hits);write_raw(dest/"hitmask.u16",masks);
    write_raw(dest/"route_ndc.u32",route_ndc);write_raw(dest/"graph_ndc.u32",graph_ndc);write_raw(dest/"ids.i32",ids);
    write_raw(dest/"entry_ids.i32",entry_ids);write_raw(dest/"router_labels.i32",labels);
    return {{"queries",n},{"total_hits",sum},{"recall_at_10",double(sum)/(n*K)},{"failed_queries",failed},{"failure_rate",double(failed)/n},
            {"mean_route_ndc",double(rndc)/n},{"mean_graph_ndc",double(gndc)/n},{"mean_total_ndc",double(rndc+gndc)/n}};
}

int benchmark(const json& c,const fs::path& out) {
    require(!fs::exists(out),"refuse existing output");fs::create_directories(out);write_json(out/"config.json",c);
    size_t d=c.at("dim"),n=c.at("num_queries"),gtk=c.at("gt_k");int threads=c.value("threads",16);
    require(threads>=1 && threads<=16 && gtk>=10,"invalid threads/GT");omp_set_num_threads(threads);
    auto q=read_raw<float>(c.at("queries_file"));auto gt=read_raw<int64_t>(c.at("gt_file"));auto rows=read_raw<int64_t>(c.at("row_ids"));
    require(q.size()==n*d && gt.size()==n*gtk && rows.size()==n,"input shape mismatch");finite_matrix(q,"queries");write_raw(out/"row_ids.i64",rows);
    auto index=std::make_unique<acsg::IndexACSGFlat>();index->loadACPG(c.at("index_path").get<std::string>().c_str());
    std::vector<float>().swap(index->acsg.pheromone);std::vector<float>().swap(index->acsg.weight);
    require(index->d==int(d) && index->metric_type==faiss::METRIC_INNER_PRODUCT,"wrong frozen index");
    Workers plain,counted;for(int t=0;t<threads;++t){plain.push_back(std::make_unique<NativeWork>(*index,false));counted.push_back(std::make_unique<NativeWork>(*index,true));}
    json result={{"status","RUNNING"},{"dataset",c.at("dataset")},{"split",c.at("split")},{"queries",n},{"threads",threads},{"methods",json::array()}};
    const auto methods=c.at("methods").get<std::vector<json>>();size_t m=methods.size();require(m>0,"no methods");
    std::vector<std::unique_ptr<Policy>> policies;std::vector<BatchOutput> counted_results;
    BatchOutput plain_result(n);
    for(size_t j=0;j<m;++j) {
        json mc=methods[j];mc["dim"]=d;std::string name=mc.at("name");require(name.find('/')==std::string::npos,"unsafe name");
        int l=mc.at("L");require(l>=10 && l<=128,"invalid L");index->acsg.search_L=l;
        if(mc.value("family",std::string())=="nsg_medoid") {
            require(index->acsg.enterpoint>=0 && index->acsg.enterpoint<index->ntotal,"invalid frozen NSG enterpoint");
            mc["fixed_entry"]=index->acsg.enterpoint;mc["k"]=1;mc["hub_count"]=0;
        } else {
            auto mapping=read_raw<int32_t>(mc.at("mapping"));for(auto id:mapping)require(id>=0 && id<index->ntotal,"mapping outside base");
        }
        fs::path file=out/(name+".hnsw");auto p=std::make_unique<Policy>(mc,file,false,false);Policy count_policy(mc,file,true,true);
        counted_results.emplace_back(n);auto& measured=counted_results.back();
        batch(*index,count_policy,q,d,counted,measured);batch(*index,*p,q,d,plain,plain_result);compare(measured,plain_result);
        auto metric=metrics(measured,gt,gtk,out/name);metric["name"]=name;metric["L"]=l;metric["seed"]=mc.at("seed");metric["configuration"]=mc;metric["plain_count_parity_queries"]=n;
        metric["timings"]=json::array();result["methods"].push_back(metric);policies.push_back(std::move(p));
        std::cout<<json({{"stage","count_and_parity"},{"method",name},{"recall",metric["recall_at_10"]},{"failure",metric["failure_rate"]}}).dump()<<std::endl;
    }
    // No GT, checksums, counters, JSON or micro-index construction in these intervals.
    int repeats=c.value("timing_repeats",3);
    for(int rep=0;rep<repeats;++rep) {
        size_t offset=(c.value("order_offset",0)+rep*std::max(size_t(1),m/3))%m;
        for(size_t position=0;position<m;++position) {
            size_t j=(offset+position)%m;const auto& policy=*policies[j];index->acsg.search_L=methods[j].at("L");
            batch(*index,policy,q,d,plain,plain_result); // Full-batch warmup.
            auto t=Clock::now();batch(*index,policy,q,d,plain,plain_result);double wall=std::chrono::duration<double>(Clock::now()-t).count();
            compare(counted_results[j],plain_result);
            route_batch(policy,q,d,plain_result);t=Clock::now();route_batch(policy,q,d,plain_result);double route_wall=std::chrono::duration<double>(Clock::now()-t).count();
            graph_batch(*index,policy,q,d,plain,plain_result);t=Clock::now();graph_batch(*index,policy,q,d,plain,plain_result);double graph_wall=std::chrono::duration<double>(Clock::now()-t).count();
            compare(counted_results[j],plain_result);
            result["methods"][j]["timings"].push_back({{"repeat",rep},{"order_position",position},{"end_to_end_seconds",wall},{"qps",n/wall},{"route_only_seconds",route_wall},{"graph_only_seconds",graph_wall}});
        }
        write_json(out/"results.json",result);std::cout<<json({{"stage","timing_repeat_complete"},{"repeat",rep},{"methods",m}}).dump()<<std::endl;
    }
    result["status"]="COMPLETE";result["timing_contract"]="Independent plain full-batch wall includes routing/mapping/original kernel/output; excludes GT/hash/JSON/count/load/build; route-only and graph-only are separate diagnostics";
    write_json(out/"results.json",result);return 0;
}

#ifndef AB_BENCHMARK_LIBRARY
int main(int argc,char** argv) {
    try {require(argc==3,"Usage: benchmark config.json new_output");std::ifstream f(argv[1]);require(bool(f),"missing config");json c;f>>c;return benchmark(c,argv[2]);}
    catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}
}
#endif

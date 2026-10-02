#define main unused_common_main
#include "common/evaluate.cpp"
#undef main
#include "kernels.hpp"

// Count actual batch4 without replacing it by four scalar operations.
struct ActualBatchCount:CountDC{
    explicit ActualBatchCount(faiss::DistanceComputer* p):CountDC(p){}
    void distances_batch_4(faiss::idx_t a,faiss::idx_t b,faiss::idx_t c,faiss::idx_t d,float& x,float& y,float& z,float& w)override{
        for(auto id:{a,b,c,d}){if(count<3)first[count]=id;++count;}
        dc->distances_batch_4(a,b,c,d,x,y,z,w);
    }
};
template<class T> static json compare_raw(const std::vector<T>& actual,const fs::path& p){
    auto expected=read_raw<T>(p);require(actual.size()==expected.size(),"reference shape "+p.string());size_t diff=0,first=actual.size();
    for(size_t i=0;i<actual.size();++i)if(memcmp(&actual[i],&expected[i],sizeof(T))){++diff;first=std::min(first,i);}
    return {{"elements",actual.size()},{"different_elements",diff},{"first_difference",diff?json(first):json(nullptr)},{"reference",p.string()}};
}
int main(int argc,char**argv){try{
    require(argc==3,"compatibility config new-output");threads();auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"new output required");fs::create_directories(out);auto start=Clock::now();
    auto idx=load_nsg(c["index"]);size_t n=c["n"],d=idx->d;require(c["threads"]==1&&c["metric_id"]==idx->metric_type,"metric/threads");Fvecs fq(c["queries"]);require(fq.n==n&&fq.d==d,"query shape");std::vector<float>q(n*d);for(size_t i=0;i<n;++i)std::copy(fq.row(i),fq.row(i)+d,q.data()+i*d);
    std::map<std::string,std::unique_ptr<Router>> routers;std::vector<std::string> methods;
    for(auto m:c["methods"]){std::string name=m["name"];if(name=="HNSW")continue;methods.push_back(name);if(name!="NSG")routers[name]=std::make_unique<Router>(m,d,fs::path(c["reference_results"].get<std::string>())/"k100"/(name+".hnsw"));}
    auto spans=make_spans(*idx->acsg.final_graph,idx->ntotal);ResearchKernel kernel(*idx->acsg.final_graph,spans,idx->ntotal);ActualBatchCount dc(acsg::storage_distance_computer(idx->storage));faiss::VisitedTable vt(idx->ntotal);std::vector<acsg::EnterPoint> ep;ep.reserve(3);std::array<faiss::idx_t,100> ids;uint64_t calls=0;int failures=0;json records=json::array();
    for(auto point:c["points"]){int K=point["K"],L=point["L"];require((K==1||K==100)&&L>=K,"K/L");
        for(const auto& method:methods){threads();Router* router=routers.count(method)?routers[method].get():nullptr;if(router)router->counting(true);Batch b(n,K);
            for(size_t i=0;i<n;++i){auto query=q.data()+i*d;std::array<int32_t,3> entries{-1,-1,-1};size_t ne=1;if(router){entries=router->route(query);ne=3;}else entries[0]=idx->acsg.enterpoint;std::copy(entries.begin(),entries.end(),b.entries.begin()+i*3);ep.clear();for(size_t j=0;j<ne;++j)ep.emplace_back(entries[j],1);vt.advance();dc.set_query(query);kernel.search<true,false,true>(dc,vt,ep,L,K,ids.data(),b.dist.data()+i*K);for(int j=0;j<K;++j)b.ids[i*K+j]=ids[j];b.graph_ndc[i]=dc.count;b.route_ndc[i]=router?router->counter.n:0;++calls;}
            std::string key=method+"_K"+std::to_string(K)+"_L"+std::to_string(L);fs::path ref=fs::path(c["reference_e99"].get<std::string>())/(method+"__optimized_K"+std::to_string(K)+"_L"+std::to_string(L));
            json checks={{"ids",compare_raw(b.ids,ref/"ids.i32")},{"distance_bits",compare_raw(b.dist,ref/"distances.f32")},{"entries",compare_raw(b.entries,ref/"entry_ids.i32")},{"route_ndc",compare_raw(b.route_ndc,ref/"route_ndc.u64")},{"graph_ndc",compare_raw(b.graph_ndc,ref/"graph_ndc.u64")}};
            bool match=true;for(const auto& item:checks.items())match=match&&item.value()["different_elements"]==0;
            if(!match){++failures;save_batch(out/key,b,false);save_batch(out/key,b,true);}
            json record={{"dataset",c["dataset"]},{"method",method},{"K",K},{"L",L},{"queries",n},{"status",match?"PASS":"MISMATCH"},{"checks",checks},{"actual_batch4",true},{"search_calls_completed",calls}};records.push_back(record);write_json(out/"progress.json",records);std::cout<<record.dump()<<std::endl;
        }
    }
    struct rusage r;getrusage(RUSAGE_SELF,&r);require(r.ru_maxrss<64LL*1024*1024,"RSS cap");require(calls==16*n,"search accounting");write_json(out/"complete.json",{{"status",failures?"COMPLETE_WITH_MISMATCH":"PASS"},{"configurations",records.size()},{"mismatched_configurations",failures},{"search_calls",calls},{"seconds_including_load",seconds(start)},{"maxrss_kib",r.ru_maxrss},{"threads",process_threads()},{"cpu",15},{"new_formal_qps",0}});return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

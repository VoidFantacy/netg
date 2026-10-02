#define main unused_e99_main
#include "common/evaluate.cpp"
#undef main
#include "kernels.hpp"
#include <faiss/IndexNSG.h>

static void reference(const Batch& b,const fs::path& root,bool counts){
    require(b.ids==read_raw<int32_t>(root/"ids.i32"),"reference IDs "+root.string());
    auto d=read_raw<float>(root/"distances.f32");require(d.size()==b.dist.size()&&!memcmp(d.data(),b.dist.data(),d.size()*4),"reference distance bits "+root.string());
    require(b.entries==read_raw<int32_t>(root/"entry_ids.i32"),"reference entries "+root.string());
    if(counts){require(b.route_ndc==read_raw<uint64_t>(root/"route_ndc.u64"),"reference route NDC");require(b.graph_ndc==read_raw<uint64_t>(root/"graph_ndc.u64"),"reference graph NDC");}
}

int main(int argc,char**argv){try{
    require(argc==3,"compare config new-output");threads();auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"output must be new");fs::create_directories(out);write_json(out/"config.json",c);
    auto idx=load_nsg(c["index"]);size_t n=c["n"],d=idx->d;require(n==10000&&d==512&&idx->metric_type==0,"frozen WebVid");
    Fvecs fq(c["queries"]);require(fq.n==n&&fq.d==d,"query identity");std::vector<float>q(n*d);for(size_t i=0;i<n;++i)std::copy(fq.row(i),fq.row(i)+d,q.data()+i*d);
    Router router(c["soft"],d,c["router"].get<std::string>());auto space=make_space(0,d);CountParam hc{space->get_dist_func(),space->get_dist_func_param(),0};Fvecs base(c["base"]);auto full=load_topology(c["hnsw_topology"].get<std::string>(),base,space.get());Worker original(*idx);
    faiss::IndexNSG native(idx->storage,idx->acsg.final_graph->K);native.own_fields=false;native.ntotal=idx->ntotal;native.is_built=true;native.is_trained=true;native.nsg.ntotal=idx->ntotal;native.nsg.enterpoint=idx->acsg.enterpoint;native.nsg.is_built=true;
    native.nsg.final_graph=std::make_shared<faiss::nsg::Graph<int>>(idx->acsg.final_graph->data,idx->ntotal,idx->acsg.final_graph->K);
    require(native.nsg.final_graph->data==idx->acsg.final_graph->data&&native.storage==idx->storage,"same graph and storage address");
    auto ts=Clock::now();auto spans=make_spans(*idx->acsg.final_graph,idx->ntotal);double span_seconds=seconds(ts);ResearchKernel kernel(*idx->acsg.final_graph,spans,idx->ntotal);
    write_json(out/"layout.json",{{"span_build_seconds",span_seconds},{"span_bytes",spans.size()},{"same_graph_storage_memory",true},{"graph_n",idx->ntotal},{"graph_R",idx->acsg.final_graph->K},{"native_enterpoint",native.nsg.enterpoint},{"native_graph_own_fields",native.nsg.final_graph->own_fields},{"native_storage_owned",native.own_fields}});
    auto plain=std::unique_ptr<faiss::DistanceComputer>(acsg::storage_distance_computer(idx->storage));CountDC counter(acsg::storage_distance_computer(idx->storage));faiss::VisitedTable vt(idx->ntotal);std::vector<acsg::EnterPoint> ep;ep.reserve(3);std::array<faiss::idx_t,100> ids;std::vector<faiss::idx_t> native_ids(n*100);
    std::vector<std::string> names=c["variants"];json rounds=json::array();uint64_t calls=0;auto started=Clock::now();int point_index=0;
    for(auto point:c["points"]){int K=point["K"],L=point["L"];require((K==1||K==100)&&L>=K,"K/L");idx->acsg.search_L=native.nsg.search_L=L;full->setEf(L);
        auto key=[&](const std::string& v){return v+"_K"+std::to_string(K)+"_L"+std::to_string(L);};
        auto run=[&](const std::string& v,Batch& b,bool count){
            router.counting(count);
            if(v=="Faiss-native"){
                if(!count){native.search(n,q.data(),K,b.dist.data(),native_ids.data());for(size_t i=0;i<n*K;++i){b.ids[i]=native_ids[i];b.dist[i]=-b.dist[i];}}
                else for(size_t i=0;i<n;++i){vt.advance();counter.set_query(q.data()+i*d);native.nsg.search(counter,K,ids.data(),b.dist.data()+i*K,vt);for(int j=0;j<K;++j)b.ids[i*K+j]=ids[j];b.graph_ndc[i]=counter.count;}
                // Anchor metadata, not the full native initialization set.
                for(size_t i=0;i<n;++i)b.entries[i*3]=native.nsg.enterpoint;
            }else if(v=="NSG-current"||v=="GT10-current"||v=="HNSW"){
                full->fstdistfunc_=count?counted:space->get_dist_func();full->dist_func_param_=count?(void*)&hc:space->get_dist_func_param();
                original.run(v=="NSG-current"?"NSG":v=="HNSW"?"HNSW":"GT10-soft-t1",v=="GT10-current"?&router:nullptr,full.get(),hc,q,d,b,count);
            }else{
                auto fn=kernel_call(v);auto& dc=count?static_cast<faiss::DistanceComputer&>(counter):*plain;
                for(size_t i=0;i<n;++i){const float* query=q.data()+i*d;auto entries=router.route(query);std::copy(entries.begin(),entries.end(),b.entries.begin()+i*3);ep.clear();for(int id:entries)ep.emplace_back(id,1);vt.advance();dc.set_query(query);(kernel.*fn)(dc,vt,ep,L,K,ids.data(),b.dist.data()+i*K);for(int j=0;j<K;++j)b.ids[i*K+j]=ids[j];if(count){b.graph_ndc[i]=counter.count;b.route_ndc[i]=router.counter.n;}}
            }
            calls+=n;require(calls<=c["max_real_search_calls"].get<uint64_t>(),"query cap");
        };
        auto verify=[&](const std::string& v,const Batch& b,bool count){
            if(v=="Faiss-native"){
                for(size_t i=0;i<n;++i){std::set<int> unique;for(int j=0;j<K;++j){int id=b.ids[i*K+j];require(id>=0&&id<idx->ntotal&&unique.insert(id).second,"native invalid/duplicate output");require(std::isfinite(b.dist[i*K+j]),"native finite distance");if(j)require(b.dist[i*K+j]>=b.dist[i*K+j-1],"native sorted");}}
                reference(b,out/key(v),false);
            }else{
                std::string m=v=="HNSW"?"HNSW":v=="NSG-current"?"NSG":"GT10-soft-t1";
                reference(b,fs::path(c["reference_e99"].get<std::string>())/(m+(m=="HNSW"?"__reference":"__optimized")+"_K"+std::to_string(K)+"_L"+std::to_string(L)),count);
            }
        };
        std::map<std::string,std::vector<double>> times;
        auto ordered=names;std::rotate(ordered.begin(),ordered.begin()+point_index%ordered.size(),ordered.end());
        for(int rep=0;rep<3;++rep){auto order=ordered;if(rep%2)std::reverse(order.begin(),order.end());for(const auto& v:order){
            Batch b(n,K);
            if(rep==0){Batch warm(n,K);run(v,warm,false);if(v=="Faiss-native")save_batch(out/key(v),warm,false);verify(v,warm,false);}
            threads();auto t=Clock::now();run(v,b,false);double sec=seconds(t);verify(v,b,false);if(rep==0&&v!="Faiss-native")save_batch(out/key(v),b,false);times[v].push_back(sec);
            json row={{"variant",v},{"K",K},{"L",L},{"repeat",rep},{"seconds",sec},{"qps",n/sec},{"n",n},{"threads",process_threads()},{"cpu",15},{"search_calls_completed",calls}};rounds.push_back(row);write_json(out/"timing_progress.json",rounds);std::cout<<row.dump()<<std::endl;
        }}
        for(const auto& v:ordered){Batch b(n,K);run(v,b,true);verify(v,b,true);save_batch(out/key(v),b,true);write_json(out/key(v)/"complete.json",{{"status","PASS"},{"variant",v},{"K",K},{"L",L},{"n",n},{"seconds",times[v]},{"output_bits_and_ndc_verified",true},{"parity_reference",v=="Faiss-native"?"own native public API output":"E99"}});std::cout<<"COUNT_PASS "<<key(v)<<std::endl;}
        ++point_index;struct rusage r;getrusage(RUSAGE_SELF,&r);require(r.ru_maxrss<64LL*1024*1024,"RSS cap");write_json(out/"progress.json",{{"completed_points",point_index},{"search_calls",calls},{"seconds",seconds(started)}});
    }
    struct rusage r;getrusage(RUSAGE_SELF,&r);write_json(out/"complete.json",{{"status","PASS"},{"search_calls",calls},{"wall_rounds",rounds.size()},{"seconds_excluding_load",seconds(started)},{"maxrss_kib",r.ru_maxrss},{"threads",process_threads()},{"cpu",15},{"same_graph_and_storage",true}});return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

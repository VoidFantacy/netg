#define main unused_common_main
#include "common/evaluate.cpp"
#undef main
#include "kernels.hpp"
struct ForwardBatchCount:CountDC{
 explicit ForwardBatchCount(faiss::DistanceComputer* p):CountDC(p){}
 void distances_batch_4(faiss::idx_t a,faiss::idx_t b,faiss::idx_t c,faiss::idx_t d,float& x,float& y,float& z,float& w)override{
  for(auto id:{a,b,c,d}){if(count<3)first[count]=id;++count;}
  dc->distances_batch_4(a,b,c,d,x,y,z,w);
 }
};
int main(int argc,char**argv){try{
 require(argc==3,"actual_batch4_count config new-output");threads();auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"new output required");fs::create_directories(out);auto start=Clock::now();auto idx=load_nsg(c["index"]);size_t n=c["n"],d=idx->d;require(n==10000&&d==512&&idx->metric_type==0,"frozen WebVid");Fvecs fq(c["queries"]);require(fq.n==n&&fq.d==d,"query shape");std::vector<float>q(n*d);for(size_t i=0;i<n;++i)std::copy(fq.row(i),fq.row(i)+d,q.data()+i*d);
 Router router(c["soft"],d,c["router"].get<std::string>());router.counting(true);auto spans=make_spans(*idx->acsg.final_graph,idx->ntotal);ResearchKernel kernel(*idx->acsg.final_graph,spans,idx->ntotal);ForwardBatchCount dc(acsg::storage_distance_computer(idx->storage));faiss::VisitedTable vt(idx->ntotal);std::vector<acsg::EnterPoint> ep;ep.reserve(3);std::array<faiss::idx_t,100> ids;uint64_t calls=0;json records=json::array();
 for(auto pt:c["points"]){int K=pt["K"],L=pt["L"];for(std::string v:{"GT10-batch4","GT10-span-batch4"}){
  threads();Batch b(n,K);auto fn=kernel_call(v);
  for(size_t i=0;i<n;++i){auto query=q.data()+i*d;auto entries=router.route(query);std::copy(entries.begin(),entries.end(),b.entries.begin()+i*3);ep.clear();for(int id:entries)ep.emplace_back(id,1);vt.advance();dc.set_query(query);(kernel.*fn)(dc,vt,ep,L,K,ids.data(),b.dist.data()+i*K);for(int j=0;j<K;++j)b.ids[i*K+j]=ids[j];b.graph_ndc[i]=dc.count;b.route_ndc[i]=router.counter.n;++calls;}
  fs::path ref=fs::path(c["reference_e99"].get<std::string>())/("GT10-soft-t1__optimized_K"+std::to_string(K)+"_L"+std::to_string(L));auto rd=read_raw<float>(ref/"distances.f32");bool pass=b.ids==read_raw<int32_t>(ref/"ids.i32")&&b.dist.size()==rd.size()&&!memcmp(b.dist.data(),rd.data(),rd.size()*4)&&b.entries==read_raw<int32_t>(ref/"entry_ids.i32")&&b.route_ndc==read_raw<uint64_t>(ref/"route_ndc.u64")&&b.graph_ndc==read_raw<uint64_t>(ref/"graph_ndc.u64");
  if(!pass){auto fail=out/(v+"_K"+std::to_string(K)+"_L"+std::to_string(L));save_batch(fail,b,false);save_batch(fail,b,true);}
  json rec={{"variant",v},{"K",K},{"L",L},{"queries",n},{"actual_batch4_forwarded",true},{"status",pass?"PASS":"MISMATCH"},{"reference",ref.string()},{"search_calls_completed",calls}};records.push_back(rec);write_json(out/"progress.json",records);std::cout<<rec.dump()<<std::endl;require(pass,"actual batch4 output/NDC mismatch");
 }}
 require(calls==80000,"query accounting");write_json(out/"complete.json",{{"status","PASS"},{"search_calls",calls},{"configurations",8},{"actual_batch4_forwarded",true},{"seconds_including_load",seconds(start)},{"threads",process_threads()},{"cpu",15},{"new_plain_rounds",0},{"new_qps_points",0}});return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

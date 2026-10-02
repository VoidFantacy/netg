#define main unused_e99_main
#include "common/evaluate.cpp"
#undef main
#include <faiss/IndexFlat.h>
#include "profile_helpers.hpp"
int main(int argc,char**argv){try{
 require(argc==3,"profile config new-output");threads();auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"new output required");fs::create_directories(out);
 auto idx=load_nsg(c["index"]);size_t n=c["n"],d=idx->d;require(n==10000&&d==512&&idx->metric_type==0,"frozen WebVid");Fvecs fq(c["queries"]);require(fq.n==n&&fq.d==d,"query shape");std::vector<float> q(n*d);for(size_t i=0;i<n;++i)std::copy(fq.row(i),fq.row(i)+d,q.data()+i*d);
 Router router(c["soft"],d,c["router"].get<std::string>());auto space=make_space(0,d);CountParam hc{space->get_dist_func(),space->get_dist_func_param(),0};Fvecs base(c["base"]);auto full=load_topology(c["hnsw_topology"].get<std::string>(),base,space.get());Worker worker(*idx);idx->acsg.search_L=1250;full->setEf(1250);uint64_t calls=0;
 for(std::string method:{"GT10-soft-t1","HNSW"}){threads();bool h=method=="HNSW";auto ref=fs::path(c["reference_e99"].get<std::string>())/(method+(h?"__reference":"__optimized")+"_K100_L1250");
 Batch warm(n,100);worker.run(method,h?nullptr:&router,full.get(),hc,q,d,warm,false);calls+=n;reference(warm,ref);std::cout<<"WARM_PARITY "<<method<<std::endl;
 Batch b(n,100);auto s=stages(worker,router,*full,q,d,b,h);calls+=n;reference(b,ref);write_json(out/(method+".stages.json"),s);std::cout<<"STAGES "<<method<<" "<<s.dump()<<std::endl;
 Batch sampled(n,100);sampler(true);auto t=Clock::now();worker.run(method,h?nullptr:&router,full.get(),hc,q,d,sampled,false);double sec=seconds(t);sampler(false);calls+=n;reference(sampled,ref);auto z=saved_samples();z["wall_seconds"]=sec;z["parity"]=true;write_json(out/(method+".samples.json"),z);std::cout<<"SAMPLE_PARITY "<<method<<" samples="<<pc_count<<std::endl;
 }
 // Fixed numeric feasibility check, no timing claims and no ANN search.
 auto* flat=dynamic_cast<faiss::IndexFlat*>(idx->storage);require(flat,"flat storage");uint64_t rng=0x12345678,mismatch=0;double maxabs=0;auto dc=std::unique_ptr<faiss::DistanceComputer>(acsg::storage_distance_computer(idx->storage));
 for(size_t group=0;group<4096;++group){const float* query=q.data()+(group%n)*d;dc->set_query(query);std::array<faiss::idx_t,4> id;std::array<float,4> a,b;
 for(int j=0;j<4;++j){rng=rng*6364136223846793005ULL+1;id[j]=(rng>>32)%idx->ntotal;a[j]=(*dc)(id[j]);}
 dc->distances_batch_4(id[0],id[1],id[2],id[3],b[0],b[1],b[2],b[3]);for(int j=0;j<4;++j){mismatch+=memcmp(&a[j],&b[j],4)!=0;maxabs=std::max(maxabs,std::abs(double(a[j])-b[j]));}}
 write_json(out/"batch4_numeric.json",{{"pairs",16384},{"different_float_bits",mismatch},{"max_absolute_difference",maxabs},{"new_ann_queries",0}});
 struct rusage r;getrusage(RUSAGE_SELF,&r);require(r.ru_maxrss<64LL*1024*1024,"RSS cap");write_json(out/"complete.json",{{"status","PASS"},{"search_calls",calls},{"threads",process_threads()},{"cpu",15},{"maxrss_kib",r.ru_maxrss},{"purpose","diagnostic only, not new formal QPS"}});return 0;
 }catch(const std::exception&e){sampler(false);std::cerr<<e.what()<<std::endl;return 1;}}

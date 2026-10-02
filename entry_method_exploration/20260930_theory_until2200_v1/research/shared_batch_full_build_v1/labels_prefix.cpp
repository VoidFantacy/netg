#include "/data/netg/ACSG/entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_approximate_target_profiles_v1/src/base_engine.hpp"
#include <ctime>
#include <cerrno>
#include <set>
#include <sys/wait.h>
#include <unistd.h>



static std::string sha256_bytes(const void* raw,size_t bytes){
 int in[2],out[2];require(pipe(in)==0&&pipe(out)==0,"sha pipes");pid_t pid=fork();require(pid>=0,"sha fork");
 if(pid==0){dup2(in[0],STDIN_FILENO);dup2(out[1],STDOUT_FILENO);close(in[0]);close(in[1]);close(out[0]);close(out[1]);execl("/usr/bin/sha256sum","sha256sum",(char*)nullptr);_exit(127);}
 close(in[0]);close(out[1]);const char*p=static_cast<const char*>(raw);size_t done=0;
 while(done<bytes){ssize_t n=write(in[1],p+done,bytes-done);if(n<0&&errno==EINTR)continue;require(n>0,"sha write");done+=size_t(n);}
 close(in[1]);std::string value;char buf[256];for(;;){ssize_t n=read(out[0],buf,sizeof(buf));if(n<0&&errno==EINTR)continue;require(n>=0,"sha read");if(!n)break;value.append(buf,size_t(n));}
 close(out[0]);int status;require(waitpid(pid,&status,0)==pid&&WIFEXITED(status)&&WEXITSTATUS(status)==0,"sha child exit");
 require(value.size()>=64,"sha length");value.resize(64);require(value.find_first_not_of("0123456789abcdef")==std::string::npos,"sha format");return value;
}

struct Teacher {
 acsg::IndexACSGFlat& idx;std::vector<uint8_t> spans;ResearchKernel kernel;std::unique_ptr<faiss::DistanceComputer>plain;ActualCount count;faiss::VisitedTable vt;std::vector<acsg::EnterPoint>ep;std::vector<acsg::Neighbor>legacy;uint64_t calls=0,cap;
 explicit Teacher(acsg::IndexACSGFlat&i,uint64_t maxcalls):idx(i),cap(maxcalls),spans(make_spans(*i.acsg.final_graph,i.ntotal)),kernel(*i.acsg.final_graph,spans,i.ntotal),plain(acsg::storage_distance_computer(i.storage)),count(acsg::storage_distance_computer(i.storage)),vt(i.ntotal){ep.reserve(3);legacy.reserve(1501);}
 void search(const float*q,const std::array<int32_t,3>&e,int K,int L,faiss::idx_t*I,float*D,bool counting,bool original=false){require(calls<cap,"teacher call cap");ep.clear();for(int h:e)if(h>=0)ep.emplace_back(h,1);vt.advance();auto&dis=counting?static_cast<faiss::DistanceComputer&>(count):*plain;dis.set_query(q);if(original){idx.acsg.search_L=L;idx.acsg.search_new(dis,K,I,D,vt,2,ep,&legacy);}else kernel.search<true,false,true>(dis,vt,ep,L,K,I,D);++calls;}
};

int main(int argc,char**argv){try{
 require(argc==3,"labels config output");threads();auto c=read_json(argv[1]);fs::path out=argv[2];require(!fs::exists(out),"fresh labels");fs::create_directories(out);auto begin=Clock::now();size_t n=c["n"],d=c["dimension"];auto idx=load_nsg(c["index"]);require(idx->ntotal==c["base_n"]&&idx->d==d&&idx->metric_type==0,"dataset contract");Fvecs base(c["base"]);std::vector<float>vv(d);for(int j=0;j<32;++j){size_t id=(base.n-1)*j/31;idx->storage->reconstruct(id,vv.data());require(!memcmp(vv.data(),base.row(id),4*d),"base graph bytes");}
 auto allq=read_raw<float>(c["queries"].get<std::string>());size_t source_n=c["source_n"];require(allq.size()==source_n*d,"source dimensions");std::vector<float>q;std::vector<int32_t>rows;if(c.contains("query_rows")){rows=read_raw<int32_t>(c["query_rows"].get<std::string>());require(rows.size()==n,"row count");std::set<int32_t>unique;for(int32_t row:rows){require(row>=0&&size_t(row)<source_n&&unique.insert(row).second,"valid unique source rows");q.insert(q.end(),allq.begin()+size_t(row)*d,allq.begin()+(size_t(row)+1)*d);}}else{require(source_n==n,"complete source");q=std::move(allq);}require(q.size()==n*d&&n>=16,"query dimensions");require(c["max_NSG_calls"].get<size_t>()==n+32,"fixed call contract");Teacher e(*idx,n+32);std::array<int32_t,3>entry{idx->acsg.enterpoint,-1,-1};int L=c["L"];std::vector<int32_t>ids(n*100);std::vector<float>dist(n*100);std::array<faiss::idx_t,100>I;std::array<float,100>D;auto t=Clock::now();
 for(size_t i=0;i<n;++i){e.search(q.data()+i*d,entry,100,L,I.data(),D.data(),false);for(int k=0;k<100;++k){require(I[k]>=0&&I[k]<idx->ntotal&&std::isfinite(D[k]),"valid labels");ids[i*100+k]=I[k];dist[i*100+k]=D[k];}if((i+1)%1000==0){require(std::time(nullptr)<c["deadline_unix"].get<double>(),"deadline");threads();std::cout<<i+1<<"/"<<n<<std::endl;}}
 double label_seconds=seconds(t);auto full_ids_sha=sha256_bytes(ids.data(),ids.size()*sizeof(int32_t));auto full_dist_sha=sha256_bytes(dist.data(),dist.size()*sizeof(float));std::vector<int32_t>compact_ids(n*11);std::vector<float>compact_dist(n*11);for(size_t row=0;row<n;++row){std::copy_n(ids.data()+row*100,11,compact_ids.data()+row*11);std::copy_n(dist.data()+row*100,11,compact_dist.data()+row*11);}write_raw(out/"ids.i32",compact_ids);write_raw(out/"distances.f32",compact_dist);uint64_t checks=0;
 for(size_t i=0;i<16;++i){e.search(q.data()+i*d,entry,100,L,I.data(),D.data(),true);uint64_t ndc=e.count.count;for(int k=0;k<100;++k)require(I[k]==ids[i*100+k]&&!memcmp(&D[k],&dist[i*100+k],4),"teacher counted bits");e.search(q.data()+i*d,entry,100,L,I.data(),D.data(),true,true);require(e.count.count==ndc,"teacher linked NDC");for(int k=0;k<100;++k)require(I[k]==ids[i*100+k]&&!memcmp(&D[k],&dist[i*100+k],4),"teacher linked bits");checks+=2;}
 require(e.calls==n+32,"no GT10 route in teacher");resources(out);write_json(out/"complete.json",{{"status","PASS"},{"n",n},{"K",100},{"L",L},{"entry",entry[0]},{"label_loop_seconds",label_seconds},{"whole_process_seconds",seconds(begin)},{"new_NSG_calls",e.calls},{"GT10_route_calls",0},{"GT10_files_read",0},{"native_parity_checks",checks},{"threads",process_threads()},{"cpu",15},{"exact_GT_generated",false},{"stored_prefix",11},{"source_n",source_n},{"all100_ids_sha256",full_ids_sha},{"all100_dist_sha256",full_dist_sha}});return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

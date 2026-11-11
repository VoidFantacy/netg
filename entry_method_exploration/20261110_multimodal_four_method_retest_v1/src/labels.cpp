#include "native_common.hpp"
#include "observer.hpp"
int main(int argc,char** argv){try{
 require(argc==3,"labels input_dir output_dir");fs::path in=argv[1],out=argv[2];fs::create_directories(out);auto c=read_json(in/"manifest.json");auto t=Clock::now();auto idx=load_nsg(c["paths"]["index"]);require(idx->metric_type==c["metric_id"].get<int>(),"label metric identity");int d=idx->d;auto hubs=read_raw<int32_t>(in/"gate.ids.i32");require(hubs.size()==512,"512 hubs");idx->acsg.search_L=64;
 auto q=read_raw<float>(in/"gate_train.f32"),monitor=read_raw<float>(in/"gate_monitor.f32");q.insert(q.end(),monitor.begin(),monitor.end());auto gt=read_raw<int32_t>(in/"gate_train.gt.i32"),gm=read_raw<int32_t>(in/"gate_monitor.gt.i32");gt.insert(gt.end(),gm.begin(),gm.end());size_t n=q.size()/d;require(n==11024&&gt.size()==n*100,"label role shapes");
 // Current original search_new versus mechanically copied observer; no test rows.
 {faiss::VisitedTable va(idx->ntotal),vb(idx->ntotal);std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx->storage));std::vector<acsg::Neighbor> a,b;std::vector<uint32_t> depth(idx->ntotal);size_t checked=0;
 for(size_t qi=0;qi<32;++qi)for(size_t h=0;h<512;h+=17){dc->set_query(q.data()+qi*d);std::vector<acsg::EnterPoint> ep{{hubs[h],0}};faiss::idx_t ids[1];float dist[1];idx->acsg.search_new(*dc,1,ids,dist,va,2,ep,&a);e96_observer::run(*idx->acsg.final_graph,*dc,vb,64,b,ep,2,1,nullptr,idx->ntotal,depth);for(int k=0;k<1;++k)require(ids[k]==b[k].id&&std::memcmp(dist+k,&b[k].distance,4)==0,"observer output bit parity failed");va.advance();vb.advance();++checked;}
 write_json(out/"parity.json",{{"status","PASS"},{"queries",32},{"searches",checked},{"returned_k",1},{"L",64},{"label","first discovery depth, seed zero"}});}
 const int threads=16;omp_set_dynamic(0);omp_set_num_threads(threads);
 for(size_t start=0;start<n;start+=128){size_t end=std::min(n,start+128);fs::path shard=out/("rows_"+std::to_string(start));if(fs::exists(shard.string()+".json"))continue;resources(out);auto ts=Clock::now();std::vector<int32_t> ids((end-start)*512),hop(ids.size(),999);std::vector<float> distances(ids.size());
 #pragma omp parallel
 {faiss::VisitedTable vt(idx->ntotal);std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx->storage));std::vector<acsg::Neighbor> ret;std::vector<uint32_t> depth(idx->ntotal);std::vector<acsg::EnterPoint> ep(1);
 #pragma omp for schedule(dynamic,1)
 for(size_t qi=start;qi<end;++qi){dc->set_query(q.data()+qi*d);for(size_t h=0;h<512;++h){ep[0]=acsg::EnterPoint(hubs[h],0);e96_observer::run(*idx->acsg.final_graph,*dc,vt,64,ret,ep,2,1,nullptr,idx->ntotal,depth);size_t at=(qi-start)*512+h;ids[at]=ret[0].id;distances[at]=ret[0].distance;if(ids[at]==gt[qi*100])hop[at]=depth[ids[at]];vt.advance();}}}
 write_raw(shard.string()+".ids.i32",ids);write_raw(shard.string()+".distances.f32",distances);write_raw(shard.string()+".hop.i32",hop);json r={{"start",start},{"end",end},{"seconds",seconds(ts)},{"searches",ids.size()},{"threads",threads}};write_json(shard.string()+".json",r);std::cout<<r.dump()<<std::endl;
 }
 write_json(out/"complete.json",{{"rows",n},{"hubs",512},{"L",64},{"K",1},{"total_seconds",seconds(t)},{"threads",threads},{"source_inputs",in.string()}});return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
#include <map>
int main(int argc,char** argv){try{
 require(argc==3,"label config new_output");std::ifstream f(argv[1]);json c;f>>c;fs::path out=argv[2];require(!fs::exists(out),"existing labels");fs::create_directories(out);write_json(out/"config.json",c);
 size_t n=c.at("num_queries"),d=c.at("dim"),h=c.at("hub_count"),gtk=c.at("gt_k"),a=56,old_a=24;require(n*a==c.at("logical_call_cap"),"label cap");
 auto q=read_raw<float>(c.at("queries_file"));auto hubs=read_raw<int32_t>(c.at("hub_ids"));auto ts=read_raw<int32_t>(c.at("triples_file"));auto ots=read_raw<int32_t>(c.at("old_triples"));
 auto oldids=read_raw<int32_t>(c.at("old_ids"));auto oldndc=read_raw<uint32_t>(c.at("old_ndc"));
 require(q.size()==n*d&&hubs.size()==h&&ts.size()==n*a*3&&ots.size()==n*old_a*3&&oldids.size()==n*old_a*K&&oldndc.size()==n*old_a,"label/cache shape");
 auto index=std::make_unique<acsg::IndexACSGFlat>();index->loadACPG(c.at("index_path").get<std::string>().c_str());std::vector<float>().swap(index->acsg.pheromone);std::vector<float>().swap(index->acsg.weight);
 require(index->d==int(d)&&index->metric_type==faiss::METRIC_INNER_PRODUCT&&c.at("L")==128,"graph contract");index->acsg.search_L=128;int nt=c.at("threads");require(nt==16,"offline threads");omp_set_dynamic(0);omp_set_num_threads(nt);
 std::vector<std::unique_ptr<NativeWork>> workers;for(int t=0;t<nt;++t)workers.push_back(std::make_unique<NativeWork>(*index,true));NativeWork plain(*index,false);Work reference(*index,true);
 auto route=[&](const int32_t* ids){Decision r;for(size_t k=0;k<3;++k){require(ids[k]>=0&&size_t(ids[k])<h,"local id");r.ids[k]=hubs[ids[k]];}require(r.ids[0]<r.ids[1]&&r.ids[1]<r.ids[2],"canonical distinct entries");return r;};
 size_t parity_calls=0;for(size_t i=0;i<32;++i){auto r=route(ts.data()+i*a*3);auto x=workers[0]->search(*index,q.data()+i*d,r,3),y=plain.search(*index,q.data()+i*d,r,3);std::vector<int32_t> es(r.ids.begin(),r.ids.end());auto z=reference.run(*index,q.data()+i*d,es,{0,1,2},3);parity_calls+=3;require(x.ids==y.ids&&x.ids==z.ids&&x.ndc==z.ndc&&std::memcmp(x.distances.data(),y.distances.data(),K*4)==0&&std::memcmp(x.distances.data(),z.distances.data(),K*4)==0,"native/reference/plain parity");
  auto cr=route(ots.data()+i*old_a*3);auto cx=workers[0]->search(*index,q.data()+i*d,cr,3);++parity_calls;require(std::equal(cx.ids.begin(),cx.ids.end(),oldids.data()+i*old_a*K)&&cx.ndc==oldndc[i*old_a],"old cache parity");}
 require(parity_calls<=256,"parity cap");write_json(out/"parity.json",{{"status","PASS"},{"physical_calls",parity_calls},{"cases",32},{"old_cache_cases",32}});
 auto gt=read_raw<int64_t>(c.at("gt_file"));require(gt.size()==n*gtk,"GT shape");
 std::ofstream idsf(out/"ids.i32",std::ios::binary),ndcf(out/"graph_ndc.u32",std::ios::binary),hitf(out/"hits.u8",std::ios::binary),maskf(out/"masks.u16",std::ios::binary),reusef(out/"reused.u8",std::ios::binary);
 size_t calls=0,reused=0;auto start=Clock::now();
 for(size_t begin=0;begin<n;begin+=64){size_t count=std::min(size_t(64),n-begin);std::vector<Search> outputs(count*a);std::vector<uint8_t> reuse(count*a);
  #pragma omp parallel for schedule(static)
  for(size_t row=0;row<count;++row){size_t i=begin+row;std::map<std::array<int32_t,3>,size_t> cache;for(size_t j=0;j<old_a;++j){std::array<int32_t,3> key;std::copy_n(ots.data()+(i*old_a+j)*3,3,key.begin());cache[key]=j;}
   for(size_t j=0;j<a;++j){std::array<int32_t,3> key;std::copy_n(ts.data()+(i*a+j)*3,3,key.begin());auto pos=cache.find(key);auto& x=outputs[row*a+j];if(pos!=cache.end()){size_t oi=i*old_a+pos->second;std::copy_n(oldids.data()+oi*K,K,x.ids.begin());x.ndc=oldndc[oi];reuse[row*a+j]=1;}else{x=workers[omp_get_thread_num()]->search(*index,q.data()+i*d,route(key.data()),3);}}
  }
  for(size_t row=0;row<count;++row)for(size_t j=0;j<a;++j){auto& x=outputs[row*a+j];uint16_t mask=hitmask(x.ids,gt.data()+(begin+row)*gtk);uint8_t hit=__builtin_popcount(unsigned(mask)),re=reuse[row*a+j];idsf.write(reinterpret_cast<char*>(x.ids.data()),K*4);ndcf.write(reinterpret_cast<char*>(&x.ndc),4);hitf.write(reinterpret_cast<char*>(&hit),1);maskf.write(reinterpret_cast<char*>(&mask),2);reusef.write(reinterpret_cast<char*>(&re),1);reused+=re;calls+=1-re;}
  require(idsf&&ndcf&&hitf&&maskf&&reusef,"label writes");double sec=std::chrono::duration<double>(Clock::now()-start).count();json p={{"rows_complete",begin+count},{"rows_total",n},{"physical_calls",calls},{"reused",reused},{"parity_calls",parity_calls},{"seconds",sec},{"eta_seconds",sec*(n-begin-count)/(begin+count)}};write_json(out/"progress.json",p);if(begin%1024==0||begin+count==n)std::cout<<p.dump()<<std::endl;
 }
 write_json(out/"complete.json",{{"status","COMPLETE"},{"logical_calls",n*a},{"physical_calls",calls},{"reused",reused},{"parity_calls",parity_calls},{"seconds",std::chrono::duration<double>(Clock::now()-start).count()}});return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

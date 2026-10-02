#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
#include <sched.h>
struct TraceParam {hnswlib::DISTFUNC<float> fn;void* param;std::unordered_map<const void*,int32_t> local;std::vector<int32_t>* events=nullptr;};
float observed_ip(const void* a,const void* b,const void* p) {
 auto* s=(TraceParam*)p;if(s->events)s->events->push_back(s->local.at(b));return s->fn(a,b,s->param);
}
class TraceSpace final:public hnswlib::SpaceInterface<float> {
 hnswlib::InnerProductSpace inner;
 public:TraceParam p;explicit TraceSpace(size_t d):inner(d),p{inner.get_dist_func(),inner.get_dist_func_param(),{},nullptr}{}
 size_t get_data_size() override{return inner.get_data_size();}
 hnswlib::DISTFUNC<float> get_dist_func() override{return observed_ip;}
 void* get_dist_func_param() override{return &p;}
};
int main(int argc,char** argv) {try {
 require(argc==3,"probe config new_output");std::ifstream f(argv[1]);json c;f>>c;fs::path out=argv[2];require(!fs::exists(out),"refuse existing output");fs::create_directories(out);
 require(c.at("threads")==1,"single thread required");omp_set_num_threads(1);cpu_set_t cp;CPU_ZERO(&cp);CPU_SET(15,&cp);require(sched_setaffinity(0,sizeof(cp),&cp)==0,"affinity");
 const size_t n=128,d=c.at("dim"),h=c.at("hub_count");auto q=read_raw<float>(c.at("queries_file"));auto w=read_raw<float>(c.at("W"));auto hubs=read_raw<int32_t>(c.at("hub_ids"));
 require(q.size()==n*d && w.size()==h*d && hubs.size()==h,"shape");finite_matrix(q,"q");finite_matrix(w,"W");
 TraceSpace ts(d);hnswlib::HierarchicalNSW<float> graph(&ts,c.at("graph_file").get<std::string>(),false,h);hnswlib::InnerProductSpace plain_space(d);
 hnswlib::HierarchicalNSW<float> plain(&plain_space,c.at("graph_file").get<std::string>(),false,h);CountSpace cs(d);hnswlib::HierarchicalNSW<float> counted(&cs,c.at("graph_file").get<std::string>(),false,h);
 std::unordered_map<int32_t,int32_t> local;for(size_t j=0;j<h;++j){require(graph.getExternalLabel(j)==size_t(hubs[j]),"ID mapping");require(std::memcmp(graph.getDataByInternalId(j),w.data()+j*d,d*4)==0,"coordinates");ts.p.local.emplace(graph.getDataByInternalId(j),j);local.emplace(hubs[j],j);}
 json pc=c.at("policy");Policy policy(pc,c.at("graph_file"),true,true);
 auto rank_heap=[&](auto heap){std::vector<int32_t> row(heap.size());for(size_t j=row.size();j-->0;){row[j]=local.at(heap.top().second);heap.pop();}return row;};
 std::vector<int32_t> exact(n*h),ann8(n*8),ann40(n*3),annH(n*3);std::vector<float> exact_dist(n*h);std::vector<uint8_t> seen(n*h),seen40(n*h),seenH(n*h);std::vector<uint32_t> ndc(n*3);
 json events=json::array();size_t hcalls=0,routechecks=0;
 for(size_t i=0;i<n;++i){const float* query=q.data()+i*d;std::vector<int32_t> ev,base3;
  graph.setEf(10);plain.setEf(10);counted.setEf(10);
  for(size_t k:{size_t(1),size_t(3),size_t(8)}) {
   ev.clear();ts.p.events=&ev;auto a=graph.searchKnn(query,k);ts.p.events=nullptr;auto b=plain.searchKnn(query,k);uint64_t ct=0;route_counter=&ct;auto z=counted.searchKnn(query,k);route_counter=nullptr;hcalls+=3;
   auto same=[](auto x,auto y){if(x.size()!=y.size())return false;while(!x.empty()){if(x.top()!=y.top())return false;x.pop();y.pop();}return true;};
   require(same(a,b) && same(a,z) && ct==ev.size(),"observer/plain/count parity");++routechecks;auto row=rank_heap(a);
   if(k==3){base3=row;Decision r=policy.route(query);++hcalls;std::array<int32_t,3> ids{hubs[row[0]],hubs[row[1]],hubs[row[2]]};std::sort(ids.begin(),ids.end());require(ids==r.ids && r.ndc==ct,"current policy parity");}
   if(k==8){require(std::equal(base3.begin(),base3.end(),row.begin()),"top8 prefix mismatch");std::copy(row.begin(),row.end(),ann8.begin()+i*8);for(int j:ev)seen[i*h+j]=1;ndc[i*3]=ct;events.push_back(ev);}
  }
  for(size_t ef:{size_t(40),h}) {graph.setEf(ef);ev.clear();ts.p.events=&ev;auto row=rank_heap(graph.searchKnn(query,3));ts.p.events=nullptr;++hcalls;
   auto& target=ef==40?ann40:annH;auto& vis=ef==40?seen40:seenH;std::copy(row.begin(),row.end(),target.begin()+i*3);for(int j:ev)vis[i*h+j]=1;ndc[i*3+(ef==40?1:2)]=ev.size();}
  std::vector<std::pair<float,int32_t>> ranked;for(size_t j=0;j<h;++j)ranked.push_back({plain_space.get_dist_func()(query,w.data()+j*d,plain_space.get_dist_func_param()),int32_t(j)});
  std::sort(ranked.begin(),ranked.end(),[&](auto a,auto b){return a.first<b.first || (a.first==b.first && hubs[a.second]<hubs[b.second]);});
  for(size_t j=0;j<h;++j){exact[i*h+j]=ranked[j].second;exact_dist[i*h+j]=ranked[j].first;}
 }
 write_raw(out/"exact_local.i32",exact);write_raw(out/"exact_distance.f32",exact_dist);write_raw(out/"ann8_local.i32",ann8);write_raw(out/"ann40_local.i32",ann40);write_raw(out/"annH_local.i32",annH);
 write_raw(out/"seen.u8",seen);write_raw(out/"seen40.u8",seen40);write_raw(out/"seenH.u8",seenH);write_raw(out/"route_ndc.u32",ndc);write_json(out/"trace_events.json",events);
 std::cout<<"ROUTE_PARITY_PASS "<<routechecks<<std::endl;
 auto index=std::make_unique<acsg::IndexACSGFlat>();index->loadACPG(c.at("index_path").get<std::string>().c_str());std::vector<float>().swap(index->acsg.pheromone);std::vector<float>().swap(index->acsg.weight);
 require(index->d==int(d) && index->metric_type==faiss::METRIC_INNER_PRODUCT,"index metric");index->acsg.search_L=128;NativeWork work(*index,true);Work ref(*index,true);
 std::vector<int32_t> ids,entries,parity_ids;std::vector<float> distances;std::vector<uint32_t> graphndc,parity_ndc;size_t calls=0;json variants=json::array();
 variants.push_back("ann3");variants.push_back("exact3");variants.push_back("ef40_3");for(int a=0;a<8;++a)for(int b=a+1;b<8;++b)for(int e=b+1;e<8;++e)variants.push_back("c8_"+std::to_string(a)+"_"+std::to_string(b)+"_"+std::to_string(e));require(variants.size()==59,"variant count");
 for(size_t i=0;i<n;++i) {
  auto run3=[&](std::array<int32_t,3> localids){Decision dec;for(size_t k=0;k<3;++k)dec.ids[k]=hubs[localids[k]];std::sort(dec.ids.begin(),dec.ids.end());auto s=work.search(*index,q.data()+i*d,dec,3);++calls;
   ids.insert(ids.end(),s.ids.begin(),s.ids.end());distances.insert(distances.end(),s.distances.begin(),s.distances.end());entries.insert(entries.end(),dec.ids.begin(),dec.ids.end());graphndc.push_back(s.ndc);};
  run3({ann8[i*8],ann8[i*8+1],ann8[i*8+2]});run3({exact[i*h],exact[i*h+1],exact[i*h+2]});run3({ann40[i*3],ann40[i*3+1],ann40[i*3+2]});
  for(int a=0;a<8;++a)for(int b=a+1;b<8;++b)for(int e=b+1;e<8;++e)run3({ann8[i*8+a],ann8[i*8+b],ann8[i*8+e]});
  if(i<16)for(size_t u:{size_t(0),h/2,h-1}){auto s=ref.run(*index,q.data()+i*d,hubs,{int32_t(u),-1,-1},1);++calls;parity_ids.insert(parity_ids.end(),s.ids.begin(),s.ids.end());parity_ndc.push_back(s.ndc);}
 }
 require(calls==7600 && hcalls==1536,"call budget");write_raw(out/"ids.i32",ids);write_raw(out/"distances.f32",distances);write_raw(out/"entries.i32",entries);write_raw(out/"graph_ndc.u32",graphndc);write_raw(out/"parity_ids.i32",parity_ids);write_raw(out/"parity_ndc.u32",parity_ndc);
 write_json(out/"complete.json",{{"status","COMPLETE"},{"NSG_calls",calls},{"HNSW_calls",hcalls},{"route_parity_checks",routechecks},{"variants",variants},{"threads",1},{"GT_read",false}});std::cout<<"COMPLETE "<<calls<<std::endl;return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

#include "/data/netg/ACSG/entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial/src/search_core.hpp"
#include <queue>
#include <tuple>

struct Sparse {
 std::vector<uint64_t> offset;
 std::vector<uint16_t> query;
 std::vector<uint8_t> value;
};
struct HeapNode {uint32_t gain;int id;bool old;};
struct LowerPriority {
 bool operator()(const HeapNode&a,const HeapNode&b)const{
  return std::make_tuple(a.gain,a.old,-a.id)<std::make_tuple(b.gain,b.old,-b.id);
 }
};
void tick(const json& c,Clock::time_point start){
 require(std::time(nullptr)<c["deadline_unix"].get<double>()&&seconds(start)<c["seconds_cap"].get<double>(),"bounded diagnostic time");
 struct rusage ru;getrusage(RUSAGE_SELF,&ru);require(ru.ru_maxrss<40LL*1024*1024,"RSS cap");
}
std::vector<int32_t> neighborhood(const acsg::Graph<int32_t>&g,int h,int total){
 std::vector<int32_t> v{h};v.reserve(g.K+1);
 for(int j=0;j<g.K;++j){int u=g.at(h,j);if(u<0)continue;require(u<total,"valid graph ID");v.push_back(u);}
 std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());require(v.size()<=65,"closed row width");return v;
}
std::vector<uint8_t> strict_first(acsg::IndexACSGFlat&idx,const std::vector<float>&q,const std::vector<int32_t>&gt,int n,fs::path out){
 std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx.storage));std::vector<uint8_t> strict(n);std::vector<float> scores(n*2);
 for(int i=0;i<n;++i){std::set<int32_t> ids;for(int k=0;k<100;++k){int id=gt[i*100+k];require(id>=0&&id<idx.ntotal,"valid GT");ids.insert(id);}require(ids.size()==100,"unique GT100");
  dc->set_query(q.data()+size_t(i)*idx.d);for(int j=0;j<2;++j){scores[i*2+j]=(*dc)(gt[i*100+j]);require(std::isfinite(scores[i*2+j]),"finite GT score");}
  strict[i]=scores[i*2]<scores[i*2+1];
 }
 write_raw(out/"strict_GT1.u8",strict);write_raw(out/"GT1_GT2.distances.f32",scores);return strict;
}
void save_matrix(const acsg::Graph<int32_t>&graph,int total,const std::vector<int32_t>&ids,const std::vector<int32_t>&gt,const std::vector<uint8_t>&strict,int n,fs::path out,const Sparse* sparse=nullptr){
 fs::create_directories(out);int h=ids.size();std::vector<int32_t> rows(h*65,-1);std::vector<uint8_t> matrix(size_t(n)*h),count(size_t(n)*h),one(size_t(n)*h);
 std::unordered_map<int,std::vector<std::pair<int,int>>> inv;
 for(int i=0;i<n;++i)for(int k=0;k<100;++k)inv[gt[i*100+k]].emplace_back(i,k);
 for(int a=0;a<h;++a){auto neighbors=neighborhood(graph,ids[a],total);std::copy(neighbors.begin(),neighbors.end(),rows.begin()+a*65);
  for(int v:neighbors){auto it=inv.find(v);if(it==inv.end())continue;for(auto item:it->second){int i=item.first,k=item.second;++count[size_t(i)*h+a];if(k==0&&strict[i])one[size_t(i)*h+a]=1;}}
  for(int i=0;i<n;++i)matrix[size_t(i)*h+a]=100*one[size_t(i)*h+a]+count[size_t(i)*h+a];
  if(sparse){std::vector<uint8_t> check(n);for(uint64_t p=sparse->offset[ids[a]];p<sparse->offset[ids[a]+1];++p)check[sparse->query[p]]=sparse->value[p];for(int i=0;i<n;++i)require(check[i]==matrix[size_t(i)*h+a],"independent sparse/dense scores");}
 }
 write_raw(out/"hub_ids.i32",ids);write_raw(out/"closed_rows.i32",rows);write_raw(out/"score.u8",matrix);write_raw(out/"GT1.u8",one);write_raw(out/"GT100_count.u8",count);
 uint64_t objective=0;for(int i=0;i<n;++i)objective+=*std::max_element(matrix.begin()+size_t(i)*h,matrix.begin()+size_t(i+1)*h);
 write_json(out/"complete.json",{{"status","PASS"},{"n",n},{"H",h},{"score_denominator",200},{"objective_integer",objective},{"sparse_dense_parity",sparse!=nullptr}});
}
int main(int argc,char**argv){try{
 require(argc==4,"mode config output");threads();std::string mode=argv[1];auto c=read_json(argv[2]);fs::path out=argv[3];require(!fs::exists(out),"preserve outputs");fs::create_directories(out);auto start=Clock::now();int n=c["n"],d=c["dimension"],B=c["H"];
 require(omp_get_max_threads()==1&&sched_getcpu()==15,"CPU15 one thread");require((mode=="select"&&n==5000)||(mode=="evaluate"&&n==4096),"fixed full source rows");
 auto gt=read_raw<int32_t>(c["GT"]);auto q=read_raw<float>(c["queries"]);require(gt.size()==size_t(n)*100&&q.size()==size_t(n)*d,"query GT shape");
 auto idx=load_nsg(c["index"]);require(idx->d==d&&idx->ntotal==c["base_n"]&&idx->metric_type==0,"fixed raw-IP index");auto&graph=*idx->acsg.final_graph;require(graph.K>0&&graph.K<=64,"graph width");int N=idx->ntotal;
 auto strict=strict_first(*idx,q,gt,n,out);uint64_t nonzero=0,recomputations=0,slots=0;json selection=json::array();
 if(mode=="select"){
  auto old=read_raw<int32_t>(c["old_hub_ids"]);require(old.size()==size_t(B)&&std::set<int32_t>(old.begin(),old.end()).size()==size_t(B),"old H identity size");std::vector<uint8_t> oldmask(N),chosen(N);for(int id:old){require(id>=0&&id<N,"old hub");oldmask[id]=1;}
  std::vector<uint64_t> targetptr(size_t(N)+1);for(int v:gt)++targetptr[v+1];for(int v=0;v<N;++v)targetptr[v+1]+=targetptr[v];auto cursor=targetptr;std::vector<uint32_t> inverted(gt.size());
  for(int i=0;i<n;++i)for(int k=0;k<100;++k)inverted[cursor[gt[i*100+k]]++]=uint32_t(i*128+k);cursor.clear();cursor.shrink_to_fit();
  Sparse s;s.offset.resize(size_t(N)+1);std::vector<uint16_t> scratch(n);std::vector<int> touched;touched.reserve(n);std::priority_queue<HeapNode,std::vector<HeapNode>,LowerPriority> heap;
  for(int h=0;h<N;++h){if(h%100000==0){tick(c,start);write_json(out/"progress.json",{{"stage","all_base_score"},{"h",h},{"N",N},{"nonzero",s.query.size()},{"seconds",seconds(start)}});}
   s.offset[h]=s.query.size();touched.clear();auto closed=neighborhood(graph,h,N);slots+=graph.K;
   for(int v:closed)for(uint64_t p=targetptr[v];p<targetptr[v+1];++p){int i=inverted[p]/128,k=inverted[p]%128;if(!scratch[i])touched.push_back(i);scratch[i]+=1+(k==0&&strict[i]?100:0);}
   std::sort(touched.begin(),touched.end());uint32_t gain=0;
   for(int i:touched){require(scratch[i]<=165,"integer score range");s.query.push_back(i);s.value.push_back(scratch[i]);gain+=scratch[i];scratch[i]=0;}
   require(s.query.size()<=c["max_nonzero"].get<uint64_t>(),"sparse label cap");if(gain)heap.push({gain,h,bool(oldmask[h])});
  }
  s.offset[N]=s.query.size();nonzero=s.query.size();write_raw(out/"all_base.offset.u64",s.offset);write_raw(out/"all_base.query.u16",s.query);write_raw(out/"all_base.score.u8",s.value);
  std::vector<uint8_t> best(n);std::vector<int32_t> greedy;uint64_t objective=0;
  while(greedy.size()<size_t(B)&&!heap.empty()){
   auto top=heap.top();heap.pop();if(chosen[top.id])continue;uint32_t gain=0;for(uint64_t p=s.offset[top.id];p<s.offset[top.id+1];++p)if(s.value[p]>best[s.query[p]])gain+=s.value[p]-best[s.query[p]];
   ++recomputations;if(recomputations%1024==0)tick(c,start);require(gain<=top.gain,"nonincreasing lazy bound");
   if(gain<top.gain){if(gain)heap.push({gain,top.id,top.old});continue;}
   if(!gain)break;require(heap.empty()||heap.top().gain<=gain,"global marginal upper bound");chosen[top.id]=1;greedy.push_back(top.id);objective+=gain;
   for(uint64_t p=s.offset[top.id];p<s.offset[top.id+1];++p)best[s.query[p]]=std::max(best[s.query[p]],s.value[p]);
   selection.push_back({{"step",greedy.size()},{"id",top.id},{"gain_integer",gain},{"remaining_heap_gain_upper",heap.empty()?0:heap.top().gain},{"objective_integer",objective}});
  }
  auto fill=[&](std::vector<int32_t>&ids){std::set<int> used(ids.begin(),ids.end());for(int id:old)if(ids.size()<size_t(B)&&used.insert(id).second)ids.push_back(id);for(int id=0;ids.size()<size_t(B);++id)if(used.insert(id).second)ids.push_back(id);std::sort(ids.begin(),ids.end());require(ids.size()==size_t(B),"fixed hub budget");};fill(greedy);
  std::unordered_map<int,uint32_t> freq;for(int i=0;i<n;++i)++freq[gt[i*100]];std::vector<std::pair<uint32_t,int>> order;for(auto item:freq)order.emplace_back(item.second,item.first);std::sort(order.begin(),order.end(),[](auto a,auto b){return a.first!=b.first?a.first>b.first:a.second<b.second;});std::vector<int32_t> frequency;for(auto item:order){if(frequency.size()==size_t(B))break;frequency.push_back(item.second);}fill(frequency);
  write_json(out/"greedy_selection.json",selection);write_raw(out/"greedy_best_score.u8",best);
  for(auto name_ids:std::vector<std::pair<std::string,std::vector<int32_t>>>{{"OriginalH",old},{"GraphH",greedy},{"FrequencyH",frequency}})save_matrix(graph,N,name_ids.second,gt,strict,n,out/name_ids.first,&s);
  require(read_json(out/"GraphH/complete.json")["objective_integer"].get<uint64_t>()==objective,"greedy final objective");
 }else{
  for(auto m:c["methods"]){auto ids=read_raw<int32_t>(m["hub_ids"]);require(ids.size()==size_t(B),"frozen H budget");save_matrix(graph,N,ids,gt,strict,n,out/m["name"].get<std::string>());tick(c,start);}
 }
 tick(c,start);struct rusage ru;getrusage(RUSAGE_SELF,&ru);write_json(out/"complete.json",{{"status","PASS"},{"mode",mode},{"n",n},{"H",B},{"NSG_calls",0},{"ANN_calls",0},{"new_GT",0},{"new_graphs",0},{"new_training",0},{"graph_derived_labels",true},{"GT_distance_checks",n*2},{"strict_GT1_queries",std::accumulate(strict.begin(),strict.end(),uint64_t(0))},{"all_base_sparse_nonzero",nonzero},{"graph_slots_scanned",slots},{"greedy_steps",selection.size()},{"lazy_recomputations",recomputations},{"seconds",seconds(start)},{"threads",omp_get_max_threads()},{"cpu",sched_getcpu()},{"maxrss_kib",ru.ru_maxrss}});return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

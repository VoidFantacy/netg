#include "e194.inc"
#include <ACSG/detail/CandidatePool.h>
#include <zlib.h>
namespace e195 {
using namespace e191;
using namespace faiss;
using acsg::Neighbor;
using acsg::EnterPoint;
using acsg::SearchTrace;
namespace detail=acsg::detail;
static std::mutex output_mutex;
struct Replay {std::vector<int32_t> scored,expanded,rejected;};
#include "replay.inc"
std::string bytes_sha(const void*p,size_t n){EVP_MD_CTX*x=EVP_MD_CTX_new();EVP_DigestInit_ex(x,EVP_sha256(),nullptr);EVP_DigestUpdate(x,p,n);unsigned char out[32];unsigned int sz;EVP_DigestFinal_ex(x,out,&sz);EVP_MD_CTX_free(x);std::ostringstream s;for(auto a:out)s<<std::hex<<std::setw(2)<<std::setfill('0')<<int(a);return s.str();}
struct Meta {
 std::vector<uint32_t> in;std::vector<uint16_t> out;std::unordered_map<int32_t,int32_t> rep;
 Meta(const json&c,const acsg::Graph<int32_t>&g,const Posting&p){
  fs::path path=fs::path(c.at("meta_dir"));
  if(fs::exists(path/"complete.json")){in=read_raw<uint32_t>(path/"indegree.u32");out=read_raw<uint16_t>(path/"outdegree.u16");auto a=read_raw<int32_t>(path/"representatives.i32");for(size_t j=0;j<a.size();j+=2)rep[a[j]]=a[j+1];require(in.size()==size_t(g.N)&&out.size()==size_t(g.N),"static degree shape");return;}
  auto t=Clock::now();fresh_dir(path);in.assign(g.N,0);out.assign(g.N,0);std::vector<int32_t>v;v.reserve(g.K);uint64_t invalid=0,self=0,duplicates=0,edges=0;
  for(int n=0;n<g.N;++n){v.clear();for(int j=0;j<g.K;++j){int id=g.at(n,j);if(id<0||id>=g.N){++invalid;continue;}if(id==n){++self;continue;}v.push_back(id);}std::sort(v.begin(),v.end());auto e=std::unique(v.begin(),v.end());duplicates+=v.end()-e;v.erase(e,v.end());require(v.size()<=65535,"outdegree storage");out[n]=v.size();edges+=v.size();for(int id:v)++in[id];}
  for(size_t row=0;row<p.H;++row)for(int j=0;j<p.counts[row];++j)rep.emplace(p.targets[row*p.b+j],-1);
  std::vector<uint8_t>target(g.N,0);for(auto a:rep)target[a.first]=1;
  for(int n=0;n<g.N;++n)for(int j=0;j<g.K;++j){int id=g.at(n,j);if(id<0||id>=g.N||id==n||!target[id])continue;int&old=rep.at(id);if(old<0||std::tuple(out[n],in[n],-n)>std::tuple(out[old],in[old],-old))old=n;}
  std::vector<int32_t>a;std::vector<int32_t>keys;for(auto x:rep)keys.push_back(x.first);std::sort(keys.begin(),keys.end());for(int id:keys){if(rep[id]<0)rep[id]=id;a.push_back(id);a.push_back(rep[id]);}
  write_raw(path/"indegree.u32",in);write_raw(path/"outdegree.u16",out);write_raw(path/"representatives.i32",a);
  uint64_t zero=std::count(in.begin(),in.end(),0),outzero=std::count(out.begin(),out.end(),0);fresh_json(path/"complete.json",{{"status","PASS_STATIC_DIRECTED_DEGREES"},{"N",g.N},{"slots",g.K},{"unique_nonself_edges",edges},{"invalid_slots",invalid},{"self_slots",self},{"duplicate_slots",duplicates},{"zero_indegree",zero},{"zero_outdegree",outzero},{"indegree_sha",bytes_sha(in.data(),in.size()*4)},{"outdegree_sha",bytes_sha(out.data(),out.size()*2)},{"representative_targets",rep.size()},{"seconds",seconds(t)},{"GT_read",false}});
 }
};
using Work=std::array<uint64_t,8>;
struct Event{int32_t id;float value;uint32_t stage;};
struct Detail{std::vector<Event>events;std::vector<int32_t>seeds;std::array<double,4>us{};};
struct Meter{std::vector<Work>work;};
struct Node{float value;uint32_t order;int32_t id;};
struct MinNode{bool operator()(const Node&a,const Node&b)const{return a.value>b.value||(a.value==b.value&&a.order>b.order);}};
void merge_linear(const int32_t*R,const float*D,int K,const std::vector<Event>&events,std::vector<int32_t>&I,std::vector<float>&V){
 std::vector<Posting::Record>x;for(int j=0;j<K;++j)x.push_back({R[j],D[j],uint32_t(j),false});
 for(size_t j=0;j<events.size();++j){size_t worst=0;for(int k=1;k<K;++k)if(Posting::better(x[worst],x[k]))worst=k;if(events[j].value<x[worst].distance)x[worst]={events[j].id,events[j].value,uint32_t(K+j),false};}
 if(!events.empty())std::sort(x.begin(),x.end(),Posting::better);I.clear();V.clear();for(auto a:x){I.push_back(a.id);V.push_back(a.distance);}
}
// Independent auxiliary expansion. Main visited is read-only, and no main beam is resumed.
void expansion(DistanceComputer&dc,const acsg::Graph<int32_t>&g,const VisitedTable&vt,const std::vector<int32_t>&C,const std::vector<float>&cv,const std::vector<Node>&seeds,bool onehop,size_t cap,size_t used,std::vector<Event>&events,Work&w){
 std::unordered_set<int32_t>seen(C.begin(),C.end()),expanded;seen.reserve(C.size()+cap+8);expanded.reserve(cap+4);for(auto a:events)seen.insert(a.id);
 std::priority_queue<Node,std::vector<Node>,MinNode>front;for(auto a:seeds)front.push(a);uint32_t arrival=0;size_t slots=0,limit=64*cap;
 auto visit=[&](int n,int slot){++slots;++w[4];int id=g.at(n,slot);if(id<0||id>=g.N||vt.get(id)||!seen.insert(id).second)return;float v=dc(id);require(std::isfinite(v),"finite auxiliary score");events.push_back({id,v,2});++used;++w[2];if(!onehop)front.push({v,arrival++,id});};
 if(onehop){for(int slot=0;slot<g.K&&used<cap&&slots<limit;++slot)for(auto a:seeds){if(used>=cap||slots>=limit)break;visit(a.id,slot);}w[3]+=seeds.size();return;}
 while(!front.empty()&&used<cap&&slots<limit){auto x=front.top();front.pop();if(!expanded.insert(x.id).second)continue;++w[3];for(int j=0;j<g.K&&used<cap&&slots<limit;++j)visit(x.id,j);}
}
void complete_nav(DistanceComputer&dc,const acsg::Graph<int32_t>&g,const VisitedTable&vt,const std::array<int32_t,3>&route,int K,int32_t*R,float*D,Posting&p,Meta&meta,const std::string&m,Work&w,Detail*detail=nullptr){
 auto t=detail?Clock::now():Clock::time_point{};std::vector<faiss::idx_t>original(R,R+K);int nc=p.plan(route,original.data(),K,nullptr);require(nc>=0,"all route rows available");std::vector<int32_t>C(p.candidate.begin(),p.candidate.begin()+nc);std::vector<float>cv;cv.reserve(nc);std::vector<Event>events;events.reserve(nc+384);
 for(int id:C){float v=dc(id);require(std::isfinite(v),"finite direct C");cv.push_back(v);events.push_back({id,v,0});}w[0]=nc;
 if(detail){detail->us[0]=std::chrono::duration<double,std::micro>(Clock::now()-t).count();t=Clock::now();}
 std::vector<int>rank(nc);std::iota(rank.begin(),rank.end(),0);std::sort(rank.begin(),rank.end(),[&](int a,int b){return cv[a]<cv[b]||(cv[a]==cv[b]&&a<b);});std::vector<Node>seeds;size_t cap=m.find("384")!=std::string::npos?384:96,used=0;
 if(m=="REP384"){
  std::unordered_set<int>unique;std::vector<Node>representatives;
  for(int id:C){int h=meta.rep.at(id);if(!unique.insert(h).second)continue;float v;auto a=std::find(C.begin(),C.end(),h);auto b=std::find(R,R+K,h);
   if(a!=C.end())v=cv[a-C.begin()];else if(b!=R+K)v=D[b-R];else{v=dc(h);require(std::isfinite(v),"finite representative");events.push_back({h,v,1});++w[1];++used;}representatives.push_back({v,uint32_t(representatives.size()),h});}
  std::sort(representatives.begin(),representatives.end(),[](auto a,auto b){return a.value<b.value||(a.value==b.value&&a.order<b.order);});for(size_t j=0;j<std::min<size_t>(3,representatives.size());++j)seeds.push_back(representatives[j]);
 }else if(m.rfind("NOVEL",0)==0){
  std::unordered_set<int32_t>covered,chosen;for(int z=0;z<3&&z<nc;++z){int best=-1;size_t gain=0;for(size_t j=0;j<std::min<size_t>(12,rank.size());++j){int pos=rank[j],id=C[pos];if(chosen.count(id))continue;std::unordered_set<int32_t>local;for(int k=0;k<g.K;++k){++w[5];int v=g.at(id,k);if(v>=0&&v<g.N&&v!=id&&!vt.get(v)&&!covered.count(v))local.insert(v);}if(best<0||local.size()>gain){best=pos;gain=local.size();}}
   if(best<0)break;int id=C[best];chosen.insert(id);seeds.push_back({cv[best],uint32_t(best),id});for(int k=0;k<g.K;++k){++w[5];int v=g.at(id,k);if(v>=0&&v<g.N)covered.insert(v);}}
 }else{
  std::unordered_set<int>selected;for(int label:route){int row=p.lookup(label,nullptr),best=-1;for(int j=0;j<p.counts[row];++j){int id=p.targets[size_t(row)*p.b+j];auto a=std::find(C.begin(),C.end(),id);if(a==C.end())continue;int pos=a-C.begin();if(best<0||cv[pos]<cv[best])best=pos;}if(best>=0&&selected.insert(C[best]).second)seeds.push_back({cv[best],uint32_t(best),C[best]});}
 }
 w[6]=seeds.size();if(detail){detail->us[1]=std::chrono::duration<double,std::micro>(Clock::now()-t).count();detail->seeds.clear();for(auto a:seeds)detail->seeds.push_back(a.id);t=Clock::now();}
 expansion(dc,g,vt,C,cv,seeds,m=="ONEHOP96",cap,used,events,w);
 if(detail){detail->us[2]=std::chrono::duration<double,std::micro>(Clock::now()-t).count();t=Clock::now();}
 std::vector<Posting::Record>heap;heap.reserve(K);for(int j=0;j<K;++j)heap.push_back({R[j],D[j],uint32_t(j),false});std::make_heap(heap.begin(),heap.end(),Posting::better);
 for(size_t j=0;j<events.size();++j)if(events[j].value<heap.front().distance){std::pop_heap(heap.begin(),heap.end(),Posting::better);heap.back()={events[j].id,events[j].value,uint32_t(K+j),false};std::push_heap(heap.begin(),heap.end(),Posting::better);}
 if(!events.empty()){std::sort(heap.begin(),heap.end(),Posting::better);for(int j=0;j<K;++j){R[j]=heap[j].id;D[j]=heap[j].distance;}}
 require(w[1]+w[2]<=cap&&w[4]<=64*cap,"auxiliary access budget");if(detail){detail->events=std::move(events);detail->us[3]=std::chrono::duration<double,std::micro>(Clock::now()-t).count();}
}
void run(acsg::IndexACSGFlat&idx,const std::vector<float>&q,int L,const std::string&m,Router&r,Posting&p,Backend&aux,Meta&meta,Batch&b,Meter&meter){
 if(m=="GT10"||m=="B32"||m=="REUSE-SQ"){Stats st;e191::run(idx,q,L,m,r,p,aux,b,st);if(m=="REUSE-SQ"){meter.work.resize(b.n);for(size_t i=0;i<b.n;++i){meter.work[i][2]=st.per_query[i*5+2];meter.work[i][7]=st.per_query[i*5];}}return;}
 if(m=="OPT-B32"){Stats st;e194::run_opt(idx,q,L,m,r,p,static_cast<e194::FastBackend&>(aux),b,st);return;}
 idx.acsg.search_L=L;std::vector<std::vector<EnterPoint>>eps(b.n);for(size_t i=0;i<b.n;++i){auto a=r.route(q.data()+i*idx.d);for(int j=0;j<3;++j){b.entries[i*3+j]=a.ids[j];b.profile_distances[i*3+j]=a.distances[j];eps[i].emplace_back(a.ids[j],1.f);}}
 VisitedTable vt(idx.ntotal);std::unique_ptr<DistanceComputer>dc(acsg::storage_distance_computer(idx.storage));std::vector<Neighbor>ret;std::vector<faiss::idx_t>ids(b.k);std::vector<int32_t>cur(b.k);meter.work.resize(b.n);
 for(size_t i=0;i<b.n;++i){dc->set_query(q.data()+i*idx.d);vt.advance();idx.acsg.search_new(*dc,b.k,ids.data(),b.distances.data()+i*b.k,vt,2,eps[i],&ret);for(size_t j=0;j<b.k;++j)cur[j]=ids[j];complete_nav(*dc,*idx.acsg.final_graph,vt,{{b.entries[i*3],b.entries[i*3+1],b.entries[i*3+2]}},b.k,cur.data(),b.distances.data()+i*b.k,p,meta,m,meter.work[i]);std::copy(cur.begin(),cur.end(),b.ids.begin()+i*b.k);}
}
__attribute__((noinline)) double timed(acsg::IndexACSGFlat&idx,const std::vector<float>&q,int L,const std::string&m,Router&r,Posting&p,Backend&aux,Meta&meta,Batch&dest,Meter&meter){auto t=Clock::now();{Batch out(dest.n,dest.k);run(idx,q,L,m,r,p,aux,meta,out,meter);copy_packet(out,dest);asm volatile(""::"g"(dest.ids.data()),"g"(out.ids.data()):"memory");}return seconds(t);}
std::vector<std::string> methods(int L,bool qualify){std::vector<std::string>m={"GT10","B32"};if(L==100||qualify)m.push_back("OPT-B32");if(L==100||L==200||L==400||L==800||qualify)m.push_back("REUSE-SQ");if(L==100||L==200||L==400||qualify)for(auto s:{"ONEHOP96","DIST96","DIST384","NOVEL96","NOVEL384","REP384"})m.push_back(s);return m;}
bool isnav(const std::string&m){return m!="GT10"&&m!="B32"&&m!="OPT-B32"&&m!="REUSE-SQ";}
void audit_nav(acsg::IndexACSGFlat&idx,const std::vector<float>&q,int L,const std::string&m,Posting&p,Meta&meta,const Batch&main,const Batch&final,const Meter&meter,const fs::path&path){
 auto t=Clock::now();std::unique_ptr<DistanceComputer>dc(acsg::storage_distance_computer(idx.storage));VisitedTable vt(idx.ntotal);std::vector<Neighbor>ret;std::vector<faiss::idx_t>ii(main.k);std::vector<float>dd(main.k);gzFile f=gzopen((path/"events.bin.gz").c_str(),"wb1");require(f,"gz candidate evidence");std::array<double,4>stage{};idx.acsg.search_L=L;
 for(size_t i=0;i<main.n;++i){dc->set_query(q.data()+i*idx.d);vt.advance();std::vector<EnterPoint>eps;for(int j=0;j<3;++j)eps.emplace_back(main.entries[i*3+j],1.f);idx.acsg.search_new(*dc,main.k,ii.data(),dd.data(),vt,2,eps,&ret);std::vector<int32_t>rr(ii.begin(),ii.end());for(size_t j=0;j<main.k;++j)require(rr[j]==main.ids[i*main.k+j]&&equal_float(dd[j],main.distances[i*main.k+j]),"native actual main replay");Work w{};Detail de;complete_nav(*dc,*idx.acsg.final_graph,vt,{{main.entries[i*3],main.entries[i*3+1],main.entries[i*3+2]}},main.k,rr.data(),dd.data(),p,meta,m,w,&de);require(w==meter.work[i],"untimed candidate work parity");std::vector<int32_t>linear;std::vector<float>values;merge_linear(main.ids.data()+i*main.k,main.distances.data()+i*main.k,main.k,de.events,linear,values);
  for(size_t j=0;j<main.k;++j)require(rr[j]==final.ids[i*main.k+j]&&linear[j]==rr[j]&&equal_float(values[j],final.distances[i*main.k+j])&&equal_float(dd[j],values[j]),"all-query auxiliary linear oracle");uint32_t h[3]={uint32_t(i),uint32_t(de.events.size()),uint32_t(de.seeds.size())};gzwrite(f,h,sizeof(h));for(auto a:de.events){uint32_t x[3];std::memcpy(&x[0],&a.id,4);std::memcpy(&x[1],&a.value,4);x[2]=a.stage;gzwrite(f,x,sizeof(x));}if(!de.seeds.empty())gzwrite(f,de.seeds.data(),de.seeds.size()*4);for(int j=0;j<4;++j)stage[j]+=de.us[j];
 }require(gzclose(f)==Z_OK,"candidate gzip close");for(auto&x:stage)x/=main.n;fresh_json(path/"oracle.json",{{"status","PASS_ALL_QUERY_LINEAR_MERGE_WORK_PARITY"},{"n",main.n},{"diagnostic_stage_us",stage},{"stage_order",{"C_score","seed_select_and_representative_score","auxiliary_expansion","merge"}},{"diagnostic_not_formal_timer",true},{"seconds",seconds(t)}});
}
void audit_sq(acsg::IndexACSGFlat&idx,const std::vector<float>&q,Backend&aux,const Batch&main,const Batch&final,const fs::path&path){
 std::unique_ptr<DistanceComputer>dc(acsg::storage_distance_computer(idx.storage));
 for(size_t i=0;i<main.n;++i){dc->set_query(q.data()+i*idx.d);std::vector<int32_t>rr(main.ids.begin()+i*main.k,main.ids.begin()+(i+1)*main.k);std::vector<float>dd(main.distances.begin()+i*main.k,main.distances.begin()+(i+1)*main.k);Stats st;aux.complete(*dc,q.data()+i*idx.d,rr.data(),dd.data(),main.k,main.entries.data()+i*3,"REUSE-SQ",st,true);for(size_t j=0;j<main.k;++j)require(rr[j]==final.ids[i*main.k+j]&&equal_float(dd[j],final.distances[i*main.k+j]),"SQ full sort merge oracle");require(st.scans<=2048&&st.exact<=96,"SQ budget");}
 fresh_json(path/"oracle.json",{{"status","PASS_ALL_QUERY_SQ_FULL_SORT"},{"n",main.n}});
}
void diagnosis(acsg::IndexACSGFlat&idx,const std::vector<float>&q,const json&c,Router&r,Posting&p,Meta&meta,Backend&aux,const fs::path&root){
 auto t=Clock::now();auto G=read_gt(c.at("test_gt"),idx.ntotal);size_t n=c.at("queries").at("n");gzFile query=gzopen((root/"query_diagnosis.csv.gz").c_str(),"wb1"),nodes=gzopen((root/"C_nodes.csv.gz").c_str(),"wb1"),probes=gzopen((root/"single_seed.csv.gz").c_str(),"wb1");require(query&&nodes&&probes,"diagnostic outputs");
 gzprintf(query,"K,L,query,main_hits,missing,missing_evaluated,missing_rejected,missing_frontier_adjacent,missing_no_frontier_edge,missing_zero_indegree,missing_expanded_parent_unseen,main_scores,main_expanded,C_count,C_missing,C_main_seen,C_mean_indegree,C_mean_outdegree,GT_mean_indegree,GT_mean_outdegree,SQ_pool_missing,SQ_scan_missing,SQ_short_missing,SQ_rescued\n");
 gzprintf(nodes,"K,L,query,target,C_rank,score,indegree,outdegree,unseen_outneighbors,is_GT,main_seen\n");gzprintf(probes,"K,L,query,seed,C_rank,indegree,outdegree,unseen_outneighbors,extra_exact,slots,expanded,new_hits_vs_B32,lost_vs_B32,net_vs_B32\n");
 std::unique_ptr<DistanceComputer>dc(acsg::storage_distance_computer(idx.storage));VisitedTable vt(idx.ntotal),native_vt(idx.ntotal);std::vector<Neighbor>ret;uint64_t rows=0,parity=0,violations=0;
 for(int K:{1,100})for(int L:{100,200,400}){idx.acsg.search_L=L;Batch main(n,K);Method method;method.route=&r;method.family="GT10";run_batch(idx,q,L,method,main);
  for(size_t i=0;i<n;++i){dc->set_query(q.data()+i*idx.d);vt.advance();std::vector<EnterPoint>eps;for(int j=0;j<3;++j)eps.emplace_back(main.entries[i*3+j],1.f);Replay rec;replay_search(*idx.acsg.final_graph,*dc,vt,L,ret,eps,rec);for(int j=0;j<K;++j)require(ret[j].id==main.ids[i*K+j]&&equal_float(ret[j].distance,main.distances[i*K+j]),"all-query copied kernel native parity");++parity;
   std::unordered_set<int>gs(G.begin()+i*100,G.begin()+i*100+K),returned(main.ids.begin()+i*K,main.ids.begin()+(i+1)*K),scored(rec.scored.begin(),rec.scored.end()),expanded(rec.expanded.begin(),rec.expanded.end()),rejected(rec.rejected.begin(),rec.rejected.end()),missing,boundary;for(int x:gs)if(!returned.count(x))missing.insert(x);
   for(int x:rec.scored)if(!expanded.count(x))for(int j=0;j<idx.acsg.final_graph->K;++j){int y=idx.acsg.final_graph->at(x,j);if(missing.count(y)&&!scored.count(y))boundary.insert(y);}
   uint64_t unexpected=0;for(int x:rec.expanded)for(int j=0;j<idx.acsg.final_graph->K;++j){int y=idx.acsg.final_graph->at(x,j);if(missing.count(y)&&!scored.count(y))++unexpected;}violations+=unexpected;require(unexpected==0,"expanded node all valid edges evaluated");
   int evaluated=0,rej=0,zero=0;double gi=0,go=0;for(int x:missing){evaluated+=scored.count(x);rej+=rejected.count(x);zero+=meta.in[x]==0;}for(int x:gs){gi+=meta.in[x];go+=meta.out[x];}
   std::vector<faiss::idx_t>R(main.ids.begin()+i*K,main.ids.begin()+(i+1)*K);int nc=p.plan({{main.entries[i*3],main.entries[i*3+1],main.entries[i*3+2]}},R.data(),K,nullptr);std::vector<int32_t>C(p.candidate.begin(),p.candidate.begin()+nc);std::vector<float>cv;for(int x:C)cv.push_back((*dc)(x));std::vector<int>rank(nc);std::iota(rank.begin(),rank.end(),0);std::sort(rank.begin(),rank.end(),[&](int a,int b){return cv[a]<cv[b]||(cv[a]==cv[b]&&a<b);});std::vector<int>unseen(nc),ranks(nc);for(int j=0;j<nc;++j)ranks[rank[j]]=j;int cm=0,cs=0;double ci=0,co=0;
   for(int j=0;j<nc;++j){int x=C[j];std::unordered_set<int>u;for(int slot=0;slot<idx.acsg.final_graph->K;++slot){int y=idx.acsg.final_graph->at(x,slot);if(y>=0&&y<idx.ntotal&&y!=x&&!vt.get(y))u.insert(y);}unseen[j]=u.size();cm+=missing.count(x);cs+=scored.count(x);ci+=meta.in[x];co+=meta.out[x];gzprintf(nodes,"%d,%d,%zu,%d,%d,%.9g,%u,%u,%d,%d,%d\n",K,L,i,x,ranks[j],cv[j],meta.in[x],unsigned(meta.out[x]),unseen[j],int(gs.count(x)),int(scored.count(x)));}
   std::vector<int32_t>sqR(main.ids.begin()+i*K,main.ids.begin()+(i+1)*K);std::vector<float>sqD(main.distances.begin()+i*K,main.distances.begin()+(i+1)*K);Stats sqst;aux.complete(*dc,q.data()+i*idx.d,sqR.data(),sqD.data(),K,main.entries.data()+i*3,"REUSE-SQ",sqst,true);std::unordered_set<int>pool(aux.pool.begin(),aux.pool.end()),scan(aux.scanned.begin(),aux.scanned.end()),shortlist(aux.candidates.begin(),aux.candidates.end()),sqfinal(sqR.begin(),sqR.end());int pm=0,sm=0,shm=0,sr=0;for(int x:missing){pm+=pool.count(aux.idblock[x]);sm+=scan.count(aux.idblock[x]);shm+=shortlist.count(x);sr+=sqfinal.count(x);}
   gzprintf(query,"%d,%d,%zu,%zu,%zu,%d,%d,%zu,%zu,%d,%llu,%zu,%zu,%d,%d,%d,%.9g,%.9g,%.9g,%.9g,%d,%d,%d,%d\n",K,L,i,gs.size()-missing.size(),missing.size(),evaluated,rej,boundary.size(),missing.size()-evaluated-boundary.size(),zero,(unsigned long long)unexpected,rec.scored.size(),rec.expanded.size(),nc,cm,cs,nc?ci/nc:0,nc?co/nc:0,gi/K,go/K,pm,sm,shm,sr);++rows;
   if(L==200&&i<64){std::vector<Event>direct;for(int j=0;j<nc;++j)direct.push_back({C[j],cv[j],0});std::vector<int32_t>base;std::vector<float>bv;merge_linear(main.ids.data()+i*K,main.distances.data()+i*K,K,direct,base,bv);std::set<int>bh;for(int x:base)if(gs.count(x))bh.insert(x);
    for(size_t j=0;j<std::min<size_t>(6,rank.size());++j){int pos=rank[j],x=C[pos];auto ev=direct;Work w{};expansion(*dc,*idx.acsg.final_graph,vt,C,cv,{{cv[pos],uint32_t(pos),x}},false,384,0,ev,w);std::vector<int32_t>fi;std::vector<float>fv;merge_linear(main.ids.data()+i*K,main.distances.data()+i*K,K,ev,fi,fv);std::set<int>fh;for(int y:fi)if(gs.count(y))fh.insert(y);int gain=0,loss=0;for(int y:fh)gain+=!bh.count(y);for(int y:bh)loss+=!fh.count(y);gzprintf(probes,"%d,%d,%zu,%d,%zu,%u,%u,%d,%llu,%llu,%llu,%d,%d,%d\n",K,L,i,x,j,meta.in[x],unsigned(meta.out[x]),unseen[pos],(unsigned long long)w[2],(unsigned long long)w[4],(unsigned long long)w[3],gain,loss,gain-loss);}
   }
  }
 }
 require(gzclose(query)==Z_OK&&gzclose(nodes)==Z_OK&&gzclose(probes)==Z_OK,"diagnostic gzip closes");fresh_json(root/"diagnosis_complete.json",{{"status","PASS_DETAILED_MECHANISM_DIAGNOSIS"},{"query_K_L_rows",rows},{"native_replay_bit_parity",parity},{"unseen_target_from_expanded_parent",violations},{"GT_used_only_untimed",true},{"seconds",seconds(t)}});
}
json bench(const json&c,bool qualify){check_threads(c);auto started=Clock::now();fs::path root=c.at("output_dir");fresh_dir(root);fresh_json(root/"config.json",c);json binding;auto idx=load_index(c,binding);Matrix qm(c.at("queries"));auto q=qm.copy();Router router(c.at("router"),idx->d,idx->ntotal);Posting post(c.at("table"),idx->ntotal);e194::FastBackend aux(c);Meta meta(c,*idx->acsg.final_graph,post);fresh_json(root/"environment.json",{{"threads",process_threads()},{"cpu",15},{"binding",binding},{"timer","complete Batch lifecycle + route/main/C/selection/auxiliary/merge/copy/destruction"},{"GT_read_by_timed_path",false}});
 json results=json::array();int ordinal=0;size_t batches=0;std::vector<int>ls=qualify?std::vector<int>{200}:c.at("Ls").get<std::vector<int>>();int reps=qualify?1:3;
 for(int K:{1,100})for(int L:ls){auto ms=methods(L,qualify);std::vector<std::unique_ptr<Batch>>first(ms.size());std::vector<Meter>meters(ms.size());std::vector<json>rounds(ms.size(),json::array());Batch dest(qm.n,K);
  for(int rep=0;rep<reps;++rep)for(size_t off=0;off<ms.size();++off){size_t mi=(ordinal+rep+off)%ms.size();auto&m=ms[mi];check_threads(c);if(!rep){Batch warm(std::min<size_t>(128,qm.n),K);Meter wm;run(*idx,q,L,m,router,post,aux,meta,warm,wm);}Meter meter;double wall=timed(*idx,q,L,m,router,post,aux,meta,dest,meter);check_threads(c);++batches;validate(dest,idx->ntotal);fs::path point=root/("k"+std::to_string(K))/(m+"_L"+std::to_string(L));auto hash=packet_sha(dest);
   if(!rep){first[mi]=std::make_unique<Batch>(dest);meters[mi]=meter;dest.save(point/"raw",false);if(!meter.work.empty())write_raw(point/"work.u64",meter.work);}else{all_same(*first[mi],dest);require(meters[mi].work==meter.work,"three-round work parity");}
   json a={{"round",rep},{"wall_seconds",wall},{"qps",qm.n/wall},{"packet_sha256",hash},{"threads",1}};rounds[mi].push_back(a);fresh_json(point/("round"+std::to_string(rep)+".json"),a);std::cout<<json({{"dataset",c.at("dataset")},{"window",c.at("window")},{"K",K},{"L",L},{"method",m},{"round",rep},{"qps",qm.n/wall}}).dump()<<std::endl;
  }
  auto&main=*first[0];for(size_t mi=0;mi<ms.size();++mi){const auto&m=ms[mi];fs::path point=root/("k"+std::to_string(K))/(m+"_L"+std::to_string(L));if(m=="B32"||m=="OPT-B32")audit_merge(*idx,q,main,*first[mi],post);if(m=="REUSE-SQ")audit_sq(*idx,q,aux,main,*first[mi],point);if(isnav(m))audit_nav(*idx,q,L,m,post,meta,main,*first[mi],meters[mi],point);
   std::vector<double>w;for(auto a:rounds[mi])w.push_back(a.at("wall_seconds"));std::sort(w.begin(),w.end());std::array<double,8>mean{};for(auto a:meters[mi].work)for(int j=0;j<8;++j)mean[j]+=double(a[j])/qm.n;json a={{"dataset",c.at("dataset")},{"window",c.at("window")},{"K",K},{"L",L},{"method",m},{"n",qm.n},{"qps",qm.n/w[w.size()/2]},{"rounds",rounds[mi]},{"mean_work",mean},{"work_order",{"C_exact","representative_exact","expansion_exact","expanded","neighbor_slots","selection_slots","seeds","SQ_scanned"}},{"result_dir",point.string()},{"all_round_bits_equal",true}};fresh_json(point/"result.json",a);results.push_back(a);
  }++ordinal;
 }
 fresh_json(root/"performance_complete.json",{{"status",qualify?"PASS_QUALIFICATION":"PASS_FORMAL_PERFORMANCE"},{"results",results},{"points",results.size()},{"batches",batches},{"seconds",seconds(started)}});
 if(!qualify)diagnosis(*idx,q,c,router,post,meta,aux,root);
 json done={{"status",qualify?"PASS_E195_QUALIFICATION":"PASS_E195_DATASET_WINDOW"},{"dataset",c.at("dataset")},{"window",c.at("window")},{"points",results.size()},{"batches",batches},{"seconds",seconds(started)}};fresh_json(root/"complete.json",done);return done;
}
}
int e195_embedded_main(int argc,char**argv){try{e195::require(argc==3,"mode config");e195::bench(e195::read_json(argv[2]),std::string(argv[1])=="qualification");return 0;}catch(const std::exception&e){std::cerr<<"FATAL E195 "<<e.what()<<std::endl;return 2;}}

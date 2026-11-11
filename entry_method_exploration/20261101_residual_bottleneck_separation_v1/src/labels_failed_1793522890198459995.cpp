#include "e195.inc"
#include <fstream>
namespace e197 {
using namespace e195;
#include "cached_search.inc"
constexpr int F=104, META=11;
struct Outcome {std::vector<Event> events;Work work{};std::vector<int32_t> ids;std::vector<float> values;};
void merge_heap(const int32_t*R,const float*D,int K,const std::vector<Event>&events,std::vector<int32_t>&I,std::vector<float>&V){
 std::vector<Posting::Record>h;h.reserve(K);for(int j=0;j<K;++j)h.push_back({R[j],D[j],uint32_t(j),false});std::make_heap(h.begin(),h.end(),Posting::better);
 for(size_t j=0;j<events.size();++j)if(events[j].value<h.front().distance){std::pop_heap(h.begin(),h.end(),Posting::better);h.back()={events[j].id,events[j].value,uint32_t(K+j),false};std::push_heap(h.begin(),h.end(),Posting::better);}
 if(!events.empty())std::sort(h.begin(),h.end(),Posting::better);I.clear();V.clear();for(auto a:h){I.push_back(a.id);V.push_back(a.distance);}
}
json subset_table(const json&c){
 const auto t=Clock::now();fs::path out=c.at("q8_table");require(!fs::exists(out),"fresh Q8 table");fs::create_directories(out.parent_path());
 auto labels=read_raw<int32_t>(c.at("router").at("ids"));auto src=fs::path(c.at("source_dir"));auto tq=read_raw<int32_t>(src/"token_queries.i32"),tt=read_raw<int32_t>(src/"token_targets.i32");auto route=read_raw<int32_t>(fs::path(c.at("teacher_dir"))/"raw/entry_ids.i32");require(tq.size()==tt.size()&&route.size()==16000*3,"bound original TRAIN source");
 std::unordered_map<int,int>slot;for(size_t i=0;i<labels.size();++i)slot[labels[i]]=i;
 std::map<std::pair<int,int>,std::vector<uint32_t>>inc;uint32_t n=0;
 for(size_t j=0;j<tq.size();++j)if(tq[j]<8000){require(tq[j]>=0,"source query bounds");for(int z=0;z<3;++z)inc[{slot.at(route[tq[j]*3+z]),tt[j]}].push_back(n);++n;}
 std::vector<Edge>edges;for(auto&a:inc)edges.push_back({a.first.first,a.first.second,std::move(a.second),false});Rows rows(labels.size());std::vector<uint8_t>covered(n,0);
 for(int cap:{8,16,32})extend(edges,covered,rows,cap);export_table(out,labels,rows,c.at("base").at("n"),32);
 json receipt={{"status","PASS_Q8_NESTED_UNIT_TOKEN_TABLE"},{"fit_original_rows",{0,8000}},{"original_source_tokens",tq.size()},{"subset_tokens",n},{"covered_tokens",std::count(covered.begin(),covered.end(),uint8_t(1))},{"table",out.string()},{"seconds",seconds(t)},{"new_GT",false},{"new_ANN",false}};
 fresh_json(out.parent_path()/"compile.json",receipt);return receipt;
}
struct Features {
 const acsg::Graph<int32_t>&g;const float*base;int d;const std::vector<uint32_t>&in;const std::vector<uint16_t>&out;const Posting&post;
 std::unordered_map<int,std::array<float,34>>nodes;
 Features(const acsg::Graph<int32_t>&gg,const float*bb,int dd,const Meta&m,const Posting&p):g(gg),base(bb),d(dd),in(m.in),out(m.out),post(p){
  std::set<int>keys;for(size_t j=0;j<p.H;++j)for(int z=0;z<p.counts[j];++z)keys.insert(p.targets[j*p.b+z]);
  for(int id:keys){std::array<float,34>a{};project(base+size_t(id)*d,a.data());for(int j=0;j<d;++j)a[32]+=base[size_t(id)*d+j]*base[size_t(id)*d+j];int used=0;
   for(int z=0;z<g.K&&used<4;++z){int v=g.at(id,z);if(v<0||v>=g.N||v==id)continue;float b[16]{};project(base+size_t(v)*d,b);for(int j=0;j<16;++j)a[16+j]+=b[j];for(int j=0;j<d;++j)a[33]+=base[size_t(v)*d+j]*base[size_t(v)*d+j];++used;}
   if(used)for(int j=16;j<32;++j)a[j]/=used;if(used)a[33]/=used;nodes.emplace(id,a);
  }
 }
 void project(const float*x,float*y)const{std::fill(y,y+16,0);for(int j=0;j<d;++j){uint32_t h=uint32_t(j)*2654435761u+19720261101ull;y[(h>>16)&15]+=(h&0x80000000u)?x[j]:-x[j];}float scale=std::sqrt(16.f/d);for(int j=0;j<16;++j)y[j]*=scale;}
 std::array<float,F> row(const float*q,const RouteData&route,const VisitedTable&vt,const std::vector<int32_t>&C,const std::vector<float>&cv,int rank,int pos,const float*D,int K,int L,bool embed=true)const{
  std::array<float,F>a{};int id=C[pos];float low=*std::min_element(cv.begin(),cv.end()),high=*std::max_element(cv.begin(),cv.end());auto pr=route.distances;std::sort(pr.begin(),pr.end());float norm=0;for(int j=0;j<d;++j)norm+=q[j]*q[j];int unseen=0;for(int z=0;z<g.K;++z){int v=g.at(id,z);if(v>=0&&v<g.N&&v!=id&&!vt.get(v))++unseen;}
  a[0]=float(rank)/std::max<size_t>(1,C.size());a[1]=cv[pos];a[2]=cv[pos]-low;a[3]=cv[pos]-D[0];a[4]=cv[pos]-D[K-1];a[5]=high-low;a[6]=D[K-1]-D[0];a[7]=pr[0];a[8]=pr[1]-pr[0];a[9]=pr[2]-pr[0];a[10]=norm;a[11]=vt.get(id);a[12]=std::log1p(in[id]);a[13]=std::log1p(out[id]);a[14]=float(unseen)/g.K;a[15]=C.size()/96.f;a[16]=K/100.f;a[17]=L/400.f;
  for(int j=0;j<3;++j){int slot=post.lookup(route.ids[j],nullptr);
   a[18+j]=std::find(post.targets.begin()+slot*post.b,post.targets.begin()+slot*post.b+post.counts[slot],id)!=post.targets.begin()+slot*post.b+post.counts[slot];
  }
  auto&v=nodes.at(id);a[21]=v[32];a[22]=v[33];a[23]=rank==0;
  if(embed){float qp[16];project(q,qp);for(int j=0;j<16;++j){a[24+j]=qp[j];a[40+j]=v[j];a[56+j]=qp[j]*v[j];a[72+j]=v[16+j];a[88+j]=qp[j]*v[16+j];}}
  for(float x:a)require(std::isfinite(x),"finite deployable features");return a;
 }
};
struct Context {
 std::unique_ptr<acsg::IndexACSGFlat>idx;std::unique_ptr<Router>router;std::unique_ptr<Posting>post,reference;std::unique_ptr<Meta>meta;std::unique_ptr<Features>features;json binding;
 Context(const json&c){idx=load_index(c,binding);router=std::make_unique<Router>(c.at("router"),idx->d,idx->ntotal);post=std::make_unique<Posting>(c.at("q8_table"),idx->ntotal);reference=std::make_unique<Posting>(c.at("table"),idx->ntotal);meta=std::make_unique<Meta>(c,*idx->acsg.final_graph,*reference);auto*flat=dynamic_cast<faiss::IndexFlat*>(idx->storage);features=std::make_unique<Features>(*idx->acsg.final_graph,flat->get_xb(),idx->d,*meta,*post);}
};
std::vector<int> ranks(const std::vector<float>&cv){std::vector<int>x(cv.size());std::iota(x.begin(),x.end(),0);std::sort(x.begin(),x.end(),[&](int a,int b){return cv[a]<cv[b]||(cv[a]==cv[b]&&a<b);});return x;}
void main_search(Context&x,const float*q,int K,int L,const RouteData&r,VisitedTable&vt,std::vector<int32_t>&R,std::vector<float>&D,std::vector<Neighbor>&ret,DistanceComputer&dc,Replay*rec=nullptr,std::vector<float>*cache=nullptr){
 x.idx->acsg.search_L=L;dc.set_query(q);vt.advance();std::vector<EnterPoint>eps;for(int id:r.ids)eps.emplace_back(id,1.f);R.resize(K);D.resize(K);
 if(rec){rec->scored.clear();rec->expanded.clear();rec->rejected.clear();cached_search(*x.idx->acsg.final_graph,dc,vt,L,ret,eps,*rec,*cache);for(int j=0;j<K;++j){R[j]=ret[j].id;D[j]=ret[j].distance;}}
 else{std::vector<faiss::idx_t>I(K);x.idx->acsg.search_new(dc,K,I.data(),D.data(),vt,2,eps,&ret);for(int j=0;j<K;++j)R[j]=I[j];}
}
void candidates(Posting&p,const RouteData&r,const std::vector<int32_t>&R,DistanceComputer&dc,std::vector<int32_t>&C,std::vector<float>&cv){
 std::vector<faiss::idx_t>rr(R.begin(),R.end());int nc=e194::fast_plan(p,r.ids,rr.data(),R.size());require(nc>=0,"all route rows");C.assign(p.candidate.begin(),p.candidate.begin()+nc);cv.clear();for(int id:C){float v=dc(id);require(std::isfinite(v),"finite direct score");cv.push_back(v);}
}
std::vector<Node> distance_seeds(const Posting&p,const RouteData&r,const std::vector<int32_t>&C,const std::vector<float>&cv){
 std::vector<Node>s;std::set<int>seen;for(int label:r.ids){int row=p.lookup(label,nullptr),best=-1;for(int j=0;j<p.counts[row];++j){int id=p.targets[row*p.b+j];auto a=std::find(C.begin(),C.end(),id);if(a!=C.end()){int pos=a-C.begin();if(best<0||cv[pos]<cv[best])best=pos;}}if(best>=0&&seen.insert(C[best]).second)s.push_back({cv[best],uint32_t(best),C[best]});}return s;
}
Outcome expand(Context&x,DistanceComputer&dc,const VisitedTable&vt,const std::vector<int32_t>&R,const std::vector<float>&D,const std::vector<int32_t>&C,const std::vector<float>&cv,const std::vector<Node>&seeds,int mode,int cap,const Replay*rec=nullptr,const std::vector<float>*cache=nullptr){
 Outcome o;o.events.reserve(C.size()+cap);for(size_t j=0;j<C.size();++j)o.events.push_back({C[j],cv[j],0});o.work[0]=C.size();o.work[6]=seeds.size();
 if(mode==0){expansion(dc,*x.idx->acsg.final_graph,vt,C,cv,seeds,false,cap,0,o.events,o.work);}
 else{
  std::unordered_map<int,float>known;for(size_t j=0;j<C.size();++j)known[C[j]]=cv[j];std::unordered_set<int>seen,expanded,main_expanded;if(rec)main_expanded.insert(rec->expanded.begin(),rec->expanded.end());
  std::priority_queue<Node,std::vector<Node>,MinNode>front;uint32_t arrival=0;for(auto s:seeds){front.push(s);seen.insert(s.id);main_expanded.erase(s.id);}auto&g=*x.idx->acsg.final_graph;
  while(!front.empty()&&o.work[2]<uint64_t(cap)&&o.work[4]<uint64_t(64*cap)){auto a=front.top();front.pop();if(!expanded.insert(a.id).second)continue;++o.work[3];
   for(int z=0;z<g.K&&o.work[2]<uint64_t(cap)&&o.work[4]<uint64_t(64*cap);++z){++o.work[4];int id=g.at(a.id,z);if(id<0||id>=g.N||main_expanded.count(id)||seen.count(id))continue;auto k=known.find(id);float v;
    if(k!=known.end()){v=k->second;++o.work[7];}
    else if(vt.get(id)){if(mode!=2)continue;require(cache,"actual main score cache");v=cache->at(id);++o.work[7];}
    else{v=dc(id);require(std::isfinite(v),"finite new auxiliary score");o.events.push_back({id,v,2});++o.work[2];}
    seen.insert(id);front.push({v,arrival++,id});
   }
  }
 }
 merge_heap(R.data(),D.data(),R.size(),o.events,o.ids,o.values);require(o.work[2]<=uint64_t(cap)&&o.work[4]<=uint64_t(64*cap),"explicit action budgets");return o;
}
int hits(const std::vector<int32_t>&ids,const std::unordered_set<int>&G){int n=0;for(int id:ids)n+=G.count(id);return n;}
json labels(const json&c){
 check_threads(c);auto started=Clock::now();fs::path root=c.at("output_dir"),scratch=c.at("scratch");fresh_dir(root);fs::create_directories(scratch);Context x(c);Matrix qm(c.at("queries"));auto Q=qm.copy();auto GT=read_gt(c.at("test_gt"),x.idx->ntotal);gzFile meta=gzopen((root/"labels.i32.gz").c_str(),"wb1");require(meta,"label gzip");std::ofstream features(scratch/"features.f32",std::ios::binary);require(bool(features),"transient feature stream");
 auto dc=std::unique_ptr<DistanceComputer>(acsg::storage_distance_computer(x.idx->storage));VisitedTable vt(x.idx->ntotal);std::vector<Neighbor>ret;std::vector<int32_t>R,C;std::vector<float>D,cv;uint64_t rows=0,checks=0;EVP_MD_CTX*dig=EVP_MD_CTX_new();EVP_DigestInit_ex(dig,EVP_sha256(),nullptr);
 for(int K:{1,100})for(size_t i=0;i<qm.n;++i){const float*q=Q.data()+i*x.idx->d;auto route=x.router->route(q);main_search(x,q,K,200,route,vt,R,D,ret,*dc);candidates(*x.post,route,R,*dc,C,cv);auto rank=ranks(cv);std::vector<Event>direct;for(size_t j=0;j<C.size();++j)direct.push_back({C[j],cv[j],0});std::vector<int32_t>B;std::vector<float>BV;merge_heap(R.data(),D.data(),K,direct,B,BV);std::unordered_set<int>G(GT.begin()+i*100,GT.begin()+i*100+K),bh;for(int id:B)if(G.count(id))bh.insert(id);
  for(size_t j=0;j<rank.size();++j){int pos=rank[j];auto o=expand(x,*dc,vt,R,D,C,cv,{{cv[pos],uint32_t(pos),C[pos]}},0,384);int gain=0,loss=0;std::unordered_set<int>fh;for(int id:o.ids)if(G.count(id))fh.insert(id);for(int id:fh)gain+=!bh.count(id);for(int id:bh)loss+=!fh.count(id);
   auto f=x.features->row(q,route,vt,C,cv,j,pos,D.data(),K,200);for(int z=0;z<3;++z){int rr=x.post->lookup(route.ids[z],nullptr);f[18+z]=std::find(x.post->targets.begin()+rr*x.post->b,x.post->targets.begin()+rr*x.post->b+x.post->counts[rr],C[pos])!=x.post->targets.begin()+rr*x.post->b+x.post->counts[rr];}
   int32_t h[META]={int32_t(i),K,C[pos],int32_t(j),int32_t(bh.size()),gain,loss,gain-loss,int32_t(o.work[2]),int32_t(o.work[4]),int32_t(o.work[3])};gzwrite(meta,h,sizeof(h));features.write((char*)f.data(),sizeof(f));EVP_DigestUpdate(dig,o.ids.data(),o.ids.size()*4);EVP_DigestUpdate(dig,o.values.data(),o.values.size()*4);
   if(i<8&&j<2){std::vector<int32_t>I;std::vector<float>V;merge_linear(R.data(),D.data(),K,o.events,I,V);require(I==o.ids&&V.size()==o.values.size()&&!std::memcmp(V.data(),o.values.data(),V.size()*4),"independent linear label oracle");++checks;}
   ++rows;
  }
  if(i%128==0)std::cout<<json{{"stage","labels"},{"dataset",c.at("dataset")},{"K",K},{"query",i},{"rows",rows},{"seconds",seconds(started)}}.dump()<<std::endl;
 }
 features.close();require(gzclose(meta)==Z_OK,"label close");unsigned char hash[32];unsigned int sz;EVP_DigestFinal_ex(dig,hash,&sz);EVP_MD_CTX_free(dig);std::ostringstream out;for(auto b:hash)out<<std::hex<<std::setw(2)<<std::setfill('0')<<int(b);
 json result={{"status","PASS_ACTUAL_SINGLE_SEED_LABELS"},{"dataset",c.at("dataset")},{"queries",qm.n},{"rows",rows},{"feature_count",F},{"metadata_int32",META},{"K",{1,100}},{"L",200},{"cap",384},{"linear_checks",checks},{"output_stream_sha256",out.str()},{"native_process_seconds",seconds(started)},{"threads",process_threads()},{"formal_QPS",nullptr}};fresh_json(root/"complete.json",result);return result;
}
}
int main(int argc,char**argv){try{using namespace e197;require(argc==3,"mode config");auto c=read_json(argv[2]);std::string mode=argv[1];json v;if(mode=="subset")v=subset_table(c);else if(mode=="labels")v=labels(c);else throw std::runtime_error("unknown mode");std::cout<<v.dump()<<std::endl;return 0;}catch(const std::exception&e){std::cerr<<"FATAL E197 "<<e.what()<<std::endl;return 2;}}

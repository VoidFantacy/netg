#include "e197.inc"
namespace e198 {
using namespace e197;
constexpr int MI=14, XF=106;
struct Cached {
 Context& x;const float*q;const RouteData&r;const VisitedTable&vt;
 const std::vector<int32_t>&C;const std::vector<float>&cv;const std::vector<float>&D;
 int K,L;float low;std::array<float,F>shared{};std::array<float,12>gate{};std::array<float,25>query{};
 Cached(Context&xx,const float*qq,const RouteData&rr,const VisitedTable&vv,const std::vector<int32_t>&cc,const std::vector<float>&dd,const std::vector<float>&mainD,int kk,int ll,bool encode=true):x(xx),q(qq),r(rr),vt(vv),C(cc),cv(dd),D(mainD),K(kk),L(ll){
  low=C.empty()?D[0]:*std::min_element(cv.begin(),cv.end());float high=C.empty()?D[0]:*std::max_element(cv.begin(),cv.end());auto p=r.distances;std::sort(p.begin(),p.end());float norm=0;for(int j=0;j<x.idx->d;++j)norm+=q[j]*q[j];
  shared[5]=high-low;shared[6]=D[K-1]-D[0];shared[7]=p[0];shared[8]=p[1]-p[0];shared[9]=p[2]-p[0];shared[10]=norm;shared[15]=C.size()/96.f;shared[16]=K/100.f;shared[17]=L/400.f;
  int si[9]={5,6,7,8,9,10,15,16,17};for(int j=0;j<9;++j){query[16+j]=shared[si[j]];gate[j]=shared[si[j]];}gate[9]=low-D[0];gate[10]=low-D[K-1];gate[11]=D[0];if(encode)project_query();
 }
 void project_query(){x.features->project(q,shared.data()+24);for(int j=0;j<16;++j)query[j]=shared[24+j];}
 std::array<float,F>row(int rank,int pos,bool heavy=true)const{
  auto a=shared;int id=C[pos];
  a[0]=float(rank)/std::max<size_t>(1,C.size());a[1]=cv[pos];a[2]=cv[pos]-low;a[3]=cv[pos]-D[0];a[4]=cv[pos]-D[K-1];a[11]=vt.get(id);a[12]=std::log1p(x.meta->in[id]);a[13]=std::log1p(x.meta->out[id]);
  if(heavy){int unseen=0;auto&g=*x.idx->acsg.final_graph;for(int z=0;z<g.K;++z){int v=g.at(id,z);if(v>=0&&v<g.N&&v!=id&&!vt.get(v))++unseen;}a[14]=float(unseen)/g.K;}
  for(int j=0;j<3;++j){int s=x.post->lookup(r.ids[j],nullptr);a[18+j]=std::find(x.post->targets.begin()+s*x.post->b,x.post->targets.begin()+s*x.post->b+x.post->counts[s],id)!=x.post->targets.begin()+s*x.post->b+x.post->counts[s];}
  auto&v=x.features->nodes.at(id);a[21]=v[32];a[22]=v[33];a[23]=rank==0;
  for(int j=0;j<16;++j){a[40+j]=v[j];a[56+j]=shared[24+j]*v[j];a[72+j]=v[16+j];a[88+j]=shared[24+j]*v[16+j];}return a;
 }
};
json make_labels(const json&c){
 check_threads(c);auto started=Clock::now();fs::path root=c.at("output_dir");fresh_dir(root);fresh_json(root/"config.json",c);Context x(c);Matrix qm(c.at("queries"));auto Q=qm.copy();auto GT=read_gt(c.at("test_gt"),x.idx->ntotal);auto dc=std::unique_ptr<DistanceComputer>(acsg::storage_distance_computer(x.idx->storage));VisitedTable vt(x.idx->ntotal);std::vector<Neighbor>ret;
 std::vector<int32_t>nodeids;for(auto&a:x.features->nodes)nodeids.push_back(a.first);std::sort(nodeids.begin(),nodeids.end());std::vector<float>nodevalues;for(int id:nodeids){auto&a=x.features->nodes.at(id);nodevalues.insert(nodevalues.end(),a.begin(),a.end());}write_raw(root/"nodes.i32",nodeids);write_raw(root/"nodes.f32",nodevalues);
 int K=c.at("K"),L=c.at("L");gzFile data=gzopen((root/"labels.bin.gz").c_str(),"wb3"),gate=gzopen((root/"gate.f32.gz").c_str(),"wb3");require(data&&gate,"persistent label streams");uint64_t rows=0,checks=0;std::vector<int32_t>R,C;std::vector<float>D,cv;
 for(size_t i=0;i<qm.n;++i){auto*q=Q.data()+i*x.idx->d;auto route=x.router->route(q);main_search(x,q,K,L,route,vt,R,D,ret,*dc);candidates(*x.post,route,R,*dc,C,cv);auto rank=ranks(cv);Cached cache(x,q,route,vt,C,cv,D,K,L);gzwrite(gate,cache.gate.data(),48);
  auto direct=expand(x,*dc,vt,R,D,C,cv,{},0,0);std::unordered_set<int>G(GT.begin()+i*100,GT.begin()+i*100+K),bh;for(int id:direct.ids)if(G.count(id))bh.insert(id);
  for(size_t j=0;j<rank.size();++j){int pos=rank[j];auto f=cache.row(j,pos);if(i<4){auto ref=x.features->row(q,route,vt,C,cv,j,pos,D.data(),K,L);require(!std::memcmp(f.data(),ref.data(),F*4),"cached feature exact parity");++checks;}
   int32_t m[MI]={int32_t(i),C[pos],int32_t(j),int32_t(bh.size())};float values[XF];std::copy(f.begin(),f.end(),values);
   for(int b=0;b<2;++b){int cap=b?384:96;auto t=Clock::now();auto o=expand(x,*dc,vt,R,D,C,cv,{{cv[pos],uint32_t(pos),C[pos]}},0,cap);values[104+b]=seconds(t)*1e6;std::unordered_set<int>fh;for(int id:o.ids)if(G.count(id))fh.insert(id);int gain=0,loss=0;for(int id:fh)gain+=!bh.count(id);for(int id:bh)loss+=!fh.count(id);int z=4+b*4;m[z]=gain;m[z+1]=loss;m[z+2]=o.work[2];m[z+3]=o.work[4];m[12+b]=o.work[3];
    if(i<4&&j<2){std::vector<int32_t>I;std::vector<float>V;merge_linear(R.data(),D.data(),K,o.events,I,V);require(I==o.ids&&!std::memcmp(V.data(),o.values.data(),K*4),"single action linear oracle");}
   }require(gzwrite(data,m,sizeof(m))==sizeof(m)&&gzwrite(data,values,sizeof(values))==sizeof(values),"label stream full write");++rows;
  }
  if(i%256==0)std::cout<<json{{"stage","labels"},{"dataset",c.at("dataset")},{"K",K},{"L",L},{"query",i},{"rows",rows},{"seconds",seconds(started)}}.dump()<<std::endl;
 }
 require(gzclose(data)==Z_OK&&gzclose(gate)==Z_OK,"label streams close");json result={{"status","PASS_STATE_MATCHED_TWO_BUDGET_LABELS"},{"rows",rows},{"queries",qm.n},{"K",K},{"L",L},{"metadata_i32",MI},{"features_f32",XF},{"cached_feature_parity_checks",checks},{"seconds",seconds(started)},{"threads",process_threads()},{"new_QPS",false}};fresh_json(root/"complete.json",result);return result;
}
#include "policy.inc"
}
int main(int argc,char**argv){try{using namespace e198;require(argc==3,"mode config");auto c=read_json(argv[2]);std::string mode=argv[1];json result;if(mode=="labels")result=make_labels(c);else if(mode=="inference")result=inference(c);else if(mode=="matrix")result=matrix198(c);else throw std::runtime_error("unknown E198 stage");std::cout<<result.dump()<<std::endl;return 0;}catch(const std::exception&e){std::cerr<<"FATAL E198 "<<e.what()<<std::endl;return 2;}}

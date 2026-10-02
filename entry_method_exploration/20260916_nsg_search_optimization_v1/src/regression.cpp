#include "native_common.hpp"
#include "legacy/ACSG.h"
#include <ACSG/detail/CandidatePool.h>
#include "legacy_pool.hpp"
#include <faiss/utils/distances.h>
#include <random>
#include <functional>
using acsg::Neighbor;
static bool eq(const Neighbor& a,const Neighbor& b){return a.id==b.id && a.flag==b.flag && !memcmp(&a.distance,&b.distance,4);}
struct Recording:faiss::FlatCodesDistanceComputer{
 size_t d;int metric;const float* q=nullptr;std::vector<faiss::idx_t> calls;std::vector<float> forced;
 Recording(const std::vector<float>& x,size_t dim,int m):FlatCodesDistanceComputer((const uint8_t*)x.data(),dim*4),d(dim),metric(m){}
 void set_query(const float* p)override{q=p;calls.clear();}
 float distance_to_code(const uint8_t* c)override{size_t id=(c-codes)/code_size;calls.push_back(id);if(!forced.empty())return forced.at(id);return metric==0?faiss::fvec_inner_product(q,(const float*)c,d):faiss::fvec_L2sqr(q,(const float*)c,d);}
 float symmetric_dis(faiss::idx_t,faiss::idx_t)override{throw std::runtime_error("unexpected symmetric distance");}
};
struct Opaque:faiss::DistanceComputer{std::unique_ptr<faiss::DistanceComputer> inner;explicit Opaque(faiss::DistanceComputer* p):inner(p){}void set_query(const float* q)override{inner->set_query(q);}float operator()(faiss::idx_t i)override{return (*inner)(i);}float symmetric_dis(faiss::idx_t i,faiss::idx_t j)override{return inner->symmetric_dis(i,j);}};
template<class T> json trace_json(const T& t){json j;
#define FIELD(f) j[#f]=t.f
 FIELD(distance_evaluations);FIELD(evaluated_neighbor_count);FIELD(expanded_count);FIELD(accepted_insertion_count);FIELD(rejected_by_pool_bound_count);FIELD(rewind_count);FIELD(rewind_span_sum);FIELD(rewind_span_max);FIELD(best_distance_improvement_count);FIELD(best_distance_improvement_sum);FIELD(pool_bound_improvement_count);FIELD(pool_bound_improvement_sum);FIELD(max_stagnation_expansions);FIELD(stagnation_run_count);FIELD(stagnation_expansion_sum);FIELD(first_topk_gt_evaluation_ndc);FIELD(first_topk_gt_expansion);FIELD(initial_best_distance);FIELD(final_best_distance);FIELD(final_frontier_gap);FIELD(final_pool_gap);
#undef FIELD
 return j;}
int main(int argc,char**argv){try{require(argc==2,"regression output_json");uint64_t pool_cases=0,searches=0,nonfinite=0;bool short_pool_bug=false;
 for(int cap=1;cap<=9;++cap)for(int live=1;live<=cap;++live){std::vector<int> values(live);std::function<void(int,int)> enumerate=[&](int at,int low){if(at<live){for(int v=low;v<4;++v){values[at]=v;enumerate(at+1,v);}return;}
  for(int v=-1;v<=4;++v)for(int id:{1000,0,live-1}){std::vector<Neighbor>a(cap+1,Neighbor(-1,std::numeric_limits<float>::max(),false));for(int i=0;i<live;++i)a[i]=Neighbor(i,values[i],i%2);auto b=a;Neighbor nn(id,v,true);int ra=legacy_insert(a.data(),cap,nn),rb=acsg::detail::insert_into_pool_live(b.data(),cap,live,nn);require(ra==rb,"pool insertion position");for(int i=0;i<=cap;++i)require(eq(a[i],b[i]),"pool state parity");++pool_cases;}
 };enumerate(0,0);}
 {std::vector<Neighbor>a(5,Neighbor(-1,std::numeric_limits<float>::max(),false));a[0]=Neighbor(0,1,true);auto b=a;legacy_insert(a.data(),4,Neighbor(1,1,true));legacy_insert(b.data(),1,Neighbor(1,1,true));short_pool_bug=a[0].id!=b[0].id;require(short_pool_bug,"expected E98 tie counterexample");}
 std::mt19937 rng(98123);size_t test_id=0;
 for(int metric:{0,1})for(int n:{1,2,17,65})for(int dim:{4,32}){
  std::vector<float>x(size_t(n)*dim),q(dim);for(float& f:x)f=int(rng()%5)-2;for(int i=1;i<n;i+=3)std::copy(x.begin(),x.begin()+dim,x.begin()+size_t(i)*dim);for(float& f:q)f=int(rng()%3)-1;
  acsg::ACSG fresh(8);acsg_legacy::ACSG old(8);fresh.ntotal=old.ntotal=n;fresh.is_built=old.is_built=true;fresh.enterpoint=old.enterpoint=0;fresh.final_graph=std::make_shared<acsg::Graph<int32_t>>(n,8);for(int i=0;i<n;++i)for(int j=0;j<8;++j)fresh.final_graph->at(i,j)=j==0?i:j==1?-1:j==2?n+2:int(rng()%n);old.final_graph=std::make_shared<acsg_legacy::Graph<int32_t>>(fresh.final_graph->data,n,8);
  auto* ra=new Recording(x,dim,metric);auto* rb=new Recording(x,dim,metric);std::unique_ptr<faiss::DistanceComputer> da(ra),db(rb);if(metric==0){da=std::make_unique<faiss::NegativeDistanceComputer>(da.release());db=std::make_unique<faiss::NegativeDistanceComputer>(db.release());}if(n==17){da=std::make_unique<Opaque>(da.release());db=std::make_unique<Opaque>(db.release());}
  faiss::VisitedTable va(n),vb(n);std::vector<acsg::Neighbor>bufa;std::vector<acsg_legacy::Neighbor>bufb;
  for(int repeat=0;repeat<10;++repeat)for(int mode:{0,1,2})for(int L:{1,2,3,5,16,100,128})for(int K:{1,100}){if(K>L)continue;++test_id;fresh.search_L=old.search_L=L;std::vector<acsg::EnterPoint>epa;std::vector<acsg_legacy::EnterPoint>epb;if(repeat%3)for(int id:{0,n-1,0}){epa.emplace_back(id,1);epb.emplace_back(id,1);}fresh.top_enterpoints=epa;old.top_enterpoints=epb;
   va.advance();vb.advance();da->set_query(q.data());db->set_query(q.data());std::vector<faiss::idx_t>ia(K),ib(K);std::vector<float>xa(K),xb(K);acsg::SearchTrace ta;acsg_legacy::SearchTrace tb;auto* pa=repeat%2?&bufa:nullptr;auto* pb=repeat%2?&bufb:nullptr;
   if(repeat%2){int64_t gt=0;fresh.search_new_traced(*da,K,ia.data(),xa.data(),va,mode,epa,ta,&gt,1,pa);old.search_new_traced(*db,K,ib.data(),xb.data(),vb,mode,epb,tb,&gt,1,pb);require(trace_json(ta).dump()==trace_json(tb).dump(),"trace parity");}
   else{fresh.search_new(*da,K,ia.data(),xa.data(),va,mode,epa,pa);old.search_new(*db,K,ib.data(),xb.data(),vb,mode,epb,pb);}
   require(ia==ib&&!memcmp(xa.data(),xb.data(),K*4),"search output parity");require(ra->calls==rb->calls,"distance evaluation order parity");searches+=2;
  }
 }
 // Non-finite/sentinel values: retain old insertion behavior for the whole query.
 for(float special:{std::numeric_limits<float>::max(),std::numeric_limits<float>::infinity(),-std::numeric_limits<float>::infinity(),std::numeric_limits<float>::quiet_NaN()})for(int L:{3,100}){
  int n=5,d=4;std::vector<float>x(n*d),q(d);acsg::ACSG a(5);acsg_legacy::ACSG b(5);a.ntotal=b.ntotal=n;a.is_built=b.is_built=true;a.search_L=b.search_L=L;a.final_graph=std::make_shared<acsg::Graph<int32_t>>(n,n);for(int i=0;i<n;++i)for(int j=0;j<n;++j)a.final_graph->at(i,j)=j;b.final_graph=std::make_shared<acsg_legacy::Graph<int32_t>>(a.final_graph->data,n,n);Recording da(x,d,1),db(x,d,1);da.forced=db.forced={0,special,1,2,3};da.set_query(q.data());db.set_query(q.data());faiss::VisitedTable va(n),vb(n);std::vector<acsg::EnterPoint>ea{{0,1}};std::vector<acsg_legacy::EnterPoint>eb{{0,1}};std::array<faiss::idx_t,1>ia,ib;float xa,xb;a.search_new(da,1,ia.data(),&xa,va,2,ea);b.search_new(db,1,ib.data(),&xb,vb,2,eb);require(ia==ib&&!memcmp(&xa,&xb,4)&&da.calls==db.calls,"nonfinite parity");searches+=2;++nonfinite;
 }
 write_json(argv[1],{{"status","PASS"},{"candidate_pool_cases",pool_cases},{"search_calls",searches},{"e98_short_pool_tie_counterexample",short_pool_bug},{"nonfinite_cases",nonfinite},{"distance_order_bit_output_trace_parity",true},{"visited_wraparound_exercised",true}});std::cout<<"PASS pool="<<pool_cases<<" search="<<searches<<std::endl;return 0;}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}

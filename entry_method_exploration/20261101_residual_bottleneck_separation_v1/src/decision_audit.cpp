#include "decision_base.inc"
int main(int argc,char**argv){try{
 using namespace e197;require(argc==3,"config output-stream");auto c=read_json(argv[1]);c.erase("teacher_masks");check_threads(c);auto start=Clock::now();Context x(c);Matrix qm(c.at("queries"));auto Q=qm.copy();std::ofstream f(argv[2],std::ios::binary);require(bool(f),"new transient decision feature stream");
 auto dc=std::unique_ptr<DistanceComputer>(acsg::storage_distance_computer(x.idx->storage));VisitedTable vt(x.idx->ntotal);std::vector<Neighbor>ret;uint64_t rows=0,queries=0;
 for(int K:{1,100})for(int L:{100,200,400})for(size_t qi=0;qi<qm.n;++qi){const float*q=Q.data()+qi*x.idx->d;auto route=x.router->route(q);std::vector<int32_t>R;std::vector<float>D;main_search(x,q,K,L,route,vt,R,D,ret,*dc);
  for(int bank:{0,1}){Posting&p=bank?*x.reference:*x.post;std::vector<int32_t>C;std::vector<float>cv;candidates(p,route,R,*dc,C,cv);auto rank=ranks(cv);uint32_t h[5]={uint32_t(K),uint32_t(L),uint32_t(qi),uint32_t(bank),uint32_t(C.size())};f.write((char*)h,sizeof(h));
   const auto&m=x.models.at(K);for(size_t j=0;j<rank.size();++j){int pos=rank[j];auto feature=x.features->row(q,route,vt,C,cv,j,pos,D.data(),K,L,m.count>24,&p);double value=m.predict(feature.data());int32_t id=C[pos];f.write((char*)&id,4);f.write((char*)feature.data(),sizeof(feature));f.write((char*)&value,8);++rows;}++queries;
  }
 }
 f.close();json receipt={{"status","PASS_ACTUAL_FEATURE_AND_MODEL_DECISION_REPLAY"},{"query_K_L_bank_rows",queries},{"candidate_rows",rows},{"features",F},{"record_bytes",428},{"header_bytes",20},{"GT_or_GT_mask_read",false},{"timed_QPS",nullptr},{"native_process_seconds",seconds(start)}};fresh_json(std::string(argv[2])+".json",receipt);std::cout<<receipt.dump()<<std::endl;return 0;
 }catch(const std::exception&e){std::cerr<<"FATAL DECISION AUDIT "<<e.what()<<std::endl;return 2;}}

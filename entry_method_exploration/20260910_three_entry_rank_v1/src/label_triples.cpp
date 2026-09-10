#define main legacy_diagnostic_main
#include "legacy_reference.cpp"
#undef main
#include <map>

int main(int argc, char** argv) {
  try {
    require(argc==3,"label_triples config.json new_output");
    std::ifstream cf(argv[1]);json c;cf>>c;
    fs::path out=argv[2];require(!fs::exists(out),"refuse existing labels");fs::create_directories(out);
    const size_t n=c.at("num_queries"), d=c.at("dim"), h=c.at("hub_count"), gtk=c.at("gt_k");
    const size_t choices=c.at("contexts").get<size_t>()*c.at("options").get<size_t>();
    require(n*choices<=c.at("logical_call_cap").get<size_t>() && choices==24,"label cap exceeded");
    auto q=read_raw<float>(c.at("queries_file"));auto gt=read_raw<int64_t>(c.at("gt_file"));
    auto hubs=read_raw<int32_t>(c.at("hub_ids"));auto triples=read_raw<int32_t>(c.at("triples_file"));
    require(q.size()==n*d && gt.size()==n*gtk && hubs.size()==h && triples.size()==n*choices*3,"label shape mismatch");
    finite_matrix(q,"fit queries");require(std::set<int32_t>(hubs.begin(),hubs.end()).size()==h,"duplicate hubs");
    for(size_t i=0;i<n*choices;++i){
      std::set<int32_t> ids;
      for(size_t k=0;k<3;++k){int32_t e=triples[i*3+k];require(e>=0 && size_t(e)<h,"bad local hub");ids.insert(e);}
      require(ids.size()==3,"nonunique three-entry label");
    }
    auto index=std::make_unique<acsg::IndexACSGFlat>();index->loadACPG(c.at("index_path").get<std::string>().c_str());
    std::vector<float>().swap(index->acsg.pheromone);std::vector<float>().swap(index->acsg.weight);
    require(index->d==int(d) && index->metric_type==faiss::METRIC_INNER_PRODUCT,"metric/index mismatch");
    for(auto e:hubs)require(e>=0 && e<index->ntotal,"hub outside base");
    for(auto e:gt)require(e>=0 && e<index->ntotal,"GT outside base");
    index->acsg.search_L=c.at("L");require(index->acsg.search_L==128,"unexpected label L");
    int nt=c.at("threads");require(nt>=1 && nt<=16,"bad threads");omp_set_dynamic(0);omp_set_num_threads(nt);
    std::vector<std::unique_ptr<Work>> workers;for(int t=0;t<nt;++t)workers.push_back(std::make_unique<Work>(*index,true));
    Work plain(*index,false);size_t parity=0;
    for(size_t i=0;i<std::min(n,size_t(16));++i)for(size_t a=0;a<choices;++a){
      std::array<int32_t,3> e;std::copy_n(triples.data()+(i*choices+a)*3,3,e.begin());
      auto x=workers[0]->run(*index,q.data()+i*d,hubs,e,3),y=plain.run(*index,q.data()+i*d,hubs,e,3);
      auto z=workers[0]->run(*index,q.data()+i*d,hubs,e,3);
      require(x.ids==y.ids && x.ids==z.ids && x.ndc==z.ndc &&
              std::memcmp(x.distances.data(),y.distances.data(),K*sizeof(float))==0,"three-entry parity failed");++parity;
    }
    write_json(out/"parity.json",{{"status","PASS"},{"three_entry_cases",parity},{"physical_calls",parity*3}});
    write_json(out/"config.json",c);
    std::ofstream hitfile(out/"hits.u8",std::ios::binary),maskfile(out/"masks.u16",std::ios::binary),
                  ndcfile(out/"graph_ndc.u32",std::ios::binary),idfile(out/"ids.i32",std::ios::binary);
    size_t physical=0;const auto start=Clock::now();
    for(size_t begin=0;begin<n;begin+=64){
      size_t count=std::min(size_t(64),n-begin);std::vector<Search> outputs(count*choices);std::vector<size_t> calls(count);
      #pragma omp parallel for schedule(static)
      for(size_t row=0;row<count;++row){
        std::map<std::array<int32_t,3>,Search> cache;
        for(size_t a=0;a<choices;++a){
          std::array<int32_t,3> e;std::copy_n(triples.data()+((begin+row)*choices+a)*3,3,e.begin());
          auto found=cache.find(e);
          if(found==cache.end())found=cache.emplace(e,workers[omp_get_thread_num()]->run(*index,q.data()+(begin+row)*d,hubs,e,3)).first;
          outputs[row*choices+a]=found->second;
        }
        calls[row]=cache.size();
      }
      // GT is consulted only after all raw searches in the block return.
      for(size_t row=0;row<count;++row)for(size_t a=0;a<choices;++a){
        const auto& x=outputs[row*choices+a];uint16_t mask=hitmask(x.ids,gt.data()+(begin+row)*gtk);
        uint8_t hits=__builtin_popcount(unsigned(mask));
        hitfile.write(reinterpret_cast<char*>(&hits),1);maskfile.write(reinterpret_cast<char*>(&mask),2);
        ndcfile.write(reinterpret_cast<const char*>(&x.ndc),4);idfile.write(reinterpret_cast<const char*>(x.ids.data()),K*4);
      }
      require(hitfile && maskfile && ndcfile && idfile,"label write failed");
      physical+=std::accumulate(calls.begin(),calls.end(),size_t(0));
      double elapsed=std::chrono::duration<double>(Clock::now()-start).count();
      json p={{"rows_complete",begin+count},{"rows_total",n},{"physical_calls",physical},{"logical_calls",(begin+count)*choices},
              {"elapsed_seconds",elapsed},{"eta_seconds",elapsed*(n-begin-count)/(begin+count)}};
      write_json(out/"progress.json",p);
      if(begin==0 || begin%1024==0 || begin+count==n)std::cout<<p.dump()<<std::endl;
    }
    write_json(out/"complete.json",{{"status","COMPLETE"},{"logical_calls",n*choices},{"physical_calls",physical},
      {"parity_calls",parity*3},{"seconds",std::chrono::duration<double>(Clock::now()-start).count()},
      {"threads",nt},{"instrumented_offline_only",true}});
    return 0;
  }catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}
}

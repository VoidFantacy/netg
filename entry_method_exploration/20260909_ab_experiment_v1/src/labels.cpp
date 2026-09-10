// Freeze a copy of the audited original-kernel wrapper for reproducibility.
#define main legacy_diagnostic_main
#include "legacy_reference.cpp"
#undef main
#include <sys/statvfs.h>

int labels(const json& c,const fs::path& out,bool parity_only) {
    require(!fs::exists(out),"refuse existing output");fs::create_directories(out);
    auto q=read_raw<float>(c.at("queries_file"));auto gt=read_raw<int64_t>(c.at("gt_file"));
    auto hubs=read_raw<int32_t>(c.at("hub_ids"));auto rows=read_raw<int64_t>(c.at("row_ids"));
    size_t n=rows.size(),h=hubs.size(),d=c.at("dim"),gtk=c.at("gt_k");
    require(n==c.at("num_queries") && h==c.at("hub_count") && q.size()==n*d && gt.size()==n*gtk,"shape mismatch");
    require(gtk>=K && std::set<int32_t>(hubs.begin(),hubs.end()).size()==h,"invalid GT/hubs");
    finite_matrix(q,"queries");
    auto index=std::make_unique<acsg::IndexACSGFlat>();index->loadACPG(c.at("index_path").get<std::string>().c_str());
    std::vector<float>().swap(index->acsg.pheromone);std::vector<float>().swap(index->acsg.weight);
    require(index->d==int(d) && index->metric_type==faiss::METRIC_INNER_PRODUCT,"wrong index");
    for(auto id:hubs) require(id>=0 && id<index->ntotal,"invalid hub");
    for(auto id:gt) require(id>=0 && id<index->ntotal,"invalid GT");
    int nt=c.value("threads",16);require(nt>=1 && nt<=16,"invalid threads");omp_set_num_threads(nt);
    std::vector<std::unique_ptr<Work>> work;for(int t=0;t<nt;++t)work.push_back(std::make_unique<Work>(*index,true));
    Work plain(*index,false);size_t parity_checks=0;const auto ls=c.at("L").get<std::vector<int>>();
    for(int l:ls) {
        require(l>=10,"invalid L");index->acsg.search_L=l;
        for(size_t i=0;i<std::min(n,size_t(16));++i)for(size_t j=0;j<5;++j) {
            std::array<int32_t,3> e{int32_t((i*97+j*(h/5))%h),-1,-1};
            auto a=work[0]->run(*index,q.data()+i*d,hubs,e,1),b=plain.run(*index,q.data()+i*d,hubs,e,1),r=work[0]->run(*index,q.data()+i*d,hubs,e,1);
            require(a.ids==b.ids && a.distances==b.distances && a.ids==r.ids && a.ndc==r.ndc,"real plain/count/repeat parity failed");
            auto mask=hitmask(a.ids,gt.data()+i*gtk);unsigned independent=0;
            for(size_t g=0;g<K;++g)if(std::find(a.ids.begin(),a.ids.end(),gt[i*gtk+g])!=a.ids.end())++independent;
            require(independent==unsigned(__builtin_popcount(unsigned(mask))),"independent hit scoring differs");++parity_checks;
        }
    }
    write_json(out/"parity.json",{{"status","PASS"},{"graph_checks",parity_checks},{"physical_calls",parity_checks*3},{"L",ls},{"query_rows",16},{"distinct_entries_per_row",5}});
    if(parity_only)return 0;
    write_json(out/"config.json",c);
    const auto start=Clock::now();size_t done=0,total=n*h*ls.size();std::ofstream progress(out/"progress.jsonl");
    for(int l:ls) {
        index->acsg.search_L=l;const auto dir=out/("L"+std::to_string(l));fs::create_directory(dir);
        std::ofstream counts(dir/"hitcount.u8",std::ios::binary),masks(dir/"hitmask.u16",std::ios::binary),ndcs(dir/"ndc.u32",std::ios::binary),sample(dir/"first2.ids.i32",std::ios::binary);
        size_t block=c.value("block_rows",16);
        for(size_t begin=0;begin<n;begin+=block) {
            struct statvfs disk{};require(statvfs(out.c_str(),&disk)==0,"disk stat failed");
            require(double(disk.f_bavail)*disk.f_frsize>10.0*1024*1024*1024,"disk below 10GiB floor");
            const size_t count=std::min(block,n-begin);std::vector<Search> results(count*h);
            #pragma omp parallel for schedule(static)
            for(size_t i=0;i<count;++i) {
                auto& w=*work[omp_get_thread_num()];
                for(size_t j=0;j<h;++j) results[i*h+j]=w.run(*index,q.data()+(begin+i)*d,hubs,{int32_t(j),-1,-1},1);
            }
            for(size_t i=0;i<count;++i)for(size_t j=0;j<h;++j) {
                const auto& r=results[i*h+j];uint16_t mask=hitmask(r.ids,gt.data()+(begin+i)*gtk);uint8_t hits=__builtin_popcount(unsigned(mask));
                counts.write(reinterpret_cast<char*>(&hits),1);masks.write(reinterpret_cast<char*>(&mask),2);ndcs.write(reinterpret_cast<const char*>(&r.ndc),4);
                if(begin+i<2)sample.write(reinterpret_cast<const char*>(r.ids.data()),K*4);
            }
            counts.flush();masks.flush();ndcs.flush();sample.flush();require(counts && masks && ndcs && sample,"label write failed");
            done+=count*h;double secs=std::chrono::duration<double>(Clock::now()-start).count();
            json j={{"stage","labels"},{"L",l},{"rows_complete",begin+count},{"queries",n},{"hubs",h},{"calls_done",done},{"calls_total",total},{"elapsed_seconds",secs},{"calls_per_second",done/secs},{"eta_seconds",(total-done)*secs/done}};
            progress<<j.dump()<<'\n';progress.flush();write_json(out/"progress.json",j);
            if(begin==0 || (begin/block)%16==0 || begin+count==n)std::cout<<j.dump()<<std::endl;
        }
        write_json(dir/"complete.json",{{"status","COMPLETE"},{"rows",n},{"hubs",h},{"L",l},{"layout","C row-major little-endian"},{"logical_search_calls",n*h}});
    }
    write_json(out/"complete.json",{{"status","COMPLETE"},{"calls",done},{"parity_calls",parity_checks*3},{"instrumented_only",true},{"seconds",std::chrono::duration<double>(Clock::now()-start).count()}});return 0;
}
int main(int argc,char** argv) {
    try {
        if(argc==2 && std::string(argv[1])=="--self-test"){self_test();return 0;}
        require(argc==3 || argc==4,"Usage: labels config.json new_output [--parity-only]");
        std::ifstream f(argv[1]);require(bool(f),"missing config");json c;f>>c;
        return labels(c,argv[2],argc==4 && std::string(argv[3])=="--parity-only");
    }catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}
}

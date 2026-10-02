#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
#include <sched.h>
int main(int argc,char**argv) {
    try {
        require(argc==3,"build_graph model.json new_graph.hnsw");require(!fs::exists(argv[2]),"refuse existing graph");
        check_multiplicity({10,20,20,30,30,30},3,true);check_multiplicity({10,10,10},1,false);
        size_t rejected=0;
        for(const auto& x:std::vector<std::vector<int32_t>>{{},{10,10,10,10},{-1},{10,20}}) {
            try{check_multiplicity(x,1,true);}catch(const std::exception&){++rejected;}
        }
        require(rejected==4,"invalid multiplicity accepted");
        std::ifstream f(argv[1]);json c;f>>c;c.erase("graph_file");c["reference_graph"]=false;
        auto start=Clock::now();Policy p(c,argv[2],false,false);
        const double sec=std::chrono::duration<double>(Clock::now()-start).count();
        int threads=0;std::ifstream status("/proc/self/status");std::string line;while(std::getline(status,line))if(line.rfind("Threads:",0)==0)threads=std::stoi(line.substr(8));
        cpu_set_t cpus;CPU_ZERO(&cpus);require(sched_getaffinity(0,sizeof(cpus),&cpus)==0 && CPU_COUNT(&cpus)==1 && CPU_ISSET(15,&cpus) && threads==1,"build thread/CPU mismatch");
        std::cout<<json({{"status","PASS"},{"builds",1},{"HNSW_queries",0},{"NSG",0},{"build_seconds",sec},{"shape_rejections",rejected},{"process_threads",threads},{"CPU",15}}).dump()<<std::endl;
        return 0;
    }catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}
}

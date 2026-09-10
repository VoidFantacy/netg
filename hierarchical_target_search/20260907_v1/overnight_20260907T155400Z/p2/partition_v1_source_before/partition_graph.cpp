// CPU-only P2 graph partitioning. Original directed NSG is opened O_RDONLY.
// Symmetric deduplicated CSR is temporary RAM only, never written to disk.
#include <algorithm>
#include <cerrno>
#include <chrono>
#include <cmath>
#include <csignal>
#include <cstdint>
#include <cstring>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <unistd.h>
#include <omp.h>
#include <metis.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;
using Clock = std::chrono::steady_clock;
namespace fs = std::filesystem;
static_assert(sizeof(idx_t) == 8, "This protocol requires METIS 64-bit idx_t");
static_assert(sizeof(real_t) == 4, "Prepared METIS real_t is 32-bit");
volatile std::sig_atomic_t stop_requested = 0;

void signal_handler(int) { stop_requested = 1; }
void checkpoint() {
    if (stop_requested) throw std::runtime_error("termination requested; retain INCOMPLETE output");
    if (std::time(nullptr) >= 1788821940) // 2026-09-07T22:59:00Z
        throw std::runtime_error("research soft deadline reached");
}
double elapsed(Clock::time_point from) { return std::chrono::duration<double>(Clock::now()-from).count(); }
long peak_rss_kib() { rusage r{}; getrusage(RUSAGE_SELF,&r); return r.ru_maxrss; }
std::string sha256_bytes(const void* data,size_t bytes) {
    constexpr uint32_t k[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
    uint32_t h[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    auto rr=[](uint32_t x,int n){return (x>>n)|(x<<(32-n));};
    auto input=static_cast<const uint8_t*>(data);size_t total=(bytes+9+63)/64*64;uint64_t bits=static_cast<uint64_t>(bytes)*8;
    for(size_t off=0;off<total;off+=64){uint32_t w[64]{};
        for(size_t j=0;j<64;++j){size_t at=off+j;uint8_t b=at<bytes?input[at]:at==bytes?0x80:0;
            if(at>=total-8)b=static_cast<uint8_t>(bits>>(8*(total-1-at)));
            w[j/4]|=uint32_t(b)<<(24-8*(j%4));}
        for(int j=16;j<64;++j){uint32_t s0=rr(w[j-15],7)^rr(w[j-15],18)^(w[j-15]>>3),s1=rr(w[j-2],17)^rr(w[j-2],19)^(w[j-2]>>10);w[j]=w[j-16]+s0+w[j-7]+s1;}
        uint32_t a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],v=h[7];
        for(int j=0;j<64;++j){uint32_t t1=v+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^(~e&g))+k[j]+w[j];
            uint32_t t2=(rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c));v=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;}
        h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=v;
    }
    constexpr char hex[]="0123456789abcdef";std::string out;out.reserve(64);
    for(auto word:h)for(int shift=28;shift>=0;shift-=4)out+=hex[(word>>shift)&15];
    return out;
}
int32_t neighbor_at(const void* data,size_t pos) {
    // Native v1 adjacency starts at an unaligned byte offset. memcpy avoids
    // undefined behavior from dereferencing an unaligned int32_t pointer.
    int32_t value;std::memcpy(&value,static_cast<const char*>(data)+pos*4,4);return value;
}
json read_json(const fs::path& p) {
    std::ifstream f(p); if (!f) throw std::runtime_error("cannot open JSON: "+p.string());
    json j; f>>j; return j;
}
void write_json(const fs::path& p,const json& j) {
    fs::path partial = p.string()+".partial";
    std::ofstream f(partial,std::ios::trunc);
    if (!f) throw std::runtime_error("cannot write JSON: "+partial.string());
    f<<j.dump(2)<<'\n'; f.close();
    if (!f) throw std::runtime_error("JSON write failed");
    fs::rename(partial,p);
}

struct Header {
    int32_t version=0,d=0,metric=0,k=0,entry=0;
    int64_t n=0;
    uint64_t adjacency_offset=0,vector_offset=0,bytes=0;
};
template<class T> T read_at(int fd,uint64_t& offset) {
    T x;
    if (pread(fd,&x,sizeof(T),static_cast<off_t>(offset)) != static_cast<ssize_t>(sizeof(T)))
        throw std::runtime_error("truncated graph header");
    offset+=sizeof(T); return x;
}
Header read_header(int fd) {
    uint64_t off=0; Header h;
    h.version=read_at<int32_t>(fd,off); h.n=read_at<int64_t>(fd,off);
    h.d=read_at<int32_t>(fd,off); h.metric=read_at<int32_t>(fd,off);
    auto trained=read_at<uint8_t>(fd,off), built=read_at<uint8_t>(fd,off);
    (void)read_at<uint8_t>(fd,off);
    if(h.version!=1||h.n<=0||h.d<=0||h.metric!=0||!trained||!built)
        throw std::runtime_error("expected built native v1 IP graph");
    off+=4*4+3*4; // alpha,beta,rho,lambda,iterations,rejection,search_L
    int32_t declared_k=read_at<int32_t>(fd,off);
    h.entry=read_at<int32_t>(fd,off); (void)read_at<int64_t>(fd,off);
    uint64_t pheromone=read_at<uint64_t>(fd,off);
    if(pheromone!=static_cast<uint64_t>(h.n)) throw std::runtime_error("pheromone count mismatch");
    off+=pheromone*4;
    uint64_t weights=read_at<uint64_t>(fd,off);
    if(weights!=static_cast<uint64_t>(h.n)) throw std::runtime_error("weight count mismatch");
    off+=weights*4;
    h.k=read_at<int32_t>(fd,off); auto neighbors=read_at<uint64_t>(fd,off);
    if(h.k!=64||h.k!=declared_k||neighbors!=static_cast<uint64_t>(h.n)*h.k||h.entry<0||h.entry>=h.n)
        throw std::runtime_error("frozen NSG shape/entry mismatch");
    h.adjacency_offset=off; off+=neighbors*4;
    auto vectors=read_at<uint64_t>(fd,off); h.vector_offset=off;
    if(vectors!=static_cast<uint64_t>(h.n)*h.d) throw std::runtime_error("vector count mismatch");
    h.bytes=off+vectors*4;
    struct stat s{}; if(fstat(fd,&s)||static_cast<uint64_t>(s.st_size)!=h.bytes)
        throw std::runtime_error("graph length mismatch");
    return h;
}
struct MappedGraph {
    int fd=-1; void* mapping=MAP_FAILED; size_t mapping_bytes=0;
    Header h; const void* adjacency=nullptr;
    explicit MappedGraph(const fs::path& p) {
        fd=open(p.c_str(),O_RDONLY);
        if(fd<0) throw std::runtime_error("cannot open graph O_RDONLY");
        try {
            h=read_header(fd);
            const uint64_t page=static_cast<uint64_t>(sysconf(_SC_PAGE_SIZE));
            const uint64_t aligned=h.adjacency_offset/page*page;
            const size_t delta=static_cast<size_t>(h.adjacency_offset-aligned);
            mapping_bytes=static_cast<size_t>(h.n)*h.k*4+delta;
            mapping=mmap(nullptr,mapping_bytes,PROT_READ,MAP_PRIVATE,fd,static_cast<off_t>(aligned));
            if(mapping==MAP_FAILED) throw std::runtime_error("adjacency-only mmap failed");
            adjacency=static_cast<const char*>(mapping)+delta;
            madvise(mapping,mapping_bytes,MADV_SEQUENTIAL);
        } catch (...) { close(fd);fd=-1;throw; }
    }
    ~MappedGraph(){ if(mapping!=MAP_FAILED)munmap(mapping,mapping_bytes);if(fd>=0)close(fd); }
    MappedGraph(const MappedGraph&)=delete;
};

struct CSR {
    idx_t n=0;
    std::vector<idx_t> offsets,edges;
    json stats;
};
void progress(const char* phase,idx_t done,idx_t total,Clock::time_point start) {
    const double sec=elapsed(start),rate=static_cast<double>(done)/std::max(sec,1e-9);
    std::cout<<"PROGRESS "<<phase<<" rows="<<done<<'/'<<total
             <<" rows_per_second="<<rate<<" eta_seconds="<<(total-done)/std::max(rate,1e-9)
             <<" peak_rss_kib="<<peak_rss_kib()<<std::endl;
}
CSR symmetrize(const void* graph,idx_t n,int k,int threads) {
    CSR csr; csr.n=n; csr.offsets.assign(static_cast<size_t>(n)+1,0);
    uint64_t padding=0,self=0,nonself=0;
    auto begin=Clock::now(); double last=0;
    std::cout<<"PHASE count_symmetric_degrees n="<<n<<" directed_width="<<k<<std::endl;
    for(idx_t u=0;u<n;++u) {
        for(int j=0;j<k;++j) {
            const idx_t v=neighbor_at(graph,static_cast<size_t>(u)*k+j);
            if(v==-1){++padding;continue;}
            if(v<0||v>=n)throw std::runtime_error("non-padding invalid neighbor at node "+std::to_string(u));
            if(v==u){++self;continue;}
            ++nonself; ++csr.offsets[u+1]; ++csr.offsets[v+1];
        }
        if((u&65535)==0) {
            checkpoint(); if(elapsed(begin)-last>=10){progress("count",u,n,begin);last=elapsed(begin);}
        }
    }
    for(idx_t i=0;i<n;++i)csr.offsets[i+1]+=csr.offsets[i];
    if(static_cast<uint64_t>(csr.offsets[n])!=nonself*2)throw std::runtime_error("symmetric degree total mismatch");
    const size_t allocated=static_cast<size_t>(csr.offsets[n]);
    const double count_seconds=elapsed(begin);
    std::cout<<"PHASE fill_symmetric_CSR allocated_edges="<<allocated
             <<" edge_bytes="<<allocated*sizeof(idx_t)<<std::endl;
    csr.edges.resize(allocated);
    std::vector<idx_t> cursor(csr.offsets.begin(),csr.offsets.end()-1);
    begin=Clock::now();last=0;
    for(idx_t u=0;u<n;++u) {
        for(int j=0;j<k;++j) {
            idx_t v=neighbor_at(graph,static_cast<size_t>(u)*k+j);
            if(v<0||v==u)continue;
            csr.edges[cursor[u]++]=v;csr.edges[cursor[v]++]=u;
        }
        if((u&65535)==0){checkpoint();if(elapsed(begin)-last>=10){progress("fill",u,n,begin);last=elapsed(begin);}}
    }
    for(idx_t u=0;u<n;++u)if(cursor[u]!=csr.offsets[u+1])throw std::runtime_error("CSR fill cursor mismatch");
    double fill_seconds=elapsed(begin);
    std::cout<<"PHASE sort_unique_rows threads="<<threads<<std::endl;
    begin=Clock::now();
    // cursor reused to store each row's unique length. No per-node vectors.
    for(idx_t start=0;start<n;start+=262144) {
        const idx_t end=std::min(n,start+262144);
        #pragma omp parallel for num_threads(threads) schedule(dynamic,256)
        for(idx_t u=start;u<end;++u) {
            auto first=csr.edges.begin()+csr.offsets[u],last_it=csr.edges.begin()+csr.offsets[u+1];
            std::sort(first,last_it);cursor[u]=std::unique(first,last_it)-first;
        }
        checkpoint();progress("sort_unique",end,n,begin);
    }
    double sort_seconds=elapsed(begin);
    std::cout<<"PHASE compact_CSR_in_place"<<std::endl;
    begin=Clock::now();idx_t write=0;idx_t max_degree=0,isolated=0;
    for(idx_t u=0;u<n;++u) {
        idx_t old=csr.offsets[u],size=cursor[u];
        if(size)std::memmove(csr.edges.data()+write,csr.edges.data()+old,static_cast<size_t>(size)*sizeof(idx_t));
        csr.offsets[u]=write;write+=size;max_degree=std::max(max_degree,size);if(!size)++isolated;
        if((u&65535)==0)checkpoint();
    }
    csr.offsets[n]=write;csr.edges.resize(static_cast<size_t>(write));
    // Keep original allocation capacity; avoid an extra multi-GB copy/shrink.
    csr.stats={{"original_directed_slots",static_cast<uint64_t>(n)*k},
               {"padding_slots",padding},{"self_loop_slots_removed_for_partition_only",self},
               {"nonself_directed_slots",nonself},{"symmetric_slots_before_dedup",allocated},
               {"symmetric_slots_after_dedup",write},{"undirected_edges",write/2},
               {"duplicate_symmetric_slots_removed",allocated-static_cast<size_t>(write)},
               {"maximum_undirected_degree",max_degree},{"isolated_nodes",isolated},
               {"csr_edge_capacity_bytes",csr.edges.capacity()*sizeof(idx_t)},
               {"csr_offset_bytes",csr.offsets.size()*sizeof(idx_t)},
               {"count_seconds",count_seconds},{"fill_seconds",fill_seconds},
               {"sort_unique_seconds",sort_seconds},{"compact_seconds",elapsed(begin)}};
    if(write%2)throw std::runtime_error("symmetric CSR edge count must be even");
    return csr;
}

struct PartitionResult { std::vector<uint16_t> labels; json stats; };
PartitionResult partition(CSR& csr,int parts,int seed,bool debug) {
    if(parts<2||parts>65535||parts>csr.n)throw std::runtime_error("invalid region count");
    idx_t n=csr.n,ncon=1,nparts=parts,edgecut=0;
    idx_t options[METIS_NOPTIONS]; METIS_SetDefaultOptions(options);
    options[METIS_OPTION_SEED]=seed;options[METIS_OPTION_UFACTOR]=200;
    options[METIS_OPTION_NCUTS]=1;options[METIS_OPTION_NITER]=10;
    options[METIS_OPTION_NUMBERING]=0;
    options[METIS_OPTION_DBGLVL]=debug ? METIS_DBG_TIME|METIS_DBG_COARSEN|METIS_DBG_MEMORY : 0;
    std::vector<idx_t> labels(static_cast<size_t>(n),-1);
    std::cout<<"PHASE METIS_PartGraphKway n="<<n<<" undirected_edges="<<csr.edges.size()/2
             <<" parts="<<parts<<" seed="<<seed<<std::endl;
    checkpoint();auto begin=Clock::now();
    int rc=METIS_PartGraphKway(&n,&ncon,csr.offsets.data(),csr.edges.data(),nullptr,nullptr,nullptr,
                             &nparts,nullptr,nullptr,options,&edgecut,labels.data());
    double metis_seconds=elapsed(begin);checkpoint();
    if(rc!=METIS_OK)throw std::runtime_error("METIS failed return="+std::to_string(rc));
    std::vector<uint64_t> sizes(parts,0);PartitionResult out;out.labels.resize(n);
    for(idx_t u=0;u<n;++u){if(labels[u]<0||labels[u]>=parts)throw std::runtime_error("METIS returned invalid region");
        ++sizes[labels[u]];out.labels[u]=static_cast<uint16_t>(labels[u]);}
    uint64_t crossing=0;begin=Clock::now();
    std::cout<<"PHASE verify_edgecut_and_region_sizes"<<std::endl;
    for(idx_t u=0;u<n;++u){
        for(idx_t e=csr.offsets[u];e<csr.offsets[u+1];++e)crossing+=labels[u]!=labels[csr.edges[e]];
        if((u&65535)==0)checkpoint();
    }
    if(crossing%2||crossing/2!=static_cast<uint64_t>(edgecut))throw std::runtime_error("independent edgecut differs from METIS");
    uint64_t limit=static_cast<uint64_t>(std::ceil(1.2*static_cast<double>(n)/parts));
    const bool nonempty=*std::min_element(sizes.begin(),sizes.end())>0;
    const bool capacity=*std::max_element(sizes.begin(),sizes.end())<=limit;
    out.stats={{"metis_return_code",rc},{"metis_idx_bits",64},{"metis_real_bits",32},{"parts",parts},
               {"seed",seed},{"ufactor",200},{"ncuts",1},{"niter",10},{"numbering",0},
               {"debug_level",options[METIS_OPTION_DBGLVL]},{"metis_seconds",metis_seconds},
               {"region_sizes",sizes},{"all_nodes_covered",std::accumulate(sizes.begin(),sizes.end(),uint64_t(0))==static_cast<uint64_t>(n)},
               {"all_regions_nonempty",nonempty},{"capacity_node_limit_ceil",limit},{"capacity_limit_factor",1.2},
               {"capacity_pass",capacity},{"metis_edgecut",edgecut},{"verified_undirected_edgecut",crossing/2},
               {"undirected_edgecut_fraction",csr.edges.empty()?0.0:static_cast<double>(crossing)/csr.edges.size()},
               {"verification_seconds",elapsed(begin)}};
    if(!nonempty||!capacity)throw std::runtime_error("METIS partition has empty region or exceeds1.2 capacity");
    return out;
}
void check_csr_exact(const CSR& csr,const std::vector<int32_t>& original,int k) {
    std::set<std::pair<idx_t,idx_t>> expected;
    for(idx_t u=0;u<csr.n;++u)for(int j=0;j<k;++j){idx_t v=original[u*k+j];if(v>=0&&v!=u){expected.insert({u,v});expected.insert({v,u});}}
    if(expected.size()!=csr.edges.size())throw std::runtime_error("synthetic CSR unique count differs");
    for(idx_t u=0;u<csr.n;++u)for(idx_t e=csr.offsets[u];e<csr.offsets[u+1];++e){
        idx_t v=csr.edges[e];if(v==u||!expected.count({u,v}))throw std::runtime_error("unexpected CSR edge");
        if(!std::binary_search(csr.edges.begin()+csr.offsets[v],csr.edges.begin()+csr.offsets[v+1],u))throw std::runtime_error("CSR not symmetric");
        if(e>csr.offsets[u]&&csr.edges[e-1]>=v)throw std::runtime_error("CSR row not sorted unique");
    }
}
json self_test(int threads) {
    if(sha256_bytes("",0)!="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"||
       sha256_bytes("abc",3)!="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")throw std::runtime_error("SHA256 known vector mismatch");
    json cases=json::array();
    for(int n: {6,24,97}) {
        int k=8,parts=n==6?2:n==24?3:4;std::vector<int32_t> g(n*k,-1);
        for(int u=0;u<n;++u){g[u*k]=(u+1)%n;g[u*k+1]=(u+n-1)%n;g[u*k+2]=(u+1)%n;
            g[u*k+3]=u;g[u*k+4]=(u+2)%n;}
        CSR csr=symmetrize(g.data(),n,k,threads);check_csr_exact(csr,g,k);
        auto r=partition(csr,parts,2026090711,false);
        cases.push_back({{"nodes",n},{"csr_exact",true},{"structure",csr.stats},{"partition",r.stats}});
    }
    bool invalid_rejected=false;
    try {std::vector<int32_t> g{1,8,0,-1};(void)symmetrize(g.data(),2,2,1);}catch(const std::runtime_error&){invalid_rejected=true;}
    if(!invalid_rejected)throw std::runtime_error("invalid edge not rejected");
    return {{"status","PASS_SYNTHETIC_PARTITION_TESTS"},{"cases",cases},{"invalid_edge_rejected",invalid_rejected},
            {"scope","Synthetic CPU algorithm correctness only; no real dataset and no performance gate"}};
}

struct Args {
    fs::path graph,audit,gate,protocol,output;std::string dataset;
    int parts=64,seed=2026090711,threads=16;bool synthetic=false;
};
Args parse(int argc,char** argv) {
    Args a;
    for(int i=1;i<argc;++i){std::string key=argv[i];
        if(key=="--help"){
            std::cout<<"CPU P2 partition tool\nReal: --graph PATH --dataset KEY --audit P0_JSON --gate P1_JSON --protocol JSON --output NEW_DIR [--parts64 --seed2026090711 --threads16]\nSynthetic: --self-test --output NEW_DIR [--threads N]\n";std::exit(0);}
        if(key=="--self-test"){a.synthetic=true;continue;}
        if(i+1==argc)throw std::runtime_error("missing option value: "+key);
        std::string value=argv[++i];
        if(key=="--graph")a.graph=value;else if(key=="--dataset")a.dataset=value;
        else if(key=="--audit")a.audit=value;else if(key=="--gate")a.gate=value;
        else if(key=="--protocol")a.protocol=value;else if(key=="--output")a.output=value;
        else if(key=="--parts")a.parts=std::stoi(value);else if(key=="--seed")a.seed=std::stoi(value);
        else if(key=="--threads")a.threads=std::stoi(value);else throw std::runtime_error("unknown option: "+key);
    }
    if(a.output.empty()||a.threads<1||a.threads>16)throw std::runtime_error("require output and threads1..16");
    if(!a.synthetic&&(a.graph.empty()||a.audit.empty()||a.gate.empty()||a.protocol.empty()||a.dataset.empty()))
        throw std::runtime_error("real partition requires graph,dataset,audit,gate,protocol");
    return a;
}
int main(int argc,char** argv) {
    std::signal(SIGTERM,signal_handler);std::signal(SIGINT,signal_handler);
    Args a;json report;bool output_reserved=false;auto started=Clock::now();
    try {
        a=parse(argc,argv);checkpoint();
        json ds,protocol;
        if(!a.synthetic){
            auto gate=read_json(a.gate);
            if(gate.value("stage","")!="P1"||gate.value("status","")!="PASS")throw std::runtime_error("P1 PASS required before real partition");
            auto audit=read_json(a.audit);if(audit.value("status","")!="PASS_INPUT_CONTRACT")throw std::runtime_error("P0 input audit required");
            for(const auto& d:audit.at("datasets"))if(d.at("dataset")==a.dataset)ds=d;
            if(ds.is_null()||fs::canonical(a.graph)!=fs::canonical(ds.at("graph").at("path").get<std::string>()))throw std::runtime_error("graph path differs from audited dataset");
            protocol=read_json(a.protocol);auto p2=protocol.at("p2_preregistered");
            if(protocol.value("status","")!="PREREGISTERED_ACCEPTED_BEFORE_P2"||a.parts!=p2.at("region_count").get<int>()||a.seed!=p2.at("partition_seed").get<int>())
                throw std::runtime_error("partition arguments differ from preregistered protocol");
        }
        if(fs::exists(a.output)||!fs::create_directory(a.output))throw std::runtime_error("output directory must be new; parent must exist");
        output_reserved=true;
        report={{"schema_version",1},{"stage","P2"},{"status","INCOMPLETE"},{"cpu_only",true},{"synthetic",a.synthetic},
                {"threads_preprocessing",a.threads},{"metis_threads",1},{"heldout_accessed",false},
                {"search_graph_modified",false},{"base_or_graph_copied",false},{"csr_saved_to_disk",false},
                {"deadline_utc","2026-09-07T23:00:00Z"},{"phase","STARTED"}};
        write_json(a.output/"manifest.json",report);
        if(a.synthetic){report["tests"]=self_test(a.threads);report["status"]="PASS_SYNTHETIC_PARTITION_TESTS";}
        else{
            MappedGraph graph(a.graph);
            if(graph.h.n!=ds.at("graph").at("header").at("n").get<int64_t>()||graph.h.d!=ds.at("graph").at("header").at("d").get<int>()||graph.h.bytes!=ds.at("graph").at("header").at("bytes").get<uint64_t>())
                throw std::runtime_error("graph header differs from P0");
            report["dataset"]=a.dataset;report["input_graph_path"]=fs::canonical(a.graph).string();
            report["input_graph_sha256"]=ds.at("graph").at("sha256");report["checksum_verification"]="Full SHA256 inherited from current P0 audit, no repeated large scan";
            report["input_audit_path"]=fs::canonical(a.audit).string();report["p1_gate_path"]=fs::canonical(a.gate).string();
            report["protocol_path"]=fs::canonical(a.protocol).string();
            report["n"]=graph.h.n;report["nodes"]=graph.h.n;report["regions"]=a.parts;report["d"]=graph.h.d;report["graph_adjacency_offset"]=graph.h.adjacency_offset;
            report["phase"]="SYMMETRIC_CSR";write_json(a.output/"manifest.json",report);
            auto csr=symmetrize(graph.adjacency,graph.h.n,graph.h.k,a.threads);
            report["structure"]=csr.stats;report["phase"]="METIS";write_json(a.output/"manifest.json",report);
            auto result=partition(csr,a.parts,a.seed,true);report["partition"]=result.stats;
            uint64_t crossing=0,nonself=0;
            for(idx_t u=0;u<graph.h.n;++u){
                for(int j=0;j<graph.h.k;++j){idx_t v=neighbor_at(graph.adjacency,static_cast<size_t>(u)*graph.h.k+j);
                    if(v>=0&&v!=u){++nonself;crossing+=result.labels[u]!=result.labels[v];}}
                if((u&65535)==0)checkpoint();
            }
            report["partition"]["original_directed_nonself_crossing_slots"]=crossing;
            report["partition"]["original_directed_nonself_cut_fraction"]=nonself?static_cast<double>(crossing)/nonself:0.0;
            const fs::path labels_path=a.output/"regions.u16";
            int out=open(labels_path.c_str(),O_WRONLY|O_CREAT|O_EXCL,0644);
            if(out<0)throw std::runtime_error("cannot reserve label output");
            size_t bytes=result.labels.size()*sizeof(uint16_t),done=0;
            while(done<bytes){ssize_t wrote=write(out,reinterpret_cast<const char*>(result.labels.data())+done,bytes-done);
                if(wrote<=0){close(out);throw std::runtime_error("label write failed");}done+=static_cast<size_t>(wrote);}
            int sync_result=fsync(out),close_result=close(out);
            if(sync_result||close_result)throw std::runtime_error("label flush/close failed");
            report["labels"]={{"path",fs::absolute(labels_path).string()},{"dtype","little-endian uint16"},{"rows",result.labels.size()},{"bytes",bytes},{"header",false},{"sha256",sha256_bytes(result.labels.data(),bytes)}};
            report["labels_file"]=fs::absolute(labels_path).string();report["labels_sha256"]=report["labels"]["sha256"];
            report["status"]="COMPLETE";report["phase"]="DONE";
        }
        report["wall_seconds"]=elapsed(started);report["peak_rss_kib"]=peak_rss_kib();
        report["performance_gate_passed"]=false;write_json(a.output/"manifest.json",report);
        std::cout<<report.dump(2)<<std::endl;return 0;
    }catch(const std::exception& e){
        std::cerr<<"ERROR "<<e.what()<<std::endl;
        if(output_reserved){report["status"]="INCOMPLETE";report["error"]=e.what();report["wall_seconds"]=elapsed(started);report["peak_rss_kib"]=peak_rss_kib();
            try{write_json(a.output/"manifest.json",report);}catch(...){}}
        return 1;
    }
}

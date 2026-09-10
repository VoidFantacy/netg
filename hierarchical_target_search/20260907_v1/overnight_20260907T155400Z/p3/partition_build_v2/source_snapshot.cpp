// CPU-only P3 common hierarchical initialization and exact directed/GT descent.
// IO/CSR/SHA helpers copied from frozen P2 source; P2 source is not modified.
// Symmetric deduplicated CSR is temporary RAM only, never written to disk.
#include <algorithm>
#include <array>
#include <functional>
#include <iomanip>
#include <random>
#include <sstream>
#include <tuple>
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
#include <memory>
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

#ifndef P3_SOURCE_SHA256
#define P3_SOURCE_SHA256 "UNBOUND_SYNTHETIC_ONLY"
#endif
constexpr int coarse_count=16, leaves_per_coarse=16, leaf_count=256, gt_width=10;
constexpr int fixed_seed=2026090711, fit_count=20000, minimum_leaf_size=3;
using Wide = __int128_t;

void require(bool yes,const std::string& message) { if(!yes)throw std::runtime_error(message); }
std::string wide_string(Wide v) {
    if(!v)return "0";
    bool negative=v<0;if(negative)v=-v;
    std::string s;while(v){s.push_back(char('0'+v%10));v/=10;}if(negative)s.push_back('-');
    std::reverse(s.begin(),s.end());return s;
}
std::vector<uint8_t> read_small_binary(const fs::path& path,size_t limit=128ULL<<20) {
    const auto bytes=fs::file_size(path);require(bytes<=limit,"refuse oversized metadata/fit input: "+path.string());
    std::vector<uint8_t> data(bytes);std::ifstream f(path,std::ios::binary);
    require(bool(f),"cannot read binary: "+path.string());f.read(reinterpret_cast<char*>(data.data()),bytes);
    require(bool(f),"truncated binary: "+path.string());return data;
}
std::string file_sha(const fs::path& p) { auto bytes=read_small_binary(p);return sha256_bytes(bytes.data(),bytes.size()); }
json write_labels_new(const fs::path& path,const std::vector<uint16_t>& labels) {
    const int fd=open(path.c_str(),O_WRONLY|O_CREAT|O_EXCL,0644);
    require(fd>=0,"cannot reserve labels: "+path.string());
    const size_t bytes=labels.size()*sizeof(uint16_t);size_t done=0;
    while(done<bytes){const ssize_t wrote=write(fd,reinterpret_cast<const char*>(labels.data())+done,bytes-done);
        if(wrote<=0){close(fd);throw std::runtime_error("label write failed");}done+=static_cast<size_t>(wrote);}
    const int synced=fsync(fd),closed=close(fd);require(!synced&&!closed,"label fsync/close failed");
    return {{"path",fs::absolute(path).string()},{"sha256",sha256_bytes(labels.data(),bytes)},
            {"dtype","little-endian uint16"},{"header",false},{"rows",labels.size()},{"bytes",bytes}};
}

struct Limits {
    int leaves=leaf_count, per_coarse=leaves_per_coarse, coarse=coarse_count;
    uint64_t leaf_cap=0,coarse_cap=0,min_leaf=minimum_leaf_size;
};
Limits production_limits(uint64_t n) {
    return {leaf_count,leaves_per_coarse,coarse_count,n*6/(5*leaf_count),n*6/(5*coarse_count),minimum_leaf_size};
}
struct Sizes { std::vector<uint64_t> leaf,coarse; };
Sizes sizes_of(const std::vector<uint16_t>& labels,const Limits& lim) {
    Sizes out;out.leaf.assign(lim.leaves,0);out.coarse.assign(lim.coarse,0);
    require(lim.leaves==lim.coarse*lim.per_coarse,"invalid hierarchy dimensions");
    for(auto r:labels){require(r<lim.leaves,"label outside hierarchy");++out.leaf[r];++out.coarse[r/lim.per_coarse];}
    return out;
}
json structure_stats(const std::vector<uint16_t>& labels,const Limits& lim) {
    const auto sizes=sizes_of(labels,lim);json violations=json::array();
    for(int r=0;r<lim.leaves;++r)if(sizes.leaf[r]<lim.min_leaf||sizes.leaf[r]>lim.leaf_cap)
        violations.push_back({{"level","leaf"},{"id",r},{"size",sizes.leaf[r]}});
    for(int r=0;r<lim.coarse;++r)if(sizes.coarse[r]>lim.coarse_cap)
        violations.push_back({{"level","coarse"},{"id",r},{"size",sizes.coarse[r]}});
    return {{"all_nodes_covered",std::accumulate(sizes.leaf.begin(),sizes.leaf.end(),uint64_t(0))==labels.size()},
            {"nodes",labels.size()},{"leaf_sizes",sizes.leaf},{"coarse_sizes",sizes.coarse},
            {"leaf_capacity",lim.leaf_cap},{"coarse_capacity",lim.coarse_cap},{"minimum_leaf_nodes",lim.min_leaf},
            {"minimum_actual_leaf_nodes",*std::min_element(sizes.leaf.begin(),sizes.leaf.end())},
            {"maximum_actual_leaf_nodes",*std::max_element(sizes.leaf.begin(),sizes.leaf.end())},
            {"maximum_actual_coarse_nodes",*std::max_element(sizes.coarse.begin(),sizes.coarse.end())},
            {"violations",violations},{"capacity_and_minimum_pass",violations.empty()}};
}
bool feasible_move(uint16_t old,uint16_t dest,const Sizes& sizes,const Limits& lim) {
    return old!=dest&&sizes.leaf[old]>lim.min_leaf&&sizes.leaf[dest]<lim.leaf_cap&&
        (old/lim.per_coarse==dest/lim.per_coarse||sizes.coarse[dest/lim.per_coarse]<lim.coarse_cap);
}

struct MetisBalance { uint64_t numerator,denominator; real_t target,input,effective; };
MetisBalance strict_metis_balance(uint64_t numerator,uint64_t denominator) {
    require(denominator>0&&numerator>denominator,"METIS target must exceed one");
    const long double exact=static_cast<long double>(numerator)/denominator;
    real_t target=static_cast<real_t>(exact);
    // Conservative conversion and the same library epsilon compensation as P2.
    if(static_cast<long double>(target)>exact)target=std::nextafter(target,real_t(1));
    target=std::nextafter(target,real_t(1));
    const real_t input=std::nextafter(real_t(target-real_t(0.0000499)),real_t(1));
    const real_t effective=real_t(static_cast<double>(input)+0.0000499);
    require(input>1&&static_cast<long double>(effective)<=exact,"METIS strict ubvec compensation failed");
    return {numerator,denominator,target,input,effective};
}
struct PartResult { std::vector<uint16_t> labels;json stats; };
PartResult metis_partition(CSR& csr,int parts,uint64_t cap,uint64_t minimum,
                          uint64_t ub_numerator,uint64_t ub_denominator,bool debug) {
    require(parts>=2&&parts<=csr.n&&parts<65536,"invalid METIS region count");
    require(static_cast<uint64_t>(csr.n)<=uint64_t(parts)*cap,"infeasible global integer partition capacity");
    auto balance=strict_metis_balance(ub_numerator,ub_denominator);real_t ub=balance.input;
    idx_t n=csr.n,ncon=1,nparts=parts,edgecut=0,options[METIS_NOPTIONS];METIS_SetDefaultOptions(options);
    options[METIS_OPTION_SEED]=fixed_seed;options[METIS_OPTION_UFACTOR]=200;
    options[METIS_OPTION_NCUTS]=1;options[METIS_OPTION_NITER]=10;options[METIS_OPTION_NUMBERING]=0;
    options[METIS_OPTION_DBGLVL]=debug?METIS_DBG_TIME:0;
    std::vector<idx_t> raw(static_cast<size_t>(n),-1);
    std::cout<<"PHASE METIS n="<<n<<" parts="<<parts<<" cap="<<cap<<" target_ub="
             <<double(ub_numerator)/ub_denominator<<" effective_ub="<<balance.effective<<std::endl;
    checkpoint();auto started=Clock::now();
    const int rc=METIS_PartGraphKway(&n,&ncon,csr.offsets.data(),csr.edges.data(),nullptr,nullptr,nullptr,
                                   &nparts,nullptr,&ub,options,&edgecut,raw.data());
    require(rc==METIS_OK,"METIS failed return="+std::to_string(rc));
    PartResult result;result.labels.resize(n);std::vector<uint64_t> sizes(parts,0);
    for(idx_t u=0;u<n;++u){require(raw[u]>=0&&raw[u]<parts,"METIS returned invalid region ID");
        result.labels[u]=static_cast<uint16_t>(raw[u]);++sizes[raw[u]];}
    uint64_t crossing=0;
    for(idx_t u=0;u<n;++u)for(idx_t e=csr.offsets[u];e<csr.offsets[u+1];++e)
        crossing+=raw[u]!=raw[csr.edges[e]];
    require(crossing%2==0&&crossing/2==static_cast<uint64_t>(edgecut),"independent METIS cut mismatch");
    json violations=json::array();for(int r=0;r<parts;++r)if(sizes[r]<minimum||sizes[r]>cap)
        violations.push_back({{"region",r},{"size",sizes[r]},{"minimum",minimum},{"capacity",cap}});
    result.stats={{"metis_return_code",rc},{"parts",parts},{"seed",fixed_seed},{"ncuts",1},{"niter",10},
                  {"numbering",0},{"ufactor_unused_when_ubvec_supplied",200},{"metis_idx_bits",64},{"metis_real_bits",32},
                  {"target_ub_rational",{ub_numerator,ub_denominator}},{"conservative_target_real",balance.target},
                  {"input_ubvec",balance.input},{"effective_internal_ubfactor",balance.effective},
                  {"library_added_epsilon",0.0000499},{"effective_bound_pass",true},
                  {"region_sizes",sizes},{"capacity",cap},{"minimum",minimum},{"violations",violations},
                  {"structure_pass",violations.empty()},{"metis_edgecut",edgecut},{"verified_undirected_edgecut",crossing/2},
                  {"metis_and_verification_seconds",elapsed(started)}};
    // Caller persists actual returned labels and diagnostics before rejecting.
    return result;
}
void canonicalize(std::vector<uint16_t>& labels,int parts) {
    std::vector<uint64_t> minima(parts,std::numeric_limits<uint64_t>::max());
    for(size_t u=0;u<labels.size();++u){require(labels[u]<parts,"canonical label invalid");minima[labels[u]]=std::min(minima[labels[u]],uint64_t(u));}
    std::vector<int> order(parts);std::iota(order.begin(),order.end(),0);
    require(*std::max_element(minima.begin(),minima.end())!=std::numeric_limits<uint64_t>::max(),"cannot canonicalize empty regions");
    std::sort(order.begin(),order.end(),[&](int a,int b){return minima[a]<minima[b];});
    std::vector<uint16_t> map(parts);for(int i=0;i<parts;++i)map[order[i]]=i;
    for(auto& label:labels)label=map[label];
}
CSR induced_csr(const CSR& original,const std::vector<int32_t>& members,std::vector<int32_t>& local_map,
                const std::vector<uint16_t>& coarse,uint16_t current) {
    CSR sub;sub.n=members.size();sub.offsets.resize(members.size()+1,0);
    for(size_t i=0;i<members.size();++i)local_map[members[i]]=static_cast<int32_t>(i);
    for(size_t i=0;i<members.size();++i){const int32_t u=members[i];
        for(idx_t e=original.offsets[u];e<original.offsets[u+1];++e)sub.offsets[i+1]+=coarse[original.edges[e]]==current;
        sub.offsets[i+1]+=sub.offsets[i];if((i&65535)==0)checkpoint();}
    sub.edges.resize(sub.offsets.back());
    for(size_t i=0;i<members.size();++i){const int32_t u=members[i];idx_t cursor=sub.offsets[i];
        for(idx_t e=original.offsets[u];e<original.offsets[u+1];++e){const idx_t v=original.edges[e];
            if(coarse[v]==current){require(local_map[v]>=0,"missing induced local ID");sub.edges[cursor++]=local_map[v];}}
        require(cursor==sub.offsets[i+1],"induced CSR fill mismatch");if((i&65535)==0)checkpoint();}
    return sub;
}
std::vector<uint16_t> common_initialization(CSR& csr,const fs::path& output,json& report) {
    const auto dir=output/"initial";require(fs::create_directory(dir),"cannot reserve initial directory");
    const uint64_t n=csr.n,coarse_cap=n*11/(10*coarse_count);const auto lim=production_limits(n);
    report["phase"]="COARSE_METIS";write_json(output/"manifest.json",report);
    auto coarse=metis_partition(csr,coarse_count,coarse_cap,leaves_per_coarse*minimum_leaf_size,11,10,true);
    coarse.stats["raw_labels"]=write_labels_new(dir/"coarse_raw.u16",coarse.labels);
    write_json(dir/"coarse.json",coarse.stats);
    require(coarse.stats.at("structure_pass").get<bool>(),"coarse initialization fails strict capacity/minimum");
    checkpoint();canonicalize(coarse.labels,coarse_count);
    const auto coarse_label_record=write_labels_new(dir/"coarse_canonical.u16",coarse.labels);
    std::vector<uint16_t> labels(n,std::numeric_limits<uint16_t>::max());
    std::vector<int32_t> local_map(n,-1);json children=json::array();auto started=Clock::now();
    for(int c=0;c<coarse_count;++c){
        checkpoint();report["phase"]="CHILD_METIS";report["coarse_child_cursor"]=c;write_json(output/"manifest.json",report);
        std::vector<int32_t> members;members.reserve(coarse_cap);
        for(size_t u=0;u<n;++u)if(coarse.labels[u]==c)members.push_back(static_cast<int32_t>(u));
        require(members.size()<=uint64_t(leaves_per_coarse)*lim.leaf_cap,"child global leaf capacity infeasible");
        auto sub=induced_csr(csr,members,local_map,coarse.labels,c);
        auto child=metis_partition(sub,leaves_per_coarse,lim.leaf_cap,minimum_leaf_size,
                                   leaves_per_coarse*lim.leaf_cap,members.size(),false);
        std::ostringstream name;name<<"child_"<<std::setw(2)<<std::setfill('0')<<c;
        child.stats["coarse_id"]=c;child.stats["member_order"]="ascending global base ID within saved canonical coarse";
        child.stats["raw_local_labels"]=write_labels_new(dir/(name.str()+"_raw.u16"),child.labels);
        write_json(dir/(name.str()+".json"),child.stats);
        require(child.stats.at("structure_pass").get<bool>(),"child initialization fails strict global capacity/minimum");
        canonicalize(child.labels,leaves_per_coarse);
        for(size_t i=0;i<members.size();++i)labels[members[i]]=static_cast<uint16_t>(c*leaves_per_coarse+child.labels[i]);
        children.push_back(child.stats);progress("children",c+1,coarse_count,started);
    }
    auto structure=structure_stats(labels,lim);const auto saved=write_labels_new(dir/"regions.u16",labels);
    json initial={{"status","COMPLETE"},{"coarse_count",coarse_count},{"leaves_per_coarse",leaves_per_coarse},
                  {"regions",leaf_count},{"nodes",n},{"coarse_initial_integer_cap",coarse_cap},
                  {"coarse_canonical_labels",coarse_label_record},{"coarse_metis",coarse.stats},{"children",children},
                  {"labels",saved},{"labels_file",saved.at("path")},{"labels_sha256",saved.at("sha256")},
                  {"structure",structure},{"canonicalized_once_before_branches",true}};
    if(!structure.at("capacity_and_minimum_pass").get<bool>())initial["status"]="INCOMPLETE";
    write_json(dir/"manifest.json",initial);require(initial.at("status")=="COMPLETE","common initialization structure failed");
    report["initialization"]=initial;return labels;
}

struct GraphView { const void* data;int32_t n;int k; };
struct Incoming { std::vector<uint64_t> offsets;std::vector<int32_t> source;uint64_t nonself=0,padding=0,self=0; };
Incoming build_incoming(const GraphView& graph) {
    Incoming in;in.offsets.assign(static_cast<size_t>(graph.n)+1,0);auto begin=Clock::now();double last=0;
    for(int32_t u=0;u<graph.n;++u){for(int j=0;j<graph.k;++j){const auto v=neighbor_at(graph.data,size_t(u)*graph.k+j);
        if(v==-1){++in.padding;continue;}require(v>=0&&v<graph.n,"invalid directed stored edge");
        if(v==u){++in.self;continue;}++in.nonself;++in.offsets[v+1];}
        if((u&65535)==0){checkpoint();if(elapsed(begin)-last>=10){progress("incoming_count",u,graph.n,begin);last=elapsed(begin);}}}
    for(int32_t u=0;u<graph.n;++u)in.offsets[u+1]+=in.offsets[u];
    require(in.offsets.back()==in.nonself,"incoming edge count mismatch");in.source.resize(in.nonself);
    std::vector<uint64_t> cursor(in.offsets.begin(),in.offsets.end()-1);begin=Clock::now();last=0;
    for(int32_t u=0;u<graph.n;++u){for(int j=0;j<graph.k;++j){const auto v=neighbor_at(graph.data,size_t(u)*graph.k+j);
        if(v>=0&&v!=u)in.source[cursor[v]++]=u;}
        if((u&65535)==0){checkpoint();if(elapsed(begin)-last>=10){progress("incoming_fill",u,graph.n,begin);last=elapsed(begin);}}}
    for(int32_t u=0;u<graph.n;++u)require(cursor[u]==in.offsets[u+1],"incoming cursor mismatch");
    return in;
}
struct GTData { std::vector<std::array<int32_t,gt_width>> rows; };
void validate_gt(const GTData& gt,int64_t n) {
    require(!gt.rows.empty(),"GT query set empty");
    for(const auto& row:gt.rows){auto sorted=row;std::sort(sorted.begin(),sorted.end());
        require(sorted.front()>=0&&sorted.back()<n,"GT ID out of range");
        require(std::adjacent_find(sorted.begin(),sorted.end())==sorted.end(),"duplicate GT10 ID in one query");}
}
GTData load_fit_gt(const json& fit,const fs::path& manifest,int64_t n) {
    fs::path path=fit.at("gt10_file").get<std::string>();if(path.is_relative())path=manifest.parent_path()/path;
    const auto bytes=read_small_binary(path);require(bytes.size()==fit_count*gt_width*sizeof(int32_t),"GT10 raw shape mismatch");
    require(sha256_bytes(bytes.data(),bytes.size())==fit.at("gt10_sha256").get<std::string>(),"GT10 SHA mismatch");
    GTData out;out.rows.resize(fit_count);std::memcpy(out.rows.data(),bytes.data(),bytes.size());validate_gt(out,n);return out;
}
struct GTIndex {
    std::vector<uint32_t> offsets,queries;
    explicit GTIndex(const GTData& gt,int n):offsets(static_cast<size_t>(n)+1,0) {
        require(gt.rows.size()*gt_width<std::numeric_limits<uint32_t>::max(),"GT incidence index exceeds uint32");
        for(const auto& row:gt.rows)for(auto id:row)++offsets[id+1];
        for(int u=0;u<n;++u)offsets[u+1]+=offsets[u];
        queries.resize(offsets.back());
        auto cursor=offsets;for(size_t q=0;q<gt.rows.size();++q)for(auto id:gt.rows[q])queries[cursor[id]++]=q;
    }
};
struct GTCounts {
    const GTData* gt=nullptr;const GTIndex* incidence=nullptr;int leaves=0;
    std::vector<uint8_t> counts;
    GTCounts(const GTData& data,const GTIndex& index,const std::vector<uint16_t>& labels,int regions):
        gt(&data),incidence(&index),leaves(regions),counts(data.rows.size()*regions,0) {
        for(size_t q=0;q<data.rows.size();++q)for(auto id:data.rows[q])++counts[q*regions+labels[id]];
    }
};
struct Objective { uint64_t M=0,C=0,S=0,coarse_C=0,coarse_S=0,Q=0; };
Objective full_objective(const GraphView& graph,const std::vector<uint16_t>& labels,const GTData& gt,int per_coarse) {
    require(labels.size()==size_t(graph.n),"objective graph/labels shape mismatch");Objective out;out.Q=gt.rows.size();
    for(int32_t u=0;u<graph.n;++u){for(int j=0;j<graph.k;++j){const int32_t v=neighbor_at(graph.data,size_t(u)*graph.k+j);
        if(v<0||v==u)continue;
        ++out.M;out.C+=labels[u]!=labels[v];out.coarse_C+=labels[u]/per_coarse!=labels[v]/per_coarse;}
        if((u&65535)==0)checkpoint();}
    for(const auto& row:gt.rows){std::array<uint16_t,gt_width> fine{},coarse{};
        for(int j=0;j<gt_width;++j){fine[j]=labels[row[j]];coarse[j]=fine[j]/per_coarse;}
        std::sort(fine.begin(),fine.end());std::sort(coarse.begin(),coarse.end());
        out.S+=std::unique(fine.begin(),fine.end())-fine.begin()-1;
        out.coarse_S+=std::unique(coarse.begin(),coarse.end())-coarse.begin()-1;}
    require(out.M>0&&out.Q>0,"objective requires nonzero original graph M and fit Q");return out;
}
Wide numerator(const Objective& o,int lambda) { return Wide(o.C)*(9*o.Q)+Wide(lambda)*o.S*o.M; }
json objective_json(const Objective& o) {
    return {{"M_original_directed_valid_nonself_slots",o.M},{"C_leaf_directed_crossing_slots",o.C},
            {"S_fit_distinct_leaf_minus_one",o.S},{"Q",o.Q},{"leaf_cut_fraction",double(o.C)/o.M},
            {"fit_leaf_fragmentation_normalized",double(o.S)/(9*o.Q)},{"mean_fit_distinct_leaf_regions",1.0+double(o.S)/o.Q},
            {"J_lambda0",double(o.C)/o.M},{"J_lambda1",double(o.C)/o.M+double(o.S)/(9*o.Q)},
            {"lambda0_exact_numerator",wide_string(numerator(o,0))},{"lambda1_exact_numerator",wide_string(numerator(o,1))},
            {"exact_common_denominator",wide_string(Wide(o.M)*9*o.Q)},
            {"coarse_crossing_slots_report_only",o.coarse_C},{"coarse_cut_fraction_report_only",double(o.coarse_C)/o.M},
            {"coarse_S_report_only",o.coarse_S},{"mean_fit_distinct_coarse_regions_report_only",1.0+double(o.coarse_S)/o.Q}};
}
struct Move { uint16_t destination;int64_t delta_C=0,delta_S=0;Wide delta_numerator=0; };
struct MoveScratch {
    std::array<uint32_t,leaf_count> seen{},query_seen{};
    std::array<int64_t,leaf_count> degree{},presence{};
    std::array<uint16_t,leaf_count> candidates{};uint32_t stamp=0,query_stamp=0;int count=0;
    void reset(){++stamp;count=0;if(!stamp){seen.fill(0);++stamp;}}
    void touch(uint16_t r){if(seen[r]!=stamp){seen[r]=stamp;degree[r]=presence[r]=0;candidates[count++]=r;}}
    int64_t degree_at(uint16_t r) const {return seen[r]==stamp?degree[r]:0;}
};
template<int Lambda>
Move choose_move(int32_t u,const GraphView& graph,const Incoming& incoming,const std::vector<uint16_t>& labels,
                 const Sizes& sizes,const Limits& lim,GTCounts* gt,MoveScratch& scratch,uint64_t M,uint64_t Q) {
    static_assert(Lambda==0||Lambda==1);const uint16_t old=labels[u];Move best{old};
    if(sizes.leaf[old]<=lim.min_leaf)return best;
    if constexpr(Lambda==0)require(gt==nullptr,"lambda0 must not receive GT move inputs");
    else require(gt!=nullptr,"lambda1 missing GT incidence state");
    scratch.reset();
    for(int j=0;j<graph.k;++j){const auto v=neighbor_at(graph.data,size_t(u)*graph.k+j);if(v>=0&&v!=u){const auto r=labels[v];scratch.touch(r);++scratch.degree[r];}}
    for(uint64_t i=incoming.offsets[u];i<incoming.offsets[u+1];++i){const auto r=labels[incoming.source[i]];scratch.touch(r);++scratch.degree[r];}
    int64_t incident=0,old_singles=0;
    if constexpr(Lambda==1){
        for(uint32_t i=gt->incidence->offsets[u];i<gt->incidence->offsets[u+1];++i){const auto q=gt->incidence->queries[i];
            ++incident;old_singles+=gt->counts[size_t(q)*lim.leaves+old]==1;
            if(++scratch.query_stamp==0){scratch.query_seen.fill(0);++scratch.query_stamp;}
            for(auto id:gt->gt->rows[q]){const auto r=labels[id];if(scratch.query_seen[r]==scratch.query_stamp)continue;
                scratch.query_seen[r]=scratch.query_stamp;scratch.touch(r);++scratch.presence[r];}
        }
    }
    std::sort(scratch.candidates.begin(),scratch.candidates.begin()+scratch.count);
    const int64_t old_degree=scratch.degree_at(old);
    for(int i=0;i<scratch.count;++i){const auto dest=scratch.candidates[i];if(!feasible_move(old,dest,sizes,lim))continue;
        const int64_t dc=old_degree-scratch.degree[dest];
        int64_t ds=0;if constexpr(Lambda==1)ds=incident-scratch.presence[dest]-old_singles;
        const Wide score=Wide(dc)*(9*Q)+Wide(Lambda)*ds*M;
        if(score<best.delta_numerator)best={dest,dc,ds,score};
    }
    return best;
}
void commit_move(int32_t u,const Move& move,std::vector<uint16_t>& labels,Sizes& sizes,const Limits& lim,GTCounts* gt) {
    const auto old=labels[u],dest=move.destination;require(feasible_move(old,dest,sizes,lim)&&move.delta_numerator<0,"invalid committed move");
    --sizes.leaf[old];++sizes.leaf[dest];--sizes.coarse[old/lim.per_coarse];++sizes.coarse[dest/lim.per_coarse];
    if(gt)for(uint32_t i=gt->incidence->offsets[u];i<gt->incidence->offsets[u+1];++i){const auto q=gt->incidence->queries[i];
        require(gt->counts[size_t(q)*lim.leaves+old]>0,"GT incremental old count underflow");
        --gt->counts[size_t(q)*lim.leaves+old];++gt->counts[size_t(q)*lim.leaves+dest];}
    labels[u]=dest;
}
struct PassStats {uint64_t cursor=0,moved=0,cross_coarse=0;int64_t delta_C=0,delta_S=0;Wide score_sum=0;double wall_seconds=0;};
json pass_json(const PassStats& p,int lambda) {
    return {{"next_node_cursor",p.cursor},{"accepted_moves",p.moved},{"cross_coarse_moves",p.cross_coarse},
            {"sum_delta_C",p.delta_C},{"sum_delta_S",lambda?json(p.delta_S):json(nullptr)},
            {"GT_S_updated_during_moves",lambda==1},{"sum_exact_delta_numerator",wide_string(p.score_sum)},
            {"all_moves_strictly_negative",true},{"wall_seconds",p.wall_seconds}};
}
template<int Lambda>
void refine_pass(const GraphView& graph,const Incoming& incoming,std::vector<uint16_t>& labels,const Limits& lim,
                 GTCounts* gt,uint64_t M,uint64_t Q,PassStats& stats,const std::function<void(const PassStats&)>& save_progress={}) {
    require(labels.size()==size_t(graph.n),"refinement shape mismatch");
    if constexpr(Lambda==0)require(gt==nullptr,"lambda0 must not receive GT move inputs");
    auto sizes=sizes_of(labels,lim);MoveScratch scratch;auto started=Clock::now();double last=0;
    for(int32_t u=0;u<graph.n;++u){
        const auto move=choose_move<Lambda>(u,graph,incoming,labels,sizes,lim,gt,scratch,M,Q);
        if(move.destination!=labels[u]){stats.cross_coarse+=labels[u]/lim.per_coarse!=move.destination/lim.per_coarse;
            commit_move(u,move,labels,sizes,lim,gt);++stats.moved;stats.delta_C+=move.delta_C;
            stats.delta_S+=move.delta_S;stats.score_sum+=move.delta_numerator;}
        stats.cursor=uint64_t(u)+1;
        if((u&65535)==0){stats.wall_seconds=elapsed(started);checkpoint();
            if(stats.wall_seconds-last>=10){progress(Lambda?"lambda1_refine":"lambda0_refine",stats.cursor,graph.n,started);
                if(save_progress)save_progress(stats);
                last=stats.wall_seconds;}}
    }
    stats.wall_seconds=elapsed(started);progress(Lambda?"lambda1_refine":"lambda0_refine",graph.n,graph.n,started);
}

bool verify_gt_counts(const GTCounts& state,const std::vector<uint16_t>& labels) {
    std::vector<uint8_t> counts(state.counts.size(),0);
    for(size_t q=0;q<state.gt->rows.size();++q)for(auto id:state.gt->rows[q])++counts[q*state.leaves+labels[id]];
    return counts==state.counts;
}
template<int Lambda>
json run_branch(const GraphView& graph,const Incoming& incoming,const GTData& gt,const GTIndex* index,
                const std::vector<uint16_t>& initial,const Objective& initial_objective,const Limits& lim,
                const fs::path& output,const json& provenance) {
    const auto dir=output/(Lambda?"lambda1":"lambda0");require(fs::create_directory(dir),"cannot reserve branch directory");
    auto labels=initial;json branch=provenance;branch["status"]="INCOMPLETE";branch["lambda"]=Lambda;
    branch["passes_required"]=2;branch["passes_completed"]=0;branch["passes"]=json::array();
    branch["initial_objective"]=objective_json(initial_objective);branch["phase"]="READY";
    branch["GT_used_for_move_candidates_or_decisions"]=Lambda==1;
    branch["GT_used_for_posthoc_full_structure_metrics"]=true;
    branch["same_initial_labels_sha256"]=provenance.at("initial_labels_sha256");
    branch["initial_state_copy_sha256"]=sha256_bytes(labels.data(),labels.size()*2);
    require(branch.at("initial_state_copy_sha256")==branch.at("initial_labels_sha256"),"branch initialization differs");
    std::unique_ptr<GTCounts> counts;
    if constexpr(Lambda==1){require(index!=nullptr,"lambda1 GT incidence missing");counts=std::make_unique<GTCounts>(gt,*index,labels,lim.leaves);}
    else require(index==nullptr,"lambda0 driver must not receive incidence index");
    write_json(dir/"manifest.json",branch);
    Objective previous=initial_objective;PassStats stats;int pass=0;auto begin=Clock::now();
    try {
        for(pass=1;pass<=2;++pass){
            stats={};checkpoint();branch["phase"]="REFINE";branch["current_pass"]=pass;
            branch["progress"]=pass_json(stats,Lambda);write_json(dir/"manifest.json",branch);
            refine_pass<Lambda>(graph,incoming,labels,lim,counts.get(),previous.M,previous.Q,stats,[&](const PassStats& p){
                branch["progress"]=pass_json(p,Lambda);write_json(dir/"manifest.json",branch);});
            branch["phase"]="FULL_RECOMPUTE";branch["progress"]=pass_json(stats,Lambda);write_json(dir/"manifest.json",branch);
            const auto verify_start=Clock::now();const auto actual=full_objective(graph,labels,gt,lim.per_coarse);
            const auto structure=structure_stats(labels,lim);
            const bool c_ok=Wide(actual.C)==Wide(previous.C)+stats.delta_C&&actual.M==previous.M;
            const bool s_ok=Lambda==0||Wide(actual.S)==Wide(previous.S)+stats.delta_S;
            const bool j_ok=numerator(actual,Lambda)==numerator(previous,Lambda)+stats.score_sum;
            const bool descent=stats.moved?numerator(actual,Lambda)<numerator(previous,Lambda):numerator(actual,Lambda)==numerator(previous,Lambda);
            const bool counts_ok=counts?verify_gt_counts(*counts,labels):true;
            const auto snapshot=write_labels_new(dir/("pass"+std::to_string(pass)+".regions.u16"),labels);
            auto record=pass_json(stats,Lambda);record["pass"]=pass;record["labels"]=snapshot;
            record["objective"]=objective_json(actual);record["structure"]=structure;
            record["full_recompute"]={{"C_matches_incremental",c_ok},{"S_matches_incremental",Lambda?json(s_ok):json(nullptr)},
                {"lambda0_S_posthoc_only",Lambda==0},{"exact_J_matches_incremental",j_ok},{"pass_strict_descent_if_any_move",descent},
                {"GT_per_query_region_counts_match",Lambda?json(counts_ok):json(nullptr)},
                {"wall_seconds",elapsed(verify_start)}};
            branch["passes"].push_back(record);write_json(dir/("pass"+std::to_string(pass)+".json"),record);
            write_json(dir/"manifest.json",branch);
            require(c_ok&&s_ok&&j_ok&&descent&&counts_ok,"incremental objective/state disagrees with full independent recomputation");
            require(structure.at("capacity_and_minimum_pass").get<bool>(),"refinement violates capacity or minimum leaf size");
            branch["passes_completed"]=pass;branch["labels_file"]=snapshot.at("path");branch["labels_sha256"]=snapshot.at("sha256");
            branch["labels"]=snapshot;branch["final_objective"]=objective_json(actual);branch["structure"]=structure;
            previous=actual;write_json(dir/"manifest.json",branch);
        }
        branch["status"]="COMPLETE";branch["phase"]="DONE";branch["wall_seconds"]=elapsed(begin);
        branch["peak_rss_kib"]=peak_rss_kib();write_json(dir/"manifest.json",branch);return branch;
    } catch(const std::exception& e) {
        branch["status"]="INCOMPLETE";branch["error"]=e.what();branch["current_pass"]=pass;
        branch["progress"]=pass_json(stats,Lambda);branch["wall_seconds"]=elapsed(begin);
        // Compact partial state may be saved after stop; no further objective scan or research work.
        try {branch["incomplete_labels"]=write_labels_new(dir/"incomplete.regions.u16",labels);}catch(const std::exception& write_error){branch["incomplete_snapshot_error"]=write_error.what();}
        write_json(dir/"manifest.json",branch);throw;
    }
}

Objective brute_objective(const GraphView& graph,const std::vector<uint16_t>& labels,const GTData& gt,int per_coarse) {
    Objective o;o.Q=gt.rows.size();
    for(int u=0;u<graph.n;++u)for(int j=0;j<graph.k;++j){const int v=neighbor_at(graph.data,size_t(u)*graph.k+j);
        if(v==-1||v==u)continue;
        ++o.M;if(labels[u]!=labels[v])++o.C;if(labels[u]/per_coarse!=labels[v]/per_coarse)++o.coarse_C;}
    for(const auto& row:gt.rows){std::set<int> fine,coarse;for(int u:row){fine.insert(labels[u]);coarse.insert(labels[u]/per_coarse);}
        o.S+=fine.size()-1;o.coarse_S+=coarse.size()-1;}
    return o;
}
uint64_t brute_cut(const GraphView& graph,const std::vector<uint16_t>& labels) {
    uint64_t cut=0;for(int u=0;u<graph.n;++u)for(int j=0;j<graph.k;++j){int v=neighbor_at(graph.data,size_t(u)*graph.k+j);
        if(v>=0&&v!=u&&labels[u]!=labels[v])++cut;}return cut;
}
// Independent graph-only reference: original stored slots, copied trial labels,
// full cut recomputation, no incoming helper or GT parameter anywhere in API.
std::vector<uint16_t> brute_lambda0(const GraphView& graph,std::vector<uint16_t> labels,const Limits& lim) {
    for(int pass=0;pass<2;++pass)for(int u=0;u<graph.n;++u){
        const auto old=labels[u];const uint64_t before=brute_cut(graph,labels);std::set<uint16_t> candidates;
        for(int v=0;v<graph.n;++v)for(int j=0;j<graph.k;++j){const auto w=neighbor_at(graph.data,size_t(v)*graph.k+j);
            if(w<0||w==v)continue;
            if(v==u)candidates.insert(labels[w]);if(w==u)candidates.insert(labels[v]);}
        std::vector<uint64_t> leaf(lim.leaves,0),coarse(lim.coarse,0);
        for(auto r:labels){++leaf[r];++coarse[r/lim.per_coarse];}
        uint16_t best=old;int64_t best_delta=0;
        for(auto dest:candidates){if(dest==old||leaf[old]<=lim.min_leaf||leaf[dest]>=lim.leaf_cap||
                (old/lim.per_coarse!=dest/lim.per_coarse&&coarse[dest/lim.per_coarse]>=lim.coarse_cap))continue;
            auto trial=labels;trial[u]=dest;int64_t dc=static_cast<int64_t>(brute_cut(graph,trial))-static_cast<int64_t>(before);
            if(dc<best_delta){best_delta=dc;best=dest;}}
        labels[u]=best;
    }
    return labels;
}
std::vector<uint16_t> brute_lambda1(const GraphView& graph,std::vector<uint16_t> labels,const GTData& gt,const Limits& lim) {
    for(int pass=0;pass<2;++pass)for(int u=0;u<graph.n;++u){
        const auto old=labels[u];const auto before=brute_objective(graph,labels,gt,lim.per_coarse);std::set<uint16_t> candidates;
        for(int v=0;v<graph.n;++v)for(int j=0;j<graph.k;++j){const auto w=neighbor_at(graph.data,size_t(v)*graph.k+j);
            if(w<0||w==v)continue;
            if(v==u)candidates.insert(labels[w]);if(w==u)candidates.insert(labels[v]);}
        for(const auto& row:gt.rows)if(std::find(row.begin(),row.end(),u)!=row.end())for(auto v:row)candidates.insert(labels[v]);
        std::vector<uint64_t> leaf(lim.leaves,0),coarse(lim.coarse,0);
        for(auto r:labels){++leaf[r];++coarse[r/lim.per_coarse];}
        uint16_t best=old;Wide best_delta=0;
        for(auto dest:candidates){if(dest==old||leaf[old]<=lim.min_leaf||leaf[dest]>=lim.leaf_cap||
                (old/lim.per_coarse!=dest/lim.per_coarse&&coarse[dest/lim.per_coarse]>=lim.coarse_cap))continue;
            auto trial=labels;trial[u]=dest;const auto after=brute_objective(graph,trial,gt,lim.per_coarse);
            const Wide delta=numerator(after,1)-numerator(before,1);if(delta<best_delta){best_delta=delta;best=dest;}}
        labels[u]=best;
    }
    return labels;
}

json self_test(int threads,const fs::path& output) {
    json tests=json::array();uint64_t delta_cases=0;const int n=48,k=8;
    std::vector<int32_t> raw(n*k,-1);std::mt19937 rng(fixed_seed);
    for(int u=0;u<n;++u){raw[u*k]=(u+1)%n;raw[u*k+1]=(u+n-1)%n;raw[u*k+2]=(u+1)%n;
        raw[u*k+3]=u;raw[u*k+4]=(u+17)%n;raw[u*k+5]=int(rng()%n);}
    GraphView graph{raw.data(),n,k};auto incoming=build_incoming(graph);
    GTData gt;gt.rows.resize(13);
    for(auto& row:gt.rows){std::vector<int32_t> order(n);std::iota(order.begin(),order.end(),0);std::shuffle(order.begin(),order.end(),rng);std::copy_n(order.begin(),gt_width,row.begin());}
    validate_gt(gt,n);const auto index=GTIndex(gt,n);Limits lim{8,4,2,8,28,3};std::vector<uint16_t> initial(n);
    for(int u=0;u<n;++u)initial[u]=u/6;
    require(structure_stats(initial,lim).at("capacity_and_minimum_pass").get<bool>(),"synthetic initial invalid");
    const auto initial_o=full_objective(graph,initial,gt,lim.per_coarse);
    const auto brute_o=brute_objective(graph,initial,gt,lim.per_coarse);
    require(initial_o.M==brute_o.M&&initial_o.C==brute_o.C&&initial_o.S==brute_o.S&&
            initial_o.coarse_C==brute_o.coarse_C&&initial_o.coarse_S==brute_o.coarse_S,"independent full objective mismatch");
    require(incoming.nonself==initial_o.M&&incoming.padding>0&&incoming.self>0,"directed incoming accounting failure");
    GTCounts state(gt,index,initial,lim.leaves);MoveScratch scratch;const auto sizes=sizes_of(initial,lim);
    for(int u=0;u<n;++u){(void)choose_move<1>(u,graph,incoming,initial,sizes,lim,&state,scratch,initial_o.M,initial_o.Q);
        for(int dest=0;dest<lim.leaves;++dest){if(dest==initial[u])continue;
            auto trial=initial;trial[u]=dest;const auto actual=brute_objective(graph,trial,gt,lim.per_coarse);
            const int64_t dc=scratch.degree_at(initial[u])-scratch.degree_at(dest);int64_t ds=0,incident=0,old_singles=0;
            for(uint32_t i=index.offsets[u];i<index.offsets[u+1];++i){const auto q=index.queries[i];++incident;
                old_singles+=state.counts[q*lim.leaves+initial[u]]==1;
                ds+=(state.counts[q*lim.leaves+dest]==0)-(state.counts[q*lim.leaves+initial[u]]==1);}
            const int64_t aggregated_ds=incident-(scratch.seen[dest]==scratch.stamp?scratch.presence[dest]:0)-old_singles;
            require(Wide(actual.C)-initial_o.C==dc&&Wide(actual.S)-initial_o.S==ds&&aggregated_ds==ds,
                    "exhaustive original-directed or aggregate GT move delta mismatch");++delta_cases;
        }
    }
    tests.push_back({{"name","exhaustive_directed_and_GT_delta"},{"cases",delta_cases},{"PASS",true}});
    uint64_t total_moves=0,total_cross=0;
    for(int lambda=0;lambda<=1;++lambda){
        auto labels=initial;auto previous=initial_o;std::unique_ptr<GTCounts> counts;
        if(lambda)counts=std::make_unique<GTCounts>(gt,index,labels,lim.leaves);
        json passes=json::array();
        for(int pass=1;pass<=2;++pass){PassStats p;
            if(lambda)refine_pass<1>(graph,incoming,labels,lim,counts.get(),initial_o.M,initial_o.Q,p);
            else refine_pass<0>(graph,incoming,labels,lim,nullptr,initial_o.M,initial_o.Q,p);
            const auto actual=brute_objective(graph,labels,gt,lim.per_coarse);
            require(Wide(actual.C)==Wide(previous.C)+p.delta_C&&(!lambda||Wide(actual.S)==Wide(previous.S)+p.delta_S),"two-pass delta accumulation mismatch");
            require(numerator(actual,lambda)==numerator(previous,lambda)+p.score_sum,"exact objective numerator mismatch");
            require(structure_stats(labels,lim).at("capacity_and_minimum_pass").get<bool>(),"two-pass capacity/minimum failure");
            if(lambda)require(verify_gt_counts(*counts,labels),"per-query GT count state mismatch");
            total_moves+=p.moved;total_cross+=p.cross_coarse;passes.push_back(pass_json(p,lambda));previous=actual;
        }
        const auto reference=lambda?brute_lambda1(graph,initial,gt,lim):brute_lambda0(graph,initial,lim);
        require(labels==reference,"two-pass refinement differs from independent brute reference");
        auto repeated=initial;std::unique_ptr<GTCounts> again;if(lambda)again=std::make_unique<GTCounts>(gt,index,repeated,lim.leaves);
        for(int pass=0;pass<2;++pass){PassStats p;if(lambda)refine_pass<1>(graph,incoming,repeated,lim,again.get(),initial_o.M,initial_o.Q,p);
            else refine_pass<0>(graph,incoming,repeated,lim,nullptr,initial_o.M,initial_o.Q,p);}
        require(labels==repeated,"two-pass deterministic repeat differs");
        tests.push_back({{"name",lambda?"lambda1_brute_and_determinism":"lambda0_GT_free_brute_and_determinism"},{"PASS",true},
                         {"passes",passes},{"final_labels_sha256",sha256_bytes(labels.data(),labels.size()*2)}});
    }
    require(total_moves>0&&total_cross>0,"synthetic graph failed to exercise improving cross-coarse moves");
    auto boundary=sizes;boundary.leaf[0]=3;require(!feasible_move(0,1,boundary,lim),"minimum3 source constraint failed");
    boundary=sizes;boundary.leaf[1]=lim.leaf_cap;require(!feasible_move(0,1,boundary,lim),"leaf cap failed");
    boundary=sizes;boundary.coarse[1]=lim.coarse_cap;require(!feasible_move(0,4,boundary,lim)&&feasible_move(0,1,boundary,lim),"cross-coarse cap failed");
    bool duplicate_rejected=false,invalid_edge_rejected=false,lambda0_gt_rejected=false;
    try{auto bad=gt;bad.rows[0][1]=bad.rows[0][0];validate_gt(bad,n);}catch(const std::runtime_error&){duplicate_rejected=true;}
    try{auto bad=raw;bad[0]=n;(void)build_incoming({bad.data(),n,k});}catch(const std::runtime_error&){invalid_edge_rejected=true;}
    try{(void)choose_move<0>(0,graph,incoming,initial,sizes,lim,&state,scratch,initial_o.M,initial_o.Q);}catch(const std::runtime_error&){lambda0_gt_rejected=true;}
    require(duplicate_rejected&&invalid_edge_rejected&&lambda0_gt_rejected,"input isolation rejection test failed");
    tests.push_back({{"name","minimum3_leaf_coarse_caps_and_invalid_inputs"},{"PASS",true}});
    const auto web=production_limits(2505000),yan=production_limits(10000000);
    require(web.leaf_cap==11742&&web.coarse_cap==187875&&yan.leaf_cap==46875&&yan.coarse_cap==750000,
            "exact production integer caps differ");
    json balances=json::array();
    for(auto pair:std::vector<std::pair<uint64_t,uint64_t>>{{11,10},{6,5},{16*11742,172218},{16*46875,687500}}){
        const auto b=strict_metis_balance(pair.first,pair.second);
        require(static_cast<long double>(b.effective)*pair.second<=pair.first&&b.input>1,"strict METIS bound test failed");
        balances.push_back({{"target_rational",{pair.first,pair.second}},{"input_ubvec",b.input},{"effective_ub",b.effective}});}
    tests.push_back({{"name","global_integer_caps_and_conservative_METIS_epsilon"},{"PASS",true},{"cases",balances}});
    auto sym=symmetrize(raw.data(),n,k,threads);std::set<std::pair<int,int>> expected;
    for(int u=0;u<n;++u)for(int j=0;j<k;++j){int v=raw[u*k+j];if(v>=0&&v!=u){expected.insert({u,v});expected.insert({v,u});}}
    require(expected.size()==sym.edges.size(),"symmetric initializer dedup count wrong");
    std::vector<uint16_t> coarse(n);for(int u=0;u<n;++u)coarse[u]=u%2;
    std::vector<int32_t> members,local(n,-1);for(int u=0;u<n;++u)if(coarse[u]==0)members.push_back(u);
    auto sub=induced_csr(sym,members,local,coarse,0);
    for(size_t i=0;i<members.size();++i){std::set<int> neighbors;
        for(const auto& edge:expected)if(edge.first==members[i]&&coarse[edge.second]==0)neighbors.insert(local[edge.second]);
        require(std::vector<idx_t>(neighbors.begin(),neighbors.end())==std::vector<idx_t>(sub.edges.begin()+sub.offsets[i],sub.edges.begin()+sub.offsets[i+1]),"induced CSR exact mismatch");}
    std::vector<uint16_t> noncanonical{2,2,0,1,0,1};canonicalize(noncanonical,3);
    require(noncanonical==std::vector<uint16_t>({0,0,1,2,1,2}),"canonical IDs not ordered by first base ID");
    tests.push_back({{"name","symmetric_union_induced_subgraph_canonicalIDs"},{"PASS",true}});
    // Full actual 16x16 METIS initialization on a 4096-node synthetic graph.
    const int hn=4096,hk=8;std::vector<int32_t> hraw(hn*hk,-1);
    for(int u=0;u<hn;++u){const int cluster=u/16,local_id=u%16;
        hraw[u*hk]=cluster*16+(local_id+1)%16;hraw[u*hk+1]=cluster*16+(local_id+15)%16;
        hraw[u*hk+2]=(u+16)%hn;hraw[u*hk+3]=(u+hn-16)%hn;hraw[u*hk+4]=u;hraw[u*hk+5]=hraw[u*hk];}
    auto hcsr=symmetrize(hraw.data(),hn,hk,threads);const auto init_dir=output/"hierarchy_fixture";
    require(fs::create_directory(init_dir),"cannot create hierarchy fixture");json hreport={{"status","INCOMPLETE"}};
    const auto hierarchy=common_initialization(hcsr,init_dir,hreport);
    require(structure_stats(hierarchy,production_limits(hn)).at("capacity_and_minimum_pass").get<bool>(),"full synthetic hierarchy failed");
    tests.push_back({{"name","full_common_16x16_METIS_global_caps"},{"PASS",true},{"nodes",hn},
                     {"labels_sha256",sha256_bytes(hierarchy.data(),hierarchy.size()*2)}});
    return {{"status","PASS_SYNTHETIC_HIERARCHY_TESTS"},{"tests",tests},{"directed_delta_cases",delta_cases},
            {"improving_moves_exercised",total_moves},{"cross_coarse_moves_exercised",total_cross},
            {"real_graph_GT_or_search_accessed",false},{"performance_gate_passed",false}};
}

struct Args {
    fs::path graph,audit,gate,protocol,fit_manifest,source_file=__FILE__,output;
    std::string dataset;int threads=16;bool synthetic=false;
};
Args parse(int argc,char** argv) {
    Args a;
    for(int i=1;i<argc;++i){const std::string key=argv[i];
        if(key=="--help"){
            std::cout<<"CPU P3 common16x16 hierarchy and exact two-pass lambda0/1 refinement\n"
                     <<"Real: --graph PATH --dataset KEY --audit P0_JSON --gate P2_JSON --protocol P3_JSON "
                     <<"--fit-manifest FIT_JSON --output NEW_DIR [--source-file SOURCE_CPP --threads16]\n"
                     <<"Synthetic only: --self-test --output NEW_DIR [--threads N]\n"
                     <<"No lambda/pass/seed tuning flags. Actual graph jobs must use the root deadline controller.\n";std::exit(0);}
        if(key=="--self-test"){a.synthetic=true;continue;}
        require(i+1<argc,"missing option value: "+key);const std::string value=argv[++i];
        if(key=="--graph")a.graph=value;else if(key=="--dataset")a.dataset=value;
        else if(key=="--audit")a.audit=value;else if(key=="--gate")a.gate=value;
        else if(key=="--protocol")a.protocol=value;else if(key=="--fit-manifest")a.fit_manifest=value;
        else if(key=="--source-file")a.source_file=value;else if(key=="--output")a.output=value;
        else if(key=="--threads")a.threads=std::stoi(value);else throw std::runtime_error("unknown option: "+key);
    }
    require(!a.output.empty()&&a.threads>=1&&a.threads<=16,"require output and threads1..16");
    if(!a.synthetic)require(!a.graph.empty()&&!a.dataset.empty()&&!a.audit.empty()&&!a.gate.empty()&&
        !a.protocol.empty()&&!a.fit_manifest.empty()&&a.threads==16,"real hierarchy requires all inputs and fixedthreads16");
    return a;
}
uint64_t available_ram_bytes() {
    std::ifstream f("/proc/meminfo");std::string line;
    while(std::getline(f,line))if(line.rfind("MemAvailable:",0)==0){std::istringstream in(line.substr(13));uint64_t kib=0;in>>kib;return kib*1024;}
    throw std::runtime_error("cannot read MemAvailable");
}
int main(int argc,char** argv) {
    std::signal(SIGTERM,signal_handler);std::signal(SIGINT,signal_handler);
    Args a;json report;bool reserved=false;const auto started=Clock::now();
    try {
        a=parse(argc,argv);checkpoint();
        const uint16_t endian=1;require(*reinterpret_cast<const uint8_t*>(&endian)==1,"little-endian host required");
        json ds,fit,protocol;std::string audit_sha,fit_sha,protocol_sha,gate_sha;
        const auto source_sha=file_sha(a.source_file),binary_sha=file_sha("/proc/self/exe");
        if(!a.synthetic){
            require(source_sha==P3_SOURCE_SHA256,"runtime source differs from compile-time source SHA256 binding");
            protocol=read_json(a.protocol);protocol_sha=file_sha(a.protocol);
            require(protocol_sha=="fea64bc3c6a8046378849f55508198dcfd9a00df880a74e9d93cf22d051a418f",
                    "P3 preregistered protocol changed; no implicit alternative protocol accepted");
            require(protocol.at("status")=="PREREGISTERED_BEFORE_IMPLEMENTATION_AND_DATA"&&protocol.at("stage")=="P3","P3 prereg required");
            const auto gate=read_json(a.gate);gate_sha=file_sha(a.gate);
            require(gate.at("stage")=="P2"&&gate.at("status")=="PASS","P2 PASS required");
            require(fs::canonical(a.gate)==fs::canonical(protocol.at("upstream_P2").at("path").get<std::string>())&&
                    gate_sha==protocol.at("upstream_P2").at("sha256").get<std::string>(),"P2 gate differs from P3 prereg binding");
            const auto audit=read_json(a.audit);audit_sha=file_sha(a.audit);
            require(audit.at("status")=="PASS_INPUT_CONTRACT","P0 input contract audit required");
            require(a.dataset=="webvid2_5m_light_v1"||a.dataset=="yandex_t2i_official10M_ip_v1","unregistered P3 dataset");
            for(const auto& row:audit.at("datasets"))if(row.at("dataset")==a.dataset)ds=row;
            require(!ds.is_null(),"dataset not in P0 audit");
            require(fs::canonical(a.graph)==fs::canonical(ds.at("graph").at("path").get<std::string>()),"graph path differs from P0");
            fit=read_json(a.fit_manifest);fit_sha=file_sha(a.fit_manifest);
            require(fit.at("status")=="COMPLETE"&&fit.at("stage")=="P3"&&fit.at("dataset")==a.dataset,
                    "fit manifest completion/stage/dataset mismatch");
            require(fit.at("fit_range")==json::array({10000,30000})&&fit.at("fit_count")==fit_count&&
                    fit.at("heldout_accessed")==false&&fit.at("pilot_accessed")==false,"fit input split isolation mismatch");
            require(fit.at("input_audit_sha256")==audit_sha&&fit.at("protocol_sha256")==protocol_sha,
                    "fit input audit/protocol binding differs");
            require(fit.at("fit_gt_values_sha256")==ds.at("fit").at("gt_values_sha256"),"fit top100 GT identity differs from P0");
            require(available_ram_bytes()>=(60ULL<<30),"require at least60GiB available RAM before P3 partition");
            require(fs::space(a.output.parent_path()).available>=(10ULL<<30),"require10GiB free disk before P3 partition");
        }
        require(!fs::exists(a.output)&&fs::create_directory(a.output),"output directory must be new and parent must exist");reserved=true;
        report={{"schema_version",1},{"stage","P3"},{"status","INCOMPLETE"},{"phase","STARTED"},{"cpu_only",true},
                {"synthetic",a.synthetic},{"heldout_accessed",false},{"pilot_accessed",false},{"base_or_graph_copied",false},
                {"search_graph_modified",false},{"CSR_saved_to_disk",false},{"threads_preprocessing",a.threads},{"metis_threads",1},
                {"source_file",fs::absolute(a.source_file).string()},{"source_sha256",source_sha},{"binary_sha256",binary_sha},
                {"compile_time_source_sha256",P3_SOURCE_SHA256},{"P3_stage_gate_passed",false},
                {"softclose_utc","2026-09-07T22:59:00Z"},{"deadline_utc","2026-09-07T23:00:00Z"}};
        write_json(a.output/"manifest.json",report);
        if(a.synthetic){report["tests"]=self_test(a.threads,a.output);report["status"]="PASS_SYNTHETIC_HIERARCHY_TESTS";}
        else {
            report["dataset"]=a.dataset;report["input_audit_path"]=fs::canonical(a.audit).string();report["input_audit_sha256"]=audit_sha;
            report["p2_gate_path"]=fs::canonical(a.gate).string();report["p2_gate_sha256"]=gate_sha;
            report["protocol_path"]=fs::canonical(a.protocol).string();report["protocol_sha256"]=protocol_sha;
            report["fit_manifest_file"]=fs::canonical(a.fit_manifest).string();report["fit_manifest_sha256"]=fit_sha;
            report["fit_gt_values_sha256"]=fit.at("fit_gt_values_sha256");report["gt10_sha256"]=fit.at("gt10_sha256");
            report["input_graph_path"]=fs::canonical(a.graph).string();report["input_graph_sha256"]=ds.at("graph").at("sha256");
            report["graph_checksum_verification"]="Full checksum inherited from current P0; no graph/base repeated hash or vector reads";
            MappedGraph mapped(a.graph);
            require(mapped.h.n<=std::numeric_limits<int32_t>::max()&&mapped.h.n==ds.at("graph").at("header").at("n").get<int64_t>()&&
                    mapped.h.d==ds.at("graph").at("header").at("d").get<int>()&&mapped.h.bytes==ds.at("graph").at("header").at("bytes").get<uint64_t>(),
                    "graph header/length differs from P0");
            report["n"]=mapped.h.n;report["nodes"]=mapped.h.n;report["regions"]=leaf_count;report["coarse_count"]=coarse_count;
            report["leaves_per_coarse"]=leaves_per_coarse;report["d"]=mapped.h.d;report["fit_range"]={10000,30000};report["fit_count"]=fit_count;
            report["graph_adjacency_offset"]=mapped.h.adjacency_offset;report["phase"]="SYMMETRIC_CSR";write_json(a.output/"manifest.json",report);
            const GraphView graph{mapped.adjacency,static_cast<int32_t>(mapped.h.n),mapped.h.k};std::vector<uint16_t> initial;
            {auto csr=symmetrize(graph.data,graph.n,graph.k,a.threads);report["initializer_CSR"]=csr.stats;
                initial=common_initialization(csr,a.output,report);}
            // Large i64 initializer CSR is released before incoming CSR/refinement.
            report["phase"]="INCOMING_CSR";write_json(a.output/"manifest.json",report);const auto incoming_start=Clock::now();
            const auto incoming=build_incoming(graph);
            report["incoming_CSR"]={{"offset_bytes",incoming.offsets.size()*sizeof(uint64_t)},{"source_bytes",incoming.source.size()*sizeof(int32_t)},
                {"directed_nonself_slots",incoming.nonself},{"padding_slots",incoming.padding},{"self_slots",incoming.self},
                {"duplicates_and_direction_preserved",true},{"wall_seconds",elapsed(incoming_start)}};
            require(incoming.nonself==report.at("initializer_CSR").at("nonself_directed_slots").get<uint64_t>(),"initializer/original directed edge totals differ");
            report["phase"]="FIT_GT10_AND_INITIAL_OBJECTIVE";write_json(a.output/"manifest.json",report);auto phase_start=Clock::now();
            const auto gt=load_fit_gt(fit,a.fit_manifest,graph.n);report["fit_gt10_load_validate_seconds"]=elapsed(phase_start);
            phase_start=Clock::now();const auto initial_o=full_objective(graph,initial,gt,leaves_per_coarse);
            report["initial_objective"]=objective_json(initial_o);report["initial_objective_seconds"]=elapsed(phase_start);
            report["initial_labels_sha256"]=report.at("initialization").at("labels_sha256");
            auto initial_manifest=read_json(a.output/"initial/manifest.json");initial_manifest["objective"]=objective_json(initial_o);
            initial_manifest["protocol_sha256"]=protocol_sha;initial_manifest["input_audit_sha256"]=audit_sha;
            initial_manifest["fit_manifest_sha256"]=fit_sha;initial_manifest["source_sha256"]=source_sha;initial_manifest["binary_sha256"]=binary_sha;
            write_json(a.output/"initial/manifest.json",initial_manifest);
            json provenance;
            for(const auto& key:{"schema_version","stage","dataset","n","nodes","regions","coarse_count","leaves_per_coarse","d",
                "cpu_only","heldout_accessed","pilot_accessed","input_audit_path","input_audit_sha256","p2_gate_path","p2_gate_sha256",
                "protocol_path","protocol_sha256","fit_manifest_file","fit_manifest_sha256","fit_gt_values_sha256","gt10_sha256",
                "input_graph_path","input_graph_sha256","graph_checksum_verification","source_file","source_sha256","binary_sha256",
                "compile_time_source_sha256","fit_range","fit_count","initial_labels_sha256","P3_stage_gate_passed"})provenance[key]=report.at(key);
            const auto lim=production_limits(graph.n);report["phase"]="LAMBDA0";write_json(a.output/"manifest.json",report);
            report["lambda0"]=run_branch<0>(graph,incoming,gt,nullptr,initial,initial_o,lim,a.output,provenance);
            report["phase"]="BUILD_GT_INCIDENCE_FOR_LAMBDA1";write_json(a.output/"manifest.json",report);phase_start=Clock::now();
            const GTIndex index(gt,graph.n);report["GT_incidence_build_seconds"]=elapsed(phase_start);
            report["phase"]="LAMBDA1";write_json(a.output/"manifest.json",report);
            report["lambda1"]=run_branch<1>(graph,incoming,gt,&index,initial,initial_o,lim,a.output,provenance);
            require(report.at("lambda0").at("status")=="COMPLETE"&&report.at("lambda1").at("status")=="COMPLETE", "both branches must complete");
            report["status"]="COMPLETE";report["hierarchy_correctness_pass"]=true;
        }
        report["phase"]="DONE";report["wall_seconds"]=elapsed(started);report["peak_rss_kib"]=peak_rss_kib();
        write_json(a.output/"manifest.json",report);std::cout<<report.dump(2)<<std::endl;return 0;
    } catch(const std::exception& e) {
        std::cerr<<"ERROR "<<e.what()<<std::endl;
        if(reserved){report["status"]="INCOMPLETE";report["error"]=e.what();report["wall_seconds"]=elapsed(started);report["peak_rss_kib"]=peak_rss_kib();
            try{write_json(a.output/"manifest.json",report);}catch(...){}}
        return 1;
    }
}

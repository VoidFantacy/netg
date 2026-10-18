// E183 common native implementation and TRAIN-only residual compiler.
// The E180 posting runtime is metric-generic: it compares the actual native
// lower-is-better scalar distance, which is negative IP or squared L2.
#include "../../20261015_m5_k100_capacity_v1/src/capacity.hpp"
#include <openssl/evp.h>
#include <iomanip>
#include <numeric>
#include <queue>
#include <sstream>
#include <unordered_map>

namespace e183 {
using namespace exp172;
using Posting = exp180::cap::Posting;

inline void fresh_json(const fs::path& p,const json& j){require(!fs::exists(p),"preserve "+p.string());write_json(p,j);}
inline void fresh_dir(const fs::path& p){require(!fs::exists(p),"fresh directory required "+p.string());fs::create_directories(p);}
inline void check_threads(const json& c){require(c.at("threads")==1&&c.at("cpu")==15,"T1 CPU15 config");threads();}
inline bool equal_float(float a,float b){return !std::memcmp(&a,&b,4);}

struct Mapped {
    int fd=-1;size_t bytes=0;const uint8_t* data=nullptr;
    explicit Mapped(const std::string& p){fd=open(p.c_str(),O_RDONLY);require(fd>=0,"open "+p);struct stat s{};
        require(!fstat(fd,&s)&&s.st_size>0,"nonempty mapped file");bytes=s.st_size;
        auto* mem=mmap(nullptr,bytes,PROT_READ,MAP_SHARED,fd,0);require(mem!=MAP_FAILED,"read-only mmap");data=(const uint8_t*)mem;}
    Mapped(const Mapped&)=delete;Mapped& operator=(const Mapped&)=delete;
    ~Mapped(){if(data)munmap((void*)data,bytes);if(fd>=0)close(fd);}
};
struct Matrix {
    Mapped file;std::string format;size_t n,d,start,total,stride,offset;
    explicit Matrix(const json& c):file(c.at("path")),format(c.at("format")),n(c.at("n")),d(c.at("d")),start(c.value("row_start",size_t(0))){
        require(n>0&&d>0,"matrix nonempty shape");offset=0;
        if(format=="fvecs") {stride=(d+1)*4;require(file.bytes%stride==0,"fvecs exact layout");total=file.bytes/stride;}
        else if(format=="fbin") {require(file.bytes>=8,"fbin header");uint32_t h[2];std::memcpy(h,file.data,8);
            require(h[1]==d,"fbin d");total=h[0];stride=d*4;offset=8;require(file.bytes==8+total*stride,"fbin exact bytes");}
        else {require(format=="raw_f32","supported vector format");stride=d*4;require(file.bytes%stride==0,"raw matrix layout");total=file.bytes/stride;}
        require(start<=total&&n<=total-start,"requested matrix window");if(c.contains("total_n"))require(c.at("total_n")==total,"full matrix container n");
    }
    const float* row(size_t i)const{require(i<n,"matrix row bounds");const auto* p=file.data+offset+(start+i)*stride;
        if(format=="fvecs"){int32_t rd;std::memcpy(&rd,p,4);require(rd==int32_t(d),"every consumed fvec row dimension");p+=4;}return (const float*)p;}
    std::vector<float> copy()const{std::vector<float> result(n*d);for(size_t i=0;i<n;++i){auto* p=row(i);for(size_t j=0;j<d;++j)require(std::isfinite(p[j]),"finite query words");std::copy(p,p+d,result.begin()+i*d);}return result;}
};
std::vector<int32_t> read_gt(const json& c,size_t N){
    Mapped f(c.at("path"));const std::string fmt=c.at("format");const size_t n=c.at("n"),k=c.at("k"),start=c.value("row_start",size_t(0));
    require(k==100&&n>0,"TRAIN GT100 nonempty");const size_t width=fmt=="raw_i64"?8:4;
    require(fmt=="raw_i32"||fmt=="raw_i64"||fmt=="ivecs","supported GT format");const size_t stride=(k+(fmt=="ivecs"))*width;
    require(f.bytes%stride==0,"GT complete layout");const size_t total=f.bytes/stride;
    require(start<=total&&n<=total-start,"GT consumed window");if(c.contains("total_n"))require(c.at("total_n")==total,"GT container rows");
    std::vector<int32_t> gt(n*k);for(size_t i=0;i<n;++i){const uint8_t* p=f.data+(start+i)*stride;
        if(fmt=="ivecs"){int32_t kk;std::memcpy(&kk,p,4);require(kk==100,"GT ivecs row width");p+=4;}
        std::set<int32_t> seen;for(size_t j=0;j<k;++j){int64_t id;if(width==8)std::memcpy(&id,p+j*width,8);else {int32_t v;std::memcpy(&v,p+j*width,4);id=v;}
            require(id>=0&&size_t(id)<N&&seen.insert(int32_t(id)).second,"GT unique in-domain ID");gt[i*k+j]=id;}}
    return gt;
}
std::unique_ptr<acsg::IndexACSGFlat> load_index(const json& c,json& binding){
    const auto start=Clock::now();auto idx=std::make_unique<acsg::IndexACSGFlat>();idx->loadACPG(c.at("index").get<std::string>().c_str());
    std::vector<float>().swap(idx->acsg.pheromone);std::vector<float>().swap(idx->acsg.weight);
    const int metric=c.at("metric_id");require((metric==0||metric==1)&&int(idx->metric_type)==metric,"actual declared IP=0 / L2=1 metric");
    Matrix base(c.at("base"));require(base.start==0&&base.n==size_t(idx->ntotal)&&base.d==size_t(idx->d),"base/index shape");
    auto* flat=dynamic_cast<faiss::IndexFlat*>(idx->storage);require(flat&&int(flat->metric_type)==metric,"Flat metric matches index");
    require(idx->acsg.final_graph&&idx->acsg.final_graph->N==idx->ntotal&&idx->acsg.final_graph->K>0,"loaded graph domain");
    const size_t samples=std::min<size_t>(256,base.n);for(size_t j=0;j<samples;++j){const size_t i=samples==1?0:j*(base.n-1)/(samples-1);
        const float* row=base.row(i);require(!std::memcmp(row,flat->get_xb()+i*idx->d,idx->d*4),"sampled embedded base words");
        for(size_t t=0;t<base.d;++t)require(std::isfinite(row[t]),"sampled finite base");}
    binding={{"metric_id",metric},{"N",idx->ntotal},{"d",idx->d},{"sampled_embedded_base_rows",samples},{"sampled_words_equal",true},
             {"full_embedded_base_audit",false},{"full_source_identity_authority","external execution lock SHA256"},{"startup_seconds",seconds(start)}};return idx;
}
struct Router {
    std::string name,order;size_t d;std::vector<int32_t> ids;std::vector<float> W;hnswlib::InnerProductSpace space;std::unique_ptr<HNSW> graph;
    Router(const json& c,size_t dim,size_t N):name(c.at("name")),order(c.at("route_order")),d(dim),space(d){
        require(order=="heap_pop"||order=="sorted_ids","explicit historic route order");ids=read_raw<int32_t>(c.at("ids").get<std::string>());W=read_raw<float>(c.at("W").get<std::string>());
        require(ids.size()>=3&&W.size()==ids.size()*d&&std::set<int32_t>(ids.begin(),ids.end()).size()==ids.size(),"router shape and unique labels");
        for(int32_t id:ids)require(id>=0&&size_t(id)<N,"real hub domain");for(float v:W)require(std::isfinite(v),"finite profile");
        graph=std::make_unique<HNSW>(&space,c.at("graph").get<std::string>(),false,ids.size());graph->setEf(10);
        require(graph->cur_element_count==ids.size(),"actual router H");for(size_t i=0;i<ids.size();++i){require(graph->getExternalLabel(i)==size_t(ids[i]),"all actual router labels");
            require(!std::memcmp(graph->getDataByInternalId(i),W.data()+i*d,d*4),"all actual router W words");}
    }
    RouteData route(const float* q){auto h=graph->searchKnn(q,3);require(h.size()==3,"router three returned hubs");
        std::array<std::pair<int32_t,float>,3> p;for(auto& x:p){x={int32_t(h.top().second),h.top().first};h.pop();}
        if(order=="sorted_ids")std::sort(p.begin(),p.end(),[](auto a,auto b){return a.first<b.first;});RouteData r;
        for(int j=0;j<3;++j){r.ids[j]=p[j].first;r.distances[j]=p[j].second;}return r;
    }
};
struct Method {std::string name,family,router,baseline;Router* route=nullptr;Posting* table=nullptr;};
void run_batch(acsg::IndexACSGFlat& idx,const std::vector<float>& q,int L,const Method& m,Batch& b){
    require(L>=int(b.k)&&q.size()>=b.n*idx.d,"search shape/L");idx.acsg.search_L=L;
    std::vector<std::vector<acsg::EnterPoint>> eps(b.n);
    for(size_t i=0;i<b.n;++i){if(m.route){auto r=m.route->route(q.data()+i*idx.d);for(int j=0;j<3;++j){b.entries[3*i+j]=r.ids[j];b.profile_distances[3*i+j]=r.distances[j];eps[i].emplace_back(r.ids[j],1.f);}}
        else {b.entries[3*i]=idx.acsg.enterpoint;b.entries[3*i+1]=b.entries[3*i+2]=-1;eps[i].emplace_back(idx.acsg.enterpoint,1.f);}}
    faiss::VisitedTable vt(idx.ntotal);std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx.storage));
    std::vector<acsg::Neighbor> ret;std::vector<faiss::idx_t> ids(b.k);
    for(size_t i=0;i<b.n;++i){dc->set_query(q.data()+i*idx.d);vt.advance();idx.acsg.search_new(*dc,b.k,ids.data(),b.distances.data()+i*b.k,vt,2,eps[i],&ret);
        if(m.table)exp180::cap::apply(*dc,*idx.acsg.final_graph,vt,{{b.entries[3*i],b.entries[3*i+1],b.entries[3*i+2]}},b.k,ids.data(),b.distances.data()+i*b.k,*m.table);
        for(size_t j=0;j<b.k;++j)b.ids[i*b.k+j]=ids[j];}
}
void validate(const Batch& b,size_t N){for(size_t i=0;i<b.n;++i){std::set<int32_t> seen;for(size_t j=0;j<b.k;++j){auto id=b.ids[i*b.k+j];float v=b.distances[i*b.k+j];
    require(id>=0&&size_t(id)<N&&seen.insert(id).second&&std::isfinite(v),"valid unique finite packet");if(j)require(v>=b.distances[i*b.k+j-1],"ascending native distance");}}}
void copy_packet(const Batch& from,Batch& to){require(from.n==to.n&&from.k==to.k,"copy shape");
    std::copy(from.ids.begin(),from.ids.end(),to.ids.begin());std::copy(from.distances.begin(),from.distances.end(),to.distances.begin());
    std::copy(from.entries.begin(),from.entries.end(),to.entries.begin());std::copy(from.profile_distances.begin(),from.profile_distances.end(),to.profile_distances.begin());
    std::copy(from.route_ndc.begin(),from.route_ndc.end(),to.route_ndc.begin());std::copy(from.graph_ndc.begin(),from.graph_ndc.end(),to.graph_ndc.begin());}
std::string packet_sha(const Batch& b){EVP_MD_CTX* ctx=EVP_MD_CTX_new();require(ctx,"SHA context");require(EVP_DigestInit_ex(ctx,EVP_sha256(),nullptr)==1,"SHA init");
    auto add=[&](const void* p,size_t n){require(EVP_DigestUpdate(ctx,p,n)==1,"SHA update");};const uint64_t shape[2]={b.n,b.k};add(shape,sizeof(shape));
    add(b.ids.data(),b.ids.size()*4);add(b.distances.data(),b.distances.size()*4);add(b.entries.data(),b.entries.size()*4);add(b.profile_distances.data(),b.profile_distances.size()*4);
    add(b.route_ndc.data(),b.route_ndc.size()*8);add(b.graph_ndc.data(),b.graph_ndc.size()*8);unsigned char digest[32];unsigned int len=0;
    require(EVP_DigestFinal_ex(ctx,digest,&len)==1&&len==32,"SHA final");EVP_MD_CTX_free(ctx);std::ostringstream s;for(auto v:digest)s<<std::hex<<std::setfill('0')<<std::setw(2)<<int(v);return s.str();}
void all_same(const Batch& a,const Batch& b){same(a,b);require(a.route_ndc==b.route_ndc&&a.graph_ndc==b.graph_ndc,"six-vector full bit parity");}
void audit_merge(acsg::IndexACSGFlat& idx,const std::vector<float>& q,const Batch& main,const Batch& final,const Posting& post){
    require(main.n==final.n&&main.k==final.k&&main.entries==final.entries&&!std::memcmp(main.profile_distances.data(),final.profile_distances.data(),main.profile_distances.size()*4),"matched actual baseline routes");
    using Item=Posting::Record;std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(idx.storage));
    for(size_t i=0;i<main.n;++i){dc->set_query(q.data()+i*idx.d);std::vector<int32_t> cand;
        for(int j=0;j<3;++j){auto it=std::find(post.labels.begin(),post.labels.end(),main.entries[3*i+j]);require(it!=post.labels.end(),"oracle complete hub lookup");size_t row=it-post.labels.begin();
            for(int t=0;t<post.counts[row];++t){int32_t id=post.targets[row*post.b+t];if(std::find(main.ids.begin()+i*main.k,main.ids.begin()+(i+1)*main.k,id)==main.ids.begin()+(i+1)*main.k&&std::find(cand.begin(),cand.end(),id)==cand.end())cand.push_back(id);}}
        std::vector<Item> out;for(size_t j=0;j<main.k;++j){int32_t id=main.ids[i*main.k+j];float value=(*dc)(id);require(equal_float(value,main.distances[i*main.k+j]),"cached native main score equals fresh scalar");out.push_back({id,value,uint32_t(j),false});}
        for(size_t t=0;t<cand.size();++t){Item in{cand[t],(*dc)(cand[t]),uint32_t(main.k+t),false};require(std::isfinite(in.distance),"finite oracle candidate");
            size_t worst=0;for(size_t j=1;j<out.size();++j)if(Posting::better(out[worst],out[j]))worst=j;
            if(in.distance<out[worst].distance)out[worst]=in;}
        if(!cand.empty())std::sort(out.begin(),out.end(),Posting::better);
        for(size_t j=0;j<main.k;++j)require(out[j].id==final.ids[i*main.k+j]&&equal_float(out[j].distance,final.distances[i*main.k+j]),"independent linear full merge oracle");
    }
}
json teacher(const json& c){check_threads(c);require(c.at("teacher_K")==100&&c.at("teacher_L")==200,"fixed teacher K100 L200");
    const auto started=Clock::now();const fs::path root=c.at("output_dir");fresh_dir(root);json binding;auto idx=load_index(c,binding);Matrix input(c.at("queries"));require(input.d==size_t(idx->d),"teacher query d");auto q=input.copy();
    json results=json::array();std::set<std::string> names;for(const auto& rc:c.at("routers")){Router router(rc,idx->d,idx->ntotal);require(names.insert(router.name).second,"unique teacher router");
        Method method;method.name=router.name;method.family="GT10";method.route=&router;method.router=router.name;Batch batch(input.n,100);
        check_threads(c);const auto t=Clock::now();run_batch(*idx,q,200,method,batch);double wall=seconds(t);validate(batch,idx->ntotal);check_threads(c);
        const auto dir=root/router.name;batch.save(dir/"raw",false);json result={{"status","PASS_TRAIN_TEACHER"},{"dataset",c.at("dataset")},{"name",router.name},{"n",input.n},{"K",100},{"L",200},
            {"metric_id",c.at("metric_id")},{"route_order",router.order},{"threads",1},{"cpu",15},{"teacher_body_seconds",wall},{"packet_sha256",packet_sha(batch)},{"raw_dir",(dir/"raw").string()},
            {"any_GT_read",false},{"test_queries_read",false},{"formal_QPS",nullptr}};fresh_json(dir/"complete.json",result);results.push_back(result);std::cout<<result.dump()<<std::endl;}
    json r={{"status","PASS_E183_TRAIN_TEACHERS"},{"dataset",c.at("dataset")},{"config",c},{"loaded_index",binding},{"results",results},{"outer_seconds",seconds(started)}};
    fresh_json(root/"complete.json",r);return r;
}

struct Edge {int32_t row,target;std::vector<uint32_t> tokens;bool selected=false;};
struct Candidate {uint32_t gain,index;int32_t row,target;};
struct CandidateLess {bool operator()(const Candidate& a,const Candidate& b)const{
    if(a.gain!=b.gain)return a.gain<b.gain;if(a.row!=b.row)return a.row>b.row;return a.target>b.target;}};
using Rows=std::vector<std::vector<int32_t>>;
using Heap=std::priority_queue<Candidate,std::vector<Candidate>,CandidateLess>;
uint32_t gain(const Edge& e,const std::vector<uint8_t>& covered){uint32_t result=0;for(auto t:e.tokens)result+=!covered[t];return result;}
json extend(std::vector<Edge>& edges,std::vector<uint8_t>& covered,Rows& rows,int cap){
    Heap heap;for(uint32_t i=0;i<edges.size();++i){const auto& e=edges[i];if(!e.selected&&rows[e.row].size()<size_t(cap)){auto g=gain(e,covered);if(g)heap.push({g,i,e.row,e.target});}}
    json log=json::array();while(!heap.empty()){auto item=heap.top();heap.pop();auto& e=edges[item.index];if(e.selected||rows[e.row].size()>=size_t(cap))continue;
        const uint32_t current=gain(e,covered);if(!current)continue;if(current<item.gain){heap.push({current,item.index,e.row,e.target});continue;}
        require(current==item.gain,"lazy gain only decreases");e.selected=true;rows[e.row].push_back(e.target);for(auto t:e.tokens)covered[t]=1;
        log.push_back({{"row",e.row},{"target",e.target},{"gain",current}});}
    return log;
}
void export_table(const fs::path& path,const std::vector<int32_t>& labels,const Rows& rows,size_t N,int cap){
    uint32_t H=labels.size(),hash_n=1,pairs=0;while(hash_n<2*H)hash_n*=2;for(const auto& r:rows)pairs+=r.size();
    std::vector<uint8_t> out;auto append=[&](const void* p,size_t size){auto b=(const uint8_t*)p;out.insert(out.end(),b,b+size);};
    append("M5POST1\0",8);const uint32_t header[8]={1,H,uint32_t(cap),hash_n,pairs,uint32_t(N),0,0};append(header,sizeof(header));append(labels.data(),H*4);
    for(const auto& r:rows)out.push_back(uint8_t(r.size()));std::vector<int32_t> targets(H*cap,-1),keys(hash_n,-1),slots(hash_n,-1),sorted_labels=labels,sorted_slots(H);
    for(size_t row=0;row<H;++row){require(rows[row].size()<=size_t(cap),"export row bound");std::copy(rows[row].begin(),rows[row].end(),targets.begin()+row*cap);
        uint32_t pos=(uint32_t(labels[row])*2654435761u)&(hash_n-1);while(keys[pos]!=-1)pos=(pos+1)&(hash_n-1);keys[pos]=labels[row];slots[pos]=row;}
    std::sort(sorted_labels.begin(),sorted_labels.end());for(size_t i=0;i<H;++i)sorted_slots[i]=std::find(labels.begin(),labels.end(),sorted_labels[i])-labels.begin();
    for(const auto* a:{&targets,&keys,&slots,&sorted_labels,&sorted_slots})append(a->data(),a->size()*4);write_raw(path,out);
    Posting reload(path.string(),N);require(reload.labels==labels&&reload.pairs==pairs,"export runtime reload");
    for(size_t row=0;row<H;++row)require(reload.counts[row]==rows[row].size()&&std::equal(rows[row].begin(),rows[row].end(),reload.targets.begin()+row*cap),"export exact row roundtrip");
}
json compile_tables(const json& c){const auto started=Clock::now();const size_t N=c.at("base_n"),n=c.at("train_gt").at("n");require(N>0&&N<=INT32_MAX,"base ID domain");
    const fs::path root=c.at("output_dir");fresh_dir(root);const auto gt=read_gt(c.at("train_gt"),N);json all=json::array();std::set<std::string> names;
    for(const auto& tc:c.at("teachers")){const auto began=Clock::now();const std::string name=tc.at("name");require(names.insert(name).second,"unique compiler teacher name");
        const fs::path teacher_dir=tc.at("teacher_dir"),out=root/name;fresh_dir(out);const auto receipt=read_json(teacher_dir/"complete.json");
        require(receipt.at("status")=="PASS_TRAIN_TEACHER"&&receipt.at("name")==name&&receipt.at("n")==n&&receipt.at("K")==100&&receipt.at("L")==200,"bound TRAIN teacher scope");
        const auto labels=read_raw<int32_t>(tc.at("ids").get<std::string>()),responses=read_raw<int32_t>(teacher_dir/"raw/ids.i32"),routes=read_raw<int32_t>(teacher_dir/"raw/entry_ids.i32");
        require(labels.size()>=3&&responses.size()==n*100&&routes.size()==n*3,"TRAIN compiler shapes");std::map<int32_t,int32_t> slots;for(size_t i=0;i<labels.size();++i)require(labels[i]>=0&&size_t(labels[i])<N&&slots.emplace(labels[i],i).second,"compiler unique hub label");
        std::map<std::pair<int32_t,int32_t>,std::vector<uint32_t>> incidence;std::vector<int32_t> token_queries,token_targets;
        for(size_t i=0;i<n;++i){std::set<int32_t> returned;for(size_t j=0;j<100;++j){int32_t id=responses[i*100+j];require(id>=0&&size_t(id)<N&&returned.insert(id).second,"teacher unique returned domain");}
            std::set<int32_t> route_slots;for(int j=0;j<3;++j){auto it=slots.find(routes[3*i+j]);require(it!=slots.end()&&route_slots.insert(it->second).second,"teacher three distinct legal hub rows");}
            std::set<int32_t> missing;for(size_t j=0;j<100;++j)if(!returned.count(gt[i*100+j]))missing.insert(gt[i*100+j]);
            for(int32_t target:missing){require(token_queries.size()<UINT32_MAX,"token integer capacity");const uint32_t t=token_queries.size();token_queries.push_back(i);token_targets.push_back(target);
                for(int32_t row:route_slots)incidence[{row,target}].push_back(t);}}
        std::vector<Edge> edges;edges.reserve(incidence.size());for(auto& item:incidence)edges.push_back({item.first.first,item.first.second,std::move(item.second),false});incidence.clear();
        std::vector<uint64_t> offsets(labels.size()+1);std::vector<int32_t> hub_targets,global_ids=token_targets;size_t cursor=0;
        for(size_t row=0;row<labels.size();++row){offsets[row]=hub_targets.size();while(cursor<edges.size()&&edges[cursor].row==int32_t(row))hub_targets.push_back(edges[cursor++].target);}offsets.back()=hub_targets.size();
        std::sort(global_ids.begin(),global_ids.end());global_ids.erase(std::unique(global_ids.begin(),global_ids.end()),global_ids.end());
        write_raw(out/"source/token_queries.i32",token_queries);write_raw(out/"source/token_targets.i32",token_targets);write_raw(out/"source/hub_offsets.u64",offsets);
        write_raw(out/"source/hub_targets.i32",hub_targets);write_raw(out/"source/global_ids.i32",global_ids);
        Rows rows(labels.size()),previous;std::vector<uint8_t> covered(token_queries.size(),0);json models=json::object();
        for(int cap:{8,16,32}){const auto log=extend(edges,covered,rows,cap);const std::string model="JOINT"+std::to_string(cap);
            if(!previous.empty())for(size_t row=0;row<rows.size();++row)require(rows[row].size()>=previous[row].size()&&std::equal(previous[row].begin(),previous[row].end(),rows[row].begin()),"nested ordered row prefix");
            uint64_t independently_covered=0;for(size_t t=0;t<token_queries.size();++t){bool hit=false;const size_t qi=token_queries[t];for(int j=0;j<3;++j){const auto& row=rows[slots.at(routes[qi*3+j])];hit=hit||std::find(row.begin(),row.end(),token_targets[t])!=row.end();}independently_covered+=hit;require(hit==bool(covered[t]),"independent per-token coverage");}
            uint64_t pairs=0;for(const auto& row:rows)pairs+=row.size();const auto bin=out/"tables"/(model+".bin"),rowfile=out/"tables"/(model+".rows.json"),logfile=out/"tables"/(model+".selection_log.json");
            export_table(bin,labels,rows,N,cap);fresh_json(rowfile,rows);fresh_json(logfile,log);Posting post(bin.string(),N);
            models[model]={{"b",cap},{"pairs",pairs},{"training_integer_coverage",independently_covered},{"file_bytes",fs::file_size(bin)},{"runtime_plus_stack_bytes",post.resident_bytes()+Posting::AUXILIARY_STACK_RESERVE},
                           {"binary",bin.string()},{"rows_file",rowfile.string()},{"selection_log",logfile.string()}};previous=rows;}
        json meta={{"status","PASS_NEW_K100_NESTED_TABLES"},{"dataset",c.at("dataset")},{"name",name},{"H",labels.size()},{"base_n",N},{"residual_n",n},{"teacher_K",100},{"teacher_L",200},
                   {"tokens",token_queries.size()},{"candidate_key_target_edges",edges.size()},{"global_source_unique_targets",global_ids.size()},{"objective","K100 omissions, unit query-target tokens"},
                   {"models",models},{"source_dir",(out/"source").string()},{"teacher_dir",teacher_dir.string()},{"ids",tc.at("ids")},{"train_gt",c.at("train_gt")},{"all_test_or_eval_GT_access",false},
                   {"nested_order","global unit-token greedy8; preserve prefix and rebuild eligible heap at16 then32"},{"greedy_ties","lower row then lower target ID"},{"independent_token_coverage_passed",true},{"seconds",seconds(began)}};
        fresh_json(out/"compile_manifest.json",meta);all.push_back(meta);std::cout<<json{{"compiled",name},{"tokens",token_queries.size()},{"seconds",seconds(began)}}.dump()<<std::endl;}
    json result={{"status","PASS_E183_COMPILE"},{"config",c},{"models",all},{"outer_seconds",seconds(started)}};fresh_json(root/"complete.json",result);return result;
}

json selftest(){
    // An exhaustive eager-greedy control checks lazy priorities, row ties,
    // duplicate target coverage, and reopening full rows at larger capacity.
    std::vector<Edge> original;for(int row=0;row<4;++row)for(int target=0;target<45;++target)
        original.push_back({row,target,{uint32_t(row*45+target),uint32_t(180+target)},false});
    auto lazy=original,eager=original;std::vector<uint8_t> a(225),b(225);Rows x(4),y(4);size_t selections=0;
    for(int cap:{8,16,32}){auto log=extend(lazy,a,x,cap);json control=json::array();while(true){int best=-1;uint32_t bg=0;for(size_t i=0;i<eager.size();++i){auto& e=eager[i];if(e.selected||y[e.row].size()>=size_t(cap))continue;uint32_t g=gain(e,b);
            if(g>bg||(g&&g==bg&&best>=0&&std::pair<int,int>(e.row,e.target)<std::pair<int,int>(eager[best].row,eager[best].target))){best=i;bg=g;}}
            if(best<0||!bg)break;auto& e=eager[best];e.selected=true;y[e.row].push_back(e.target);for(auto t:e.tokens)b[t]=1;control.push_back({{"row",e.row},{"target",e.target},{"gain",bg}});}
        require(log==control&&x==y&&a==b,"synthetic lazy/eager full sequence equality");for(const auto& row:x)require(row.size()==size_t(cap),"synthetic exhausted rows reopen at new capacity");selections+=log.size();}
    Batch p(3,1),q(3,1);p.ids={1,2,3};p.distances={1.f,2.f,3.f};copy_packet(p,q);all_same(p,q);require(packet_sha(p)==packet_sha(q),"packet hash parity");q.ids[0]=4;require(packet_sha(p)!=packet_sha(q),"packet hash distinguishes ID");
    return {{"status","PASS_E183_SYNTHETIC"},{"greedy_selections_checked",selections},{"capacities",{8,16,32}},{"scientific_data_read",false},{"ANN_calls",0}};
}
} // namespace e183

#ifndef E183_EMBED_COMMON
int main(int argc,char** argv){try{using namespace e183;require(argc>=2,"residual_tools teacher|compile config.json or selftest");const std::string mode=argv[1];json result;
    if(mode=="selftest"){require(argc==2,"selftest takes no data");result=selftest();}
    else {require(argc==3,"mode and config required");const auto c=read_json(argv[2]);if(mode=="teacher")result=teacher(c);else if(mode=="compile")result=compile_tables(c);else throw std::runtime_error("unknown mode");}
    std::cout<<(mode=="selftest"?result:json{{"status",result.at("status")}}).dump()<<std::endl;return 0;
}catch(const std::exception& e){std::cerr<<"FATAL E183 "<<e.what()<<std::endl;return 2;}}
#endif

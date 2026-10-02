#include "native_reference.hpp"
using namespace cstage1;
struct TableDC:faiss::DistanceComputer {
    const std::vector<float>& a;uint64_t count=0;std::vector<int> order;bool recording;
    TableDC(const std::vector<float>& a_,bool recording_=true):a(a_),recording(recording_){}
    void set_query(const float*)override{}
    float operator()(faiss::idx_t i)override{require(i>=0 && i<int(a.size()),"table invalid ID");++count;if(recording)order.push_back(i);return a[i];}
    float symmetric_dis(faiss::idx_t i,faiss::idx_t j)override{return a[i]+a[j];}
};
struct NativeResult {std::vector<int> ids;std::vector<float> distances;std::vector<acsg::Neighbor> pool;Observer obs;uint64_t ndc=0,expansions=0;};
NativeResult native(acsg::ACSG& a,int L,int K,const std::vector<int>& entries,const std::vector<int>& previsited,
    faiss::DistanceComputer& dc,const float* q,bool reference,bool trace=true) {
    NativeResult r;faiss::VisitedTable vt(a.ntotal);for(int id:previsited)vt.set(id);
    std::vector<acsg::EnterPoint> ep;for(int id:entries)ep.emplace_back(id,1);dc.set_query(q);
    acsg::SearchTrace tr;std::vector<faiss::idx_t> ids(K);r.distances.resize(K);a.search_L=L;
    if(reference){native_reference::run(*a.final_graph,dc,vt,L,r.pool,ep,2,1,&tr,a.ntotal,&r.obs);
        for(int i=0;i<K;++i){ids[i]=r.pool[i].id;r.distances[i]=r.pool[i].distance;}}
    else if(trace)a.search_new_traced(dc,K,ids.data(),r.distances.data(),vt,2,ep,tr,nullptr,0,&r.pool);
    else a.search_new(dc,K,ids.data(),r.distances.data(),vt,2,ep,&r.pool);
    r.ids.assign(ids.begin(),ids.end());r.ndc=tr.distance_evaluations;r.expansions=tr.expanded_count;return r;
}
void equal_output(const State& s,const NativeResult& r,const Observer& o,const std::string& ctx) {
    require(s.top_ids()==r.ids,ctx+" top IDs");auto d=s.top_distances();
    require(d.size()==r.distances.size() && !memcmp(d.data(),r.distances.data(),d.size()*sizeof(float)),ctx+" float bits");
    require(s.ndc==r.ndc,ctx+" NDC");require(o.expanded_order==r.obs.expanded_order,ctx+" expansion order");
    require(o.distance_order==r.obs.distance_order,ctx+" evaluation order");
    require(s.natural_finished && !s.row_active,ctx+" termination");
    for(size_t i=0;i<r.pool.size();++i)require(s.retset[i].id==r.pool[i].id && s.retset[i].distance==r.pool[i].distance && s.retset[i].flag==r.pool[i].flag,ctx+" entire pool");
}
json synthetic() {
    uint64_t assertions=0,search_calls=0,partial_rows=0,rewinds=0,pool_rejections=0,ties=0,forced=0,natural_controls=0;
    json cases=json::array();
    for(int fixture=0;fixture<12;++fixture) {
        const int n=(fixture==0?12:192),degree=(fixture==1?0:12);acsg::ACSG a(degree);a.ntotal=n;a.is_built=true;
        a.final_graph=std::make_shared<acsg::Graph<int32_t>>(n,degree);
        for(int i=0;i<n;++i)for(int j=0;j<degree;++j){int id=(i+j*13+1)%n;
            if(fixture==2)id=(i+1)%n;if(fixture==3 && j>1)id=-1;
            if(fixture==4 && j==0)id=n+2;if(fixture==5 && j%2==0)id=i;
            a.final_graph->at(i,j)=id;}
        std::vector<float> distances(n);for(int i=0;i<n;++i){distances[i]=std::sin((i+1)*(fixture+1)*.371f);
            if(fixture==6 || fixture==7)distances[i]=float((i*7)%9);
            if(fixture==8)distances[i]=-float(i);if(fixture==9)distances[i]=float(i);}
        if(fixture==6 || fixture==7)++ties;
        float q=1;Engine e(*a.final_graph,n,1,{{"fixture",fixture},{"kernel","c_stage1_v1"}});
        for(int L:{10,64,128})for(int variant=0;variant<5;++variant){int K=10;
            std::vector<int> entries={0,1,2},pre;
            if(variant==1)entries={0,0,1,3};if(variant==2)entries={};
            if(variant==3){entries={0,1,2};pre={0,1,2};}if(variant==4){entries={1,2,3};pre={1};}
            TableDC d1(distances),d2(distances),dp(distances,false);
            auto r1=native(a,L,K,entries,pre,d1,&q,false),r=native(a,L,K,entries,pre,d2,&q,true);
            auto plain=native(a,L,K,entries,pre,dp,&q,false,false);search_calls+=3;
            require(r.ids==r1.ids && r.distances==r1.distances && r.ndc==r1.ndc && d1.count==r.ndc && d2.count==r.ndc && d1.order==r.obs.distance_order,"reference/native parity");
            require(plain.ids==r.ids && plain.distances==r.distances && dp.count==r.ndc,"native plain/count/trace");assertions+=2;
            std::set<uint64_t> checkpoints={0,1,2,3,r.expansions/2,r.expansions,r.expansions+1};
            for(auto cp:checkpoints){TableDC ds(distances);Observer obs;auto s=e.initialize(&q,L,K,entries,7,ds,&obs,pre);e.resume(s,ds,cp,&obs);
                auto frozen=s.to_json().dump();auto sc=s;auto ss=State::from_json(json::parse(frozen));
                Observer oc=obs,os=obs;TableDC dc(distances),dr(distances);
                e.resume(sc,dc,unlimited,&oc);e.resume(ss,dr,unlimited,&os);search_calls+=2;
                equal_output(sc,r,oc,"clone");equal_output(ss,r,os,"serialization");
                require(sc.to_json()==ss.to_json() && frozen==s.to_json().dump(),"repeat or branch pollution");assertions+=3;
                rewinds+=sc.rewinds;pool_rejections+=sc.rejected;
            }
            for(uint64_t cap:{uint64_t(0),uint64_t(1),uint64_t(2),uint64_t(7),uint64_t(64),r.ndc/2}){
                TableDC ds(distances);Observer obs;auto s=e.initialize(&q,L,K,entries,7,ds,&obs,pre);s.set_additional_cap(cap);e.resume(s,ds,unlimited,&obs);
                require(s.ndc<=s.limit,"cap envelope");if(s.row_active){++partial_rows;int id=a.final_graph->at(s.current_node,s.neighbor_offset);require(!s.visited.count(id),"unevaluated cap ID marked visited");}
                auto resumed=State::from_json(json::parse(s.to_json().dump()));resumed.remove_cap();e.resume(resumed,ds,unlimited,&obs);++search_calls;
                equal_output(resumed,r,obs,"partial-row resume");++assertions;
            }
            TableDC dbase(distances);Observer obs;auto prefix=e.initialize(&q,L,K,entries,7,dbase,&obs,pre);e.resume(prefix,dbase,1,&obs);
            auto frozen=prefix.to_json();int candidate=-1;for(int id=n-1;id>=0;--id)if(!prefix.visited.count(id)){candidate=id;break;}
            if(candidate>=0 && !prefix.natural_finished){auto f=prefix,ni=prefix;f.set_additional_cap(128);ni.set_additional_cap(128);
                TableDC df(distances),dn(distances);Observer of,on;auto af=e.inject(f,candidate,true,df,&of);auto an=e.inject(ni,candidate,false,dn,&on);
                e.resume(f,df,unlimited,&of);e.resume(ni,dn,unlimited,&on);search_calls+=2;++forced;++natural_controls;
                require(f.expanded.count(candidate)==1 && std::count(of.expanded_order.begin(),of.expanded_order.end(),candidate)==1,"forced exactly once");
                require(df.count==f.ndc-prefix.ndc && dn.count==ni.ndc-prefix.ndc,"paid action distances");
                require(f.ndc<=f.limit && ni.ndc<=ni.limit && prefix.to_json()==frozen,"action cap/isolation");
                auto repeat=prefix;repeat.set_additional_cap(128);TableDC dd(distances);e.inject(repeat,candidate,true,dd);e.resume(repeat,dd);++search_calls;
                require(repeat.to_json()==f.to_json(),"repeated force deterministic");assertions+=4;
                // A visited or illegal intervention is a no-op, never a repeated forced expansion.
                auto no=prefix;TableDC no_dc(distances);auto status=e.inject(no,entries.empty()?*prefix.visited.begin():entries[0],false,no_dc);
                require(status!="eligible" && no_dc.count==0 && no.to_json()==frozen,"visited no-op");++assertions;
            }
            cases.push_back({{"fixture",fixture},{"L",L},{"variant",variant},{"native_ndc",r.ndc},{"native_expansions",r.expansions}});
        }
        TableDC dc(distances);for(int bad:{-1,n}){bool caught=false;try{e.initialize(&q,64,10,{bad},0,dc);}catch(const std::exception&){caught=true;}require(caught && dc.count==0,"illegal init safely rejected");++assertions;}
        TableDC di(distances);auto s=e.initialize(&q,64,10,{0},0,di);auto wrong=s;wrong.identity["fixture"]=-1;bool caught=false;try{e.resume(wrong,di);}catch(const std::exception&){caught=true;}require(caught,"wrong identity accepted");++assertions;
    }
    require(partial_rows>0 && rewinds>0 && pool_rejections>0 && ties>0 && forced>0,"missing mandatory edge coverage");
    return {{"status","PASS"},{"assertions",assertions},{"native_or_branch_calls",search_calls},{"partial_row_cases",partial_rows},{"rewind_events",rewinds},{"pool_rejections",pool_rejections},{"tie_fixtures",ties},{"force_cases",forced},{"natural_cases",natural_controls},{"cases",cases}};
}

json real_parity(const fs::path& config,const fs::path& lock) {
    Dataset d(config);json locked=read_json(lock);json ident=read_json(d.c.at("identity_file").get<std::string>());
    ident["state_kernel"]="cstage1_v1";Engine e(*d.index.acsg.final_graph,d.index.ntotal,d.index.d,ident);
    json checks=json::array();uint64_t calls=0;
    for(int L:{64,128})for(int i=0;i<16;++i){auto q=d.query(i);auto r3=d.router->run(q,3),r7=d.router->run(q,7);
        CountDC da(acsg::storage_distance_computer(d.index.storage),true),db(acsg::storage_distance_computer(d.index.storage),true);
        auto r1=native(d.index.acsg,L,10,r3.ids,{},da,q,false),r=native(d.index.acsg,L,10,r3.ids,{},db,q,true);calls+=2;
        require(r.ids==r1.ids && r.distances==r1.distances && r.ndc==r1.ndc && da.count==r.ndc && db.count==r.ndc && da.order==r.obs.distance_order,"real reference parity");
        std::unique_ptr<faiss::DistanceComputer> dp(acsg::storage_distance_computer(d.index.storage));auto plain=native(d.index.acsg,L,10,r3.ids,{},*dp,q,false,false);++calls;
        require(plain.ids==r.ids && plain.distances==r.distances,"real original plain");
        CountDC ds(acsg::storage_distance_computer(d.index.storage),true);Observer obs;
        auto s=e.initialize(q,L,10,r3.ids,d.row_ids[i],ds,&obs);auto cp=locked["checkpoint_completed_expansions"][std::to_string(L)].get<uint64_t>();e.resume(s,ds,cp,&obs);
        auto prefix=s.to_json();auto restored=State::from_json(json::parse(prefix.dump()));auto copy=s;
        Observer oc=obs,os=obs;CountDC dc(acsg::storage_distance_computer(d.index.storage)),dr(acsg::storage_distance_computer(d.index.storage));
        e.resume(copy,dc,unlimited,&oc);e.resume(restored,dr,unlimited,&os);calls+=2;
        equal_output(copy,r,oc,"real clone");equal_output(restored,r,os,"real restore");
        // Mutating shared legacy search_L must not change the frozen branch L.
        d.index.acsg.search_L=257;auto pl=s;std::unique_ptr<faiss::DistanceComputer> pd(acsg::storage_distance_computer(d.index.storage));e.resume(pl,*pd);++calls;
        require(pl.to_json()==copy.to_json(),"state/plain or shared L leakage");
        for(int rank=3;rank<7;++rank)if(e.eligibility(s,r7.ids[rank])=="eligible"){
            auto f=s,ni=s;f.set_additional_cap(locked["B"]);ni.set_additional_cap(locked["B"]);
            CountDC df(acsg::storage_distance_computer(d.index.storage)),dn(acsg::storage_distance_computer(d.index.storage));
            e.inject(f,r7.ids[rank],true,df);e.resume(f,df);e.inject(ni,r7.ids[rank],false,dn);e.resume(ni,dn);calls+=2;
            require(s.to_json()==prefix,"real branch pollution");require(f.ndc<=f.limit && ni.ndc<=ni.limit,"real cap");
        }
        checks.push_back({{"L",L},{"sample_index",i},{"row_id",d.row_ids[i]},{"ndc",r.ndc},{"expanded_order",r.obs.expanded_order},
            {"prefix_ndc",s.ndc},{"prefix_expansions",s.completed_expansions},{"ids",r.ids},{"distances",r.distances},
            {"direct_top3_equals_top7_prefix",std::equal(r3.ids.begin(),r3.ids.end(),r7.ids.begin())}});
    }
    return {{"status","PASS"},{"dataset",d.c["dataset"]},{"GT_accessed",false},{"native_or_branch_calls",calls},{"checks",checks}};
}
int main(int argc,char** argv){try{
    if(argc<3){std::cout<<"parity synthetic NEW_JSON | parity real CONFIG LOCK NEW_JSON\n";return 0;}
    omp_set_num_threads(1);fs::path out=argv[argc-1];require(!fs::exists(out),"output exists");auto begin=Clock::now();
    json result;if(std::string(argv[1])=="synthetic" && argc==3)result=synthetic();
    else{require(argc==5 && std::string(argv[1])=="real","bad args");result=real_parity(argv[2],argv[3]);}
    result["wall_seconds"]=seconds(begin);write_json(out,result);std::cout<<"PASS wall="<<seconds(begin)<<std::endl;return 0;
}catch(const std::exception& e){std::cerr<<"C1_FAIL "<<e.what()<<std::endl;return 1;}}

#pragma once
#include "common.hpp"
#include <deque>

// C stage1 v1: independent mode-2 state machine. The legacy ACSG kernel is never edited.
namespace cstage1 {
constexpr uint64_t unlimited=std::numeric_limits<uint64_t>::max();
struct Observer {std::vector<int> expanded_order;std::vector<int> distance_order;};
struct State {
    int schema=1,L=0,K=0,dim=0,ntotal=0,num_ids=0,cursor=0,updated_pos=0;
    int current_node=-1,neighbor_offset=0;
    bool row_active=false,row_forced=false,natural_finished=false,cap_exhausted=false;
    float best_before_row=std::numeric_limits<float>::max();
    uint64_t ndc=0,limit=unlimited,prefix_ndc=0,completed_expansions=0,started_expansions=0;
    uint64_t accepted=0,rejected=0,rewinds=0,stagnation=0;
    std::vector<acsg::Neighbor> retset;
    std::unordered_set<int> visited,expanded;
    std::vector<int> initial_entries,last_expanded;
    std::vector<float> query;
    json identity;
    int64_t query_id=-1;
    uint64_t remaining()const{return limit==unlimited?unlimited:limit-ndc;}
    void set_additional_cap(uint64_t B){require(B<=unlimited-ndc,"cap overflow");prefix_ndc=ndc;limit=ndc+B;cap_exhausted=false;}
    void remove_cap(){limit=unlimited;cap_exhausted=false;}
    std::vector<int> top_ids()const {std::vector<int> a;for(int i=0;i<K;++i)a.push_back(retset[i].id);return a;}
    std::vector<float> top_distances()const {std::vector<float>a;for(int i=0;i<K;++i)a.push_back(retset[i].distance);return a;}
    json to_json()const {
        std::vector<int> v(visited.begin(),visited.end()),e(expanded.begin(),expanded.end());
        std::sort(v.begin(),v.end());std::sort(e.begin(),e.end());json pool=json::array();
        for(const auto& n:retset)pool.push_back({n.id,n.distance,n.flag});
        return {{"schema",schema},{"L",L},{"K",K},{"dim",dim},{"ntotal",ntotal},{"num_ids",num_ids},
            {"cursor",cursor},{"updated_pos",updated_pos},{"current_node",current_node},{"neighbor_offset",neighbor_offset},
            {"row_active",row_active},{"row_forced",row_forced},{"natural_finished",natural_finished},{"cap_exhausted",cap_exhausted},
            {"best_before_row",best_before_row},{"ndc",ndc},{"limit",limit},{"prefix_ndc",prefix_ndc},{"remaining",remaining()},
            {"completed_expansions",completed_expansions},{"started_expansions",started_expansions},{"accepted",accepted},
            {"rejected",rejected},{"rewinds",rewinds},{"stagnation",stagnation},{"retset",pool},{"visited",v},{"expanded",e},
            {"initial_entries",initial_entries},{"last_expanded",last_expanded},{"query",query},{"identity",identity},{"query_id",query_id}};
    }
    static State from_json(const json& j) {
        State s;
#define C_READ(x) s.x=j.at(#x).get<decltype(s.x)>()
        C_READ(schema);C_READ(L);C_READ(K);C_READ(dim);C_READ(ntotal);C_READ(num_ids);C_READ(cursor);C_READ(updated_pos);
        C_READ(current_node);C_READ(neighbor_offset);C_READ(row_active);C_READ(row_forced);C_READ(natural_finished);C_READ(cap_exhausted);
        C_READ(best_before_row);C_READ(ndc);C_READ(limit);C_READ(prefix_ndc);C_READ(completed_expansions);C_READ(started_expansions);
        C_READ(accepted);C_READ(rejected);C_READ(rewinds);C_READ(stagnation);C_READ(initial_entries);C_READ(last_expanded);
        C_READ(query);C_READ(identity);C_READ(query_id);
#undef C_READ
        for(auto& x:j.at("retset"))s.retset.emplace_back(x.at(0).get<int>(),x.at(1).get<float>(),x.at(2).get<bool>());
        for(auto& x:j.at("visited"))require(s.visited.insert(x.get<int>()).second,"serialized duplicate visited");
        for(auto& x:j.at("expanded"))require(s.expanded.insert(x.get<int>()).second,"serialized duplicate expanded");
        require(s.schema==1 && s.L>=s.K && s.K>0 && s.L>=3 && s.retset.size()==size_t(s.L+1),"state shape");
        require(s.num_ids>=1 && s.num_ids<=s.L && s.cursor>=0 && s.cursor<=s.L && s.updated_pos>=0 && s.updated_pos<=s.L+1,"state scheduler");
        require(s.query.size()==size_t(s.dim) && s.last_expanded.size()<=16 && s.ndc<=s.limit && s.prefix_ndc<=s.ndc,"state counters");
        for(int id:s.visited)require(id>=0 && id<s.ntotal,"state visited range");
        for(int id:s.expanded)require(s.visited.count(id),"expanded not visited");
        for(int i=0;i<s.num_ids;++i){require(s.visited.count(s.retset[i].id),"pool not visited");require(std::isfinite(s.retset[i].distance),"pool nonfinite");
            if(i)require(s.retset[i-1].distance<=s.retset[i].distance,"unsorted pool");}
        require(s.remaining()==j.at("remaining").get<uint64_t>(),"remaining mismatch");return s;
    }
};

// Literal insertion algorithm from the frozen ACSG.cpp; L+1 scratch slot is retained.
inline int insert_into_pool(acsg::Neighbor* addr,int K,acsg::Neighbor nn) {
    int left=0,right=K-1;
    if(addr[left].distance>nn.distance){memmove(&addr[left+1],&addr[left],K*sizeof(acsg::Neighbor));addr[left]=nn;return left;}
    if(addr[right].distance<nn.distance){addr[K]=nn;return K;}
    while(left<right-1){int mid=(left+right)/2;if(addr[mid].distance>nn.distance)right=mid;else left=mid;}
    while(left>0){if(addr[left].distance<nn.distance)break;if(addr[left].id==nn.id)return K+1;left--;}
    if(addr[left].id==nn.id || addr[right].id==nn.id)return K+1;
    memmove(&addr[right+1],&addr[right],(K-right)*sizeof(acsg::Neighbor));addr[right]=nn;return right;
}

struct Engine {
    const acsg::Graph<int32_t>& graph; const int ntotal,dim; const json identity;
    Engine(const acsg::Graph<int32_t>& g,int n,int d,json ident):graph(g),ntotal(n),dim(d),identity(std::move(ident)){}
    void validate(const State& s)const {
        require(s.identity==identity && s.ntotal==ntotal && s.dim==dim,"state engine identity mismatch");
        require(s.schema==1 && s.L>=s.K && s.K>0 && s.L>=3 && s.query.size()==size_t(dim),"state L/K/query");
        require(s.retset.size()==size_t(s.L+1) && s.num_ids>=1 && s.num_ids<=s.L && s.cursor>=0 && s.cursor<=s.L,
                "state pool/cursor shape mismatch");
        require(s.updated_pos>=0 && s.updated_pos<=s.L+1 && s.ndc<=s.limit && s.prefix_ndc<=s.ndc && s.last_expanded.size()<=16,
                "state scheduler/counters mismatch");
        require(!s.row_active || (s.current_node>=0 && s.current_node<ntotal && s.neighbor_offset>=0 && s.neighbor_offset<=graph.K),"partial row invalid");
    }
    float evaluate(State& s,faiss::DistanceComputer& dc,int id,Observer* obs)const {
        require(s.ndc<s.limit,"distance past cap");require(id>=0 && id<ntotal && !s.visited.count(id),"duplicate or invalid distance");
        s.visited.insert(id);++s.ndc;if(obs)obs->distance_order.push_back(id);float d=dc(id);require(std::isfinite(d),"nonfinite distance");return d;
    }
    State initialize(const float* q,int L,int K,const std::vector<int>& entries,int64_t query_id,
                     faiss::DistanceComputer& dc,Observer* obs=nullptr,const std::vector<int>& previsited={})const {
        require(K>0 && L>=K && L>=3,"invalid pool size");
        for(int id:entries)require(id>=0 && id<ntotal,"invalid initial entry (legacy undefined input rejected)");
        require(previsited.size()<size_t(ntotal),"all visited cannot fallback");
        State s;s.L=L;s.K=K;s.ntotal=ntotal;s.dim=dim;s.query.assign(q,q+dim);s.query_id=query_id;s.identity=identity;
        for(float x:s.query)require(std::isfinite(x),"nonfinite query");
        s.initial_entries=entries;s.updated_pos=L;s.retset.assign(L+1,acsg::Neighbor(-1,std::numeric_limits<float>::max(),false));
        for(int id:previsited){require(id>=0 && id<ntotal,"invalid previsited");s.visited.insert(id);}
        dc.set_query(s.query.data());
        for(size_t i=0;i<std::min<size_t>(3,entries.size()) && s.num_ids<L;++i){int id=entries[i];if(s.visited.count(id))continue;
            float dist=evaluate(s,dc,id,obs);s.retset[s.num_ids++]=acsg::Neighbor(id,dist,true);}
        if(!s.num_ids){faiss::RandomGenerator gen(0x1234);while(!s.num_ids){int id=gen.rand_int(ntotal);if(s.visited.count(id))continue;
            s.retset[s.num_ids++]=acsg::Neighbor(id,evaluate(s,dc,id,obs),true);}}
        std::sort(s.retset.begin(),s.retset.begin()+s.num_ids);return s;
    }
    int insert(State& s,int id,float dist,bool pending)const {
        if(s.num_ids>=s.L && dist>=s.retset[s.L-1].distance){++s.rejected;return s.L+1;}
        int r=insert_into_pool(s.retset.data(),s.L,acsg::Neighbor(id,dist,pending));
        if(r<s.L){++s.accepted;s.updated_pos=std::min(s.updated_pos,r);if(s.num_ids<s.L)++s.num_ids;}return r;
    }
    void start_row(State& s,int id,bool forced,Observer* obs)const {
        require(!s.row_active && !s.expanded.count(id),"duplicate expansion");
        s.row_active=true;s.row_forced=forced;s.current_node=id;s.neighbor_offset=0;s.best_before_row=s.retset[0].distance;
        s.expanded.insert(id);++s.started_expansions;s.last_expanded.push_back(id);
        if(s.last_expanded.size()>16)s.last_expanded.erase(s.last_expanded.begin());
        if(obs)obs->expanded_order.push_back(id);
    }
    void settle_cursor(State& s)const {
        while(s.cursor<s.L && s.cursor<s.num_ids && !s.retset[s.cursor].flag)++s.cursor;
        if(s.cursor>=s.L || s.cursor>=s.num_ids)s.natural_finished=true;
    }
    // completed_limit is an absolute complete-row checkpoint; infinity means finish/cap.
    void resume(State& s,faiss::DistanceComputer& dc,uint64_t completed_limit=unlimited,Observer* obs=nullptr)const {
        validate(s);dc.set_query(s.query.data());s.cap_exhausted=false;
        while(!s.natural_finished) {
            if(!s.row_active){settle_cursor(s);if(s.natural_finished || s.completed_expansions>=completed_limit)return;
                s.updated_pos=s.L;int n=s.retset[s.cursor].id;s.retset[s.cursor].flag=false;start_row(s,n,false,obs);}
            while(s.neighbor_offset<graph.K){int id=graph.at(s.current_node,s.neighbor_offset);
                if(id<0 || id>=ntotal || s.visited.count(id)){++s.neighbor_offset;continue;}
                if(s.ndc>=s.limit){s.cap_exhausted=true;return;}
                float dist=evaluate(s,dc,id,obs);++s.neighbor_offset;insert(s,id,dist,true);
            }
            ++s.completed_expansions;
            if(s.retset[0].distance<s.best_before_row)s.stagnation=0;else ++s.stagnation;
            if(s.updated_pos<=s.cursor)++s.rewinds;
            if(s.row_forced)s.cursor=std::min(s.cursor,s.updated_pos);
            else s.cursor=(s.updated_pos<=s.cursor)?s.updated_pos:s.cursor+1;
            s.row_active=false;s.row_forced=false;s.current_node=-1;s.neighbor_offset=0;s.updated_pos=s.L;
            settle_cursor(s);
            if(s.completed_expansions>=completed_limit)return;
        }
    }
    std::string eligibility(const State& s,int e)const {
        if(s.natural_finished)return "early_finished";
        if(e<0 || e>=ntotal)return "invalid_or_empty";
        if(s.visited.count(e))return "visited";
        if(s.expanded.count(e))return "expanded";
        return "eligible";
    }
    // Returns action status; no GT is accepted by any online API.
    std::string inject(State& s,int e,bool force,faiss::DistanceComputer& dc,Observer* obs=nullptr)const {
        validate(s);require(!s.row_active,"injection requires complete-row checkpoint");
        auto why=eligibility(s,e);if(why!="eligible")return why;
        require(s.remaining()>=65,"action cap must allow complete worst-case force row");
        dc.set_query(s.query.data());s.updated_pos=s.L;
        float dist=evaluate(s,dc,e,obs);int r=insert(s,e,dist,!force);
        if(r<s.L)s.cursor=std::min(s.cursor,r);
        if(force){start_row(s,e,true,obs);}
        else{s.updated_pos=s.L;settle_cursor(s);}
        return r<s.L?"inserted":"pool_rejected";
    }
};
} // namespace cstage1

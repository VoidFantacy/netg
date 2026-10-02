#include "kernels.hpp"
#include <faiss/IndexFlat.h>
#include <random>
struct Recording:faiss::FlatCodesDistanceComputer{
    std::unique_ptr<faiss::DistanceComputer> inner;
    std::vector<int> calls;
    explicit Recording(faiss::DistanceComputer* p):inner(p){auto* base=p;while(auto* neg=dynamic_cast<faiss::NegativeDistanceComputer*>(base))base=neg->basedis;if(auto* f=dynamic_cast<faiss::FlatCodesDistanceComputer*>(base)){codes=f->codes;code_size=f->code_size;}}
    void set_query(const float* q)override{calls.clear();inner->set_query(q);}
    float operator()(faiss::idx_t id)override{calls.push_back(id);return (*inner)(id);}
    float distance_to_code(const uint8_t* c)override{return (*this)((c-codes)/code_size);}
    float symmetric_dis(faiss::idx_t a,faiss::idx_t b)override{return inner->symmetric_dis(a,b);}
    void distances_batch_4(faiss::idx_t a,faiss::idx_t b,faiss::idx_t c,faiss::idx_t d,float& x,float& y,float& z,float& w)override{
        calls.insert(calls.end(),{int(a),int(b),int(c),int(d)});inner->distances_batch_4(a,b,c,d,x,y,z,w);
    }
};
int main(int argc,char**argv){try{
    require(argc==2,"regression output");std::mt19937 rng(1012026);uint64_t cases=0,calls=0;
    std::vector<std::string> names={"GT10-minimal","GT10-core","GT10-span","GT10-prefetch-filter","GT10-batch4","GT10-span-batch4"};
    for(int metric:{0,1})for(int n:{1,17,65})for(int dim:{4,32,512}){
        std::vector<float> x(n*dim),q(dim);for(auto& v:x)v=int(rng()%5)-2;
        for(int i=1;i<n;i+=3)std::copy(x.begin(),x.begin()+dim,x.begin()+i*dim);
        faiss::IndexFlat storage(dim,faiss::MetricType(metric));storage.add(n,x.data());
        acsg::ACSG original(8);original.ntotal=n;original.is_built=true;original.enterpoint=0;original.final_graph=std::make_shared<acsg::Graph<int32_t>>(n,8);
        for(int i=0;i<n;++i)for(int j=0;j<8;++j)original.final_graph->at(i,j)=j==0?i:j==1?-1:j==2?n+2:j==7?-1:int(rng()%n);
        auto spans=make_spans(*original.final_graph,n);ResearchKernel candidate(*original.final_graph,spans,n);
        Recording a(acsg::storage_distance_computer(&storage)),b(acsg::storage_distance_computer(&storage));faiss::VisitedTable va(n),vb(n);
        std::vector<acsg::Neighbor> scratch;std::array<faiss::idx_t,100> ia,ib;std::array<float,100> da,db;
        for(int rep=0;rep<12;++rep)for(int L:{1,3,16,100})for(int K:{1,100}){
            if(K>L)continue;for(auto& v:q)v=int(rng()%3)-1;original.search_L=L;
            std::vector<acsg::EnterPoint> ep;if(rep%3)for(int id:{0,n-1,0})ep.emplace_back(id,1);
            // Also exercises visited generation wraparound via all repeated variants.
            for(const auto& name:names){va.advance();vb.advance();a.set_query(q.data());b.set_query(q.data());original.search_new(a,K,ia.data(),da.data(),va,2,ep,&scratch);auto fn=kernel_call(name);(candidate.*fn)(b,vb,ep,L,K,ib.data(),db.data());
                require(std::equal(ia.begin(),ia.begin()+K,ib.begin()),name+" synthetic IDs");require(!memcmp(da.data(),db.data(),K*sizeof(float)),name+" synthetic distance bits");require(a.calls==b.calls,name+" synthetic distance order");++cases;calls+=2;}
        }
    }
    write_json(argv[1],{{"status","PASS"},{"paired_cases",cases},{"synthetic_search_calls",calls},{"metrics",{"IP","L2"}},{"dimensions",{4,32,512}},{"covers","ties, duplicate entries, empty-entry fallback, holes, invalid neighbors, trailing padding, short result sets, K1/K100, visited wraparound, distance call order, actual Faiss scalar/batch4 bits"}});
    std::cout<<"PASS cases="<<cases<<" searches="<<calls<<std::endl;return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}

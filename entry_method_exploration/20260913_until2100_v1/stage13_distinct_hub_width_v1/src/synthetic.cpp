#include "hnswlib/hnswlib.h"
#include "distinct_stop.hpp"
#include <iostream>
#include <set>
#include <cstring>
#include <cmath>
static size_t calls=0;
static float counted_ip(const void* a,const void* b,const void* p) {
    ++calls;return hnswlib::InnerProductDistance(a,b,p);
}
struct Space:hnswlib::SpaceInterface<float> {
    size_t d=4;
    size_t get_data_size() override {return d*sizeof(float);}
    hnswlib::DISTFUNC<float> get_dist_func()override{return counted_ip;}
    void* get_dist_func_param()override{return &d;}
};
void ensure(bool ok){if(!ok)throw std::runtime_error("synthetic invariant failed");}
int main() {
    size_t routes=0;
    for(int multi=0;multi<2;++multi)for(int ties=0;ties<2;++ties) {
        size_t n=multi?60:20;std::vector<int32_t> mapping(n);
        for(size_t j=0;j<n;++j)mapping[j]=1009+int(j/(multi?3:1))*37;
        Space space;hnswlib::HierarchicalNSW<float> graph(&space,n,8,40,77);graph.setEf(10);
        for(size_t i=0;i<n;++i) {
            size_t slot=(i*7)%n; // Nonidentity internal/external labels, coprime with 20/60.
            float p[4];for(size_t k=0;k<4;++k)p[k]=ties?float((slot/(multi?3:1))%3==k):std::sin(float((slot/(multi?3:1)+1)*(k+2)));
            graph.addPoint(p,multi?slot:size_t(mapping[slot]));
        }
        DistinctHubStop stop(mapping,multi);
        for(size_t qi=0;qi<64;++qi) {
            float q[4];for(size_t k=0;k<4;++k)q[k]=ties?(qi%2?0.f:1.f):std::cos(float(qi*(k+3)));
            stop.reset();calls=0;auto a=graph.searchStopConditionClosest(q,stop);++routes;auto ndc=calls;
            ensure(stop.distinct()==10 && a.size()>=10 && a.size()<=size_t(multi?30:10));
            std::set<size_t> internal,real;for(auto x:a) {
                ensure(internal.insert(x.second).second);auto lab=graph.getExternalLabel(x.second);real.insert(multi?mapping.at(lab):lab);
            }
            ensure(real.size()==10);
            if(!multi) {
                calls=0;auto b=graph.searchKnn(q,3);++routes;ensure(calls==ndc);
                std::priority_queue<std::pair<float,size_t>> first;
                for(size_t j=0;j<3;++j)first.emplace(a[j].first,graph.getExternalLabel(a[j].second));
                while(!b.empty()){ensure(b.top()==first.top());b.pop();first.pop();}
            } else {
                stop.reset();calls=0;auto b=graph.searchStopConditionClosest(q,stop);++routes;
                ensure(a==b && calls==ndc);
            }
        }
    }
    DistinctHubStop refs({71,71,83},true,2);
    refs.add_point_to_result(0,nullptr,1);refs.add_point_to_result(1,nullptr,1);refs.add_point_to_result(2,nullptr,2);
    ensure(refs.distinct()==2 && refs.points()==3);
    refs.remove_point_from_result(0,nullptr,999);ensure(refs.distinct()==2);
    refs.remove_point_from_result(1,nullptr,-999);ensure(refs.distinct()==1);
    bool rejected=false;try{refs.remove_point_from_result(0,nullptr,0);}catch(...){rejected=true;}ensure(rejected);
    refs.reset();ensure(refs.points()==0 && refs.distinct()==0);
    std::cout<<"{\"status\":\"PASS\",\"synthetic_builds\":4,\"synthetic_HNSW\":"<<routes<<",\"NSG\":0,\"singleton_tie_distance_count_parity\":true,\"nonidentity_labels\":true,\"reset_and_remove_dist_ignored\":true}"<<std::endl;
}

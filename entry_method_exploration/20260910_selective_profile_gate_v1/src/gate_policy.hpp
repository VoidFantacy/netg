#pragma once
#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"

constexpr size_t FEATURE_COUNT=13;
using FeatureVector=std::array<double,FEATURE_COUNT>;
struct FeaturePair { FeatureVector x{}; Decision base,newer; };
struct Choice {
    Decision route;
    uint8_t use_new=0;
    double logit=0;
    uint32_t feature_dots=0,base_calls=0,new_calls=0;
};

class SelectivePolicy {
    size_t d_,h_,k_=3;
    bool counted_;
    std::string kind_;
    int force_=-1;
    std::unique_ptr<Policy> base_,newer_,direct_;
    std::vector<float> w0_,w1_;
    std::vector<double> hub_;
    std::unordered_map<int32_t,size_t> local_;
    std::vector<double> mean_,scale_,beta_;
    double bias_=0,threshold_=0;
    mutable hnswlib::InnerProductSpace score_space_;

    double norm(const float* q)const {
        double sum=0;for(size_t j=0;j<d_;++j)sum+=double(q[j])*q[j];
        return std::sqrt(sum);
    }
    std::array<double,3> scores(const float* q,const Decision& a,const std::vector<float>& w,double qnorm)const {
        std::array<double,3> s;
        auto fn=score_space_.get_dist_func();auto param=score_space_.get_dist_func_param();
        for(size_t j=0;j<3;++j)s[j]=(1.0-double(fn(q,w.data()+local_.at(a.ids[j])*d_,param)))/std::max(qnorm,1e-12);
        std::sort(s.begin(),s.end(),std::greater<double>());return s;
    }
    void first_features(const float* q,const Decision& a,FeatureVector& x)const {
        const double qnorm=norm(q);auto s=scores(q,a,w0_,qnorm);
        x[0]=std::log1p(qnorm);x[1]=s[0];x[2]=s[0]-s[1];x[3]=s[0]-s[2];
        x[4]=0;x[5]=std::numeric_limits<double>::infinity();x[6]=0;
        for(auto id:a.ids) {size_t j=local_.at(id);x[4]+=hub_[j*3];x[5]=std::min(x[5],hub_[j*3]);x[6]+=hub_[j*3+2];}
        x[4]/=3;x[6]/=3;
    }
    void extra_features(const float* q,const Decision& a,const Decision& b,FeatureVector& x)const {
        auto s=scores(q,b,w1_,norm(q));x[7]=s[0]-x[1];x[8]=s[0]-s[1];x[9]=s[0]-s[2];
        x[10]=0;x[11]=std::numeric_limits<double>::infinity();size_t overlap=0;
        for(auto id:b.ids) {
            size_t j=local_.at(id);x[10]+=hub_[j*3+1];x[11]=std::min(x[11],hub_[j*3+1]);
            overlap+=std::find(a.ids.begin(),a.ids.end(),id)!=a.ids.end();
        }
        x[10]/=3;x[12]=double(overlap)/3;
    }
    double predict(const FeatureVector& x)const {
        double z=bias_;
        for(size_t j=0;j<beta_.size();++j) {
            const double normalized=std::max(-6.0,std::min(6.0,(x[j]-mean_[j])/scale_[j]));
            volatile double term=beta_[j]*normalized; // Match explicit offline summation; no fused threshold surprises.
            z+=term;
        }
        return z;
    }
public:
    SelectivePolicy(const json& shared,const json& method,const fs::path& prefix,bool counted,bool load):
        d_(shared.at("A0").at("dim")),h_(shared.at("A0").at("hub_count")),counted_(counted),
        kind_(method.at("kind")),force_(method.value("force",-1)),score_space_(d_) {
        require(std::set<std::string>{"fast20k","e24","base_gate","dual_gate","features","nsg","fast30k"}.count(kind_),"unknown policy kind");
        require(force_>=-1 && force_<=1,"invalid force switch");
        if(kind_=="nsg" || kind_=="fast30k") {
            auto direct=method.at("direct");direct["dim"]=d_;
            direct_=std::make_unique<Policy>(direct,fs::path(prefix.string()+".direct.hnsw"),counted,load);
            k_=direct_->entry_count();return;
        }
        if(kind_!="e24")base_=std::make_unique<Policy>(shared.at("A0"),fs::path(prefix.string()+".base.hnsw"),counted,load);
        if(kind_!="fast20k")newer_=std::make_unique<Policy>(shared.at("A1"),fs::path(prefix.string()+".new.hnsw"),counted,load);
        if(kind_=="fast20k" || kind_=="e24")return;
        w0_=read_raw<float>(shared.at("A0").at("W"));w1_=read_raw<float>(shared.at("A1").at("W"));
        auto ids=read_raw<int32_t>(shared.at("A0").at("mapping"));auto ids1=read_raw<int32_t>(shared.at("A1").at("mapping"));
        hub_=read_raw<double>(shared.at("hub_features"));
        require(ids==ids1 && ids.size()==h_ && hub_.size()==3*h_ && w0_.size()==h_*d_ && w1_.size()==h_*d_,"feature metadata shape/mapping mismatch");
        for(size_t j=0;j<h_;++j)require(local_.emplace(ids[j],j).second,"duplicate feature hub ID");
        for(double v:hub_)require(std::isfinite(v),"nonfinite hub metadata");
        if(kind_=="features" || force_>=0)return;
        std::ifstream f(method.at("model_path").get<std::string>());require(bool(f),"missing frozen gate");json m;f>>m;
        require(m.at("feature_set")==kind_,"gate feature-set mismatch");
        mean_=m.at("mean").get<std::vector<double>>();scale_=m.at("scale").get<std::vector<double>>();beta_=m.at("beta").get<std::vector<double>>();
        bias_=m.at("bias");threshold_=m.at("threshold");
        const size_t p=kind_=="base_gate"?7:13;
        require(mean_.size()==p && scale_.size()==p && beta_.size()==p,"wrong gate dimension");
        for(size_t j=0;j<p;++j)require(std::isfinite(mean_[j]) && std::isfinite(scale_[j]) && std::isfinite(beta_[j]) && scale_[j]>=1e-6,"invalid gate parameters");
        require(std::isfinite(bias_) && std::isfinite(threshold_),"invalid gate intercept/threshold");
    }
    size_t entry_count()const{return k_;}
    const std::string& kind()const{return kind_;}
    FeaturePair inspect(const float* q)const {
        require(base_ && newer_ && !w0_.empty(),"feature inspection unavailable");
        FeaturePair p;p.base=base_->route(q);p.newer=newer_->route(q);
        first_features(q,p.base,p.x);extra_features(q,p.base,p.newer,p.x);
        for(double x:p.x)require(std::isfinite(x),"nonfinite online features");return p;
    }
    Choice choose(const float* q)const {
        Choice c;
        if(direct_){c.route=direct_->route(q);return c;}
        if(kind_=="fast20k"){c.route=base_->route(q);c.base_calls=1;return c;}
        if(kind_=="e24"){c.route=newer_->route(q);c.new_calls=1;c.use_new=1;return c;}
        FeatureVector x{};auto a=base_->route(q);c.base_calls=1;first_features(q,a,x);c.feature_dots=3;
        Decision b;
        const bool dual=kind_=="dual_gate" || kind_=="features";
        if(dual){b=newer_->route(q);c.new_calls=1;extra_features(q,a,b,x);c.feature_dots=6;}
        for(size_t j=0;j<(dual?13:7);++j)require(std::isfinite(x[j]),"nonfinite online gate feature");
        c.logit=force_>=0?double(force_):predict(x);
        c.use_new=force_>=0?uint8_t(force_):uint8_t(c.logit>=threshold_);
        if(c.use_new && !dual){b=newer_->route(q);c.new_calls=1;}
        c.route=c.use_new?b:a;
        c.route.ndc=counted_?a.ndc+(c.new_calls?b.ndc:0)+c.feature_dots:0;
        return c;
    }
};

struct AnnotatedBatch {
    BatchOutput out;
    std::vector<uint8_t> choices;
    std::vector<double> logits;
    std::vector<uint32_t> feature_dots,base_calls,new_calls;
    explicit AnnotatedBatch(size_t n):out(n),choices(n),logits(n),feature_dots(n),base_calls(n),new_calls(n){}
};
void routes(const SelectivePolicy& p,const std::vector<float>& q,size_t d,AnnotatedBatch& out) {
    for(size_t i=0;i<out.choices.size();++i) {
        const auto c=p.choose(q.data()+i*d);out.out.routes[i]=c.route;out.choices[i]=c.use_new;out.logits[i]=c.logit;
        out.feature_dots[i]=c.feature_dots;out.base_calls[i]=c.base_calls;out.new_calls[i]=c.new_calls;
    }
}
void run_plain(acsg::IndexACSGFlat& index,const SelectivePolicy& p,const std::vector<float>& q,size_t d,NativeWork& worker,AnnotatedBatch& out) {
    for(size_t i=0;i<out.choices.size();++i) {
        const auto c=p.choose(q.data()+i*d);out.out.routes[i]=c.route;out.choices[i]=c.use_new;out.logits[i]=c.logit;
        out.feature_dots[i]=c.feature_dots;out.base_calls[i]=c.base_calls;out.new_calls[i]=c.new_calls;
        out.out.searches[i]=worker.search(index,q.data()+i*d,c.route,p.entry_count());
    }
}
void run_graph(acsg::IndexACSGFlat& index,const SelectivePolicy& p,const std::vector<float>& q,size_t d,NativeWork& worker,AnnotatedBatch& out) {
    for(size_t i=0;i<out.choices.size();++i)out.out.searches[i]=worker.search(index,q.data()+i*d,out.out.routes[i],p.entry_count());
}
void compare_annotated(const AnnotatedBatch& a,const AnnotatedBatch& b) {
    compare(a.out,b.out);require(a.choices==b.choices && a.logits==b.logits && a.feature_dots==b.feature_dots && a.base_calls==b.base_calls && a.new_calls==b.new_calls,"decision/feature path mismatch");
    for(size_t i=0;i<a.choices.size();++i)require(std::memcmp(a.out.searches[i].distances.data(),b.out.searches[i].distances.data(),K*sizeof(float))==0,"distance bits differ");
}
void save_unscored(const AnnotatedBatch& a,const fs::path& path) {
    fs::create_directories(path);const size_t n=a.choices.size();
    std::vector<int32_t> ids(n*K),entries(n*3);std::vector<float> distances(n*K);
    for(size_t i=0;i<n;++i) {
        std::copy(a.out.searches[i].ids.begin(),a.out.searches[i].ids.end(),ids.begin()+i*K);
        std::copy(a.out.searches[i].distances.begin(),a.out.searches[i].distances.end(),distances.begin()+i*K);
        std::copy(a.out.routes[i].ids.begin(),a.out.routes[i].ids.end(),entries.begin()+i*3);
    }
    write_raw(path/"ids.i32",ids);write_raw(path/"distances.f32",distances);write_raw(path/"entry_ids.i32",entries);
    write_raw(path/"choose_new.u8",a.choices);write_raw(path/"logits.f64",a.logits);write_raw(path/"feature_dots.u32",a.feature_dots);
    write_raw(path/"base_route_calls.u32",a.base_calls);write_raw(path/"new_route_calls.u32",a.new_calls);
}

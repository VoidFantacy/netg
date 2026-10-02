#pragma once
#include <vector>
#include <unordered_map>
#include <stdexcept>

// Existing float-only graph; no appended document IDs or shadow result heap.
class DistinctHubStop final : public hnswlib::BaseSearchStopCondition<float> {
    bool slots_;
    std::vector<size_t> slot_hub_;
    std::unordered_map<hnswlib::labeltype,size_t> external_hub_;
    std::vector<unsigned> refs_;
    std::vector<size_t> touched_;
    size_t distinct_=0,points_=0,width_;
    size_t hub(hnswlib::labeltype label) const {
        if(slots_) {
            if(label>=slot_hub_.size())throw std::runtime_error("callback slot out of range");
            return slot_hub_[label];
        }
        return external_hub_.at(label);
    }
public:
    DistinctHubStop(const std::vector<int32_t>& mapping,bool slots,size_t width=10):slots_(slots),width_(width) {
        if(!width)throw std::runtime_error("zero distinct width");
        std::unordered_map<int32_t,size_t> dense;
        for(auto real:mapping) {
            auto p=dense.emplace(real,dense.size());size_t h=p.first->second;
            slot_hub_.push_back(h);external_hub_.emplace(size_t(real),h);
        }
        refs_.resize(dense.size());touched_.reserve(mapping.size());
    }
    void reset() {
        for(auto h:touched_)refs_[h]=0;
        touched_.clear();distinct_=0;points_=0;
    }
    void add_point_to_result(hnswlib::labeltype label,const void*,float) override {
        auto h=hub(label);if(refs_[h]++==0){++distinct_;touched_.push_back(h);}++points_;
    }
    void remove_point_from_result(hnswlib::labeltype label,const void*,float) override {
        auto h=hub(label);if(!refs_[h] || !points_)throw std::runtime_error("callback reference underflow");
        if(--refs_[h]==0)--distinct_;--points_;
    }
    bool should_stop_search(float candidate,float lower) override {return candidate>lower && distinct_==width_;}
    bool should_consider_candidate(float candidate,float lower) override {return distinct_<width_ || candidate<lower;}
    bool should_remove_extra() override {return distinct_>width_;}
    void filter_results(std::vector<std::pair<float,hnswlib::labeltype>>& x) override {
        if(x.size()!=points_)throw std::runtime_error("callback result count mismatch");
    }
    size_t distinct()const{return distinct_;}
    size_t points()const{return points_;}
};

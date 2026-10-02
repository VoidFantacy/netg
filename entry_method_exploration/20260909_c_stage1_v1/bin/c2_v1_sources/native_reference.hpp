#pragma once
#include "state_machine.hpp"
namespace native_reference {
using namespace faiss;
using namespace acsg;
inline std::mutex output_mutex;
    inline int insert_into_pool(Neighbor *addr, int K, Neighbor nn)
    {
        // find the location to insert
        int left = 0, right = K - 1;
        if (addr[left].distance > nn.distance)
        {
            memmove(&addr[left + 1], &addr[left], K * sizeof(Neighbor));
            addr[left] = nn;
            return left;
        }
        if (addr[right].distance < nn.distance)
        {
            addr[K] = nn;
            return K;
        }
        while (left < right - 1)
        {
            int mid = (left + right) / 2;
            if (addr[mid].distance > nn.distance)
            {
                right = mid;
            }
            else
            {
                left = mid;
            }
        }
        // check equal ID

        while (left > 0)
        {
            if (addr[left].distance < nn.distance)
            {
                break;
            }
            if (addr[left].id == nn.id)
            {
                return K + 1;
            }
            left--;
        }
        if (addr[left].id == nn.id || addr[right].id == nn.id)
        {
            return K + 1;
        }
        memmove(&addr[right + 1], &addr[right], (K - right) * sizeof(Neighbor));
        addr[right] = nn;
        return right;
    }

inline void run(const Graph<int32_t>& graph, DistanceComputer& dis, VisitedTable& vt,
    int L, std::vector<Neighbor>& retset, const std::vector<EnterPoint>& enterpoints,
    int mode, int query_id, SearchTrace* trace, int ntotal, cstage1::Observer* observer)
{
    RandomGenerator gen(0x1234);
    retset.resize(L + 1); 
    
    // 显式初始化 retset 为无穷大
    for(size_t i = 0; i <= L; ++i) {
        retset[i].distance = std::numeric_limits<float>::max();
        retset[i].id = -1;
        retset[i].flag = false;
    }

    int num_ids = 0;
    float first_enterpoint_distance = 0.0f;
    bool distance_recorded = false;

    auto record_distance = [&](int id, bool neighbor) {
        if (observer) observer->distance_order.push_back(id);
        if (!trace) return;
        ++trace->distance_evaluations;
        if (neighbor) ++trace->evaluated_neighbor_count;
        if (trace->first_topk_gt_evaluation_ndc != std::numeric_limits<uint64_t>::max() ||
            !trace->trace_gt || trace->trace_gt_k <= 0) return;
        for (int g = 0; g < trace->trace_gt_k; ++g) {
            if (id == trace->trace_gt[g]) {
                trace->first_topk_gt_evaluation_ndc = trace->distance_evaluations;
                trace->first_topk_gt_expansion = trace->expanded_count;
                break;
            }
        }
    };

    switch (mode) {
        case 0: { // 模式0: 单点随机入口
            int init_count = 0;
            while (init_count < 1) { 
                int node = gen.rand_int(ntotal);
                if (vt.get(node)) continue;
                
                vt.set(node);
                record_distance(node, false);
                float dist = dis(node);
                
                if (!distance_recorded && num_ids == 0) {
                    first_enterpoint_distance = dist;
                    distance_recorded = true;
                }
                
                retset[num_ids] = Neighbor(node, dist, true);
                num_ids++;
                init_count++;
            }
            break;
        }
        
        case 1: { // 模式1: ACO 全局 Top-1 入口
            for (int i = 0; i < enterpoints.size() && num_ids < 1; i++) {
                int id = enterpoints[i].id;
                if (!vt.get(id)) {
                    vt.set(id);
                    record_distance(id, false);
                    float dist = dis(id);
                    
                    if (!distance_recorded && num_ids == 0) {
                        first_enterpoint_distance = dist;
                        distance_recorded = true;
                    }
                    
                    retset[num_ids] = Neighbor(id, dist, true);
                    num_ids++;
                }
            }
            break;
        }

        case 2: { // 模式2: 自定义入口 (Neural Router)
            // 【修改第二步：解决挤占问题】
            // 限制初始填入的点数，给贪婪搜索留出“呼吸空间”。
            // 策略：最多只取 enterpoints 的前 1/3 或前 5 个，取较小值但至少留 1 个。
            // 这样既利用了 Neural 的好起点，又保留了随机游走的宽容度。
            
            int limit_heuristic = 3; 
            int max_init_points = std::min((int)enterpoints.size(), limit_heuristic);
            
            // 注意：循环条件增加了 i < max_init_points
            for (int i = 0; i < max_init_points && num_ids < L; i++) {
                int id = enterpoints[i].id;
                
                if (!vt.get(id)) {
                    vt.set(id);
                    record_distance(id, false);
                    float dist = dis(id);
                    
                    if (!distance_recorded && num_ids == 0) {
                        first_enterpoint_distance = dist;
                        distance_recorded = true;
                    }
                    
                    retset[num_ids] = Neighbor(id, dist, true);
                    num_ids++;
                }
            }
            
            // 兜底逻辑：如果传入的入口点都无效（例如越界），随机补一个
            if (num_ids == 0) {
                int init_count = 0;
                while (init_count < 1) {
                    int node = gen.rand_int(ntotal);
                    if (!vt.get(node)) {
                        vt.set(node);
                        record_distance(node, false);
                        retset[num_ids++] = Neighbor(node, dis(node), true);
                        init_count++;
                    }
                }
            }
            break;
        }
        
        default:
            FAISS_THROW_FMT("Invalid search mode in graph search: %d", mode);
    }
    
    // 仅用于调试日志
    if (query_id % 1000 == 0 && distance_recorded) {
        std::lock_guard<std::mutex> lock(output_mutex);
        // 日志逻辑...
    }
    
    std::sort(retset.begin(), retset.begin() + num_ids);
    if (trace && num_ids > 0) trace->initial_best_distance = retset[0].distance;

    int k = 0;
    uint64_t current_stagnation = 0;
    while (k < L) { 
        if (k >= num_ids) break; 

        int updated_pos = L;

        if (retset[k].flag) {
            retset[k].flag = false;
            int n = retset[k].id;
            if (observer) observer->expanded_order.push_back(n);
            if (trace) ++trace->expanded_count;
            const float best_before_expansion = retset[0].distance;

            for (int m = 0; m < graph.K; m++) {
                int id = (int)graph.at(n, m);
                if (id < 0 || id >= ntotal || vt.get(id)) {
                    continue;
                }
                vt.set(id);
                record_distance(id, true);
                float dist = dis(id);
                Neighbor nn(id, dist, true);
                
                if (num_ids >= L && dist >= retset[L - 1].distance) {
                    if (trace) ++trace->rejected_by_pool_bound_count;
                    continue;
                }
                const float best_before_insert = retset[0].distance;
                const float pool_before_insert = num_ids >= L
                    ? retset[L - 1].distance : std::numeric_limits<float>::max();
                int r = insert_into_pool(retset.data(), L, nn);
                if (r < L) { 
                    if (trace) {
                        ++trace->accepted_insertion_count;
                        if (retset[0].distance < best_before_insert) {
                            ++trace->best_distance_improvement_count;
                            trace->best_distance_improvement_sum +=
                                static_cast<double>(best_before_insert - retset[0].distance);
                        }
                        if (num_ids >= L && retset[L - 1].distance < pool_before_insert) {
                            ++trace->pool_bound_improvement_count;
                            trace->pool_bound_improvement_sum +=
                                static_cast<double>(pool_before_insert - retset[L - 1].distance);
                        }
                    }
                    updated_pos = std::min(updated_pos, r);
                    if (num_ids < L) num_ids++;
                }
            }
            if (trace) {
                if (retset[0].distance < best_before_expansion) {
                    if (current_stagnation > 0) {
                        ++trace->stagnation_run_count;
                        trace->stagnation_expansion_sum += current_stagnation;
                        trace->max_stagnation_expansions = std::max(
                            trace->max_stagnation_expansions, current_stagnation);
                        current_stagnation = 0;
                    }
                } else {
                    ++current_stagnation;
                }
            }
        }

        if (trace && updated_pos <= k) {
            ++trace->rewind_count;
            const uint64_t span = static_cast<uint64_t>(k - updated_pos);
            trace->rewind_span_sum += span;
            trace->rewind_span_max = std::max(trace->rewind_span_max, span);
        }
        k = (updated_pos <= k) ? updated_pos : (k + 1);
    }
    if (trace) {
        if (current_stagnation > 0) {
            ++trace->stagnation_run_count;
            trace->stagnation_expansion_sum += current_stagnation;
            trace->max_stagnation_expansions = std::max(trace->max_stagnation_expansions,
                                                         current_stagnation);
        }
        if (num_ids > 0) {
            trace->final_best_distance = retset[0].distance;
            const int last = std::min(num_ids, L) - 1;
            trace->final_pool_gap = retset[last].distance - retset[0].distance;
            if (last >= 1) trace->final_frontier_gap = retset[1].distance - retset[0].distance;
        }
    }
}
}

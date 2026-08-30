#include <faiss/impl/DistanceComputer.h>
#include <faiss/impl/NSG.h>
#include <ACSG/ACSG.h>

#include <algorithm>
#include <memory>
#include <mutex>
#include <iostream>
#include <atomic>
#include <unordered_set>
#include <queue>
#include <vector>
#include <unordered_map>

//thread_local std::vector<acsg::EnterPoint> acsg::ACSG::top_enterpoints;

namespace acsg
{
    using namespace faiss;
    using LockGuard = std::lock_guard<std::mutex>;

    

    std::mutex ndc_mutex;

    namespace
    {

        // It needs to be smaller than 0
        constexpr int EMPTY_ID = -1;
    } // namespace

    DistanceComputer *storage_distance_computer(const Index *storage)
    {
        if (is_similarity_metric(storage->metric_type))
        {
            return new NegativeDistanceComputer(storage->get_distance_computer());
        }
        else
        {
            return storage->get_distance_computer();
        }
    }

    struct Node
    {
        int id;
        float distance;

        Node() = default;
        Node(int id, float distance) : id(id), distance(distance) {}

        inline bool operator<(const Node &other) const
        {
            return distance < other.distance;
        }
    };

    struct newNeighbor
    {
        int id;
        float distance;
        float weight;
        bool flag;

        newNeighbor() = default;
        newNeighbor(int id, float distance, float weight, bool f)
            : id(id), distance(distance), weight(weight), flag(f) {}

        inline bool operator<(const newNeighbor &other) const
        {

            return distance < other.distance; // 在权重相同的情况下，距离小的优先
        }
    };

    inline int insert_into_new_pool(newNeighbor *addr, int K, newNeighbor nn)
    {
        // 二分查找插入位置
        int left = 0, right = K - 1;

        // 如果新元素更优，直接插入头部
        if (addr[left].weight < nn.weight)
        {
            memmove(&addr[left + 1], &addr[left], (K - left) * sizeof(newNeighbor));
            addr[left] = nn;
            return left;
        }

        // 如果新元素比最差的还差，直接返回
        if (addr[right].weight > nn.weight)
        {
            return K + 1;
        }

        // 二分查找插入位置
        while (left < right - 1)
        {
            int mid = (left + right) / 2;
            if (addr[mid].weight < nn.weight)
            {
                right = mid;
            }
            else
            {
                left = mid;
            }
        }

        // 检查 ID 是否已存在（避免重复插入）
        if (addr[left].id == nn.id || addr[right].id == nn.id)
        {
            return K + 1;
        }

        // 插入到 right 位置
        memmove(&addr[right + 1], &addr[right], (K - right - 1) * sizeof(newNeighbor));
        addr[right] = nn;
        return right;
    }

    inline int insert_into_pool_dis(newNeighbor *addr, int K, newNeighbor nn)
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
        memmove(&addr[right + 1], &addr[right], (K - right) * sizeof(newNeighbor));
        addr[right] = nn;
        return right;
    }

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

    ACSG::ACSG(int R) : nsg_R(R)
    {
        nsg_R = R;
        nsg_L = R + 32;
        nsg_C = R + 100;
        srand(0x1998);
    }

    void ACSG::build(
        Index *storage,
        idx_t n,
        const Graph<idx_t> &knn_graph,
        bool verbose)
    {
        FAISS_THROW_IF_NOT(!is_built && ntotal == 0);
        ntotal = n;
        int K = knn_graph.K;
        final_graph = std::make_shared<Graph<int32_t>>(n, K);
        std::fill_n(final_graph->data, n * K, EMPTY_ID);
        pheromone.resize(ntotal, 1.0f);
        weight.resize(ntotal, 0.0f);
#pragma omp parallel for

        for (int i = 0; i < n; i++)
        {
            int cnt = 0;
            for (int j = 0; j < knn_graph.K; j++)
            {
                int id = knn_graph.at(i, j);
                if (id != EMPTY_ID)
                {
                    final_graph->at(i, cnt) = id;
                    cnt += 1;
                }
            }
        }

        auto &graph = *final_graph;

        is_built = true;
    }

    std::tuple<std::vector<int>, double> ACSG::ant_search(faiss::DistanceComputer &dis, int k_target,
                                                          idx_t *gt,
                                                          faiss::VisitedTable &vt,
                                                          bool similarity_metric)
    {
        std::vector<int> path;
        int L = std::max(search_L, k_target); 
        int ep = enterpoint;
        auto &graph = *(final_graph);
        std::vector<int> init_ids(L, -1);
        int num_ids = 0;

        // Step 1: 从初始点获取有效邻居
        for (int i = 0; i < L && i < graph.K; i++)
        {
            int id = (int)graph.at(ep, i);
            if (id < 0 || id >= ntotal) continue;
            init_ids[num_ids++] = id;
            vt.set(id);
        }

        // Step 2: 用随机节点填充 init_ids
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dist(0, ntotal - 1);

        while (num_ids < L)
        {
            int id = dist(gen);
            if (vt.get(id)) continue;
            init_ids[num_ids++] = id;
            vt.set(id);
        }

        // Step 3: 初始化 retset 和 probabilities
        struct ScoredNeighbor {
            Neighbor n;
            float p;
            bool operator<(const ScoredNeighbor& other) const {
                return n.distance < other.n.distance;
            }
        };

        std::vector<ScoredNeighbor> temp_scored;
        temp_scored.reserve(L);
        std::vector<Neighbor> retset(L + 1);
        // retset needs L+1 slots for insert_into_pool's temporary shift, but
        // roulette selection must only see the L initialized candidates.
        std::vector<float> log_probabilities(
            L, -std::numeric_limits<float>::infinity());
        bool invalid_probability = false;

        // DistanceComputer is wrapped in NegativeDistanceComputer for IP, so
        // both metrics use the same "smaller is better" ordering.  The old
        // 1/(distance+eps) heuristic is invalid for negative IP distances:
        // raising a negative value to fractional alpha produces NaN.
        auto heuristic_for_distance = [similarity_metric](float distance) {
            if (similarity_metric) {
                // distance == -inner_product.  exp(inner_product) is positive
                // and monotonic; clipping prevents overflow on unnormalised IP.
                return std::exp(std::clamp(-distance, -20.0f, 20.0f));
            }
            return 1.0f / (std::max(distance, 0.0f) + 1e-6f);
        };

        for (int i = 0; i < L; i++)
        {
            int id = init_ids[i];
            float dist_val = dis(id); // Renamed to avoid confusion
            Neighbor nn(id, dist_val, true);
            
            float heuristic = heuristic_for_distance(dist_val);
            const float pheromone_value = pheromone[id];
            float log_probability = -std::numeric_limits<float>::infinity();
            if (pheromone_value > 0.0f && std::isfinite(pheromone_value) &&
                heuristic > 0.0f && std::isfinite(heuristic)) {
                // Equivalent to pheromone^beta * heuristic^alpha, without
                // overflow/underflow from the direct power/product form.
                log_probability = beta * std::log(pheromone_value) +
                                  alpha * std::log(heuristic);
            }
            if (!std::isfinite(log_probability)) {
                invalid_probability = true;
            }

            temp_scored.push_back({nn, log_probability});
            path.push_back(id);
        }

        // Step 4: 同步排序
        std::sort(temp_scored.begin(), temp_scored.end());
        for (int i = 0; i < L; i++) {
            retset[i] = temp_scored[i].n;
            log_probabilities[i] = temp_scored[i].p;
        }

        // Step 5: 蚁群搜索主循环
        int k = 0; 
        while (k < L)
        {
            int updated_pos = L;
            int n = roulette_wheel_selection(log_probabilities);

            if (n == -1) break;

            if (retset[n].flag)
            {
                idx_t node = retset[n].id;
                retset[n].flag = false;
                log_probabilities[n] = -std::numeric_limits<float>::infinity();

                for (int m = 0; m < graph.K; m++)
                {
                    int id = (int)graph.at(node, m);
                    if (id < 0 || id >= ntotal || vt.get(id)) continue;

                    vt.set(id);
                    float distance = dis(id);

                    if (distance > retset[L - 1].distance) continue;

                    path.push_back(id);
                    Neighbor nn(id, distance, true);
                    
                    int r = insert_into_pool(retset.data(), L, nn);

                    float heuristic = heuristic_for_distance(distance);
                    const float pheromone_value = pheromone[id];
                    float log_probability = -std::numeric_limits<float>::infinity();
                    if (pheromone_value > 0.0f && std::isfinite(pheromone_value) &&
                        heuristic > 0.0f && std::isfinite(heuristic)) {
                        log_probability = beta * std::log(pheromone_value) +
                                          alpha * std::log(heuristic);
                    }
                    if (!std::isfinite(log_probability)) {
                        invalid_probability = true;
                    }

                    insert_with_binary_search(log_probabilities, log_probability, r);
                    updated_pos = std::min(updated_pos, r);
                }
            }
            k = (updated_pos <= k) ? updated_pos : (k + 1);
        }

        // Step 6: metric-aware top-1 relative error. Keep the established L2
        // formula unchanged. For IP, DistanceComputer is wrapped and returns
        // -inner_product, so the relative similarity gap is
        // (gt_ip - candidate_ip) / |gt_ip|.
        float accuracy = 1.0f;
        const float epsilon = 1e-6f;
        if (gt != nullptr) {
            idx_t gt_id = *gt;
            if (gt_id < 0 || gt_id >= ntotal) {
                static std::atomic<bool> warned{false};
                bool expected = false;
                if (warned.compare_exchange_strong(expected, true)) {
                    std::cerr << "\n[CRITICAL ERROR] GT index out of bounds! gt_id="
                              << gt_id << ", ntotal=" << ntotal << "\n"
                              << "PLEASE CHECK: Are you using the correct GT file for this Index?" << std::endl;
                }
            } else {
                const float candidate_dist = retset[0].distance;
                const float gt_dist = dis(gt_id);
                if (similarity_metric) {
                    const float similarity_gap = candidate_dist - gt_dist;
                    accuracy = std::max(0.0f, similarity_gap) /
                               std::max(std::abs(gt_dist), epsilon);
                } else if (candidate_dist > epsilon) {
                    // Preserve the pre-existing L2 behavior.
                    accuracy = std::abs(candidate_dist - gt_dist) /
                               (gt_dist + epsilon);
                } else {
                    accuracy = 0.0f;
                }
            }
        }

        if (invalid_probability) {
            accuracy = std::numeric_limits<float>::quiet_NaN();
        }
        return {path, accuracy};
    }

void ACSG::insert_with_binary_search(
        std::vector<float> &log_probabilities, float log_probability, int r)
    {
        if (r >= 0 && r < static_cast<int>(log_probabilities.size()))
        {
            log_probabilities.insert(log_probabilities.begin() + r, log_probability);
            log_probabilities.pop_back();
        }
    }

    int ACSG::roulette_wheel_selection(
        const std::vector<float> &log_probabilities)
    {
        float max_log_probability = -std::numeric_limits<float>::infinity();
        int last_valid_index = -1;
        for (size_t i = 0; i < log_probabilities.size(); ++i) {
            if (std::isfinite(log_probabilities[i])) {
                max_log_probability = std::max(max_log_probability, log_probabilities[i]);
                last_valid_index = static_cast<int>(i);
            }
        }
        if (last_valid_index == -1) return -1;

        double sum_probability = 0.0;
        for (float log_probability : log_probabilities) {
            if (std::isfinite(log_probability)) {
                sum_probability += std::exp(
                    static_cast<double>(log_probability - max_log_probability));
            }
        }
        if (!std::isfinite(sum_probability) || sum_probability <= 0.0) return -1;

        static thread_local std::mt19937 gen(std::random_device{}());
        std::uniform_real_distribution<double> dist(0.0, sum_probability);
        const double threshold = dist(gen);

        double cumulative_probability = 0.0;
        for (size_t i = 0; i < log_probabilities.size(); ++i) {
            if (std::isfinite(log_probabilities[i])) {
                cumulative_probability += std::exp(static_cast<double>(
                    log_probabilities[i] - max_log_probability));
                if (cumulative_probability >= threshold) {
                    return static_cast<int>(i);
                }
            }
        }
        return last_valid_index;
    }

    void ACSG::update_weight()
    {
        // === 修改：使用对数归一化 (Log-Normalization) ===
        // 解决权重分布极化问题，让 DPC 能识别出次优的枢纽点

        float max_log_ph = -std::numeric_limits<float>::max();
        float min_log_ph = std::numeric_limits<float>::max();
        
        // 临时存储对数值，避免重复计算
        std::vector<float> log_pheromone(ntotal);

        // 1. 先取对数，压缩动态范围 (顺便找最大最小值)
        // 使用 log1p(x) = log(1+x) 可以处理 x=0 的情况，且数值更稳
        for (int i = 0; i < ntotal; i++) {
            // 加上 1.0f 保证 log 的参数 >= 1，结果 >= 0
            float val = std::log(pheromone[i] + 1.0f);
            log_pheromone[i] = val;
            
            if (val > max_log_ph) max_log_ph = val;
            if (val < min_log_ph) min_log_ph = val;
        }

        std::cout << "[Weight Update] Log-Pheromone Range: [" << min_log_ph << ", " << max_log_ph << "]" << std::endl;
        
        float range = max_log_ph - min_log_ph;
        if (range < 1e-6) range = 1.0f; // 防止除以0

        // 2. 基于对数域进行归一化
        #pragma omp parallel for
        for (int i = 0; i < ntotal; i++) {
            weight[i] = (log_pheromone[i] - min_log_ph) / range;
        }

        // === 下面是原有的 Top-Enterpoints 更新逻辑 (保持不变) ===
        
        // 创建索引数组
        std::vector<int> indices(ntotal);
        std::iota(indices.begin(), indices.end(), 0);

        size_t target_k = 1000;
        if (target_k > ntotal) target_k = ntotal;

        // 使用 nth_element 快速筛选
        std::nth_element(indices.begin(), indices.begin() + target_k, indices.end(),
                        [&](int a, int b) { return weight[a] > weight[b]; });

        std::sort(indices.begin(), indices.begin() + target_k,
                [&](int a, int b) { return weight[a] > weight[b]; });

        top_enterpoints.clear();
        top_enterpoints.reserve(target_k);
        for (size_t i = 0; i < target_k; i++) {
            int idx = indices[i];
            top_enterpoints.emplace_back(idx, (double)weight[idx]);
        }
        
        std::cout << "[Weight Update] Top-1 Weight: " << weight[indices[0]] 
                << ", Top-" << target_k << " Weight: " << weight[indices[target_k-1]] << std::endl;
    }


    void ACSG::print_weight_distribution()
    {
        if (weight.empty())
        {
            std::cout << "⚠️ Warning: Weights are empty!" << std::endl;
            return;
        }

        // 1. 拷贝权重并进行降序排序
        std::vector<float> sorted_weights = weight;
        std::sort(sorted_weights.begin(), sorted_weights.end(), std::greater<float>());

        size_t n = sorted_weights.size();
        
        std::cout << "\n=============================================" << std::endl;
        std::cout << "📊 Weight Distribution Statistics (Total: " << n << ")" << std::endl;
        std::cout << "=============================================" << std::endl;

        // 2. 打印最高权重 (Top 0%)
        std::cout << "Top 0%   (Max) : " << sorted_weights[0] << std::endl;

        // 3. 打印 10% 到 90% 的分位点
        for (int i = 1; i <= 9; ++i)
        {
            // 计算索引：例如 10% 对应索引 n * 0.1
            size_t idx = static_cast<size_t>(n * i * 0.1);
            if (idx >= n) idx = n - 1;
            
            std::cout << "Top " << i * 10 << "%         : " << sorted_weights[idx] << std::endl;
        }

        // 4. 打印最低权重 (Top 100%)
        std::cout << "Top 100% (Min) : " << sorted_weights.back() << std::endl;
        std::cout << "=============================================\n" << std::endl;
    }

    // 信息素更新
    // 修改文件：code/ACSG/ACSG.cpp

    void ACSG::update_pheromone(const std::vector<int> &paths, const float accuracy)
    {
        // 1. 准确率得分 (基础分)
        // 你的日志显示 accuracy 经常为 0，所以这一项经常是常数最大值
        float accuracy_score = 1.0f / (accuracy + 1e-6f);

        // 2. [新增] 效率得分 (路径长度惩罚)
        // 这才是打破 "Error=0" 僵局的关键！
        // 步数越少 (paths.size 小)，得分越高
        float efficiency_score = 1.0f / std::log((float)paths.size() + 2.0f);

        // 3. 综合权重
        float path_quality = Q * accuracy_score * efficiency_score;

        // 4. 原子更新
        for (size_t i = 0; i < paths.size(); i++)
        {
            const auto &node = paths[i];
            #pragma omp atomic
            pheromone[node] += path_quality;
        }
    }

    void ACSG::decrease_pheromone()
    {
        auto &graph = *final_graph;

#pragma omp parallel for

        for (int i = 0; i < ntotal; i++)
        {
            pheromone[i] *= (1 - rho); // 挥发
        }
    }

    // float ACSG::eval_recall(
    //     const size_t nq, const size_t k, const size_t stride_labels,
    //     const std::unique_ptr<faiss::idx_t[]> &labels,
    //     const size_t stride_gt,
    //     const int64_t *gt)
    // {

    //     assert(k <= stride_labels);

    //     float mean_recall = 0;
    //     for (int i = 0; i < nq; ++i)
    //     {
    //         float recall = 0;
    //         std::unordered_set<int> cur_query_res;
    //         std::unordered_set<int> cur_query_gt;

    //         for (int j = 0; j < k; ++j)
    //         {
    //             cur_query_res.insert(labels[i * stride_labels + j]);
    //             cur_query_gt.insert(gt[i * stride_gt + j]);
    //         }
    //         for (const auto &id : cur_query_res)
    //         {
    //             if (cur_query_gt.count(id))
    //             {
    //                 recall += 1.0f;
    //             }
    //         }
    //         recall = recall / k;
    //         mean_recall += recall;
    //     }
    //     mean_recall = mean_recall / nq;

    //     return mean_recall;
    // }

    void ACSG::search(
        DistanceComputer &dis,
        int k,
        idx_t *I,
        float *D,
        VisitedTable &vt) const
    {
        FAISS_THROW_IF_NOT(is_built);
        FAISS_THROW_IF_NOT(final_graph);

        int pool_size = std::max(search_L, k);
        std::vector<Neighbor> retset;
        std::vector<Node> tmp;
        search_on_graph<false>(
            *final_graph, dis, vt, enterpoint, pool_size, retset, tmp);

        for (size_t i = 0; i < k; i++)
        {
            I[i] = retset[i].id;
            D[i] = retset[i].distance;
        }
    }

    void ACSG::reset()
    {
        final_graph.reset();
        ntotal = 0;
        is_built = false;
    }

    template <bool collect_fullset, class index_t>
    void ACSG::search_on_graph(
        const Graph<index_t> &graph,
        DistanceComputer &dis,
        VisitedTable &vt,
        int ep,
        int pool_size,
        std::vector<Neighbor> &retset,
        std::vector<Node> &fullset) const
    {
        RandomGenerator gen(0x1234);
        retset.resize(pool_size + 1);
        std::vector<int> init_ids(pool_size);

        int num_ids = 0;
        for (int i = 0; i < init_ids.size() && i < graph.K; i++)
        {
            int id = (int)graph.at(ep, i);
            if (id < 0 || id >= ntotal)
            {
                continue;
            }

            init_ids[i] = id;
            vt.set(id);
            num_ids += 1;
        }

        while (num_ids < pool_size)
        {
            int id = gen.rand_int(ntotal);
            if (vt.get(id))
            {
                continue;
            }

            init_ids[num_ids] = id;
            num_ids++;
            vt.set(id);
        }

        for (int i = 0; i < init_ids.size(); i++)
        {
            int id = init_ids[i];

            float dist = dis(id);
            retset[i] = Neighbor(id, dist, true);

            if (collect_fullset)
            {
                fullset.emplace_back(retset[i].id, retset[i].distance);
            }
        }

        std::sort(retset.begin(), retset.begin() + pool_size);

        int k = 0;
        while (k < pool_size)
        {
            int updated_pos = pool_size;

            if (retset[k].flag)
            {
                retset[k].flag = false;
                int n = retset[k].id;

                for (int m = 0; m < graph.K; m++)
                {
                    int id = (int)graph.at(n, m);
                    if (id < 0 || id >= ntotal || vt.get(id))
                    {
                        continue;
                    }
                    vt.set(id);

                    float dist = dis(id);
                    Neighbor nn(id, dist, true);
                    if (collect_fullset)
                    {
                        fullset.emplace_back(id, dist);
                    }

                    if (dist >= retset[pool_size - 1].distance)
                    {
                        continue;
                    }

                    int r = insert_into_pool(retset.data(), pool_size, nn);

                    updated_pos = std::min(updated_pos, r);
                }
            }

            k = (updated_pos <= k) ? updated_pos : (k + 1);
        }
    }


    
    template <bool collect_fullset, class index_t>
    void ACSG::search_on_graph_ACO(const Graph<index_t> &graph,
                                   DistanceComputer &dis,
                                   VisitedTable &vt,
                                   int ep,
                                   int L,
                                   std::vector<Neighbor> &retset)
    {
        RandomGenerator gen(0x1234);
        retset.resize(L + 1);
        int num_ids = 0;
        for (int i = 0; i < top_enterpoints.size() && num_ids < L; i++)
        {
            // 获取from和to
            int id = top_enterpoints[i].id;
            if (!vt.get(id))
            {
                vt.set(id);
                float dist = dis(id);
                //NDC.fetch_add(1, std::memory_order_relaxed);
                retset[num_ids] = Neighbor(id, dist, true);
                num_ids += 1;
            }
        }
        while (num_ids < L)
        {
            int node = gen.rand_int(ntotal);
            int id = (int)graph.at(node, 0);
            if (vt.get(id))
            {
                continue;
            }
            vt.set(id);
            float dist = dis(id);
            //NDC.fetch_add(1, std::memory_order_relaxed);
            retset[num_ids] = Neighbor(id, dist, true);
            num_ids += 1;
        }
        std::sort(retset.begin(), retset.begin() + L);
        int k = 0;
        while (k < L)
        {
            int updated_pos = L;

            if (retset[k].flag)
            {
                retset[k].flag = false;
                int n = retset[k].id;

                for (int m = 0; m < graph.K; m++)
                {
                    int id = (int)graph.at(n, m);
                    if (id < 0 || id >= ntotal || vt.get(id))
                    {
                        continue;
                    }
                    vt.set(id);
                    float dist = dis(id);
                    //NDC.fetch_add(1, std::memory_order_relaxed);
                    Neighbor nn(id, dist, true);
                    if (dist >= retset[L - 1].distance)
                    {
                        continue;
                    }
                    int r = insert_into_pool(retset.data(), L, nn);
                    updated_pos = std::min(updated_pos, r);
                }
            }

            k = (updated_pos <= k) ? updated_pos : (k + 1);
        }
    }

    template <bool collect_fullset, class index_t>
    void ACSG::search_on_graph_ACO_v1(const Graph<index_t> &graph,
                                      DistanceComputer &dis,
                                      VisitedTable &vt,
                                      int ep,
                                      int L,
                                      std::vector<Neighbor> &retset)
    {
        RandomGenerator gen(0x1234);
        retset.resize(L + 1);
        int num_ids = 0;
        std::vector<newNeighbor> weights(L + 1);
        for (int i = 0; i < top_enterpoints.size() && num_ids < L; i++)
        {
            // 获取from和to
            int id = top_enterpoints[i].id;
            if (!vt.get(id))
            {
                vt.set(id);
                float dist = dis(id);
                //NDC.fetch_add(1, std::memory_order_relaxed);
                retset[num_ids] = Neighbor(id, dist, true);
                num_ids += 1;
            }
        }
        while (num_ids < L)
        {
            int node = gen.rand_int(ntotal);
            int id = (int)graph.at(node, 0);
            if (vt.get(id))
            {
                continue;
            }
            vt.set(id);
            float dist = dis(id);
            //NDC.fetch_add(1, std::memory_order_relaxed);
            retset[num_ids] = Neighbor(id, dist, true);
            num_ids += 1;
        }
        std::sort(retset.begin(), retset.begin() + L);
        for (size_t i = 0; i < L; i++)
        {
            /* code */
            weights[i] = newNeighbor(retset[i].id, retset[i].distance, weight[retset[i].id], true);
            // std::cerr << "weight[" << i << "]:" << weights[i].id << weights[i].weight << std::endl;
        }

        int k = 0;
        while (k < L)
        {
            int updated_pos = L;

            if (weights[k].flag)
            {
                weights[k].flag = false;
                int n = weights[k].id;

                for (int m = 0; m < graph.K; m++)
                {
                    int id = (int)graph.at(n, m);
                    if (id < 0 || id >= ntotal || vt.get(id))
                    {
                        continue;
                    }
                    vt.set(id);
                    float dist = dis(id);
                    // std::lock_guard<std::mutex> lock(ndc_mutex);
                    // NDC++;
                    Neighbor nn(id, dist, true);
                    if (dist >= retset[L - 1].distance)
                    {
                        continue;
                    }
                    insert_into_pool(retset.data(), L, nn);
                    int r = insert_into_new_pool(weights.data(), L, newNeighbor(id, dist, weight[id], true));
                    updated_pos = std::min(updated_pos, r);
                }
            }

            k = (updated_pos <= k) ? updated_pos : (k + 1);
        }
    }

    void ACSG::search_ACO(
        DistanceComputer &dis,
        int topk,
        idx_t *I,
        float *D,
        VisitedTable &vt)
    { 
        FAISS_THROW_IF_NOT(is_built);
        FAISS_THROW_IF_NOT(final_graph);

        int pool_size = std::max(search_L, topk);
        std::vector<Neighbor> retset;
        search_on_graph_ACO<false>(
            *final_graph, dis, vt, enterpoint, pool_size, retset);

        for (size_t i = 0; i < topk; i++)
        {
            I[i] = retset[i].id;
            D[i] = retset[i].distance;
        }
        // for (size_t i = 0; i < topk; i++)
        // {
        //     gt_simi[i] = dis(gts[i]);
        // }
    }

    void ACSG::search_DPC_ACO(
        DistanceComputer &dis,
        int topk,
        idx_t *I,
        float *D,
        VisitedTable &vt,
        const std::vector<EnterPoint> &custom_enterpoints)
    { 
        FAISS_THROW_IF_NOT(is_built);
        FAISS_THROW_IF_NOT(final_graph);

        int pool_size = std::max(search_L, topk);
        std::vector<Neighbor> retset;
        
        // 使用自定义入口点进行搜索
        search_on_graph_DPC_ACO<false>(
            *final_graph, dis, vt, enterpoint, pool_size, retset, custom_enterpoints);

        for (size_t i = 0; i < topk; i++)
        {
            I[i] = retset[i].id;
            D[i] = retset[i].distance;
        }
    }

    template <bool collect_fullset, class index_t>
    void ACSG::search_on_graph_DPC_ACO(const Graph<index_t> &graph,
                                    DistanceComputer &dis,
                                    VisitedTable &vt,
                                    int ep,
                                    int L,
                                    std::vector<Neighbor> &retset,
                                    const std::vector<EnterPoint> &custom_enterpoints)
    {
        RandomGenerator gen(0x1234);
        retset.resize(L + 1);
        int num_ids = 0;

        static std::once_flag once_flag;
        std::call_once(once_flag, [&]() {
            std::cout << "DPC_ACO搜索初始化 - 使用自定义入口点，大小: " 
                    << custom_enterpoints.size() << std::endl;
        });
        
        // 使用传入的自定义入口点，而不是默认的 top_enterpoints
        for (int i = 0; i < custom_enterpoints.size() && num_ids < L; i++)
        {
            // 获取自定义入口点的ID
            int id = custom_enterpoints[i].id;
            if (!vt.get(id))
            {
                vt.set(id);
                float dist = dis(id);
                //NDC.fetch_add(1, std::memory_order_relaxed);
                retset[num_ids] = Neighbor(id, dist, true);
                num_ids += 1;
            }
        }
        
        // 如果自定义入口点数量不足，用随机节点补充
        while (num_ids < L)
        {
            int node = gen.rand_int(ntotal);
            int id = (int)graph.at(node, 0);
            if (vt.get(id))
            {
                continue;
            }
            vt.set(id);
            float dist = dis(id);
            //NDC.fetch_add(1, std::memory_order_relaxed);
            retset[num_ids] = Neighbor(id, dist, true);
            num_ids += 1;
        }
        
        std::sort(retset.begin(), retset.begin() + L);
        int k = 0;
        while (k < L)
        {
            int updated_pos = L;

            if (retset[k].flag)
            {
                retset[k].flag = false;
                int n = retset[k].id;

                for (int m = 0; m < graph.K; m++)
                {
                    int id = (int)graph.at(n, m);
                    if (id < 0 || id >= ntotal || vt.get(id))
                    {
                        continue;
                    }
                    vt.set(id);
                    float dist = dis(id);
                    //NDC.fetch_add(1, std::memory_order_relaxed);
                    Neighbor nn(id, dist, true);
                    if (dist >= retset[L - 1].distance)
                    {
                        continue;
                    }
                    int r = insert_into_pool(retset.data(), L, nn);
                    updated_pos = std::min(updated_pos, r);
                }
            }

            k = (updated_pos <= k) ? updated_pos : (k + 1);
        }
    }

    template <bool collect_fullset, class index_t>
    void ACSG::search_on_graph_v1(
        const Graph<index_t> &graph,
        DistanceComputer &dis,
        VisitedTable &vt,
        int ep,
        int pool_size,
        std::vector<Neighbor> &retset,
        std::vector<Node> &fullset)
    {
        RandomGenerator gen(0x1234);
        retset.resize(pool_size + 1);
        std::vector<int> init_ids(pool_size);

        int num_ids = 0;
        for (int i = 0; i < init_ids.size() && i < graph.K; i++)
        {
            int id = (int)graph.at(ep, i);
            if (id < 0 || id >= ntotal)
            {
                continue;
            }

            init_ids[i] = id;
            vt.set(id);
            num_ids += 1;
        }

        while (num_ids < pool_size)
        {
            int id = gen.rand_int(ntotal);
            if (vt.get(id))
            {
                continue;
            }

            init_ids[num_ids] = id;
            num_ids++;
            vt.set(id);
        }

        for (int i = 0; i < init_ids.size(); i++)
        {
            int id = init_ids[i];

            float dist = dis(id);
            //NDC.fetch_add(1, std::memory_order_relaxed);
            retset[i] = Neighbor(id, dist, true);

            if (collect_fullset)
            {
                fullset.emplace_back(retset[i].id, retset[i].distance);
            }
        }

        std::sort(retset.begin(), retset.begin() + pool_size);

        int k = 0;
        while (k < pool_size)
        {
            int updated_pos = pool_size;

            if (retset[k].flag)
            {
                retset[k].flag = false;
                int n = retset[k].id;

                for (int m = 0; m < graph.K; m++)
                {
                    int id = (int)graph.at(n, m);
                    if (id < 0 || id >= ntotal || vt.get(id))
                    {
                        continue;
                    }
                    vt.set(id);

                    float dist = dis(id);
                    //NDC.fetch_add(1, std::memory_order_relaxed);
                    Neighbor nn(id, dist, true);
                    if (collect_fullset)
                    {
                        fullset.emplace_back(id, dist);
                    }

                    if (dist >= retset[pool_size - 1].distance)
                    {
                        continue;
                    }

                    int r = insert_into_pool(retset.data(), pool_size, nn);

                    updated_pos = std::min(updated_pos, r);
                }
            }

            k = (updated_pos <= k) ? updated_pos : (k + 1);
        }
    }

    template <bool collect_fullset, class index_t>
    void ACSG::search_on_graph_v2(
        const Graph<index_t> &graph,
        DistanceComputer &dis,
        VisitedTable &vt,
        int ep,
        int pool_size,
        std::vector<Neighbor> &retset,
        std::vector<Node> &fullset)
    {
        RandomGenerator gen(0x1234);
        retset.resize(pool_size + 1);
        int num_ids = 0;
        
        // 修改入口点选择逻辑：完全随机选择，与第二个函数保持一致
        while (num_ids < pool_size)
        {
            int node = gen.rand_int(ntotal);
            int id = (int)graph.at(node, 0);
            if (vt.get(id))
            {
                continue;
            }
            vt.set(id);
            float dist = dis(id);
            //NDC.fetch_add(1, std::memory_order_relaxed);
            retset[num_ids] = Neighbor(id, dist, true);
            num_ids += 1;
        }

        std::sort(retset.begin(), retset.begin() + pool_size);

        int k = 0;
        while (k < pool_size)
        {
            int updated_pos = pool_size;

            if (retset[k].flag)
            {
                retset[k].flag = false;
                int n = retset[k].id;

                for (int m = 0; m < graph.K; m++)
                {
                    int id = (int)graph.at(n, m);
                    if (id < 0 || id >= ntotal || vt.get(id))
                    {
                        continue;
                    }
                    vt.set(id);

                    float dist = dis(id);
                    //NDC.fetch_add(1, std::memory_order_relaxed);
                    Neighbor nn(id, dist, true);

                    if (dist >= retset[pool_size - 1].distance)
                    {
                        continue;
                    }

                    int r = insert_into_pool(retset.data(), pool_size, nn);

                    updated_pos = std::min(updated_pos, r);
                }
            }

            k = (updated_pos <= k) ? updated_pos : (k + 1);
        }
    }
    
    void ACSG::search_v1(
        DistanceComputer &dis,
        int k,
        idx_t *I,
        float *D,
        VisitedTable &vt)
    {
        FAISS_THROW_IF_NOT(is_built);
        FAISS_THROW_IF_NOT(final_graph);

        int pool_size = std::max(search_L, k);
        std::vector<Neighbor> retset;
        std::vector<Node> tmp;
        search_on_graph_v2<false>(
            *final_graph, dis, vt, enterpoint, pool_size, retset, tmp);

        for (size_t i = 0; i < k; i++)
        {
            I[i] = retset[i].id;
            D[i] = retset[i].distance;
        }

        // for (size_t i = 0; i < k; i++)
        // {
        //     gt_simi[i] = dis(gts[i]);
        // }
    }

    void ACSG::brute_force_search(
        DistanceComputer &dis,
        int topk,
        idx_t *I,
        float *D,
        idx_t nb,
        const float *xb)
    {
        std::vector<Neighbor> retset(topk);
        for (size_t i = 0; i < topk; i++)
        {
            /* code */
            retset[i] = Neighbor(i, dis(i), true);
        }
        std::sort(retset.begin(), retset.begin() + topk);
        for (size_t i = topk; i < nb; i++)
        {
            /* code */
            float dist = dis(i);
            if (dist < retset[topk - 1].distance)
            {
                insert_into_pool(retset.data(), topk, Neighbor(i, dist, true));
            }
        }

        for (int j = 0; j < topk; j++)
        {
            I[j] = retset[j].id;
            D[j] = retset[j].distance;
        }
    }

void ACSG::search_new(
    DistanceComputer &dis,
    int topk,
    idx_t *I,
    float *D,
    VisitedTable &vt,
    int mode,
    const std::vector<EnterPoint> &custom_enterpoints,
    std::vector<Neighbor> *retset_buf)
{ 
    FAISS_THROW_IF_NOT(is_built);
    FAISS_THROW_IF_NOT(final_graph);

    int pool_size = std::max(search_L, topk); 

    // 【性能优化】如果外部传入了 retset 缓冲区，直接复用避免堆分配
    // 否则创建局部变量（向后兼容旧调用方）
    std::vector<Neighbor> retset_local;
    std::vector<Neighbor> &retset = retset_buf ? *retset_buf : retset_local;

    int current_query = query_counter.fetch_add(1, std::memory_order_relaxed);
    
    // 根据模式选择不同的入口点策略
    switch (mode) {
        case 0: // 模式0: 随机选择入口点
            search_on_graph_new<false>(
                *final_graph, dis, vt, pool_size, retset, 
                std::vector<EnterPoint>(), mode, current_query);
            break;
        case 1: // 模式1: 使用固定权重高的入口点 (Top-1)
            search_on_graph_new<false>(
                *final_graph, dis, vt, pool_size, retset, 
                top_enterpoints, mode, current_query);
            break;
        case 2: // 模式2: 使用自定义入口点 (Neural Router)
            search_on_graph_new<false>(
                *final_graph, dis, vt, pool_size, retset, 
                custom_enterpoints, mode, current_query);
            break;
        default:
            FAISS_THROW_FMT("Invalid search mode: %d", mode);
    }

    // 安全地将结果写入输出数组
    for (size_t i = 0; i < topk; i++) {
        // 检查 i 是否在 retset 有效范围内，且 ID 有效
        if (i < retset.size() && retset[i].id != -1) {
            I[i] = retset[i].id;
            D[i] = retset[i].distance;
        } else {
            // 兜底：如果结果不足，填充 -1
            I[i] = -1;
            D[i] = std::numeric_limits<float>::max();
        }
    }
}

template <bool collect_fullset, class index_t>
void ACSG::search_on_graph_new(const Graph<index_t> &graph,
                            DistanceComputer &dis,
                            VisitedTable &vt,
                            int L,
                            std::vector<Neighbor> &retset,
                            const std::vector<EnterPoint> &enterpoints,
                            int mode,
                            int query_id)
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

    switch (mode) {
        case 0: { // 模式0: 单点随机入口
            int init_count = 0;
            while (init_count < 1) { 
                int node = gen.rand_int(ntotal);
                if (vt.get(node)) continue;
                
                vt.set(node);
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

    int k = 0;
    while (k < L) { 
        if (k >= num_ids) break; 

        int updated_pos = L;

        if (retset[k].flag) {
            retset[k].flag = false;
            int n = retset[k].id;

            for (int m = 0; m < graph.K; m++) {
                int id = (int)graph.at(n, m);
                if (id < 0 || id >= ntotal || vt.get(id)) {
                    continue;
                }
                vt.set(id);
                float dist = dis(id);
                Neighbor nn(id, dist, true);
                
                if (num_ids >= L && dist >= retset[L - 1].distance) {
                    continue;
                }
                
                int r = insert_into_pool(retset.data(), L, nn);
                if (r < L) { 
                    updated_pos = std::min(updated_pos, r);
                    if (num_ids < L) num_ids++;
                }
            }
        }

        k = (updated_pos <= k) ? updated_pos : (k + 1);
    }
}

}

#include <iostream>
#include <argparse/argparse.hpp>
#include <benches/datasets/DataLoader.hpp>
#include <nlohmann/json.hpp>
#include <ACSG/IndexACSG.h>
#include <tuple>
#include <fstream>
#include <filesystem>
#include <vector>
#include <algorithm>
#include <numeric>
#include <random>
#include <omp.h>
#include <atomic>
#include <mutex>
#include <map>
#include <unordered_set>
#include <cmath>

#include <benches/utils/Timer.hpp>
#include <benches/utils/metrics.hpp>
#include <benches/utils/graph_properties.hpp>
#include <iomanip>

// 聚类结果数据结构
struct ClusterHierarchy {
    std::vector<int> top_centers;
    std::vector<int> bottom_centers;
    std::vector<std::vector<int>> region_to_fine;
    std::vector<float> densities;
    std::vector<int> top_labels;
    std::vector<int> bottom_labels;
};

// KPH-DPC 配置结构
struct KPHDPCConfig {
    int top_percent_threshold = 5;
    int knn_search_limit = 32;
    int max_search_depth = 3;
    int target_centers = 100;
    std::string search_strategy = "global";
    std::string gamma_method = "original";
    
    float gamma_exponent = 1.0f;
    float min_density_threshold = 0.0f;
    
    KPHDPCConfig() = default;
    KPHDPCConfig(int percent, int knn, int depth, int centers, 
                 const std::string& strategy, const std::string& method = "sqrt")
        : top_percent_threshold(percent), knn_search_limit(knn),
          max_search_depth(depth), target_centers(centers), 
          search_strategy(strategy), gamma_method(method) {}
};

// 聚类结果
struct DPCResult {
    std::vector<int> cluster_centers;
    std::vector<int> cluster_labels;
    std::vector<float> densities;
    std::vector<float> deltas;
    std::vector<float> gammas;
    
    void clear() {
        cluster_centers.clear(); cluster_labels.clear();
        densities.clear(); deltas.clear(); gammas.clear();
    }
};

// 两层聚类结果
struct TwoLayerClustering {
    DPCResult top_layer;
    DPCResult bottom_layer;
    std::vector<std::vector<int>> region_to_fine;
    void clear() { top_layer.clear(); bottom_layer.clear(); region_to_fine.clear(); }
};

void extract_cluster_centers_from_dpc(const TwoLayerClustering& dpc_result, ClusterHierarchy& hierarchy) {
    hierarchy.top_centers = dpc_result.top_layer.cluster_centers;
    hierarchy.bottom_centers = dpc_result.bottom_layer.cluster_centers;
    hierarchy.top_labels = dpc_result.top_layer.cluster_labels;
    hierarchy.bottom_labels = dpc_result.bottom_layer.cluster_labels;
    hierarchy.densities = dpc_result.bottom_layer.densities;
    std::cout << "Extracted cluster centers: " << hierarchy.top_centers.size() 
              << " top, " << hierarchy.bottom_centers.size() << " bottom" << std::endl;
}

// 线程安全随机数
class ThreadSafeRandom {
public:
    std::mt19937& get_local() {
        static thread_local std::mt19937 generator(std::random_device{}());
        return generator;
    }
};

// K-means加速器 (纯串行，彻底解决段错误)
class KMeansDistanceCalculator {
private:
    int n_ = 0, d_ = 0, k_ = 0;
    std::vector<int> point_to_cluster_;
    std::vector<std::vector<float>> cluster_centers_;
    std::vector<std::vector<float>> cluster_distances_;
    bool use_kmeans_ = false;
    
    float direct_euclidean_distance(int i, int j, const float* vectors) const {
        const float* vec_i = vectors + i * d_;
        const float* vec_j = vectors + j * d_;
        float dist = 0.0f;
        #pragma omp simd reduction(+:dist)
        for (int k = 0; k < d_; k++) {
            float diff = vec_i[k] - vec_j[k];
            dist += diff * diff;
        }
        return std::sqrt(dist);
    }
    
public:
    void build(const float* vectors, int n, int dim, int k, bool use_1000_subspaces = false) {
        n_ = n; d_ = dim;
        
        if (n < 500) {
            use_kmeans_ = false;
            k_ = 0;
            return;
        }
        
        use_kmeans_ = true;
        k_ = use_1000_subspaces ? std::min(1000, n / 100) : std::min(512, n / 100);
        k_ = std::max(k_, 10);
        
        const int max_iterations = (n > 5000) ? 3 : 5;
        
        cluster_centers_.resize(k_);
        std::vector<int> all_indices(n);
        std::iota(all_indices.begin(), all_indices.end(), 0);
        
        ThreadSafeRandom random_gen;
        std::shuffle(all_indices.begin(), all_indices.end(), random_gen.get_local());
        
        for (int i = 0; i < k_; i++) {
            cluster_centers_[i].resize(d_);
            const float* vec = vectors + all_indices[i] * d_;
            std::copy(vec, vec + d_, cluster_centers_[i].begin());
        }
        
        for (int iter = 0; iter < max_iterations; iter++) {
            point_to_cluster_.resize(n);
            // 并行分配：每个线程维护私有的 counts/sums，最后合并
            int num_threads = omp_get_max_threads();
            std::vector<std::vector<int>> local_counts(num_threads, std::vector<int>(k_, 0));
            std::vector<std::vector<std::vector<float>>> local_sums(num_threads, std::vector<std::vector<float>>(k_, std::vector<float>(d_, 0.0f)));

            #pragma omp parallel for schedule(static)
            for (int i = 0; i < n; i++) {
                int tid = omp_get_thread_num();
                const float* vec = vectors + i * d_;
                int best_c = 0;
                float min_d = std::numeric_limits<float>::max();
                for (int j = 0; j < k_; j++) {
                    float dist = 0.0f;
                    #pragma omp simd reduction(+:dist)
                    for (int x = 0; x < d_; x++) {
                        float diff = vec[x] - cluster_centers_[j][x];
                        dist += diff * diff;
                    }
                    if (dist < min_d) { min_d = dist; best_c = j; }
                }
                point_to_cluster_[i] = best_c;
                local_counts[tid][best_c]++;
                for (int x = 0; x < d_; x++) local_sums[tid][best_c][x] += vec[x];
            }

            // 合并各线程的 counts/sums
            std::vector<int> counts(k_, 0);
            std::vector<std::vector<float>> sums(k_, std::vector<float>(d_, 0.0f));
            for (int t = 0; t < num_threads; t++) {
                for (int j = 0; j < k_; j++) {
                    counts[j] += local_counts[t][j];
                    for (int x = 0; x < d_; x++) sums[j][x] += local_sums[t][j][x];
                }
            }
            
            bool changed = false;
            for (int j = 0; j < k_; j++) {
                if (counts[j] > 0) {
                    float diff_sum = 0.0f;
                    for (int x = 0; x < d_; x++) {
                        float val = sums[j][x] / counts[j];
                        float diff = val - cluster_centers_[j][x];
                        diff_sum += diff * diff;
                        cluster_centers_[j][x] = val;
                    }
                    if (diff_sum > 1e-6) changed = true;
                }
            }
            if (!changed) break;
        }
        
        cluster_distances_.resize(k_, std::vector<float>(k_));
        for (int i = 0; i < k_; i++) {
            for (int j = i + 1; j < k_; j++) {
                float dist = 0.0f;
                #pragma omp simd reduction(+:dist)
                for (int x = 0; x < d_; x++) {
                    float diff = cluster_centers_[i][x] - cluster_centers_[j][x];
                    dist += diff * diff;
                }
                float d_val = std::sqrt(dist);
                cluster_distances_[i][j] = d_val;
                cluster_distances_[j][i] = d_val;
            }
        }
    }
    
    float distance(int i, int j, const float* vectors) const {
        if (!use_kmeans_) return direct_euclidean_distance(i, j, vectors);
        int ci = point_to_cluster_[i];
        int cj = point_to_cluster_[j];
        return (ci == cj) ? direct_euclidean_distance(i, j, vectors) : cluster_distances_[ci][cj];
    }
};

class KPH_DPC {
private:
    const std::vector<float>& node_weights_;
    std::shared_ptr<acsg::Graph<int32_t>> knn_graph_;
    const float* vectors_;
    int n_, d_;
    const KMeansDistanceCalculator* shared_kmeans_ = nullptr;
    KMeansDistanceCalculator local_kmeans_;
    
    std::vector<int> global_to_local_map_, local_to_global_map_;
    bool use_local_mapping_ = false;
    ThreadSafeRandom random_gen_;
    
public:
    KPH_DPC(const std::vector<float>& w, std::shared_ptr<acsg::Graph<int32_t>> g,
            const float* v, int n, int d, bool use_1000 = false)
        : node_weights_(w), knn_graph_(g), vectors_(v), n_(n), d_(d) {
        
        if (!knn_graph_) throw std::invalid_argument("KNN graph null");
        int sub_k = use_1000 ? std::min(1000, n/100) : std::min(512, n/100);
        
        local_kmeans_.build(v, n, d, sub_k, use_1000);
        shared_kmeans_ = &local_kmeans_;
    }

    KPH_DPC(const std::vector<float>& w, std::shared_ptr<acsg::Graph<int32_t>> g,
            const float* v, int n, int d, const KMeansDistanceCalculator* shared_calc)
        : node_weights_(w), knn_graph_(g), vectors_(v), n_(n), d_(d), shared_kmeans_(shared_calc) {
    }
    
    void set_local_mapping(const std::vector<int>& l2g) {
        use_local_mapping_ = true;
        local_to_global_map_ = l2g;
        n_ = l2g.size();
        global_to_local_map_.assign(node_weights_.size(), -1);
        for(size_t i=0; i<l2g.size(); ++i) {
            int g_idx = l2g[i];
            if(g_idx < (int)global_to_local_map_.size()) global_to_local_map_[g_idx] = i;
        }
    }
    
    DPCResult perform_kph_dpc(const KPHDPCConfig& config) {
        DPCResult result;
        result.densities.resize(n_);
        if (use_local_mapping_) {
            for(int i=0; i<n_; ++i) result.densities[i] = node_weights_[local_to_global_map_[i]];
        } else {
            result.densities = node_weights_;
        }
        
        auto sorted_idx = sort_by_density(result.densities);
        result.deltas = compute_deltas_hybrid(sorted_idx, config, result.densities);
        result.gammas = compute_gammas(result.densities, result.deltas, config);
        result.cluster_centers = select_cluster_centers(result.densities, result.deltas, result.gammas, sorted_idx, config);
        result.cluster_labels = assign_cluster_labels(result.cluster_centers, sorted_idx, result.densities);
        return result;
    }

private:
    std::vector<int> sort_by_density(const std::vector<float>& densities) {
        std::vector<int> idx(n_);
        std::iota(idx.begin(), idx.end(), 0);
        std::sort(idx.begin(), idx.end(), [&](int i, int j){ return densities[i] > densities[j]; });
        return idx;
    }
    
    std::vector<float> compute_deltas_hybrid(const std::vector<int>& sorted, const KPHDPCConfig& cfg, const std::vector<float>& dens) {
        (void)cfg;

        std::vector<float> deltas(n_, std::numeric_limits<float>::max());
        float max_dist = estimate_max_distance();

        // 密度最高的节点直接赋最大距离（无需计算）
        if(n_ > 0) deltas[sorted[0]] = max_dist;

        // 【并行化】每个节点的 delta 只读 dens/sorted/knn_graph，写各自独立的 deltas[u]
        // 节点间无写竞争，可安全并行；随机采样使用 thread_local 保证线程安全
        #pragma omp parallel for schedule(dynamic, 512)
        for(int rank = 1; rank < n_; ++rank) {
            int u = sorted[rank];
            int g_u = use_local_mapping_ ? local_to_global_map_[u] : u;

            float min_d = std::numeric_limits<float>::max();
            bool found = false;

            // 策略 A：KNN 图快速查找（最常命中，O(K) 且 cache 友好）
            if(g_u >= 0 && g_u < knn_graph_->N) {
                for(int k = 0; k < knn_graph_->K; ++k) {
                    int g_v = knn_graph_->at(g_u, k);
                    if(g_v < 0) continue;
                    int v = use_local_mapping_ ? global_to_local_map_[g_v] : g_v;
                    if(v != -1 && dens[v] > dens[u]) {
                        float d = compute_distance(u, v);
                        if(d < min_d) { min_d = d; found = true; }
                    }
                }
            }

            // 策略 B：随机采样兜底（KNN 图未命中时）
            if(!found) {
                auto& gen = random_gen_.get_local(); // thread_local，无竞争
                int samples = 1000;
                if(rank <= samples) {
                    for(int j = 0; j < rank; ++j) {
                        int cand = sorted[j];
                        if(dens[cand] > dens[u]) {
                            float d = compute_distance(u, cand);
                            if(d < min_d) min_d = d;
                        }
                    }
                } else {
                    std::uniform_int_distribution<int> dis(0, rank - 1);
                    for(int s = 0; s < samples; ++s) {
                        int cand = sorted[dis(gen)];
                        if(dens[cand] > dens[u]) {
                            float d = compute_distance(u, cand);
                            if(d < min_d) min_d = d;
                        }
                    }
                }
            }

            deltas[u] = (min_d == std::numeric_limits<float>::max()) ? max_dist : min_d;
        }
        return deltas;
    }
    
    std::vector<float> compute_gammas(const std::vector<float>& dens, const std::vector<float>& deltas, const KPHDPCConfig& cfg) {
        std::vector<float> gammas(n_);
        bool use_pow = (cfg.gamma_method == "power");
        for(int i=0; i<n_; ++i) {
            if(use_pow) gammas[i] = std::pow(dens[i], cfg.gamma_exponent) * deltas[i];
            else gammas[i] = dens[i] * deltas[i];
        }
        return gammas;
    }
    
    std::vector<int> select_cluster_centers(const std::vector<float>& dens, const std::vector<float>& deltas, 
                                            const std::vector<float>& gammas, const std::vector<int>& sorted, 
                                            const KPHDPCConfig& cfg) {
        (void)deltas; 
        
        std::vector<int> candidates;
        for(int idx : sorted) {
            if(dens[idx] >= cfg.min_density_threshold) candidates.push_back(idx);
        }
        if(candidates.empty()) candidates = sorted;
        
        std::sort(candidates.begin(), candidates.end(), [&](int i, int j){ return gammas[i] > gammas[j]; });
        
        int n_centers = std::min(cfg.target_centers, (int)candidates.size());
        n_centers = std::max(n_centers, std::min((int)candidates.size(), 2));
        
        std::vector<int> centers(candidates.begin(), candidates.begin() + n_centers);
        return centers;
    }
    
    std::vector<int> assign_cluster_labels(const std::vector<int>& centers, const std::vector<int>& sorted, const std::vector<float>& dens) {
        std::vector<int> labels(n_, -1);
        for(int i=0; i<(int)centers.size(); ++i) labels[centers[i]] = i;

        // DPC 标签传播是严格顺序依赖的（按密度降序，从高密度传向低密度）。
        // 两阶段拆分：
        //   阶段1（并行）：只做"找最近高密度邻居"的距离计算，结果写入独立的 candidates[]
        //                  candidates[rank] 是 rank 号节点的候选邻居（局部坐标）
        //                  阶段1 只读 dens[]（只读，无竞争），只写 candidates[rank]（rank唯一，无竞争）
        //   阶段2（串行）：按 rank 顺序传播标签
        //                  正确性保证：cand.best_neighbor = v，dens[v] > dens[u]
        //                  → rank(v) < rank(u) → 阶段2 处理 u 时 v 已被处理 → labels[v] 已赋值 ✅

        struct Candidate { int best_neighbor; bool from_knn; };
        std::vector<Candidate> candidates(n_, {-1, false});

        #pragma omp parallel for schedule(dynamic, 512)
        for(int rank = 1; rank < n_; ++rank) {
            int u = sorted[rank];
            if(labels[u] != -1) continue;  // 已是聚类中心，跳过（只读，无竞争）

            int g_u = use_local_mapping_ ? local_to_global_map_[u] : u;
            float min_d = std::numeric_limits<float>::max();
            int best_neighbor = -1;

            // 策略 A：KNN 图中找密度更高的邻居
            if(g_u >= 0 && g_u < knn_graph_->N) {
                for(int k=0; k<knn_graph_->K; ++k) {
                    int g_v = knn_graph_->at(g_u, k);
                    if(g_v < 0) continue;
                    int v = use_local_mapping_ ? global_to_local_map_[g_v] : g_v;
                    // 条件：v 有效 + 密度严格大于 u（保证 rank(v) < rank(u)，阶段2 传播有序）
                    if(v >= 0 && v < n_ && dens[v] > dens[u]) {
                        float d = compute_distance(u, v);
                        if(d < min_d) { min_d = d; best_neighbor = v; }
                    }
                }
            }

            if(best_neighbor >= 0) {
                candidates[rank] = {best_neighbor, true};
            } else {
                // 策略 B fallback：找最近的聚类中心，直接记录 label 值（centers 下标 = label）
                int best_c = 0;
                float min_c_d = std::numeric_limits<float>::max();
                for(int i=0; i<(int)centers.size(); ++i) {
                    float d = compute_distance(u, centers[i]);
                    if(d < min_c_d) { min_c_d = d; best_c = i; }
                }
                candidates[rank] = {best_c, false};
            }
        }

        // 阶段2：串行按密度降序传播标签
        // 正确性：处理 rank r 时，所有 rank < r（密度更高）的节点已全部标注完毕
        for(int rank = 1; rank < n_; ++rank) {
            int u = sorted[rank];
            if(labels[u] != -1) continue;  // 聚类中心已初始化，跳过
            const auto& cand = candidates[rank];
            if(cand.from_knn) {
                // best_neighbor = v（局部坐标），rank(v) < rank(u) → labels[v] 已赋值
                int lbl = labels[cand.best_neighbor];
                labels[u] = (lbl >= 0) ? lbl : 0;  // 正常情况 lbl >= 0，0 仅为安全兜底
            } else {
                // fallback：cand.best_neighbor 就是 centers[] 下标，即 label 值
                labels[u] = cand.best_neighbor;
            }
        }
        return labels;
    }
    
    float estimate_max_distance() const {
        int samples = std::min(1000, n_);
        float max_d = 0;
        // 仅 1000 次采样，线程启动开销远大于收益，保持串行
        ThreadSafeRandom rnd;
        std::uniform_int_distribution<> dis(0, n_-1);
        for(int i=0; i<samples; ++i) {
            float d = compute_distance(dis(rnd.get_local()), dis(rnd.get_local()));
            if(d > max_d) max_d = d;
        }
        return max_d * 1.1f;
    }
    
    float compute_distance(int u, int v) const {
        int g_u = use_local_mapping_ ? local_to_global_map_[u] : u;
        int g_v = use_local_mapping_ ? local_to_global_map_[v] : v;
        return shared_kmeans_->distance(g_u, g_v, vectors_);
    }
};

void print_cluster_size_stats(const DPCResult& result, const std::string& layer_name) {
    std::vector<int> sizes(result.cluster_centers.size(), 0);
    int unassigned = 0;
    for(int lbl : result.cluster_labels) {
        if(lbl >= 0 && lbl < (int)sizes.size()) sizes[lbl]++;
        else unassigned++;
    }
    std::cout << "\n=== " << layer_name << " Stats ===" << std::endl;
    std::cout << "Centers: " << sizes.size() << ", Unassigned: " << unassigned << std::endl;
    
    int max_s = 0;
    if (!sizes.empty()) {
        max_s = *std::max_element(sizes.begin(), sizes.end());
    }
    std::cout << "Max cluster size: " << max_s << std::endl;
}

void print_center_weights_and_rankings(const std::vector<int>& centers, const std::vector<float>& all_weights) {
    if (centers.empty() || all_weights.empty()) {
        std::cout << "No centers or weights to display." << std::endl;
        return;
    }

    std::vector<float> sorted_weights = all_weights;
    std::sort(sorted_weights.begin(), sorted_weights.end(), std::greater<float>());
    size_t total_points = sorted_weights.size();

    std::cout << "\n==========================================================================" << std::endl;
    std::cout << "📊 Cluster Centers Detail Report (Total Centers: " << centers.size() << ")" << std::endl;
    std::cout << "   Format: [ID : Weight (Top X%)]" << std::endl;
    std::cout << "==========================================================================" << std::endl;

    int count = 0;
    for (int center_id : centers) {
        if (center_id < 0 || center_id >= (int)all_weights.size()) continue;

        float w = all_weights[center_id];
        
        auto it = std::lower_bound(sorted_weights.begin(), sorted_weights.end(), w, std::greater<float>());
        int rank = std::distance(sorted_weights.begin(), it);
        
        float top_percent = (static_cast<float>(rank) / total_points) * 100.0f;

        std::cout << "[" << std::setw(7) << center_id << " : " 
                  << std::fixed << std::setprecision(4) << w 
                  << " (" << std::setw(5) << std::setprecision(2) << top_percent << "%)]  ";

        if (++count % 4 == 0) std::cout << std::endl; 
    }
    
    if (count % 4 != 0) std::cout << std::endl;
    std::cout << "==========================================================================\n" << std::endl;
}

// 辅助结构：用于 DASP 选择候选点
struct SubPeakCandidate {
    int id;
    float delta;
    float gamma;
};

class TwoLayerHierarchicalDPC {
private:
    acsg::IndexACSG& index_;
    KMeansDistanceCalculator shared_kmeans_;
    bool kmeans_built_ = false;
    
public:
    TwoLayerHierarchicalDPC(acsg::IndexACSG& index) : index_(index) {}
    
    void init_kmeans() {
        if(kmeans_built_) return;
        auto st = dynamic_cast<faiss::IndexFlat*>(index_.storage);
        const float* vectors = st->get_xb();
        shared_kmeans_.build(vectors, index_.ntotal, index_.d, 0, false);
        kmeans_built_ = true;
        std::cout << "Global K-Means index built." << std::endl;
    }
    
    TwoLayerClustering perform_two_layer_clustering() {
        init_kmeans();
        TwoLayerClustering res;
        std::cout << "\n=== Phase 1: Top Layer ===" << std::endl;
        res.top_layer = perform_top_layer();
        print_cluster_size_stats(res.top_layer, "Top Layer");
        
        std::cout << "\n=== Phase 2: Bottom Layer ===" << std::endl;
        res.bottom_layer = perform_bottom_layer(res.top_layer);
        print_cluster_size_stats(res.bottom_layer, "Bottom Layer");
        
        build_mappings(res);
        
        std::cout << "\n=== Two-Layer Clustering Complete ===" << std::endl;
        print_hierarchy_summary(res); 
        
        return res;
    }

private:
    void get_data(std::vector<float>& w, std::shared_ptr<acsg::Graph<int32_t>>& g, std::vector<float>& v) {
        w = index_.get_acpg_weights();
        g = index_.get_acpg_graph();
        auto st = dynamic_cast<faiss::IndexFlat*>(index_.storage);
        size_t sz = index_.ntotal * index_.d;
        v.resize(sz);
        const float* src = st->get_xb();
        #pragma omp parallel for schedule(static)
        for(size_t i=0; i<sz; ++i) v[i] = src[i];
    }
    
    DPCResult perform_top_layer() {
        std::vector<float> w, v;
        std::shared_ptr<acsg::Graph<int32_t>> g;
        get_data(w, g, v);
        KPHDPCConfig cfg(10, index_.nsg_R, 5, 32, "global", "original");
        KPH_DPC dpc(w, g, v.data(), index_.ntotal, index_.d, &shared_kmeans_);
        return dpc.perform_kph_dpc(cfg);
    }

    // === 新增：DASP (Density-Adaptive Sub-peak Promotion) 方法 ===
    void refine_giant_clusters(std::vector<int>& final_centers, 
                               const std::vector<int>& all_labels,
                               const std::vector<float>& densities,
                               const float* vectors) {
        
        std::cout << ">>> Running DASP (Density-Adaptive Sub-peak Promotion) [Optimized]..." << std::endl;
        
        // 1. 建立簇到成员的反向索引
        std::map<int, std::vector<int>> cluster_map;
        for (int i = 0; i < (int)all_labels.size(); ++i) {
            int lbl = all_labels[i];
            if (lbl != -1) {
                cluster_map[lbl].push_back(i);
            }
        }

        int ntotal = index_.ntotal;
        int threshold = ntotal / 50; // 2% 阈值
        int added_centers_count = 0;
        std::vector<int> new_global_centers;

        // 获取 KNN 图用于加速
        auto knn_graph_ptr = index_.get_acpg_graph();

        // 遍历所有簇
        for (auto& entry : cluster_map) {
            int old_center_idx = entry.first;
            std::vector<int>& members = entry.second;
            int m = members.size();

            // 只处理超大簇
            if (m > threshold) {
                int target_parts = (int)((long long)m * 50 / ntotal);
                if (target_parts <= 1) continue;
                
                int num_to_add = target_parts - 1;
                
                std::cout << "[DASP] Giant Cluster (ID: " << final_centers[old_center_idx] 
                          << ", Size: " << m << ") -> Adding " << num_to_add << " routing nodes." << std::endl;

                // 1. 按密度降序排序成员
                std::sort(members.begin(), members.end(), [&](int a, int b) {
                    return densities[a] > densities[b];
                });

                // 2. 计算内部 Delta (并行 + 近似优化)
                std::vector<float> local_deltas(m);
                local_deltas[0] = std::numeric_limits<float>::max(); // 簇中心 (局部密度最大)

                #pragma omp parallel for schedule(dynamic, 100)
                for (int i = 1; i < m; ++i) {
                    int u = members[i];
                    float min_d = std::numeric_limits<float>::max();
                    
                    // 策略 A: 查 KNN 图 (最快、最准确)
                    // 在 u 的邻居中找 "同簇" 且 "密度更高" 的点
                    if (knn_graph_ptr) {
                        for (int k = 0; k < knn_graph_ptr->K; ++k) {
                            int v_global = knn_graph_ptr->at(u, k);
                            if (v_global < 0) continue;
                            
                            // 检查条件：同簇 + 密度更高
                            if (all_labels[v_global] == old_center_idx && densities[v_global] > densities[u]) {
                                float d = shared_kmeans_.distance(u, v_global, vectors);
                                if (d < min_d) min_d = d;
                            }
                        }
                    }

                    // 策略 B: 随机采样 (兜底，防止 KNN 图稀疏导致 disconnect)
                    // 从比 u 密度高的点 (members[0...i-1]) 中随机选一些计算
                    int samples = 32; 
                    if (i <= samples) {
                        // 候选很少，全算
                        for (int j = 0; j < i; ++j) {
                            float d = shared_kmeans_.distance(u, members[j], vectors);
                            if (d < min_d) min_d = d;
                        }
                    } else {
                        // 候选很多，随机采
                        // 使用 thread_local 保证并行安全
                        static thread_local std::mt19937 rng(std::random_device{}());
                        std::uniform_int_distribution<int> dist(0, i - 1);
                        
                        for (int s = 0; s < samples; ++s) {
                            int v = members[dist(rng)];
                            float d = shared_kmeans_.distance(u, v, vectors);
                            if (d < min_d) min_d = d;
                        }
                    }

                    // 策略 C: 绝对保底
                    // 如果还找不到 (极罕见)，直接计算到簇中心 members[0] 的距离
                    if (min_d == std::numeric_limits<float>::max()) {
                         min_d = shared_kmeans_.distance(u, members[0], vectors);
                    }

                    local_deltas[i] = min_d;
                }

                // 统计 sum_delta (在并行循环外累加)
                double sum_delta = 0.0;
                for(int i = 1; i < m; ++i) sum_delta += local_deltas[i];

                // 3. 筛选候选点
                float avg_delta = (float)(sum_delta / (m - 1));
                
                std::vector<SubPeakCandidate> candidates;
                for (int i = 1; i < m; ++i) {
                    if (local_deltas[i] > avg_delta) {
                        float gamma = densities[members[i]] * local_deltas[i];
                        candidates.push_back({members[i], local_deltas[i], gamma});
                    }
                }

                // 4. 按 Gamma 降序排序
                std::sort(candidates.begin(), candidates.end(), [](const SubPeakCandidate& a, const SubPeakCandidate& b) {
                    return a.gamma > b.gamma;
                });

                // 5. 选出 Top K
                for (int i = 0; i < std::min((int)candidates.size(), num_to_add); ++i) {
                    new_global_centers.push_back(candidates[i].id);
                }
                
                added_centers_count += std::min((int)candidates.size(), num_to_add);
            }
        }

        if (added_centers_count > 0) {
            final_centers.insert(final_centers.end(), new_global_centers.begin(), new_global_centers.end());
        }
        std::cout << "[DASP] Finished. Added " << added_centers_count << " new routing centers." << std::endl;
    }
    
    DPCResult perform_bottom_layer(const DPCResult& top) {
        std::vector<float> w, v;
        std::shared_ptr<acsg::Graph<int32_t>> g;
        get_data(w, g, v);
        
        std::vector<float> sorted_w = w;
        std::sort(sorted_w.begin(), sorted_w.end(), std::greater<float>());
        int top50_idx = std::min((int)(sorted_w.size()*0.1), (int)sorted_w.size()-1);
        float dens_thresh = sorted_w[top50_idx];
        std::cout << "Density Threshold (Top 10%): " << dens_thresh << std::endl;
        
        std::vector<std::vector<int>> regions(top.cluster_centers.size());
        for(int i=0; i<index_.ntotal; ++i) {
            int r = top.cluster_labels[i];
            if(r >= 0 && r < (int)regions.size()) regions[r].push_back(i);
        }
        
        std::vector<int> all_centers;
        std::vector<int> all_labels(index_.ntotal, -1);
        
        // ======================= MODIFICATION START =======================
        // 动态计算目标中心数量
        // 规则：默认目标 1200 个，但增加硬性上限 N / 500
        // 对于 100K 数据集：limit = 200 -> global_target = 200
        // 对于 1M 数据集：  limit = 2000 -> global_target = 1200 (保持原状)
        int max_centers_limit = std::max(50, (int)(index_.ntotal / 500)); 
        int global_target = std::min(800, max_centers_limit);
        
        std::cout << ">>> [Config] Global Target Centers: " << global_target 
                  << " (Constraint: N/500 = " << (index_.ntotal/500) << ")" << std::endl;
        // ======================= MODIFICATION END =========================

        // 外层并行：32 个 region 分配给 8 核（粒度大、无依赖，并行效率最高）
        // 内层 compute_deltas_hybrid / assign_cluster_labels 已加 OMP，但 nested=0 时退化串行
        // 这与原始代码行为一致，且外层并行是主要加速来源
        std::mutex mtx;
        #pragma omp parallel for schedule(dynamic, 1)
        for(int r=0; r<(int)regions.size(); ++r) {
            const auto& pts = regions[r];
            if(pts.size() < 100) continue;
            
            float ratio = (float)pts.size() / index_.ntotal;
            
            // 使用动态计算的 global_target
            int target = std::max(2, (int)(global_target * ratio));
            
            KPHDPCConfig cfg(3, index_.nsg_R, 2, target, "local", "power");
            cfg.gamma_exponent = 1.5f;
            cfg.min_density_threshold = dens_thresh;
            
            KPH_DPC dpc(w, g, v.data(), index_.ntotal, index_.d, &shared_kmeans_);
            dpc.set_local_mapping(pts);
            auto res = dpc.perform_kph_dpc(cfg);
            
            std::lock_guard<std::mutex> lock(mtx);
            int offset = all_centers.size();
            for(int c : res.cluster_centers) all_centers.push_back(pts[c]);
            for(size_t i=0; i<pts.size(); ++i) {
                if(res.cluster_labels[i] != -1) 
                    all_labels[pts[i]] = res.cluster_labels[i] + offset;
            }
        }
        
        // 过滤过小的簇 (没必要过滤了)
        int min_size = 0; 
        std::cout << "Filtering clusters size < " << min_size << std::endl;
        
        std::vector<int> counts(all_centers.size(), 0);
        for(int l : all_labels) if(l >= 0) counts[l]++;
        
        std::vector<int> final_centers;
        std::vector<int> map_old_new(all_centers.size(), -1);
        int valid_cnt = 0;
        for(size_t i=0; i<all_centers.size(); ++i) {
            if(counts[i] > min_size) {
                map_old_new[i] = valid_cnt++;
                final_centers.push_back(all_centers[i]);
            }
        }
        
        int filtered = 0;
        #pragma omp parallel for reduction(+:filtered)
        for(int i=0; i<index_.ntotal; ++i) {
            if(all_labels[i] != -1) {
                int new_lbl = map_old_new[all_labels[i]];
                all_labels[i] = new_lbl;
                if(new_lbl == -1) filtered++;
            }
        }
        std::cout << "Final centers before refinement: " << final_centers.size() << ", Filtered points: " << filtered << std::endl;

        // === 插入 DASP 优化 (无 Re-assignment) ===
        auto st = dynamic_cast<faiss::IndexFlat*>(index_.storage);
        const float* vectors_ptr = st->get_xb();
        
        refine_giant_clusters(final_centers, all_labels, w, vectors_ptr);

        DPCResult res;
        res.cluster_centers = final_centers;
        res.cluster_labels = all_labels;
        res.densities = w;
        return res;
    }
    
    void build_mappings(TwoLayerClustering& res) {
        std::cout << "Building mappings (parallel with unordered_set dedup)..." << std::endl;
        int n_top = res.top_layer.cluster_centers.size();
        res.region_to_fine.resize(n_top);

        // 并行阶段：每个 top region 用 unordered_set 去重，然后转成 vector
        // 先按 top label 收集对应的 fine label 集合
        std::vector<std::unordered_set<int>> region_fine_sets(n_top);
        std::vector<std::mutex> region_mtx(n_top);

        #pragma omp parallel for schedule(static)
        for(int i = 0; i < index_.ntotal; ++i) {
            int r = res.top_layer.cluster_labels[i];
            int f = res.bottom_layer.cluster_labels[i];
            if(r >= 0 && r < n_top && f >= 0) {
                std::lock_guard<std::mutex> lk(region_mtx[r]);
                region_fine_sets[r].insert(f);
            }
        }

        // 转成 vector
        #pragma omp parallel for schedule(static)
        for(int r = 0; r < n_top; ++r) {
            res.region_to_fine[r].assign(region_fine_sets[r].begin(), region_fine_sets[r].end());
        }
    }
    
    void print_hierarchy_summary(const TwoLayerClustering& result) {
        std::cout << "\n===== Two-Layer Clustering Summary =====" << std::endl;
        std::cout << "Top Layer (Macro Regions): " 
                << result.top_layer.cluster_centers.size() << " centers" << std::endl;
        std::cout << "Bottom Layer (Fine Clusters): " 
                << result.bottom_layer.cluster_centers.size() << " centers" << std::endl;
        
        int avg_fine_per_region = 0;
        int regions_with_fine = 0;
        for (const auto& fines : result.region_to_fine) {
            if (!fines.empty()) {
                avg_fine_per_region += fines.size();
                regions_with_fine++;
            }
        }
        if (regions_with_fine > 0) {
            avg_fine_per_region /= regions_with_fine;
        }
        
        std::cout << "Average fine clusters per region: " << avg_fine_per_region << std::endl;
        std::cout << "Regions with fine clusters: " << regions_with_fine << std::endl;

        if (result.bottom_layer.cluster_centers.empty()) {
            std::cout << "===========================================" << std::endl;
            return;
        }

        std::vector<int> cluster_sizes(result.bottom_layer.cluster_centers.size(), 0);
        
        for (int label : result.bottom_layer.cluster_labels) {
            if (label >= 0 && label < (int)cluster_sizes.size()) {
                cluster_sizes[label]++;
            }
        }

        int cnt_0_10 = 0;
        int cnt_10_50 = 0;
        int cnt_50_100 = 0;
        int cnt_100_200 = 0;
        int cnt_200_500 = 0;
        int cnt_500_plus = 0;

        for (int size : cluster_sizes) {
            if (size <= 10) {
                cnt_0_10++;
            } else if (size <= 50) {
                cnt_10_50++;
            } else if (size <= 100) {
                cnt_50_100++;
            } else if (size <= 200) {
                cnt_100_200++;
            } else if (size <= 500) {
                cnt_200_500++;
            } else {
                cnt_500_plus++;
            }
        }

        std::cout << "\n--- Bottom Layer Cluster Size Distribution ---" << std::endl;
        std::cout << "  0   - 10 : " << cnt_0_10 << " clusters" << std::endl;
        std::cout << "  10  - 50 : " << cnt_10_50 << " clusters" << std::endl;
        std::cout << "  50  - 100: " << cnt_50_100 << " clusters" << std::endl;
        std::cout << "  100 - 200: " << cnt_100_200 << " clusters" << std::endl;
        std::cout << "  200 - 500: " << cnt_200_500 << " clusters" << std::endl;
        std::cout << "  > 500    : " << cnt_500_plus << " clusters" << std::endl;
        std::cout << "===========================================" << std::endl;
    }
};

int main(int argc, char **argv) {
    std::cout << "Starting KPH-DPC Two-Layer Hierarchical Clustering" << std::endl;
    
        omp_set_dynamic(0);
        omp_set_nested(0);  // 禁止嵌套并行，避免外层 region 并行 × 内层 delta 并行 = 线程过度订阅
    
    try {
        argparse::ArgumentParser program("kph_dpc");
        program.add_argument("--acpg_file").required();
        program.add_argument("--output_file").required();
        program.add_argument("--num_threads").default_value(0).scan<'i', int>();
        program.parse_args(argc, argv);
        
        std::string acpg = program.get<std::string>("--acpg_file");
        std::string out = program.get<std::string>("--output_file");
        int nth = program.get<int>("--num_threads");
        if(nth > 0) omp_set_num_threads(nth);
        
        auto index = std::make_unique<acsg::IndexACSG>();
        index->loadACPG(acpg.c_str());
        
        TwoLayerHierarchicalDPC dpc(*index);
        auto res = dpc.perform_two_layer_clustering();
        
        ClusterHierarchy h;
        extract_cluster_centers_from_dpc(res, h);

        print_center_weights_and_rankings(h.bottom_centers, h.densities);

        std::ofstream f(out);
        nlohmann::json j;
        j["top_layer_centers"] = res.top_layer.cluster_centers.size();
        j["bottom_layer_centers"] = res.bottom_layer.cluster_centers.size();
        j["region_to_fine"] = res.region_to_fine;
        j["top_centers"] = h.top_centers;
        j["bottom_centers"] = h.bottom_centers;
        
        std::vector<float> ds;
        int sz = std::min(1000, (int)h.densities.size());
        ds.assign(h.densities.begin(), h.densities.begin()+sz);
        j["density_sample"] = ds;
        j["total_densities"] = h.densities.size();
        
        f << j.dump(4);
        std::cout << "Done." << std::endl;
    } catch(const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}
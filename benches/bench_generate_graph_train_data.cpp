/**
 * @file bench_generate_graph_train_data.cpp
 * @brief 挖掘 "Golden Edges"：基于 Top-K 召回挖掘纠偏路径
 * [修复版] 增加了对 DPC 原始 JSON 格式 (top/bottom centers) 的兼容支持
 */

#include <iostream>
#include <fstream>
#include <vector>
#include <algorithm>
#include <random>
#include <omp.h>
#include <cmath>
#include <mutex>
#include <queue>
#include <set> // [新增] 用于去重
#include <argparse/argparse.hpp>
#include <nlohmann/json.hpp>
#include <benches/datasets/DataLoader.hpp>

using json = nlohmann::json;

// L2 距离计算
inline float dist_l2(const float* a, const float* b, int d) {
    float dist = 0;
    for (int i = 0; i < d; ++i) {
        float diff = a[i] - b[i];
        dist += diff * diff;
    }
    return dist;
}

int main(int argc, char** argv) {
    argparse::ArgumentParser program("gen_graph_data");
    program.add_argument("--dataset").required();
    program.add_argument("--cluster_file").required().help("entry_points.json");
    program.add_argument("--output_file").required().help("edges_train.txt");
    program.add_argument("--query_type").default_value(std::string("learn")); 

    try {
        program.parse_args(argc, argv);
    } catch (const std::runtime_error& err) {
        std::cerr << err.what() << std::endl;
        std::cerr << program;
        return 1;
    }

    std::string dataset = program.get<std::string>("--dataset");
    std::string cluster_file = program.get<std::string>("--cluster_file");
    std::string output_file = program.get<std::string>("--output_file");
    std::string query_type = program.get<std::string>("--query_type");

    // 1. 加载聚类中心向量
    std::cout << ">>> Loading Cluster Centers..." << std::endl;
    DataLoader loader(dataset);
    auto [nb, xb] = loader.load_base(); 
    int dim = loader.dim();

    std::ifstream f_cluster(cluster_file);
    if (!f_cluster.is_open()) {
        std::cerr << "❌ Error: Cannot open cluster file: " << cluster_file << std::endl;
        return 1;
    }
    json j_cluster; 
    f_cluster >> j_cluster;

    // [修复逻辑开始] --------------------------------------------------
    std::vector<int> center_ids;
    // 优先读取 combined_centers
    if (j_cluster.contains("combined_centers") && !j_cluster["combined_centers"].is_null()) {
        center_ids = j_cluster["combined_centers"].get<std::vector<int>>();
    } 
    // 如果没有，尝试合并 top/bottom centers
    else if (j_cluster.contains("top_centers")) {
        std::cout << "⚠️  'combined_centers' missing, merging top/bottom centers..." << std::endl;
        std::vector<int> top = j_cluster["top_centers"].get<std::vector<int>>();
        std::vector<int> bottom = j_cluster["bottom_centers"].get<std::vector<int>>();
        std::set<int> unique_hubs(top.begin(), top.end());
        unique_hubs.insert(bottom.begin(), bottom.end());
        center_ids.assign(unique_hubs.begin(), unique_hubs.end());
    } else {
        std::cerr << "❌ Error: Invalid cluster file format (missing combined_centers or top_centers)!" << std::endl;
        return 1;
    }
    // [修复逻辑结束] --------------------------------------------------

    int num_centers = center_ids.size();
    std::cout << "✅ Loaded " << num_centers << " centers." << std::endl;
    
    // 提取中心向量
    std::vector<float> center_vecs(num_centers * dim);
    for(int i=0; i<num_centers; ++i) {
        if (center_ids[i] >= nb) {
            std::cerr << "❌ Error: Center ID " << center_ids[i] << " exceeds base size " << nb << std::endl;
            return 1;
        }
        const float* src = xb.get() + center_ids[i] * dim;
        std::copy(src, src + dim, center_vecs.data() + i * dim);
    }

    // 2. 加载查询
    std::cout << ">>> Loading Queries (" << query_type << ")..." << std::endl;
    auto [nq, xq] = loader.load_query(query_type);
    
    // 3. 挖掘逻辑
    std::cout << ">>> Mining Golden Edges (Hard Positives: Neighbor -> Best)..." << std::endl;
    std::vector<std::pair<int, int>> positive_edges;
    std::mutex mtx;

    // 挖掘参数
    int top_k_scan = 10; // 扫描每个查询的前 10 个最近中心

    #pragma omp parallel for
    for (size_t i = 0; i < nq; ++i) {
        const float* q = xq.get() + i * dim;

        // 维护 Top-K (大顶堆，保留最小的K个)
        std::priority_queue<std::pair<float, int>> top_candidates;

        for (int c = 0; c < num_centers; ++c) {
            float d = dist_l2(q, center_vecs.data() + c * dim, dim);
            if (top_candidates.size() < (size_t)top_k_scan) {
                top_candidates.push({d, c});
            } else if (d < top_candidates.top().first) {
                top_candidates.pop();
                top_candidates.push({d, c});
            }
        }

        // 排序：距离从小到大
        std::vector<std::pair<float, int>> sorted_centers;
        while(!top_candidates.empty()) {
            sorted_centers.push_back(top_candidates.top());
            top_candidates.pop();
        }
        std::reverse(sorted_centers.begin(), sorted_centers.end());

        // Best Center 是 sorted_centers[0]
        if (sorted_centers.empty()) continue;
        int best_center = sorted_centers[0].second;

        // [核心改进]
        // 建立从 "次优节点" (第2名, 第3名...) 到 "最优节点" (第1名) 的边
        std::lock_guard<std::mutex> lock(mtx);
        for (size_t k = 1; k < sorted_centers.size(); ++k) {
            int neighbor = sorted_centers[k].second;
            // 只有当距离确实有差异时才添加（避免重复中心）
            if (neighbor != best_center) {
                positive_edges.push_back({neighbor, best_center});
            }
        }
    }

    // 4. 保存
    std::ofstream out(output_file);
    out << dim << " " << num_centers << "\n";
    // 保存向量
    for (int i = 0; i < num_centers; ++i) {
        for (int j = 0; j < dim; ++j) {
            out << center_vecs[i * dim + j] << (j == dim - 1 ? "" : " ");
        }
        out << "\n";
    }
    // 保存边
    for (const auto& edge : positive_edges) {
        out << edge.first << " " << edge.second << "\n";
    }
    out.close();
    std::cout << "✅ Generated " << positive_edges.size() << " edges (Hard Positives)." << std::endl;
    return 0;
}
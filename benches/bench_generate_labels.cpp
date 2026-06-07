/**
 * @file bench_generate_labels.cpp
 * @brief 拓扑感知训练标签生成器 (Oracle Simulation)
 * 核心功能: 暴力模拟图搜索，为每个查询找到真实搜索代价 (NDC) 最小的最佳入口点 (Hub)，作为神经网络训练的真值标签。
 * * * 更新特性:
 * - [关键修复] 兼容 top_centers/bottom_centers 的 JSON 格式
 * - 支持自定义查询类型选择 (--query_type)
 * - 支持限制查询处理数量 (--limit) 以加速流程
 * - 线程安全的并行执行
 */

#include <iostream>
#include <fstream>
#include <vector>
#include <limits>
#include <algorithm>
#include <omp.h>
#include <chrono>
#include <atomic>
#include <mutex>
#include <set> // [新增] 用于去重
#include <unistd.h> 

#include <argparse/argparse.hpp>
#include <nlohmann/json.hpp>
#include <benches/datasets/DataLoader.hpp>
#include <ACSG/IndexACSG.h>
#include <faiss/utils/distances.h>

using json = nlohmann::json;

/**
 * @brief 执行从特定起点出发的贪婪图搜索，判断能否找到 Ground Truth (GT)。
 */
std::pair<bool, int> probe_search(
    const acsg::Graph<int32_t>& graph,
    faiss::DistanceComputer& dis,
    int start_node,
    int gt_node, 
    int search_L,
    faiss::VisitedTable& vt) 
{
    int ndc = 0; 
    std::vector<std::pair<float, int>> pool;
    pool.reserve(search_L * 2);
    
    if (!vt.get(start_node)) {
        vt.set(start_node);
        float dist = dis(start_node);
        ndc++;
        pool.push_back({dist, start_node});
    } else {
        return {false, 999999};
    }

    int cursor = 0;
    while (cursor < (int)pool.size()) {
        if (cursor >= search_L) break;
        
        int u = pool[cursor].second;
        float dist_u = pool[cursor].first;
        
        if (pool.size() >= (size_t)search_L && dist_u > pool[search_L-1].first) break;
        
        cursor++;

        for (int i = 0; i < graph.K; ++i) {
            int v = graph.at(u, i);
            if (v < 0 || vt.get(v)) continue;
            
            vt.set(v);
            float dist_v = dis(v);
            ndc++;
            pool.push_back({dist_v, v});
        }
        
        std::sort(pool.begin(), pool.end());
        if (pool.size() > (size_t)search_L) pool.resize(search_L);
    }

    bool success = false;
    if (!pool.empty() && pool[0].second == gt_node) {
        success = true;
    }
    
    return {success, ndc};
}

int main(int argc, char** argv) {
    argparse::ArgumentParser program("generate_labels");
    program.add_argument("--dataset").required().help("数据集名称");
    program.add_argument("--index_file").required().help("NSG 索引路径");
    program.add_argument("--cluster_file").required().help("聚类中心路径");
    program.add_argument("--output_file").required().help("输出路径 (.ivecs)");
    program.add_argument("--L").default_value(50).scan<'i', int>().help("搜索深度");
    program.add_argument("--query_type").default_value(std::string("drl_train")).help("DataLoader 键值");
    program.add_argument("--limit").default_value(0).scan<'i', int>().help("处理数量限制");

    try {
        program.parse_args(argc, argv);
    } catch (const std::runtime_error& err) {
        std::cerr << err.what() << std::endl;
        std::cerr << program;
        return 1;
    }

    std::string dataset = program.get<std::string>("--dataset");
    std::string index_file = program.get<std::string>("--index_file");
    std::string cluster_file = program.get<std::string>("--cluster_file");
    std::string output_file = program.get<std::string>("--output_file");
    int L = program.get<int>("--L");
    std::string query_type = program.get<std::string>("--query_type");
    int limit = program.get<int>("--limit");

    // 2. 加载索引
    std::cout << ">>> 正在加载索引: " << index_file << std::endl;
    auto index = std::make_unique<acsg::IndexACSGFlat>();
    if (access(index_file.c_str(), F_OK) == -1) {
        std::cerr << "❌ 错误: 找不到索引文件: " << index_file << std::endl;
        return 1;
    }
    index->loadACPG(index_file.c_str());
    std::cout << "    索引已加载. 维度: " << index->d << ", 总向量数: " << index->ntotal << std::endl;

    // 3. 加载聚类中心 (Hubs) - [关键修复部分]
    std::cout << ">>> 正在加载聚类中心: " << cluster_file << std::endl;
    std::ifstream f_cluster(cluster_file);
    if (!f_cluster.is_open()) {
        std::cerr << "❌ 错误: 找不到聚类文件!" << std::endl;
        return 1;
    }
    json j_cluster; 
    f_cluster >> j_cluster;
    
    std::vector<int> hubs;
    // 兼容逻辑: 优先读取 combined_centers，如果为 null 则读取 top/bottom 并合并
    if (j_cluster.contains("combined_centers") && !j_cluster["combined_centers"].is_null()) {
        hubs = j_cluster["combined_centers"].get<std::vector<int>>();
    } else if (j_cluster.contains("top_centers")) {
        std::cout << "    ⚠️ 'combined_centers' 未找到或为空，尝试合并 top/bottom centers..." << std::endl;
        std::vector<int> top = j_cluster["top_centers"].get<std::vector<int>>();
        std::vector<int> bottom = j_cluster["bottom_centers"].get<std::vector<int>>();
        std::set<int> unique_hubs(top.begin(), top.end());
        unique_hubs.insert(bottom.begin(), bottom.end());
        hubs.assign(unique_hubs.begin(), unique_hubs.end());
    } else {
        std::cerr << "❌ JSON 错误: 找不到有效的中心点数据 (combined_centers 或 top_centers)!" << std::endl;
        return 1;
    }
    
    // 确保 hubs 有序（可选，但推荐）
    std::sort(hubs.begin(), hubs.end());
    std::cout << "    共加载 " << hubs.size() << " 个 Hubs." << std::endl;

    // 4. 加载查询数据
    std::cout << ">>> 正在加载查询数据 (类型: " << query_type << ")..." << std::endl;
    DataLoader loader(dataset);
    auto [nq_total, xq] = loader.load_query(query_type); 
    auto [k_gt, gt] = loader.load_gt(query_type); 

    if (nq_total == 0) {
        std::cerr << "❌ 错误: 未加载到任何查询!" << std::endl;
        return 1;
    }
    std::cout << "    加载了 " << nq_total << " 条查询." << std::endl;

    // 5. 应用数量限制
    int nq = (int)nq_total;
    if (limit > 0 && limit < nq) {
        std::cout << "⚠️  已启用数量限制: 仅处理前 " << limit << " 条查询" << std::endl;
        nq = limit;
    }

    // 6. 开始 Oracle 模拟
    std::cout << ">>> 开始 Oracle 模拟..." << std::endl;
    
    struct Label { int best_hub_idx; int min_ndc; };
    std::vector<Label> labels(nq);
    std::atomic<int> processed{0};
    std::atomic<int> success_count{0};
    
    auto start_time = std::chrono::high_resolution_clock::now();

    #pragma omp parallel for schedule(dynamic)
    for (int i = 0; i < nq; ++i) {
        const float* q = xq.get() + i * index->d;
        long gt_node = gt[i * k_gt]; 
        
        auto dis = acsg::storage_distance_computer(index->storage);
        dis->set_query(q);
        
        int best_hub_local_idx = -1;
        int min_cost = std::numeric_limits<int>::max();

        // 【性能优化】将 VisitedTable 移到 Hub 循环外，用 advance() O(1) 重置
        // 原来每次 probe_search 内部 new 一个 vt 需要清零 ntotal/8 字节内存
        // 对于 deep10M(11M节点)，每次清零 ~1.37MB，×500 hubs ×N queries 极慢
        faiss::VisitedTable vt(index->ntotal);
        for (int h = 0; h < (int)hubs.size(); ++h) {
            int start_node = hubs[h];
            vt.advance(); // O(1) 重置，generation++ 即可
            auto result = probe_search(*index->acsg.final_graph, *dis, start_node, gt_node, L, vt);
            
            if (result.first) {
                if (result.second < min_cost) {
                    min_cost = result.second;
                    best_hub_local_idx = h;
                }
            }
        }
        
        if (best_hub_local_idx == -1) {
            float min_dist = std::numeric_limits<float>::max();
            for (int h = 0; h < (int)hubs.size(); ++h) {
                float d = dis->operator()(hubs[h]);
                if (d < min_dist) { 
                    min_dist = d; 
                    best_hub_local_idx = h; 
                }
            }
            min_cost = -1;
        } else {
            success_count++;
        }
        
        labels[i] = {best_hub_local_idx, min_cost};
        
        int p = ++processed;
        if (p % 500 == 0 || p == nq) { 
            auto now = std::chrono::high_resolution_clock::now();
            std::chrono::duration<double> elapsed = now - start_time;
            double eta = (elapsed.count() / p) * (nq - p);
            printf("已处理 %d / %d 查询... (成功率: %.1f%%, 剩余时间: %.0fs)\r", 
                   p, nq, (float)success_count/p * 100.0, eta); 
            fflush(stdout); 
        }
    }
    std::cout << "\n模拟结束." << std::endl;

    // 7. 保存结果
    std::ofstream out(output_file, std::ios::binary);
    int dim_placeholder = 3; 
    out.write((char*)&nq, 4);
    out.write((char*)&dim_placeholder, 4);
    
    for (int i = 0; i < nq; ++i) {
        int buf[3] = {i, labels[i].best_hub_idx, labels[i].min_ndc};
        out.write((char*)buf, sizeof(int) * 3);
    }
    out.close();
    
    std::cout << "✅ 标签已保存至: " << output_file << std::endl;
    return 0;
}
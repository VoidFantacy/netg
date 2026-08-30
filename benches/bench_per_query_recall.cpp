#include <iostream>
#include <vector>
#include <algorithm>
#include <memory>
#include <chrono>
#include <fstream>
#include <argparse/argparse.hpp>
#include <benches/datasets/DataLoader.hpp>
#include <nlohmann/json.hpp>
#include <ACSG/IndexACSG.h>
#include <benches/utils/Timer.hpp>
#include <benches/utils/graph_properties.hpp>
#include <atomic>
#include <queue>
#include <cmath>
#include <filesystem>
#include <faiss/utils/distances.h>
#include <iomanip>
#include <cstring>
#include <unordered_set>
#include <sstream>
#include <random>
#include <limits>
#include <faiss/IndexFlat.h>
#include <numeric>

#include <hnswlib/hnswlib.h>
#include <faiss/VectorTransform.h>
#include <faiss/index_io.h>

using json = nlohmann::json;

// ==========================================
// Per-Query Recall Distribution Benchmark
// ==========================================
// 对比 NSG (Medoid baseline) 与 NETG (Asym-Neural HNSW) 
// 在相同 search_L 下每个查询的 recall，用于验证几何迷失

// ==========================================
// EntryPointSearcher (简化版，只保留需要的模式)
// ==========================================

class EntryPointSearcher {
public:
    enum Mode { MEDOID, HNSW_ROUTING };

    hnswlib::SpaceInterface<float>* hnsw_space_ = nullptr;
    hnswlib::HierarchicalNSW<float>* hnsw_router_ = nullptr;
    bool hnsw_use_ip_ = false;
    acsg::IndexACSG* index_ptr_ = nullptr;

    ~EntryPointSearcher() { reset(); }

    void reset() {
        if (hnsw_router_) { delete hnsw_router_; hnsw_router_ = nullptr; }
        if (hnsw_space_) { delete hnsw_space_; hnsw_space_ = nullptr; }
        hnsw_use_ip_ = false;
    }

    bool load_hnsw(const std::string& hubs_file, const std::string& ids_file, int dim, acsg::IndexACSG* index, bool use_ip = false) {
        reset();
        index_ptr_ = index;

        std::ifstream f_hubs(hubs_file, std::ios::binary | std::ios::ate);
        std::ifstream f_ids(ids_file, std::ios::binary | std::ios::ate);
        if (!f_hubs || !f_ids) {
            std::cerr << "❌ HNSW Routing Files Missing!" << std::endl;
            return false;
        }

        size_t hubs_size = f_hubs.tellg();
        int hub_num = hubs_size / (dim * sizeof(float));
        f_hubs.seekg(0, std::ios::beg);
        std::vector<float> hubs(hub_num * dim);
        f_hubs.read(reinterpret_cast<char*>(hubs.data()), hubs_size);

        size_t ids_size = f_ids.tellg();
        f_ids.seekg(0, std::ios::beg);
        std::vector<int> ids(hub_num);
        f_ids.read(reinterpret_cast<char*>(ids.data()), ids_size);

        hnsw_use_ip_ = use_ip;
        if (use_ip) {
            hnsw_space_ = new hnswlib::InnerProductSpace(dim);
        } else {
            hnsw_space_ = new hnswlib::L2Space(dim);
        }
        hnsw_router_ = new hnswlib::HierarchicalNSW<float>(hnsw_space_, hub_num, 16, 200);

        for (int i = 0; i < hub_num; ++i) {
            hnsw_router_->addPoint(hubs.data() + i * dim, ids[i]);
        }
        
        std::string space_name = use_ip ? "InnerProduct (cosine)" : "L2";
        std::cout << "✅ Loaded HNSW Router [" << space_name << "] (Hubs: " << hub_num << ", Dim: " << dim << ")" << std::endl;
        return true;
    }
};

// ==========================================
// 核心函数：逐查询计算 recall 并返回 per-query 结果
// ==========================================

std::vector<float> run_per_query_recall(
    acsg::IndexACSGFlat& index,
    const float* xq, int nq, int d, int k,
    const std::unique_ptr<faiss::idx_t[]>& gt,
    EntryPointSearcher& searcher,
    EntryPointSearcher::Mode mode)
{
    using idx_t = faiss::idx_t;
    std::unique_ptr<idx_t[]> I(new idx_t[nq * k]);
    std::unique_ptr<float[]> D(new float[nq * k]);

    // 为每个查询准备入口点
    std::vector<std::vector<acsg::EnterPoint>> all_eps(nq);

    if (mode == EntryPointSearcher::HNSW_ROUTING) {
        for (int i = 0; i < nq; ++i) {
            auto pq = searcher.hnsw_router_->searchKnn(xq + i * d, 3);
            while (!pq.empty()) {
                all_eps[i].emplace_back(acsg::EnterPoint(pq.top().second, 1.0));
                pq.pop();
            }
        }
    } else {
        // MEDOID baseline
        for (int i = 0; i < nq; ++i) {
            all_eps[i].emplace_back(acsg::EnterPoint(index.acsg.enterpoint, 1.0));
        }
    }

    // 搜索
    int search_internal_mode = 2;
    faiss::VisitedTable vt(index.ntotal);
    std::unique_ptr<faiss::DistanceComputer> dis(acsg::storage_distance_computer(index.storage));
    std::vector<acsg::Neighbor> retset_buf;

    for (int i = 0; i < nq; ++i) {
        faiss::idx_t* res_I = I.get() + i * k;
        float* res_D = D.get() + i * k;
        dis->set_query(xq + i * d);
        vt.advance();
        index.acsg.search_new(*dis, k, res_I, res_D, vt, search_internal_mode, all_eps[i], &retset_buf);
    }

    // 逐查询计算 recall
    std::vector<float> per_query_recalls(nq);
    for (int i = 0; i < nq; ++i) {
        std::unordered_set<faiss::idx_t> query_res;
        std::unordered_set<faiss::idx_t> query_gt;
        for (int j = 0; j < k; ++j) {
            query_res.insert(I[i * k + j]);
            query_gt.insert(gt[i * 100 + j]);  // gt stride = 100
        }
        float hit = 0;
        for (const auto& id : query_res) {
            if (query_gt.count(id)) hit += 1.0f;
        }
        per_query_recalls[i] = hit / k;
    }

    return per_query_recalls;
}

// ==========================================
// 主程序
// ==========================================

int main(int argc, char** argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    argparse::ArgumentParser program("bench_per_query_recall");
    
    program.add_argument("--dataset").required();
    program.add_argument("--acpg_file").required();
    program.add_argument("--output_file").required();
    program.add_argument("--transformed_hubs").default_value(std::string(""));
    program.add_argument("--transformed_ids").default_value(std::string(""));
    program.add_argument("--raw_hubs").default_value(std::string(""));
    program.add_argument("--search_L").default_value(std::string("512,1024"));
    program.add_argument("--top_k").default_value(1).scan<'i', int>();
    program.add_argument("--max_queries").default_value(10000).scan<'i', int>();

    try { program.parse_args(argc, argv); } catch (const std::exception& e) {
        std::cerr << e.what() << std::endl;
        return 1;
    }

    std::string dataset = program.get<std::string>("--dataset");
    std::string acpg_file = program.get<std::string>("--acpg_file");
    std::string output_file = program.get<std::string>("--output_file");
    std::string trans_hubs = program.get<std::string>("--transformed_hubs");
    std::string trans_ids = program.get<std::string>("--transformed_ids");
    std::string raw_hubs = program.get<std::string>("--raw_hubs");
    std::string search_L_str = program.get<std::string>("--search_L");
    int top_k = program.get<int>("--top_k");
    int max_q = program.get<int>("--max_queries");

    // 解析 search_L 列表
    std::vector<int> search_Ls;
    std::stringstream ss(search_L_str);
    std::string token;
    while (std::getline(ss, token, ',')) {
        search_Ls.push_back(std::stoi(token));
    }

    std::cout << "\n========================================" << std::endl;
    std::cout << "📊 Per-Query Recall Distribution Benchmark" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Dataset: " << dataset << std::endl;
    std::cout << "Top-K: " << top_k << std::endl;
    std::cout << "Search_L values: ";
    for (int L : search_Ls) std::cout << L << " ";
    std::cout << std::endl;

    // 加载数据
    std::cout << "\n>>> Loading Data..." << std::endl;
    DataLoader data_loader(dataset);
    auto [nq, xq] = data_loader.load_query("drl_test");
    auto [k_gt, gt] = data_loader.load_gt("drl_test");
    int d = data_loader.dim();

    if (max_q > 0 && nq > (size_t)max_q) { 
        std::cout << "⚠️ Truncating queries to " << max_q << std::endl; 
        nq = max_q; 
    }
    std::cout << "Queries: " << nq << ", Dim: " << d << std::endl;

    // 加载索引
    std::cout << "\n>>> Loading ACPG Index: " << acpg_file << std::endl;
    auto index = std::make_unique<acsg::IndexACSGFlat>();
    index->loadACPG(acpg_file.c_str());
    { std::vector<float>().swap(index->acsg.pheromone); }
    { std::vector<float>().swap(index->acsg.weight); }
    std::cout << "✅ Index loaded, pheromone & weight released." << std::endl;

    EntryPointSearcher searcher;
    json all_results;
    all_results["dataset"] = dataset;
    all_results["num_queries"] = nq;
    all_results["top_k"] = top_k;
    all_results["split"] = "held-out-test";
    all_results["metric"] = data_loader.metric_name();
    all_results["normalization"] = data_loader.normalization();
    all_results["artifact_version"] = data_loader.artifact_version();
    all_results["methods"] = json::array();

    // ==========================================
    // Method 1: NSG Baseline (Medoid entry point)
    // ==========================================
    {
        std::cout << "\n🔧 [NSG Baseline] Medoid entry point..." << std::endl;
        json method_result;
        method_result["method"] = "NSG_Medoid";
        method_result["search_results"] = json::array();

        for (int L : search_Ls) {
            index->acsg.search_L = L;
            auto recalls = run_per_query_recall(*index, xq.get(), nq, d, top_k, gt, searcher, EntryPointSearcher::MEDOID);

            // 计算统计数据
            float mean_r = 0;
            for (float r : recalls) mean_r += r;
            mean_r /= nq;

            const auto recalls_aligned = recalls;
            std::sort(recalls.begin(), recalls.end());
            float p5 = recalls[(int)(nq * 0.05)];
            float p10 = recalls[(int)(nq * 0.10)];
            float p25 = recalls[(int)(nq * 0.25)];
            float median = recalls[(int)(nq * 0.50)];

            // 计算低召回查询占比
            int count_below_50 = 0, count_below_80 = 0, count_below_90 = 0;
            int count_perfect = 0;
            for (float r : recalls) {
                if (r < 0.5f) count_below_50++;
                if (r < 0.8f) count_below_80++;
                if (r < 0.9f) count_below_90++;
                if (r >= 1.0f) count_perfect++;
            }

            json l_result;
            l_result["search_L"] = L;
            l_result["mean_recall"] = mean_r;
            l_result["p5"] = p5;
            l_result["p10"] = p10;
            l_result["p25"] = p25;
            l_result["median"] = median;
            l_result["pct_below_50"] = (float)count_below_50 / nq * 100;
            l_result["pct_below_80"] = (float)count_below_80 / nq * 100;
            l_result["pct_below_90"] = (float)count_below_90 / nq * 100;
            l_result["pct_perfect"] = (float)count_perfect / nq * 100;
            l_result["per_query_recalls"] = recalls;
            l_result["per_query_recalls_aligned"] = recalls_aligned;

            method_result["search_results"].push_back(l_result);

            std::cout << "  L=" << std::setw(5) << L 
                      << " | Mean=" << std::fixed << std::setprecision(4) << mean_r
                      << " | P5=" << std::setprecision(3) << p5
                      << " | <0.8: " << std::setprecision(1) << ((float)count_below_80 / nq * 100) << "%"
                      << " | <0.5: " << std::setprecision(1) << ((float)count_below_50 / nq * 100) << "%"
                      << std::endl;
        }
        all_results["methods"].push_back(method_result);
    }

    // ==========================================
    // Method 2: NETG (Asymmetric Neural HNSW Routing)
    // ==========================================
    if (!trans_hubs.empty() && std::filesystem::exists(trans_hubs) && 
        !trans_ids.empty() && std::filesystem::exists(trans_ids)) {
        
        std::cout << "\n🚀 [NETG] Asymmetric Neural HNSW Routing..." << std::endl;
        if (searcher.load_hnsw(trans_hubs, trans_ids, d, index.get(), true)) {
            json method_result;
            method_result["method"] = "NETG_AsymHNSW";
            method_result["search_results"] = json::array();

            for (int L : search_Ls) {
                index->acsg.search_L = L;
                auto recalls = run_per_query_recall(*index, xq.get(), nq, d, top_k, gt, searcher, EntryPointSearcher::HNSW_ROUTING);

                float mean_r = 0;
                for (float r : recalls) mean_r += r;
                mean_r /= nq;

                const auto recalls_aligned = recalls;
                std::sort(recalls.begin(), recalls.end());
                float p5 = recalls[(int)(nq * 0.05)];
                float p10 = recalls[(int)(nq * 0.10)];
                float p25 = recalls[(int)(nq * 0.25)];
                float median = recalls[(int)(nq * 0.50)];

                int count_below_50 = 0, count_below_80 = 0, count_below_90 = 0;
                int count_perfect = 0;
                for (float r : recalls) {
                    if (r < 0.5f) count_below_50++;
                    if (r < 0.8f) count_below_80++;
                    if (r < 0.9f) count_below_90++;
                    if (r >= 1.0f) count_perfect++;
                }

                json l_result;
                l_result["search_L"] = L;
                l_result["mean_recall"] = mean_r;
                l_result["p5"] = p5;
                l_result["p10"] = p10;
                l_result["p25"] = p25;
                l_result["median"] = median;
                l_result["pct_below_50"] = (float)count_below_50 / nq * 100;
                l_result["pct_below_80"] = (float)count_below_80 / nq * 100;
                l_result["pct_below_90"] = (float)count_below_90 / nq * 100;
                l_result["pct_perfect"] = (float)count_perfect / nq * 100;
                l_result["per_query_recalls"] = recalls;
                l_result["per_query_recalls_aligned"] = recalls_aligned;

                method_result["search_results"].push_back(l_result);

                std::cout << "  L=" << std::setw(5) << L 
                          << " | Mean=" << std::fixed << std::setprecision(4) << mean_r
                          << " | P5=" << std::setprecision(3) << p5
                          << " | <0.8: " << std::setprecision(1) << ((float)count_below_80 / nq * 100) << "%"
                          << " | <0.5: " << std::setprecision(1) << ((float)count_below_50 / nq * 100) << "%"
                          << std::endl;
            }
            all_results["methods"].push_back(method_result);
        }
    } else {
        std::cout << "\n⚠️ [NETG] Transformed hubs not found, skipping." << std::endl;
    }

    // ==========================================
    // Method 3: Raw HNSW (Ablation - no neural folding)
    // ==========================================
    if (!raw_hubs.empty() && std::filesystem::exists(raw_hubs) &&
        !trans_ids.empty() && std::filesystem::exists(trans_ids)) {
        
        std::cout << "\n📊 [Ablation] Raw HNSW Routing (no neural folding)..." << std::endl;
        searcher.reset();
        if (searcher.load_hnsw(raw_hubs, trans_ids, d, index.get(), data_loader.metric_type() == faiss::METRIC_INNER_PRODUCT)) {
            json method_result;
            method_result["method"] = "Raw_HNSW_Ablation";
            method_result["search_results"] = json::array();

            for (int L : search_Ls) {
                index->acsg.search_L = L;
                auto recalls = run_per_query_recall(*index, xq.get(), nq, d, top_k, gt, searcher, EntryPointSearcher::HNSW_ROUTING);

                float mean_r = 0;
                for (float r : recalls) mean_r += r;
                mean_r /= nq;

                const auto recalls_aligned = recalls;
                std::sort(recalls.begin(), recalls.end());
                float p5 = recalls[(int)(nq * 0.05)];
                float p10 = recalls[(int)(nq * 0.10)];
                float p25 = recalls[(int)(nq * 0.25)];
                float median = recalls[(int)(nq * 0.50)];

                int count_below_50 = 0, count_below_80 = 0, count_below_90 = 0;
                int count_perfect = 0;
                for (float r : recalls) {
                    if (r < 0.5f) count_below_50++;
                    if (r < 0.8f) count_below_80++;
                    if (r < 0.9f) count_below_90++;
                    if (r >= 1.0f) count_perfect++;
                }

                json l_result;
                l_result["search_L"] = L;
                l_result["mean_recall"] = mean_r;
                l_result["p5"] = p5;
                l_result["p10"] = p10;
                l_result["p25"] = p25;
                l_result["median"] = median;
                l_result["pct_below_50"] = (float)count_below_50 / nq * 100;
                l_result["pct_below_80"] = (float)count_below_80 / nq * 100;
                l_result["pct_below_90"] = (float)count_below_90 / nq * 100;
                l_result["pct_perfect"] = (float)count_perfect / nq * 100;
                l_result["per_query_recalls"] = recalls;
                l_result["per_query_recalls_aligned"] = recalls_aligned;

                method_result["search_results"].push_back(l_result);

                std::cout << "  L=" << std::setw(5) << L 
                          << " | Mean=" << std::fixed << std::setprecision(4) << mean_r
                          << " | P5=" << std::setprecision(3) << p5
                          << " | <0.8: " << std::setprecision(1) << ((float)count_below_80 / nq * 100) << "%"
                          << " | <0.5: " << std::setprecision(1) << ((float)count_below_50 / nq * 100) << "%"
                          << std::endl;
            }
            all_results["methods"].push_back(method_result);
        }
    }

    // 保存结果
    std::ofstream out(output_file);
    out << all_results.dump(2);
    std::cout << "\n✅ Results saved to: " << output_file << std::endl;

    return 0;
}

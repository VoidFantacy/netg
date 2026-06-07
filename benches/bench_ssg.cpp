/**
 * bench_ssg.cpp
 * NETG on SSG —— 用 SSG 作为图索引，验证 NETG 框架的通用性
 *
 * 流程：
 *   1. 加载数据 & GT
 *   2. 加载 SSG 索引（需要提前用 test_ssg_index 建图）
 *   3. 加载 HNSW Router（transformed_hubs + hub_ids）
 *   4. 遍历 search_L，测试：
 *      - SSG Medoid Baseline（单入口点）
 *      - NETG on SSG（HNSW 路由 → 多 Hub 入口点）
 *   5. 输出 QPS / Recall@K
 */

#include <iostream>
#include <vector>
#include <algorithm>
#include <memory>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <numeric>
#include <filesystem>

#include <argparse/argparse.hpp>
#include <nlohmann/json.hpp>
#include <hnswlib/hnswlib.h>

#include <benches/datasets/DataLoader.hpp>
#include <benches/utils/metrics.hpp>
#include <ACSG/IndexSSGWrapper.h>

using json = nlohmann::json;

// =====================================================================
// 1. HNSW 路由器（复用 test.cpp 逻辑）
// =====================================================================

struct HNSWRouter {
    hnswlib::SpaceInterface<float>* space = nullptr;
    hnswlib::HierarchicalNSW<float>* hnsw = nullptr;

    ~HNSWRouter() { delete hnsw; delete space; }

    bool load(const std::string& hubs_file, const std::string& ids_file,
              int dim, bool use_ip = true) {
        std::ifstream fh(hubs_file, std::ios::binary | std::ios::ate);
        std::ifstream fi(ids_file,  std::ios::binary | std::ios::ate);
        if (!fh || !fi) { std::cerr << "❌ Router files missing\n"; return false; }

        size_t hubs_bytes = fh.tellg(); fh.seekg(0);
        int hub_num = (int)(hubs_bytes / (dim * sizeof(float)));
        std::vector<float> hubs(hub_num * dim);
        fh.read(reinterpret_cast<char*>(hubs.data()), hubs_bytes);

        fi.seekg(0);
        std::vector<int> ids(hub_num);
        fi.read(reinterpret_cast<char*>(ids.data()), hub_num * sizeof(int));

        // ⚠️  关键修复：HNSW 的 max_elements 必须 >= 所有 label 值
        // hub_ids 文件里存的是原始图的 node ID（可达数百万），远超 hub_num
        // 用 max_id+1 作为 max_elements，避免内部 label_lookup 等数组越界
        int max_label = *std::max_element(ids.begin(), ids.end());
        size_t hnsw_max_elements = (size_t)max_label + 1;

        space = use_ip ? (hnswlib::SpaceInterface<float>*)new hnswlib::InnerProductSpace(dim)
                       : (hnswlib::SpaceInterface<float>*)new hnswlib::L2Space(dim);
        hnsw = new hnswlib::HierarchicalNSW<float>(space, hnsw_max_elements, 16, 200);
        for (int i = 0; i < hub_num; ++i)
            hnsw->addPoint(hubs.data() + i * dim, (size_t)ids[i]);

        std::cout << "✅ Loaded HNSW Router ["
                  << (use_ip ? "IP" : "L2")
                  << "] (Hubs: " << hub_num << ", Dim: " << dim << ")\n";
        return true;
    }

    std::vector<unsigned> query(const float* q, int top_k = 3) {
        auto pq = hnsw->searchKnn(q, top_k);
        std::vector<unsigned> ids;
        while (!pq.empty()) {
            ids.push_back((unsigned)pq.top().second);
            pq.pop();
        }
        return ids;
    }
};

// =====================================================================
// 2. 测试函数：返回 QPS + Recall
// =====================================================================

struct BenchResult { double qps; double recall; };

BenchResult run_bench(
    netg::IndexSSGWrapper& index,
    const float* xq, int nq, int d, int top_k,
    const std::unique_ptr<faiss::idx_t[]>& gt, int gt_k,
    unsigned L, HNSWRouter* router)
{
    std::vector<unsigned> result_buf(nq * top_k);

    auto t0 = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < nq; ++i) {
        unsigned* res = result_buf.data() + i * top_k;
        if (router) {
            auto hub_ids = router->query(xq + i * d, 3);
            index.search_with_eps(xq + i * d, top_k, L, hub_ids, res);
        } else {
            index.search(xq + i * d, top_k, L, res);
        }
    }

    auto t1 = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double>(t1 - t0).count();

    std::unique_ptr<faiss::idx_t[]> I(new faiss::idx_t[nq * top_k]);
    for (int i = 0; i < nq * top_k; ++i) I[i] = (faiss::idx_t)result_buf[i];

    BenchResult r;
    r.qps    = nq / elapsed;
    r.recall = recall_at_k(nq, top_k, top_k, I, gt_k, gt);
    return r;
}

// =====================================================================
// 3. 主程序
// =====================================================================

int main(int argc, char** argv) {
    argparse::ArgumentParser prog("bench_ssg");
    prog.add_argument("--dataset").required();
    prog.add_argument("--ssg_file").required();
    prog.add_argument("--fn_result").required();
    prog.add_argument("--transformed_hubs").default_value(std::string(""));
    prog.add_argument("--transformed_ids").default_value(std::string(""));
    prog.add_argument("--num_runs").default_value(3).scan<'i', int>();
    prog.add_argument("--recall_k").default_value(100).scan<'i', int>();

    try { prog.parse_args(argc, argv); }
    catch (const std::runtime_error& e) {
        std::cerr << e.what() << "\n" << prog; return 1;
    }

    const auto dataset    = prog.get<std::string>("--dataset");
    const auto ssg_file   = prog.get<std::string>("--ssg_file");
    const auto result_file= prog.get<std::string>("--fn_result");
    const auto trans_hubs = prog.get<std::string>("--transformed_hubs");
    const auto trans_ids  = prog.get<std::string>("--transformed_ids");
    const int  num_runs   = prog.get<int>("--num_runs");
    const int  recall_k   = prog.get<int>("--recall_k");

    // ── 加载数据 ─────────────────────────────────────────────────────
    std::cout << "\n>>> Loading Data (" << dataset << ")...\n";
    DataLoader dl(dataset);
    auto [nq, xq]     = dl.load_query("drl_test");
    auto [gt_k, gt]   = dl.load_gt("drl_test");
    auto [nb, xb]     = dl.load_base();
    int d = dl.dim();
    const int top_k   = recall_k;  // 由 --recall_k 控制
    std::cout << "📊 Recall@" << top_k << " mode\n";

    if ((int)nq > 10000) { nq = 10000; std::cout << "⚠️ Truncating queries to 10000\n"; }

    // ── 加载 SSG 索引 ─────────────────────────────────────────────────
    // yandex_t2i 使用 Inner Product 距离，其他数据集使用 L2
    bool use_ip = (dataset == "yandex_t2i");
    netg::IndexSSGWrapper index;
    index.load(ssg_file, xb.get(), nb, d, use_ip);

    // ── 加载 HNSW 路由器 ──────────────────────────────────────────────
    HNSWRouter router;
    bool has_router = false;
    if (!trans_hubs.empty() && std::filesystem::exists(trans_hubs) &&
        !trans_ids.empty()  && std::filesystem::exists(trans_ids)) {
        has_router = router.load(trans_hubs, trans_ids, d, use_ip);
    }

    // search_L 范围：完整列表（recall@1 时小 L 有意义；recall@100 时 L<100 自动跳过）
    const std::vector<unsigned> all_Ls = {
        1, 2, 4, 8, 16, 32, 64,
        100, 128, 150, 200, 250, 300, 400, 512, 600, 800, 1024, 1200, 1500
    };
    // L 必须 >= top_k（否则结果无意义）
    std::vector<unsigned> search_Ls;
    for (unsigned L : all_Ls)
        if ((int)L >= top_k) search_Ls.push_back(L);

    struct Task { std::string name; bool use_router; };
    // 双路测试：先跑 Baseline，再跑 NETG
    std::vector<Task> tasks;
    tasks.push_back({"SSG Medoid (Baseline)", false});
    if (has_router)
        tasks.push_back({"NETG on SSG (HNSW Routing)", true});

    json all_results = json::array();

    for (const auto& task : tasks) {
        std::cout << "\n================================================================\n";
        std::cout << "🔥 " << task.name << "\n";
        std::cout << std::setw(6)  << "L"
                  << " | " << std::setw(12) << "QPS"
                  << " | " << std::setw(10) << "Recall\n";
        std::cout << std::string(34, '-') << "\n";

        json perf = json::array();

        for (unsigned L : search_Ls) {
            double t_qps = 0, t_rec = 0;
            for (int r = 0; r < num_runs; ++r) {
                auto res = run_bench(index, xq.get(), (int)nq, d, top_k,
                                     gt, gt_k, L,
                                     task.use_router ? &router : nullptr);
                t_qps += res.qps;
                t_rec += res.recall;
            }
            double avg_qps = t_qps / num_runs;
            double avg_rec = t_rec / num_runs;

            std::cout << std::setw(6) << L
                      << " | " << std::setw(12) << std::fixed << std::setprecision(1) << avg_qps
                      << " | " << std::setw(10) << std::setprecision(4) << avg_rec << "\n";
            std::cout.flush();

            perf.push_back({{"L", L}, {"qps", avg_qps}, {"recall", avg_rec}});
        }

        all_results.push_back({{"method", task.name}, {"performance", perf}});
    }

    json output;
    output["dataset"] = dataset;
    output["index"]   = "SSG";
    output["recall_k"]= top_k;
    output["results"] = all_results;

    std::ofstream ofs(result_file);
    ofs << output.dump(4) << "\n";
    std::cout << "\n✅ Done. Saved to " << result_file << "\n";
    return 0;
}

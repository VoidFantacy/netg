/**
 * test_hop.cpp
 * NETG 专用测试：只统计 Recall / Memory / Hop Count
 * search_L 与 HNSW ef_params 对齐：{10,20,40,80,100,150,200,300,400,500,600,800,1024,1600}
 *
 * 编译：在 benches/CMakeLists.txt 中已注册 test_hop 目标
 * 用法示例：
 *   ./build/benches/test_hop \
 *       --dataset deep10M \
 *       --acpg_file /path/to/acpg \
 *       --fn_result result_hop.json \
 *       --transformed_hubs /path/to/hub_embeddings.bin \
 *       --transformed_ids  /path/to/hub_ids.bin
 */

#include <iostream>
#include <vector>
#include <algorithm>
#include <memory>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <numeric>
#include <cstring>
#include <filesystem>
#include <unordered_set>
#include <malloc.h>

#include <argparse/argparse.hpp>
#include <nlohmann/json.hpp>

#include <benches/datasets/DataLoader.hpp>
#include <benches/utils/metrics.hpp>

#include <ACSG/IndexACSG.h>
#include <faiss/utils/distances.h>
#include <faiss/impl/DistanceComputer.h>
#include <hnswlib/hnswlib.h>

using json = nlohmann::json;

// =====================================================================
// 1. 辅助工具
// =====================================================================

static double get_memory_mb() {
    std::ifstream f("/proc/self/status");
    std::string line;
    while (std::getline(f, line)) {
        if (line.substr(0, 6) == "VmRSS:") {
            std::istringstream ss(line);
            std::string key; long val;
            ss >> key >> val;
            return val / 1024.0;
        }
    }
    return 0.0;
}

// =====================================================================
// 2. 跳数统计 DistanceComputer 包装器
//    每次 operator()(idx_t) 被调用 = 访问一个节点 = 一跳
// =====================================================================

struct CountingDC : faiss::DistanceComputer {
    faiss::DistanceComputer* inner;
    long hop_count = 0;

    explicit CountingDC(faiss::DistanceComputer* inner) : inner(inner) {}

    float operator()(faiss::idx_t i) override {
        ++hop_count;
        return (*inner)(i);
    }

    float symmetric_dis(faiss::idx_t i, faiss::idx_t j) override {
        return inner->symmetric_dis(i, j);
    }

    void set_query(const float* x) override {
        inner->set_query(x);
    }

    void reset() { hop_count = 0; }
};

// =====================================================================
// 3. HNSW 路由器（复用 test.cpp 的 load_hnsw 逻辑）
// =====================================================================

struct HNSWRouter {
    hnswlib::SpaceInterface<float>* space = nullptr;
    hnswlib::HierarchicalNSW<float>* hnsw  = nullptr;
    bool use_ip = false;

    ~HNSWRouter() {
        delete hnsw;  hnsw  = nullptr;
        delete space; space = nullptr;
    }

    bool load(const std::string& hubs_file, const std::string& ids_file, int dim, bool ip) {
        use_ip = ip;
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

        space = ip ? (hnswlib::SpaceInterface<float>*)new hnswlib::InnerProductSpace(dim)
                   : (hnswlib::SpaceInterface<float>*)new hnswlib::L2Space(dim);
        hnsw = new hnswlib::HierarchicalNSW<float>(space, hub_num, 16, 200);
        for (int i = 0; i < hub_num; ++i)
            hnsw->addPoint(hubs.data() + i * dim, ids[i]);

        std::cout << "✅ Loaded HNSW Router ["
                  << (ip ? "InnerProduct" : "L2")
                  << "] (Hubs: " << hub_num << ", Dim: " << dim << ")\n";
        return true;
    }

    // 返回 top-3 hub node IDs
    std::vector<int> query(const float* q, int dim) {
        auto pq = hnsw->searchKnn(q, 3);
        std::vector<int> ids;
        while (!pq.empty()) { ids.push_back((int)pq.top().second); pq.pop(); }
        return ids;
    }
};

// =====================================================================
// 4. 单次搜索批次：返回 recall / avg_hops / mem_mb
// =====================================================================

struct BatchResult {
    double recall  = 0;
    double avg_hops = 0;
    double mem_mb  = 0;
};

BatchResult run_batch(
    acsg::IndexACSG& index,
    const float* xq, int nq, int d, int k,
    const std::unique_ptr<faiss::idx_t[]>& gt,
    HNSWRouter* router,          // nullptr = medoid
    int medoid_id
) {
    std::unique_ptr<faiss::idx_t[]> I(new faiss::idx_t[nq * k]);
    std::unique_ptr<float[]>        D(new float[nq * k]);

    // 底层 DC + 计数包装
    std::unique_ptr<faiss::DistanceComputer> base_dc(
        acsg::storage_distance_computer(index.storage));
    CountingDC cdc(base_dc.get());

    faiss::VisitedTable vt(index.ntotal);
    std::vector<acsg::Neighbor> retset_buf;

    long total_hops = 0;

    for (int i = 0; i < nq; ++i) {
        cdc.set_query(xq + i * d);
        cdc.reset();
        vt.advance();

        std::vector<acsg::EnterPoint> eps;
        if (router) {
            for (int id : router->query(xq + i * d, d))
                eps.emplace_back(id, 1.0f);
        } else {
            eps.emplace_back(medoid_id, 1.0f);
        }

        faiss::idx_t* res_I = I.get() + i * k;
        float*        res_D = D.get() + i * k;
        index.acsg.search_new(cdc, k, res_I, res_D, vt, 2, eps, &retset_buf);

        total_hops += cdc.hop_count;
    }

    BatchResult r;
    r.recall   = recall_at_k(nq, k, k, I, 100, gt);
    r.avg_hops = (double)total_hops / nq;
    r.mem_mb   = get_memory_mb();
    return r;
}

// =====================================================================
// 5. 主程序
// =====================================================================

int main(int argc, char** argv) {
    setvbuf(stdout, NULL, _IONBF, 0);

    argparse::ArgumentParser prog("test_hop");
    prog.add_argument("--dataset").required();
    prog.add_argument("--acpg_file").required();
    prog.add_argument("--fn_result").required();
    prog.add_argument("--transformed_hubs").default_value(std::string(""));
    prog.add_argument("--transformed_ids").default_value(std::string(""));
    prog.add_argument("--num_runs").default_value(3).scan<'i', int>();

    try { prog.parse_args(argc, argv); } catch (const std::runtime_error& e) {
        std::cerr << e.what() << "\n" << prog; return 1;
    }

    const std::string dataset    = prog.get<std::string>("--dataset");
    const std::string acpg_file  = prog.get<std::string>("--acpg_file");
    const std::string result_file= prog.get<std::string>("--fn_result");
    const std::string trans_hubs = prog.get<std::string>("--transformed_hubs");
    const std::string trans_ids  = prog.get<std::string>("--transformed_ids");
    const int         num_runs   = prog.get<int>("--num_runs");

    // ── 加载数据 ──────────────────────────────────────────────────────
    std::cout << "\n>>> Loading Data (" << dataset << ")...\n";
    DataLoader dl(dataset);
    auto [nq, xq] = dl.load_query("drl_test");
    auto [k_gt, gt] = dl.load_gt("drl_test");
    int d = dl.dim();
    int top_k = 100;  // Recall@10

    const int max_q = 10000;
    if ((int)nq > max_q) { std::cout << "⚠️ Truncating to " << max_q << "\n"; nq = max_q; }

    // ── 加载索引 ──────────────────────────────────────────────────────
    std::cout << "\n>>> Loading ACPG: " << acpg_file << "\n";
    auto index = std::make_unique<acsg::IndexACSGFlat>();
    index->loadACPG(acpg_file.c_str());

    // 释放搜索阶段不需要的内存
    { std::vector<float>().swap(index->acsg.pheromone); }
    { std::vector<float>().swap(index->acsg.weight);    }
    { std::vector<acsg::EnterPoint>().swap(index->acsg.top_enterpoints); }
    // 强制将释放的堆内存归还 OS，使 VmRSS 立即下降
    malloc_trim(0);

    int medoid_id = index->acsg.enterpoint;

    // ── 索引加载完成后立即采样内存（此后搜索阶段内存基本不变）────────
    double index_mem_mb = get_memory_mb();
    std::cout << "📊 Index loaded. Memory: " << std::fixed
              << std::setprecision(1) << index_mem_mb << " MB\n";

    // ── 加载 HNSW 路由器 ──────────────────────────────────────────────
    HNSWRouter router;
    bool has_router = false;
    if (!trans_hubs.empty() && std::filesystem::exists(trans_hubs) &&
        !trans_ids.empty()  && std::filesystem::exists(trans_ids)) {
        has_router = router.load(trans_hubs, trans_ids, d, /*use_ip=*/true);
    }

    // ── search_L 列表（与 HNSW ef_params 对齐）────────────────────────
    const std::vector<int> search_Ls = {
        100, 150, 200, 300, 400, 500, 600, 800, 1024, 1600
    };

    struct TaskConf {
        std::string name;
        bool use_router;
    };
    std::vector<TaskConf> task_confs;
    task_confs.push_back({"Medoid (Baseline)", false});
    if (has_router) task_confs.push_back({"NETG (HNSW Routing)", true});

    json all_results = json::array();

    for (const auto& tc : task_confs) {
        std::cout << "\n================================================================\n";
        std::cout << "🔥 Task: " << tc.name << "\n";
        std::cout << "   L  |   Recall   | Avg Hops  |   Mem (MB)\n";
        std::cout << "------+------------+-----------+-----------\n";

        json method_res;
        method_res["method_name"] = tc.name;
        json perf = json::array();

        for (int L : search_Ls) {
            index->acsg.search_L = L;

            double t_rec = 0, t_hops = 0, last_mem = 0;
            for (int r = 0; r < num_runs; ++r) {
                BatchResult br = run_batch(*index, xq.get(), (int)nq, d, top_k, gt,
                                           tc.use_router ? &router : nullptr,
                                           medoid_id);
                t_rec  += br.recall;
                t_hops += br.avg_hops;
                last_mem = br.mem_mb;
            }

            double avg_rec  = t_rec  / num_runs;
            double avg_hops = t_hops / num_runs;

            std::cout << std::setw(5)  << L       << " | "
                      << std::setw(9)  << std::fixed << std::setprecision(4) << avg_rec  << " | "
                      << std::setw(9)  << std::setprecision(1) << avg_hops  << " | "
                      << std::setw(9)  << std::setprecision(1) << last_mem  << " MB\n";

            perf.push_back({
                {"search_L",  L},
                {"recall",    avg_rec},
                {"avg_hops",  avg_hops},
                {"mem_mb",    last_mem}
            });
        }

        method_res["performance"] = perf;
        all_results.push_back(method_res);
    }

    json output;
    output["dataset"]       = dataset;
    output["recall_k"]      = top_k;
    output["index_mem_mb"]  = index_mem_mb;
    output["results"]       = all_results;

    std::ofstream ofs(result_file);
    ofs << output.dump(4) << "\n";
    std::cout << "\n✅ Done. Saved to " << result_file << "\n";
    return 0;
}

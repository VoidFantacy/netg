/**
 * LSH-APG Benchmark — 对齐 bench_nsg / bench_ssg 测试格式
 * Usage:
 *   ./lgo --dataset <name> --base <base.fvecs> --query <q.fvecs>
 *         --gt <gt.ivecs> --index_dir <dir/> --result <out.json>
 *         [--recall_k 100] [--num_runs 10]
 */
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <chrono>
#include <iomanip>
#include <algorithm>
#include <set>
#include <filesystem>
#include "alg.h"

int _lsh_UB = 0;

// ── 简单 CLI 解析 ──────────────────────────────────────────────────
static std::string get_arg(int argc, char const* argv[],
                            const std::string& key, const std::string& def = "") {
    for (int i = 1; i < argc - 1; ++i)
        if (std::string(argv[i]) == key) return argv[i + 1];
    return def;
}

// ── 数据加载 ───────────────────────────────────────────────────────
void load_fvecs(const std::string& path, float*& data, unsigned& num, unsigned& dim) {
    std::ifstream in(path, std::ios::binary);
    if (!in) { std::cerr << "Cannot open: " << path << "\n"; exit(1); }
    in.read((char*)&dim, 4);
    in.seekg(0, std::ios::end);
    num = (unsigned)((size_t)in.tellg() / (dim * 4 + 4));
    data = new float[(size_t)num * dim];
    in.seekg(0);
    for (size_t i = 0; i < num; i++) {
        in.seekg(4, std::ios::cur);
        in.read((char*)(data + i * dim), dim * 4);
    }
}

void load_ivecs(const std::string& path, unsigned*& data, unsigned& num, unsigned& dim) {
    std::ifstream in(path, std::ios::binary);
    if (!in) { std::cerr << "Cannot open: " << path << "\n"; exit(1); }
    in.read((char*)&dim, 4);
    in.seekg(0, std::ios::end);
    num = (unsigned)((size_t)in.tellg() / (dim * 4 + 4));
    data = new unsigned[(size_t)num * dim];
    in.seekg(0);
    for (size_t i = 0; i < num; i++) {
        in.seekg(4, std::ios::cur);
        in.read((char*)(data + i * dim), dim * 4);
    }
}

// ── Recall@K ──────────────────────────────────────────────────────
float calc_recall(const std::vector<std::vector<unsigned>>& results,
                  const unsigned* gt, unsigned gt_dim, unsigned K) {
    size_t nq = results.size(), hit = 0;
    for (size_t i = 0; i < nq; ++i) {
        std::set<unsigned> gt_set;
        for (unsigned j = 0; j < K && j < gt_dim; ++j) gt_set.insert(gt[i * gt_dim + j]);
        for (unsigned v : results[i]) if (gt_set.count(v)) ++hit;
    }
    return (float)hit / (nq * K);
}

// ── 单次运行 ──────────────────────────────────────────────────────
struct RunResult { double qps; float recall; };

RunResult run_once(fastGraph* fsG, queryN* qTpl,
                   const float* xq, unsigned nq, unsigned dim,
                   const unsigned* gt, unsigned gt_dim,
                   unsigned ef, unsigned K) {
    fsG->ef = (int)ef;
    std::vector<std::vector<unsigned>> results(nq);

    auto t0 = std::chrono::high_resolution_clock::now();
    for (unsigned i = 0; i < nq; ++i) {
        qTpl->queryPoint = const_cast<float*>(xq + i * dim);
        qTpl->res.clear();
        qTpl->k = (int)K;
        fsG->knn(qTpl);
        results[i].resize(qTpl->res.size());
        for (size_t j = 0; j < qTpl->res.size(); ++j)
            results[i][j] = (unsigned)qTpl->res[j].id;
    }
    auto t1 = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double>(t1 - t0).count();

    return { nq / elapsed, calc_recall(results, gt, gt_dim, K) };
}

// ── 主程序 ────────────────────────────────────────────────────────
int main(int argc, char const* argv[]) {
    std::string dataset    = get_arg(argc, argv, "--dataset");
    std::string base_file  = get_arg(argc, argv, "--base");
    std::string query_file = get_arg(argc, argv, "--query");
    std::string gt_file    = get_arg(argc, argv, "--gt");
    std::string index_dir  = get_arg(argc, argv, "--index_dir", "./indexes/");
    std::string result_file= get_arg(argc, argv, "--result",    dataset + "_result.json");
    int recall_k = std::stoi(get_arg(argc, argv, "--recall_k", "100"));
    int num_runs = std::stoi(get_arg(argc, argv, "--num_runs",  "10"));

    if (dataset.empty() || base_file.empty() || query_file.empty() || gt_file.empty()) {
        std::cerr << "Usage: ./lgo --dataset <name> --base <f> --query <f> --gt <f>\n"
                     "             --index_dir <dir/> --result <out.json>\n"
                     "             [--recall_k 100] [--num_runs 10]\n";
        return 1;
    }

    // 加载 base（Preprocess 负责读取）
    std::cout << "\n>>> Loading Data (" << dataset << ")...\n";
    Preprocess prep(base_file.c_str(), "");

    // 加载 / 构建索引
    std::string index_path = index_dir + dataset + ".index";
    divGraph* divG = nullptr;
    if (find_file(index_path + "_divGraph")) {
        std::cout << ">>> Loading index: " << index_path << "_divGraph\n";
        divG = new divGraph(&prep, index_path + "_divGraph", 0.9);
    } else {
        std::cout << ">>> Building index -> " << index_path << "_divGraph\n";
        std::filesystem::create_directories(index_dir);
        Parameter param1(prep, 8, 10, 1.0f);
        divG = new divGraph(prep, param1, index_path + "_divGraph", 24, 80, 0.95, 0.9);
    }
    fastGraph* fsG = new fastGraph(divG);
    fsG->initFlagPool();   // 预分配复用 flag 数组，避免每次 query O(N) memset
    std::cout << "Index ready. N=" << fsG->N << " dim=" << fsG->dim << "\n";

    // 加载 query / GT（必须在构造 queryN 之前完成）
    float*    xq = nullptr; unsigned nq = 0, qdim = 0;
    unsigned* gt = nullptr; unsigned ngt = 0, gt_dim = 0;
    load_fvecs(query_file, xq, nq, qdim);
    load_ivecs(gt_file,    gt, ngt, gt_dim);
    std::cout << "Recall@" << recall_k << " | nq=" << nq << "\n";

    // queryN 构造时访问 prep.data.query[flag=0]，需提前设为合法指针
    prep.data.query    = new float*[1];
    prep.data.query[0] = xq;          // 随便指向第 0 条 query，反正之后会覆盖

    // queryN 模板（每次搜索前会重设 queryPoint / k）
    queryN* qTpl = new queryN(0, 1.5f, recall_k, prep, 0.1f);

    // search_L 列表：recall@1 时从 1 开始；recall@100 时自动跳过 < 100 的值
    const std::vector<unsigned> all_Ls = {
        1, 2, 4, 8, 16, 32, 64,
        100, 128, 150, 200, 250, 300, 400, 512, 600, 800, 1024, 1200, 1500
    };
    std::vector<unsigned> search_Ls;
    for (unsigned L : all_Ls) if ((int)L >= recall_k) search_Ls.push_back(L);

    // 测试
    std::cout << "\n================================================================\n";
    std::cout << "LSH-APG\n";
    std::cout << std::setw(6)  << "ef"
              << " | " << std::setw(12) << "QPS"
              << " | " << std::setw(10) << "Recall\n";
    std::cout << std::string(34, '-') << "\n";

    std::vector<std::tuple<unsigned,double,float>> perf;

    for (unsigned ef : search_Ls) {
        double sum_qps = 0; float sum_rec = 0;
        for (int r = 0; r < num_runs; ++r) {
            auto res = run_once(fsG, qTpl, xq, nq, qdim, gt, gt_dim, ef, recall_k);
            sum_qps += res.qps;
            sum_rec += res.recall;
        }
        double avg_qps = sum_qps / num_runs;
        float  avg_rec = sum_rec / num_runs;
        std::cout << std::setw(6) << ef
                  << " | " << std::setw(12) << std::fixed << std::setprecision(1) << avg_qps
                  << " | " << std::setw(10) << std::setprecision(4) << avg_rec << "\n";
        std::cout.flush();
        perf.emplace_back(ef, avg_qps, avg_rec);
    }

    // 输出 JSON（与 bench_nsg/bench_ssg 格式一致）
    std::ofstream ofs(result_file);
    ofs << "{\n"
        << "  \"dataset\": \"" << dataset << "\",\n"
        << "  \"index\": \"LSH-APG\",\n"
        << "  \"recall_k\": " << recall_k << ",\n"
        << "  \"results\": [\n    {\n"
        << "      \"method\": \"LSH-APG\",\n"
        << "      \"performance\": [\n";
    for (size_t i = 0; i < perf.size(); ++i) {
        auto [ef, qps, rec] = perf[i];
        ofs << "        {\"L\": " << ef
            << ", \"qps\": " << std::fixed << std::setprecision(2) << qps
            << ", \"recall\": " << std::setprecision(6) << rec << "}";
        if (i + 1 < perf.size()) ofs << ",";
        ofs << "\n";
    }
    ofs << "      ]\n    }\n  ]\n}\n";

    std::cout << "\nDone. Saved to " << result_file << "\n";

    delete[] xq; delete[] gt; delete qTpl; delete fsG; delete divG;
    return 0;
}

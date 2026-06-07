#include <iostream>
#include <vector>
#include <algorithm>
#include <memory>
#include <chrono>
#include <fstream>
#include <argparse/argparse.hpp>
#include <benches/datasets/DataLoader.hpp>
#include <nlohmann/json.hpp>
#include <benches/utils/Timer.hpp>
#include <benches/utils/metrics.hpp>
#include <iomanip>
#include <sstream>
#include <thread>
#include <numeric>
#include <cmath>
#include <unordered_set>

// hnswlib (header-only)
#include <benches/hnswlib/hnswlib.h>

using json = nlohmann::json;

// ==========================================
// Recall (intersection-based)
// ==========================================
double compute_recall(
    const std::vector<std::vector<hnswlib::labeltype>>& results,
    const faiss::idx_t* gt, int gt_k, int top_k, int nq)
{
    size_t hit = 0, total = 0;
    for (int i = 0; i < nq; ++i) {
        std::unordered_set<hnswlib::labeltype> gt_set;
        for (int j = 0; j < top_k && j < gt_k; ++j)
            gt_set.insert(static_cast<hnswlib::labeltype>(gt[i * gt_k + j]));
        for (int j = 0; j < top_k && j < (int)results[i].size(); ++j)
            if (gt_set.count(results[i][j])) ++hit;
        total += top_k;
    }
    return (double)hit / total;
}

// ==========================================
// Search
// ==========================================
struct SearchResult { double qps; double recall; };

SearchResult run_search(
    hnswlib::HierarchicalNSW<float>& index,
    const float* xq, int nq, int d, int top_k,
    const faiss::idx_t* gt, int gt_k)
{
    std::vector<std::vector<hnswlib::labeltype>> results(nq);
    auto t0 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < nq; ++i) {
        auto pq = index.searchKnn(xq + i * d, top_k);
        results[i].resize(pq.size());
        for (int j = (int)pq.size() - 1; j >= 0; --j) {
            results[i][j] = pq.top().second; pq.pop();
        }
    }
    auto t1 = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double>(t1 - t0).count();
    return { (double)nq / elapsed, compute_recall(results, gt, gt_k, top_k, nq) };
}

// ==========================================
// Main
// ==========================================
int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    argparse::ArgumentParser program("bench_hnsw");
    program.add_argument("--M").default_value(32).scan<'i', int>();
    program.add_argument("--efConstruction").default_value(200).scan<'i', int>();
    program.add_argument("--dataset").required();
    program.add_argument("--fn_result").required();
    program.add_argument("--top_k_list").default_value(std::string("1,100"));
    program.add_argument("--num_runs").default_value(3).scan<'i', int>();
    program.add_argument("--use_ip").default_value(false).implicit_value(true);

    try { program.parse_args(argc, argv); }
    catch (const std::runtime_error &err) {
        std::cerr << err.what() << "\n" << program; std::exit(1);
    }

    std::string dataset_name = program.get<std::string>("--dataset");
    int M = program.get<int>("--M");
    int efC = program.get<int>("--efConstruction");
    int num_runs = program.get<int>("--num_runs");
    bool use_ip = program.get<bool>("--use_ip");
    std::string fn_result_prefix = program.get<std::string>("--fn_result");

    std::vector<int> top_k_list;
    {
        std::string s = program.get<std::string>("--top_k_list");
        std::stringstream ss(s); std::string tok;
        while (std::getline(ss, tok, ',')) top_k_list.push_back(std::stoi(tok));
    }

    std::cout << "\n>>> Loading Data (" << dataset_name << ")...\n";
    DataLoader data_loader(dataset_name);
    auto [nq, xq] = data_loader.load_query("drl_test");
    auto [gt_k, gt] = data_loader.load_gt("drl_test");
    int d = data_loader.dim();
    if (nq > 10000u) { std::cout << "Truncating queries to 10000\n"; nq = 10000; }

    // hnswlib space
    hnswlib::SpaceInterface<float>* space;
    if (use_ip) {
        space = new hnswlib::InnerProductSpace(d);
        std::cout << ">>> Metric: InnerProduct (hnswlib)\n";
    } else {
        space = new hnswlib::L2Space(d);
        std::cout << ">>> Metric: L2 (hnswlib)\n";
    }

    // Build index
    auto [nb, xb] = data_loader.load_base();
    std::cout << ">>> Building hnswlib (M=" << M << " efC=" << efC
              << " n=" << nb << " d=" << d << ")\n";

    auto* index = new hnswlib::HierarchicalNSW<float>(space, nb, M, efC);
    Timer timer;
    index->addPoint(xb.get(), 0);
    int nt = std::max(1, (int)std::thread::hardware_concurrency());
    #pragma omp parallel for num_threads(nt) schedule(dynamic)
    for (size_t i = 1; i < nb; ++i) index->addPoint(xb.get() + i * d, i);
    double ct = timer.elapsed_ms() * 1e-3;
    std::cout << "Construction Time = " << ct << " [s]\n";
    xb.reset();

    json params = {{"M",M},{"efConstruction",efC},{"use_ip",use_ip},{"library","hnswlib"}};

    // Benchmark each top_k
    for (int top_k : top_k_list) {
        if (top_k > (int)gt_k) top_k = (int)gt_k;
        std::vector<int> efs;
        if (top_k <= 1)
            efs = {1,2,4,8,16,32,64,100,128,150,200,250,300,400,512,600,800,1024,1200,1500};
        else
            efs = {100,128,150,200,250,300,400,512,600,800,1024,1200,1500};

        json perf = json::array();
        std::cout << "\n==================================================================\n";
        std::cout << "HNSW (hnswlib): Recall@" << top_k
                  << "  Runs=" << num_runs << "  Single-Thread\n\n";
        std::cout << std::setw(6) << "ef_s" << " | "
                  << std::setw(12) << "QPS" << " | "
                  << std::setw(10) << "Recall" << "\n";
        std::cout << std::string(34, '-') << "\n";

        for (int ef : efs) {
            index->setEf(ef);
            int wnq = std::min((int)nq, 2000);
            for (int w = 0; w < 2; ++w)
                run_search(*index, xq.get(), wnq, d, top_k, gt.get(), gt_k);

            double tq = 0, tr = 0;
            for (int r = 0; r < num_runs; ++r) {
                auto m = run_search(*index, xq.get(), nq, d, top_k, gt.get(), gt_k);
                tq += m.qps; tr += m.recall;
            }
            double aq = tq / num_runs, ar = tr / num_runs;
            std::cout << std::setw(6) << ef << " | "
                      << std::setw(12) << std::fixed << std::setprecision(1) << aq << " | "
                      << std::setw(10) << std::setprecision(4) << ar << "\n";
            perf.push_back({{"efSearch",ef},{"qps",aq},{"recall",ar}});
        }

        std::string fn = fn_result_prefix + "_recall" + std::to_string(top_k) + ".json";
        json out = {{"dataset",dataset_name},{"method","HNSW"},{"top_k",top_k},
                    {"parameters",params},{"construction_time",ct},{"search_performances",perf}};
        std::ofstream(fn) << out.dump(4) << "\n";
        std::cout << "\n✅ Recall@" << top_k << " saved to \"" << fn << "\"\n";
    }

    delete index;
    delete space;
    return 0;
}

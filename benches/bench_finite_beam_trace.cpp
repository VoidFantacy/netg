#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>

#include <argparse/argparse.hpp>
#include <nlohmann/json.hpp>
#include <omp.h>

#include <ACSG/IndexACSG.h>
#include <benches/datasets/DataLoader.hpp>
#include <faiss/impl/DistanceComputer.h>
#include <hnswlib/hnswlib.h>

using json = nlohmann::json;
using Clock = std::chrono::steady_clock;

namespace {

struct CountingDistanceComputer final : faiss::DistanceComputer {
    std::unique_ptr<faiss::DistanceComputer> inner;
    uint64_t count = 0;
    explicit CountingDistanceComputer(faiss::DistanceComputer* ptr) : inner(ptr) {}
    void set_query(const float* x) override { inner->set_query(x); }
    float operator()(faiss::idx_t i) override { ++count; return (*inner)(i); }
    float symmetric_dis(faiss::idx_t i, faiss::idx_t j) override { return inner->symmetric_dis(i, j); }
};

std::vector<int> parse_ints(const std::string& text) {
    std::vector<int> out; std::stringstream stream(text); std::string item;
    while (std::getline(stream, item, ',')) out.push_back(std::stoi(item));
    return out;
}

std::vector<int> load_i32(const std::string& path) {
    std::ifstream in(path, std::ios::binary | std::ios::ate);
    if (!in) throw std::runtime_error("cannot open int32 file: " + path);
    const size_t bytes = static_cast<size_t>(in.tellg());
    if (bytes == 0 || bytes % sizeof(int32_t)) throw std::runtime_error("bad int32 file: " + path);
    in.seekg(0); std::vector<int> values(bytes / sizeof(int32_t));
    in.read(reinterpret_cast<char*>(values.data()), static_cast<std::streamsize>(bytes));
    if (!in) throw std::runtime_error("failed to read: " + path);
    return values;
}

class FastRouter {
    std::unique_ptr<hnswlib::SpaceInterface<float>> space;
    std::unique_ptr<hnswlib::HierarchicalNSW<float>> graph;
public:
    FastRouter(const std::string& hubs_path, const std::string& ids_path, int dim, bool ip) {
        std::ifstream hubs(hubs_path, std::ios::binary | std::ios::ate);
        if (!hubs) throw std::runtime_error("cannot open prototypes: " + hubs_path);
        const size_t bytes = static_cast<size_t>(hubs.tellg());
        if (bytes == 0 || bytes % (sizeof(float) * static_cast<size_t>(dim)))
            throw std::runtime_error("bad prototype shape");
        const size_t count = bytes / (sizeof(float) * static_cast<size_t>(dim));
        hubs.seekg(0); std::vector<float> vectors(count * static_cast<size_t>(dim));
        hubs.read(reinterpret_cast<char*>(vectors.data()), static_cast<std::streamsize>(bytes));
        const auto ids = load_i32(ids_path);
        if (!hubs || ids.size() != count) throw std::runtime_error("prototype/id mismatch");
        if (ip) space = std::make_unique<hnswlib::InnerProductSpace>(dim);
        else space = std::make_unique<hnswlib::L2Space>(dim);
        graph = std::make_unique<hnswlib::HierarchicalNSW<float>>(space.get(), count, 16, 200);
        for (size_t i = 0; i < count; ++i) graph->addPoint(vectors.data() + i * dim, ids[i]);
    }
    std::pair<std::vector<int>, std::vector<float>> topk(const float* q, size_t k) const {
        auto heap = graph->searchKnn(q, k); std::vector<int> ids; std::vector<float> distances;
        while (!heap.empty()) { ids.push_back(static_cast<int>(heap.top().second)); distances.push_back(heap.top().first); heap.pop(); }
        std::reverse(ids.begin(), ids.end()); std::reverse(distances.begin(), distances.end());
        return {ids, distances};
    }
};

struct Result { std::array<faiss::idx_t, 10> ids{}; std::array<float, 10> distances{}; uint64_t ndc = 0; double recall = 0.0; };

double recall10(const std::array<faiss::idx_t, 10>& ids, const int64_t* gt) {
    int hits = 0;
    for (auto id : ids) for (int g = 0; g < 10; ++g) if (id == gt[g]) { ++hits; break; }
    return static_cast<double>(hits) / 10.0;
}

Result native_search(acsg::IndexACSGFlat& index, CountingDistanceComputer& dis, faiss::VisitedTable& vt,
                     std::vector<acsg::Neighbor>& retset, const float* q, const int64_t* gt,
                     const std::vector<int>& entries) {
    std::vector<acsg::EnterPoint> eps; for (int id : entries) eps.emplace_back(id, 1.0);
    Result out; dis.set_query(q); dis.count = 0; vt.advance();
    index.acsg.search_new(dis, 10, out.ids.data(), out.distances.data(), vt, 2, eps, &retset);
    out.ndc = dis.count; out.recall = recall10(out.ids, gt); return out;
}

Result traced_search(acsg::IndexACSGFlat& index, CountingDistanceComputer& dis, faiss::VisitedTable& vt,
                     std::vector<acsg::Neighbor>& retset, const float* q, const int64_t* gt,
                     const std::vector<int>& entries, acsg::SearchTrace& trace) {
    std::vector<acsg::EnterPoint> eps; for (int id : entries) eps.emplace_back(id, 1.0);
    Result out; dis.set_query(q); dis.count = 0; vt.advance();
    index.acsg.search_new_traced(dis, 10, out.ids.data(), out.distances.data(), vt, 2, eps, trace, gt, 10, &retset);
    out.ndc = dis.count; out.recall = recall10(out.ids, gt); return out;
}

json trace_json(const acsg::SearchTrace& t) {
    const auto missing = std::numeric_limits<uint64_t>::max();
    return {
        {"distance_evaluations", t.distance_evaluations}, {"evaluated_neighbor_count", t.evaluated_neighbor_count},
        {"expanded_count", t.expanded_count}, {"accepted_insertion_count", t.accepted_insertion_count},
        {"rejected_by_pool_bound_count", t.rejected_by_pool_bound_count}, {"rewind_count", t.rewind_count},
        {"rewind_span_sum", t.rewind_span_sum}, {"rewind_span_max", t.rewind_span_max},
        {"best_distance_improvement_count", t.best_distance_improvement_count}, {"best_distance_improvement_sum", t.best_distance_improvement_sum},
        {"pool_bound_improvement_count", t.pool_bound_improvement_count}, {"pool_bound_improvement_sum", t.pool_bound_improvement_sum},
        {"max_stagnation_expansions", t.max_stagnation_expansions}, {"stagnation_run_count", t.stagnation_run_count},
        {"stagnation_expansion_sum", t.stagnation_expansion_sum}, {"initial_best_distance", t.initial_best_distance},
        {"final_best_distance", t.final_best_distance}, {"final_frontier_gap", std::isnan(t.final_frontier_gap) ? json(nullptr) : json(t.final_frontier_gap)},
        {"final_pool_gap", std::isnan(t.final_pool_gap) ? json(nullptr) : json(t.final_pool_gap)},
        {"first_top10_gt_evaluation_ndc", t.first_topk_gt_evaluation_ndc == missing ? json(nullptr) : json(t.first_topk_gt_evaluation_ndc)},
        {"first_top10_gt_expansion", t.first_topk_gt_expansion == missing ? json(nullptr) : json(t.first_topk_gt_expansion)}
    };
}

bool identical(const Result& a, const Result& b) {
    if (a.ndc != b.ndc || a.ids != b.ids) return false;
    for (size_t i = 0; i < a.distances.size(); ++i) if (std::abs(a.distances[i] - b.distances[i]) > 1e-6f) return false;
    return true;
}

} // namespace

int main(int argc, char** argv) {
    argparse::ArgumentParser program("bench_finite_beam_trace");
    program.add_argument("--dataset").required(); program.add_argument("--index_file").required();
    program.add_argument("--candidate_ids").required(); program.add_argument("--prototype_hubs").required();
    program.add_argument("--prototype_ids").required(); program.add_argument("--output_file").required();
    program.add_argument("--query_type").default_value(std::string("drl_train"));
    program.add_argument("--query_offset").default_value(0).scan<'i', int>();
    program.add_argument("--max_queries").default_value(20).scan<'i', int>();
    program.add_argument("--candidate_count").default_value(8).scan<'i', int>();
    program.add_argument("--search_Ls").default_value(std::string("64,128"));
    program.add_argument("--threads").default_value(16).scan<'i', int>();
    program.add_argument("--verify_parity").default_value(false).implicit_value(true);
    try { program.parse_args(argc, argv); } catch (const std::exception& e) { std::cerr << e.what() << '\n' << program; return 2; }
    const auto dataset = program.get<std::string>("--dataset"); const auto query_type = program.get<std::string>("--query_type");
    const int offset = program.get<int>("--query_offset"), requested = program.get<int>("--max_queries"), candidate_count = program.get<int>("--candidate_count");
    const auto search_ls = parse_ints(program.get<std::string>("--search_Ls")); const bool verify_parity = program.get<bool>("--verify_parity");
    if (offset < 0 || requested < 1 || candidate_count < 1 || search_ls.empty()) throw std::runtime_error("invalid range or candidate count");
    omp_set_num_threads(program.get<int>("--threads"));

    DataLoader loader(dataset); auto [nq_all, queries] = loader.load_query(query_type); auto [gt_k, gt] = loader.load_gt(query_type);
    if (gt_k < 10 || static_cast<size_t>(offset) >= nq_all) throw std::runtime_error("need top-10 GT and valid query offset");
    const int nq = std::min<int>(requested, static_cast<int>(nq_all) - offset);
    const auto candidate_ids = load_i32(program.get<std::string>("--candidate_ids"));
    std::unordered_set<int> candidate_set(candidate_ids.begin(), candidate_ids.end());
    if (candidate_set.size() != candidate_ids.size()) throw std::runtime_error("candidate_ids contains duplicates");
    FastRouter router(program.get<std::string>("--prototype_hubs"), program.get<std::string>("--prototype_ids"), loader.dim(), loader.metric_type() == faiss::METRIC_INNER_PRODUCT);
    auto index = std::make_unique<acsg::IndexACSGFlat>(); index->loadACPG(program.get<std::string>("--index_file").c_str());
    std::vector<float>().swap(index->acsg.pheromone); std::vector<float>().swap(index->acsg.weight);

    json output = {{"schema_version", 1}, {"status", "running"}, {"dataset", dataset}, {"split", query_type},
                   {"query_offset", offset}, {"num_queries", nq}, {"candidate_count", candidate_count}, {"search_Ls", search_ls},
                   {"top_k", 10}, {"threads", program.get<int>("--threads")}, {"metric", loader.metric_name()},
                   {"normalization", loader.normalization()}, {"artifact_version", loader.artifact_version()},
                   {"heldout_accessed", false}, {"trace_design", "finite_beam_reachability_diagnostics/v1/trace_design.md"}, {"rows", json::array()}};
    std::vector<json> rows(static_cast<size_t>(nq * candidate_count * static_cast<int>(search_ls.size())));
    std::atomic<int> parity_failures{0}; const auto start = Clock::now();
    for (size_t lidx = 0; lidx < search_ls.size(); ++lidx) {
        const int L = search_ls[lidx]; if (L < 10) throw std::runtime_error("search_L must be at least 10"); index->acsg.search_L = L;
        #pragma omp parallel for schedule(dynamic)
        for (int local_q = 0; local_q < nq; ++local_q) {
            const int qid = offset + local_q; const float* q = queries.get() + static_cast<size_t>(qid) * loader.dim();
            const int64_t* truth = gt.get() + static_cast<size_t>(qid) * gt_k; auto [entries, prototype_distances] = router.topk(q, candidate_count);
            if (entries.size() != static_cast<size_t>(candidate_count)) throw std::runtime_error("router returned too few entries");
            for (int entry : entries) if (!candidate_set.count(entry)) throw std::runtime_error("router entry is outside candidate_ids");
            CountingDistanceComputer traced_dis(acsg::storage_distance_computer(index->storage)); faiss::VisitedTable traced_vt(index->ntotal); std::vector<acsg::Neighbor> traced_retset;
            CountingDistanceComputer baseline_dis(acsg::storage_distance_computer(index->storage)); faiss::VisitedTable baseline_vt(index->ntotal); std::vector<acsg::Neighbor> baseline_retset;
            CountingDistanceComputer raw_dis(acsg::storage_distance_computer(index->storage)); raw_dis.set_query(q);
            const auto fast3 = native_search(*index, baseline_dis, baseline_vt, baseline_retset, q, truth, {entries[0], entries.size() > 1 ? entries[1] : entries[0], entries.size() > 2 ? entries[2] : entries[0]});
            const auto medoid = native_search(*index, baseline_dis, baseline_vt, baseline_retset, q, truth, {index->acsg.enterpoint});
            for (int rank = 0; rank < candidate_count; ++rank) {
                acsg::SearchTrace trace; const auto traced = traced_search(*index, traced_dis, traced_vt, traced_retset, q, truth, {entries[rank]}, trace);
                bool parity_ok = true;
                if (verify_parity) { const auto native = native_search(*index, baseline_dis, baseline_vt, baseline_retset, q, truth, {entries[rank]}); parity_ok = identical(traced, native); if (!parity_ok) ++parity_failures; }
                const size_t pos = (lidx * static_cast<size_t>(nq) + local_q) * candidate_count + rank;
                rows[pos] = {{"query_id", qid}, {"entry_id", entries[rank]}, {"geometry_rank", rank}, {"prototype_distance", prototype_distances[rank]},
                             {"raw_entry_distance", raw_dis(entries[rank])}, {"search_L", L}, {"top_k", 10}, {"result_ids", traced.ids}, {"result_distances", traced.distances},
                             {"recall_at_10", traced.recall}, {"graph_ndc", traced.ndc}, {"fast_top3_recall_at_10", fast3.recall}, {"fast_top3_graph_ndc", fast3.ndc},
                             {"medoid_recall_at_10", medoid.recall}, {"medoid_graph_ndc", medoid.ndc}, {"trace", trace_json(trace)}, {"parity_ok", parity_ok}};
            }
        }
    }
    for (const auto& row : rows) output["rows"].push_back(row);
    output["parity_failures"] = parity_failures.load(); output["wall_seconds"] = std::chrono::duration<double>(Clock::now() - start).count();
    output["status"] = parity_failures.load() == 0 ? "complete" : "parity_failed";
    const std::filesystem::path output_path = program.get<std::string>("--output_file"); std::filesystem::create_directories(output_path.parent_path());
    std::ofstream out(output_path); out << output.dump(2) << '\n'; if (!out) throw std::runtime_error("failed to write output");
    std::cout << "FINITE_BEAM_TRACE_COMPLETE rows=" << rows.size() << " parity_failures=" << parity_failures.load() << " output=" << output_path << '\n';
    return parity_failures.load() == 0 ? 0 : 3;
}

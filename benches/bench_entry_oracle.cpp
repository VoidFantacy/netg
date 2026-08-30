#include <algorithm>
#include <array>
#include <atomic>
#include <bitset>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <numeric>
#include <sstream>
#include <string>
#include <unordered_map>
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
using Mask = std::bitset<100>;

namespace {

struct CountingDistanceComputer final : faiss::DistanceComputer {
    std::unique_ptr<faiss::DistanceComputer> inner;
    uint64_t count = 0;

    explicit CountingDistanceComputer(faiss::DistanceComputer* ptr)
        : inner(ptr) {}
    void set_query(const float* x) override { inner->set_query(x); }
    float operator()(faiss::idx_t i) override { ++count; return (*inner)(i); }
    float symmetric_dis(faiss::idx_t i, faiss::idx_t j) override {
        return inner->symmetric_dis(i, j);
    }
};

struct SearchResult {
    Mask hits;
    double recall = 0.0;
    uint64_t ndc = 0;
    double latency_us = 0.0;
};

std::vector<int> load_i32(const std::string& path) {
    std::ifstream in(path, std::ios::binary | std::ios::ate);
    if (!in) throw std::runtime_error("cannot open ids: " + path);
    const auto bytes = static_cast<size_t>(in.tellg());
    if (bytes % sizeof(int32_t)) throw std::runtime_error("bad int32 file size: " + path);
    in.seekg(0);
    std::vector<int> out(bytes / sizeof(int32_t));
    in.read(reinterpret_cast<char*>(out.data()), bytes);
    return out;
}

std::vector<int> parse_ints(const std::string& text) {
    std::vector<int> out;
    std::stringstream ss(text);
    std::string token;
    while (std::getline(ss, token, ',')) out.push_back(std::stoi(token));
    return out;
}

std::vector<std::pair<int, int>> parse_pairs(const std::string& text) {
    std::vector<std::pair<int, int>> out;
    std::stringstream ss(text);
    std::string token;
    while (std::getline(ss, token, ',')) {
        const auto pos = token.find(':');
        if (pos == std::string::npos) throw std::runtime_error("budget pair must be target:reroute");
        out.emplace_back(std::stoi(token.substr(0, pos)), std::stoi(token.substr(pos + 1)));
    }
    return out;
}

Mask hit_mask(const faiss::idx_t* result, int k, const int64_t* gt) {
    Mask mask;
    for (int r = 0; r < k; ++r) {
        if (result[r] < 0) continue;
        for (int g = 0; g < k; ++g) {
            if (result[r] == gt[g]) { mask.set(g); break; }
        }
    }
    return mask;
}

double merged_recall(
    const std::vector<int>& ids_a, const std::vector<float>& distances_a,
    const std::vector<int>& ids_b, const std::vector<float>& distances_b,
    const int64_t* gt, int k)
{
    std::unordered_map<int, float> best;
    for (size_t i = 0; i < ids_a.size(); ++i)
        if (ids_a[i] >= 0) best[ids_a[i]] = distances_a[i];
    for (size_t i = 0; i < ids_b.size(); ++i) {
        if (ids_b[i] < 0) continue;
        auto it = best.find(ids_b[i]);
        if (it == best.end() || distances_b[i] < it->second) best[ids_b[i]] = distances_b[i];
    }
    std::vector<std::pair<float, int>> ranked;
    ranked.reserve(best.size());
    for (const auto& [id, distance] : best) ranked.emplace_back(distance, id);
    std::sort(ranked.begin(), ranked.end());
    int hits = 0;
    for (int i = 0; i < std::min<int>(k, ranked.size()); ++i) {
        for (int g = 0; g < k; ++g) if (ranked[i].second == gt[g]) { ++hits; break; }
    }
    return static_cast<double>(hits) / k;
}

SearchResult search_once(
    acsg::IndexACSGFlat& index,
    CountingDistanceComputer& dis,
    faiss::VisitedTable& vt,
    std::vector<acsg::Neighbor>& retset,
    const float* query,
    const int64_t* gt,
    int k,
    const std::vector<int>& entries,
    std::vector<int>* result_ids = nullptr,
    std::vector<float>* result_distances = nullptr)
{
    std::array<faiss::idx_t, 100> ids;
    std::array<float, 100> distances;
    std::vector<acsg::EnterPoint> eps;
    eps.reserve(entries.size());
    for (int id : entries) eps.emplace_back(id, 1.0);

    dis.set_query(query);
    dis.count = 0;
    vt.advance();
    const auto begin = Clock::now();
    index.acsg.search_new(dis, k, ids.data(), distances.data(), vt, 2, eps, &retset);
    const auto end = Clock::now();

    SearchResult out;
    out.hits = hit_mask(ids.data(), k, gt);
    out.recall = static_cast<double>(out.hits.count()) / k;
    out.ndc = dis.count;
    out.latency_us = std::chrono::duration<double, std::micro>(end - begin).count();
    if (result_ids) result_ids->assign(ids.begin(), ids.begin() + k);
    if (result_distances) result_distances->assign(distances.begin(), distances.begin() + k);
    return out;
}

class FastRouter {
    std::unique_ptr<hnswlib::SpaceInterface<float>> space_;
    std::unique_ptr<hnswlib::HierarchicalNSW<float>> graph_;
public:
    FastRouter(const std::string& hubs_path, const std::string& ids_path, int dim, bool ip) {
        std::ifstream hubs(hubs_path, std::ios::binary | std::ios::ate);
        if (!hubs) throw std::runtime_error("cannot open prototypes: " + hubs_path);
        const size_t bytes = static_cast<size_t>(hubs.tellg());
        const size_t count = bytes / (sizeof(float) * dim);
        hubs.seekg(0);
        std::vector<float> vectors(count * dim);
        hubs.read(reinterpret_cast<char*>(vectors.data()), bytes);
        const auto ids = load_i32(ids_path);
        if (ids.size() != count) throw std::runtime_error("prototype/id count mismatch");
        if (ip) space_ = std::make_unique<hnswlib::InnerProductSpace>(dim);
        else space_ = std::make_unique<hnswlib::L2Space>(dim);
        graph_ = std::make_unique<hnswlib::HierarchicalNSW<float>>(space_.get(), count, 16, 200);
        for (size_t i = 0; i < count; ++i) graph_->addPoint(vectors.data() + i * dim, ids[i]);
    }

    std::vector<int> topk(const float* query, size_t k) const {
        auto heap = graph_->searchKnn(query, k);
        std::vector<int> ids;
        while (!heap.empty()) { ids.push_back(static_cast<int>(heap.top().second)); heap.pop(); }
        std::reverse(ids.begin(), ids.end());
        return ids;
    }

    std::pair<std::vector<int>, std::vector<float>> topk_with_distances(
        const float* query, size_t k) const {
        auto heap = graph_->searchKnn(query, k);
        std::vector<int> ids;
        std::vector<float> distances;
        while (!heap.empty()) {
            ids.push_back(static_cast<int>(heap.top().second));
            distances.push_back(heap.top().first);
            heap.pop();
        }
        std::reverse(ids.begin(), ids.end());
        std::reverse(distances.begin(), distances.end());
        return {ids, distances};
    }
};

struct Aggregate {
    double recall_sum = 0.0;
    double ndc_sum = 0.0;
    double latency_sum = 0.0;
    uint64_t samples = 0;
    void add(const SearchResult& value) {
        recall_sum += value.recall;
        ndc_sum += value.ndc;
        latency_sum += value.latency_us;
        ++samples;
    }
    json to_json() const {
        return {{"mean_recall", recall_sum / samples},
                {"mean_graph_ndc", ndc_sum / samples},
                {"mean_graph_latency_us", latency_sum / samples},
                {"samples", samples}};
    }
};

} // namespace

int main(int argc, char** argv) {
    setvbuf(stdout, nullptr, _IONBF, 0);
    argparse::ArgumentParser program("bench_entry_oracle");
    program.add_argument("--dataset").required();
    program.add_argument("--index_file").required();
    program.add_argument("--candidate_ids").required();
    program.add_argument("--prototype_hubs").required();
    program.add_argument("--prototype_ids").required();
    program.add_argument("--extra_prototype_hubs").default_value(std::string(""));
    program.add_argument("--extra_prototype_ids").default_value(std::string(""));
    program.add_argument("--extra_routes").default_value(std::string(""));
    program.add_argument("--extra_method").default_value(std::string("SearchAware_Prototype_Top3"));
    program.add_argument("--extra_top_m").default_value(3).scan<'i', int>();
    program.add_argument("--skip_oracle").default_value(false).implicit_value(true);
    program.add_argument("--generate_sparse_utility").default_value(false).implicit_value(true);
    program.add_argument("--utility_shortlist").default_value(32).scan<'i', int>();
    program.add_argument("--generate_probe_trace").default_value(false).implicit_value(true);
    program.add_argument("--probe_Ls").default_value(std::string("10,16,32"));
    program.add_argument("--generate_budget_reroute").default_value(false).implicit_value(true);
    program.add_argument("--probe_L").default_value(10).scan<'i', int>();
    program.add_argument("--budget_pairs").default_value(std::string("64:46,128:108"));
    program.add_argument("--output_file").required();
    program.add_argument("--query_type").default_value(std::string("validation"));
    program.add_argument("--max_queries").default_value(1000).scan<'i', int>();
    program.add_argument("--search_Ls").default_value(std::string("64,128,200,400"));
    program.add_argument("--top_ks").default_value(std::string("1,10,100"));
    program.add_argument("--num_runs").default_value(3).scan<'i', int>();
    program.add_argument("--threads").default_value(16).scan<'i', int>();
    try { program.parse_args(argc, argv); }
    catch (const std::exception& e) { std::cerr << e.what() << '\n' << program; return 2; }

    const auto dataset = program.get<std::string>("--dataset");
    const auto index_file = program.get<std::string>("--index_file");
    const auto candidate_file = program.get<std::string>("--candidate_ids");
    const auto prototype_hubs = program.get<std::string>("--prototype_hubs");
    const auto prototype_ids = program.get<std::string>("--prototype_ids");
    const auto extra_prototype_hubs = program.get<std::string>("--extra_prototype_hubs");
    const auto extra_prototype_ids = program.get<std::string>("--extra_prototype_ids");
    const auto extra_routes = program.get<std::string>("--extra_routes");
    const auto extra_method = program.get<std::string>("--extra_method");
    const int extra_top_m = program.get<int>("--extra_top_m");
    const bool skip_oracle = program.get<bool>("--skip_oracle");
    const bool generate_sparse_utility = program.get<bool>("--generate_sparse_utility");
    const int utility_shortlist = program.get<int>("--utility_shortlist");
    const bool generate_probe_trace = program.get<bool>("--generate_probe_trace");
    const auto probe_ls = parse_ints(program.get<std::string>("--probe_Ls"));
    const bool generate_budget_reroute = program.get<bool>("--generate_budget_reroute");
    const int probe_l = program.get<int>("--probe_L");
    const auto budget_pairs = parse_pairs(program.get<std::string>("--budget_pairs"));
    const auto output_file = program.get<std::string>("--output_file");
    const auto query_type = program.get<std::string>("--query_type");
    const auto search_ls = parse_ints(program.get<std::string>("--search_Ls"));
    const auto top_ks = parse_ints(program.get<std::string>("--top_ks"));
    const int runs = program.get<int>("--num_runs");
    const int threads = program.get<int>("--threads");

    for (int k : top_ks) if (k < 1 || k > 100) throw std::runtime_error("top_k must be 1..100");
    omp_set_num_threads(threads);

    DataLoader loader(dataset);
    auto [nq_all, queries] = loader.load_query(query_type);
    auto [gt_k, gt] = loader.load_gt(query_type);
    const int nq = std::min<int>(program.get<int>("--max_queries"), nq_all);
    if (gt_k < 100) throw std::runtime_error("oracle requires top-100 GT");

    auto index = std::make_unique<acsg::IndexACSGFlat>();
    index->loadACPG(index_file.c_str());
    std::vector<float>().swap(index->acsg.pheromone);
    std::vector<float>().swap(index->acsg.weight);
    const auto candidates = load_i32(candidate_file);
    FastRouter fast_router(prototype_hubs, prototype_ids, loader.dim(),
                           loader.metric_type() == faiss::METRIC_INNER_PRODUCT);
    std::vector<std::vector<int>> fast_entries(nq);
    for (int q = 0; q < nq; ++q) fast_entries[q] = fast_router.topk(queries.get() + q * loader.dim(), 3);
    std::vector<std::vector<int>> extra_entries;
    std::unique_ptr<FastRouter> extra_router;
    if (!extra_prototype_hubs.empty() && !extra_routes.empty())
        throw std::runtime_error("provide either extra prototypes or extra routes, not both");
    if (!extra_prototype_hubs.empty()) {
        if (extra_prototype_ids.empty()) throw std::runtime_error("extra prototype ids missing");
        extra_router = std::make_unique<FastRouter>(extra_prototype_hubs, extra_prototype_ids,
            loader.dim(), loader.metric_type() == faiss::METRIC_INNER_PRODUCT);
        extra_entries.resize(nq);
        if (extra_top_m < 1 || extra_top_m > 3) throw std::runtime_error("extra_top_m must be 1..3");
        for (int q = 0; q < nq; ++q)
            extra_entries[q] = extra_router->topk(queries.get() + q * loader.dim(), extra_top_m);
    } else if (!extra_routes.empty()) {
        const auto flat_routes = load_i32(extra_routes);
        if (extra_top_m < 1 || flat_routes.size() != static_cast<size_t>(nq * extra_top_m))
            throw std::runtime_error("extra route count mismatch");
        extra_entries.resize(nq);
        for (int q = 0; q < nq; ++q) {
            extra_entries[q].assign(flat_routes.begin() + q * extra_top_m,
                                    flat_routes.begin() + (q + 1) * extra_top_m);
        }
    }

    json output = {
        {"schema_version", 1}, {"status", "running"}, {"dataset", dataset},
        {"split", query_type}, {"num_queries", nq}, {"candidate_count", candidates.size()},
        {"search_Ls", search_ls}, {"top_ks", top_ks}, {"num_runs", runs},
        {"threads", threads}, {"metric", loader.metric_name()},
        {"artifact_version", loader.artifact_version()},
        {"oracle_definition", "single=exhaustive current-hub true-search best; top3=greedy union of single-entry GT-hit masks then true multi-entry replay"},
        {"results", json::array()}
    };
    std::filesystem::create_directories(std::filesystem::path(output_file).parent_path());

    if (generate_budget_reroute) {
        struct StoredSearch {
            double recall = 0.0;
            uint64_t ndc = 0;
            std::vector<int> ids;
            std::vector<float> distances;
        };
        output["oracle_definition"] = "always-probe plus Fast restart or shortlist-oracle reroute; merged top-10; graph frozen";
        output["probe_L"] = probe_l;
        output["budget_pairs"] = json::array();
        for (const auto& [target_l, reroute_l] : budget_pairs) {
            std::vector<StoredSearch> baseline(nq), probe(nq);
            index->acsg.search_L = target_l;
            #pragma omp parallel for schedule(static)
            for (int q = 0; q < nq; ++q) {
                CountingDistanceComputer dis(acsg::storage_distance_computer(index->storage));
                faiss::VisitedTable vt(index->ntotal);
                std::vector<acsg::Neighbor> retset;
                auto value = search_once(*index, dis, vt, retset, queries.get() + q * loader.dim(),
                    gt.get() + q * gt_k, 10, fast_entries[q], &baseline[q].ids, &baseline[q].distances);
                baseline[q].recall = value.recall; baseline[q].ndc = value.ndc;
            }
            index->acsg.search_L = probe_l;
            #pragma omp parallel for schedule(static)
            for (int q = 0; q < nq; ++q) {
                CountingDistanceComputer dis(acsg::storage_distance_computer(index->storage));
                faiss::VisitedTable vt(index->ntotal);
                std::vector<acsg::Neighbor> retset;
                auto value = search_once(*index, dis, vt, retset, queries.get() + q * loader.dim(),
                    gt.get() + q * gt_k, 10, fast_entries[q], &probe[q].ids, &probe[q].distances);
                probe[q].recall = value.recall; probe[q].ndc = value.ndc;
            }
            index->acsg.search_L = reroute_l;
            std::vector<json> rows(nq);
            #pragma omp parallel for schedule(dynamic)
            for (int q = 0; q < nq; ++q) {
                CountingDistanceComputer dis(acsg::storage_distance_computer(index->storage));
                faiss::VisitedTable vt(index->ntotal);
                std::vector<acsg::Neighbor> retset;
                std::vector<int> restart_ids;
                std::vector<float> restart_distances;
                const int64_t* truth = gt.get() + q * gt_k;
                const float* query = queries.get() + q * loader.dim();
                auto restart = search_once(*index, dis, vt, retset, query, truth, 10, fast_entries[q],
                                           &restart_ids, &restart_distances);
                const double restart_merged = merged_recall(probe[q].ids, probe[q].distances,
                    restart_ids, restart_distances, truth, 10);
                double best_recall = -1.0;
                uint64_t best_ndc = std::numeric_limits<uint64_t>::max();
                int best_entry = -1;
                const auto shortlist = fast_router.topk(query, utility_shortlist);
                std::vector<double> candidate_merged_recalls;
                std::vector<uint64_t> candidate_total_ndcs;
                std::vector<std::vector<double>> candidate_topology_features;
                candidate_merged_recalls.reserve(shortlist.size());
                candidate_total_ndcs.reserve(shortlist.size());
                candidate_topology_features.reserve(shortlist.size());
                std::unordered_set<int> probe_ids_set(probe[q].ids.begin(), probe[q].ids.end());
                probe_ids_set.erase(-1);
                std::unordered_set<int> probe_neighbor_set;
                for (int probe_id : probe_ids_set) {
                    for (int m = 0; m < index->acsg.final_graph->K; ++m) {
                        const int neighbor = index->acsg.final_graph->at(probe_id, m);
                        if (neighbor >= 0 && neighbor < index->ntotal) probe_neighbor_set.insert(neighbor);
                    }
                }
                for (int entry : shortlist) {
                    std::vector<int> candidate_ids;
                    std::vector<float> candidate_distances;
                    auto candidate = search_once(*index, dis, vt, retset, query, truth, 10, {entry},
                                                 &candidate_ids, &candidate_distances);
                    const double recall = merged_recall(probe[q].ids, probe[q].distances,
                        candidate_ids, candidate_distances, truth, 10);
                    const uint64_t total_ndc = probe[q].ndc + candidate.ndc;
                    candidate_merged_recalls.push_back(recall);
                    candidate_total_ndcs.push_back(total_ndc);
                    int valid_degree = 0;
                    int probe_hits = 0;
                    int frontier_overlap = 0;
                    double weighted_probe_hits = 0.0;
                    for (int m = 0; m < index->acsg.final_graph->K; ++m) {
                        const int neighbor = index->acsg.final_graph->at(entry, m);
                        if (neighbor < 0 || neighbor >= index->ntotal) continue;
                        ++valid_degree;
                        if (probe_ids_set.count(neighbor)) {
                            ++probe_hits;
                            for (size_t rank = 0; rank < probe[q].ids.size(); ++rank)
                                if (probe[q].ids[rank] == neighbor) weighted_probe_hits += 1.0 / (rank + 1.0);
                        }
                        if (probe_neighbor_set.count(neighbor)) ++frontier_overlap;
                    }
                    const bool entry_in_probe = probe_ids_set.count(entry) > 0;
                    const bool entry_adjacent_to_probe = probe_neighbor_set.count(entry) > 0;
                    const int min_hop = entry_in_probe ? 0 : ((probe_hits > 0 || entry_adjacent_to_probe) ? 1 : (frontier_overlap > 0 ? 2 : 3));
                    candidate_topology_features.push_back({
                        entry_in_probe ? 1.0 : 0.0,
                        entry_adjacent_to_probe ? 1.0 : 0.0,
                        probe_hits / 10.0,
                        frontier_overlap / static_cast<double>(std::max(valid_degree, 1)),
                        weighted_probe_hits,
                        min_hop / 3.0,
                        valid_degree / static_cast<double>(index->acsg.final_graph->K)
                    });
                    if (recall > best_recall || (recall == best_recall && total_ndc < best_ndc)) {
                        best_recall = recall; best_ndc = total_ndc; best_entry = entry;
                    }
                }
                rows[q] = {
                    {"query_id", q}, {"baseline_recall", baseline[q].recall},
                    {"baseline_graph_ndc", baseline[q].ndc}, {"probe_recall", probe[q].recall},
                    {"probe_graph_ndc", probe[q].ndc}, {"restart_merged_recall", restart_merged},
                    {"restart_total_graph_ndc", probe[q].ndc + restart.ndc},
                    {"oracle_reroute_merged_recall", best_recall},
                    {"oracle_reroute_total_graph_ndc", best_ndc}, {"oracle_reroute_entry_id", best_entry}
                    ,{"candidate_entry_ids", shortlist}
                    ,{"candidate_merged_recalls", candidate_merged_recalls}
                    ,{"candidate_total_graph_ndcs", candidate_total_ndcs}
                    ,{"candidate_topology_features", candidate_topology_features}
                };
            }
            output["budget_pairs"].push_back({{"target_L", target_l}, {"reroute_L", reroute_l},
                                               {"queries", std::move(rows)}});
            std::ofstream checkpoint(output_file);
            checkpoint << output.dump(2);
        }
        output["results"] = json::array();
        output["status"] = "complete";
        std::ofstream final_out(output_file);
        final_out << output.dump(2);
        std::cout << "BUDGET_REROUTE_COMPLETE output=" << output_file << std::endl;
        return 0;
    }

    if (generate_probe_trace) {
        output["oracle_definition"] = "GT-free online features from Fast router and frozen-graph early probes";
        output["probe_Ls"] = probe_ls;
        output["probe_top_k"] = 10;
        std::vector<json> query_rows(nq);
        for (int q = 0; q < nq; ++q) {
            const auto [router_ids, router_distances] =
                fast_router.topk_with_distances(queries.get() + q * loader.dim(), 32);
            query_rows[q] = {{"query_id", q}, {"router_entry_ids", router_ids},
                             {"router_distances", router_distances}, {"probes", json::array()}};
        }
        for (int L : probe_ls) {
            index->acsg.search_L = L;
            std::cout << "PROBE_TRACE_STAGE L=" << L << " queries=" << nq << std::endl;
            #pragma omp parallel for schedule(static)
            for (int q = 0; q < nq; ++q) {
                CountingDistanceComputer dis(acsg::storage_distance_computer(index->storage));
                faiss::VisitedTable vt(index->ntotal);
                std::vector<acsg::Neighbor> retset;
                std::vector<int> result_ids;
                std::vector<float> result_distances;
                const auto value = search_once(
                    *index, dis, vt, retset, queries.get() + q * loader.dim(),
                    gt.get() + q * gt_k, 10, fast_entries[q], &result_ids, &result_distances);
                query_rows[q]["probes"].push_back({
                    {"search_L", L}, {"graph_ndc", value.ndc}, {"recall", value.recall},
                    {"result_ids", result_ids}, {"result_distances", result_distances}
                });
            }
        }
        output["probe_queries"] = std::move(query_rows);
        output["results"] = json::array();
        output["status"] = "complete";
        std::ofstream final_out(output_file);
        final_out << output.dump(2);
        std::cout << "PROBE_TRACE_COMPLETE output=" << output_file << std::endl;
        return 0;
    }

    if (generate_sparse_utility) {
        if (utility_shortlist < 2 || utility_shortlist > static_cast<int>(candidates.size()))
            throw std::runtime_error("utility_shortlist must be between 2 and candidate_count");
        output["oracle_definition"] = "sparse continuous utility over current Fast prototype shortlist";
        output["utility_shortlist"] = utility_shortlist;
        for (int L : search_ls) {
            index->acsg.search_L = L;
            for (int k : top_ks) {
                std::cout << "UTILITY_STAGE L=" << L << " K=" << k << " queries=" << nq
                          << " shortlist=" << utility_shortlist << std::endl;
                std::vector<json> query_rows(nq);
                #pragma omp parallel for schedule(dynamic)
                for (int q = 0; q < nq; ++q) {
                    CountingDistanceComputer dis(acsg::storage_distance_computer(index->storage));
                    faiss::VisitedTable vt(index->ntotal);
                    std::vector<acsg::Neighbor> retset;
                    const float* query = queries.get() + q * loader.dim();
                    const int64_t* truth = gt.get() + q * gt_k;
                    const auto shortlist = fast_router.topk(query, utility_shortlist);
                    std::vector<double> recalls;
                    std::vector<uint64_t> ndcs;
                    recalls.reserve(shortlist.size());
                    ndcs.reserve(shortlist.size());
                    for (int entry : shortlist) {
                        const auto value = search_once(*index, dis, vt, retset, query, truth, k, {entry});
                        recalls.push_back(value.recall);
                        ndcs.push_back(value.ndc);
                    }
                    const auto medoid = search_once(*index, dis, vt, retset, query, truth, k,
                                                    {index->acsg.enterpoint});
                    const auto fast3 = search_once(*index, dis, vt, retset, query, truth, k,
                                                   fast_router.topk(query, 3));
                    query_rows[q] = {
                        {"query_id", q}, {"candidate_entry_ids", shortlist},
                        {"candidate_recalls", recalls}, {"candidate_graph_ndcs", ndcs},
                        {"medoid_recall", medoid.recall}, {"medoid_graph_ndc", medoid.ndc},
                        {"fast_top3_recall", fast3.recall}, {"fast_top3_graph_ndc", fast3.ndc}
                    };
                }
                output["results"].push_back({{"search_L", L}, {"top_k", k},
                                              {"queries", std::move(query_rows)}});
                std::ofstream checkpoint(output_file);
                checkpoint << output.dump(2);
            }
        }
        output["status"] = "complete";
        std::ofstream final_out(output_file);
        final_out << output.dump(2);
        std::cout << "SPARSE_UTILITY_COMPLETE output=" << output_file << std::endl;
        return 0;
    }

    if (skip_oracle) {
        output["oracle_definition"] = "skipped; router comparison only";
        for (int L : search_ls) {
            index->acsg.search_L = L;
            for (int k : top_ks) {
                const int method_count = extra_entries.empty() ? 2 : 3;
                std::vector<Aggregate> totals(method_count);
                std::vector<std::string> names = {"Medoid", "Fast_Prototype_Top3"};
                if (!extra_entries.empty()) names.push_back(extra_method);
                for (int run = 0; run < runs; ++run) {
                    #pragma omp parallel
                    {
                        std::vector<Aggregate> local(method_count);
                        CountingDistanceComputer dis(acsg::storage_distance_computer(index->storage));
                        faiss::VisitedTable vt(index->ntotal);
                        std::vector<acsg::Neighbor> retset;
                        #pragma omp for schedule(static)
                        for (int q = 0; q < nq; ++q) {
                            const float* query = queries.get() + q * loader.dim();
                            const int64_t* truth = gt.get() + q * gt_k;
                            local[0].add(search_once(*index, dis, vt, retset, query, truth, k, {index->acsg.enterpoint}));
                            local[1].add(search_once(*index, dis, vt, retset, query, truth, k, fast_entries[q]));
                            if (method_count == 3)
                                local[2].add(search_once(*index, dis, vt, retset, query, truth, k, extra_entries[q]));
                        }
                        #pragma omp critical
                        for (int m = 0; m < method_count; ++m) {
                            totals[m].recall_sum += local[m].recall_sum;
                            totals[m].ndc_sum += local[m].ndc_sum;
                            totals[m].latency_sum += local[m].latency_sum;
                            totals[m].samples += local[m].samples;
                        }
                    }
                }
                json row = {{"search_L", L}, {"top_k", k}, {"methods", json::array()}};
                for (int m = 0; m < method_count; ++m) {
                    auto method = totals[m].to_json();
                    method["method"] = names[m];
                    row["methods"].push_back(method);
                }
                output["results"].push_back(row);
                std::ofstream checkpoint(output_file);
                checkpoint << output.dump(2);
            }
        }
        output["status"] = "complete";
        std::ofstream final_out(output_file);
        final_out << output.dump(2);
        std::cout << "ROUTER_COMPARISON_COMPLETE output=" << output_file << std::endl;
        return 0;
    }

    for (int L : search_ls) {
        index->acsg.search_L = L;
        for (int k : top_ks) {
            std::cout << "ORACLE_STAGE L=" << L << " K=" << k << " queries=" << nq
                      << " candidates=" << candidates.size() << std::endl;
            std::vector<int> best_single(nq, -1);
            std::vector<std::array<int, 3>> best_diverse(nq);
            std::atomic<int> finished{0};

            #pragma omp parallel for schedule(dynamic)
            for (int q = 0; q < nq; ++q) {
                CountingDistanceComputer dis(acsg::storage_distance_computer(index->storage));
                faiss::VisitedTable vt(index->ntotal);
                std::vector<acsg::Neighbor> retset;
                std::vector<Mask> masks(candidates.size());
                std::vector<uint64_t> ndcs(candidates.size());
                size_t best = 0;
                for (size_t c = 0; c < candidates.size(); ++c) {
                    auto value = search_once(*index, dis, vt, retset,
                        queries.get() + q * loader.dim(), gt.get() + q * gt_k, k,
                        std::vector<int>{candidates[c]});
                    masks[c] = value.hits;
                    ndcs[c] = value.ndc;
                    if (masks[c].count() > masks[best].count() ||
                        (masks[c].count() == masks[best].count() && ndcs[c] < ndcs[best])) best = c;
                }
                best_single[q] = candidates[best];
                Mask covered;
                std::vector<char> used(candidates.size(), 0);
                for (int slot = 0; slot < 3; ++slot) {
                    size_t choice = candidates.size();
                    size_t best_gain = 0, best_total = 0;
                    for (size_t c = 0; c < candidates.size(); ++c) if (!used[c]) {
                        const size_t gain = (masks[c] & ~covered).count();
                        const size_t total = masks[c].count();
                        if (choice == candidates.size() || gain > best_gain ||
                            (gain == best_gain && total > best_total) ||
                            (gain == best_gain && total == best_total && ndcs[c] < ndcs[choice])) {
                            choice = c; best_gain = gain; best_total = total;
                        }
                    }
                    used[choice] = 1;
                    covered |= masks[choice];
                    best_diverse[q][slot] = candidates[choice];
                }
                const int done = ++finished;
                if (done % 100 == 0 || done == nq)
                    std::cout << "ORACLE_PROGRESS L=" << L << " K=" << k << " done=" << done << "/" << nq << std::endl;
            }

            std::array<Aggregate, 4> totals;
            std::array<std::string, 4> names = {"Medoid", "Fast_Prototype_Top3", "CurrentHub_Single_Oracle", "CurrentHub_Diverse_Top3_GreedyProxy"};
            for (int run = 0; run < runs; ++run) {
                #pragma omp parallel
                {
                    std::array<Aggregate, 4> local;
                    CountingDistanceComputer dis(acsg::storage_distance_computer(index->storage));
                    faiss::VisitedTable vt(index->ntotal);
                    std::vector<acsg::Neighbor> retset;
                    #pragma omp for schedule(static)
                    for (int q = 0; q < nq; ++q) {
                        const float* query = queries.get() + q * loader.dim();
                        const int64_t* truth = gt.get() + q * gt_k;
                        local[0].add(search_once(*index, dis, vt, retset, query, truth, k, {index->acsg.enterpoint}));
                        local[1].add(search_once(*index, dis, vt, retset, query, truth, k, fast_entries[q]));
                        local[2].add(search_once(*index, dis, vt, retset, query, truth, k, {best_single[q]}));
                        local[3].add(search_once(*index, dis, vt, retset, query, truth, k,
                            {best_diverse[q][0], best_diverse[q][1], best_diverse[q][2]}));
                    }
                    #pragma omp critical
                    for (int m = 0; m < 4; ++m) {
                        totals[m].recall_sum += local[m].recall_sum;
                        totals[m].ndc_sum += local[m].ndc_sum;
                        totals[m].latency_sum += local[m].latency_sum;
                        totals[m].samples += local[m].samples;
                    }
                }
            }

            json row = {{"search_L", L}, {"top_k", k}, {"methods", json::array()}};
            for (int m = 0; m < 4; ++m) {
                auto method = totals[m].to_json();
                method["method"] = names[m];
                row["methods"].push_back(method);
            }
            row["selected_single_entry_ids"] = best_single;
            row["selected_diverse_top3_entry_ids"] = best_diverse;
            output["results"].push_back(row);
            std::ofstream checkpoint(output_file);
            checkpoint << output.dump(2);
        }
    }
    output["status"] = "complete";
    std::ofstream final_out(output_file);
    final_out << output.dump(2);
    std::cout << "ORACLE_COMPLETE output=" << output_file << std::endl;
    return 0;
}

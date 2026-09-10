#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <numeric>
#include <sstream>
#include <string>
#include <unordered_map>
#include <utility>
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

thread_local uint64_t* tls_routing_distance_counter = nullptr;

struct CountingSpaceParam {
    hnswlib::DISTFUNC<float> inner = nullptr;
    void* inner_param = nullptr;
};

float counted_hnsw_distance(const void* a, const void* b, const void* raw_param) {
    if (tls_routing_distance_counter) ++(*tls_routing_distance_counter);
    const auto* param = static_cast<const CountingSpaceParam*>(raw_param);
    return param->inner(a, b, param->inner_param);
}

class CountingInnerProductSpace final : public hnswlib::SpaceInterface<float> {
    hnswlib::InnerProductSpace inner_;
    CountingSpaceParam param_;

public:
    explicit CountingInnerProductSpace(size_t dim) : inner_(dim) {
        param_.inner = inner_.get_dist_func();
        param_.inner_param = inner_.get_dist_func_param();
    }

    size_t get_data_size() override { return inner_.get_data_size(); }
    hnswlib::DISTFUNC<float> get_dist_func() override { return counted_hnsw_distance; }
    void* get_dist_func_param() override { return &param_; }
};

class RoutingCounterScope {
    uint64_t* previous_;

public:
    explicit RoutingCounterScope(uint64_t* counter)
        : previous_(tls_routing_distance_counter) {
        tls_routing_distance_counter = counter;
    }
    ~RoutingCounterScope() { tls_routing_distance_counter = previous_; }
};

struct CountingDistanceComputer final : faiss::DistanceComputer {
    std::unique_ptr<faiss::DistanceComputer> inner;
    uint64_t count = 0;

    explicit CountingDistanceComputer(faiss::DistanceComputer* ptr) : inner(ptr) {}
    void set_query(const float* x) override { inner->set_query(x); }
    float operator()(faiss::idx_t i) override {
        ++count;
        return (*inner)(i);
    }
    float symmetric_dis(faiss::idx_t i, faiss::idx_t j) override {
        return inner->symmetric_dis(i, j);
    }
};

std::vector<int> parse_ints(const std::string& text) {
    std::vector<int> values;
    std::stringstream stream(text);
    std::string token;
    while (std::getline(stream, token, ',')) {
        if (!token.empty()) values.push_back(std::stoi(token));
    }
    if (values.empty()) throw std::runtime_error("integer list must not be empty");
    return values;
}

std::vector<int> load_i32(const std::string& path) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    if (!input) throw std::runtime_error("cannot open int32 file: " + path);
    const auto bytes = static_cast<size_t>(input.tellg());
    if (bytes % sizeof(int32_t) != 0) throw std::runtime_error("invalid int32 file size: " + path);
    input.seekg(0);
    std::vector<int> values(bytes / sizeof(int32_t));
    input.read(reinterpret_cast<char*>(values.data()), static_cast<std::streamsize>(bytes));
    if (!input) throw std::runtime_error("failed reading int32 file: " + path);
    return values;
}

std::vector<float> load_f32_matrix(const std::string& path, size_t rows, int dim) {
    std::ifstream input(path, std::ios::binary | std::ios::ate);
    if (!input) throw std::runtime_error("cannot open float matrix: " + path);
    const auto bytes = static_cast<size_t>(input.tellg());
    const size_t expected = rows * static_cast<size_t>(dim) * sizeof(float);
    if (bytes != expected) {
        throw std::runtime_error("float matrix bytes mismatch for " + path +
                                 ": expected " + std::to_string(expected) +
                                 ", got " + std::to_string(bytes));
    }
    input.seekg(0);
    std::vector<float> values(rows * static_cast<size_t>(dim));
    input.read(reinterpret_cast<char*>(values.data()), static_cast<std::streamsize>(bytes));
    if (!input) throw std::runtime_error("failed reading float matrix: " + path);
    for (float value : values) {
        if (!std::isfinite(value)) throw std::runtime_error("non-finite prototype in " + path);
    }
    return values;
}

class ExactPrototypeView {
    int dim_;
    std::vector<int> ids_;
    std::vector<float> vectors_;
    std::unordered_map<int, size_t> local_by_id_;

    float dot(const float* query, size_t row) const {
        const float* vector = vectors_.data() + row * static_cast<size_t>(dim_);
        float score = 0.0f;
        for (int d = 0; d < dim_; ++d) score += query[d] * vector[d];
        return score;
    }

public:
    ExactPrototypeView(const std::string& hubs_path, const std::string& ids_path, int dim)
        : dim_(dim), ids_(load_i32(ids_path)), vectors_(load_f32_matrix(hubs_path, ids_.size(), dim)) {
        if (ids_.empty()) throw std::runtime_error("prototype view must not be empty");
        for (size_t i = 0; i < ids_.size(); ++i) {
            if (ids_[i] < 0) throw std::runtime_error("negative prototype id in " + ids_path);
            if (!local_by_id_.emplace(ids_[i], i).second)
                throw std::runtime_error("duplicate prototype id in " + ids_path);
        }
    }

    size_t size() const { return ids_.size(); }
    const std::vector<int>& ids() const { return ids_; }

    float score(const float* query, int id) const {
        const auto found = local_by_id_.find(id);
        if (found == local_by_id_.end()) throw std::runtime_error("entry id absent from prototype view");
        return dot(query, found->second);
    }

    std::vector<std::pair<int, float>> topk(const float* query, size_t k, uint64_t* counter) const {
        std::vector<std::pair<int, float>> scored(ids_.size());
        for (size_t i = 0; i < ids_.size(); ++i) scored[i] = {ids_[i], dot(query, i)};
        if (counter) *counter += ids_.size();
        k = std::min(k, scored.size());
        auto better = [](const auto& a, const auto& b) {
            return a.second != b.second ? a.second > b.second : a.first < b.first;
        };
        std::partial_sort(scored.begin(), scored.begin() + k, scored.end(), better);
        scored.resize(k);
        return scored;
    }
};

class HnswPrototypeView {
    std::unique_ptr<hnswlib::SpaceInterface<float>> space_;
    std::unique_ptr<hnswlib::HierarchicalNSW<float>> graph_;

public:
    HnswPrototypeView(const ExactPrototypeView& view, const std::string& hubs_path,
                      int dim, bool counting, size_t ef_search, size_t random_seed) {
        if (counting) space_ = std::make_unique<CountingInnerProductSpace>(dim);
        else space_ = std::make_unique<hnswlib::InnerProductSpace>(dim);
        graph_ = std::make_unique<hnswlib::HierarchicalNSW<float>>(
            space_.get(), view.size(), 16, 200, random_seed);
        const auto vectors = load_f32_matrix(hubs_path, view.size(), dim);
        for (size_t i = 0; i < view.size(); ++i) {
            graph_->addPoint(vectors.data() + i * static_cast<size_t>(dim), view.ids()[i]);
        }
        graph_->setEf(ef_search);
    }

    std::vector<int> topk(const float* query, size_t k, uint64_t* counter) const {
        RoutingCounterScope scope(counter);
        auto heap = graph_->searchKnn(query, k);
        if (heap.size() != k) throw std::runtime_error("primary HNSW returned too few entries");
        std::vector<int> ids;
        ids.reserve(k);
        while (!heap.empty()) {
            ids.push_back(static_cast<int>(heap.top().second));
            heap.pop();
        }
        std::reverse(ids.begin(), ids.end());
        return ids;
    }
};

std::array<int, 3> merge_candidates(
    int anchor,
    const std::array<std::vector<std::pair<int, float>>, 3>& candidates) {
    std::unordered_map<int, float> best;
    for (const auto& view : candidates) {
        for (const auto& [id, score] : view) {
            auto found = best.find(id);
            if (found == best.end() || score > found->second) best[id] = score;
        }
    }
    best.erase(anchor);
    std::vector<std::pair<int, float>> ranked(best.begin(), best.end());
    auto better = [](const auto& a, const auto& b) {
        return a.second != b.second ? a.second > b.second : a.first < b.first;
    };
    if (ranked.size() < 2) throw std::runtime_error("fewer than two non-anchor candidates after merge");
    std::partial_sort(ranked.begin(), ranked.begin() + 2, ranked.end(), better);
    return {anchor, ranked[0].first, ranked[1].first};
}

struct RouteResult {
    std::array<int, 3> final_ids{-1, -1, -1};
    std::vector<int> primary_ids;
    std::array<std::vector<std::pair<int, float>>, 3> candidates;
    uint64_t hnsw_ndc = 0;
    uint64_t exact_ndc = 0;
    double latency_us = 0.0;
};

class TargetBasinRouter {
    ExactPrototypeView view1_;
    ExactPrototypeView view2_;
    ExactPrototypeView view3_;
    HnswPrototypeView primary_;
    std::unique_ptr<HnswPrototypeView> secondary2_;
    std::unique_ptr<HnswPrototypeView> secondary3_;
    bool hnsw_all_ = false;

public:
    TargetBasinRouter(const std::array<std::string, 3>& hubs,
                      const std::array<std::string, 3>& ids,
                      int dim, bool counting, size_t hnsw_seed,
                      const std::string& backend)
        : view1_(hubs[0], ids[0], dim),
          view2_(hubs[1], ids[1], dim),
          view3_(hubs[2], ids[2], dim),
          primary_(view1_, hubs[0], dim, counting, 10, hnsw_seed),
          hnsw_all_(backend == "hnsw_all") {
        if (view1_.size() < 8 || view2_.size() < 8 || view3_.size() < 8)
            throw std::runtime_error("each prototype view must contain at least eight entries");
        if (hnsw_all_) {
            secondary2_ = std::make_unique<HnswPrototypeView>(
                view2_, hubs[1], dim, counting, 32, hnsw_seed + 1);
            secondary3_ = std::make_unique<HnswPrototypeView>(
                view3_, hubs[2], dim, counting, 32, hnsw_seed + 2);
        }
    }

    RouteResult fast(const float* query, bool count) const {
        const auto begin = Clock::now();
        RouteResult result;
        uint64_t* hnsw_counter = count ? &result.hnsw_ndc : nullptr;
        result.primary_ids = primary_.topk(query, 3, hnsw_counter);
        std::copy(result.primary_ids.begin(), result.primary_ids.end(), result.final_ids.begin());
        result.latency_us = std::chrono::duration<double, std::micro>(Clock::now() - begin).count();
        return result;
    }

    RouteResult ensemble(const float* query, bool count, bool details) const {
        const auto begin = Clock::now();
        RouteResult result;
        uint64_t* hnsw_counter = count ? &result.hnsw_ndc : nullptr;
        uint64_t* exact_counter = count ? &result.exact_ndc : nullptr;
        result.primary_ids = primary_.topk(query, 8, hnsw_counter);
        result.candidates[0].reserve(8);
        for (int id : result.primary_ids) {
            result.candidates[0].push_back({id, view1_.score(query, id)});
            if (exact_counter) ++(*exact_counter);
        }
        if (hnsw_all_) {
            const auto ids2 = secondary2_->topk(query, 8, hnsw_counter);
            const auto ids3 = secondary3_->topk(query, 8, hnsw_counter);
            for (int id : ids2) {
                result.candidates[1].push_back({id, view2_.score(query, id)});
                if (exact_counter) ++(*exact_counter);
            }
            for (int id : ids3) {
                result.candidates[2].push_back({id, view3_.score(query, id)});
                if (exact_counter) ++(*exact_counter);
            }
        } else {
            result.candidates[1] = view2_.topk(query, 8, exact_counter);
            result.candidates[2] = view3_.topk(query, 8, exact_counter);
        }
        result.final_ids = merge_candidates(result.primary_ids.front(), result.candidates);
        result.latency_us = std::chrono::duration<double, std::micro>(Clock::now() - begin).count();
        if (!details) {
            result.primary_ids.clear();
            for (auto& values : result.candidates) values.clear();
        }
        return result;
    }
};

json scored_json(const std::vector<std::pair<int, float>>& values) {
    json rows = json::array();
    for (const auto& [id, score] : values) rows.push_back({{"id", id}, {"score", score}});
    return rows;
}

json route_json(int query_id, const RouteResult& route) {
    json row = {
        {"query_id", query_id},
        {"final_entry_ids", route.final_ids},
        {"routing_hnsw_ndc", route.hnsw_ndc},
        {"routing_exact_ndc", route.exact_ndc},
        {"routing_total_ndc", route.hnsw_ndc + route.exact_ndc},
        {"routing_latency_us", route.latency_us}
    };
    if (!route.primary_ids.empty()) {
        row["primary_entry_ids"] = route.primary_ids;
        row["view_candidates"] = {
            scored_json(route.candidates[0]), scored_json(route.candidates[1]),
            scored_json(route.candidates[2])
        };
    }
    return row;
}

double recall_at_k(const faiss::idx_t* result, const int64_t* truth, int k) {
    int hits = 0;
    for (int i = 0; i < k; ++i) {
        if (result[i] < 0) continue;
        for (int g = 0; g < k; ++g) {
            if (result[i] == truth[g]) {
                ++hits;
                break;
            }
        }
    }
    return static_cast<double>(hits) / k;
}

struct QueryEvaluation {
    double recall = 0.0;
    uint64_t graph_ndc = 0;
    double graph_latency_us = 0.0;
    double total_latency_us = 0.0;
    RouteResult route;
    std::vector<int> result_ids;
};

QueryEvaluation evaluate_query(
    acsg::IndexACSGFlat& index,
    faiss::DistanceComputer& distance,
    CountingDistanceComputer* counted,
    faiss::VisitedTable& visited,
    std::vector<acsg::Neighbor>& retset,
    const TargetBasinRouter* router,
    const std::string& method,
    const std::vector<std::array<int, 3>>& replay_routes,
    int query_id,
    const float* query,
    const int64_t* truth,
    int k,
    bool count,
    bool route_details) {
    const auto total_begin = Clock::now();
    QueryEvaluation output;
    std::vector<int> entries;
    if (method == "medoid") {
        entries = {index.acsg.enterpoint};
    } else if (method == "fast") {
        output.route = router->fast(query, count);
        entries.assign(output.route.final_ids.begin(), output.route.final_ids.end());
    } else if (method == "ensemble") {
        output.route = router->ensemble(query, count, route_details);
        entries.assign(output.route.final_ids.begin(), output.route.final_ids.end());
    } else if (method == "replay") {
        output.route.final_ids = replay_routes.at(query_id);
        entries.assign(output.route.final_ids.begin(), output.route.final_ids.end());
    } else {
        throw std::runtime_error("unsupported method: " + method);
    }

    for (int id : entries) {
        if (id < 0 || id >= index.ntotal) throw std::runtime_error("entry id outside frozen index");
    }
    std::vector<acsg::EnterPoint> enterpoints;
    for (int id : entries) enterpoints.emplace_back(id, 1.0);
    std::array<faiss::idx_t, 100> ids;
    std::array<float, 100> distances;
    distance.set_query(query);
    if (counted) counted->count = 0;
    visited.advance();
    const auto graph_begin = Clock::now();
    index.acsg.search_new(distance, k, ids.data(), distances.data(), visited, 2, enterpoints, &retset);
    output.graph_latency_us = std::chrono::duration<double, std::micro>(Clock::now() - graph_begin).count();
    output.total_latency_us = std::chrono::duration<double, std::micro>(Clock::now() - total_begin).count();
    output.graph_ndc = counted ? counted->count : 0;
    output.recall = recall_at_k(ids.data(), truth, k);
    output.result_ids.assign(ids.begin(), ids.begin() + k);
    return output;
}

void write_json_new(const std::string& path, const json& value) {
    if (path.empty()) throw std::runtime_error("--output_file is required");
    if (std::filesystem::exists(path)) throw std::runtime_error("refusing to overwrite output: " + path);
    const auto parent = std::filesystem::path(path).parent_path();
    if (!parent.empty()) std::filesystem::create_directories(parent);
    std::ofstream output(path);
    if (!output) throw std::runtime_error("cannot create output: " + path);
    output << value.dump(2) << '\n';
}

void run_self_test() {
    std::array<std::vector<std::pair<int, float>>, 3> candidates = {{
        {{10, 0.5f}, {11, 0.9f}, {12, 0.8f}},
        {{11, 0.95f}, {20, 0.7f}},
        {{30, 0.85f}, {20, 0.75f}}
    }};
    if (merge_candidates(10, candidates) != std::array<int, 3>{10, 11, 30})
        throw std::runtime_error("duplicate max-score merge self-test failed");
    candidates = {{{{5, 1.0f}}, {{9, 0.8f}}, {{7, 0.8f}}}};
    if (merge_candidates(5, candidates) != std::array<int, 3>{5, 7, 9})
        throw std::runtime_error("tie-break self-test failed");
    bool rejected = false;
    try {
        candidates = {{{{5, 1.0f}}, {{5, 0.9f}}, {{6, 0.8f}}}};
        static_cast<void>(merge_candidates(5, candidates));
    } catch (const std::runtime_error&) {
        rejected = true;
    }
    if (!rejected) throw std::runtime_error("undersized merge self-test failed");
    std::cout << "TARGET_BASIN_SELF_TEST_OK\n";
}

}  // namespace

int main(int argc, char** argv) {
    setvbuf(stdout, nullptr, _IONBF, 0);
    argparse::ArgumentParser program("bench_target_basin_eval");
    program.add_argument("--dataset").default_value(std::string(""));
    program.add_argument("--index_file").default_value(std::string(""));
    program.add_argument("--view1_hubs").default_value(std::string(""));
    program.add_argument("--view1_ids").default_value(std::string(""));
    program.add_argument("--view2_hubs").default_value(std::string(""));
    program.add_argument("--view2_ids").default_value(std::string(""));
    program.add_argument("--view3_hubs").default_value(std::string(""));
    program.add_argument("--view3_ids").default_value(std::string(""));
    program.add_argument("--routes_file").default_value(std::string(""));
    program.add_argument("--output_file").default_value(std::string(""));
    program.add_argument("--method").default_value(std::string("ensemble"));
    program.add_argument("--measurement").default_value(std::string("count"));
    program.add_argument("--query_type").default_value(std::string("drl_train"));
    program.add_argument("--max_queries").default_value(128).scan<'i', int>();
    program.add_argument("--search_Ls").default_value(std::string("64,128"));
    program.add_argument("--top_ks").default_value(std::string("10"));
    program.add_argument("--num_runs").default_value(1).scan<'i', int>();
    program.add_argument("--warmup_runs").default_value(0).scan<'i', int>();
    program.add_argument("--threads").default_value(16).scan<'i', int>();
    program.add_argument("--hnsw_seed").default_value(100).scan<'i', int>();
    program.add_argument("--router_backend").default_value(std::string("dense"));
    program.add_argument("--route_only").default_value(false).implicit_value(true);
    program.add_argument("--export_route_details").default_value(false).implicit_value(true);
    program.add_argument("--allow_heldout").default_value(false).implicit_value(true);
    program.add_argument("--self_test").default_value(false).implicit_value(true);

    try {
        program.parse_args(argc, argv);
        if (program.get<bool>("--self_test")) {
            run_self_test();
            return 0;
        }

        const auto dataset = program.get<std::string>("--dataset");
        const auto index_file = program.get<std::string>("--index_file");
        const auto output_file = program.get<std::string>("--output_file");
        const auto method = program.get<std::string>("--method");
        const auto measurement = program.get<std::string>("--measurement");
        const auto query_type = program.get<std::string>("--query_type");
        const auto routes_file = program.get<std::string>("--routes_file");
        const bool route_only = program.get<bool>("--route_only");
        const bool route_details = program.get<bool>("--export_route_details");
        const bool count = measurement == "count";
        const int max_queries = program.get<int>("--max_queries");
        const int runs = program.get<int>("--num_runs");
        const int warmups = program.get<int>("--warmup_runs");
        const int threads = program.get<int>("--threads");
        const int hnsw_seed = program.get<int>("--hnsw_seed");
        const auto router_backend = program.get<std::string>("--router_backend");
        const auto search_ls = parse_ints(program.get<std::string>("--search_Ls"));
        const auto top_ks = parse_ints(program.get<std::string>("--top_ks"));

        if (dataset.empty()) throw std::runtime_error("--dataset is required");
        if (measurement != "count" && measurement != "timing")
            throw std::runtime_error("--measurement must be count or timing");
        if (method != "medoid" && method != "fast" && method != "ensemble" && method != "replay")
            throw std::runtime_error("--method must be medoid, fast, ensemble, or replay");
        if (router_backend != "dense" && router_backend != "hnsw_all")
            throw std::runtime_error("--router_backend must be dense or hnsw_all");
        if (route_only && method != "fast" && method != "ensemble")
            throw std::runtime_error("--route_only requires fast or ensemble method");
        if ((query_type == "drl_test" || query_type == "test") &&
            !program.get<bool>("--allow_heldout"))
            throw std::runtime_error("held-out access requires explicit --allow_heldout");
        if (max_queries <= 0 || runs <= 0 || warmups < 0 || threads <= 0 || hnsw_seed < 0)
            throw std::runtime_error("query/run/thread/seed values are invalid");
        for (int k : top_ks) {
            if (k < 1 || k > 100) throw std::runtime_error("top_k must be in 1..100");
            for (int L : search_ls) if (L < k) throw std::runtime_error("search_L must be >= top_k");
        }

        std::array<std::string, 3> hubs = {
            program.get<std::string>("--view1_hubs"),
            program.get<std::string>("--view2_hubs"),
            program.get<std::string>("--view3_hubs")
        };
        std::array<std::string, 3> ids = {
            program.get<std::string>("--view1_ids"),
            program.get<std::string>("--view2_ids"),
            program.get<std::string>("--view3_ids")
        };

        DataLoader loader(dataset);
        if (loader.metric_type() != faiss::METRIC_INNER_PRODUCT)
            throw std::runtime_error("target-basin evaluator currently requires inner product");
        auto [query_count, queries] = loader.load_query(query_type);
        const int nq = std::min<int>(max_queries, query_count);
        omp_set_num_threads(threads);

        std::unique_ptr<TargetBasinRouter> router;
        if (method == "fast" || method == "ensemble") {
            const int required_views = method == "ensemble" ? 3 : 1;
            for (int v = 0; v < required_views; ++v) {
                if (hubs[v].empty() || ids[v].empty())
                    throw std::runtime_error("required view prototype paths are missing");
            }
            if (method == "fast") {
                hubs[1] = hubs[0]; hubs[2] = hubs[0];
                ids[1] = ids[0]; ids[2] = ids[0];
            }
            router = std::make_unique<TargetBasinRouter>(
                hubs, ids, static_cast<int>(loader.dim()), count, static_cast<size_t>(hnsw_seed),
                router_backend);
        }

        std::vector<std::array<int, 3>> replay_routes;
        if (method == "replay") {
            if (routes_file.empty()) throw std::runtime_error("--routes_file is required for replay");
            const auto flat = load_i32(routes_file);
            if (flat.size() < static_cast<size_t>(nq * 3))
                throw std::runtime_error("routes file has fewer rows than queries");
            replay_routes.resize(nq);
            for (int q = 0; q < nq; ++q)
                std::copy_n(flat.begin() + q * 3, 3, replay_routes[q].begin());
        }

        json output = {
            {"schema_version", 2}, {"status", "running"}, {"dataset", dataset},
            {"artifact_version", loader.artifact_version()}, {"metric", loader.metric_name()},
            {"normalization", loader.normalization()}, {"split", query_type},
            {"heldout_accessed", query_type == "drl_test" || query_type == "test"},
            {"num_queries", nq}, {"method", method}, {"measurement", measurement},
            {"router_backend", router_backend},
            {"timing_publishable", measurement == "timing"}, {"threads", threads},
            {"hnsw", {
                {"M", 16}, {"ef_construction", 200},
                {"primary", {{"ef_search", 10}, {"random_seed", hnsw_seed}}},
                {"secondary", {{"ef_search", 32}, {"random_seeds", {hnsw_seed + 1, hnsw_seed + 2}}}}
            }},
            {"search_Ls", search_ls}, {"top_ks", top_ks}, {"num_runs", runs},
            {"warmup_runs", warmups}, {"results", json::array()}
        };

        if (route_only) {
            std::vector<json> rows(nq);
            #pragma omp parallel for schedule(static)
            for (int q = 0; q < nq; ++q) {
                const float* query = queries.get() + static_cast<size_t>(q) * loader.dim();
                const auto route = method == "fast" ? router->fast(query, count)
                                                     : router->ensemble(query, count, true);
                rows[q] = route_json(q, route);
            }
            size_t anchor_mismatches = 0;
            for (const auto& row : rows) {
                if (row["final_entry_ids"][0] != row["primary_entry_ids"][0]) ++anchor_mismatches;
            }
            output["route_only"] = true;
            output["gt_loaded"] = false;
            output["rank0_mismatch_count"] = anchor_mismatches;
            output["rank0_preserved"] = anchor_mismatches == 0;
            output["routes"] = std::move(rows);
            output["status"] = "complete";
            write_json_new(output_file, output);
            std::cout << "TARGET_BASIN_ROUTE_COMPLETE output=" << output_file << '\n';
            return 0;
        }

        if (index_file.empty()) throw std::runtime_error("--index_file is required outside route-only mode");
        auto [gt_k, gt] = loader.load_gt(query_type);
        if (gt_k < 100) throw std::runtime_error("evaluation requires top-100 GT");
        auto index = std::make_unique<acsg::IndexACSGFlat>();
        index->loadACPG(index_file.c_str());
        std::vector<float>().swap(index->acsg.pheromone);
        std::vector<float>().swap(index->acsg.weight);

        for (int L : search_ls) {
            index->acsg.search_L = L;
            for (int k : top_ks) {
                for (int pass = -warmups; pass < runs; ++pass) {
                    const bool keep = pass >= 0;
                    std::vector<QueryEvaluation> per_query(nq);
                    const auto batch_begin = Clock::now();
                    #pragma omp parallel
                    {
                        std::unique_ptr<faiss::DistanceComputer> raw;
                        std::unique_ptr<CountingDistanceComputer> counted;
                        faiss::DistanceComputer* active = nullptr;
                        if (count) {
                            counted = std::make_unique<CountingDistanceComputer>(
                                acsg::storage_distance_computer(index->storage));
                            active = counted.get();
                        } else {
                            raw.reset(acsg::storage_distance_computer(index->storage));
                            active = raw.get();
                        }
                        faiss::VisitedTable visited(index->ntotal);
                        std::vector<acsg::Neighbor> retset;
                        #pragma omp for schedule(static)
                        for (int q = 0; q < nq; ++q) {
                            per_query[q] = evaluate_query(
                                *index, *active, counted.get(), visited, retset, router.get(), method,
                                replay_routes, q, queries.get() + static_cast<size_t>(q) * loader.dim(),
                                gt.get() + static_cast<size_t>(q) * gt_k, k, count,
                                route_details && keep && pass == 0);
                        }
                    }
                    const double batch_wall_us = std::chrono::duration<double, std::micro>(
                        Clock::now() - batch_begin).count();
                    if (!keep) continue;

                    double recall_sum = 0.0, route_us_sum = 0.0, graph_us_sum = 0.0, total_us_sum = 0.0;
                    uint64_t route_ndc_sum = 0, graph_ndc_sum = 0;
                    json aligned = json::array();
                    for (int q = 0; q < nq; ++q) {
                        const auto& value = per_query[q];
                        const uint64_t route_ndc = value.route.hnsw_ndc + value.route.exact_ndc;
                        recall_sum += value.recall;
                        route_ndc_sum += route_ndc;
                        graph_ndc_sum += value.graph_ndc;
                        route_us_sum += value.route.latency_us;
                        graph_us_sum += value.graph_latency_us;
                        total_us_sum += value.total_latency_us;
                        json row = {
                            {"query_id", q}, {"recall", value.recall},
                            {"entry_ids", value.route.final_ids}, {"result_ids", value.result_ids},
                            {"routing_hnsw_ndc", count ? json(value.route.hnsw_ndc) : json(nullptr)},
                            {"routing_exact_ndc", count ? json(value.route.exact_ndc) : json(nullptr)},
                            {"routing_total_ndc", count ? json(route_ndc) : json(nullptr)},
                            {"graph_ndc", count ? json(value.graph_ndc) : json(nullptr)},
                            {"total_ndc", count ? json(route_ndc + value.graph_ndc) : json(nullptr)},
                            {"routing_latency_us", value.route.latency_us},
                            {"graph_latency_us", value.graph_latency_us},
                            {"total_latency_us", value.total_latency_us}
                        };
                        if (!value.route.primary_ids.empty()) {
                            row["primary_entry_ids"] = value.route.primary_ids;
                            row["view_candidates"] = {
                                scored_json(value.route.candidates[0]),
                                scored_json(value.route.candidates[1]),
                                scored_json(value.route.candidates[2])
                            };
                        }
                        aligned.push_back(std::move(row));
                    }
                    output["results"].push_back({
                        {"search_L", L}, {"top_k", k}, {"run", pass},
                        {"batch_wall_us", batch_wall_us},
                        {"qps", 1e6 * nq / batch_wall_us},
                        {"mean_recall", recall_sum / nq},
                        {"mean_routing_ndc", count ? json(static_cast<double>(route_ndc_sum) / nq) : json(nullptr)},
                        {"mean_graph_ndc", count ? json(static_cast<double>(graph_ndc_sum) / nq) : json(nullptr)},
                        {"mean_total_ndc", count ? json(static_cast<double>(route_ndc_sum + graph_ndc_sum) / nq) : json(nullptr)},
                        {"mean_routing_latency_us", route_us_sum / nq},
                        {"mean_graph_latency_us", graph_us_sum / nq},
                        {"mean_total_latency_us", total_us_sum / nq},
                        {"per_query", std::move(aligned)}
                    });
                    std::cout << "TARGET_BASIN_STAGE method=" << method << " measurement=" << measurement
                              << " L=" << L << " K=" << k << " run=" << pass
                              << " qps=" << (1e6 * nq / batch_wall_us) << '\n';
                }
            }
        }

        output["gt_loaded"] = true;
        output["route_only"] = false;
        output["status"] = "complete";
        write_json_new(output_file, output);
        std::cout << "TARGET_BASIN_EVAL_COMPLETE output=" << output_file << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "ERROR: " << error.what() << '\n';
        std::cerr << program;
        return 2;
    }
}

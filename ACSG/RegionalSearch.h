#pragma once

// Frozen-graph search experiment. No ground-truth dependency or legacy changes.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <vector>

namespace acsg::regional {

constexpr int max_active = 4;
constexpr int max_entries = 18;
struct Route {
    std::array<int, max_active> regions{};
    std::array<double, max_active> weights{};
    std::array<int32_t, max_entries> entries{};
    int active = 0, entry_count = 0;
    // The default entry is submitted first and forced into the shared queue.
    int32_t shared_seed = -1;
};

struct Candidate {
    int32_t id;
    float distance;
    bool expanded;
};
enum class EventKind { discover, accept, reject, evict, expand };
struct Event {
    EventKind kind;
    int32_t id, parent;
    int queue;
    float distance;
    bool expanded;
};
struct Stats { uint64_t ndc = 0, expanded = 0, rejected = 0, evicted_unexpanded = 0; };

struct Workspace {
    std::vector<uint8_t> visited;
    uint8_t epoch = 0;
    std::array<std::vector<Candidate>, max_active + 1> queues;
    std::array<int, max_active + 1> capacity{}, head{};
    std::array<double, max_active + 1> credit{};
    std::vector<Candidate> results;
    int max_l, max_k;

    Workspace(size_t n, int l, int k) : visited(n, 0), max_l(l), max_k(k) {
        if (!n || k < 1 || l < k) throw std::invalid_argument("invalid workspace dimensions");
        for (auto& queue : queues) queue.reserve(static_cast<size_t>(l) + 1);
        results.reserve(static_cast<size_t>(k) + 1);
    }
    void reset() {
        if (++epoch == 0) { std::fill(visited.begin(), visited.end(), 0); epoch = 1; }
        for (auto& queue : queues) queue.clear();
        results.clear(); head.fill(0); credit.fill(0);
    }
};

inline void validate_regions(const uint16_t* labels, size_t n, int region_count) {
    if (!labels || !n || region_count < 1 || region_count > 65536)
        throw std::invalid_argument("invalid region map");
    for (size_t i = 0; i < n; ++i)
        if (labels[i] >= region_count) throw std::invalid_argument("node region outside region map");
}

inline int allocate(const Route& route, int l, int region_count, bool regional,
                    bool uniform, std::array<int, max_active + 1>& caps) {
    if (route.active < 0 || route.active > max_active || l < 1 ||
        region_count < 1 || region_count > 65536)
        throw std::invalid_argument("invalid active region count or L");
    double weight_sum = 0;
    for (int r = 0; r < route.active; ++r) {
        if (route.regions[r] < 0 || route.regions[r] >= region_count ||
            !std::isfinite(route.weights[r]) || route.weights[r] < 0)
            throw std::invalid_argument("invalid route region/weight");
        for (int t = 0; t < r; ++t)
            if (route.regions[t] == route.regions[r]) throw std::invalid_argument("duplicate route region");
        weight_sum += route.weights[r];
    }
    if (!std::isfinite(weight_sum)) throw std::invalid_argument("region weight sum is not finite");
    caps.fill(0);
    if (!regional || region_count == 1 || route.active == 0) { caps[0] = l; return 1; }
    if (weight_sum <= 0) throw std::invalid_argument("region weights must have positive mass");
    caps[0] = l / 4;
    int remainder = l - caps[0] - 4 * route.active;
    if (caps[0] < 1 || remainder < 0) throw std::invalid_argument("L cannot satisfy queue minima");
    std::array<double, max_active> fractions{};
    std::array<int, max_active> order{};
    int used = 0;
    for (int r = 0; r < route.active; ++r) {
        const double portion = remainder * (uniform ? 1.0 / route.active : route.weights[r] / weight_sum);
        const int floor = static_cast<int>(std::floor(portion));
        caps[r + 1] = 4 + floor; used += floor;
        fractions[r] = portion - floor; order[r] = r;
    }
    std::sort(order.begin(), order.begin() + route.active, [&](int a, int b) {
        return fractions[a] != fractions[b] ? fractions[a] > fractions[b] : route.regions[a] < route.regions[b];
    });
    for (int i = 0; i < remainder - used; ++i) ++caps[order[i] + 1];
    return route.active + 1;
}

// Graph must expose N, K, at(node, offset); distance(id) is smaller-is-better.
// Region-map validation belongs to loading, outside the online timer.
template<bool Instrument, class Graph, class Distance>
Stats search(const Graph& graph, Distance& distance, const uint16_t* labels, int region_count,
             const Route& route, int l, int k, bool regional, bool uniform,
             Workspace& work, int64_t* ids, float* distances, std::vector<Event>* trace = nullptr) {
    if (k < 1 || l < k || l > work.max_l || k > work.max_k ||
        graph.N < 1 || graph.K < 0 ||
        static_cast<size_t>(graph.N) != work.visited.size() || !ids || !distances ||
        route.entry_count < 0 || route.entry_count > max_entries ||
        route.shared_seed < -1 || route.shared_seed >= graph.N ||
        (regional && !labels)) throw std::invalid_argument("invalid search inputs/capacity");
    if constexpr (!Instrument) {
        if (trace) throw std::invalid_argument("plain search cannot collect traces");
    }
    const int nq = allocate(route, l, region_count, regional, uniform, work.capacity);
    work.reset();
    if (trace) trace->clear();
    Stats stats;
    auto record = [&](EventKind kind, const Candidate& node, int parent, int queue) {
        if constexpr (Instrument) if (trace)
            trace->push_back({kind, node.id, parent, queue, node.distance, node.expanded});
    };
    auto discover = [&](int32_t id, int parent, bool shared_seed) {
        if (id < 0 || id >= graph.N) throw std::invalid_argument("invalid entry or graph node");
        if (work.visited[id] == work.epoch) return;
        work.visited[id] = work.epoch;
        const float d = distance(id);
        if (!std::isfinite(d)) throw std::invalid_argument("non-finite search distance");
        if constexpr (Instrument) ++stats.ndc;
        Candidate node{id, d, false};
        int owner = 0;
        if (nq > 1 && !shared_seed) {
            for (int r = 0; r < route.active; ++r)
                if (labels[id] == route.regions[r]) { owner = r + 1; break; }
        }
        record(EventKind::discover, node, parent, owner);
        // Results include every evaluated node, even if its candidate queue rejects it.
        auto& result = work.results;
        // Keep discovery order for equal distances, as the finite beam does.
        // A node-ID tie break here would change even a unified-pool baseline.
        auto result_pos = std::upper_bound(result.begin(), result.end(), d,
                                          [](float value, const Candidate& other) { return value < other.distance; });
        if (result_pos - result.begin() < k) {
            result.insert(result_pos, node);
            if (static_cast<int>(result.size()) > k) result.pop_back();
        }
        auto& queue = work.queues[owner];
        const int cap = work.capacity[owner];
        if (static_cast<int>(queue.size()) == cap && d >= queue.back().distance) {
            if constexpr (Instrument) ++stats.rejected;
            record(EventKind::reject, node, parent, owner); return;
        }
        // Distance-only stable insertion follows legacy finite-beam ordering.
        auto pos = std::upper_bound(queue.begin(), queue.end(), d,
                                   [](float value, const Candidate& other) { return value < other.distance; });
        const int position = static_cast<int>(pos - queue.begin());
        if (static_cast<int>(queue.size()) == cap) {
            if constexpr (Instrument) if (!queue.back().expanded) ++stats.evicted_unexpanded;
            record(EventKind::evict, queue.back(), id, owner);
        }
        queue.insert(pos, node);
        if (static_cast<int>(queue.size()) > cap) queue.pop_back();
        work.head[owner] = std::min(work.head[owner], position);
        record(EventKind::accept, node, parent, owner);
    };
    if (route.shared_seed >= 0) discover(route.shared_seed, -1, true);
    for (int e = 0; e < route.entry_count; ++e) discover(route.entries[e], -1, false);
    if (work.results.empty()) throw std::invalid_argument("route must supply an entry");
    while (true) {
        int chosen = -1;
        double live_weight = 0;
        for (int q = 0; q < nq; ++q) {
            auto& queue = work.queues[q];
            auto& head = work.head[q];
            while (head < static_cast<int>(queue.size()) && queue[head].expanded) ++head;
            if (head == static_cast<int>(queue.size())) { work.credit[q] = 0; continue; }
            work.credit[q] += work.capacity[q]; live_weight += work.capacity[q];
            if (chosen < 0 || work.credit[q] > work.credit[chosen]) chosen = q;
        }
        if (chosen < 0) break;
        work.credit[chosen] -= live_weight;
        auto& node = work.queues[chosen][work.head[chosen]];
        node.expanded = true;
        const int32_t id = node.id;
        if constexpr (Instrument) ++stats.expanded;
        record(EventKind::expand, node, -1, chosen);
        for (int j = 0; j < graph.K; ++j) {
            const auto neighbor = graph.at(id, j);
            if (neighbor == -1) continue;
            if (neighbor < 0 || neighbor >= graph.N) throw std::invalid_argument("invalid frozen graph edge");
            discover(static_cast<int32_t>(neighbor), id, false);
        }
    }
    for (int i = 0; i < k; ++i) {
        ids[i] = i < static_cast<int>(work.results.size()) ? work.results[i].id : -1;
        distances[i] = i < static_cast<int>(work.results.size()) ? work.results[i].distance : std::numeric_limits<float>::max();
    }
    return stats;
}
} // namespace acsg::regional

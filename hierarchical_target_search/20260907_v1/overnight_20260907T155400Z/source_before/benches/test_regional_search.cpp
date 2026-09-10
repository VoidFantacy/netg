#include <ACSG/ACSG.h>
#include <ACSG/RegionalSearch.h>
#include <faiss/impl/DistanceComputer.h>
#include <nlohmann/json.hpp>
#include <iostream>
#include <random>
#include <set>
#include <map>

using namespace acsg::regional;
using json = nlohmann::json;

void require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}
template<class F> void rejects(F&& call) {
    bool caught = false;
    try { call(); } catch (const std::invalid_argument&) { caught = true; }
    require(caught, "invalid input was accepted");
}
struct Distance : faiss::DistanceComputer {
    std::vector<float> values;
    std::vector<unsigned> calls;
    explicit Distance(int n) : values(n), calls(n, 0) {}
    void set_query(const float*) override {}
    float operator()(faiss::idx_t id) override { ++calls.at(id); return values.at(id); }
    float symmetric_dis(faiss::idx_t, faiss::idx_t) override { return 0; }
    void reset() { std::fill(calls.begin(), calls.end(), 0); }
    uint64_t total() const { return std::accumulate(calls.begin(), calls.end(), uint64_t(0)); }
};

// Independently replay traces; no inspection of internal queue implementation.
void replay(const std::vector<Event>& trace, const Workspace& work) {
    std::set<int32_t> discovered, expanded;
    std::array<std::map<int32_t, bool>, max_active + 1> retained;
    for (const auto& event : trace) {
        auto& queue = retained.at(event.queue);
        switch (event.kind) {
            case EventKind::discover:
                require(discovered.insert(event.id).second, "duplicate discovery/distance");
                if (event.parent >= 0) require(expanded.count(event.parent), "discovery before parent expansion");
                break;
            case EventKind::accept:
                require(discovered.count(event.id), "accept before discovery");
                require(queue.emplace(event.id, false).second, "duplicate candidate");
                require(queue.size() <= static_cast<size_t>(work.capacity[event.queue]), "capacity exceeded");
                break;
            case EventKind::reject:
                require(discovered.count(event.id) && !queue.count(event.id), "invalid rejection");
                break;
            case EventKind::evict:
                require(queue.count(event.id), "eviction of absent candidate");
                require(queue.at(event.id) == event.expanded, "wrong eviction expansion state");
                queue.erase(event.id); break;
            case EventKind::expand:
                require(queue.count(event.id) && !queue.at(event.id), "expansion of absent/expanded candidate");
                require(expanded.insert(event.id).second, "node expanded twice");
                queue[event.id] = true; break;
        }
    }
    for (const auto& queue : retained)
        for (const auto& [id, done] : queue) { (void)id; require(done, "retained node unexpanded at termination"); }
}

int main(int argc, char** argv) {
    if (argc == 2 && std::string(argv[1]) == "--help") {
        std::cout << "test_regional_search: deterministic synthetic correctness and legacy parity checks\n";
        return 0;
    }
    try {
        json checks = json::array();
        std::mt19937 rng(2026090711);
        uint64_t parity_queries = 0;
        for (int trial = 0; trial < 400; ++trial) {
            const int n = 64, degree = 8, l = trial % 2 ? 16 : 32, k = 10;
            acsg::ACSG old(8);
            old.ntotal = n; old.is_built = true; old.search_L = l;
            old.final_graph = std::make_shared<acsg::Graph<int32_t>>(n, degree);
            for (int node = 0; node < n; ++node)
                for (int j = 0; j < degree; ++j) old.final_graph->at(node, j) = static_cast<int>(rng() % n);
            Distance legacy(n), current(n);
            std::iota(current.values.begin(), current.values.end(), -20.125f);
            std::shuffle(current.values.begin(), current.values.end(), rng);
            legacy.values = current.values;
            Route route;
            route.entry_count = 3;
            route.entries[0] = trial % n; route.entries[1] = (trial + 7) % n; route.entries[2] = (trial + 19) % n;
            std::vector<acsg::EnterPoint> entries;
            for (int i = 0; i < 3; ++i) entries.emplace_back(route.entries[i], 1.0);
            faiss::VisitedTable vt(n);
            std::vector<acsg::Neighbor> buffer;
            std::array<int64_t, 10> a{}, b{}, c{};
            std::array<float, 10> da{}, db{}, dc{};
            old.search_new(legacy, k, a.data(), da.data(), vt, 2, entries, &buffer);
            Workspace work(n, l, k);
            auto stats = search<true>(*old.final_graph, current, nullptr, 1, route, l, k, false, false, work, b.data(), db.data());
            require(a == b, "legacy/shared result ID mismatch");
            require(legacy.total() == stats.ndc && current.total() == stats.ndc, "legacy/shared NDC mismatch");
            require(*std::max_element(current.calls.begin(), current.calls.end()) == 1, "duplicate exact distance");
            current.reset();
            search<false>(*old.final_graph, current, nullptr, 1, route, l, k, false, false, work, c.data(), dc.data());
            require(b == c && db == dc, "count/plain mismatch");
            std::vector<uint16_t> one(n, 0);
            route.active = 1; route.regions[0] = 0; route.weights[0] = 1;
            current.reset();
            search<true>(*old.final_graph, current, one.data(), 1, route, l, k, true, false, work, c.data(), dc.data());
            require(b == c && stats.ndc == current.total(), "single region did not degenerate to shared");
            ++parity_queries;
        }
        checks.push_back({{"name", "legacy_shared_unique_distance_parity"}, {"queries", parity_queries}, {"status", "PASS"}});
        checks.push_back({{"name", "count_plain_and_single_region_parity"}, {"status", "PASS"}});

        const int n = 64, l = 32, k = 10;
        acsg::Graph<int32_t> graph(n, 42);
        std::fill_n(graph.data, n * graph.K, -1);
        for (int i = 1; i <= 41; ++i) graph.at(0, i - 1) = i;
        graph.at(41, 0) = 42;
        graph.at(42, 0) = 0; // A cycle must not cause a second distance or expansion.
        std::vector<uint16_t> labels(n, 0); labels[41] = 3; labels[42] = 3;
        validate_regions(labels.data(), n, 4);
        Distance distance(n); std::iota(distance.values.begin(), distance.values.end(), 0.f);
        distance.values[41] = 100; distance.values[42] = -100;
        Route route; route.active = 4; route.shared_seed = 0; route.entry_count = 3;
        route.entries = {0, 0, 0}; // Actual duplicates, also duplicate the shared seed.
        for (int r = 0; r < 4; ++r) { route.regions[r] = r; route.weights[r] = r + 1; }
        Workspace work(n, 128, k);
        std::array<int64_t, k> shared{}, protected_ids{}, plain{};
        std::array<float, k> distances{};
        auto shared_stats = search<true>(graph, distance, labels.data(), 4, route, l, k, false, false, work, shared.data(), distances.data());
        require(shared[0] != 42, "synthetic shared-pool bridge must be rejected");
        distance.reset(); std::vector<Event> events;
        auto protected_stats = search<true>(graph, distance, labels.data(), 4, route, l, k, true, false, work, protected_ids.data(), distances.data(), &events);
        require(protected_ids[0] == 42, "protected bridge failed to reach target across region boundary");
        require(protected_stats.ndc == distance.total(), "shared distance counter mismatch");
        require(*std::max_element(distance.calls.begin(), distance.calls.end()) == 1, "duplicate entries/cycle caused duplicate distance");
        replay(events, work);
        for (int repeat = 0; repeat < 520; ++repeat) {
            distance.reset();
            search<false>(graph, distance, labels.data(), 4, route, l, k, true, false, work, plain.data(), distances.data());
            require(plain == protected_ids, "repeat/epoch-wrap result mismatch");
            require(distance.total() == protected_stats.ndc, "epoch-wrap distance mismatch");
        }
        checks.push_back({{"name", "protected_bridge_cross_region_and_empty_regions"}, {"status", "PASS"},
                          {"shared_ndc", shared_stats.ndc}, {"regional_ndc", protected_stats.ndc}});
        checks.push_back({{"name", "trace_replay_duplicates_shared_visited_epoch_wrap"}, {"status", "PASS"}, {"trace_events", events.size()}});
        for (int capacity : {32, 64, 128}) for (bool uniform : {false, true}) {
            std::array<int, 5> caps;
            allocate(route, capacity, 4, true, uniform, caps);
            require(std::accumulate(caps.begin(), caps.end(), 0) == capacity, "capacity sum != L");
            for (int r = 1; r < 5; ++r) require(caps[r] >= 4, "regional minimum violated");
        }
        auto call = [&](Route input, int cap, int top) {
            search<false>(graph, distance, labels.data(), 4, input, cap, top, true, false, work, plain.data(), distances.data());
        };
        rejects([&] { call(route, 8, 10); });
        rejects([&] { call(route, 16, 10); });
        auto invalid = route; invalid.regions[0] = 4; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.regions[0] = 1; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.weights[0] = -1; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.entries[0] = n; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.shared_seed = -1; invalid.entry_count = 0; rejects([&] { call(invalid, l, k); });
        labels[63] = 4; rejects([&] { validate_regions(labels.data(), n, 4); }); labels[63] = 0;
        checks.push_back({{"name", "capacity_and_invalid_inputs"}, {"status", "PASS"}});
        std::cout << json({{"status", "PASS"}, {"seed", 2026090711}, {"tests", checks},
                          {"limitations", "Synthetic suite; full-data legacy parity and evaluator timing isolation are separate P1 gates"}}).dump(2) << '\n';
    } catch (const std::exception& error) {
        std::cerr << "REGIONAL_TEST_FAIL " << error.what() << '\n'; return 1;
    }
}

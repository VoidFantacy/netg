#include <ACSG/ACSG.h>
#include <ACSG/RegionalSearch.h>
#include <faiss/impl/DistanceComputer.h>
#include <hnswlib/hnswlib.h>
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
void replay(const std::vector<Event>& trace, const Workspace& work,
            const int64_t* ids, const float* distances, int k, const Stats& stats) {
    std::set<int32_t> discovered, expanded;
    std::set<int32_t> decided;
    std::vector<Event> evaluated;
    uint64_t rejected = 0, evicted_unexpanded = 0;
    std::array<std::map<int32_t, bool>, max_active + 1> retained;
    for (const auto& event : trace) {
        auto& queue = retained.at(event.queue);
        switch (event.kind) {
            case EventKind::discover:
                require(discovered.insert(event.id).second, "duplicate discovery/distance");
                evaluated.push_back(event);
                if (event.parent >= 0) require(expanded.count(event.parent), "discovery before parent expansion");
                break;
            case EventKind::accept:
                require(discovered.count(event.id), "accept before discovery");
                require(decided.insert(event.id).second, "node received multiple admission decisions");
                require(queue.emplace(event.id, false).second, "duplicate candidate");
                require(queue.size() <= static_cast<size_t>(work.capacity[event.queue]), "capacity exceeded");
                break;
            case EventKind::reject:
                require(discovered.count(event.id) && !queue.count(event.id), "invalid rejection");
                require(decided.insert(event.id).second, "node received multiple admission decisions");
                ++rejected;
                break;
            case EventKind::evict:
                require(queue.count(event.id), "eviction of absent candidate");
                require(queue.at(event.id) == event.expanded, "wrong eviction expansion state");
                evicted_unexpanded += !event.expanded;
                queue.erase(event.id); break;
            case EventKind::expand:
                require(queue.count(event.id) && !queue.at(event.id), "expansion of absent/expanded candidate");
                require(expanded.insert(event.id).second, "node expanded twice");
                queue[event.id] = true; break;
        }
    }
    for (const auto& queue : retained)
        for (const auto& [id, done] : queue) { (void)id; require(done, "retained node unexpanded at termination"); }
    require(decided == discovered, "discovery lacks admission decision");
    require(discovered.size() == stats.ndc && expanded.size() == stats.expanded &&
            rejected == stats.rejected && evicted_unexpanded == stats.evicted_unexpanded,
            "trace and aggregate counters disagree");
    std::stable_sort(evaluated.begin(), evaluated.end(), [](const Event& a, const Event& b) {
        return a.distance < b.distance;
    });
    for (int i = 0; i < k; ++i) {
        const int64_t expected_id = i < static_cast<int>(evaluated.size()) ? evaluated[i].id : -1;
        const float expected_distance = i < static_cast<int>(evaluated.size()) ? evaluated[i].distance : std::numeric_limits<float>::max();
        require(ids[i] == expected_id && distances[i] == expected_distance,
                "global top-K does not match independently sorted evaluated nodes");
    }
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
        for (int trial = 0; trial < 1200; ++trial) {
            const int n = 64, degree = 8, l = trial % 2 ? 16 : 32, k = 10;
            acsg::ACSG old(8);
            old.ntotal = n; old.is_built = true; old.search_L = l;
            old.final_graph = std::make_shared<acsg::Graph<int32_t>>(n, degree);
            for (int node = 0; node < n; ++node)
                for (int j = 0; j < degree; ++j) old.final_graph->at(node, j) = static_cast<int>(rng() % n);
            Distance legacy(n), current(n);
            std::iota(current.values.begin(), current.values.end(), -20.125f);
            if (trial >= 400) for (auto& value : current.values)
                value = trial >= 800 ? 0.0f : static_cast<int>(value) / 8;
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
            if (a != b || da != db) {
                std::cerr << json({{"trial", trial}, {"legacy_ids", a}, {"current_ids", b},
                                   {"legacy_distances", da}, {"current_distances", db}}).dump() << '\n';
                throw std::runtime_error("legacy/shared result ID or distance mismatch");
            }
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
        checks.push_back({{"name", "legacy_shared_unique_and_tied_distance_parity"},
                          {"queries", parity_queries}, {"unique_queries", 400}, {"tied_queries", 800}, {"status", "PASS"}});
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
        replay(events, work, protected_ids.data(), distances.data(), k, protected_stats);
        const auto visited_storage = work.visited.data();
        const auto result_storage = work.results.data();
        std::array<const Candidate*, 5> queue_storage{};
        for (int q = 0; q < 5; ++q) queue_storage[q] = work.queues[q].data();
        for (int repeat = 0; repeat < 520; ++repeat) {
            distance.reset();
            search<false>(graph, distance, labels.data(), 4, route, l, k, true, false, work, plain.data(), distances.data());
            require(plain == protected_ids, "repeat/epoch-wrap result mismatch");
            require(distance.total() == protected_stats.ndc, "epoch-wrap distance mismatch");
            require(work.visited.data() == visited_storage && work.results.data() == result_storage,
                    "search reallocated preallocated workspace");
            for (int q = 0; q < 5; ++q)
                require(work.queues[q].data() == queue_storage[q], "search reallocated a candidate queue");
        }
        checks.push_back({{"name", "protected_bridge_cross_region_and_empty_regions"}, {"status", "PASS"},
                          {"shared_ndc", shared_stats.ndc}, {"regional_ndc", protected_stats.ndc}});
        checks.push_back({{"name", "trace_replay_duplicates_shared_visited_epoch_wrap"}, {"status", "PASS"}, {"trace_events", events.size()}});
        checks.push_back({{"name", "preallocated_search_storage_retained"}, {"status", "PASS"}, {"queries", 520}});
        for (int capacity = 21; capacity <= 128; ++capacity) for (bool uniform : {false, true}) {
            std::array<int, 5> caps;
            allocate(route, capacity, 4, true, uniform, caps);
            require(std::accumulate(caps.begin(), caps.end(), 0) == capacity, "capacity sum != L");
            for (int r = 1; r < 5; ++r) require(caps[r] >= 4, "regional minimum violated");
        }
        Route tied = route;
        for (int r = 0; r < 4; ++r) { tied.regions[r] = 3 - r; tied.weights[r] = 1; }
        std::array<int, 5> tied_caps{};
        allocate(tied, 23, 4, true, false, tied_caps);
        require(tied_caps == std::array<int, 5>{5, 4, 4, 5, 5}, "region-ID largest-remainder tie break mismatch");
        auto call = [&](Route input, int cap, int top) {
            search<false>(graph, distance, labels.data(), 4, input, cap, top, true, false, work, plain.data(), distances.data());
        };
        rejects([&] { call(route, 8, 10); });
        rejects([&] { call(route, 16, 10); });
        rejects([&] { call(route, 20, 10); });
        rejects([&] { call(route, 129, 10); });
        rejects([&] { call(route, 32, 0); });
        rejects([&] { call(route, 32, 11); });
        auto invalid = route; invalid.regions[0] = 4; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.regions[0] = 1; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.weights[0] = -1; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.weights.fill(0); rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.weights[0] = std::numeric_limits<double>::infinity(); rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.weights.fill(std::numeric_limits<double>::max()); rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.weights[0] = std::numeric_limits<double>::quiet_NaN(); rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.active = 5; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.active = -1; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.entry_count = max_entries + 1; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.entry_count = -1; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.shared_seed = -2; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.shared_seed = n; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.entries[0] = n; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.entries[0] = -1; rejects([&] { call(invalid, l, k); });
        invalid = route; invalid.shared_seed = -1; invalid.entry_count = 0; rejects([&] { call(invalid, l, k); });
        labels[63] = 4; rejects([&] { validate_regions(labels.data(), n, 4); }); labels[63] = 0;
        rejects([&] { validate_regions(nullptr, n, 4); });
        rejects([&] { validate_regions(labels.data(), 0, 4); });
        rejects([&] { validate_regions(labels.data(), n, 0); });
        rejects([&] { allocate(route, l, 65537, false, false, tied_caps); });
        rejects([&] { Workspace bad(0, l, k); });
        rejects([&] { Workspace bad(n, k - 1, k); });
        rejects([&] { search<false>(graph, distance, labels.data(), 4, route, l, k, true, false,
                                   work, nullptr, distances.data()); });
        rejects([&] { search<false>(graph, distance, labels.data(), 4, route, l, k, true, false,
                                   work, plain.data(), nullptr); });
        rejects([&] { search<false>(graph, distance, labels.data(), 4, route, l, k, true, false,
                                   work, plain.data(), distances.data(), &events); });
        rejects([&] { search<true>(graph, distance, nullptr, 4, route, l, k, true, false,
                                  work, plain.data(), distances.data()); });
        graph.at(0, 0) = n; rejects([&] { call(route, l, k); });
        graph.at(0, 0) = -2; rejects([&] { call(route, l, k); }); graph.at(0, 0) = 1;
        graph.K = -1; rejects([&] { call(route, l, k); }); graph.K = 42;
        for (float nonfinite : {std::numeric_limits<float>::infinity(), -std::numeric_limits<float>::infinity(),
                                std::numeric_limits<float>::quiet_NaN()}) {
            distance.values[0] = nonfinite; rejects([&] { call(route, l, k); });
        }
        distance.values[0] = 0;
        checks.push_back({{"name", "capacity_and_invalid_inputs"}, {"status", "PASS"}});

        // Some evaluated top-K nodes cannot fit their regional candidate queue.
        // Both controls must nevertheless return them from the global result pool.
        acsg::Graph<int32_t> star(20, 16);
        std::fill_n(star.data, star.N * star.K, -1);
        for (int i = 1; i <= 16; ++i) star.at(0, i - 1) = i;
        std::vector<uint16_t> star_labels(star.N, 1); star_labels[0] = 0;
        Distance star_distance(star.N); std::iota(star_distance.values.begin(), star_distance.values.end(), 0.f);
        star_distance.values[0] = 100;
        Workspace star_work(star.N, l, k);
        std::array<float, k> shared_distances{}, protected_distances{};
        search<true>(star, star_distance, star_labels.data(), 4, route, l, k, false, false,
                     star_work, shared.data(), shared_distances.data());
        star_distance.reset();
        const auto star_stats = search<true>(star, star_distance, star_labels.data(), 4, route, l, k, true, false,
                                            star_work, protected_ids.data(), protected_distances.data(), &events);
        require(shared == protected_ids && shared_distances == protected_distances, "global top-K fairness mismatch");
        bool returned_rejected = false;
        for (const auto& event : events)
            if (event.kind == EventKind::reject && std::find(protected_ids.begin(), protected_ids.end(), event.id) != protected_ids.end())
                returned_rejected = true;
        require(returned_rejected, "test did not exercise rejected nodes in global top-K");
        replay(events, star_work, protected_ids.data(), protected_distances.data(), k, star_stats);
        require(events.front().id == route.shared_seed && events.front().queue == 0, "default seed not first/shared");
        checks.push_back({{"name", "global_topk_includes_rejected_regional_candidates"}, {"status", "PASS"}});

        acsg::Graph<int32_t> isolated(64, 1); std::fill_n(isolated.data, isolated.N, -1);
        Distance isolated_distance(isolated.N);
        for (int id = 0; id < isolated.N; ++id) isolated_distance.values[id] = -static_cast<float>(id);
        hnswlib::InnerProductSpace space(2);
        hnswlib::HierarchicalNSW<float> hnsw(&space, 32, 16, 200, 2026090711);
        for (int i = 0; i < 32; ++i) {
            const std::array<float, 2> vector{static_cast<float>(2 * i + 1), 1.f};
            hnsw.addPoint(vector.data(), 2 * i + 1);
        }
        hnsw.setEf(32);
        const std::array<float, 2> query{1.f, 0.f};
        json top_m_records = json::array();
        for (int m : {3, 4, 6, 8, 18}) {
            auto heap = hnsw.searchKnn(query.data(), m);
            Route topm; topm.entry_count = m;
            std::vector<int32_t> popped;
            while (!heap.empty()) { popped.push_back(static_cast<int32_t>(heap.top().second)); heap.pop(); }
            require(static_cast<int>(popped.size()) == m, "HNSW top-m count mismatch");
            std::reverse_copy(popped.begin(), popped.end(), topm.entries.begin());
            for (int i = 0; i < m; ++i) require(topm.entries[i] == 63 - 2 * i, "HNSW heap was not consumed best-first");
            isolated_distance.reset();
            const auto topm_stats = search<true>(isolated, isolated_distance, nullptr, 1, topm, l, k, false, false,
                                                work, protected_ids.data(), protected_distances.data(), &events);
            require(topm_stats.ndc == static_cast<uint64_t>(m) && isolated_distance.total() == static_cast<uint64_t>(m),
                    "top-m entries were silently capped");
            std::vector<int32_t> consumed;
            for (const auto& event : events) if (event.kind == EventKind::discover) consumed.push_back(event.id);
            require(std::equal(consumed.begin(), consumed.end(), topm.entries.begin()), "entry consumption order mismatch");
            replay(events, work, protected_ids.data(), protected_distances.data(), k, topm_stats);
            for (int i = m; i < k; ++i)
                require(protected_ids[i] == -1 && protected_distances[i] == std::numeric_limits<float>::max(), "incorrect short-result padding");
            isolated_distance.reset();
            search<false>(isolated, isolated_distance, nullptr, 1, topm, l, k, false, false,
                          work, plain.data(), distances.data());
            require(plain == protected_ids && distances == protected_distances, "top-m count/plain mismatch");
            top_m_records.push_back({{"m", m}, {"heap_pop_order", popped}, {"consumed_entry_ids", consumed}, {"ndc", topm_stats.ndc}});
            if (m == 3) {
                acsg::ACSG short_old(8); short_old.ntotal = isolated.N; short_old.is_built = true; short_old.search_L = l;
                short_old.final_graph = std::make_shared<acsg::Graph<int32_t>>(isolated.N, 1);
                std::fill_n(short_old.final_graph->data, isolated.N, -1);
                std::vector<acsg::EnterPoint> short_entries;
                for (int i = 0; i < m; ++i) short_entries.emplace_back(topm.entries[i], 1.0);
                faiss::VisitedTable short_visited(isolated.N);
                isolated_distance.reset();
                short_old.search_new(isolated_distance, k, plain.data(), distances.data(), short_visited, 2, short_entries);
                require(plain == protected_ids && distances == protected_distances && isolated_distance.total() == topm_stats.ndc,
                        "legacy short-result padding or NDC mismatch");
            }
            topm.entries[1] = topm.entries[0];
            isolated_distance.reset();
            search<true>(isolated, isolated_distance, nullptr, 1, topm, l, k, false, false,
                         work, plain.data(), distances.data());
            require(isolated_distance.total() == static_cast<uint64_t>(m - 1), "duplicate top-m entry was recomputed");
        }
        checks.push_back({{"name", "hnsw_top_m_actual_consumption_order_and_dedup"}, {"status", "PASS"}, {"records", top_m_records}});
        checks.push_back({{"name", "legacy_short_results_ids_distances_ndc"}, {"status", "PASS"}});

        uint64_t replayed_events = 0;
        for (int trial = 0; trial < 300; ++trial) {
            const int nodes = 17 + rng() % 103, degree = 2 + rng() % 15, capacity = 21 + rng() % 44;
            acsg::Graph<int32_t> varied(nodes, degree);
            for (int i = 0; i < nodes * degree; ++i)
                varied.data[i] = rng() % 5 == 0 ? -1 : static_cast<int32_t>(rng() % nodes);
            std::vector<uint16_t> varied_labels(nodes);
            for (auto& label : varied_labels) label = rng() % 8;
            Route varied_route; varied_route.active = 1 + rng() % 4;
            varied_route.shared_seed = rng() % nodes; varied_route.entry_count = 1 + rng() % max_entries;
            for (int i = 0; i < varied_route.entry_count; ++i) varied_route.entries[i] = rng() % nodes;
            for (int i = 0; i < varied_route.active; ++i) {
                varied_route.regions[i] = 2 * i; varied_route.weights[i] = i == 0 ? 1 : rng() % 4;
            }
            Distance varied_distance(nodes);
            for (auto& value : varied_distance.values) value = static_cast<float>(static_cast<int>(rng() % 17) - 8);
            Workspace varied_work(nodes, capacity, k);
            const auto varied_stats = search<true>(varied, varied_distance, varied_labels.data(), 8, varied_route,
                capacity, k, true, trial % 2, varied_work, protected_ids.data(), protected_distances.data(), &events);
            replay(events, varied_work, protected_ids.data(), protected_distances.data(), k, varied_stats);
            require(varied_stats.ndc == varied_distance.total(), "random regional NDC mismatch");
            require(*std::max_element(varied_distance.calls.begin(), varied_distance.calls.end()) == 1, "random regional duplicate distance");
            replayed_events += events.size(); varied_distance.reset();
            search<false>(varied, varied_distance, varied_labels.data(), 8, varied_route,
                capacity, k, true, trial % 2, varied_work, plain.data(), distances.data());
            require(plain == protected_ids && distances == protected_distances && varied_distance.total() == varied_stats.ndc,
                    "random regional count/plain mismatch");
        }
        checks.push_back({{"name", "random_multiregion_trace_and_count_plain"}, {"status", "PASS"},
                          {"queries", 300}, {"trace_events", replayed_events}});
        acsg::Graph<int32_t> singleton(1, 0);
        Distance singleton_distance(1); singleton_distance.values[0] = -1;
        Route singleton_route; singleton_route.entry_count = 1; singleton_route.entries[0] = 0;
        Workspace singleton_work(1, 1, 1);
        const auto singleton_stats = search<true>(singleton, singleton_distance, nullptr, 1, singleton_route, 1, 1,
            false, false, singleton_work, plain.data(), distances.data(), &events);
        replay(events, singleton_work, plain.data(), distances.data(), 1, singleton_stats);
        require(plain[0] == 0 && distances[0] == -1 && singleton_stats.ndc == 1, "N=K=L=1 boundary mismatch");
        checks.push_back({{"name", "singleton_zero_degree_minimum_capacity"}, {"status", "PASS"}});
        std::cout << json({{"status", "PASS"}, {"seed", 2026090711}, {"tests", checks},
                          {"limitations", "Synthetic suite; full-data legacy parity and evaluator timing isolation are separate P1 gates"}}).dump(2) << '\n';
    } catch (const std::exception& error) {
        std::cerr << "REGIONAL_TEST_FAIL " << error.what() << '\n'; return 1;
    }
}

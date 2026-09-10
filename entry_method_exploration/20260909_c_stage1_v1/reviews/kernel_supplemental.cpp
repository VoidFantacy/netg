#include "../src/state_machine.hpp"
using namespace cstage1;

struct QueryDC : faiss::DistanceComputer {
    const float* query = nullptr;
    uint64_t count = 0;
    void set_query(const float* q) override { query = q; }
    float operator()(faiss::idx_t id) override {
        ++count;
        require(query != nullptr && id >= 0 && id < 3, "query DC input");
        const float delta = float(id) - query[0];
        return delta * delta;
    }
    float symmetric_dis(faiss::idx_t a, faiss::idx_t b) override {
        return float((a - b) * (a - b));
    }
};

int main(int argc, char** argv) {
    try {
        require(argc == 2 && !fs::exists(argv[1]), "new result path required");
        omp_set_num_threads(1);
        acsg::Graph<int32_t> graph(3, 3);
        std::fill(graph.data, graph.data + 9, -1);
        graph.at(0, 0) = 1; graph.at(0, 1) = 2;
        graph.at(1, 0) = 0; graph.at(1, 1) = 2;
        graph.at(2, 0) = 1; graph.at(2, 1) = 0;
        Engine engine(graph, 3, 1, {{"fixture", "exact-cap-terminal-query-binding"}});
        float q = 0, wrong_query = 100;
        QueryDC dc;
        Observer observer;
        auto exact = engine.initialize(&q, 3, 3, {0}, 0, dc, &observer);
        exact.set_additional_cap(2);
        dc.set_query(&wrong_query);
        engine.resume(exact, dc, unlimited, &observer);
        require(exact.natural_finished && !exact.cap_exhausted && !exact.row_active, "exact cap terminal classification");
        require(exact.ndc == 3 && exact.remaining() == 0 && dc.count == 3, "exact cap accounting");
        require(exact.top_ids() == std::vector<int>({0, 1, 2}), "DC query rebound IDs");
        require(exact.top_distances() == std::vector<float>({0, 1, 4}), "DC query rebound distances");
        require(observer.expanded_order == std::vector<int>({0, 1, 2}), "zero cost trailing expansion order");
        require(observer.distance_order == std::vector<int>({0, 1, 2}), "exact cap evaluation order");

        QueryDC partial_dc;
        Observer partial_observer;
        auto partial = engine.initialize(&q, 3, 3, {0}, 0, partial_dc, &partial_observer);
        partial.set_additional_cap(1);
        engine.resume(partial, partial_dc, unlimited, &partial_observer);
        require(partial.row_active && partial.cap_exhausted && !partial.natural_finished, "partial cap classification");
        require(partial.current_node == 0 && partial.neighbor_offset == 1 && !partial.visited.count(2), "partial row exact offset");
        auto restored = State::from_json(json::parse(partial.to_json().dump()));
        restored.remove_cap();
        partial_dc.set_query(&wrong_query);
        engine.resume(restored, partial_dc, unlimited, &partial_observer);
        require(restored.top_ids() == exact.top_ids() && restored.top_distances() == exact.top_distances(), "partial restore output");
        require(partial_dc.count == 3 && restored.ndc == 3, "partial restore no double charge");
        require(partial_observer.distance_order == observer.distance_order && partial_observer.expanded_order == observer.expanded_order,
                "partial restore full trajectory");

        const auto frozen = exact.to_json();
        const auto calls = dc.count;
        require(engine.inject(exact, 2, true, dc) == "early_finished", "terminal force is no-op");
        require(exact.to_json() == frozen && dc.count == calls, "terminal no-op preserves state and cost");
        write_json(argv[1], {{"status", "PASS"}, {"GT_accessed", false},
            {"checks", {"exact_cap_followed_by_visited_padding_natural_end", "zero_cost_trailing_expansions",
                        "independent_DC_wrong_query_rebound", "partial_offset_serialization_no_double_charge",
                        "terminal_injection_noop"}},
            {"native_or_branch_execution_count", 3}, {"initializations", 2},
            {"expanded_order", observer.expanded_order}, {"distance_order", observer.distance_order}});
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "INDEPENDENT_REVIEW_FAIL " << e.what() << '\n';
        return 1;
    }
}

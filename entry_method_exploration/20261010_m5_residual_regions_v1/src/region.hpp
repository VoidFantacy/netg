#pragma once
#include "runtime.hpp"

// One-hop append-only region candidates. The caller supplies the current query's
// naturally completed native main packet/DC/visited epoch. This helper never
// sets or advances main-vt, never calls search_new, and never copies base/index.
namespace exp172::m5 {

struct RegionStats {
    // Original counters retained: dots/commits describe the R+C M5 stage;
    // row_reads also counts the additional physical seed target-row scan.
    PostStats post{};
    uint64_t queries = 0;
    uint64_t seed_candidates = 0, seeds_selected = 0, seed_duplicate_skips = 0;
    uint64_t seed_posting_slots = 0, seed_rows = 0, graph_slots = 0;
    uint64_t new_distances = 0;
    uint64_t main_seen_skips = 0, c_duplicate_skips = 0, x_duplicate_skips = 0;
    uint64_t invalid_neighbor_skips = 0;
    uint64_t extension_nonfinite_failures = 0, extension_commits = 0;
};

// Diagnostic-only fixed storage; nullptr means no per-candidate trace writes.
// nc/nx count actually returned scalar words, including a failing nonfinite
// word; use the status flags before applying an independent finite oracle.
struct CandidateAudit {
    int K = 0, planned_candidates = 0, nc = 0, nx = 0, nseeds = 0;
    bool r_rescored_complete = false;
    bool m5_committed = false, extension_aborted = false;
    std::array<faiss::idx_t, 100> r_ids{};
    std::array<float, 100> r_distances{};
    std::array<int32_t, 24> c_ids{};
    std::array<float, 24> c_distances{};
    std::array<int32_t, 96> x_ids{};
    std::array<float, 96> x_distances{};
    std::array<int32_t, 3> seeds{{-1, -1, -1}};
    std::array<float, 3> seed_distances{};
    std::array<int32_t, 3> seed_route_positions{{-1, -1, -1}};
};

// Incremental timed ID scratch beyond the original Posting's buffers. Other
// fixed local state/Record/loop variables and optional audit must also be
// accounted for by the runner's complete resident/stack accounting.
inline constexpr size_t region_candidate_id_scratch_bytes() {
    return sizeof(std::array<int32_t, 96>);
}

inline void apply(
        faiss::DistanceComputer& dc,
        const std::array<int32_t, 3>& route,
        int K,
        faiss::idx_t* I,
        float* D,
        const acsg::Graph<int32_t>& graph,
        const faiss::VisitedTable& vt,
        Posting& posting,
        int extra_cap,
        bool first_seed,
        RegionStats* stats = nullptr,
        CandidateAudit* audit = nullptr) {
    require(K == 1 || K == 100, "region actual K1/K100");
    require(extra_cap == 0 || extra_cap == 24 || extra_cap == 96,
            "region frozen extra-distance cap 0/24/96");
    require(!posting.global, "region requires route-indexed posting rows");
    require(graph.N > 0 && graph.K > 0 && graph.data &&
                    posting.base_n == uint32_t(graph.N) &&
                    vt.visited.size() == size_t(graph.N),
            "region actual graph/base/visited domain");
    if (stats) ++stats->queries;
    if (audit) {
        *audit = CandidateAudit{};
        audit->K = K;
        for (int j = 0; j < K; ++j) {
            audit->r_ids[j] = I[j];
            audit->r_distances[j] = D[j];
        }
    }
    if (posting.empty) return;
    PostStats* ps = stats ? &stats->post : nullptr;

    // Exactly the original plan on the ORIGINAL GT packet: same route/slot
    // traversal, remove-R/first-occurrence dedup, lookup/fallback and counters.
    // Save the row slots here; replanning after M5 would discard rescued seeds.
    std::array<int, 3> row_slots{{-1, -1, -1}};
    int nc = 0;
    auto append = [&](int32_t id) {
        for (int j = 0; j < K; ++j) if (I[j] == id) return;
        for (int j = 0; j < nc; ++j) if (posting.candidate[j] == id) return;
        require(nc < 24, "region original posting candidate cap");
        posting.candidate[nc++] = id;
    };
    for (int row = 0; row < 3; ++row) {
        const int slot = posting.lookup(route[row], ps);
        if (slot < 0) return; // Original M5 all-row fallback, no partial C.
        row_slots[row] = slot;
        if (ps) ++ps->row_reads;
        for (int j = 0; j < posting.counts[slot]; ++j)
            append(posting.targets[size_t(slot) * 8 + j]);
    }
    if (ps) ps->candidates += nc;
    if (audit) audit->planned_candidates = nc;
    if (nc <= 0) return;

    // Reproduce old fresh-scalar R then C score order. Keep all original C
    // words in records[K+j] for seed selection; no second seed callback.
    for (int j = 0; j < K; ++j) {
        posting.records[j] = {I[j], std::numeric_limits<float>::max(),
                              uint32_t(j), I[j] < 0};
        if (I[j] >= 0) {
            posting.records[j].distance = dc(I[j]);
            if (ps) ++ps->dots;
            if (audit) audit->r_distances[j] = posting.records[j].distance;
            if (!std::isfinite(posting.records[j].distance)) {
                if (ps) ++ps->nonfinite_failures;
                return; // Untouched original GT packet, exactly old M5.
            }
        }
    }
    if (audit) audit->r_rescored_complete = true;
    for (int j = 0; j < nc; ++j) {
        const float value = dc(posting.candidate[j]);
        if (ps) ++ps->dots;
        if (audit) {
            audit->c_ids[j] = posting.candidate[j];
            audit->c_distances[j] = value;
            audit->nc = j + 1;
        }
        if (!std::isfinite(value)) {
            if (ps) ++ps->nonfinite_failures;
            return;
        }
        posting.records[K + j] = {posting.candidate[j], value,
                                  uint32_t(K + j), false};
    }

    auto merge_record = [&](const Posting::Record& incoming) {
        if (posting.heap[0].padding ||
                incoming.distance < posting.heap[0].distance) {
            std::pop_heap(posting.heap.begin(), posting.heap.begin() + K,
                          Posting::better);
            posting.heap[K - 1] = incoming;
            std::push_heap(posting.heap.begin(), posting.heap.begin() + K,
                           Posting::better);
        }
    };
    auto emit_sorted = [&]() {
        std::sort(posting.heap.begin(), posting.heap.begin() + K,
                  Posting::better);
        for (int j = 0; j < K; ++j) {
            I[j] = posting.heap[j].padding ? -1 : posting.heap[j].id;
            D[j] = posting.heap[j].padding
                    ? std::numeric_limits<float>::max()
                    : posting.heap[j].distance;
        }
    };
    std::copy(posting.records.begin(), posting.records.begin() + K,
              posting.heap.begin());
    std::make_heap(posting.heap.begin(), posting.heap.begin() + K,
                   Posting::better);
    for (int j = 0; j < nc; ++j) merge_record(posting.records[K + j]);
    emit_sorted(); // Full successful old-M5 packet is the extension fallback.
    if (ps) ++ps->commits;
    if (audit) audit->m5_committed = true;
    if (extra_cap == 0) return;

    // Each row picks its best original-C word (or first slot for control).
    // Duplicate winners are suppressed in route order WITHOUT replacement.
    // A different posting-row origin is not a proven different basin.
    std::array<int, 3> seed_indices{{-1, -1, -1}};
    for (int row = 0; row < 3; ++row) {
        const int slot = row_slots[row];
        if (ps) ++ps->row_reads; // Physical second target-row scan is paid.
        int winner = -1;
        for (int j = 0; j < posting.counts[slot]; ++j) {
            if (stats) ++stats->seed_posting_slots;
            const int32_t id = posting.targets[size_t(slot) * 8 + j];
            int ci = -1;
            for (int c = 0; c < nc; ++c) {
                if (posting.candidate[c] == id) { ci = c; break; }
            }
            if (ci < 0) continue; // Original-R target is never a seed here.
            if (stats) ++stats->seed_candidates;
            if (winner < 0 ||
                    Posting::better(posting.records[K + ci],
                                    posting.records[K + winner]))
                winner = ci;
            if (first_seed) break;
        }
        if (winner < 0) continue;
        bool duplicate = false;
        for (int earlier = 0; earlier < row; ++earlier) {
            if (seed_indices[earlier] == winner) { duplicate = true; break; }
        }
        if (duplicate) {
            if (stats) ++stats->seed_duplicate_skips;
            continue;
        }
        seed_indices[row] = winner;
        if (stats) ++stats->seeds_selected;
        if (audit) {
            const int a = audit->nseeds++;
            audit->seeds[a] = posting.candidate[winner];
            audit->seed_distances[a] = posting.records[K + winner].distance;
            audit->seed_route_positions[a] = row;
        }
    }

    // Logical result heap has K entries; retained records keep their ORIGINAL
    // R/C priorities. New arrivals are strictly later than every old R/C.
    std::make_heap(posting.heap.begin(), posting.heap.begin() + K,
                   Posting::better);
    std::array<int32_t, 96> x_ids{};
    int nx = 0;
    for (int graph_slot = 0; graph_slot < graph.K && nx < extra_cap;
            ++graph_slot) {
        for (int row = 0; row < 3 && nx < extra_cap; ++row) {
            const int ci = seed_indices[row];
            if (ci < 0) continue;
            if (stats) {
                if (graph_slot == 0) ++stats->seed_rows;
                ++stats->graph_slots;
            }
            const int32_t id = graph.at(posting.candidate[ci], graph_slot);
            if (id < 0 || id >= graph.N) {
                if (stats) ++stats->invalid_neighbor_skips;
                continue;
            }
            if (vt.get(id)) {
                if (stats) ++stats->main_seen_skips;
                continue;
            }
            bool duplicate = false;
            for (int c = 0; c < nc; ++c) {
                if (posting.candidate[c] == id) { duplicate = true; break; }
            }
            if (duplicate) {
                if (stats) ++stats->c_duplicate_skips;
                continue;
            }
            for (int x = 0; x < nx; ++x) {
                if (x_ids[x] == id) { duplicate = true; break; }
            }
            if (duplicate) {
                if (stats) ++stats->x_duplicate_skips;
                continue;
            }
            // No main-vt write, advance, query reset or fabricated callback.
            const float value = dc(id);
            if (stats) ++stats->new_distances;
            x_ids[nx] = id;
            if (audit) {
                audit->x_ids[nx] = id;
                audit->x_distances[nx] = value;
                audit->nx = nx + 1;
            }
            if (!std::isfinite(value)) {
                if (stats) ++stats->extension_nonfinite_failures;
                if (audit) audit->extension_aborted = true;
                return; // I/D remain full old M5; all incurred costs remain.
            }
            const Posting::Record incoming{
                id, value, uint32_t(K + nc + nx), false};
            ++nx;
            merge_record(incoming);
        }
    }
    if (nx == 0) return; // Preserve old packet without another output pass.
    emit_sorted();
    if (stats) ++stats->extension_commits;
}

// Runner-friendly parameter-order alias; the original-epoch contract is the
// same. It deliberately receives graph/vt by const reference.
inline void applyRegion(
        faiss::DistanceComputer& dc,
        const acsg::Graph<int32_t>& graph,
        const faiss::VisitedTable& vt,
        const std::array<int32_t, 3>& route,
        int K, faiss::idx_t* I, float* D, Posting& posting,
        int extra_cap, bool first_seed,
        RegionStats* stats = nullptr, CandidateAudit* audit = nullptr) {
    apply(dc, route, K, I, D, graph, vt, posting, extra_cap, first_seed,
          stats, audit);
}

} // namespace exp172::m5

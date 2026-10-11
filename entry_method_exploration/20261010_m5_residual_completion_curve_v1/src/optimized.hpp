#pragma once
#include "region.hpp"

// E176 cost-only M5/REG optimization. The old E175 runtime/region are preserved.
// Caller contract: I/D are the immediately completed native search_new packet
// for this dc's unchanged query, base, metric, and floating-point environment.
// Native search_new copies the actual dc(id) word from its result pool to D.
// Repeating the same stateless Flat scalar callback therefore supplies the same
// word; a mathematical IP identity alone is NOT enough for this contract.
// The untimed non-null audit path verifies EVERY used finite cached R word.
// Timed nullptr does not perform these verification distance calls.
namespace exp172::m5 {

struct OptimizedStats : RegionStats {
    uint64_t r_cache_queries = 0, r_cache_hits = 0;
    uint64_t r_cache_fallback_queries = 0;
    uint64_t r_word_checks = 0, r_word_check_dots = 0, r_word_mismatches = 0;
    // First posting scan stores row-slot -> C-index; no second target scan.
    uint64_t seed_mapping_slots = 0;
    // Invalid tail slots bypassed by the bound, not physical graph reads.
    uint64_t trimmed_invalid_slots = 0;
};

inline bool optimized_word_equal(float a, float b) {
    return !std::memcmp(&a, &b, sizeof(float));
}

// Optional frozen seed-row metadata. Only H*8 slot bounds are retained; no graph
// or base copy, target-ID hash, candidate-list reordering, or new learned data.
// Each bound is one past the LAST in-domain neighbor, so internal invalid slots
// remain in their original positions. A bound of zero means all slots invalid.
// Binding uses the actual loaded graph/posting objects; their contents must be
// protected by the caller's source/live-word and immutable-data guards.
struct OptimizedLayout {
    const Posting* posting_identity = nullptr;
    const int32_t* graph_identity = nullptr;
    const int32_t* target_identity = nullptr;
    const uint8_t* count_identity = nullptr;
    int graph_n = 0, graph_k = 0;
    std::vector<uint32_t> end_slots;
    uint64_t startup_graph_reads = 0, startup_trimmed_slots = 0;
    double startup_seconds = 0;

    OptimizedLayout(const acsg::Graph<int32_t>& graph, const Posting& posting)
            : posting_identity(&posting), graph_identity(graph.data),
              target_identity(posting.targets.data()),
              count_identity(posting.counts.data()),
              graph_n(graph.N), graph_k(graph.K) {
        require(!posting.global && graph.N > 0 && graph.K > 0 && graph.data &&
                        posting.base_n == uint32_t(graph.N),
                "optimized layout actual route posting/graph domain");
        const auto before = Clock::now();
        end_slots.assign(posting.targets.size(), 0);
        require(posting.targets.size() == size_t(posting.H) * 8 &&
                        posting.counts.size() == posting.H,
                "optimized layout complete posting shape");
        for (size_t row = 0; row < posting.H; ++row) {
            require(posting.counts[row] <= 8, "optimized layout row capacity");
            for (int j = 0; j < posting.counts[row]; ++j) {
                const size_t p = row * 8 + size_t(j);
                const int32_t seed = posting.targets[p];
                require(seed >= 0 && seed < graph.N,
                        "optimized layout seed in graph domain");
                int end = graph.K;
                while (end > 0) {
                    const int32_t id = graph.at(seed, end - 1);
                    ++startup_graph_reads;
                    if (id >= 0 && id < graph.N) break;
                    --end;
                }
                end_slots[p] = uint32_t(end);
                startup_trimmed_slots += uint64_t(graph.K - end);
            }
        }
        startup_seconds = seconds(before);
    }

    bool bound_to(const acsg::Graph<int32_t>& graph,
                  const Posting& posting) const {
        return posting_identity == &posting && graph_identity == graph.data &&
                target_identity == posting.targets.data() &&
                count_identity == posting.counts.data() &&
                graph_n == graph.N && graph_k == graph.K &&
                end_slots.size() == posting.targets.size();
    }
    size_t resident_bytes() const {
        return sizeof(*this) + sizeof(uint32_t) * end_slots.capacity() +
                (end_slots.capacity() ? 64 : 0);
    }
};

// Fixed incremental timed local arrays: original row-to-C membership, each C's
// tail bound, three selected seed indices, and X dedup IDs. Posting already owns
// R/C records and K-heap. Runner also accounts for ordinary stack/scalars and
// optional CandidateAudit, which must only be allocated in the untimed rerun.
inline constexpr size_t optimized_fixed_array_scratch_bytes() {
    return sizeof(std::array<std::array<int, 8>, 3>) +
            sizeof(std::array<int, 24>) + sizeof(std::array<int, 3>) +
            sizeof(std::array<int32_t, 96>);
}

inline void applyOptimized(
        faiss::DistanceComputer& dc,
        const acsg::Graph<int32_t>& graph,
        const faiss::VisitedTable& vt,
        const std::array<int32_t, 3>& route,
        int K, faiss::idx_t* I, float* D, Posting& posting,
        int extra_cap, bool first_seed,
        OptimizedStats* stats = nullptr, CandidateAudit* audit = nullptr,
        const OptimizedLayout* layout = nullptr) {
    require(K == 1 || K == 100, "optimized actual K1/K100");
    require(extra_cap == 0 || extra_cap == 24 || extra_cap == 96,
            "optimized preserved region extra cap 0/24/96");
    require(!posting.global && graph.N > 0 && graph.K > 0 && graph.data &&
                    posting.base_n == uint32_t(graph.N) &&
                    vt.visited.size() == size_t(graph.N),
            "optimized actual graph/base/visited domain");
    if (layout)
        require(layout->bound_to(graph, posting),
                "optimized layout bound to immutable live graph/posting");

    // Unknown/negative non-padding IDs are not eligible native packets. A
    // positive out-of-domain ID is fatal rather than an unsafe DC invocation.
    // Cached nonfinite scores (or noncanonical negative padding) take exactly
    // the old fresh-R path; all its incurred costs/status are retained.
    bool cache_eligible = true;
    for (int j = 0; j < K; ++j) {
        require(I[j] < graph.N, "optimized original R upper domain");
        if (I[j] < -1 || (I[j] >= 0 && !std::isfinite(D[j])))
            cache_eligible = false;
    }
    if (!cache_eligible) {
        if (stats) ++stats->r_cache_fallback_queries;
        applyRegion(dc, graph, vt, route, K, I, D, posting, extra_cap,
                    first_seed, stats, audit);
        return;
    }
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

    // Same all-three-row plan on ORIGINAL R. Save every physical posting slot's
    // original-C index, including duplicate targets shared by routed rows.
    std::array<std::array<int, 8>, 3> row_to_c;
    for (auto& row : row_to_c) row.fill(-1);
    std::array<int, 24> candidate_ends;
    candidate_ends.fill(graph.K);
    int nc = 0;
    auto append = [&](int32_t id) {
        for (int j = 0; j < K; ++j) if (I[j] == id) return -1;
        for (int j = 0; j < nc; ++j)
            if (posting.candidate[j] == id) return j;
        require(nc < 24, "optimized original posting candidate cap");
        posting.candidate[nc] = id;
        return nc++;
    };
    for (int row = 0; row < 3; ++row) {
        const int slot = posting.lookup(route[row], ps);
        if (slot < 0) return; // Same all-row fallback; no partial candidates.
        if (ps) ++ps->row_reads;
        for (int j = 0; j < posting.counts[slot]; ++j) {
            const size_t p = size_t(slot) * 8 + size_t(j);
            const int ci = append(posting.targets[p]);
            row_to_c[row][j] = ci;
            if (stats) ++stats->seed_mapping_slots;
            if (ci >= 0 && layout) candidate_ends[ci] = int(layout->end_slots[p]);
        }
    }
    if (ps) ps->candidates += nc;
    if (audit) audit->planned_candidates = nc;
    if (nc <= 0) return;
    if (stats) ++stats->r_cache_queries;

    for (int j = 0; j < K; ++j) {
        posting.records[j] = {I[j], std::numeric_limits<float>::max(),
                              uint32_t(j), I[j] < 0};
        if (I[j] >= 0) {
            posting.records[j].distance = D[j];
            if (stats) ++stats->r_cache_hits;
            if (audit) {
                const float checked = dc(I[j]);
                if (ps) ++ps->dots; // Actual untimed verification call.
                if (stats) {
                    ++stats->r_word_checks;
                    ++stats->r_word_check_dots;
                }
                const bool equal = optimized_word_equal(checked, D[j]);
                if (!equal && stats) ++stats->r_word_mismatches;
                require(equal,
                        "cached native R word differs from actual fresh scalar");
            }
        }
    }
    // In this helper the legacy flag denotes complete finite R words: with
    // audit present they were also independently CALLBACK-rechecked above.
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
            return; // Original native R remains untouched.
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
    emit_sorted(); // Exact original M5 success packet is the X-failure fallback.
    if (ps) ++ps->commits;
    if (audit) audit->m5_committed = true;
    if (extra_cap == 0) return;

    std::array<int, 3> seed_indices{{-1, -1, -1}};
    int max_end = 0, nseeds = 0;
    for (int row = 0; row < 3; ++row) {
        int winner = -1;
        // A cached -1 marks either original-R exclusion or unused row padding.
        // For valid targets, mapping order is exactly the original row order.
        for (int j = 0; j < 8; ++j) {
            const int ci = row_to_c[row][j];
            if (ci < 0) continue;
            if (stats) ++stats->seed_candidates;
            if (winner < 0 ||
                    Posting::better(posting.records[K + ci],
                                    posting.records[K + winner])) winner = ci;
            if (first_seed) break;
        }
        if (winner < 0) continue;
        bool duplicate = false;
        for (int earlier = 0; earlier < row; ++earlier)
            if (seed_indices[earlier] == winner) { duplicate = true; break; }
        if (duplicate) {
            if (stats) ++stats->seed_duplicate_skips;
            continue; // No substitute seed, same as old REG.
        }
        seed_indices[row] = winner;
        max_end = std::max(max_end, candidate_ends[winner]);
        ++nseeds;
        if (stats) {
            ++stats->seeds_selected;
            ++stats->seed_rows;
        }
        if (audit) {
            const int a = audit->nseeds++;
            audit->seeds[a] = posting.candidate[winner];
            audit->seed_distances[a] = posting.records[K + winner].distance;
            audit->seed_route_positions[a] = row;
        }
    }

    std::make_heap(posting.heap.begin(), posting.heap.begin() + K,
                   Posting::better);
    std::array<int32_t, 96> x_ids{};
    int nx = 0;
    for (int graph_slot = 0; graph_slot < max_end && nx < extra_cap;
            ++graph_slot) {
        for (int row = 0; row < 3 && nx < extra_cap; ++row) {
            const int ci = seed_indices[row];
            if (ci < 0) continue;
            if (graph_slot >= candidate_ends[ci]) {
                if (stats) ++stats->trimmed_invalid_slots;
                continue;
            }
            if (stats) ++stats->graph_slots;
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
            for (int c = 0; c < nc; ++c)
                if (posting.candidate[c] == id) { duplicate = true; break; }
            if (duplicate) {
                if (stats) ++stats->c_duplicate_skips;
                continue;
            }
            for (int x = 0; x < nx; ++x)
                if (x_ids[x] == id) { duplicate = true; break; }
            if (duplicate) {
                if (stats) ++stats->x_duplicate_skips;
                continue;
            }
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
                return; // Preserve fully merged M5 and all incurred costs.
            }
            const Posting::Record incoming{
                id, value, uint32_t(K + nc + nx), false};
            ++nx;
            merge_record(incoming);
        }
    }
    // If cap was not filled, the old loop also scans these all-invalid tails.
    // This is an avoided-slot count, separate from actual graph_slots/skips.
    if (stats && nx < extra_cap)
        stats->trimmed_invalid_slots +=
                uint64_t(graph.K - max_end) * uint64_t(nseeds);
    if (nx == 0) return;
    emit_sorted();
    if (stats) ++stats->extension_commits;
}

} // namespace exp172::m5

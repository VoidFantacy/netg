#include "region.hpp"
#include "optimized.hpp"
#include "residual.hpp"
#include <limits>

using namespace exp172;
namespace {

struct Method {
    std::string name, table;
    m5::Posting* posting = nullptr;
    int extra_cap = 0;
    bool first_seed = false;
    bool nsg = false;
    bool optimized = false;
    std::string family, completion_family;
    std::map<std::pair<int, int>, std::unique_ptr<m5::CompletionTable>> completion_models;
    std::unique_ptr<m5::OptimizedLayout> layout;
};

struct Stats {
    m5::OptimizedStats region;
    uint64_t domain_checks = 0, domain_fallbacks = 0;
    uint64_t main_packet_checks = 0, cachedmain_valid_R_checks = 0;
    uint64_t cachedmain_R_word_mismatches = 0;
};

struct TraceSummary {
    uint64_t queries = 0, legal_queries = 0, c_words = 0, x_words = 0;
    uint64_t m5_commits = 0, extension_aborts = 0;
    std::array<uint64_t, 25> c_hist{};
    std::array<uint64_t, 97> x_hist{};
    std::array<uint64_t, 4> seed_hist{};
};

struct OriginalPacket {
    std::array<faiss::idx_t, 100> ids;
    std::array<float, 100> distances;
};

// Eight metadata words and 120 candidate-ID slots = exactly 512 bytes/query.
// Scalar score words exist only in the untimed CandidateAudit and are checked
// against an independent DC before this bounded ID-only trace is serialized.
constexpr size_t trace_words_per_query = 128, trace_c_offset = 8,
                 trace_x_offset = 32;

bool word_equal(float a, float b) { return !memcmp(&a, &b, sizeof(float)); }

bool legal_query(const float* q, size_t d) {
    if ((_mm_getcsr() & 0xffc0U) != 0x1f80U) return false;
    for (size_t j = 0; j < d; ++j) {
        uint32_t bits;
        memcpy(&bits, q + j, 4);
        if ((bits & 0x7fffffffU) > 0x49800000U) return false;
    }
    return true;
}

void same_route(const Batch& a, const Batch& b) {
    require(a.n == b.n && a.entries == b.entries &&
            !memcmp(a.profile_distances.data(), b.profile_distances.data(),
                    a.profile_distances.size() * sizeof(float)),
            "unchanged original GT route ID/profile words");
}

void check_nsg_route(const Batch& batch, int32_t enterpoint) {
    for (size_t i = 0; i < batch.n; ++i) {
        require(batch.entries[3 * i] == enterpoint &&
                batch.entries[3 * i + 1] == -1 &&
                batch.entries[3 * i + 2] == -1 && batch.route_ndc[i] == 0,
                "original NSG constant entry packet and zero route NDC");
        for (int j = 0; j < 3; ++j)
            require(word_equal(batch.profile_distances[3 * i + j], 0.f),
                    "NSG unused profile words are positive zero");
    }
}

struct LinearItem { int32_t id; float distance; int priority; };

// This oracle deliberately uses linear worst-slot replacement, not the runtime
// heap, runtime better(), runtime plan(), or runtime candidate scratch.
bool linear_worse(const LinearItem& a, const LinearItem& b) {
    if ((a.id < 0) != (b.id < 0)) return a.id < 0;
    if (a.distance != b.distance) return a.distance > b.distance;
    return a.priority > b.priority;
}

void linear_insert(std::vector<LinearItem>& packet, LinearItem incoming) {
    size_t worst = 0;
    for (size_t j = 1; j < packet.size(); ++j)
        if (linear_worse(packet[j], packet[worst])) worst = j;
    if (packet[worst].id < 0 || incoming.distance < packet[worst].distance)
        packet[worst] = incoming;
}

void check_linear_packet(std::vector<LinearItem> packet,
                         const faiss::idx_t* ids, const float* distances) {
    std::sort(packet.begin(), packet.end(), [](const LinearItem& a,
                                               const LinearItem& b) {
        return linear_worse(b, a);
    });
    for (size_t j = 0; j < packet.size(); ++j) {
        const int32_t id = packet[j].id < 0 ? -1 : packet[j].id;
        const float value = id < 0 ? std::numeric_limits<float>::max()
                                   : packet[j].distance;
        require(ids[j] == id && word_equal(distances[j], value),
                "independent linear region ID/score-word oracle");
    }
}

void check_original_packet(int K, const faiss::idx_t* original,
                            const float* old_distances,
                            const faiss::idx_t* actual,
                            const float* actual_distances) {
    for (int j = 0; j < K; ++j)
        require(original[j] == actual[j] &&
                word_equal(old_distances[j], actual_distances[j]),
                "region fallback preserves original GT words");
}

int independent_slot(const m5::Posting& post, int32_t label) {
    const auto it = std::lower_bound(post.sorted_labels.begin(),
                                     post.sorted_labels.end(), label);
    if (it == post.sorted_labels.end() || *it != label) return -1;
    return post.sorted_slots[size_t(it - post.sorted_labels.begin())];
}

// Runs after the untimed region call while the ORIGINAL main visited epoch is
// still live. Recomputes every actual R/C/X scalar word with a separate DC,
// independently derives C, seed rows and the complete X arrival sequence, and
// rebuilds the result using only the linear oracle above.
void audit_region(faiss::DistanceComputer& fresh,
                  const acsg::Graph<int32_t>& graph,
                  const faiss::VisitedTable& vt,
                  const std::array<int32_t, 3>& route, const Method& method,
                  int K, const faiss::idx_t* original,
                  const float* original_distances,
                  const faiss::idx_t* actual, const float* actual_distances,
                  const m5::CandidateAudit& audit) {
    const auto& post = *method.posting;
    require(audit.K == K && audit.nc >= 0 && audit.nc <= 24 &&
            audit.nx >= 0 && audit.nx <= method.extra_cap &&
            audit.nseeds >= 0 && audit.nseeds <= 3,
            "region trace actual K/C/X/seed budgets");
    for (int j = 0; j < K; ++j)
        require(audit.r_ids[j] == original[j], "trace original GT R IDs");

    std::array<int, 3> slots{{-1, -1, -1}};
    std::vector<int32_t> c;
    bool missing_row = false;
    if (!post.empty) for (int row = 0; row < 3; ++row) {
        slots[row] = independent_slot(post, route[row]);
        if (slots[row] < 0) { missing_row = true; break; }
        for (int j = 0; j < post.counts[slots[row]]; ++j) {
            const int32_t id = post.targets[size_t(slots[row]) * 8 + j];
            bool in_r = false;
            for (int r = 0; r < K; ++r) in_r = in_r || original[r] == id;
            if (!in_r && std::find(c.begin(), c.end(), id) == c.end())
                c.push_back(id);
        }
    }
    if (missing_row) c.clear();
    require(audit.planned_candidates == int(c.size()),
            "independent original-R posting candidate plan");
    if (c.empty()) {
        require(audit.nc == 0 && audit.nx == 0 && audit.nseeds == 0 &&
                !audit.m5_committed && !audit.extension_aborted,
                "empty/fallback region has no extra work");
        check_original_packet(K, original, original_distances, actual,
                              actual_distances);
        return;
    }

    std::vector<LinearItem> packet;
    for (int j = 0; j < K; ++j) {
        const float value = original[j] < 0
                ? std::numeric_limits<float>::max() : fresh(original[j]);
        if (original[j] >= 0)
            require(word_equal(value, audit.r_distances[j]),
                    "independently recomputed R score word");
        if (!std::isfinite(value)) {
            require(!audit.r_rescored_complete && !audit.m5_committed &&
                    audit.nc == 0 && audit.nx == 0,
                    "nonfinite R trace/fallback status");
            check_original_packet(K, original, original_distances, actual,
                                  actual_distances);
            return;
        }
        packet.push_back({int32_t(original[j]), value, j});
    }
    require(audit.r_rescored_complete, "complete finite R re-score trace");
    std::vector<float> c_values;
    for (size_t j = 0; j < c.size(); ++j) {
        require(audit.nc > int(j) && audit.c_ids[j] == c[j],
                "independent complete C arrival IDs");
        const float value = fresh(c[j]);
        require(word_equal(value, audit.c_distances[j]),
                "independently recomputed C score word");
        if (!std::isfinite(value)) {
            require(audit.nc == int(j + 1) && !audit.m5_committed &&
                    audit.nx == 0 && audit.nseeds == 0,
                    "nonfinite C trace/fallback status");
            check_original_packet(K, original, original_distances, actual,
                                  actual_distances);
            return;
        }
        c_values.push_back(value);
        linear_insert(packet, {c[j], value, K + int(j)});
    }
    require(audit.nc == int(c.size()) && audit.m5_committed,
            "all finite C words committed before extension");
    const auto m5_packet = packet;
    if (method.extra_cap == 0) {
        require(audit.nx == 0 && audit.nseeds == 0 &&
                !audit.extension_aborted, "zero-cap intervention no extension");
        check_linear_packet(packet, actual, actual_distances);
        return;
    }

    std::array<int, 3> winners{{-1, -1, -1}};
    int selected = 0;
    for (int row = 0; row < 3; ++row) {
        int winner = -1;
        for (int j = 0; j < post.counts[slots[row]]; ++j) {
            const int32_t id = post.targets[size_t(slots[row]) * 8 + j];
            const auto it = std::find(c.begin(), c.end(), id);
            if (it == c.end()) continue;
            const int ci = int(it - c.begin());
            if (winner < 0 || c_values[ci] < c_values[winner] ||
                    (c_values[ci] == c_values[winner] && ci < winner))
                winner = ci;
            if (method.first_seed) break;
        }
        if (winner < 0 ||
                std::find(winners.begin(), winners.begin() + row, winner) !=
                        winners.begin() + row) continue;
        winners[row] = winner;
        require(selected < audit.nseeds && audit.seeds[selected] == c[winner] &&
                audit.seed_route_positions[selected] == row &&
                word_equal(audit.seed_distances[selected], c_values[winner]),
                "independent seed choice/order/origin/score");
        ++selected;
    }
    require(audit.nseeds == selected, "independent seed count/no replacement");

    std::vector<int32_t> x;
    for (int slot = 0; slot < graph.K && int(x.size()) < method.extra_cap;
            ++slot) {
        for (int row = 0; row < 3 && int(x.size()) < method.extra_cap; ++row) {
            if (winners[row] < 0) continue;
            const int32_t id = graph.at(c[winners[row]], slot);
            if (id < 0 || id >= graph.N || vt.get(id) ||
                    std::find(c.begin(), c.end(), id) != c.end() ||
                    std::find(x.begin(), x.end(), id) != x.end()) continue;
            for (int r = 0; r < K; ++r)
                require(original[r] != id, "X excludes original GT R");
            const size_t xi = x.size();
            require(audit.nx > int(xi) && audit.x_ids[xi] == id,
                    "independent legal/unseen/unique complete X arrival");
            const float value = fresh(id);
            require(word_equal(value, audit.x_distances[xi]),
                    "independently recomputed X score word");
            x.push_back(id);
            if (!std::isfinite(value)) {
                require(audit.extension_aborted && audit.nx == int(x.size()),
                        "failed X word counts within score cap");
                check_linear_packet(m5_packet, actual, actual_distances);
                return;
            }
            linear_insert(packet, {id, value, K + int(c.size()) + int(xi)});
        }
    }
    require(audit.nx == int(x.size()) && !audit.extension_aborted,
            "independent complete X count/status");
    check_linear_packet(packet, actual, actual_distances);
}

// Separate BANK oracle: route-aligned winners may repeat; no graph/visited
// filter or REG seed suppression applies to a frozen residual completion row.
const std::array<int32_t, 7>* independent_completion_row(
        const m5::CompletionTable& table, int32_t route, int32_t winner) {
    const std::pair<int32_t, int32_t> key{route, table.conditioned ? winner : -1};
    size_t lo = 0, hi = table.rows.size();
    while (lo < hi) {
        const size_t mid = lo + (hi - lo) / 2;
        const auto& row = table.rows[mid];
        if (std::pair<int32_t, int32_t>{row[0], row[1]} < key) lo = mid + 1;
        else hi = mid;
    }
    if (lo == table.rows.size()) return nullptr;
    const auto& row = table.rows[lo];
    return std::pair<int32_t, int32_t>{row[0], row[1]} == key ? &row : nullptr;
}

void audit_completion(faiss::DistanceComputer& fresh,
        const std::array<int32_t, 3>& route, const m5::Posting& post,
        const m5::CompletionTable& table, int K,
        const faiss::idx_t* original, const float* old_distances,
        const faiss::idx_t* actual, const float* actual_distances,
        const m5::CandidateAudit& audit) {
    require(audit.K == K && audit.nc >= 0 && audit.nc <= 24 &&
            audit.nx >= 0 && audit.nx <= 12 && audit.nseeds >= 0 && audit.nseeds <= 3,
            "completion actual C24/X12/route winner budgets");
    for (int j = 0; j < K; ++j) require(audit.r_ids[j] == original[j], "completion original R IDs");
    std::array<int, 3> slots{{-1, -1, -1}};
    std::vector<int32_t> c;
    bool missing_row = false;
    if (!post.empty) for (int row = 0; row < 3; ++row) {
        slots[row] = independent_slot(post, route[row]);
        if (slots[row] < 0) { missing_row = true; break; }
        for (int j = 0; j < post.counts[slots[row]]; ++j) {
            const int32_t id = post.targets[size_t(slots[row]) * 8 + j];
            bool in_r = false;
            for (int r = 0; r < K; ++r) in_r = in_r || original[r] == id;
            if (!in_r && std::find(c.begin(), c.end(), id) == c.end()) c.push_back(id);
        }
    }
    if (missing_row) c.clear();
    require(audit.planned_candidates == int(c.size()), "completion independently reconstructed original C");
    if (c.empty()) {
        require(audit.nc == 0 && audit.nx == 0 && audit.nseeds == 0 &&
                !audit.m5_committed && !audit.extension_aborted, "completion empty original C has no bank action");
        check_original_packet(K, original, old_distances, actual, actual_distances);
        return;
    }
    std::vector<LinearItem> packet;
    for (int j = 0; j < K; ++j) {
        const float v = original[j] < 0 ? std::numeric_limits<float>::max() : fresh(original[j]);
        if (original[j] >= 0) require(word_equal(v, audit.r_distances[j]), "completion independent fresh R word");
        if (!std::isfinite(v)) {
            require(!audit.r_rescored_complete && !audit.m5_committed && audit.nc == 0 && audit.nx == 0,
                    "completion nonfinite R fail closed");
            check_original_packet(K, original, old_distances, actual, actual_distances);
            return;
        }
        packet.push_back({int32_t(original[j]), v, j});
    }
    require(audit.r_rescored_complete, "completion complete finite R words");
    std::vector<float> cv;
    for (size_t j = 0; j < c.size(); ++j) {
        require(audit.nc > int(j) && audit.c_ids[j] == c[j], "completion independent C arrival IDs");
        const float v = fresh(c[j]);
        require(word_equal(v, audit.c_distances[j]), "completion independent C scalar word");
        if (!std::isfinite(v)) {
            require(audit.nc == int(j + 1) && !audit.m5_committed && audit.nx == 0,
                    "completion nonfinite C fail closed");
            check_original_packet(K, original, old_distances, actual, actual_distances);
            return;
        }
        cv.push_back(v); linear_insert(packet, {c[j], v, K + int(j)});
    }
    require(audit.nc == int(c.size()) && audit.m5_committed, "completion full original M5 before extra IDs");
    const auto m5_packet = packet;
    std::array<int32_t, 3> winners{{-1, -1, -1}};
    std::array<int, 3> winner_indices{{-1, -1, -1}};
    for (int row = 0; row < 3; ++row) {
        int best = -1;
        for (int j = 0; j < post.counts[slots[row]]; ++j) {
            const int32_t id = post.targets[size_t(slots[row]) * 8 + j];
            auto it = std::find(c.begin(), c.end(), id);
            if (it == c.end()) continue;
            const int ci = int(it - c.begin());
            if (best < 0 || cv[ci] < cv[best] || (cv[ci] == cv[best] && ci < best)) best = ci;
        }
        if (best >= 0) {
            winners[row] = c[best]; winner_indices[row] = best;
        }
    }
    std::vector<int32_t> x;
    std::vector<int> x_rows;
    for (int row = 0; row < 3; ++row) {
        if (table.conditioned && winners[row] < 0) continue;
        const auto* found = independent_completion_row(table, route[row], winners[row]);
        if (!found) continue;
        for (int j = 0; j < (*found)[2]; ++j) {
            const int32_t id = (*found)[3 + j];
            bool in_r = false;
            for (int r = 0; r < K; ++r) in_r = in_r || original[r] == id;
            if (in_r || std::find(c.begin(), c.end(), id) != c.end() ||
                    std::find(x.begin(), x.end(), id) != x.end()) continue;
            x.push_back(id);
            x_rows.push_back(row);
        }
    }
    require(x.size() <= 12, "completion independent all-row X cap");
    require(audit.nx <= int(x.size()), "completion actual X prefix bounds");
    const int processed_rows = audit.extension_aborted
            ? (require(audit.nx > 0, "completion aborted X has a failing scalar word"), x_rows[audit.nx - 1] + 1)
            : 3;
    int n_winners = 0;
    for (int row = 0; row < 3; ++row) {
        const bool present = row < processed_rows && winners[row] >= 0;
        if (present) {
            ++n_winners;
            require(audit.seeds[row] == winners[row] && audit.seed_route_positions[row] == row &&
                    word_equal(audit.seed_distances[row], cv[winner_indices[row]]),
                    "completion sparse route-aligned winner word; duplicates allowed");
        } else require(audit.seeds[row] == -1 && audit.seed_route_positions[row] == -1,
                       "completion absent or not-yet-visited winner row");
    }
    require(audit.nseeds == n_winners, "completion number of visited winning route rows");
    for (size_t j = 0; j < x.size(); ++j) {
        require(audit.nx > int(j) && audit.x_ids[j] == x[j], "completion full X route/row/slot arrival");
        const float v = fresh(x[j]);
        require(word_equal(v, audit.x_distances[j]), "completion independently fresh X score word");
        if (!std::isfinite(v)) {
            require(audit.nx == int(j + 1) && audit.extension_aborted, "completion X failure trace includes failing word");
            check_linear_packet(m5_packet, actual, actual_distances); return;
        }
        linear_insert(packet, {x[j], v, K + int(c.size()) + int(j)});
    }
    require(audit.nx == int(x.size()) && !audit.extension_aborted, "completion entire finite X plan");
    check_linear_packet(packet, actual, actual_distances);
}

void append_trace(std::vector<int32_t>& trace, size_t query,
                  const m5::CandidateAudit& audit, bool legal,
                  TraceSummary& summary) {
    const size_t base = query * trace_words_per_query;
    require(base + trace_words_per_query <= trace.size(), "trace storage bounds");
    for (int j = 0; j < 3; ++j) trace[base + j] = audit.seeds[j];
    trace[base + 3] = audit.nc;
    trace[base + 4] = audit.nx;
    trace[base + 5] = audit.nseeds;
    trace[base + 6] = audit.m5_committed ? 1 : 0;
    trace[base + 7] = audit.extension_aborted ? 1 : 0;
    for (int j = 0; j < audit.nc; ++j)
        trace[base + trace_c_offset + j] = audit.c_ids[j];
    for (int j = 0; j < audit.nx; ++j)
        trace[base + trace_x_offset + j] = audit.x_ids[j];
    ++summary.queries;
    summary.legal_queries += legal;
    summary.c_words += audit.nc;
    summary.x_words += audit.nx;
    summary.m5_commits += audit.m5_committed;
    summary.extension_aborts += audit.extension_aborted;
    ++summary.c_hist[audit.nc];
    ++summary.x_hist[audit.nx];
    ++summary.seed_hist[audit.nseeds];
}

void append_completion_trace(std::vector<int32_t>& trace, size_t query,
        const m5::CandidateAudit& audit, bool legal, TraceSummary& summary) {
    constexpr size_t width = 20;
    const size_t base = query * width;
    require(base + width <= trace.size() && audit.nx <= 12, "completion compact trace bounds");
    for (int row = 0; row < 3; ++row) trace[base + row] = audit.seeds[row];
    trace[base + 3] = audit.nc; trace[base + 4] = audit.nx;
    trace[base + 5] = audit.nseeds; trace[base + 6] = audit.m5_committed ? 1 : 0;
    trace[base + 7] = audit.extension_aborted ? 1 : 0;
    for (int j = 0; j < audit.nx; ++j) trace[base + 8 + j] = audit.x_ids[j];
    ++summary.queries; summary.legal_queries += legal;
    summary.c_words += audit.nc; summary.x_words += audit.nx;
    summary.m5_commits += audit.m5_committed; summary.extension_aborts += audit.extension_aborted;
    ++summary.c_hist[audit.nc]; ++summary.x_hist[audit.nx]; ++summary.seed_hist[audit.nseeds];
}

// Original E173 route, scalar main-search, DC/visited and owned output body.
// Tracing and independent oracle work are confined to a separate untimed run.
void run(acsg::IndexACSGFlat& idx, NativeRouter& router,
         const std::vector<float>& q, int L, Batch& batch,
         const Method& method, bool counting, Stats* stats,
         bool independent_audit = false,
         std::vector<int32_t>* trace = nullptr, TraceSummary* summary = nullptr,
         bool zero_intervention = false, const Batch* gt_reference = nullptr) {
    const size_t d = idx.d;
    require(q.size() >= batch.n * d, "query batch bounds");
    require(!counting || !independent_audit, "count/audit bodies separate");
    require(!trace || (independent_audit && method.extra_cap > 0 && summary &&
                      (!method.optimized || !method.completion_family.empty())),
            "trace only in independent untimed original REG or BANK oracle");
    const m5::CompletionTable* completion = method.completion_family.empty()
            ? nullptr : method.completion_models.at({int(batch.k), L}).get();
    idx.acsg.search_L = L;
    router.counting(counting);
    std::vector<std::vector<acsg::EnterPoint>> eps(batch.n);
    for (size_t i = 0; i < batch.n; ++i) {
        if (method.nsg) {
            // Exact E173 NSG entry construction; unused profile/NDC words
            // remain Batch's constructor-initialized positive zero.
            eps[i].emplace_back(idx.acsg.enterpoint, 1.f);
            batch.entries[3 * i] = idx.acsg.enterpoint;
            batch.entries[3 * i + 1] = batch.entries[3 * i + 2] = -1;
        } else {
            const auto route = router.route(q.data() + i * d);
            for (int j = 0; j < 3; ++j) {
                eps[i].emplace_back(route.ids[j], 1.f);
                batch.entries[3 * i + j] = route.ids[j];
                batch.profile_distances[3 * i + j] = route.distances[j];
            }
            if (counting) batch.route_ndc[i] = router.counter.calls;
        }
    }
    faiss::VisitedTable vt(idx.ntotal);
    std::unique_ptr<faiss::DistanceComputer> computer, fresh;
    std::unique_ptr<m5::CandidateAudit> audit_storage;
    std::unique_ptr<OriginalPacket> original;
    CounterDC* count = nullptr;
    if (counting) {
        count = new CounterDC(acsg::storage_distance_computer(idx.storage));
        computer.reset(count);
    } else computer.reset(acsg::storage_distance_computer(idx.storage));
    if (independent_audit && method.posting &&
            (method.extra_cap > 0 || method.optimized || zero_intervention))
        fresh.reset(acsg::storage_distance_computer(idx.storage));
    if (independent_audit && method.posting) {
        audit_storage = std::make_unique<m5::CandidateAudit>();
        original = std::make_unique<OriginalPacket>();
    }
    auto& dc = *computer;
    std::vector<acsg::Neighbor> ret;
    std::vector<faiss::idx_t> out(batch.k);
    for (size_t i = 0; i < batch.n; ++i) {
        const float* current = q.data() + i * d;
        dc.set_query(current);
        vt.advance();
        idx.acsg.search_new(dc, int(batch.k), out.data(),
                batch.distances.data() + i * batch.k, vt, 2, eps[i], &ret);
        const std::array<int32_t, 3> route{{batch.entries[3 * i],
                batch.entries[3 * i + 1], batch.entries[3 * i + 2]}};
        if (gt_reference && !method.nsg) {
            require(gt_reference->n == batch.n && gt_reference->k == batch.k,
                    "fresh GT main-reference dimensions");
            for (size_t j = 0; j < batch.k; ++j)
                require(out[j] == gt_reference->ids[i * batch.k + j] &&
                        word_equal(batch.distances[i * batch.k + j],
                                   gt_reference->distances[i * batch.k + j]),
                        "original scalar main packet matches this KL fresh GT before any post");
            for (int j = 0; j < 3; ++j)
                require(batch.entries[3 * i + j] == gt_reference->entries[3 * i + j] &&
                        word_equal(batch.profile_distances[3 * i + j],
                                   gt_reference->profile_distances[3 * i + j]),
                        "original route ID/profile words match fresh GT");
            if (stats) ++stats->main_packet_checks;
        }
        if (independent_audit && method.posting) {
            *audit_storage = m5::CandidateAudit{};
            std::copy(out.begin(), out.end(), original->ids.begin());
            std::copy(batch.distances.begin() + i * batch.k,
                      batch.distances.begin() + (i + 1) * batch.k,
                      original->distances.begin());
            if (method.optimized || completion) {
                fresh->set_query(current);
                for (size_t j = 0; j < batch.k; ++j) if (out[j] >= 0) {
                    const float value = (*fresh)(out[j]);
                    const bool equal = word_equal(value, batch.distances[i * batch.k + j]);
                    if (stats) {
                        ++stats->cachedmain_valid_R_checks;
                        if (!equal) ++stats->cachedmain_R_word_mismatches;
                    }
                    require(equal, "whole-window independent fresh scalar verifies cached main R word");
                }
            }
        }
        bool legal = false;
        if (method.posting) {
            if (stats) ++stats->domain_checks;
            legal = legal_query(current, d);
            if (legal) {
                if (completion)
                    m5::applyCompletion(dc, route, int(batch.k), out.data(),
                            batch.distances.data() + i * batch.k, *method.posting,
                            *completion, stats ? &stats->region : nullptr, audit_storage.get());
                else if (method.optimized)
                    m5::applyOptimized(dc, *idx.acsg.final_graph, vt, route,
                            int(batch.k), out.data(), batch.distances.data() + i * batch.k,
                            *method.posting, method.extra_cap, method.first_seed,
                            stats ? &stats->region : nullptr, audit_storage.get(), method.layout.get());
                else if (method.extra_cap == 0)
                    method.posting->apply(dc, route, int(batch.k), out.data(),
                            batch.distances.data() + i * batch.k, m5::Mode::POST,
                            stats ? &stats->region.post : nullptr);
                else
                    m5::applyRegion(dc, *idx.acsg.final_graph, vt, route,
                            int(batch.k), out.data(),
                            batch.distances.data() + i * batch.k,
                            *method.posting, method.extra_cap, method.first_seed,
                            stats ? &stats->region : nullptr,
                            audit_storage.get());
            } else if (stats) ++stats->domain_fallbacks;
        }
        if (independent_audit && method.posting && legal) {
            if (completion) {
                fresh->set_query(current);
                audit_completion(*fresh, route, *method.posting, *completion, int(batch.k),
                        original->ids.data(), original->distances.data(), out.data(),
                        batch.distances.data() + i * batch.k, *audit_storage);
            } else if (method.extra_cap > 0 || method.optimized) {
                fresh->set_query(current);
                audit_region(*fresh, *idx.acsg.final_graph, vt, route, method,
                        int(batch.k), original->ids.data(), original->distances.data(),
                        out.data(), batch.distances.data() + i * batch.k, *audit_storage);
            } else if (zero_intervention) {
                auto zero_ids = original->ids;
                auto zero_distances = original->distances;
                fresh->set_query(current);
                m5::applyRegion(*fresh, *idx.acsg.final_graph, vt, route,
                        int(batch.k), zero_ids.data(), zero_distances.data(),
                        *method.posting, 0, false, nullptr, audit_storage.get());
                for (size_t j = 0; j < batch.k; ++j)
                    require(zero_ids[j] == out[j] && word_equal(zero_distances[j],
                                    batch.distances[i * batch.k + j]),
                            "region extra0 intervention equals original apply");
                fresh->set_query(current);
                audit_region(*fresh, *idx.acsg.final_graph, vt, route, method,
                        int(batch.k), original->ids.data(), original->distances.data(),
                        zero_ids.data(), zero_distances.data(), *audit_storage);
            }
        }
        if (trace) {
            if (completion) append_completion_trace(*trace, i, *audit_storage, legal, *summary);
            else append_trace(*trace, i, *audit_storage, legal, *summary);
        }
        for (size_t j = 0; j < batch.k; ++j)
            batch.ids[i * batch.k + j] = int32_t(out[j]);
        if (counting) {
            batch.graph_ndc[i] = count->count;
            if (method.nsg)
                require(count->first[0] == idx.acsg.enterpoint &&
                        batch.route_ndc[i] == 0, "NSG original entry score order");
            else
                require(count->first == route, "actual original GT entry score order");
        }
    }
}

inline void publish_normal_packet(const Batch& b) {
    asm volatile("" : : "g"(b.ids.data()), "g"(b.distances.data()),
            "g"(b.entries.data()), "g"(b.profile_distances.data()),
            "g"(b.route_ndc.data()), "g"(b.graph_ndc.data()),
            "g"(b.n), "g"(b.k) : "memory");
}

__attribute__((noinline)) double timed_normal_batch(
        acsg::IndexACSGFlat& idx, NativeRouter& router,
        const std::vector<float>& q, int L, size_t n, size_t K,
        const Method& method) {
    const auto started = Clock::now();
    {
        Batch output(n, K);
        run(idx, router, q, L, output, method, false, nullptr);
        publish_normal_packet(output);
    }
    asm volatile("" : : : "memory");
    return seconds(started);
}

// Original E173 full direct-M5 independent linear merge oracle. It shares no
// runtime heap/apply; candidates are independently reconstructed in row order.
void audit_merge(acsg::IndexACSGFlat& idx, const std::vector<float>& q,
                 const Batch& before, const Batch& after, m5::Posting* post) {
    same_route(before, after);
    if (!post || post->empty) { same(before, after); return; }
    std::unique_ptr<faiss::DistanceComputer> dc(
            acsg::storage_distance_computer(idx.storage));
    struct Item { int32_t id; float distance; int priority; };
    for (size_t i = 0; i < before.n; ++i) {
        const float* current = q.data() + i * idx.d;
        dc->set_query(current);
        std::vector<faiss::idx_t> original(before.k);
        for (size_t j = 0; j < before.k; ++j)
            original[j] = before.ids[i * before.k + j];
        std::vector<int32_t> candidates;
        bool missing_row = false;
        for (int row = 0; row < 3; ++row) {
            const int slot = independent_slot(*post, before.entries[3 * i + row]);
            if (slot < 0) { missing_row = true; break; }
            for (int j = 0; j < post->counts[slot]; ++j) {
                const int32_t id = post->targets[size_t(slot) * 8 + j];
                if (std::find(original.begin(), original.end(), id) == original.end() &&
                        std::find(candidates.begin(), candidates.end(), id) == candidates.end()) candidates.push_back(id);
            }
        }
        if (missing_row) candidates.clear();
        const int nc = int(candidates.size());
        auto fallback = [&]() {
            for (size_t j = 0; j < before.k; ++j)
                require(before.ids[i * before.k + j] == after.ids[i * before.k + j] &&
                        word_equal(before.distances[i * before.k + j],
                                   after.distances[i * before.k + j]),
                        "direct empty/fallback ID and score parity");
        };
        if (nc <= 0 || !legal_query(current, idx.d)) { fallback(); continue; }
        std::vector<Item> packet;
        bool nonfinite = false;
        for (size_t j = 0; j < before.k; ++j) {
            const int32_t id = before.ids[i * before.k + j];
            const float value = id < 0 ? std::numeric_limits<float>::max() : (*dc)(id);
            if (!std::isfinite(value)) { nonfinite = true; break; }
            packet.push_back({id, value, int(j)});
        }
        if (nonfinite) { fallback(); continue; }
        auto worse = [](const Item& a, const Item& b) {
            if (a.id < 0 || b.id < 0) return a.id < 0 && b.id >= 0;
            if (a.distance != b.distance) return a.distance > b.distance;
            return a.priority > b.priority;
        };
        for (int j = 0; j < nc; ++j) {
            Item candidate{candidates[j], (*dc)(candidates[j]),
                           int(before.k) + j};
            if (!std::isfinite(candidate.distance)) { nonfinite = true; break; }
            size_t worst = 0;
            for (size_t t = 1; t < packet.size(); ++t)
                if (worse(packet[t], packet[worst])) worst = t;
            if (packet[worst].id < 0 || candidate.distance < packet[worst].distance)
                packet[worst] = candidate;
        }
        if (nonfinite) { fallback(); continue; }
        std::sort(packet.begin(), packet.end(), [&](const Item& a, const Item& b) {
            return worse(b, a);
        });
        for (size_t j = 0; j < before.k; ++j)
            require(packet[j].id == after.ids[i * before.k + j] &&
                    word_equal(packet[j].distance, after.distances[i * before.k + j]),
                    "original independent direct linear ID/score oracle");
    }
}

json stats_json(const Stats& s) {
    const auto& p = s.region.post;
    const auto& r = s.region;
    return {{"domain_checks", s.domain_checks}, {"domain_fallbacks", s.domain_fallbacks},
            {"lookups", p.lookups}, {"probes", p.probes}, {"fallbacks", p.fallbacks},
            {"row_reads", p.row_reads}, {"candidate_count", p.candidates},
            {"post_dots", p.dots}, {"commits", p.commits},
            {"nonfinite_failures", p.nonfinite_failures},
            {"region_queries", r.queries}, {"seed_candidates", r.seed_candidates},
            {"seeds_selected", r.seeds_selected},
            {"seed_duplicate_skips", r.seed_duplicate_skips},
            {"seed_posting_slots", r.seed_posting_slots}, {"seed_rows", r.seed_rows},
            {"graph_slots", r.graph_slots}, {"new_distances", r.new_distances},
            {"main_seen_skips", r.main_seen_skips},
            {"c_duplicate_skips", r.c_duplicate_skips},
            {"x_duplicate_skips", r.x_duplicate_skips},
            {"invalid_neighbor_skips", r.invalid_neighbor_skips},
            {"extension_nonfinite_failures", r.extension_nonfinite_failures},
            {"extension_commits", r.extension_commits},
            {"r_cache_queries", r.r_cache_queries}, {"r_cache_hits", r.r_cache_hits},
            {"r_cache_fallback_queries", r.r_cache_fallback_queries},
            {"r_word_checks", r.r_word_checks}, {"r_word_check_dots", r.r_word_check_dots},
            {"r_word_mismatches", r.r_word_mismatches},
            {"seed_mapping_slots", r.seed_mapping_slots}, {"trimmed_invalid_slots", r.trimmed_invalid_slots},
            {"main_packet_checks", s.main_packet_checks},
            {"cachedmain_valid_R_checks", s.cachedmain_valid_R_checks},
            {"cachedmain_R_word_mismatches", s.cachedmain_R_word_mismatches},
            {"additional_scalar_calls", p.dots + r.new_distances}};
}

json trace_summary_json(const TraceSummary& s) {
    return {{"scope", "full independent untimed normal plain scalar/linear oracle; not timed NDC"},
            {"queries", s.queries}, {"legal_queries", s.legal_queries},
            {"c_words", s.c_words}, {"x_words", s.x_words},
            {"m5_commits", s.m5_commits}, {"extension_aborts", s.extension_aborts},
            {"c_count_histogram", s.c_hist}, {"x_count_histogram", s.x_hist},
            {"seed_count_histogram", s.seed_hist}};
}

Batch sample_packet(const Batch& full, const std::vector<int32_t>& audit_ids) {
    Batch sample(audit_ids.size(), full.k);
    for (size_t i = 0; i < audit_ids.size(); ++i) {
        const size_t src = size_t(audit_ids[i]);
        for (size_t j = 0; j < full.k; ++j) {
            sample.ids[i * full.k + j] = full.ids[src * full.k + j];
            sample.distances[i * full.k + j] = full.distances[src * full.k + j];
        }
        for (size_t j = 0; j < 3; ++j) {
            sample.entries[3 * i + j] = full.entries[3 * src + j];
            sample.profile_distances[3 * i + j] = full.profile_distances[3 * src + j];
        }
    }
    return sample;
}

bool safe_name(const std::string& name) {
    if (name.empty()) return false;
    for (char x : name)
        if (!((x >= 'A' && x <= 'Z') || (x >= 'a' && x <= 'z') ||
              (x >= '0' && x <= '9') || x == '_' || x == '-')) return false;
    return true;
}

} // namespace

int main(int argc, char** argv) {
    try {
        require(argc == 2, "benchmark JOB.json");
        const auto c = read_json(argv[1]);
        threads();
        const fs::path dest = c.at("out").get<std::string>();
        require(!fs::exists(dest), "preserve output");
        fs::create_directories(dest);
        write_json(dest / "job.json", c);
        const auto started = Clock::now();
        const size_t n = c.at("n"), d = c.at("dimension");
        const int repeats = c.value("timing_repeats", 3);
        const int warmups = c.value("warmup_batches", 1);
        const size_t warm_n = std::min(n, c.value("warmup_n", size_t(256)));
        require(d > 0 && n > 0 && repeats >= 1 && warmups >= 0,
                "actual nonempty shape/repetition counts");
        const bool smoke = n == 16 && repeats == 1;
        require(smoke || (n == 10000 && repeats == 3 && warmups == 1 &&
                          warm_n == 256), "E176 public10K protocol or n16 smoke");
        require(c.value("no_training", true), "query-only frozen model protocol");
        const bool zero_intervention = c.value("check_region_zero", smoke);
        std::vector<float> q(n * d);
        if (c.value("query_format", std::string("fvecs")) == "fvecs") {
            Fvecs input(c.at("queries"));
            const size_t first = c.value("query_first", size_t(0));
            require(input.d == d && first <= input.n && n <= input.n - first,
                    "test query source shape");
            for (size_t i = 0; i < n; ++i)
                std::copy(input.row(first + i), input.row(first + i) + d,
                          q.data() + i * d);
        } else {
            require(c.at("query_format") == "raw", "registered query format");
            const auto input = read_raw<float>(c.at("queries").get<std::string>());
            const size_t first = c.value("query_first", size_t(0));
            require(input.size() % d == 0 && first <= input.size() / d &&
                    n <= input.size() / d - first, "raw query source shape");
            std::copy(input.begin() + first * d, input.begin() + (first + n) * d,
                      q.begin());
        }
        for (float v : q) require(std::isfinite(v), "finite test query");

        NativeRouter router(c.at("anchor"), d);
        auto index = load_nsg(c.at("index").get<std::string>());
        require(index->ntotal == c.at("base_n").get<int64_t>() &&
                index->d == int(d), "loaded base identity");
        require(index->acsg.final_graph && index->acsg.final_graph->data &&
                index->acsg.final_graph->N == index->ntotal &&
                index->acsg.final_graph->K > 0, "actual original graph domain");
        for (auto id : router.ids)
            require(id >= 0 && id < index->ntotal, "real hub loaded base domain");
        auto* flat = dynamic_cast<faiss::IndexFlat*>(index->storage);
        require(flat, "actual original flat base");
        require(c.value("verify_loaded_base_words", true), "full current-process base/ordered-graph binding required");
        const auto loaded_domain = bind_loaded_base(*index, c);

        // Models are loaded once per distinct frozen table path. Reusing a
        // table across methods shares only its serial scratch/resident model.
        std::map<std::string, std::unique_ptr<m5::Posting>> tables;
        std::vector<Method> methods;
        std::set<std::string> names;
        size_t gt_index = size_t(-1);
        for (const auto& j : c.at("methods")) {
            Method method;
            method.name = j.at("name").get<std::string>();
            method.nsg = method.name == "NSG";
            method.family = j.at("family").get<std::string>();
            method.optimized = j.at("optimized").get<bool>();
            const std::map<std::string, std::string> expected_families{
                {"NSG", "base"}, {"GT", "base"}, {"M5", "post"}, {"M5OPT", "opt"},
                {"M5REG96", "reg"}, {"REGOPT96", "opt_reg"}, {"M5RES12", "bank"}, {"WIDE12", "route_bank"}};
            require(expected_families.count(method.name) && method.family == expected_families.at(method.name),
                    "method name matches locked family");
            if (method.family == "bank") method.completion_family = "pair";
            if (method.family == "route_bank") method.completion_family = "route";
            method.extra_cap = j.at("extra_cap").get<int>();
            method.first_seed = j.at("first_seed").get<bool>();
            require(safe_name(method.name) && names.insert(method.name).second,
                    "unique safe method name");
            require(method.family == "base" || method.family == "post" ||
                    method.family == "opt" || method.family == "reg" ||
                    method.family == "opt_reg" || !method.completion_family.empty(), "frozen E176 method family");
            const bool bank = !method.completion_family.empty();
            const bool reg = method.family == "reg" || method.family == "opt_reg";
            require(method.extra_cap == (bank ? 12 : reg ? 96 : 0) && !method.first_seed,
                    "fixed family scalar cap 0/12/96 and best-C winner");
            require(bank || method.optimized == (method.family == "opt" || method.family == "opt_reg"),
                    "optimization family declaration");
            if (j.at("table").is_null()) {
                require(method.family == "base" && (method.name == "GT" || method.nsg) && method.extra_cap == 0 &&
                        !method.first_seed, "null-table original GT or NSG method");
                if (method.name == "GT") gt_index = methods.size();
            } else {
                require(method.name != "GT" && !method.nsg,
                        "GT and NSG have no posting table");
                method.table = j.at("table").get<std::string>();
                auto it = tables.find(method.table);
                if (it == tables.end()) {
                    auto post = std::make_unique<m5::Posting>(
                            method.table, false, uint32_t(index->ntotal));
                    require(post->labels == router.ids && post->b == 8,
                            "posting exact frozen real labels and eight-row schema");
                    it = tables.emplace(method.table, std::move(post)).first;
                }
                method.posting = it->second.get();
                if (method.family == "opt_reg")
                    method.layout = std::make_unique<m5::OptimizedLayout>(*index->acsg.final_graph, *method.posting);
                if (bank) for (int K : c.at("K_values")) for (int L : c.at("L")) {
                    const auto key = "k" + std::to_string(K) + "_L" + std::to_string(L);
                    const auto path = c.at("completion_models").at(key).at(method.completion_family).get<std::string>();
                    method.completion_models.emplace(std::make_pair(K, L),
                        std::make_unique<m5::CompletionTable>(path, method.completion_family == "pair",
                                uint32_t(index->ntotal), *method.posting));
                }
            }
            methods.push_back(std::move(method));
        }
        require(methods.size() == 8 && gt_index < methods.size() &&
                names == std::set<std::string>{"NSG", "GT", "M5", "M5OPT", "M5REG96", "REGOPT96", "M5RES12", "WIDE12"},
                "complete E176 eight-method comparison includes original M5 and GT");
        json table_bindings = json::array();
        uint64_t resident_bytes = 0;
        for (const auto& item : tables) {
            resident_bytes += item.second->resident_bytes();
            table_bindings.push_back({{"table", item.first},
                    {"pairs", item.second->pairs},
                    {"resident_bytes", item.second->resident_bytes()}});
        }
        json completion_bindings = json::array(), layout_bindings = json::array();
        const uint64_t posting_resident_bytes = resident_bytes;
        for (const auto& method : methods) {
            for (const auto& item : method.completion_models) {
                resident_bytes += item.second->resident_bytes();
                completion_bindings.push_back({{"method", method.name}, {"family", method.completion_family},
                    {"K", item.first.first}, {"L", item.first.second}, {"rows", item.second->rows.size()},
                    {"table", c.at("completion_models").at("k" + std::to_string(item.first.first) + "_L" + std::to_string(item.first.second)).at(method.completion_family)},
                    {"resident_bytes", item.second->resident_bytes()}});
            }
            if (method.layout) {
                resident_bytes += method.layout->resident_bytes();
                layout_bindings.push_back({{"method", method.name}, {"resident_bytes", method.layout->resident_bytes()},
                    {"startup_seconds", method.layout->startup_seconds}, {"startup_graph_reads", method.layout->startup_graph_reads},
                    {"startup_trimmed_slots", method.layout->startup_trimmed_slots}});
            }
        }
        std::ifstream boot_file("/proc/sys/kernel/random/boot_id");
        std::string boot;
        std::getline(boot_file, boot);
        write_json(dest / "native_environment.json", {
                {"router", router.binding()}, {"mxcsr", _mm_getcsr()},
                {"threads", process_threads()}, {"pid", getpid()}, {"boot_id", boot},
                {"no_GT_read", true}, {"no_training", true},
                {"smoke_only", smoke}, {"startup_seconds", seconds(started)},
                {"enterpoint", index->acsg.enterpoint},
                {"loaded_base_words_checked", c.value("verify_loaded_base_words", true)},
                {"loaded_domain", loaded_domain},
                {"loaded_base_words", uint64_t(index->ntotal) * d},
                {"graph_N", index->acsg.final_graph->N},
                {"graph_degree", index->acsg.final_graph->K},
                {"main_kernel", "original E173 scalar search_new, mode2; NSG original enterpoint or unchanged GT route"},
                {"whole_wall", "normal Batch allocate/init/release, routes/vt/DC/pool, guard, original posting, seed selection, adjacency/filter/new scores/merge/output; loading/audits/serialization separate"},
                {"distinct_frozen_tables", table_bindings},
                {"completion_tables", completion_bindings}, {"optimized_layouts", layout_bindings},
                {"complete_distinct_posting_resident_bytes", posting_resident_bytes},
                {"complete_posting_completion_layout_resident_bytes", resident_bytes},
                {"region_candidate_id_scratch_bytes", m5::region_candidate_id_scratch_bytes()},
                {"optimized_fixed_array_scratch_bytes", m5::optimized_fixed_array_scratch_bytes()},
                {"region_fixed_stack_state_note", "ID scratch plus local seed/row/record/loop state; ordinary compiler stack-frame bytes are not inferred from ID scratch alone"},
                {"untimed_candidate_audit_sizeof", sizeof(m5::CandidateAudit)},
                {"declared_source_identities", c}});
        resource_guard(c, dest);

        // This fixed uniform sample is chosen before responses are available.
        const size_t audit_n = std::min(n, size_t(256));
        require(c.value("audit_n", size_t(256)) == 256,
                "fixed uniform 256 count sample");
        std::vector<int32_t> audit_ids(audit_n);
        std::vector<float> audit_q(audit_n * d);
        for (size_t i = 0; i < audit_n; ++i) {
            audit_ids[i] = audit_n == 1 ? 0 : int32_t(i * (n - 1) / (audit_n - 1));
            std::copy(q.begin() + size_t(audit_ids[i]) * d,
                      q.begin() + (size_t(audit_ids[i]) + 1) * d,
                      audit_q.begin() + i * d);
        }
        write_raw(dest / "audit_query_ids.i32", audit_ids);
        json rounds = json::array(), results = json::array();
        size_t point_ordinal = 0;
        uint64_t native_calls = 0;
        const size_t m = methods.size();
        for (int K : c.at("K_values")) for (int L : c.at("L")) {
            require((K == 1 || K == 100) && L >= K, "actual K/L");
            const fs::path group = dest / ("k" + std::to_string(K));
            std::vector<std::vector<double>> timings(m);
            std::vector<std::unique_ptr<Batch>> full_plain(m);
            std::vector<Stats> full_stats(m);
            std::vector<TraceSummary> trace_summaries(m);
            std::vector<std::vector<int32_t>> traces(m);
            std::vector<size_t> plain_order{gt_index};
            for (size_t vi = 0; vi < m; ++vi) if (vi != gt_index) plain_order.push_back(vi);
            write_json(dest / "progress.json", {{"phase", "full_plain_oracles"}, {"completed_KL", point_ordinal},
                    {"native_calls", native_calls}, {"timing_values_hidden_until_complete", true}});
            // One full native pass per method. GT is generated first and serves
            // as this exact KL's pre-post main reference for every other GT path.
            for (size_t vi : plain_order) {
                const auto& method = methods[vi];
                const bool bank = !method.completion_family.empty();
                const bool old_reg = method.family == "reg";
                if (old_reg) traces[vi].assign(n * trace_words_per_query, -1);
                if (bank) traces[vi].assign(n * 20, -1);
                full_plain[vi] = std::make_unique<Batch>(n, K);
                run(*index, router, q, L, *full_plain[vi], method, false, &full_stats[vi],
                        true, traces[vi].empty() ? nullptr : &traces[vi],
                        traces[vi].empty() ? nullptr : &trace_summaries[vi],
                        zero_intervention && method.family == "post",
                        vi == gt_index || method.nsg ? nullptr : full_plain[gt_index].get());
                native_calls += n;
                if (method.nsg) check_nsg_route(*full_plain[vi], index->acsg.enterpoint);
                else same_route(*full_plain[gt_index], *full_plain[vi]);
                if (method.family == "post")
                    audit_merge(*index, q, *full_plain[gt_index], *full_plain[vi], method.posting);
                if (method.posting && !method.nsg)
                    require(full_stats[vi].main_packet_checks == n,
                            "full method main packet compared with fresh GT before post");
                if (method.optimized || bank)
                    require(full_stats[vi].cachedmain_R_word_mismatches == 0 &&
                            full_stats[vi].region.r_word_mismatches == 0,
                            "no independent cached-main R word mismatch");
                resource_guard(c, dest);
            }
            // Optimization eligibility is word equality to the complete original
            // algorithms; performance observations cannot waive this check.
            for (size_t vi = 0; vi < m; ++vi) if (methods[vi].family == "opt" || methods[vi].family == "opt_reg") {
                const std::string reference = methods[vi].family == "opt" ? "M5" : "M5REG96";
                size_t ref = 0;
                while (ref < m && methods[ref].name != reference) ++ref;
                require(ref < m, "optimization complete original reference exists");
                same(*full_plain[vi], *full_plain[ref]);
            }
            write_json(dest / "progress.json", {{"phase", "warmup"}, {"completed_KL", point_ordinal},
                    {"native_calls", native_calls}, {"full_plain_oracles_passed_methods", m}});
            for (int w = 0; w < warmups; ++w) for (const auto& method : methods) {
                Batch warm(warm_n, K);
                run(*index, router, q, L, warm, method, false, nullptr);
                publish_normal_packet(warm); native_calls += warm_n;
            }
            for (int round = 0; round < repeats; ++round)
                for (size_t offset = 0; offset < m; ++offset) {
                    const size_t vi = (point_ordinal + size_t(round) + offset) % m;
                    threads();
                    const double wall = timed_normal_batch(*index, router, q, L, n, K, methods[vi]);
                    timings[vi].push_back(wall); native_calls += n;
                    resource_guard(c, dest);
                    rounds.push_back({{"K", K}, {"L", L}, {"method", methods[vi].name},
                            {"round", round}, {"seconds", wall}, {"qps", n / wall},
                            {"n", n}, {"threads", process_threads()}, {"cpu", 15}, {"native_calls", native_calls}});
                    // Administrative progress deliberately has no partial wall/QPS.
                    write_json(dest / "progress.json", {{"phase", "timing"}, {"completed_KL", point_ordinal},
                            {"completed_timed_batches", rounds.size()}, {"native_calls", native_calls},
                            {"timing_values_hidden_until_complete", true}});
                }
            for (size_t vi = 0; vi < m; ++vi) {
                const auto& method = methods[vi]; const Batch& plain = *full_plain[vi];
                const bool bank = !method.completion_family.empty();
                const bool old_reg = method.family == "reg";
                const bool opt_reference = method.family == "opt" || method.family == "opt_reg";
                Batch sample_plain = sample_packet(plain, audit_ids);
                Batch counted(audit_n, K); Stats count_stats;
                run(*index, router, audit_q, L, counted, method, true, &count_stats);
                native_calls += audit_n; same(sample_plain, counted);
                require(count_stats.region.r_word_checks == 0 && count_stats.cachedmain_valid_R_checks == 0,
                        "count audit has no cached-R qualification scoring");
                if (method.nsg) check_nsg_route(counted, index->acsg.enterpoint);
                const fs::path out = group / (method.name + "_L" + std::to_string(L));
                plain.save(out / "raw", false); counted.save(out / "raw", true);
                write_raw(out / "raw/audit_query_ids.i32", audit_ids);
                if (old_reg) {
                    require(traces[vi].size() * sizeof(int32_t) <= 5 * 1024 * 1024,
                            "bounded original REG trace five MiB per point");
                    write_raw(out / "raw/region_trace.i32", traces[vi]);
                    write_json(out / "raw/region_trace_schema.json", {
                        {"dtype", "<i4"}, {"n", n}, {"words_per_query", 128},
                        {"bytes", traces[vi].size() * 4}, {"metadata_offsets", {{"seed0", 0}, {"seed1", 1}, {"seed2", 2},
                            {"nC", 3}, {"nX", 4}, {"nSeeds", 5}, {"m5_committed", 6}, {"extension_aborted", 7}}},
                        {"C_offset", 8}, {"C_capacity", 24}, {"X_offset", 32}, {"X_capacity", 96},
                        {"candidate_padding", -1}, {"seed_padding", -1}, {"K", K}, {"extra_cap", 96},
                        {"candidate_order", "complete scalar-call arrival; failing nonfinite word included"},
                        {"trace_source", "single full normal untimed pass with independent fresh scalar/linear oracle; no full-main replay"}});
                    write_json(out / "trace_summary.json", trace_summary_json(trace_summaries[vi]));
                    write_json(out / "full_region_audit_stats.json", {{"n", n}, {"stats", stats_json(full_stats[vi])},
                            {"scope", "full untimed single native pass plus helper qualification; independent fresh oracle DC calls are separate from these run counters"}});
                }
                if (bank) {
                    write_raw(out / "raw/completion_trace.i32", traces[vi]);
                    write_json(out / "raw/completion_trace_schema.json", {
                        {"dtype", "<i4"}, {"n", n}, {"words_per_query", 20}, {"bytes", traces[vi].size() * 4},
                        {"metadata_offsets", {{"winner0", 0}, {"winner1", 1}, {"winner2", 2}, {"nC", 3}, {"nX", 4},
                            {"nWinnerRows", 5}, {"m5_committed", 6}, {"extension_aborted", 7}}},
                        {"X_offset", 8}, {"X_capacity", 12}, {"candidate_padding", -1}, {"winner_padding", -1},
                        {"winners", "sparse original-route aligned; duplicate winner IDs permitted"},
                        {"C", "not serialized; independently reconstructed from full GT and original frozen posting"},
                        {"K", K}, {"L", L}, {"family", method.completion_family},
                        {"candidate_order", "route0 row slots then route1 then route2; remove original R, full C and earlier X; strict later priority"},
                        {"trace_source", "single full untimed pass with independent C/winner/table/X/score/linear oracle"}});
                    write_json(out / "trace_summary.json", trace_summary_json(trace_summaries[vi]));
                    write_json(out / "full_completion_audit_stats.json", {{"n", n}, {"family", method.completion_family},
                            {"stats", stats_json(full_stats[vi])}, {"scope", "full untimed single native pass; all sparse-row winner and C/X words independently checked; not timed NDC"}});
                }
                if (method.posting)
                    write_json(out / "full_oracle_stats.json", {{"n", n}, {"stats", stats_json(full_stats[vi])},
                            {"cachedmain_valid_R_checks", full_stats[vi].cachedmain_valid_R_checks},
                            {"cachedmain_R_word_mismatches", full_stats[vi].cachedmain_R_word_mismatches},
                            {"scope", "single full normal plain run counters; helper audit callbacks included; separate independent fresh-DC oracle calls not included"}});
                json result = {{"method", method.name}, {"family", method.family}, {"optimized", method.optimized},
                        {"completion_family", method.completion_family}, {"table", method.table},
                        {"extra_cap", method.extra_cap}, {"first_seed", method.first_seed}, {"K", K}, {"L", L}, {"n", n},
                        {"smoke_only", smoke}, {"timing_seconds", timings[vi]}, {"warmup_batches", warmups}, {"warmup_n", warm_n},
                        {"full_plain_return_n", n}, {"full_plain_independent_scalar_linear_oracle", bool(method.posting)},
                        {"full_scalar_linear_oracle_n", method.posting ? n : 0},
                        {"original_scalar_main_kernel", true}, {"main_packet_words_equal_fresh_GT", !method.nsg},
                        {"main_packet_words_equal_fresh_GT_n", method.nsg ? 0 : n},
                        {"cached_main_R_fresh_score_words_equal", method.optimized || bank},
                        {"cached_main_R_fresh_score_query_n", method.optimized || bank ? n : 0},
                        {"cachedmain_valid_R_checks", full_stats[vi].cachedmain_valid_R_checks},
                        {"cachedmain_R_word_mismatches", full_stats[vi].cachedmain_R_word_mismatches},
                        {"cached_R_word_check_n", full_stats[vi].cachedmain_valid_R_checks},
                        {"full_plain_independent_replay_bits_equal", false}, {"full_plain_independent_replay_n", 0},
                        {"optimized_reference_method", opt_reference ? (method.family == "opt" ? "M5" : "M5REG96") : ""},
                        {"optimized_reference_packet_bits_equal", opt_reference},
                        {"plain_count_bits_equal", true}, {"count_audit_n", audit_n},
                        {"plain_count_parity_scope", "fixed uniform query sample only"},
                        {"audit_query_ids_formula", "floor(i*(n-1)/(audit_n-1)), endpoints; frozen before responses"},
                        {"stats_scope", "fixed uniform count-audit queries only, not full NDC"},
                        {"graph_ndc_scope", "actual DC main plus physical helper callbacks; qualification callbacks absent in this sample"},
                        {"independent_original_linear_merge", method.family == "post"},
                        {"independent_region_linear_oracle", old_reg || method.family == "opt" || method.family == "opt_reg"},
                        {"independent_completion_linear_oracle", bank}, {"linear_merge_audit_n", method.posting ? n : 0},
                        {"region_zero_intervention", zero_intervention && method.family == "post"},
                        {"region_zero_intervention_n", zero_intervention && method.family == "post" ? n : 0},
                        {"original_GT_route_words_unchanged", !method.nsg}, {"original_NSG_constant_route_words_checked", method.nsg},
                        {"main_entry_mode", method.nsg ? "original_NSG_enterpoint" : "original_GT_top3"},
                        {"NSG_enterpoint", method.nsg ? index->acsg.enterpoint : -1},
                        {"route_schema", method.nsg ? "[enterpoint,-1,-1]; profile words +0; route NDC 0" : "actual GT maxheap-pop top3 IDs/profile words"},
                        {"threads", 1}, {"cpu", 15}, {"normal_output_release_before_stop", true}, {"timed_output_retained", false},
                        {"audit_scope", "full single normal plain scalar/linear oracle before timing; post main matches freshly generated GT; full cached R word qualification; fixed256 plain/count parity; no second native full replay or timed-output capture"},
                        {"stats", stats_json(count_stats)}};
                if (bank) {
                    result["completion_table"] = c.at("completion_models").at("k" + std::to_string(K) + "_L" + std::to_string(L)).at(method.completion_family);
                    result["shared_cost_baseline"] = "M5OPT";
                }
                write_json(out / "complete.json", result); results.push_back(result); resource_guard(c, dest);
            }
            ++point_ordinal;
            write_json(dest / "progress.json", {{"phase", "KL_complete"}, {"completed_KL", point_ordinal},
                    {"native_calls", native_calls}, {"timing_values_hidden_until_complete", true}});
        }
        write_json(dest / "complete.json", {
                {"status", smoke ? "PASS_E176_SMOKE_NATIVE_ORACLES" : "PASS_E176_FROZEN_CURVE_NATIVE_FULL_WORD_ORACLES_SAMPLED_COUNT"},
                {"smoke_only", smoke}, {"results", results}, {"wall_rounds", rounds.size()}, {"native_calls", native_calls},
                {"formal_order", rounds}, {"rotation", "(KL ordinal + round + method offset) mod method count; prelocked"},
                {"execution_order", "fresh full GT, each method full single untimed word/linear oracle, optimization reference parity, warmup, timed rotation, 256 count sample and serialization"},
                {"wall_boundary", "complete owned normal Batch allocate/init/release and all routes/main/guard/post/completion/region work; loading/live binding/qualification/serialization excluded and separately charged"},
                {"count_audit_n", audit_n}, {"count_audit_scope", "fixed uniform sample only; not full NDC"},
                {"full_plain_return_n", n}, {"full_independent_replay_n", 0}, {"full_direct_and_region_oracle_n", n},
                {"full_oracle_query_scope", "all post methods; base NSG/GT have no post-merge oracle"},
                {"seconds_with_startup_and_audits", seconds(started)}, {"no_GT_read", true}, {"no_training", true},
                {"no_quality_claim_before_GT_evaluation", true}});
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "FATAL " << e.what() << '\n';
        return 2;
    }
}

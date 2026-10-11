#include "region.hpp"
#include <limits>

using namespace exp172;
namespace {

struct Method {
    std::string name, table;
    m5::Posting* posting = nullptr;
    int extra_cap = 0;
    bool first_seed = false;
};

struct Stats {
    m5::RegionStats region;
    uint64_t domain_checks = 0, domain_fallbacks = 0;
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

// Original E173 route, scalar main-search, DC/visited and owned output body.
// Tracing and independent oracle work are confined to a separate untimed run.
void run(acsg::IndexACSGFlat& idx, NativeRouter& router,
         const std::vector<float>& q, int L, Batch& batch,
         const Method& method, bool counting, Stats* stats,
         bool independent_audit = false,
         std::vector<int32_t>* trace = nullptr, TraceSummary* summary = nullptr,
         bool zero_intervention = false) {
    const size_t d = idx.d;
    require(q.size() >= batch.n * d, "query batch bounds");
    require(!counting || !independent_audit, "count/audit bodies separate");
    require(!trace || (independent_audit && method.extra_cap > 0 && summary),
            "trace only in independent untimed region audit");
    idx.acsg.search_L = L;
    router.counting(counting);
    std::vector<std::vector<acsg::EnterPoint>> eps(batch.n);
    for (size_t i = 0; i < batch.n; ++i) {
        const auto route = router.route(q.data() + i * d);
        for (int j = 0; j < 3; ++j) {
            eps[i].emplace_back(route.ids[j], 1.f);
            batch.entries[3 * i + j] = route.ids[j];
            batch.profile_distances[3 * i + j] = route.distances[j];
        }
        if (counting) batch.route_ndc[i] = router.counter.calls;
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
            (method.extra_cap > 0 || zero_intervention))
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
        if (independent_audit && method.posting) {
            *audit_storage = m5::CandidateAudit{};
            std::copy(out.begin(), out.end(), original->ids.begin());
            std::copy(batch.distances.begin() + i * batch.k,
                      batch.distances.begin() + (i + 1) * batch.k,
                      original->distances.begin());
        }
        bool legal = false;
        if (method.posting) {
            if (stats) ++stats->domain_checks;
            legal = legal_query(current, d);
            if (legal) {
                if (method.extra_cap == 0)
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
            if (method.extra_cap > 0) {
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
        if (trace) append_trace(*trace, i, *audit_storage, legal, *summary);
        for (size_t j = 0; j < batch.k; ++j)
            batch.ids[i * batch.k + j] = int32_t(out[j]);
        if (counting) {
            batch.graph_ndc[i] = count->count;
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
// runtime heap/apply; this preserved control still uses the original plan().
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
        const int nc = post->plan({before.entries[3 * i],
                before.entries[3 * i + 1], before.entries[3 * i + 2]},
                original.data(), int(before.k), nullptr);
        if (nc <= 0 || !legal_query(current, idx.d)) {
            for (size_t j = 0; j < before.k; ++j)
                require(before.ids[i * before.k + j] == after.ids[i * before.k + j] &&
                        word_equal(before.distances[i * before.k + j],
                                   after.distances[i * before.k + j]),
                        "direct empty/fallback ID and score parity");
            continue;
        }
        std::vector<Item> packet;
        for (size_t j = 0; j < before.k; ++j) {
            const int32_t id = before.ids[i * before.k + j];
            packet.push_back({id, id < 0 ? std::numeric_limits<float>::max()
                                       : (*dc)(id), int(j)});
        }
        auto worse = [](const Item& a, const Item& b) {
            if (a.id < 0 || b.id < 0) return a.id < 0 && b.id >= 0;
            if (a.distance != b.distance) return a.distance > b.distance;
            return a.priority > b.priority;
        };
        for (int j = 0; j < nc; ++j) {
            Item candidate{post->candidate[j], (*dc)(post->candidate[j]),
                           int(before.k) + j};
            size_t worst = 0;
            for (size_t t = 1; t < packet.size(); ++t)
                if (worse(packet[t], packet[worst])) worst = t;
            if (packet[worst].id < 0 || candidate.distance < packet[worst].distance)
                packet[worst] = candidate;
        }
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
            {"additional_scalar_calls", p.dots + r.new_distances}};
}

json trace_summary_json(const TraceSummary& s) {
    return {{"scope", "full independent untimed region replay; not timed NDC"},
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
        require(smoke || (n == 4096 && repeats == 3 && warmups == 1 &&
                          warm_n == 256), "frozen full protocol or n16 smoke");
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
        if (c.value("verify_loaded_base_words", true)) {
            Fvecs base(c.at("base"));
            require(base.n == size_t(index->ntotal) && base.d == d,
                    "registered base shape");
            for (size_t i = 0; i < base.n; ++i)
                require(!memcmp(flat->get_xb() + i * d, base.row(i), d * 4),
                        "actual loaded base words differ from registered base");
        }

        // Models are loaded once per distinct frozen table path. Reusing a
        // table across methods shares only its serial scratch/resident model.
        std::map<std::string, std::unique_ptr<m5::Posting>> tables;
        std::vector<Method> methods;
        std::set<std::string> names;
        size_t gt_index = size_t(-1);
        for (const auto& j : c.at("methods")) {
            Method method;
            method.name = j.at("name").get<std::string>();
            method.extra_cap = j.at("extra_cap").get<int>();
            method.first_seed = j.at("first_seed").get<bool>();
            require(safe_name(method.name) && names.insert(method.name).second,
                    "unique safe method name");
            require(method.extra_cap == 0 || method.extra_cap == 24 ||
                    method.extra_cap == 96, "frozen method extra cap");
            require(method.extra_cap > 0 || !method.first_seed,
                    "first-seed control requires region extension");
            if (j.at("table").is_null()) {
                require(method.name == "GT" && method.extra_cap == 0 &&
                        !method.first_seed, "null-table original GT method");
                gt_index = methods.size();
            } else {
                require(method.name != "GT", "GT has no posting table");
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
            }
            methods.push_back(std::move(method));
        }
        require(methods.size() >= 2 && gt_index < methods.size(),
                "dynamic comparison includes original GT");
        json table_bindings = json::array();
        uint64_t resident_bytes = 0;
        for (const auto& item : tables) {
            resident_bytes += item.second->resident_bytes();
            table_bindings.push_back({{"table", item.first},
                    {"pairs", item.second->pairs},
                    {"resident_bytes", item.second->resident_bytes()}});
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
                {"loaded_base_words", uint64_t(index->ntotal) * d},
                {"graph_N", index->acsg.final_graph->N},
                {"graph_degree", index->acsg.final_graph->K},
                {"main_kernel", "original E173 scalar search_new, mode2, original GT route"},
                {"whole_wall", "normal Batch allocate/init/release, routes/vt/DC/pool, guard, original posting, seed selection, adjacency/filter/new scores/merge/output; loading/audits/serialization separate"},
                {"distinct_frozen_tables", table_bindings},
                {"complete_distinct_posting_resident_bytes", resident_bytes},
                {"region_candidate_id_scratch_bytes", m5::region_candidate_id_scratch_bytes()},
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
            for (int w = 0; w < warmups; ++w) for (const auto& method : methods) {
                Batch warm(warm_n, K);
                run(*index, router, q, L, warm, method, false, nullptr);
                publish_normal_packet(warm);
                native_calls += warm_n;
            }
            for (int round = 0; round < repeats; ++round)
                for (size_t offset = 0; offset < m; ++offset) {
                    const size_t vi = (point_ordinal + size_t(round) + offset) % m;
                    threads();
                    const double wall = timed_normal_batch(*index, router, q,
                            L, n, K, methods[vi]);
                    timings[vi].push_back(wall);
                    native_calls += n;
                    resource_guard(c, dest);
                    json row = {{"K", K}, {"L", L}, {"method", methods[vi].name},
                            {"round", round}, {"seconds", wall}, {"qps", n / wall},
                            {"n", n}, {"threads", process_threads()}, {"cpu", 15},
                            {"native_calls", native_calls}};
                    rounds.push_back(row);
                    write_json(dest / "timing_progress.json", rounds);
                    std::cout << row.dump() << std::endl;
                }

            std::vector<std::unique_ptr<Batch>> full_plain(m);
            for (size_t vi = 0; vi < m; ++vi) {
                full_plain[vi] = std::make_unique<Batch>(n, K);
                run(*index, router, q, L, *full_plain[vi], methods[vi], false, nullptr);
                native_calls += n;
            }
            for (size_t vi = 0; vi < m; ++vi) {
                const auto& method = methods[vi];
                const Batch& plain = *full_plain[vi];
                same_route(*full_plain[gt_index], plain);
                if (method.extra_cap == 0)
                    audit_merge(*index, q, *full_plain[gt_index], plain, method.posting);
                Batch replay(n, K);
                Stats replay_stats;
                TraceSummary trace_summary;
                std::vector<int32_t> trace;
                if (method.extra_cap > 0)
                    trace.assign(n * trace_words_per_query, -1);
                run(*index, router, q, L, replay, method, false, &replay_stats,
                        true, trace.empty() ? nullptr : &trace,
                        trace.empty() ? nullptr : &trace_summary, zero_intervention);
                native_calls += n;
                same(plain, replay);
                same_route(*full_plain[gt_index], replay);

                Batch sample_plain = sample_packet(plain, audit_ids);
                Batch counted(audit_n, K);
                Stats count_stats;
                run(*index, router, audit_q, L, counted, method, true, &count_stats);
                native_calls += audit_n;
                same(sample_plain, counted);
                const fs::path out = group / (method.name + "_L" + std::to_string(L));
                plain.save(out / "raw", false);
                counted.save(out / "raw", true);
                write_raw(out / "raw/audit_query_ids.i32", audit_ids);
                if (!trace.empty()) {
                    require(trace.size() * sizeof(int32_t) <= 2 * 1024 * 1024,
                            "per-point bounded two-MiB candidate trace");
                    write_raw(out / "raw/region_trace.i32", trace);
                    write_json(out / "raw/region_trace_schema.json", {
                            {"dtype", "native little-endian int32"},
                            {"n", n}, {"words_per_query", trace_words_per_query},
                            {"bytes", trace.size() * sizeof(int32_t)},
                            {"metadata_offsets", {{"seed0", 0}, {"seed1", 1}, {"seed2", 2},
                                    {"nC", 3}, {"nX", 4}, {"nSeeds", 5},
                                    {"m5_committed", 6}, {"extension_aborted", 7}}},
                            {"C_offset", trace_c_offset}, {"C_capacity", 24},
                            {"X_offset", trace_x_offset}, {"X_capacity", 96},
                            {"candidate_padding", -1},
                            {"seed_padding", -1}, {"K", K},
                            {"extra_cap", method.extra_cap},
                            {"candidate_order", "complete scalar-call arrival order; C then X; failing nonfinite word included"},
                            {"score_words", "not serialized; each runtime word independently re-scored and bit-checked in full untimed oracle"},
                            {"trace_source", "independent untimed replay, bit-equal to separately saved full normal plain batch"}});
                    write_json(out / "trace_summary.json", trace_summary_json(trace_summary));
                    write_json(out / "full_region_audit_stats.json", {
                            {"scope", "full untimed region replay only; not timed/full NDC"},
                            {"n", n}, {"stats", stats_json(replay_stats)}});
                }
                json result = {{"method", method.name}, {"table", method.table},
                        {"extra_cap", method.extra_cap}, {"first_seed", method.first_seed},
                        {"K", K}, {"L", L}, {"n", n}, {"smoke_only", smoke},
                        {"timing_seconds", timings[vi]}, {"warmup_batches", warmups},
                        {"warmup_n", warm_n}, {"full_plain_return_n", n},
                        {"full_plain_independent_replay_bits_equal", true},
                        {"full_plain_independent_replay_n", n},
                        {"plain_count_bits_equal", true}, {"count_audit_n", audit_n},
                        {"plain_count_parity_scope", "fixed uniform query sample only"},
                        {"audit_query_ids_formula", "floor(i*(n-1)/(audit_n-1)), endpoints; frozen before responses"},
                        {"stats_scope", "fixed uniform count-audit queries only, not full NDC"},
                        {"graph_ndc_scope", "raw DC calls including main, R/C re-score and additional X; sampled only"},
                        {"independent_original_linear_merge", method.posting && method.extra_cap == 0},
                        {"independent_region_linear_oracle", method.extra_cap > 0},
                        {"linear_merge_audit_n", method.posting ? n : 0},
                        {"region_zero_intervention", zero_intervention && method.posting && method.extra_cap == 0},
                        {"region_zero_intervention_n", zero_intervention && method.posting && method.extra_cap == 0 ? n : 0},
                        {"original_GT_route_words_unchanged", true},
                        {"threads", 1}, {"cpu", 15},
                        {"normal_output_release_before_stop", true}, {"timed_output_retained", false},
                        {"audit_scope", "full saved normal plain plus independent full replay; direct full linear oracle or region full C/X independent score/linear oracle; 256-sample plain/count parity and NDC; timed outputs not captured"},
                        {"stats", stats_json(count_stats)}};
                write_json(out / "complete.json", result);
                results.push_back(result);
                resource_guard(c, dest);
            }
            ++point_ordinal;
            write_json(dest / "progress.json", {{"completed_KL", point_ordinal},
                    {"native_calls", native_calls},
                    {"seconds_including_startup_and_audits", seconds(started)}});
        }
        write_json(dest / "complete.json", {
                {"status", smoke ? "PASS_SMOKE_NATIVE_FULL_REPLAY_ORACLES" :
                                   "PASS_FROZEN_REGION_NATIVE_FULL_PLAIN_REPLAY_SAMPLED_COUNT_ORACLES"},
                {"smoke_only", smoke}, {"results", results},
                {"wall_rounds", rounds.size()}, {"native_calls", native_calls},
                {"formal_order", rounds},
                {"rotation", "(KL ordinal + round + method offset) mod dynamic method count; prelocked"},
                {"wall_boundary", "complete owned normal Batch lifetime, including allocation/init/release and all query/post/region work; loading/GT-scoring/serialization/counts/oracles excluded"},
                {"count_audit_n", audit_n},
                {"count_audit_scope", "fixed uniform sample only; not full NDC"},
                {"full_plain_return_n", n}, {"full_independent_replay_n", n},
                {"full_direct_and_region_oracle_n", n},
                {"seconds_with_startup_and_audits", seconds(started)},
                {"no_GT_read", true}, {"no_training", true},
                {"no_quality_claim_before_GT_evaluation", true}});
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "FATAL " << e.what() << '\n';
        return 2;
    }
}

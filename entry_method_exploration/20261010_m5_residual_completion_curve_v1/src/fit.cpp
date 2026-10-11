#include "runtime.hpp"
#include <limits>

// Training-window response generation only. One original GT10 main search and
// one unmodified Posting::apply per query/K/L; no optimized scorer or region.
// This is charged fitting work. An external dataset-wide deadline must also
// cover this process, compilation, hashes and compile_residual.py.
using namespace exp172;
namespace {
constexpr size_t artifact_cap = 100000000;
bool words(float a, float b) { return !memcmp(&a, &b, 4); }
bool legal(const float* q, size_t d) {
    if ((_mm_getcsr() & 0xffc0U) != 0x1f80U) return false;
    for (size_t j = 0; j < d; ++j) {
        uint32_t b; memcpy(&b, q + j, 4);
        if ((b & 0x7fffffffU) > 0x49800000U) return false;
    }
    return true;
}
json stat4(const fs::path& p) {
    struct stat s; require(!::stat(p.c_str(), &s), "input stat " + p.string());
    return {s.st_dev, s.st_ino, s.st_size,
            uint64_t(s.st_mtim.tv_sec) * 1000000000ULL + s.st_mtim.tv_nsec};
}
struct Item { int32_t id; float d; int priority; };
bool worse(const Item& a, const Item& b) {
    if ((a.id < 0) != (b.id < 0)) return a.id < 0;
    if (a.d != b.d) return a.d > b.d;
    return a.priority > b.priority;
}
void insert(std::vector<Item>& p, const Item& x) {
    size_t w = 0;
    for (size_t j = 1; j < p.size(); ++j) if (worse(p[j], p[w])) w = j;
    if (p[w].id < 0 || x.d < p[w].d) p[w] = x;
}
std::vector<int32_t> independent_candidates(const m5::Posting& p,
        const std::array<int32_t, 3>& route, const std::vector<faiss::idx_t>& r) {
    std::vector<int32_t> c;
    for (auto label : route) {
        auto it = std::lower_bound(p.sorted_labels.begin(), p.sorted_labels.end(), label);
        if (it == p.sorted_labels.end() || *it != label) return {};
        const int slot = p.sorted_slots[it - p.sorted_labels.begin()];
        for (int j = 0; j < p.counts[slot]; ++j) {
            const int32_t id = p.targets[size_t(slot) * 8 + j];
            if (std::find(r.begin(), r.end(), id) == r.end() &&
                    std::find(c.begin(), c.end(), id) == c.end()) c.push_back(id);
        }
    }
    return c;
}
// Independent linear replacement plus independent scalar word checks. Winner
// keys use only actual finite, already-scored original C, never original R.
std::array<int32_t, 3> audit_and_winners(faiss::DistanceComputer& fresh,
        const m5::Posting& p, const std::array<int32_t, 3>& route,
        const std::vector<faiss::idx_t>& original, const std::vector<float>& old_d,
        const std::vector<faiss::idx_t>& actual, const std::vector<float>& actual_d,
        const m5::PostStats& ps) {
    std::array<int32_t, 3> winners{{-1, -1, -1}};
    const auto c = independent_candidates(p, route, original);
    if (p.empty || c.empty() || !ps.commits) {
        for (size_t j = 0; j < original.size(); ++j)
            require(actual[j] == original[j] && words(actual_d[j], old_d[j]),
                    "original M5 fallback packet words");
        return winners;
    }
    require(ps.commits == 1 && ps.candidates == c.size(), "one original M5 commit");
    std::vector<Item> packet;
    std::vector<float> scores;
    for (size_t j = 0; j < original.size(); ++j) {
        const float v = original[j] < 0 ? std::numeric_limits<float>::max() : fresh(original[j]);
        require(std::isfinite(v) && words(v, p.records[j].distance), "fresh original R score word");
        if (original[j] >= 0) require(words(v, old_d[j]), "main R score word equals fresh scalar");
        packet.push_back({int32_t(original[j]), v, int(j)});
    }
    for (size_t j = 0; j < c.size(); ++j) {
        const float v = fresh(c[j]);
        require(p.candidate[j] == c[j] && std::isfinite(v) &&
                words(v, p.records[original.size() + j].distance), "fresh original C ID/score word");
        scores.push_back(v); insert(packet, {c[j], v, int(original.size() + j)});
    }
    std::sort(packet.begin(), packet.end(), [](const Item& a, const Item& b) { return worse(b, a); });
    for (size_t j = 0; j < packet.size(); ++j)
        require(actual[j] == packet[j].id && words(actual_d[j], packet[j].d),
                "independent linear original M5 merge");
    for (size_t row = 0; row < 3; ++row) {
        auto it = std::lower_bound(p.sorted_labels.begin(), p.sorted_labels.end(), route[row]);
        require(it != p.sorted_labels.end() && *it == route[row], "winner route exists");
        const int slot = p.sorted_slots[it - p.sorted_labels.begin()];
        int winner = -1;
        for (int j = 0; j < p.counts[slot]; ++j) {
            const int32_t id = p.targets[size_t(slot) * 8 + j];
            const auto ci = std::find(c.begin(), c.end(), id);
            if (ci == c.end()) continue;
            const int pos = int(ci - c.begin());
            if (winner < 0 || scores[pos] < scores[winner] ||
                    (scores[pos] == scores[winner] && pos < winner)) winner = pos;
        }
        if (winner >= 0) winners[row] = c[winner]; // Distinct route keys are not deduplicated.
    }
    return winners;
}
}

int main(int argc, char** argv) {
    const auto started = Clock::now();
    fs::path dest; json receipt, points = json::array();
    try {
        require(argc == 2, "usage: fit JOB.json");
        const auto c = read_json(argv[1]);
        const size_t n = c.at("n"), d = c.at("dimension");
        require(n == 20000 && (d == 200 || d == 512), "locked historical FIT20K");
        require(c.at("role") == "fit" && c.value("query_format", std::string("raw")) == "raw",
                "only prelocked historical raw TRAIN queries");
        require(c.at("K_values") == json::array({1, 100}) &&
                c.at("L") == json::array({200, 400, 800, 1000, 1200}), "fixed two-K five-L fit matrix");
        const double budget = c.at("max_elapsed_seconds");
        require(budget > 0 && budget <= 900, "remaining dataset fitting budget <=900s");
        dest = c.at("out").get<std::string>(); require(!fs::exists(dest), "preserve fit output");
        fs::create_directories(dest);
        auto guard = [&]() {
            require(seconds(started) < budget, "FIT elapsed deadline exceeded; incomplete artifacts ineligible");
            resource_guard(c, dest);
        };
        threads(); guard();
        const std::string query_path = c.at("queries"), table_path = c.at("original_m5_table");
        json input_stats;
        for (auto p : {query_path, table_path, c.at("index").get<std::string>(),
                c.at("anchor").at("W").get<std::string>(), c.at("anchor").at("graph").get<std::string>(),
                c.at("anchor").at("ids").get<std::string>(), std::string(argv[1])}) input_stats[p] = stat4(p);
        const auto t_load = Clock::now();
        auto q = read_raw<float>(query_path); require(q.size() == n * d, "FIT raw query shape");
        auto index = load_nsg(c.at("index"));
        require(size_t(index->d) == d && index->ntotal == c.at("base_n"), "actual original index dimensions");
        auto loaded = bind_loaded_base(*index, c);
        NativeRouter router(c.at("anchor"), d); router.counting(false);
        m5::Posting posting(table_path); require(posting.base_n == uint32_t(index->ntotal), "frozen M5 base");
        const double loading_seconds = seconds(t_load); guard();
        const auto t_route = Clock::now();
        std::vector<int32_t> entries(n * 3);
        std::vector<std::vector<acsg::EnterPoint>> eps(n);
        for (size_t i = 0; i < n; ++i) {
            if ((i & 63) == 0) guard();
            const auto route = router.route(q.data() + i * d);
            for (int j = 0; j < 3; ++j) {
                require(route.ids[j] >= 0 && route.ids[j] < index->ntotal, "actual route base domain");
                entries[3 * i + j] = route.ids[j]; eps[i].emplace_back(route.ids[j], 1.f);
            }
        }
        const double route_seconds = seconds(t_route);
        faiss::VisitedTable vt(index->ntotal);
        std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(index->storage));
        std::unique_ptr<faiss::DistanceComputer> fresh(acsg::storage_distance_computer(index->storage));
        std::vector<acsg::Neighbor> ret;
        size_t bytes_saved = 0;
        double main_seconds = 0, post_seconds = 0, oracle_seconds = 0, serialization_seconds = 0;
        for (int K : {1, 100}) for (int L : {200, 400, 800, 1000, 1200}) {
            guard(); const auto t_point = Clock::now(); index->acsg.search_L = L;
            std::vector<int32_t> gt_ids(n * K), m5_ids(n * K), winners(n * 3, -1);
            std::vector<uint8_t> statuses(n, 0);
            std::vector<faiss::idx_t> ids(K), original(K); std::vector<float> scores(K), old(K);
            uint64_t committed = 0, unsupported = 0, nonfinite = 0, c_words = 0, post_dots = 0, winner_count = 0;
            double point_main = 0, point_post = 0, point_oracle = 0;
            for (size_t i = 0; i < n; ++i) {
                if ((i & 31) == 0) guard();
                const float* current = q.data() + i * d; dc->set_query(current); vt.advance();
                auto t = Clock::now();
                index->acsg.search_new(*dc, K, ids.data(), scores.data(), vt, 2, eps[i], &ret);
                point_main += seconds(t); original = ids; old = scores;
                for (int j = 0; j < K; ++j) {
                    require(ids[j] >= -1 && ids[j] < index->ntotal, "main ID domain");
                    gt_ids[i * K + j] = int32_t(ids[j]);
                }
                const std::array<int32_t, 3> route{{entries[3 * i], entries[3 * i + 1], entries[3 * i + 2]}};
                m5::PostStats ps;
                const bool supported = legal(current, d);
                t = Clock::now();
                if (supported) posting.apply(*dc, route, K, ids.data(), scores.data(), m5::Mode::POST, &ps);
                point_post += seconds(t);
                if (supported) {
                    statuses[i] = ps.commits ? 2 : (ps.nonfinite_failures ? 3 : 1);
                    t = Clock::now(); fresh->set_query(current);
                    const auto ws = audit_and_winners(*fresh, posting, route, original, old, ids, scores, ps);
                    for (int row = 0; row < 3; ++row) {
                        winners[3 * i + row] = ws[row]; winner_count += ws[row] >= 0;
                    }
                    point_oracle += seconds(t);
                } else {
                    ++unsupported;
                    for (int j = 0; j < K; ++j) require(ids[j] == original[j] && words(scores[j], old[j]), "unsupported keeps GT");
                }
                committed += ps.commits; nonfinite += ps.nonfinite_failures;
                c_words += ps.candidates; post_dots += ps.dots;
                for (int j = 0; j < K; ++j) m5_ids[i * K + j] = int32_t(ids[j]);
            }
            guard(); const auto t_save = Clock::now();
            const fs::path out = dest / ("k" + std::to_string(K) + "_L" + std::to_string(L));
            bytes_saved += (gt_ids.size() + m5_ids.size() + entries.size() + winners.size()) * 4 + statuses.size();
            require(bytes_saved <= artifact_cap, "FIT raw artifacts <=100 decimal MB per dataset");
            write_raw(out / "gt_ids.i32", gt_ids); write_raw(out / "m5_ids.i32", m5_ids);
            write_raw(out / "entry_ids.i32", entries); write_raw(out / "c_winners.i32", winners);
            write_raw(out / "fit_status.u8", statuses);
            const double point_save = seconds(t_save);
            main_seconds += point_main; post_seconds += point_post; oracle_seconds += point_oracle; serialization_seconds += point_save;
            json p = {{"K", K}, {"L", L}, {"n", n}, {"status", "PASS_FIT_ORIGINAL_M5_RESPONSES"},
                {"main_searches", n}, {"full_independent_linear_merge_n", n - unsupported},
                {"m5_commits", committed}, {"unsupported_queries", unsupported}, {"nonfinite_failures", nonfinite},
                {"planned_C", c_words}, {"post_dots", post_dots}, {"winner_route_incidence", winner_count},
                {"main_seconds", point_main}, {"original_m5_seconds", point_post}, {"oracle_seconds", point_oracle},
                {"serialization_seconds", point_save}, {"point_whole_seconds", seconds(t_point)},
                {"winner_scope", "per route best actual original C word; same-score tie by C arrival; no cross-route dedup"},
                {"fit_status", {{"0", "unsupported query; original GT packet"}, {"1", "legal empty/fallback; original GT packet"},
                                {"2", "successful original M5 commit"}, {"3", "nonfinite original M5 fallback"}}}};
            write_json(out / "complete.json", p); points.push_back(p);
            write_json(dest / "progress.json", {{"status", "INCOMPLETE_FIT_NOT_MODEL_ELIGIBLE"},
                {"completed_points", points.size()}, {"seconds", seconds(started)}, {"raw_bytes", bytes_saved}});
        }
        guard();
        for (auto it = input_stats.begin(); it != input_stats.end(); ++it) require(stat4(it.key()) == it.value(), "FIT readonly input identity changed");
        receipt = {{"status", "PASS_FIT_ORIGINAL_M5_ALL_10_POINTS"}, {"dataset", c.at("dataset")}, {"role", "fit"},
            {"n", n}, {"points", points}, {"point_count", points.size()}, {"threads", 1}, {"cpu", 15},
            {"original_m5_unmodified", true}, {"optimized_or_region_used", false}, {"ground_truth_read", false},
            {"raw_artifact_bytes", bytes_saved}, {"raw_artifact_cap", artifact_cap}, {"source_stats_before_after", input_stats},
            {"source_job", fs::absolute(argv[1]).string()}, {"loaded_domain", loaded}, {"router_binding", router.binding()},
            {"loading_and_binding_seconds", loading_seconds}, {"route_seconds", route_seconds}, {"main_seconds", main_seconds},
            {"original_m5_seconds", post_seconds}, {"oracle_seconds", oracle_seconds}, {"serialization_seconds", serialization_seconds},
            {"max_elapsed_seconds", budget}, {"elapsed_seconds", seconds(started)},
            {"charged_scope", "full native process stage, including loading/live binding/route/main/original-M5/independent score/linear oracle/serialization; additional compiler/hash/parent elapsed also charged to the same dataset fitting budget"}};
        write_json(dest / "complete.json", receipt); guard();
        std::cout << "PASS_FIT_ORIGINAL_M5_ALL_10_POINTS " << c.at("dataset") << " " << seconds(started) << '\n';
        return 0;
    } catch (const std::exception& e) {
        if (!dest.empty() && fs::exists(dest)) {
            std::error_code ec; fs::remove(dest / "complete.json", ec);
            write_json(dest / "failure.json", {{"status", "FAIL_FIT_INELIGIBLE"}, {"error", e.what()},
                {"completed_points", points}, {"elapsed_seconds", seconds(started)}, {"partial_is_model_eligible", false}});
        }
        std::cerr << "FIT_FATAL " << e.what() << '\n'; return 2;
    }
}

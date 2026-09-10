// Isolated P3 diagnostic evaluator. The frozen P2 evaluator is unchanged. The online API deliberately has no GT argument.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <fcntl.h>
#include <sys/resource.h>
#include <unistd.h>
#include <argparse/argparse.hpp>
#include <nlohmann/json.hpp>
#include <omp.h>
#include <ACSG/IndexACSG.h>
#include <ACSG/RegionalSearch.h>
#include <benches/datasets/DataLoader.hpp>
#include <hnswlib/hnswlib.h>

using json = nlohmann::json;
using Clock = std::chrono::steady_clock;
namespace rg = acsg::regional;
namespace {
constexpr int region_limit = 256;
thread_local uint64_t* route_counter = nullptr;
struct CountParam { hnswlib::DISTFUNC<float> fn; void* param; };
float count_ip(const void* a, const void* b, const void* p) {
    if (route_counter) ++*route_counter;
    const auto& x = *static_cast<const CountParam*>(p);
    return x.fn(a, b, x.param);
}
class CountSpace final : public hnswlib::SpaceInterface<float> {
    hnswlib::InnerProductSpace inner;
    CountParam p;
public:
    explicit CountSpace(int d) : inner(d), p{inner.get_dist_func(), inner.get_dist_func_param()} {}
    size_t get_data_size() override { return inner.get_data_size(); }
    hnswlib::DISTFUNC<float> get_dist_func() override { return count_ip; }
    void* get_dist_func_param() override { return &p; }
};
struct CountDC final : faiss::DistanceComputer {
    std::unique_ptr<faiss::DistanceComputer> inner;
    uint64_t n = 0;
    explicit CountDC(faiss::DistanceComputer* p) : inner(p) {}
    void set_query(const float* q) override { inner->set_query(q); }
    float operator()(faiss::idx_t id) override { ++n; return (*inner)(id); }
    float symmetric_dis(faiss::idx_t a, faiss::idx_t b) override { return inner->symmetric_dis(a, b); }
};
template<class T> std::vector<T> raw_load(const std::string& p, size_t n = 0) {
    std::ifstream f(p, std::ios::binary | std::ios::ate);
    if (!f) throw std::runtime_error("cannot open: " + p);
    const auto bytes = static_cast<size_t>(f.tellg());
    if (bytes % sizeof(T) || (n && bytes != n * sizeof(T)))
        throw std::runtime_error("raw file size mismatch: " + p);
    std::vector<T> x(bytes / sizeof(T)); f.seekg(0);
    f.read(reinterpret_cast<char*>(x.data()), bytes);
    if (!f) throw std::runtime_error("short read: " + p);
    return x;
}
std::string sha256_bytes(const void* data,size_t bytes) {
    constexpr uint32_t k[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
    uint32_t h[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    auto rr=[](uint32_t x,int n){return (x>>n)|(x<<(32-n));};
    auto input=static_cast<const uint8_t*>(data);size_t total=(bytes+9+63)/64*64;uint64_t bits=static_cast<uint64_t>(bytes)*8;
    for(size_t off=0;off<total;off+=64){uint32_t w[64]{};
        for(size_t j=0;j<64;++j){size_t at=off+j;uint8_t b=at<bytes?input[at]:at==bytes?0x80:0;
            if(at>=total-8)b=static_cast<uint8_t>(bits>>(8*(total-1-at)));
            w[j/4]|=uint32_t(b)<<(24-8*(j%4));}
        for(int j=16;j<64;++j){uint32_t s0=rr(w[j-15],7)^rr(w[j-15],18)^(w[j-15]>>3),s1=rr(w[j-2],17)^rr(w[j-2],19)^(w[j-2]>>10);w[j]=w[j-16]+s0+w[j-7]+s1;}
        uint32_t a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],v=h[7];
        for(int j=0;j<64;++j){uint32_t t1=v+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^(~e&g))+k[j]+w[j];
            uint32_t t2=(rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c));v=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;}
        h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=v;
    }
    constexpr char hex[]="0123456789abcdef";std::string out;out.reserve(64);
    for(auto word:h)for(int shift=28;shift>=0;shift-=4)out+=hex[(word>>shift)&15];
    return out;
}
std::string sha256_file(const std::string& p) {
    const auto bytes = raw_load<uint8_t>(p);
    return sha256_bytes(bytes.data(), bytes.size());
}
json evaluator_provenance() {
    const std::string source = std::filesystem::absolute(__FILE__).string();
    const std::string binary = std::filesystem::read_symlink("/proc/self/exe").string();
    return {{"source_path", source}, {"source_sha256", sha256_file(source)},
            {"binary_path", binary}, {"binary_sha256", sha256_file(binary)},
            {"source_hash_scope", "source file present at execution; root build manifest binds compiled source"}};
}
std::vector<std::string> split_csv(const std::string& s) {
    std::stringstream in(s); std::string x; std::vector<std::string> out;
    while (std::getline(in, x, ',')) { if (x.empty()) throw std::runtime_error("empty CSV item"); out.push_back(x); }
    if (out.empty()) throw std::runtime_error("empty CSV");
    return out;
}
std::vector<int> ints(const std::string& s) {
    std::vector<int> out; for (const auto& x : split_csv(s)) out.push_back(std::stoi(x)); return out;
}
void write_new(const std::string& p, const json& j) {
    const auto parent = std::filesystem::path(p).parent_path();
    if (!parent.empty()) std::filesystem::create_directories(parent);
    const int fd = ::open(p.c_str(), O_WRONLY | O_CREAT | O_EXCL, 0644);
    if (fd < 0) throw std::runtime_error("cannot exclusively create output: " + p);
    const std::string text = j.dump(2) + "\n";
    size_t done = 0;
    while (done < text.size()) {
        const auto n = ::write(fd, text.data() + done, text.size() - done);
        if (n <= 0) { ::close(fd); throw std::runtime_error("output write failed; retained incomplete file: " + p); }
        done += n;
    }
    ::fsync(fd); ::close(fd);
}
struct Model {
    int dim = 0, regions = 64, portals_per_region = 2, schema_version = 1;
    double temperature = 1;
    bool oracle_diagnostic_only = false;
    std::vector<uint16_t> labels;
    std::vector<float> prototypes;
    std::vector<int32_t> portals;
    json manifest;
    void validate_loaded(size_t n) const {
        if ((regions != 64 && regions != 256) || labels.size() != n ||
            portals.size() != static_cast<size_t>(regions * portals_per_region) ||
            (regions == 64 ? portals_per_region != 2 : portals_per_region != 3))
            throw std::runtime_error("model label/portal shape violates fixed P2/P3 schema");
        rg::validate_regions(labels.data(), n, regions);
        if (!oracle_diagnostic_only) {
            if (prototypes.size() != static_cast<size_t>(regions * dim) || temperature != 1.0)
                throw std::runtime_error("P2 prototype shape/temperature mismatch");
            for (float v : prototypes) if (!std::isfinite(v)) throw std::runtime_error("nonfinite model prototype");
        }
        for (int r = 0; r < regions; ++r) {
            if (!oracle_diagnostic_only) {
                double norm = 0; for (int d0 = 0; d0 < dim; ++d0) norm += std::pow(prototypes[r * dim + d0], 2);
                if (std::abs(norm - 1) > .002) throw std::runtime_error("region prototype must be unit normalized");
            }
            for (int j = 0; j < portals_per_region; ++j) {
                const int id = portals[r * portals_per_region + j];
                if (id < 0 || static_cast<size_t>(id) >= n || labels[id] != r)
                    throw std::runtime_error("portal is not a real node in its region");
                for (int t = 0; t < j; ++t)
                    if (id == portals[r * portals_per_region + t]) throw std::runtime_error("duplicate portal within region");
            }
        }
    }
    void load(const std::string& p, size_t n, int d, const std::string& dataset) {
        std::ifstream f(p); if (!f) throw std::runtime_error("missing model: " + p); f >> manifest;
        dim = manifest.at("dim"); regions = manifest.at("region_count");
        schema_version = manifest.at("schema_version"); portals_per_region = manifest.at("portals_per_region");
        if (dim != d || manifest.at("active_regions") != 4 || manifest.at("fit_range") != json::array({10000, 30000}))
            throw std::runtime_error("model violates fixed dimensions/active/fit schema");
        if (schema_version == 1) {
            temperature = manifest.at("temperature");
            if (regions != 64 || portals_per_region != 2 || temperature != 1.0)
                throw std::runtime_error("model violates frozen P2 schema/temperature");
        } else if (schema_version == 2) {
            oracle_diagnostic_only = manifest.at("oracle_diagnostic_only").get<bool>();
            const std::string portal_rule = manifest.at("portal_rule");
            const int lambda = manifest.at("lambda");
            if (regions != 256 || portals_per_region != 3 || !oracle_diagnostic_only ||
                manifest.at("status") != "COMPLETE" || manifest.at("stage") != "P3" ||
                manifest.at("dataset") != dataset || manifest.at("base_nodes") != n ||
                manifest.at("coarse_count") != 16 || manifest.at("leaves_per_coarse") != 16 ||
                manifest.at("parent_rule") != "leaf_id // 16" ||
                (portal_rule != "frequency3" && portal_rule != "greedy3") || (lambda != 0 && lambda != 1))
                throw std::runtime_error("model violates fixed P3 oracle-only schema");
        } else throw std::runtime_error("unsupported model schema");
        auto path = [&](const char* key) {
            std::filesystem::path q = manifest.at(key).get<std::string>();
            return (q.is_absolute() ? q : std::filesystem::path(p).parent_path() / q).string();
        };
        labels = raw_load<uint16_t>(path("labels_file"), n);
        if (!oracle_diagnostic_only) prototypes = raw_load<float>(path("prototypes_file"), regions * dim);
        portals = raw_load<int32_t>(path("portals_file"), regions * portals_per_region);
        if (schema_version == 2 &&
            (sha256_bytes(labels.data(), labels.size() * sizeof(uint16_t)) != manifest.at("labels_sha256") ||
             sha256_bytes(portals.data(), portals.size() * sizeof(int32_t)) != manifest.at("portals_sha256")))
            throw std::runtime_error("P3 model label/portal SHA256 mismatch");
        validate_loaded(n);
    }
};
class FastRouter {
    std::unique_ptr<hnswlib::SpaceInterface<float>> space;
    std::unique_ptr<hnswlib::HierarchicalNSW<float>> graph;
public:
    FastRouter(const std::vector<float>& p, const std::vector<int32_t>& ids, int d, bool count, int seed) {
        if (count) space = std::make_unique<CountSpace>(d);
        else space = std::make_unique<hnswlib::InnerProductSpace>(d);
        graph = std::make_unique<hnswlib::HierarchicalNSW<float>>(space.get(), ids.size(), 16, 200, seed);
        for (size_t i = 0; i < ids.size(); ++i) graph->addPoint(p.data() + i * d, ids[i]);
        graph->setEf(10);
    }
    template<bool Count> void route(const float* q, int m, rg::Route& out, uint64_t& ndc) const {
        // Upstream HNSW queue allocations are real routing costs and remain timed.
        if constexpr (Count) route_counter = &ndc;
        auto heap = graph->searchKnn(q, m);
        if constexpr (Count) route_counter = nullptr;
        if (static_cast<int>(heap.size()) != m) throw std::runtime_error("Fast returned too few entries");
        out.entry_count = m;
        for (int i = m - 1; i >= 0; --i) { out.entries[i] = static_cast<int32_t>(heap.top().second); heap.pop(); }
    }
};
enum class Method { fast, fast_unified, geom_unified, geom_uniform, geom_probability, oracle_unified, oracle_probability };
Method method_of(const std::string& x) {
    if (x == "fast" || x == "fast_legacy") return Method::fast;
    if (x == "fast_unified") return Method::fast_unified;
    if (x == "geom_unified") return Method::geom_unified;
    if (x == "geom_uniform") return Method::geom_uniform;
    if (x == "geom_probability") return Method::geom_probability;
    if (x == "oracle_unified") return Method::oracle_unified;
    if (x == "oracle_probability") return Method::oracle_probability;
    throw std::runtime_error("unknown method: " + x);
}
bool is_oracle(Method m) { return m == Method::oracle_unified || m == Method::oracle_probability; }
bool needs_model(Method m) { return m != Method::fast && m != Method::fast_unified; }
struct Row {
    rg::Route route;
    rg::Stats stats;
    uint64_t routing_ndc = 0, routing_mac = 0;
    double routing_us = 0, graph_us = 0;
    int actual_entries = 0;
    int fast_anchor = -1;
};
struct ThreadWork {
    rg::Workspace search;
    std::vector<float> normalized;
    std::array<double, region_limit> scores{};
    std::array<int, region_limit> order{};
    std::unique_ptr<faiss::DistanceComputer> distance;
    CountDC* counted = nullptr;
    faiss::VisitedTable legacy_visited;
    std::vector<acsg::Neighbor> legacy_pool;
    std::vector<acsg::EnterPoint> legacy_entries;
    ThreadWork(acsg::IndexACSGFlat& index, int l, int k, bool count)
        : search(index.ntotal, l, k), normalized(index.d), legacy_visited(index.ntotal) {
        if (count) {
            counted = new CountDC(acsg::storage_distance_computer(index.storage)); distance.reset(counted);
        } else distance.reset(acsg::storage_distance_computer(index.storage));
        legacy_pool.reserve(l + 1); legacy_entries.reserve(rg::max_entries);
    }
};
void select_regions(const std::array<double, region_limit>& scores, int regions, ThreadWork& w, rg::Route& route) {
    if (regions < 4 || regions > region_limit) throw std::runtime_error("invalid region selector shape");
    std::iota(w.order.begin(), w.order.begin() + regions, 0);
    std::partial_sort(w.order.begin(), w.order.begin() + 4, w.order.begin() + regions, [&](int a, int b) {
        return scores[a] != scores[b] ? scores[a] > scores[b] : a < b;
    });
    route.active = 4; double z = 0;
    for (int i = 0; i < 4; ++i) z += scores[w.order[i]];
    if (!(z > 0)) throw std::runtime_error("region route has no positive mass");
    for (int i = 0; i < 4; ++i) { route.regions[i] = w.order[i]; route.weights[i] = scores[w.order[i]] / z; }
}
// Evaluation-only adapter: never called by route_online, online_query, or batch.
rg::Route oracle_regions(const int64_t* gt10, const Model& model, ThreadWork& work) {
    std::array<double, region_limit> mass{};
    for (int j = 0; j < 10; ++j) {
        const auto id = gt10[j];
        if (id < 0 || static_cast<size_t>(id) >= model.labels.size()) throw std::runtime_error("GT ID outside base");
        mass[model.labels[id]] += .1;
    }
    rg::Route route;
    select_regions(mass, model.regions, work, route);
    return route;
}
template<bool Count>
Row route_online(const float* query, const FastRouter& fast, const Model* model,
                 const rg::Route* diagnostic_regions, Method method, int m, int default_seed, ThreadWork& work) {
    Row out;
    Clock::time_point start;
    if constexpr (Count) start = Clock::now();
    fast.route<Count>(query, m, out.route, out.routing_ndc);
    out.fast_anchor = out.route.entries[0];
    if (needs_model(method)) {
        const int anchor = out.route.entries[0];
        out.route.entry_count = 1; out.route.entries[0] = anchor;
        out.route.shared_seed = default_seed;
        if (is_oracle(method)) {
            if (!diagnostic_regions) throw std::runtime_error("oracle requires evaluation-only region adapter");
            out.route.active = diagnostic_regions->active;
            out.route.regions = diagnostic_regions->regions; out.route.weights = diagnostic_regions->weights;
        } else {
            if (model->oracle_diagnostic_only) throw std::runtime_error("P3 model forbids geometric routing");
            double norm2 = 0;
            for (int d = 0; d < model->dim; ++d) norm2 += static_cast<double>(query[d]) * query[d];
            const float inv = norm2 > 0 ? static_cast<float>(1.0 / std::sqrt(norm2)) : 0;
            for (int d = 0; d < model->dim; ++d) work.normalized[d] = query[d] * inv;
            double max_score = -std::numeric_limits<double>::infinity();
            for (int r = 0; r < model->regions; ++r) {
                float dot = 0;
                for (int d = 0; d < model->dim; ++d) dot += work.normalized[d] * model->prototypes[r * model->dim + d];
                work.scores[r] = dot / model->temperature; max_score = std::max(max_score, work.scores[r]);
            }
            for (int r = 0; r < model->regions; ++r) work.scores[r] = std::exp(work.scores[r] - max_score);
            select_regions(work.scores, model->regions, work, out.route);
            if constexpr (Count) { out.routing_ndc += model->regions; out.routing_mac += uint64_t(model->regions) * model->dim; }
        }
        for (int r = 0; r < out.route.active; ++r) for (int j = 0; j < model->portals_per_region; ++j)
            out.route.entries[out.route.entry_count++] = model->portals[out.route.regions[r] * model->portals_per_region + j];
    }
    // Explicit seed de-duplication is part of the timed online operation.
    int n = 0;
    for (int e = 0; e < out.route.entry_count; ++e) {
        int id = out.route.entries[e]; bool duplicate = id == out.route.shared_seed;
        for (int j = 0; j < n; ++j) duplicate = duplicate || out.route.entries[j] == id;
        if (!duplicate) out.route.entries[n++] = id;
    }
    out.route.entry_count = n; out.actual_entries = n + (out.route.shared_seed >= 0);
    if constexpr (Count) {
        out.routing_mac += (out.routing_ndc - (needs_model(method) && !is_oracle(method) ? model->regions : 0)) * work.normalized.size();
        out.routing_us = std::chrono::duration<double, std::micro>(Clock::now() - start).count();
    }
    return out;
}
// No GT, score, JSON, hash, tracing or output allocation is reachable here.
template<bool Count>
void online_query(acsg::IndexACSGFlat& index, const float* query, const FastRouter& fast,
                  const Model* model, const rg::Route* diagnostic_regions, Method method,
                  int m, int l, int k, ThreadWork& work, int64_t* ids, float* distances, Row& out) {
    out = route_online<Count>(query, fast, model, diagnostic_regions, method, m, index.acsg.enterpoint, work);
    work.distance->set_query(query);
    if constexpr (Count) work.counted->n = 0;
    Clock::time_point graph_start;
    if constexpr (Count) graph_start = Clock::now();
    if (method == Method::fast) {
        work.legacy_entries.clear();
        for (int i = 0; i < out.route.entry_count; ++i) work.legacy_entries.emplace_back(out.route.entries[i], 1.0);
        work.legacy_visited.advance();
        index.acsg.search_new(*work.distance, k, ids, distances, work.legacy_visited, 2,
                              work.legacy_entries, &work.legacy_pool);
    } else {
        const bool regional = method == Method::geom_uniform || method == Method::geom_probability || method == Method::oracle_probability;
        out.stats = rg::search<Count>(*index.acsg.final_graph, *work.distance,
            model ? model->labels.data() : nullptr, model ? model->regions : 1,
            out.route, l, k, regional, method == Method::geom_uniform, work.search, ids, distances);
    }
    if constexpr (Count) {
        if (method != Method::fast && out.stats.ndc != work.counted->n)
            throw std::runtime_error("regional kernel and independent distance counter disagree");
        out.stats.ndc = work.counted->n;
        out.graph_us = std::chrono::duration<double, std::micro>(Clock::now() - graph_start).count();
    }
}
double recall(const int64_t* ids, const int64_t* gt, int k) {
    int hits = 0;
    for (int i = 0; i < k; ++i) if (ids[i] >= 0)
        for (int j = 0; j < k; ++j) if (ids[i] == gt[j]) { ++hits; break; }
    return double(hits) / k;
}
uint64_t hash_ids(const std::vector<int64_t>& ids) {
    uint64_t hash = 1469598103934665603ULL;
    for (auto id : ids) { hash ^= static_cast<uint64_t>(id); hash *= 1099511628211ULL; } return hash;
}
uint64_t hash_routes(const std::vector<Row>& rows) {
    uint64_t h = 1469598103934665603ULL;
    auto put = [&](uint64_t x) { h ^= x; h *= 1099511628211ULL; };
    for (const auto& row : rows) {
        put(row.fast_anchor); put(row.route.shared_seed); put(row.route.entry_count); put(row.route.active);
        for (int i = 0; i < row.route.entry_count; ++i) put(row.route.entries[i]);
        for (int i = 0; i < row.route.active; ++i) {
            put(row.route.regions[i]); uint64_t bits; std::memcpy(&bits, &row.route.weights[i], sizeof(bits)); put(bits);
        }
    }
    return h;
}
bool same_route(const Row& a, const Row& b) {
    return a.fast_anchor == b.fast_anchor && a.actual_entries == b.actual_entries &&
        a.route.entry_count == b.route.entry_count && a.route.active == b.route.active &&
        a.route.shared_seed == b.route.shared_seed && a.route.entries == b.route.entries &&
        a.route.regions == b.route.regions && a.route.weights == b.route.weights;
}
void self_test() {
    constexpr int n = 192, d = 8, degree = 12, l = 32, k = 10;
    acsg::IndexACSGFlat index(d, degree, faiss::METRIC_INNER_PRODUCT);
    std::vector<float> base(n * d);
    for (size_t i = 0; i < base.size(); ++i) base[i] = std::sin(float(i + 1) * .371f);
    index.storage->add(n, base.data()); index.ntotal = n; index.is_built = true;
    index.acsg.ntotal = n; index.acsg.is_built = true; index.acsg.enterpoint = 0; index.acsg.search_L = l;
    index.acsg.final_graph = std::make_shared<acsg::Graph<int32_t>>(n, degree);
    for (int i = 0; i < n; ++i) for (int j = 0; j < degree; ++j)
        index.acsg.final_graph->at(i, j) = (i + j * 13 + 1) % n;
    Model model; model.dim = d; model.labels.resize(n); model.portals.resize(128); model.prototypes.resize(64 * d);
    for (int i = 0; i < n; ++i) model.labels[i] = i % 64;
    for (int r = 0; r < 64; ++r) {
        model.portals[r * 2] = r; model.portals[r * 2 + 1] = r + 64;
        float norm = 0;
        for (int j = 0; j < d; ++j) { model.prototypes[r * d + j] = base[r * d + j]; norm += base[r * d + j] * base[r * d + j]; }
        for (int j = 0; j < d; ++j) model.prototypes[r * d + j] /= std::sqrt(norm);
    }
    std::vector<int32_t> hubs(64); std::iota(hubs.begin(), hubs.end(), 0);
    FastRouter plain(model.prototypes, hubs, d, false, 100), counted(model.prototypes, hubs, d, true, 100);
    ThreadWork wp(index, l, k, false), wc(index, l, k, true);
    std::array<int64_t, k> a{}, b{}; std::array<float, k> da{}, db{};
    int checks = 0;
    rg::Route oracle; oracle.active = 4; oracle.regions = {2, 8, 14, 20}; oracle.weights = {.5, .3, .1, .1};
    for (int q = 0; q < 40; ++q) {
      Row legacy, geometric, oracle_reference;
      std::array<int64_t, k> legacy_ids{}; std::array<float, k> legacy_distances{};
      for (Method m : {Method::fast, Method::fast_unified, Method::geom_unified, Method::geom_uniform, Method::geom_probability, Method::oracle_unified, Method::oracle_probability}) {
        Row ra, rb;
        online_query<false>(index, base.data() + q * d, plain, &model, &oracle, m, 3, l, k, wp, a.data(), da.data(), ra);
        online_query<true>(index, base.data() + q * d, counted, &model, &oracle, m, 3, l, k, wc, b.data(), db.data(), rb);
        if (a != b || da != db || !same_route(ra, rb) ||
            rb.stats.ndc == 0 || rb.routing_ndc == 0 || ra.routing_ndc != 0)
            throw std::runtime_error("synthetic count/plain route/result/distance parity failure");
        if (m == Method::fast) { legacy = rb; legacy_ids = b; legacy_distances = db; }
        if (m == Method::fast_unified && (b != legacy_ids || db != legacy_distances || rb.stats.ndc != legacy.stats.ndc || !same_route(rb, legacy)))
            throw std::runtime_error("synthetic Fast legacy/unified same-entry parity failure");
        if (m == Method::geom_unified) geometric = rb;
        if ((m == Method::geom_uniform || m == Method::geom_probability) && !same_route(geometric, rb))
            throw std::runtime_error("geometric ablations have mismatched routes");
        if (m == Method::oracle_unified) oracle_reference = rb;
        if (m == Method::oracle_probability && !same_route(oracle_reference, rb))
            throw std::runtime_error("oracle ablations have mismatched routes");
        ++checks;
      }
    }
    // A graph with no edges makes actual seed consumption directly observable.
    std::fill_n(index.acsg.final_graph->data, n * degree, -1);
    for (int m : {3, 4, 6, 8}) {
        Row row;
        online_query<true>(index, base.data(), counted, nullptr, nullptr, Method::fast_unified, m, l, k, wc, a.data(), da.data(), row);
        if (row.actual_entries != m || row.route.entry_count != m || row.stats.ndc != static_cast<uint64_t>(m))
            throw std::runtime_error("Fast top-m dropped entries");
        for (int e = 0; e < m; ++e) if (std::find(a.begin(), a.end(), row.route.entries[e]) == a.end())
            throw std::runtime_error("Fast top-m reported a seed that was not searched");
    }
    std::cout << "HIERARCHICAL_SELF_TEST_PASS count_plain_checks=" << checks << " cpu_only=true\n";
}
void self_test_p3() {
    if (sha256_bytes("", 0) != "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" ||
        sha256_bytes("abc", 3) != "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        throw std::runtime_error("SHA256 known-answer test failed");
    constexpr int n = 1024, d = 8, degree = 12, l = 64, k = 10;
    acsg::IndexACSGFlat index(d, degree, faiss::METRIC_INNER_PRODUCT);
    std::vector<float> base(n * d);
    for (size_t i = 0; i < base.size(); ++i) base[i] = std::sin(float(i + 1) * .371f);
    index.storage->add(n, base.data()); index.ntotal = n; index.is_built = true;
    index.acsg.ntotal = n; index.acsg.is_built = true; index.acsg.enterpoint = n - 1; index.acsg.search_L = l;
    index.acsg.final_graph = std::make_shared<acsg::Graph<int32_t>>(n, degree);
    for (int i = 0; i < n; ++i) for (int j = 0; j < degree; ++j)
        index.acsg.final_graph->at(i, j) = (i + j * 13 + 1) % n;
    Model model; model.dim = d; model.regions = 256; model.portals_per_region = 3;
    model.schema_version = 2; model.oracle_diagnostic_only = true; model.labels.resize(n); model.portals.resize(768);
    for (int i = 0; i < n; ++i) model.labels[i] = i % 256;
    for (int r = 0; r < 256; ++r) for (int j = 0; j < 3; ++j) model.portals[r * 3 + j] = r + j * 256;
    model.validate_loaded(n); // Geometry/prototype storage is deliberately empty.
    auto expect_invalid_model = [&](const Model& broken) {
        try { broken.validate_loaded(n); } catch (const std::exception&) { return; }
        throw std::runtime_error("synthetic invalid P3 model was accepted");
    };
    { auto broken = model; broken.labels[1023] = 256; expect_invalid_model(broken); }
    { auto broken = model; broken.portals[767] = 1024; expect_invalid_model(broken); }
    { auto broken = model; broken.portals[767] = 0; expect_invalid_model(broken); }
    { auto broken = model; broken.portals[767] = broken.portals[766]; expect_invalid_model(broken); }
    { auto broken = model; broken.portals.pop_back(); expect_invalid_model(broken); }
    std::vector<int32_t> hubs(64); std::vector<float> prototypes(64 * d);
    for (int r = 0; r < 64; ++r) {
        hubs[r] = 768 + r;
        std::copy_n(base.data() + hubs[r] * d, d, prototypes.data() + r * d);
    }
    FastRouter plain(prototypes, hubs, d, false, 100), counted(prototypes, hubs, d, true, 100);
    ThreadWork wp(index, l, k, false), wc(index, l, k, true);
    auto check_gt_route = [&](std::array<int64_t, 10> gt, std::array<int, 4> regions) {
        const auto route = oracle_regions(gt.data(), model, wp);
        if (route.regions != regions || route.active != 4)
            throw std::runtime_error("256-leaf oracle global ordering/tie/parent selection failed");
        return route;
    };
    const auto oracle = check_gt_route({0,256,16,272,32,288,48,304,64,80}, {0,16,32,48});
    check_gt_route({128,384,144,400,192,448,255,511,0,16}, {128,144,192,255});
    check_gt_route({17,273,18,274,19,275,20,276,32,48}, {17,18,19,20});
    check_gt_route({255,511,767,1023,255,511,767,1023,255,511}, {255,0,1,2});
    std::array<int64_t, k> a{}, b{}; std::array<float, k> da{}, db{};
    int parity_checks = 0;
    for (int q = 0; q < 40; ++q) {
        Row first;
        for (auto method : {Method::oracle_unified, Method::oracle_probability}) {
            Row ra, rb;
            online_query<false>(index, base.data() + q * d, plain, &model, &oracle, method, 3, l, k, wp, a.data(), da.data(), ra);
            online_query<true>(index, base.data() + q * d, counted, &model, &oracle, method, 3, l, k, wc, b.data(), db.data(), rb);
            if (a != b || da != db || !same_route(ra, rb) || rb.stats.ndc == 0 ||
                rb.routing_ndc == 0 || ra.routing_ndc != 0 || rb.actual_entries != 14)
                throw std::runtime_error("P3 count/plain route/result/distance/entry parity failure");
            if (method == Method::oracle_unified) first = rb;
            else if (!same_route(first, rb)) throw std::runtime_error("P3 oracle ablation route mismatch");
            ++parity_checks;
        }
    }
    // No-edge replay proves that all 14 unique seeds reach the actual kernel,
    // including the shared default and each of the twelve real leaf portals.
    std::fill_n(index.acsg.final_graph->data, n * degree, -1);
    int seed_checks = 0, owner_checks = 0;
    auto check_seed_replay = [&](const rg::Route& diagnostic, int expected) {
        for (auto method : {Method::oracle_unified, Method::oracle_probability}) {
            Row ra, rb;
            online_query<false>(index, base.data(), plain, &model, &diagnostic, method, 3, l, k, wp, a.data(), da.data(), ra);
            online_query<true>(index, base.data(), counted, &model, &diagnostic, method, 3, l, k, wc, b.data(), db.data(), rb);
            if (a != b || da != db || !same_route(ra, rb) || rb.actual_entries != expected || rb.stats.ndc != static_cast<uint64_t>(expected))
                throw std::runtime_error("P3 seeds were dropped or evaluated twice");
            std::vector<rg::Event> events;
            wc.distance->set_query(base.data()); wc.counted->n = 0;
            const auto stats = rg::search<true>(*index.acsg.final_graph, *wc.distance, model.labels.data(), model.regions,
                rb.route, l, k, method == Method::oracle_probability, false, wc.search, b.data(), db.data(), &events);
            if (stats.ndc != static_cast<uint64_t>(expected) || wc.counted->n != stats.ndc || a != b || da != db)
                throw std::runtime_error("P3 actual-seed trace replay parity failure");
            std::vector<int> discovered;
            for (const auto& event : events) if (event.kind == rg::EventKind::discover) {
                int owner = 0;
                if (method == Method::oracle_probability && event.id != rb.route.shared_seed)
                    for (int r = 0; r < 4; ++r) if (model.labels[event.id] == rb.route.regions[r]) owner = r + 1;
                if (event.queue != owner || event.parent != -1 || std::find(discovered.begin(), discovered.end(), event.id) != discovered.end())
                    throw std::runtime_error("P3 shared-seed ownership or seed deduplication failed");
                discovered.push_back(event.id); ++owner_checks;
            }
            if (static_cast<int>(discovered.size()) != expected || discovered.front() != rb.route.shared_seed)
                throw std::runtime_error("P3 actual seed discovery set mismatch");
            for (int e = 0; e < rb.route.entry_count; ++e)
                if (std::find(discovered.begin(), discovered.end(), rb.route.entries[e]) == discovered.end())
                    throw std::runtime_error("P3 reported seed was not searched");
            ++seed_checks;
        }
    };
    check_seed_replay(oracle, 14);
    // Two deliberate overlaps: Fast anchor is a leaf portal; default is a
    // second portal of that same active leaf. It must still own shared queue 0.
    const auto anchor = route_online<false>(base.data(), plain, &model, &oracle, Method::oracle_unified, 3, index.acsg.enterpoint, wp).fast_anchor;
    rg::Route duplicate_route = oracle;
    const int leaf = model.labels[anchor];
    duplicate_route.regions = {leaf, 64, 128, 192};
    model.portals[leaf * 3] = anchor;
    index.acsg.enterpoint = model.portals[leaf * 3 + 1];
    model.validate_loaded(n);
    check_seed_replay(duplicate_route, 12);
    std::cout << "HIERARCHICAL_P3_SELF_TEST_PASS oracle_selector_checks=4 invalid_model_checks=5 count_plain_checks=" << parity_checks
              << " actual_seed_checks=" << seed_checks << " owner_checks=" << owner_checks
              << " sha256_known_answers=2 geometry_prototypes=0 cpu_only=true\n";
    std::cout << "HIERARCHICAL_P3_PROVENANCE " << evaluator_provenance().dump() << '\n';
}
} // namespace

int main(int argc, char** argv) {
    setvbuf(stdout, nullptr, _IONBF, 0);
    argparse::ArgumentParser cli("bench_hierarchical_eval_p3");
    for (const auto* name : {"--stage", "--split", "--measurement", "--output", "--dataset", "--index-file", "--model", "--fast-hubs", "--fast-ids", "--p6-gate"})
        cli.add_argument(name).default_value(std::string(""));
    cli.add_argument("--methods").default_value(std::string("fast,geom_unified,geom_uniform,geom_probability"));
    cli.add_argument("--search-ls").default_value(std::string("64,128"));
    cli.add_argument("--top-k").default_value(10).scan<'i', int>();
    cli.add_argument("--fast-m").default_value(3).scan<'i', int>();
    cli.add_argument("--max-queries").default_value(10000).scan<'i', int>();
    cli.add_argument("--query-offset").default_value(0).scan<'i', int>();
    cli.add_argument("--threads").default_value(16).scan<'i', int>();
    cli.add_argument("--rounds").default_value(5).scan<'i', int>();
    cli.add_argument("--warmup-queries").default_value(128).scan<'i', int>();
    cli.add_argument("--hnsw-seed").default_value(100).scan<'i', int>();
    cli.add_argument("--self-test").default_value(false).implicit_value(true);
    try {
        cli.parse_args(argc, argv);
        if (cli.get<bool>("--self-test")) { self_test(); self_test_p3(); return 0; }
        auto str = [&](const char* key) { return cli.get<std::string>(key); };
        const auto stage = str("--stage"), split = str("--split"), measurement = str("--measurement"), output_path = str("--output");
        const bool trace_mode = measurement == "trace";
        const bool count = measurement == "count" || trace_mode;
        const int k = cli.get<int>("--top-k"), m = cli.get<int>("--fast-m"), threads = cli.get<int>("--threads"), rounds = cli.get<int>("--rounds");
        const int limit = cli.get<int>("--max-queries"), offset = cli.get<int>("--query-offset"), warmup = cli.get<int>("--warmup-queries"), seed = cli.get<int>("--hnsw-seed");
        const auto ls = ints(str("--search-ls")); const auto names = split_csv(str("--methods"));
        if (stage != "P1" && stage != "P2" && stage != "P3") throw std::runtime_error("P3 diagnostic binary requires explicit --stage P1|P2|P3");
        if (split != "pilot" && split != "fit") throw std::runtime_error("P3 diagnostic binary permits only --split pilot|fit; validation/heldout forbidden");
        if (measurement != "count" && measurement != "timing" && !trace_mode) throw std::runtime_error("explicit --measurement count|timing|trace required");
        if (output_path.empty() || std::filesystem::exists(output_path)) throw std::runtime_error("--output must name a new file");
        if (k < 1 || k > 100 || m < 1 || m > 8 || threads < 1 || rounds < 1 || limit < 1 || offset < 0 || warmup < 1 || seed < 0)
            throw std::runtime_error("invalid K/m/thread/round/query/warmup/seed");
        for (int l : ls) if (l < k) throw std::runtime_error("K > L is forbidden");
        if (!count && split != "heldout" && rounds != 5) throw std::runtime_error("pilot/validation timing requires five preregistered rounds");
        if (!count && split == "heldout" && rounds != 3) throw std::runtime_error("heldout timing requires three rounds per frozen build");
        if (count && rounds != 1) throw std::runtime_error("count requires --rounds 1; it is not a timing replicate");
        if (trace_mode && (limit > 32 || k != 10)) throw std::runtime_error("trace requires max-queries<=32 and K=10");
        std::vector<Method> methods; bool want_model = false, want_oracle = false;
        for (const auto& name : names) {
            const auto method = method_of(name);
            if (std::find(methods.begin(), methods.end(), method) != methods.end()) throw std::runtime_error("duplicate method");
            methods.push_back(method); want_model |= needs_model(method); want_oracle |= is_oracle(method);
        }
        if (want_oracle && split != "pilot" && split != "fit") throw std::runtime_error("oracle is train-development-only");
        if (m != 3 && std::find(methods.begin(), methods.end(), Method::fast) != methods.end()) throw std::runtime_error("legacy Fast consumes three entries; use fast_unified for top-m");
        if (trace_mode && std::find(methods.begin(), methods.end(), Method::fast) != methods.end()) throw std::runtime_error("trace requires new search methods; use fast_unified for matched Fast entries");
        if (str("--dataset").empty() || str("--index-file").empty() || str("--fast-hubs").empty() || str("--fast-ids").empty() || (want_model && str("--model").empty()))
            throw std::runtime_error("dataset/index/Fast/model input paths required");
        const std::string parts = output_path + ".parts";
        if (std::filesystem::exists(parts)) throw std::runtime_error("refusing existing output parts directory");
        const auto parts_parent = std::filesystem::path(parts).parent_path();
        if (!parts_parent.empty()) std::filesystem::create_directories(parts_parent);
        if (!std::filesystem::create_directory(parts)) throw std::runtime_error("could not exclusively create output parts");
        write_new(parts + "/started.json", {{"status", "INCOMPLETE"}, {"stage", stage}, {"split", split}, {"measurement", measurement}, {"final_output", output_path}, {"pid", getpid()}});
        DataLoader loader(str("--dataset"));
        if (loader.metric_type() != faiss::METRIC_INNER_PRODUCT) throw std::runtime_error("P2/P3 requires frozen inner-product data");
        const std::string query_type = "drl_train";
        auto [all_nq, queries] = loader.load_query(query_type);
        auto [gt_k, gt] = loader.load_gt(query_type);
        const int split_begin = split == "fit" ? 10000 : 0;
        const int split_size = split == "fit" ? 20000 : 10000;
        if (offset >= split_size || split_begin + split_size > static_cast<int>(all_nq) || gt_k < static_cast<size_t>(k))
            throw std::runtime_error("requested split/range/GT not available");
        const int nq = std::min(limit, split_size - offset), begin = split_begin + offset;
        // Validate measured queries outside all timers; fitting rows remain unused.
        for (size_t i = static_cast<size_t>(begin) * loader.dim(); i < static_cast<size_t>(begin + nq) * loader.dim(); ++i)
            if (!std::isfinite(queries[i])) throw std::runtime_error("nonfinite query");
        auto index = std::make_unique<acsg::IndexACSGFlat>(); index->loadACPG(str("--index-file").c_str());
        std::vector<float>().swap(index->acsg.pheromone); std::vector<float>().swap(index->acsg.weight);
        if (index->d != static_cast<int>(loader.dim()) || index->metric_type != loader.metric_type() || !index->acsg.final_graph)
            throw std::runtime_error("frozen index dimensionality/metric mismatch");
        Model model; if (want_model) model.load(str("--model"), index->ntotal, index->d, str("--dataset"));
        if (want_model && model.schema_version == 2) {
            if (stage != "P1" && stage != "P3") throw std::runtime_error("P3 model requires P1 reacceptance or P3 diagnostics");
            for (auto method : methods) if (needs_model(method) && !is_oracle(method))
                throw std::runtime_error("P3 model only permits Fast and diagnostic oracle methods");
            if (k != 10 || m != 3) throw std::runtime_error("P3 fixed protocol requires K=10 and Fast m=3");
            if (stage == "P3") for (int l : ls) if (l != 64 && l != 128)
                throw std::runtime_error("P3 fixed protocol requires L64/128");
        }
        const auto hubs = raw_load<int32_t>(str("--fast-ids"));
        if (hubs.size() < 8) throw std::runtime_error("Fast requires at least eight hubs");
        auto unique_hubs = hubs; std::sort(unique_hubs.begin(), unique_hubs.end());
        if (unique_hubs.front() < 0 || unique_hubs.back() >= index->ntotal || std::adjacent_find(unique_hubs.begin(), unique_hubs.end()) != unique_hubs.end())
            throw std::runtime_error("Fast IDs invalid/duplicate");
        const auto prototypes = raw_load<float>(str("--fast-hubs"), hubs.size() * index->d);
        for (float v : prototypes) if (!std::isfinite(v)) throw std::runtime_error("nonfinite Fast prototype");
        const auto router_begin = Clock::now(); FastRouter router(prototypes, hubs, index->d, count, seed);
        const double router_build_s = std::chrono::duration<double>(Clock::now() - router_begin).count();
        omp_set_dynamic(0); omp_set_num_threads(threads);
        std::vector<std::unique_ptr<ThreadWork>> work;
        for (int t = 0; t < threads; ++t) work.push_back(std::make_unique<ThreadWork>(*index, *std::max_element(ls.begin(), ls.end()), k, count));
        std::vector<int64_t> ids(static_cast<size_t>(nq) * k); std::vector<float> distances(ids.size());
        std::vector<Row> rows(nq); std::vector<rg::Route> oracle(nq);
        // GT -> region mass is confined to this separate, untimed diagnostic adapter.
        if (want_oracle && gt_k < 10) throw std::runtime_error("oracle requires GT10");
        if (want_oracle) for (int q = 0; q < nq; ++q)
            oracle[q] = oracle_regions(gt.get() + static_cast<size_t>(begin + q) * gt_k, model, *work[0]);
        json schedule = json::array();
        for (int l : ls) for (int r = 0; r < rounds; ++r) {
            std::vector<int> order(methods.size()); std::iota(order.begin(), order.end(), 0);
            if (r % 2) std::reverse(order.begin(), order.end());
            for (int mi : order) schedule.push_back({{"L", l}, {"round", r}, {"method_index", mi}, {"method", names[mi]}, {"order", r % 2 ? "BA" : "AB"}});
        }
        json output = {{"schema_version", 1}, {"status", "RUNNING"}, {"dataset", str("--dataset")}, {"stage", stage}, {"split", split}, {"source_query_type", query_type},
            {"source_query_range", {begin, begin + nq}}, {"num_queries", nq}, {"measurement", measurement}, {"threads", threads}, {"cpu_only", true},
            {"metric", loader.metric_name()}, {"dim", index->d}, {"base_nodes", index->ntotal}, {"normalization", loader.normalization()}, {"artifact_version", loader.artifact_version()},
            {"index_file", str("--index-file")}, {"model_file", str("--model")}, {"fast_hubs", str("--fast-hubs")}, {"fast_ids", str("--fast-ids")},
            {"model_manifest", want_model ? model.manifest : json(nullptr)}, {"fast_m", m}, {"top_k", k}, {"search_Ls", ls}, {"rounds", rounds}, {"warmup_queries", std::min(warmup, nq)},
            {"schedule", schedule}, {"schedule_prerecorded", true}, {"heldout_accessed", split == "heldout"}, {"oracle_is_deployment", false},
            {"hnsw", {{"M", 16}, {"ef_construction", 200}, {"ef_search", 10}, {"seed", seed}, {"build_seconds", router_build_s}}},
            {"timer_contract", {{"gt_scoring_inside", false}, {"workspace_allocation_inside", false}, {"output_allocation_inside", false}, {"trace_inside", false}, {"hash_inside", false}, {"json_inside", false},
                {"query_normalization_inside", true}, {"query_normalization_applies_to", {"geom_unified", "geom_uniform", "geom_probability"}}, {"fast_and_oracle_hnsw_query", "unchanged raw query"},
                {"routing_inside", true}, {"search_and_reset_inside", true}, {"result_writes_inside", true}, {"hnsw_internal_allocations_inside", true}}},
            {"cache_condition", "same-process warmed; warmup before each L/method; no cache flushing"},
            {"routing_mac_definition", "one MAC per dimension per routing distance; excludes norm/softmax/scheduling scalar operations, which remain timed"},
            {"results", json::array()}};
        output["evaluator_provenance"] = evaluator_provenance();
        output["model_sha256"] = want_model ? json(sha256_file(str("--model"))) : json(nullptr);
        output["region_count"] = want_model ? model.regions : 0;
        output["portals_per_region"] = want_model ? model.portals_per_region : 0;
        output["oracle_selection"] = "GT10 mass; global top four leaf IDs; mass ties by ascending leaf ID; at most four parents by leaf_id // 16";
        output["parts_directory"] = parts;
        output["aligned_rows_round"] = 0;
        output["trace_mode"] = trace_mode;
        write_new(parts + "/manifest.json", output);
        int completed_batches = 0;
        // Dedicated reusable batch function: timed boundary encloses only online work.
        auto batch = [&](Method method, int l, int count_q, bool route_only) {
            const auto start = Clock::now();
            #pragma omp parallel for schedule(static)
            for (int q = 0; q < count_q; ++q) {
                auto& w = *work[omp_get_thread_num()];
                const auto* query = queries.get() + static_cast<size_t>(begin + q) * index->d;
                const auto* diagnostic = is_oracle(method) ? &oracle[q] : nullptr;
                if (route_only) {
                    if (count) rows[q] = route_online<true>(query, router, want_model ? &model : nullptr, diagnostic, method, m, index->acsg.enterpoint, w);
                    else rows[q] = route_online<false>(query, router, want_model ? &model : nullptr, diagnostic, method, m, index->acsg.enterpoint, w);
                } else {
                    if (count) online_query<true>(*index, query, router, want_model ? &model : nullptr, diagnostic, method, m, l, k, w, ids.data() + q * k, distances.data() + q * k, rows[q]);
                    else online_query<false>(*index, query, router, want_model ? &model : nullptr, diagnostic, method, m, l, k, w, ids.data() + q * k, distances.data() + q * k, rows[q]);
                }
            }
            return std::chrono::duration<double, std::micro>(Clock::now() - start).count();
        };
        for (int l : ls) {
            index->acsg.search_L = l;
            // Warm every method and worker before its first recorded sample at this L.
            for (auto method : methods) batch(method, l, std::min(warmup, nq), false);
            std::vector<uint64_t> first_ids(methods.size()), first_routes(methods.size());
            for (int r = 0; r < rounds; ++r) {
                std::vector<int> order(methods.size()); std::iota(order.begin(), order.end(), 0);
                if (r % 2) std::reverse(order.begin(), order.end());
                for (int mi : order) {
                    const Method method = methods[mi];
                    const double wall_us = batch(method, l, nq, false);
                    // The timer has ended. All scoring, hashing and JSON happen here.
                    const uint64_t ids_hash = hash_ids(ids), route_hash = hash_routes(rows);
                    if (r == 0) { first_ids[mi] = ids_hash; first_routes[mi] = route_hash; }
                    else if (first_ids[mi] != ids_hash || first_routes[mi] != route_hash)
                        throw std::runtime_error("result/route changed across repeated timing rounds");
                    double sum_recall = 0, route_us = 0, graph_us = 0;
                    uint64_t route_ndc = 0, graph_ndc = 0, mac = 0; int min_entries = 100, max_entries = 0;
                    json aligned = json::array();
                    for (int q = 0; q < nq; ++q) {
                        const auto& row = rows[q]; const auto* result = ids.data() + q * k;
                        const double rec = recall(result, gt.get() + static_cast<size_t>(begin + q) * gt_k, k); sum_recall += rec;
                        route_ndc += row.routing_ndc; graph_ndc += row.stats.ndc; mac += row.routing_mac; route_us += row.routing_us; graph_us += row.graph_us;
                        min_entries = std::min(min_entries, row.actual_entries); max_entries = std::max(max_entries, row.actual_entries);
                        json item = {{"query_id", begin + q}, {"recall", rec}, {"result_ids", std::vector<int64_t>(result, result + k)},
                            {"entry_ids", std::vector<int32_t>(row.route.entries.begin(), row.route.entries.begin() + row.route.entry_count)}, {"fast_anchor_id", row.fast_anchor}, {"shared_seed", row.route.shared_seed}, {"actual_entry_count", row.actual_entries},
                            {"regions", std::vector<int>(row.route.regions.begin(), row.route.regions.begin() + row.route.active)}, {"weights", std::vector<double>(row.route.weights.begin(), row.route.weights.begin() + row.route.active)}};
                        if (count) {
                            item["routing_ndc"] = row.routing_ndc; item["graph_ndc"] = row.stats.ndc; item["total_ndc"] = row.routing_ndc + row.stats.ndc;
                            item["routing_mac"] = row.routing_mac; item["routing_us_instrumented"] = row.routing_us; item["graph_us_instrumented"] = row.graph_us;
                            item["graph_mac"] = row.stats.ndc * index->d; item["total_mac"] = row.routing_mac + row.stats.ndc * index->d;
                            item["expanded"] = row.stats.expanded; item["rejected"] = row.stats.rejected; item["evicted_unexpanded"] = row.stats.evicted_unexpanded;
                        }
                        if (r == 0) aligned.push_back(std::move(item));
                    }
                    json result = {{"method", names[mi]}, {"search_L", l}, {"top_k", k}, {"round", r}, {"mean_recall", sum_recall / nq}, {"result_hash_fnv1a64", ids_hash}, {"route_hash_fnv1a64", route_hash}, {"repeated_routes_results_stable", true},
                        {"oracle", is_oracle(method)}, {"timing_publishable", !count && !is_oracle(method)}, {"batch_wall_us", count ? json(nullptr) : json(wall_us)}, {"qps", count ? json(nullptr) : json(nq * 1e6 / wall_us)},
                        {"mean_routing_ndc", count ? json(double(route_ndc) / nq) : json(nullptr)}, {"mean_graph_ndc", count ? json(double(graph_ndc) / nq) : json(nullptr)}, {"mean_total_ndc", count ? json(double(route_ndc + graph_ndc) / nq) : json(nullptr)},
                        {"mean_routing_mac", count ? json(double(mac) / nq) : json(nullptr)}, {"min_actual_entry_count", min_entries}, {"max_actual_entry_count", max_entries}};
                    result["mean_graph_mac"] = count ? json(double(graph_ndc) * index->d / nq) : json(nullptr);
                    result["mean_total_mac"] = count ? json((double(mac) + double(graph_ndc) * index->d) / nq) : json(nullptr);
                    if (r == 0) result["per_query"] = std::move(aligned);
                    else result["aligned_reference_round"] = 0;
                    if (count) { result["mean_routing_us_instrumented"] = route_us / nq; result["mean_graph_us_instrumented"] = graph_us / nq; }
                    if (trace_mode) {
                        result["trace_files"] = json::array();
                        for (int q = 0; q < nq; ++q) {
                            auto& w = *work[0]; const auto& route = rows[q].route;
                            w.distance->set_query(queries.get() + static_cast<size_t>(begin + q) * index->d); w.counted->n = 0;
                            std::vector<rg::Event> events; events.reserve(65536);
                            std::vector<int64_t> trace_ids(k); std::vector<float> trace_distances(k);
                            const bool regional = method == Method::geom_uniform || method == Method::geom_probability || method == Method::oracle_probability;
                            const auto stats = rg::search<true>(*index->acsg.final_graph, *w.distance,
                                want_model ? model.labels.data() : nullptr, want_model ? model.regions : 1,
                                route, l, k, regional, method == Method::geom_uniform, w.search,
                                trace_ids.data(), trace_distances.data(), &events);
                            if (!std::equal(trace_ids.begin(), trace_ids.end(), ids.begin() + q * k) || stats.ndc != rows[q].stats.ndc)
                                throw std::runtime_error("trace replay result/count mismatch");
                            // Event-to-GT association occurs only after search returns.
                            json event_rows = json::array();
                            for (const auto& event : events) {
                                bool gt10 = false;
                                for (int j = 0; j < 10; ++j) gt10 |= event.id == gt[static_cast<size_t>(begin + q) * gt_k + j];
                                const std::array<const char*, 5> event_names = {"discover", "accept", "reject", "evict", "expand"};
                                event_rows.push_back({{"kind", event_names[static_cast<int>(event.kind)]}, {"id", event.id}, {"parent", event.parent},
                                    {"queue", event.queue}, {"distance", event.distance}, {"expanded", event.expanded}, {"is_gt10", gt10}});
                            }
                            const auto filename = "trace_L" + std::to_string(l) + "_" + names[mi] + "_q" + std::to_string(begin + q) + ".json";
                            write_new(parts + "/" + filename, {{"query_id", begin + q}, {"method", names[mi]}, {"L", l}, {"events", event_rows}, {"result_ids", trace_ids},
                                {"ndc", stats.ndc}, {"gt_associated_after_search", true}, {"timing_publishable", false}});
                            result["trace_files"].push_back(filename);
                        }
                    }
                    const auto chunk = "batch_" + std::to_string(completed_batches) + ".json";
                    write_new(parts + "/" + chunk, result);
                    output["results"].push_back(std::move(result));
                    ++completed_batches;
                    write_new(parts + "/checkpoint_" + std::to_string(completed_batches) + ".json", {{"status", "INCOMPLETE"}, {"completed_batches", completed_batches}, {"total_batches", schedule.size()}, {"last_chunk", chunk}});
                    std::cout << "HIERARCHICAL_BATCH method=" << names[mi] << " L=" << l << " round=" << r << " measurement=" << measurement << " recall=" << sum_recall / nq << " wall_us=" << wall_us << '\n';
                }
            }
        }
        // Separate routing-only wall is explanatory; never add it to a graph mean for QPS.
        if (!count) {
            output["routing_only"] = json::array();
            for (size_t mi = 0; mi < methods.size(); ++mi) {
                const double us = batch(methods[mi], ls.front(), nq, true);
                output["routing_only"].push_back({{"method", names[mi]}, {"batch_wall_us", us}, {"num_queries", nq}});
            }
        }
        rusage usage{}; getrusage(RUSAGE_SELF, &usage);
        output["peak_rss_kib"] = usage.ru_maxrss; output["index_bytes"] = std::filesystem::file_size(str("--index-file"));
        output["status"] = "COMPLETE"; write_new(output_path, output);
        write_new(parts + "/complete.json", {{"status", "COMPLETE"}, {"final_output", output_path}, {"completed_batches", completed_batches}});
        std::cout << "HIERARCHICAL_EVAL_COMPLETE output=" << output_path << '\n';
        return 0;
    } catch (const std::exception& e) { std::cerr << "ERROR: " << e.what() << '\n'; return 2; }
}

// P3 CPU-only fit-suffix portal probes. No DataLoader, Fast router or online GT API.
#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <csignal>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <mutex>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
#include <fcntl.h>
#include <sys/resource.h>
#include <unistd.h>
#include <omp.h>
#include <argparse/argparse.hpp>
#include <nlohmann/json.hpp>
#include <ACSG/IndexACSG.h>
#include <ACSG/RegionalSearch.h>

using json = nlohmann::json;
using Clock = std::chrono::steady_clock;
namespace fs = std::filesystem;
namespace rg = acsg::regional;
namespace {
constexpr int leaf_count = 256, fit_count = 20000, fit_begin = 10000;
constexpr int probe_k = 10, probe_l = 32, query_limit = 128, candidate_limit = 8;
constexpr int selection_seed = 2026090711;
constexpr std::time_t soft_deadline = 1788821940; // 2026-09-07T22:59:00Z
volatile std::sig_atomic_t stopping = 0;
void stop_handler(int) { stopping = 1; }
bool stop_now() { return stopping || std::time(nullptr) >= soft_deadline; }
void checkpoint() {
    if (stop_now()) throw std::runtime_error("termination or research soft deadline; INCOMPLETE");
}
void require(bool ok, const std::string& reason) { if (!ok) throw std::runtime_error(reason); }
double elapsed(Clock::time_point t) { return std::chrono::duration<double>(Clock::now() - t).count(); }
long peak_rss_kib() { rusage r{}; getrusage(RUSAGE_SELF, &r); return r.ru_maxrss; }

// Same self-contained SHA256 algorithm as the audited P2 partition helper.
std::string sha256_bytes(const void* data, size_t bytes) {
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
    const auto* input=static_cast<const uint8_t*>(data);
    const size_t total=(bytes+9+63)/64*64;
    const uint64_t bits=static_cast<uint64_t>(bytes)*8;
    for(size_t off=0;off<total;off+=64){uint32_t w[64]{};
        for(size_t j=0;j<64;++j){const size_t at=off+j;uint8_t b=at<bytes?input[at]:at==bytes?0x80:0;
            if(at>=total-8)b=static_cast<uint8_t>(bits>>(8*(total-1-at)));
            w[j/4]|=uint32_t(b)<<(24-8*(j%4));}
        for(int j=16;j<64;++j){const uint32_t s0=rr(w[j-15],7)^rr(w[j-15],18)^(w[j-15]>>3),s1=rr(w[j-2],17)^rr(w[j-2],19)^(w[j-2]>>10);w[j]=w[j-16]+s0+w[j-7]+s1;}
        uint32_t a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],v=h[7];
        for(int j=0;j<64;++j){const uint32_t t1=v+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^(~e&g))+k[j]+w[j];
            const uint32_t t2=(rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c));v=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;}
        h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=v;
    }
    constexpr char hex[]="0123456789abcdef";std::string out;out.reserve(64);
    for(auto word:h)for(int shift=28;shift>=0;shift-=4)out+=hex[(word>>shift)&15];
    return out;
}
bool valid_sha(const std::string& s) {
    return s.size() == 64 && std::all_of(s.begin(), s.end(), [](char c) { return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'); });
}
std::string hash_text(const std::string& s) { return sha256_bytes(s.data(), s.size()); }
fs::path input_path(const json& descriptor, const fs::path& plan_parent) {
    fs::path p = descriptor.at("path").get<std::string>();
    return fs::weakly_canonical(p.is_absolute() ? p : plan_parent / p);
}
std::vector<char> read_bytes(const fs::path& p) {
    std::ifstream f(p, std::ios::binary | std::ios::ate);
    require(bool(f), "cannot open " + p.string());
    const auto end = f.tellg(); require(end >= 0, "cannot size " + p.string());
    std::vector<char> b(static_cast<size_t>(end)); f.seekg(0);
    if (!b.empty()) f.read(b.data(), static_cast<std::streamsize>(b.size()));
    require(bool(f), "short read " + p.string()); return b;
}
std::string hash_file(const fs::path& p) { const auto b = read_bytes(p); return sha256_bytes(b.data(), b.size()); }
json read_bound_json(const json& desc, const fs::path& parent) {
    const auto bytes = read_bytes(input_path(desc, parent));
    require(valid_sha(desc.at("sha256")) && sha256_bytes(bytes.data(), bytes.size()) == desc.at("sha256"), "JSON checksum mismatch: " + desc.at("path").get<std::string>());
    return json::parse(bytes.begin(), bytes.end());
}
template<class T> std::vector<T> read_raw(const json& desc, const fs::path& parent, size_t count) {
    const auto p = input_path(desc, parent);
    require(fs::file_size(p) == count * sizeof(T), "raw shape mismatch: " + p.string());
    std::vector<T> values(count); std::ifstream f(p, std::ios::binary);
    if (count) f.read(reinterpret_cast<char*>(values.data()), static_cast<std::streamsize>(count * sizeof(T)));
    require(bool(f), "short raw read: " + p.string());
    require(valid_sha(desc.at("sha256")) && sha256_bytes(values.data(), count * sizeof(T)) == desc.at("sha256"), "raw checksum mismatch: " + p.string());
    return values;
}
void write_new(const fs::path& p, const void* data, size_t bytes) {
    const int fd = ::open(p.c_str(), O_WRONLY | O_CREAT | O_EXCL, 0644);
    require(fd >= 0, "cannot exclusively create " + p.string());
    const auto* b = static_cast<const char*>(data); size_t pos = 0;
    while (pos < bytes) {
        const auto n = ::write(fd, b + pos, bytes - pos);
        if (n <= 0) { ::close(fd); throw std::runtime_error("write failed; partial file retained: " + p.string()); }
        pos += static_cast<size_t>(n);
    }
    const int sync_result = ::fsync(fd), close_result = ::close(fd);
    require(sync_result == 0 && close_result == 0, "flush failed; retained " + p.string());
}
void write_json(const fs::path& p, const json& j) { const auto s = j.dump(2) + "\n"; write_new(p, s.data(), s.size()); }
template<class T> json write_raw(const fs::path& p, const std::vector<T>& values) {
    write_new(p, values.data(), values.size() * sizeof(T));
    return {{"path", fs::absolute(p).string()}, {"bytes", values.size() * sizeof(T)}, {"sha256", sha256_bytes(values.data(), values.size() * sizeof(T))}};
}
struct LeafPlan { std::vector<int32_t> candidates; std::vector<int> query_ids; };

// Plan generation is fit-only offline work. No query/GT/region reaches the search API.
std::vector<LeafPlan> rebuild_plan(const std::string& dataset, const std::vector<uint16_t>& labels,
                                  const std::vector<int32_t>& gt, int nq, int begin, int regions) {
    require(gt.size() == static_cast<size_t>(nq) * probe_k, "GT10 shape mismatch");
    std::vector<LeafPlan> out(regions);
    std::vector<std::vector<int32_t>> smallest(regions);
    std::vector<size_t> sizes(regions, 0);
    for (size_t id = 0; id < labels.size(); ++id) {
        const int r = labels[id]; require(r < regions, "node leaf outside map"); ++sizes[r];
        if (smallest[r].size() < candidate_limit) smallest[r].push_back(static_cast<int32_t>(id));
    }
    for (int r = 0; r < regions; ++r) require(sizes[r] >= 3, "leaf contains fewer than three nodes");
    std::vector<int32_t> targets = gt;
    std::vector<std::vector<std::pair<std::string, int>>> eligible(regions);
    for (int q = 0; q < nq; ++q) {
        const auto* row = gt.data() + q * probe_k;
        std::array<int, probe_k> leaves{};
        for (int j = 0; j < probe_k; ++j) {
            require(row[j] >= 0 && static_cast<size_t>(row[j]) < labels.size(), "GT ID outside base");
            for (int i = 0; i < j; ++i) require(row[i] != row[j], "duplicate GT10 ID");
            leaves[j] = labels[row[j]];
        }
        std::sort(leaves.begin(), leaves.end());
        const auto last_leaf = std::unique(leaves.begin(), leaves.end());
        for (auto it = leaves.begin(); it != last_leaf; ++it) {
            const int r = *it, global = begin + q;
            const auto key = dataset + "|" + std::to_string(selection_seed) + "|" + std::to_string(global) + "|" + std::to_string(r);
            eligible[r].emplace_back(hash_text(key), global);
        }
    }
    std::sort(targets.begin(), targets.end());
    std::vector<std::vector<std::pair<int, int32_t>>> frequencies(regions);
    for (size_t i = 0; i < targets.size();) {
        size_t j = i + 1; while (j < targets.size() && targets[j] == targets[i]) ++j;
        frequencies[labels[targets[i]]].emplace_back(-static_cast<int>(j - i), targets[i]); i = j;
    }
    for (int r = 0; r < regions; ++r) {
        std::sort(frequencies[r].begin(), frequencies[r].end());
        for (const auto& x : frequencies[r]) {
            if (out[r].candidates.size() == candidate_limit) break;
            out[r].candidates.push_back(x.second);
        }
        for (const auto id : smallest[r]) {
            if (out[r].candidates.size() == candidate_limit) break;
            if (std::find(out[r].candidates.begin(), out[r].candidates.end(), id) == out[r].candidates.end()) out[r].candidates.push_back(id);
        }
        std::sort(eligible[r].begin(), eligible[r].end());
        for (const auto& x : eligible[r]) {
            if (out[r].query_ids.size() == query_limit) break;
            out[r].query_ids.push_back(x.second);
        }
    }
    return out;
}
void validate_plan_rows(const json& rows, const std::vector<LeafPlan>& expected) {
    require(rows.is_array() && rows.size() == expected.size(), "plan must contain every leaf once");
    for (size_t r = 0; r < expected.size(); ++r) {
        require(rows[r].at("region") == r, "leaf plan order/coverage mismatch");
        require(rows[r].at("candidate_ids") == expected[r].candidates, "frequency candidate rule mismatch at leaf " + std::to_string(r));
        require(rows[r].at("query_ids") == expected[r].query_ids, "fit-query sampling/order mismatch at leaf " + std::to_string(r));
    }
}

// This boundary deliberately cannot receive GT, labels, a default seed or a router.
template<bool Count, class Graph, class Distance>
rg::Stats single_portal(const Graph& graph, Distance& distance, int32_t portal,
                        rg::Workspace& work, int64_t* ids, float* distances) {
    rg::Route route; route.shared_seed = -1; route.entry_count = 1; route.entries[0] = portal;
    return rg::search<Count>(graph, distance, nullptr, 1, route, probe_l, probe_k, false, false, work, ids, distances);
}
uint16_t score_mask(const int64_t* result, const int32_t* gt, const uint16_t* labels, int leaf) {
    uint16_t mask = 0;
    for (int j = 0; j < probe_k; ++j) if (labels[gt[j]] == leaf)
        for (int i = 0; i < probe_k; ++i) if (result[i] == gt[j]) { mask |= uint16_t(1u << j); break; }
    return mask;
}
struct Greedy { std::array<int32_t, 3> portals{}; std::array<uint64_t, 3> gains{}; uint64_t hits = 0; };
Greedy choose_greedy(const LeafPlan& plan, const std::vector<uint16_t>& masks) {
    require(plan.candidates.size() >= 3 && plan.candidates.size() <= candidate_limit, "greedy candidate count invalid");
    const size_t nq = plan.query_ids.size();
    require(masks.size() == plan.candidates.size() * nq, "candidate-major mask shape mismatch");
    for (const auto mask : masks) require(mask < (1 << probe_k), "non-GT10 bits in mask");
    Greedy out;
    if (nq == 0) { std::copy_n(plan.candidates.begin(), 3, out.portals.begin()); return out; }
    std::vector<uint16_t> covered(nq, 0); std::array<bool, candidate_limit> used{};
    for (int step = 0; step < 3; ++step) {
        int best = -1; uint64_t gain = 0;
        for (size_t c = 0; c < plan.candidates.size(); ++c) if (!used[c]) {
            uint64_t value = 0;
            for (size_t q = 0; q < nq; ++q) value += __builtin_popcount(static_cast<unsigned>(masks[c * nq + q] & ~covered[q]));
            if (best < 0 || value > gain || (value == gain && plan.candidates[c] < plan.candidates[best])) { best = static_cast<int>(c); gain = value; }
        }
        used[best] = true; out.portals[step] = plan.candidates[best]; out.gains[step] = gain; out.hits += gain;
        for (size_t q = 0; q < nq; ++q) covered[q] |= masks[static_cast<size_t>(best) * nq + q];
    }
    return out;
}
uint64_t frequency_hits(const LeafPlan& plan, const std::vector<uint16_t>& masks) {
    uint64_t hits = 0; const size_t nq = plan.query_ids.size();
    for (size_t q = 0; q < nq; ++q) hits += __builtin_popcount(static_cast<unsigned>(masks[q] | masks[nq + q] | masks[2 * nq + q]));
    return hits;
}
struct Work {
    rg::Workspace search;
    std::unique_ptr<faiss::DistanceComputer> distance;
    std::array<int64_t, probe_k> ids{};
    std::array<float, probe_k> distances{};
    explicit Work(acsg::IndexACSGFlat& index) : search(index.ntotal, probe_l, probe_k), distance(acsg::storage_distance_computer(index.storage)) {}
};
struct PairResult { uint64_t ndc = 0, expanded = 0; double probe_s = 0, score_s = 0; };

void self_test();
} // namespace

int main(int argc, char** argv) {
    argparse::ArgumentParser cli("bench_hierarchical_portals");
    cli.add_description("P3 fit-only CPU single-portal K10/L32 probes and cached greedy3; offline costs only.");
    cli.add_argument("--plan").default_value(std::string());
    cli.add_argument("--output").default_value(std::string());
    cli.add_argument("--threads").default_value(16).scan<'i', int>();
    cli.add_argument("--self-test").default_value(false).implicit_value(true);
    fs::path output;
    const auto started = Clock::now();
    bool output_created = false;
    int complete_leaves = 0;
    uint64_t completed_calls = 0, total_ndc = 0, total_expanded = 0;
    json summary;
    try {
        cli.parse_args(argc, argv);
        if (cli.get<bool>("--self-test")) {
            require(cli.get<std::string>("--plan").empty() && cli.get<std::string>("--output").empty(), "self-test cannot consume real inputs");
            self_test(); return 0;
        }
        const auto plan_name = cli.get<std::string>("--plan"), output_name = cli.get<std::string>("--output");
        require(!plan_name.empty() && !output_name.empty(), "--plan and --output are required");
        require(cli.get<int>("--threads") == 16, "P3 preregistered production thread count is 16");
        const uint16_t endian = 1; require(*reinterpret_cast<const uint8_t*>(&endian) == 1, "little-endian inputs required");
        std::signal(SIGINT, stop_handler); std::signal(SIGTERM, stop_handler); std::signal(SIGHUP, stop_handler); checkpoint();
        output = fs::absolute(output_name);
        if (!output.parent_path().empty()) fs::create_directories(output.parent_path());
        require(fs::create_directory(output), "refusing existing output directory"); output_created = true;
        write_json(output / "started.json", {{"status", "INCOMPLETE"}, {"stage", "P3_PORTAL_PROBES"}, {"pid", getpid()}, {"cpu_only", true}, {"plan", fs::absolute(plan_name).string()}});
        const auto input_start = Clock::now();
        const auto plan_path = fs::absolute(plan_name), parent = plan_path.parent_path();
        const auto plan_bytes = read_bytes(plan_path); const auto plan_sha = sha256_bytes(plan_bytes.data(), plan_bytes.size());
        const auto plan = json::parse(plan_bytes.begin(), plan_bytes.end());
        const std::string dataset = plan.at("dataset");
        require(plan.at("schema_version") == 1 && (dataset == "webvid2_5m_light_v1" || dataset == "yandex_t2i_official10M_ip_v1"), "unsupported plan schema/dataset");
        require(plan.at("fit_range") == json::array({fit_begin, fit_begin + fit_count}) && plan.at("fit_count") == fit_count && plan.at("region_count") == leaf_count && plan.at("seed") == selection_seed, "fixed fit/leaf/seed contract mismatch");
        const int lambda = plan.at("structure_lambda"); require(lambda == 0 || lambda == 1, "structure lambda must be 0 or 1");
        const int d = plan.at("dim"); const int64_t n = plan.at("n_base");
        require(d > 0 && d <= 65536 && n >= 3 * leaf_count && n <= std::numeric_limits<int32_t>::max(), "invalid declared dimensions");
        const auto protocol = read_bound_json(plan.at("protocol"), parent);
        require(protocol.at("stage") == "P3" && protocol.at("fit_range") == plan.at("fit_range") && protocol.at("cpu_only") == true && protocol.at("validation_heldout_allowed") == false, "P3 protocol boundary mismatch");
        const auto& portal_protocol = protocol.at("portals");
        require(portal_protocol.at("per_leaf") == 3 && portal_protocol.at("candidate_limit") == candidate_limit && portal_protocol.at("query_limit_per_leaf") == query_limit && portal_protocol.at("query_selection_seed") == selection_seed, "P3 portal constants mismatch");
        require(protocol.at("resources").at("softclose_utc") == "2026-09-07T22:59:00Z", "soft deadline mismatch");
        const auto gate = read_bound_json(plan.at("gate"), parent);
        require(gate.at("stage") == "P2" && gate.at("status") == "PASS" && gate.at("decision") == "GO_P3_STRUCTURE_DIAGNOSTIC_ONLY", "P2 limited P3 gate required");
        require(plan.at("gate").at("sha256") == protocol.at("upstream_P2").at("sha256"), "gate differs from preregistered P2 gate");
        const auto audit = read_bound_json(plan.at("audit"), parent);
        require(audit.at("status") == "PASS_INPUT_CONTRACT", "P0 input audit required");
        json audited;
        for (const auto& item : audit.at("datasets")) if (item.at("dataset") == dataset) audited = item;
        require(!audited.is_null(), "dataset absent from P0 audit");
        const auto& audited_graph = audited.at("graph");
        const auto index_path = input_path(plan.at("index"), parent);
        require(index_path == fs::weakly_canonical(audited_graph.at("path").get<std::string>()) && plan.at("index").at("sha256") == audited_graph.at("sha256") && valid_sha(plan.at("index").at("sha256")), "index not bound to audited frozen graph");
        require(fs::file_size(index_path) == plan.at("index").at("bytes").get<uint64_t>() && plan.at("index").at("bytes") == audited_graph.at("header").at("bytes") && n == audited_graph.at("header").at("n") && d == audited_graph.at("header").at("d"), "index size or shape differs from audit");
        const auto fit_manifest = read_bound_json(plan.at("fit_manifest"), parent);
        require(fit_manifest.at("status") == "COMPLETE" && fit_manifest.at("stage") == "P3" && fit_manifest.at("dataset") == dataset &&
                fit_manifest.at("fit_range") == plan.at("fit_range") && fit_manifest.at("fit_count") == fit_count &&
                fit_manifest.at("cpu_only") == true && fit_manifest.at("pilot_accessed") == false &&
                fit_manifest.at("validation_accessed") == false && fit_manifest.at("heldout_accessed") == false,
                "fit manifest violates P3 suffix isolation");
        require(fit_manifest.at("input_audit_sha256") == plan.at("audit").at("sha256") &&
                fit_manifest.at("protocol_sha256") == plan.at("protocol").at("sha256") &&
                fit_manifest.at("base_nodes") == n && fit_manifest.at("dim") == d &&
                fit_manifest.at("fit_gt_values_sha256") == audited.at("fit").at("gt_values_sha256"), "fit provenance differs from audited input");
        require(input_path(plan.at("queries"), parent) == fs::weakly_canonical(fit_manifest.at("queries_file").get<std::string>()) &&
                input_path(plan.at("gt10"), parent) == fs::weakly_canonical(fit_manifest.at("gt10_file").get<std::string>()) &&
                plan.at("queries").at("sha256") == fit_manifest.at("queries_sha256") &&
                plan.at("gt10").at("sha256") == fit_manifest.at("gt10_sha256"), "raw fit inputs differ from extraction manifest");
        const auto partition = read_bound_json(plan.at("partition_manifest"), parent);
        require(partition.at("status") == "COMPLETE" && partition.at("stage") == "P3" && partition.at("dataset") == dataset &&
                partition.at("lambda") == lambda && partition.at("regions") == leaf_count && partition.at("coarse_count") == 16 &&
                partition.at("leaves_per_coarse") == 16 && partition.at("nodes") == n &&
                partition.at("protocol_sha256") == plan.at("protocol").at("sha256") && partition.at("input_audit_sha256") == plan.at("audit").at("sha256") &&
                partition.at("fit_manifest_sha256") == plan.at("fit_manifest").at("sha256") &&
                partition.at("fit_gt_values_sha256") == audited.at("fit").at("gt_values_sha256"), "partition branch provenance mismatch");
        require(input_path(plan.at("labels"), parent) == fs::weakly_canonical(partition.at("labels_file").get<std::string>()) &&
                plan.at("labels").at("sha256") == partition.at("labels_sha256"), "leaf labels differ from completed partition");
        require(plan.at("queries").at("sha256") == audited.at("fit").at("query_values_sha256"), "fit query SHA differs from audited suffix");
        require(plan.at("source_binding").is_array() && plan.at("source_binding").size() >= 4, "source/build/running-binary bindings required");
        const auto binary_path = fs::read_symlink("/proc/self/exe"); const auto binary_sha = hash_file(binary_path);
        bool own_source = false, kernel_source = false, running_binary = false;
        for (const auto& bound : plan.at("source_binding")) {
            const auto p = input_path(bound, parent);
            require(valid_sha(bound.at("sha256")) && hash_file(p) == bound.at("sha256"), "source/build checksum mismatch: " + p.string());
            own_source |= p.filename() == "bench_hierarchical_portals.cpp";
            kernel_source |= p.filename() == "RegionalSearch.h";
            running_binary |= fs::equivalent(p, "/proc/self/exe") && bound.at("sha256") == binary_sha;
        }
        require(own_source && kernel_source && running_binary, "prober/kernel sources and currently running binary must all be bound");
        auto queries = read_raw<float>(plan.at("queries"), parent, static_cast<size_t>(fit_count) * d);
        auto gt = read_raw<int32_t>(plan.at("gt10"), parent, static_cast<size_t>(fit_count) * probe_k);
        auto labels = read_raw<uint16_t>(plan.at("labels"), parent, static_cast<size_t>(n));
        for (const auto value : queries) require(std::isfinite(value), "nonfinite fit query");
        const double input_s = elapsed(input_start); checkpoint();
        const auto selection_start = Clock::now();
        const auto leaves = rebuild_plan(dataset, labels, gt, fit_count, fit_begin, leaf_count);
        validate_plan_rows(plan.at("regions"), leaves);
        std::array<int64_t, leaf_count> leaf_sizes{}; std::array<int64_t, 16> coarse_sizes{};
        for (const auto label : labels) { ++leaf_sizes[label]; ++coarse_sizes[label / 16]; }
        for (const auto size : leaf_sizes) require(size >= 3 && size <= 6 * n / (5 * leaf_count), "leaf hard capacity failed");
        for (const auto size : coarse_sizes) require(size <= 6 * n / (5 * 16), "coarse hard capacity failed");
        uint64_t planned_calls = 0; for (const auto& leaf : leaves) planned_calls += leaf.candidates.size() * leaf.query_ids.size();
        require(planned_calls <= 262144, "probe limit exceeded");
        const double selection_s = elapsed(selection_start); checkpoint();
        const auto index_start = Clock::now();
        auto index = std::make_unique<acsg::IndexACSGFlat>(); index->loadACPG(index_path.c_str());
        std::vector<float>().swap(index->acsg.pheromone); std::vector<float>().swap(index->acsg.weight);
        require(index->ntotal == n && index->d == d && index->metric_type == faiss::METRIC_INNER_PRODUCT && index->acsg.final_graph && index->acsg.final_graph->N == n && index->acsg.final_graph->K == audited_graph.at("header").at("degree"), "loaded frozen index mismatch");
        const double index_s = elapsed(index_start); checkpoint();
        const auto allocation_start = Clock::now();
        omp_set_dynamic(0); omp_set_num_threads(16);
        std::vector<std::unique_ptr<Work>> work; for (int t = 0; t < 16; ++t) work.push_back(std::make_unique<Work>(*index));
        const double allocation_s = elapsed(allocation_start);
        summary = {{"schema_version", 1}, {"status", "INCOMPLETE"}, {"stage", "P3_PORTAL_PROBES"}, {"dataset", dataset}, {"structure_lambda", lambda},
            {"plan", fs::absolute(plan_path).string()}, {"plan_sha256", plan_sha}, {"protocol", plan.at("protocol")}, {"fit_manifest", plan.at("fit_manifest")}, {"partition_manifest", plan.at("partition_manifest")}, {"audit", plan.at("audit")}, {"gate", plan.at("gate")},
            {"source_binding", plan.at("source_binding")}, {"binary", {{"path", binary_path.string()}, {"sha256", binary_sha}}},
            {"inputs", {{"queries", plan.at("queries")}, {"gt10", plan.at("gt10")}, {"labels", plan.at("labels")}, {"index", plan.at("index")}}},
            {"index_checksum_verification", "Inherited full P0 SHA256; this program verified bound path, current bytes and loaded shape, without a repeated full index hash"},
            {"fit_range", plan.at("fit_range")}, {"fit_count", fit_count}, {"threads", 16}, {"cpu_only", true}, {"pilot_accessed", false}, {"validation_accessed", false}, {"heldout_accessed", false},
            {"search_contract", {{"K", probe_k}, {"L", probe_l}, {"single_portal", true}, {"default_seed", false}, {"Fast", false}, {"GT_argument", false}, {"raw_query_IP", true}, {"score_after_search", true}}},
            {"mask_layout", "little-endian uint16, candidate-major, query-contiguous; bits follow saved GT10 order and are restricted to target leaf"},
            {"planned_calls", planned_calls}, {"cost_seconds", {{"upstream", plan.at("upstream_cost_seconds")}, {"input_read_hash_validation", input_s}, {"independent_candidate_query_verification", selection_s}, {"index_load", index_s}, {"workspace_allocation", allocation_s}}},
            {"exact_GT_cost_seconds", nullptr}, {"exact_GT_cost_reason", "Previously computed GT reused; original computation cost is not reconstructed"}, {"online_QPS_publishable", false}, {"regions", json::array()}};
        write_json(output / "validated.json", summary);
        std::vector<int32_t> frequency_portals, greedy_portals;
        frequency_portals.reserve(3 * leaf_count); greedy_portals.reserve(3 * leaf_count);
        double batch_wall_s = 0, probe_thread_s = 0, score_thread_s = 0, greedy_wall_s = 0, write_wall_s = 0;
        for (int r = 0; r < leaf_count; ++r) {
            checkpoint(); const auto& leaf = leaves[r]; const size_t nq = leaf.query_ids.size(), count = nq * leaf.candidates.size();
            std::vector<uint16_t> masks(count, 0); std::vector<uint8_t> completed(count, 0); std::vector<PairResult> costs(count);
            std::atomic<bool> failed{false}; std::mutex error_mutex; std::string error;
            const auto batch_start = Clock::now();
            #pragma omp parallel for schedule(static)
            for (int64_t pair = 0; pair < static_cast<int64_t>(count); ++pair) {
                if (stop_now() || failed.load()) continue;
                try {
                    const size_t c = static_cast<size_t>(pair) / nq, q = static_cast<size_t>(pair) % nq;
                    const int row = leaf.query_ids[q] - fit_begin;
                    auto& w = *work[omp_get_thread_num()];
                    w.distance->set_query(queries.data() + static_cast<size_t>(row) * d);
                    const auto t = Clock::now();
                    const auto stats = single_portal<true>(*index->acsg.final_graph, *w.distance, leaf.candidates[c], w.search, w.ids.data(), w.distances.data());
                    costs[pair].probe_s = elapsed(t); costs[pair].ndc = stats.ndc; costs[pair].expanded = stats.expanded;
                    const auto s = Clock::now();
                    masks[pair] = score_mask(w.ids.data(), gt.data() + static_cast<size_t>(row) * probe_k, labels.data(), r);
                    costs[pair].score_s = elapsed(s); completed[pair] = 1;
                } catch (const std::exception& e) {
                    failed.store(true); std::lock_guard<std::mutex> lock(error_mutex); if (error.empty()) error = e.what();
                }
            }
            const double region_batch_s = elapsed(batch_start); batch_wall_s += region_batch_s;
            uint64_t calls = 0, ndc = 0, expanded = 0; double probe_s = 0, score_s = 0;
            for (size_t i = 0; i < count; ++i) if (completed[i]) { ++calls; ndc += costs[i].ndc; expanded += costs[i].expanded; probe_s += costs[i].probe_s; score_s += costs[i].score_s; }
            completed_calls += calls; total_ndc += ndc; total_expanded += expanded; probe_thread_s += probe_s; score_thread_s += score_s;
            const bool complete = calls == count && !failed.load() && !stop_now();
            char stem[32]; std::snprintf(stem, sizeof(stem), "leaf_%03d", r);
            const std::string suffix = complete ? "" : ".partial";
            const auto write_start = Clock::now();
            const auto mask_info = write_raw(output / (std::string(stem) + suffix + ".masks.u16"), masks);
            json gt_rows = json::array();
            for (const auto qid : leaf.query_ids) { const auto* row = gt.data() + static_cast<size_t>(qid - fit_begin) * probe_k; gt_rows.push_back(std::vector<int32_t>(row, row + probe_k)); }
            json region = {{"schema_version", 1}, {"status", complete ? "COMPLETE" : "INCOMPLETE"}, {"region", r}, {"plan_sha256", plan_sha}, {"binary_sha256", binary_sha},
                {"candidate_ids", leaf.candidates}, {"query_ids", leaf.query_ids}, {"GT10_order", gt_rows}, {"GT10_order_sha256", hash_text(gt_rows.dump())},
                {"mask_file", mask_info}, {"mask_shape", {leaf.candidates.size(), nq}}, {"mask_layout", "candidate-major/query-contiguous uint16 little-endian"},
                {"calls_planned", count}, {"calls_completed", calls}, {"ndc", ndc}, {"expanded", expanded},
                {"cost_seconds", {{"probe_and_score_batch_wall", region_batch_s}, {"probe_thread_seconds_sum", probe_s}, {"GT_score_thread_seconds_sum", score_s}}},
                {"no_fit_query_evidence", nq == 0}, {"error", error.empty() ? json(nullptr) : json(error)}};
            double region_greedy_s = 0;
            if (!complete) region["completed_bitmap"] = write_raw(output / (std::string(stem) + ".partial.completed.u8"), completed);
            else {
                const auto greedy_start = Clock::now(); const auto chosen = choose_greedy(leaf, masks); const auto freq_hits = frequency_hits(leaf, masks);
                const double greedy_s = elapsed(greedy_start); greedy_wall_s += greedy_s; region_greedy_s = greedy_s;
                region["frequency_portals"] = std::vector<int32_t>(leaf.candidates.begin(), leaf.candidates.begin() + 3);
                region["greedy_portals"] = chosen.portals; region["greedy_gains"] = chosen.gains; region["greedy_union_hits"] = chosen.hits; region["frequency_union_hits"] = freq_hits;
                region["cost_seconds"]["greedy_wall"] = greedy_s;
                frequency_portals.insert(frequency_portals.end(), leaf.candidates.begin(), leaf.candidates.begin() + 3);
                greedy_portals.insert(greedy_portals.end(), chosen.portals.begin(), chosen.portals.end());
            }
            region["cost_seconds"]["mask_and_binding_write_wall_before_checkpoint"] = elapsed(write_start) - region_greedy_s;
            const auto region_path = output / (std::string(stem) + suffix + ".json"); write_json(region_path, region);
            const double write_s = elapsed(write_start) - region_greedy_s; write_wall_s += write_s;
            summary["regions"].push_back({{"region", r}, {"status", region["status"]}, {"path", region_path.string()}, {"sha256", hash_file(region_path)}, {"checkpoint_write_wall", write_s}});
            std::cout << json({{"region", r}, {"status", region["status"]}, {"calls", calls}, {"cumulative_calls", completed_calls}, {"planned_calls", planned_calls}, {"batch_wall_seconds", region_batch_s}, {"ndc", ndc}, {"elapsed_seconds", elapsed(started)}, {"peak_rss_kib", peak_rss_kib()}}).dump() << std::endl;
            if (!complete) throw std::runtime_error(error.empty() ? "stopped in leaf; partial mask bitmap retained" : error);
            ++complete_leaves;
        }
        checkpoint();
        require(completed_calls == planned_calls && frequency_portals.size() == 768 && greedy_portals.size() == 768, "incomplete final portal coverage");
        const auto final_write_start = Clock::now();
        summary["frequency_portals"] = write_raw(output / "portals_frequency.i32", frequency_portals);
        summary["greedy_portals"] = write_raw(output / "portals_greedy.i32", greedy_portals);
        write_wall_s += elapsed(final_write_start);
        summary["status"] = "COMPLETE"; summary["complete_leaves"] = complete_leaves; summary["calls_completed"] = completed_calls;
        summary["ndc"] = total_ndc; summary["expanded"] = total_expanded; summary["graph_MAC"] = total_ndc * static_cast<uint64_t>(d);
        summary["cost_seconds"]["probe_and_score_batch_wall"] = batch_wall_s;
        summary["cost_seconds"]["probe_thread_seconds_sum"] = probe_thread_s;
        summary["cost_seconds"]["GT_score_thread_seconds_sum"] = score_thread_s;
        summary["cost_seconds"]["greedy_wall"] = greedy_wall_s;
        summary["cost_seconds"]["artifact_write_before_final_manifest"] = write_wall_s;
        summary["cost_seconds"]["program_wall_before_final_manifest"] = elapsed(started);
        summary["cost_interpretation"] = "Batch wall includes OpenMP scheduling, query setup, search, and post-search scoring. Probe/score sums are thread-seconds, not wall time. Whole-process wall including final manifest comes from external stage_run.";
        summary["peak_rss_kib"] = peak_rss_kib(); write_json(output / "complete.json", summary);
        std::cout << json({{"status", "COMPLETE"}, {"calls", completed_calls}, {"ndc", total_ndc}, {"output", output.string()}, {"elapsed_seconds", elapsed(started)}}).dump() << std::endl;
        return 0;
    } catch (const std::exception& e) {
        const std::string status = stop_now() ? "INCOMPLETE" : "FAILED";
        if (output_created) {
            summary["status"] = status; summary["error"] = e.what(); summary["complete_leaves"] = complete_leaves;
            summary["calls_completed"] = completed_calls; summary["ndc"] = total_ndc; summary["expanded"] = total_expanded;
            summary["program_wall_seconds"] = elapsed(started); summary["peak_rss_kib"] = peak_rss_kib();
            try { write_json(output / "stopped.json", summary); } catch (const std::exception& error) { std::cerr << error.what() << '\n'; }
        }
        std::cerr << json({{"status", status}, {"error", e.what()}}).dump() << '\n'; return stop_now() ? 130 : 1;
    }
}

namespace {
struct SyntheticDistance final : faiss::DistanceComputer {
    std::vector<float> values; uint64_t calls = 0;
    explicit SyntheticDistance(int n) : values(n) {}
    void set_query(const float*) override {}
    float operator()(faiss::idx_t id) override { ++calls; return values.at(id); }
    float symmetric_dis(faiss::idx_t, faiss::idx_t) override { return 0; }
};
template<class Fn> void rejects(Fn&& fn) {
    bool failed = false; try { fn(); } catch (const std::exception&) { failed = true; }
    require(failed, "negative self-test unexpectedly accepted");
}
void self_test() {
    require(hash_text("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" && hash_text("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "SHA256 known vectors failed");
    std::mt19937 rng(selection_seed);
    for (int trial = 0; trial < 300; ++trial) {
        constexpr int n = 64; acsg::ACSG old(8); old.ntotal = n; old.is_built = true; old.search_L = probe_l;
        old.final_graph = std::make_shared<acsg::Graph<int32_t>>(n, 8);
        for (int i = 0; i < n * 8; ++i) old.final_graph->data[i] = static_cast<int32_t>(rng() % n);
        SyntheticDistance a(n), b(n), c(n);
        for (int i = 0; i < n; ++i) a.values[i] = trial < 100 ? static_cast<float>(i) : trial < 200 ? static_cast<float>(i / 8) : 1.0f;
        std::shuffle(a.values.begin(), a.values.end(), rng); b.values = a.values; c.values = a.values;
        const int32_t portal = static_cast<int32_t>(rng() % n);
        std::vector<acsg::EnterPoint> entries; entries.emplace_back(portal, 1.0);
        faiss::VisitedTable visited(n); std::vector<acsg::Neighbor> buffer;
        std::array<int64_t, probe_k> legacy{}, counted{}, plain{}; std::array<float, probe_k> dl{}, dc{}, dp{};
        old.search_new(a, probe_k, legacy.data(), dl.data(), visited, 2, entries, &buffer);
        rg::Workspace work(n, probe_l, probe_k);
        const auto stats = single_portal<true>(*old.final_graph, b, portal, work, counted.data(), dc.data());
        single_portal<false>(*old.final_graph, c, portal, work, plain.data(), dp.data());
        require(legacy == counted && counted == plain && dl == dc && dc == dp && a.calls == stats.ndc && b.calls == stats.ndc && c.calls == stats.ndc, "single-portal legacy/count/plain parity failed");
    }
    // A disconnected graph must visit the portal alone, including when portal != 0.
    acsg::Graph<int32_t> isolated(16, 1); std::fill_n(isolated.data, 16, -1);
    SyntheticDistance distance(16); rg::Workspace work(16, probe_l, probe_k);
    std::array<int64_t, probe_k> ids{}; std::array<float, probe_k> ds{};
    const auto only = single_portal<true>(isolated, distance, 7, work, ids.data(), ds.data());
    require(only.ndc == 1 && only.expanded == 1 && ids[0] == 7 && ids[1] == -1, "implicit default seed or padding error");
    std::array<int32_t, probe_k> truth{{7, 2, 3, 4, 5, 6, 8, 9, 10, 11}};
    std::array<uint16_t, 16> labels{}; labels[7] = 1; labels[2] = 1;
    require(score_mask(ids.data(), truth.data(), labels.data(), 1) == 1 && score_mask(ids.data(), truth.data(), labels.data(), 0) == 0, "target-leaf result-mask boundary failed");
    ids[1] = 2; require(score_mask(ids.data(), truth.data(), labels.data(), 1) == 3, "GT bit order failed");
    LeafPlan leaf{{9, 2, 5, 7}, {10000, 10001}};
    std::vector<uint16_t> masks{1, 1, 2, 0, 3, 0, 0, 4};
    const auto greedy = choose_greedy(leaf, masks);
    require(greedy.portals == std::array<int32_t, 3>{{5, 7, 9}} && greedy.gains == std::array<uint64_t, 3>{{2, 1, 1}} && greedy.hits == 4 && frequency_hits(leaf, masks) == 3, "greedy marginal union/tie test failed");
    const auto zero = choose_greedy(leaf, std::vector<uint16_t>(8, 0));
    require(zero.portals == std::array<int32_t, 3>{{2, 5, 7}} && zero.hits == 0, "zero-gain ID tie must still fill three");
    leaf.query_ids.clear(); require(choose_greedy(leaf, {}).portals == std::array<int32_t, 3>{{9, 2, 5}}, "empty-fit fallback must preserve frequency order");
    std::vector<uint16_t> node_labels(24); for (int i = 0; i < 24; ++i) node_labels[i] = static_cast<uint16_t>(i / 8);
    std::vector<int32_t> gt(20); std::iota(gt.begin(), gt.begin() + 10, 0); std::iota(gt.begin() + 10, gt.end(), 2);
    const auto rebuilt = rebuild_plan("synthetic", node_labels, gt, 2, fit_begin, 3);
    require(rebuilt[0].candidates == std::vector<int32_t>({2, 3, 4, 5, 6, 7, 0, 1}) && rebuilt[2].candidates == std::vector<int32_t>({16, 17, 18, 19, 20, 21, 22, 23}) && rebuilt[2].query_ids.empty(), "frequency/fallback reconstruction failed");
    json rows = json::array(); for (int r = 0; r < 3; ++r) rows.push_back({{"region", r}, {"candidate_ids", rebuilt[r].candidates}, {"query_ids", rebuilt[r].query_ids}});
    validate_plan_rows(rows, rebuilt);
    auto wrong = rows; wrong[0]["query_ids"][0] = 0; rejects([&] { validate_plan_rows(wrong, rebuilt); });
    wrong = rows; std::swap(wrong[0]["candidate_ids"][0], wrong[0]["candidate_ids"][1]); rejects([&] { validate_plan_rows(wrong, rebuilt); });
    auto duplicate = gt; duplicate[1] = duplicate[0]; rejects([&] { rebuild_plan("synthetic", node_labels, duplicate, 2, fit_begin, 3); });
    duplicate = gt; duplicate[0] = 24; rejects([&] { rebuild_plan("synthetic", node_labels, duplicate, 2, fit_begin, 3); });
    std::cout << json({{"status", "PASS"}, {"self_test", "P3 portal kernel/GT boundary/greedy/suffix plan"}, {"legacy_count_plain_parity_queries", 300}, {"real_data_accessed", false}}).dump(2) << '\n';
}
} // namespace

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
#include <nlohmann/json.hpp>
#include <omp.h>
#include <ACSG/IndexACSG.h>
#include <hnswlib/hnswlib.h>

using json = nlohmann::json;
namespace fs = std::filesystem;
using Clock = std::chrono::steady_clock;
constexpr size_t K = 10;

namespace {
template<class T> std::vector<T> read_raw(const std::string& path) {
    std::ifstream f(path, std::ios::binary | std::ios::ate);
    if (!f) throw std::runtime_error("cannot open " + path);
    const auto pos = f.tellg();
    if (pos < 0 || static_cast<size_t>(pos) % sizeof(T)) throw std::runtime_error("invalid raw size: " + path);
    std::vector<T> data(static_cast<size_t>(pos) / sizeof(T));
    f.seekg(0); f.read(reinterpret_cast<char*>(data.data()), static_cast<std::streamsize>(data.size() * sizeof(T)));
    if (!f) throw std::runtime_error("read failed: " + path);
    return data;
}
template<class T> void write_raw(const fs::path& path, const std::vector<T>& data) {
    std::ofstream f(path, std::ios::binary);
    f.write(reinterpret_cast<const char*>(data.data()), data.size() * sizeof(T));
    if (!f) throw std::runtime_error("write failed: " + path.string());
}
void write_json(const fs::path& path, const json& j) {
    std::ofstream f(path); f << j.dump(2) << '\n';
    if (!f) throw std::runtime_error("write failed: " + path.string());
}
void require(bool ok, const std::string& message) { if (!ok) throw std::runtime_error(message); }
void finite_matrix(const std::vector<float>& x, const char* name) {
    for (float v : x) require(std::isfinite(v), std::string("nonfinite ") + name);
}
void normalize(float* v, size_t d) {
    double norm = 0;
    for (size_t j = 0; j < d; ++j) norm += static_cast<double>(v[j]) * v[j];
    require(norm > 0 && std::isfinite(norm), "zero/nonfinite normalization norm");
    const double inv = 1.0 / std::sqrt(norm);
    for (size_t j = 0; j < d; ++j) v[j] = static_cast<float>(v[j] * inv);
}
uint16_t hitmask(const std::array<int32_t,K>& ids, const int64_t* gt) {
    uint16_t mask = 0;
    for (int id : ids) if (id >= 0) for (size_t g = 0; g < K; ++g)
        if (id == gt[g]) { mask |= uint16_t(1) << g; break; }
    return mask;
}

thread_local uint64_t* route_counter = nullptr;
struct SpaceParam { hnswlib::DISTFUNC<float> fn; void* param; };
float counted_ip(const void* a, const void* b, const void* p) {
    if (route_counter) ++*route_counter;
    auto* param = static_cast<const SpaceParam*>(p);
    return param->fn(a, b, param->param);
}
class CountSpace final : public hnswlib::SpaceInterface<float> {
    hnswlib::InnerProductSpace inner;
    SpaceParam param;
public:
    explicit CountSpace(size_t d) : inner(d), param{inner.get_dist_func(), inner.get_dist_func_param()} {}
    size_t get_data_size() override { return inner.get_data_size(); }
    hnswlib::DISTFUNC<float> get_dist_func() override { return counted_ip; }
    void* get_dist_func_param() override { return &param; }
};
struct Route {
    std::array<int32_t,8> local{};
    std::array<float,8> distance{};
    uint32_t ndc = 0;
};
class Router {
    std::unique_ptr<hnswlib::SpaceInterface<float>> space;
    std::unique_ptr<hnswlib::HierarchicalNSW<float>> graph;
    std::unordered_map<int32_t,int32_t> local_by_id;
public:
    Router(size_t d, const std::vector<float>& proto, const std::vector<int32_t>& ids, size_t seed, bool counting) {
        if (counting) space = std::make_unique<CountSpace>(d);
        else space = std::make_unique<hnswlib::InnerProductSpace>(d);
        graph = std::make_unique<hnswlib::HierarchicalNSW<float>>(space.get(), ids.size(), 16, 200, seed);
        for (size_t h = 0; h < ids.size(); ++h) {
            graph->addPoint(proto.data() + h * d, ids[h]);
            local_by_id.emplace(ids[h], static_cast<int32_t>(h));
        }
        graph->setEf(10);
    }
    Route route(const float* q, size_t k = 8) const {
        uint64_t count = 0;
        route_counter = &count;
        auto heap = graph->searchKnn(q, k);
        route_counter = nullptr;
        require(heap.size() == k, "router returned fewer than k");
        Route result;
        result.local.fill(-1); result.distance.fill(std::numeric_limits<float>::quiet_NaN());
        for (size_t j = k; j-- > 0;) {
            result.local[j] = local_by_id.at(static_cast<int32_t>(heap.top().second));
            result.distance[j] = heap.top().first;
            heap.pop();
        }
        require(count <= UINT32_MAX, "routing NDC overflow"); result.ndc = static_cast<uint32_t>(count);
        return result;
    }
};
struct CountDC final : faiss::DistanceComputer {
    std::unique_ptr<faiss::DistanceComputer> inner;
    uint64_t count = 0;
    std::array<int32_t,3> first_ids{};
    explicit CountDC(faiss::DistanceComputer* p) : inner(p) {}
    void set_query(const float* q) override { inner->set_query(q); }
    float operator()(faiss::idx_t i) override {
        if (count < first_ids.size()) first_ids[count] = static_cast<int32_t>(i);
        ++count; return (*inner)(i);
    }
    float symmetric_dis(faiss::idx_t i, faiss::idx_t j) override { return inner->symmetric_dis(i,j); }
};
struct Search {
    std::array<int32_t,K> ids{};
    std::array<float,K> distances{};
    uint32_t ndc = 0;
};
struct Work {
    std::unique_ptr<faiss::DistanceComputer> dc;
    CountDC* counted = nullptr;
    faiss::VisitedTable visited;
    std::vector<acsg::Neighbor> retset;
    std::vector<acsg::EnterPoint> entries;
    Work(acsg::IndexACSGFlat& index, bool counting) : visited(index.ntotal) {
        if (counting) { counted = new CountDC(acsg::storage_distance_computer(index.storage)); dc.reset(counted); }
        else dc.reset(acsg::storage_distance_computer(index.storage));
        entries.reserve(3); retset.reserve(129);
    }
    // Intentionally GT-free. Uses the exact legacy shared-beam search kernel.
    Search run(acsg::IndexACSGFlat& index, const float* q, const std::vector<int32_t>& hubs,
               const std::array<int32_t,3>& local, size_t size) {
        entries.clear();
        for (size_t j = 0; j < size; ++j) entries.emplace_back(hubs[local[j]], 1.0);
        dc->set_query(q); if (counted) counted->count = 0; visited.advance();
        std::array<faiss::idx_t,K> ids;
        Search result;
        index.acsg.search_new(*dc, K, ids.data(), result.distances.data(), visited, 2, entries, &retset);
        for (size_t j = 0; j < K; ++j) result.ids[j] = static_cast<int32_t>(ids[j]);
        if (counted) {
            require(counted->count <= UINT32_MAX, "graph NDC overflow"); result.ndc = static_cast<uint32_t>(counted->count);
            require(counted->count >= size, "fewer distances than requested entries");
            for (size_t j=0;j<size;++j) require(counted->first_ids[j] == hubs[local[j]], "actual initial entry order/count mismatch");
        }
        return result;
    }
};

struct Variant { std::string name, source; std::array<int32_t,3> ranks; size_t size; };
std::vector<Variant> variants(bool seed100_search) {
    std::vector<Variant> v;
    for (auto source : {"fast", "exact"}) for (int k = 1; k <= 3; ++k)
        v.push_back({std::string(source) + "_top" + std::to_string(k), source, {0,1,2}, static_cast<size_t>(k)});
    for (int i = 0; i < 8; ++i) for (int j = i + 1; j < 8; ++j)
        v.push_back({"c8_pair_" + std::to_string(i) + "_" + std::to_string(j), "fast", {i,j,-1}, 2});
    for (int i = 0; i < 8; ++i) for (int j = i + 1; j < 8; ++j) for (int k = j + 1; k < 8; ++k)
        v.push_back({"c8_triple_" + std::to_string(i) + "_" + std::to_string(j) + "_" + std::to_string(k), "fast", {i,j,k}, 3});
    if (seed100_search) v.push_back({"seed100_top3", "seed100", {0,1,2}, 3});
    return v;
}
json variant_json(const std::vector<Variant>& variants_) {
    json out = json::array();
    for (size_t i = 0; i < variants_.size(); ++i) {
        const auto& v = variants_[i];
        out.push_back({{"column",i},{"name",v.name},{"route",v.source},{"route_ranks",v.ranks},{"entry_count",v.size}});
    }
    return out;
}
struct Output {
    std::ofstream count, mask, ndc, ids;
    Output(const fs::path& dir, const std::string& prefix) :
        count(dir / (prefix + ".hitcount.u8"), std::ios::binary),
        mask(dir / (prefix + ".hitmask.u16"), std::ios::binary),
        ndc(dir / (prefix + ".ndc.u32"), std::ios::binary),
        ids(dir / (prefix + ".ids.i32"), std::ios::binary) {}
    void append(const std::vector<Search>& rows, const std::vector<int64_t>& gt, size_t gt_k,
                size_t query_start, size_t columns) {
        for (size_t i = 0; i < rows.size(); ++i) {
            const auto& row = rows[i];
            uint16_t m = hitmask(row.ids, gt.data() + (query_start + i / columns) * gt_k);
            uint8_t c = static_cast<uint8_t>(__builtin_popcount(static_cast<unsigned>(m)));
            count.write(reinterpret_cast<const char*>(&c), sizeof(c));
            mask.write(reinterpret_cast<const char*>(&m), sizeof(m));
            ndc.write(reinterpret_cast<const char*>(&row.ndc), sizeof(row.ndc));
            ids.write(reinterpret_cast<const char*>(row.ids.data()), K * sizeof(int32_t));
        }
        count.flush(); mask.flush(); ndc.flush(); ids.flush();
        require(count && mask && ndc && ids, "incremental output write failed");
    }
};
json shape_schema(size_t n, size_t columns) {
    return {{"hitcount",{{"dtype","uint8"},{"shape",{n,columns}}}},
            {"hitmask",{{"dtype","uint16"},{"shape",{n,columns}},{"bit_g","exact GT rank g in [0,10) returned"}}},
            {"ndc",{{"dtype","uint32"},{"shape",{n,columns}}}},
            {"ids",{{"dtype","int32"},{"shape",{n,columns,K}}}}};
}

void self_test() {
    constexpr size_t n = 192, d = 8, degree = 12;
    acsg::IndexACSGFlat index(d, degree, faiss::METRIC_INNER_PRODUCT);
    std::vector<float> base(n * d);
    for (size_t i = 0; i < base.size(); ++i) base[i] = std::sin(float(i + 1) * .371f);
    index.storage->add(n, base.data()); index.ntotal = n; index.is_built = true;
    index.acsg.ntotal = n; index.acsg.is_built = true; index.acsg.enterpoint = 0;
    index.acsg.final_graph = std::make_shared<acsg::Graph<int32_t>>(n, degree);
    for (size_t i = 0; i < n; ++i) for (size_t j = 0; j < degree; ++j)
        index.acsg.final_graph->at(i,j) = (i + j * 13 + 1) % n;
    std::vector<int32_t> hubs(32); std::iota(hubs.begin(), hubs.end(), 0);
    std::vector<float> proto(base.begin(), base.begin() + hubs.size() * d);
    for (size_t h = 0; h < hubs.size(); ++h) normalize(proto.data() + h * d, d);
    Router counted(d,proto,hubs,20260828,true), plain(d,proto,hubs,20260828,false);
    Work wc(index,true), wp(index,false);
    size_t checks = 0;
    for (int l : {64,128}) {
        index.acsg.search_L = l;
        for (size_t q = 0; q < 24; ++q) {
            auto a = counted.route(base.data()+q*d), b = plain.route(base.data()+q*d);
            require(a.local == b.local && a.distance == b.distance && a.ndc > 0, "synthetic route parity failure");
            for (size_t k = 1; k <= 3; ++k) {
                auto ak = counted.route(base.data()+q*d,k);
                for(size_t j=0;j<k;++j) require(ak.local[j] == a.local[j], "route top8 prefix differs from top-k");
                std::array<int32_t,3> entries{a.local[0],a.local[1],a.local[2]};
                auto x = wc.run(index,base.data()+q*d,hubs,entries,k), y = wp.run(index,base.data()+q*d,hubs,entries,k);
                require(x.ids == y.ids && x.distances == y.distances && x.ndc >= k, "synthetic graph parity failure");
                ++checks;
            }
        }
    }
    std::cout << json({{"status","PASS"},{"kind","synthetic_only"},{"graph_plain_count_checks",checks},
                      {"router_plain_count_checks",48},{"kernel","ACSG::search_new mode=2"}}).dump() << std::endl;
}

int run(const json& c, const fs::path& output, size_t parity_queries, bool parity_only) {
    const auto started = Clock::now();
    const size_t d = c.at("dim").get<size_t>();
    require(d > 0, "dim must be positive");
    auto queries = read_raw<float>(c.at("queries_file"));
    auto gt = read_raw<int64_t>(c.at("gt_file"));
    auto row_ids = read_raw<int64_t>(c.at("row_ids"));
    auto hubs = read_raw<int32_t>(c.at("hub_ids"));
    auto raw_hubs = read_raw<float>(c.at("raw_hubs"));
    auto proto = read_raw<float>(c.at("prototypes"));
    const size_t n = row_ids.size(), h = hubs.size(), p = c.value("pilot_count",size_t(512)), gtk = c.value("gt_k",size_t(100));
    const auto ls = c.value("L",std::vector<int>{64,128});
    const int threads = c.value("threads",16);
    require(n > 0 && p <= n && h >= 8 && gtk >= K, "invalid query/pilot/hub/GT count");
    require(c.value("num_queries",n) == n && c.value("hub_count",h) == h, "configured count disagrees with files");
    require(c.value("K",10) == 10, "this diagnostic is fixed K=10");
    require(threads >= 1 && threads <= 16, "threads must be 1..16");
    require(!ls.empty(), "empty L list"); for (int l:ls) require(l >= 10, "L must be >= 10");
    require(std::set<int>(ls.begin(),ls.end()).size() == ls.size(), "duplicate L");
    require(queries.size() == n*d && gt.size() == n*gtk && raw_hubs.size() == h*d && proto.size() == h*d, "input matrix shape mismatch");
    require(std::set<int64_t>(row_ids.begin(),row_ids.end()).size() == n, "duplicate row IDs");
    require(std::set<int32_t>(hubs.begin(),hubs.end()).size() == h, "duplicate hub IDs");
    finite_matrix(queries,"query"); finite_matrix(raw_hubs,"raw hub"); finite_matrix(proto,"prototype");
    require(parity_queries <= n-p, "parity rows must come exclusively after pilot_count");
    omp_set_num_threads(threads);
    require(!fs::exists(output), "refusing existing output root: " + output.string());
    if (!output.parent_path().empty()) fs::create_directories(output.parent_path());
    require(fs::create_directory(output), "could not exclusively create output root");
    write_json(output/"config.json",c);
    write_raw(output/"row_ids.i64",row_ids); write_raw(output/"hub_ids.i32",hubs);
    std::ofstream progress(output/"progress.jsonl");
    auto log = [&](json j) {
        j["elapsed_instrumented_seconds"] = std::chrono::duration<double>(Clock::now()-started).count();
        progress << j.dump() << '\n'; progress.flush(); std::cout << j.dump() << std::endl;
    };
    log({{"stage","load_index"}});
    auto index = std::make_unique<acsg::IndexACSGFlat>(); index->loadACPG(c.at("index_path").get<std::string>().c_str());
    std::vector<float>().swap(index->acsg.pheromone); std::vector<float>().swap(index->acsg.weight);
    require(index->d == static_cast<int>(d) && index->metric_type == faiss::METRIC_INNER_PRODUCT, "index dim/metric mismatch");
    for (int32_t id:hubs) require(id >= 0 && id < index->ntotal, "hub outside frozen index");
    for (int64_t id:gt) require(id >= 0 && id < index->ntotal, "GT outside frozen index");
    log({{"stage","route"},{"queries",n},{"hubs",h}});
    Router fast(d,proto,hubs,20260828,true), old(d,proto,hubs,100,true);
    std::unique_ptr<Router> plain;
    if (parity_queries) plain = std::make_unique<Router>(d,proto,hubs,20260828,false);
    hnswlib::InnerProductSpace ip(d);
    auto distance = ip.get_dist_func(); auto* param = ip.get_dist_func_param();
    std::vector<Route> approximate(n), old_routes(n);
    std::vector<int32_t> exact_local(n*h), approx_local(n*8), seed100_local(n*8), basin;
    std::vector<float> exact_dist(n*h), approx_dist(n*8), seed100_dist(n*8);
    std::vector<uint32_t> approx_ndc(n), seed100_ndc(n);
    if (c.contains("basin_label_local")) basin = read_raw<int32_t>(c.at("basin_label_local"));
    if (!basin.empty()) { require(basin.size() == n, "basin label shape mismatch"); for(auto id:basin) require(id >= 0 && static_cast<size_t>(id)<h,"invalid basin local label"); }
    else {
        basin.resize(n);
        for (size_t j = 0; j < h; ++j) normalize(raw_hubs.data()+j*d,d);
        std::vector<float> gt1(d);
        for(size_t q=0;q<n;++q) {
            index->storage->reconstruct(gt[q*gtk],gt1.data()); normalize(gt1.data(),d);
            float best=std::numeric_limits<float>::infinity(); int32_t label=-1;
            for(size_t j=0;j<h;++j) { float dist=distance(gt1.data(),raw_hubs.data()+j*d,param); if(dist<best) {best=dist;label=j;} }
            basin[q]=label;
        }
    }
    #pragma omp parallel for schedule(static)
    for (size_t q=0;q<n;++q) {
        const float* query=queries.data()+q*d;
        approximate[q]=fast.route(query); old_routes[q]=old.route(query);
        approx_ndc[q]=approximate[q].ndc; seed100_ndc[q]=old_routes[q].ndc;
        std::copy(approximate[q].local.begin(),approximate[q].local.end(),approx_local.begin()+q*8);
        std::copy(approximate[q].distance.begin(),approximate[q].distance.end(),approx_dist.begin()+q*8);
        std::copy(old_routes[q].local.begin(),old_routes[q].local.end(),seed100_local.begin()+q*8);
        std::copy(old_routes[q].distance.begin(),old_routes[q].distance.end(),seed100_dist.begin()+q*8);
        std::vector<std::pair<float,int32_t>> ranked(h);
        for(size_t j=0;j<h;++j) ranked[j]={distance(query,proto.data()+j*d,param),static_cast<int32_t>(j)};
        std::sort(ranked.begin(),ranked.end(),[&](auto a,auto b) {return a.first != b.first ? a.first < b.first : hubs[a.second] < hubs[b.second];});
        for(size_t j=0;j<h;++j) {exact_local[q*h+j]=ranked[j].second;exact_dist[q*h+j]=ranked[j].first;}
    }
    write_raw(output/"exact.rank_local.i32",exact_local); write_raw(output/"exact.rank_distance.f32",exact_dist);
    write_raw(output/"fast.top8_local.i32",approx_local); write_raw(output/"fast.top8_distance.f32",approx_dist); write_raw(output/"fast.route_ndc.u32",approx_ndc);
    write_raw(output/"seed100.top8_local.i32",seed100_local); write_raw(output/"seed100.top8_distance.f32",seed100_dist); write_raw(output/"seed100.route_ndc.u32",seed100_ndc);
    write_raw(output/"basin_label_local.i32",basin);
    const auto vs = variants(c.value("seed100_search",true)); const size_t v=vs.size();
    auto entries_for = [&](size_t q,const Variant& variant) {
        std::array<int32_t,3> entries{-1,-1,-1};
        for(size_t j=0;j<variant.size;++j) {
            int rank=variant.ranks[j];
            entries[j]=variant.source=="exact" ? exact_local[q*h+rank] : variant.source=="seed100" ? old_routes[q].local[rank] : approximate[q].local[rank];
        }
        return entries;
    };
    std::vector<int32_t> pilot_entries(p*v*3);
    for(size_t q=0;q<p;++q) for(size_t j=0;j<v;++j) {
        const auto entries=entries_for(q,vs[j]); std::copy(entries.begin(),entries.end(),pilot_entries.begin()+(q*v+j)*3);
    }
    write_raw(output/"pilot.entry_local.i32",pilot_entries);
    json metadata={{"schema_version",1},{"status","RUNNING"},{"dim",d},{"num_queries",n},{"pilot_count",p},{"hub_count",h},{"K",K},{"gt_k",gtk},{"L",ls},{"threads",threads},
        {"index_path",c.at("index_path")},{"index_ntotal",index->ntotal},{"query_contract","unchanged raw query for HNSW, exact prototype distance and graph search"},
        {"kernel","original linked ACSG::search_new(mode=2), shared beam, max 3 entries"},{"timing_contract","all times instrumented diagnostic including scoring/allocation/I/O; never QPS"},
        {"router",{{"M",16},{"efConstruction",200},{"efSearch",10},{"seed",20260828},{"seed_control",100},{"labels","real base ID, mapped to hub row ordinal in output"},{"output_order","searchKnn heap reversed, near to far"}}},
        {"exact_router",{{"distance","same hnswlib::InnerProductSpace function as approximate"},{"ranking","distance ascending, then real base ID ascending"},{"score_conversion","inner product = 1 - distance"}}},
        {"all_single",shape_schema(n,h)},{"pilot",shape_schema(p,v)},{"variants",variant_json(vs)}};
    metadata["array_contract"]={{"byte_order","little-endian native"},{"layout","C row-major"},
        {"local_id","hub ordinal; real ID = hub_ids[local_id]"},{"invalid_entry_padding",-1}};
    metadata["array_contract"]["route_shapes"]={
        {"exact.rank_local.i32",{n,h}},{"exact.rank_distance.f32",{n,h}},
        {"fast.top8_local.i32",{n,8}},{"fast.top8_distance.f32",{n,8}},{"fast.route_ndc.u32",{n}},
        {"seed100.top8_local.i32",{n,8}},{"seed100.top8_distance.f32",{n,8}},{"seed100.route_ndc.u32",{n}},
        {"basin_label_local.i32",{n}},{"pilot.entry_local.i32",{p,v,3}}};
    write_json(output/"metadata.json",metadata);
    json parity={{"status","NOT_RUN"},{"rows_begin",p},{"query_count",parity_queries},{"pilot_excluded",true},{"graph_checks",0},{"route_checks",0},
        {"searches_per_graph_check",3},{"graph_comparison","counted vs plain vs counted repeat; IDs and distances exact; repeat NDC exact"},
        {"entry_audit","first distance evaluations equal every supplied real entry ID in supplied order"}};
    size_t graph_checks=0,route_checks=0;
    if(parity_queries) {
        Work wc(*index,true),wp(*index,false);
        for(size_t q=p;q<p+parity_queries;++q) {
            const float* query=queries.data()+q*d;
            auto plain_route=plain->route(query);
            require(plain_route.local==approximate[q].local && plain_route.distance==approximate[q].distance,"real route plain/count mismatch"); ++route_checks;
            auto repeated_route=fast.route(query);
            require(repeated_route.local==approximate[q].local && repeated_route.distance==approximate[q].distance && repeated_route.ndc==approximate[q].ndc,"real route repeat mismatch");
            for(size_t k=1;k<=3;++k) {
                auto rk=fast.route(query,k);
                for(size_t j=0;j<k;++j) require(rk.local[j]==approximate[q].local[j],"Fast top8 prefix differs from direct top-k");
            }
            for(int l:ls) {
                index->acsg.search_L=l;
                auto compare=[&](std::array<int32_t,3> entries,size_t size) {
                    auto a=wc.run(*index,query,hubs,entries,size),b=wp.run(*index,query,hubs,entries,size);
                    auto repeat=wc.run(*index,query,hubs,entries,size);
                    require(a.ids==b.ids && a.distances==b.distances,"real graph plain/count mismatch");
                    require(a.ids==repeat.ids && a.distances==repeat.distances && a.ndc==repeat.ndc,"real graph repeat mismatch"); ++graph_checks;
                };
                for(size_t j=0;j<h;++j) compare({static_cast<int32_t>(j),-1,-1},1);
                for(const auto& variant:vs) if(variant.size>1) compare(entries_for(q,variant),variant.size);
            }
        }
        parity["status"]="PASS";parity["graph_checks"]=graph_checks;parity["route_checks"]=route_checks;
        parity["graph_search_calls"]=graph_checks*3;
        log({{"stage","parity"},{"status","PASS"},{"graph_checks",graph_checks},{"route_checks",route_checks}});
    }
    write_json(output/"parity.json",parity);
    if(parity_only) {
        metadata["status"]="PARITY_ONLY_COMPLETE"; metadata["graph_search_calls_including_parity"]=graph_checks*3;
        metadata["instrumented_wall_seconds"]=std::chrono::duration<double>(Clock::now()-started).count();
        write_json(output/"metadata.json",metadata);return 0;
    }
    size_t total_searches=graph_checks*3;
    for(int l:ls) {
        index->acsg.search_L=l;
        fs::path dir=output/("L"+std::to_string(l));fs::create_directory(dir);
        Output singles(dir,"all_single"),pilot(dir,"pilot");
        std::vector<std::unique_ptr<Work>> works;
        for(int t=0;t<threads;++t) works.push_back(std::make_unique<Work>(*index,true));
        size_t l_searches=0;
        double single_wall=0,pilot_wall=0,scoring_io_wall=0;
        for(size_t begin=0;begin<n;begin+=16) {
            const size_t batch=std::min(size_t(16),n-begin), pb=begin<p?std::min(batch,p-begin):0;
            std::vector<Search> single_rows(batch*h),pilot_rows(pb*v);
            size_t batch_searches=0;
            auto stage_begin=Clock::now();
            #pragma omp parallel for schedule(static) reduction(+:batch_searches)
            for(size_t i=0;i<batch;++i) {
                size_t q=begin+i;const float* query=queries.data()+q*d;
                auto& work=*works[omp_get_thread_num()];
                for(size_t j=0;j<h;++j) {single_rows[i*h+j]=work.run(*index,query,hubs,{static_cast<int32_t>(j),-1,-1},1);++batch_searches;}
            }
            single_wall+=std::chrono::duration<double>(Clock::now()-stage_begin).count();
            stage_begin=Clock::now();
            #pragma omp parallel for schedule(static) reduction(+:batch_searches)
            for(size_t i=0;i<pb;++i) {
                    size_t q=begin+i;const float* query=queries.data()+q*d;
                    auto& work=*works[omp_get_thread_num()];
                    // Cache same ordered entry sets: Fast top2/3 reuse the corresponding C8 pair/triple searches.
                    std::vector<std::pair<std::array<int32_t,3>,Search>> cache;
                    for(size_t j=0;j<v;++j) {
                        auto entries=entries_for(q,vs[j]); auto& result=pilot_rows[i*v+j];
                        if(vs[j].size==1) {result=single_rows[i*h+entries[0]];continue;}
                        bool found=false;
                        for(const auto& prior:cache) if(prior.first==entries) {result=prior.second;found=true;break;}
                        if(!found) {result=work.run(*index,query,hubs,entries,vs[j].size);cache.emplace_back(entries,result);++batch_searches;}
                    }
            }
            pilot_wall+=std::chrono::duration<double>(Clock::now()-stage_begin).count();
            stage_begin=Clock::now();
            singles.append(single_rows,gt,gtk,begin,h);if(pb) pilot.append(pilot_rows,gt,gtk,begin,v);
            scoring_io_wall+=std::chrono::duration<double>(Clock::now()-stage_begin).count();
            l_searches+=batch_searches;total_searches+=batch_searches;
            json checkpoint={{"stage","search"},{"L",l},{"rows_complete",begin+batch},{"rows_total",n},{"pilot_rows_complete",std::min(begin+batch,p)},{"search_calls_this_L",l_searches},{"search_calls_total_including_parity",total_searches}};
            write_json(dir/"progress.json",checkpoint);log(checkpoint);
        }
        write_json(dir/"complete.json",{{"status","COMPLETE"},{"L",l},{"rows",n},{"pilot_rows",p},{"graph_search_calls",l_searches},{"instrumented_diagnostic_only",true},
            {"all_single_instrumented_wall_seconds",single_wall},{"pilot_joint_instrumented_wall_seconds",pilot_wall},{"scoring_and_binary_io_wall_seconds",scoring_io_wall}});
    }
    metadata["status"]="COMPLETE";metadata["graph_search_calls_including_parity"]=total_searches;
    metadata["instrumented_wall_seconds"]=std::chrono::duration<double>(Clock::now()-started).count();
    write_json(output/"metadata.json",metadata);log({{"stage","complete"},{"search_calls_total_including_parity",total_searches}});
    return 0;
}
} // namespace

int main(int argc,char** argv) {
    try {
        std::string config,output;size_t parity=8;bool parity_only=false;
        for(int i=1;i<argc;++i) {
            std::string a=argv[i];
            if(a=="--help" || a=="-h") {std::cout << "Fast root-cause diagnostic (CPU, original frozen-NSG shared-beam kernel)\nUsage: fast_router_diagnosis --config FILE --output NEW_DIR [--parity-queries 8] [--parity-only]\n       fast_router_diagnosis --self-test\nJSON required: dim,index_path,queries_file,gt_file,row_ids,hub_ids,raw_hubs,prototypes.\nOptional: num_queries,hub_count,gt_k=100,pilot_count=512,L=[64,128],K=10,threads=16,basin_label_local,seed100_search=true.\nAll binary inputs are headerless native little-endian C-order; query/prototype f32, GT/row_ids i64, hub IDs/basin labels i32.\nParity samples are exclusively rows after pilot_count. No timing from this diagnostic is publishable QPS.\n";return 0;}
            if(a=="--self-test") {self_test();return 0;}
            if(a=="--parity-only") {parity_only=true;continue;}
            require(i+1<argc,"missing argument value: "+a);
            if(a=="--config") config=argv[++i]; else if(a=="--output") output=argv[++i];
            else if(a=="--parity-queries") parity=std::stoul(argv[++i]);else throw std::runtime_error("unknown argument: "+a);
        }
        require(!config.empty() && !output.empty(),"--config and --output are required; see --help");
        require(!parity_only || parity>0,"--parity-only requires positive --parity-queries");
        std::ifstream f(config);require(bool(f),"cannot read config");json c;f>>c;
        return run(c,output,parity,parity_only);
    } catch(const std::exception& e) {std::cerr << "ERROR: " << e.what() << std::endl;return 1;}
}

#define main e206_embedded_main
#include "../../20261120_residual_budget_matched_table_v1/src/common.inc"
#undef main

#ifdef VERIFY_DISPATCH
namespace {
thread_local uint64_t ip_batches = 0;
}
extern "C" void __real__ZN5faiss26fvec_inner_product_batch_4EPKfS1_S1_S1_S1_mRfS2_S2_S2_(
    const float*, const float*, const float*, const float*, const float*, size_t,
    float&, float&, float&, float&);
extern "C" void __wrap__ZN5faiss26fvec_inner_product_batch_4EPKfS1_S1_S1_S1_mRfS2_S2_S2_(
    const float* q, const float* a, const float* b, const float* c, const float* d,
    size_t n, float& w, float& x, float& y, float& z) {
    ++ip_batches;
    __real__ZN5faiss26fvec_inner_product_batch_4EPKfS1_S1_S1_S1_mRfS2_S2_S2_(
        q, a, b, c, d, n, w, x, y, z);
}
#endif

namespace {
using namespace e183;

struct Arm {
    const char* name;
    size_t method;
    bool span;
};
constexpr std::array<Arm, 4> arms{{
    {"NSG-SPAN4", 0, true}, {"GT10-B32-SPAN4", 1, true},
    {"GATE-SPAN4", 2, true}, {"GATE-scalar", 2, false}
}};
struct Budget { int k, l; };
constexpr std::array<Budget, 14> matrix{{
    {1,64}, {1,100}, {1,160}, {1,200}, {1,320}, {1,400}, {1,800},
    {100,100}, {100,160}, {100,200}, {100,320}, {100,400}, {100,640}, {100,960}
}};

template<class Action>
double timed(Batch& destination, Action run) {
    const auto begin = Clock::now();
    {
        Batch received(destination.n, destination.k);
        run(received);
        copy_packet(received, destination);
        asm volatile("" :: "g"(destination.ids.data()), "g"(received.ids.data()) : "memory");
    }
    return seconds(begin);
}

json suite(const json& config) {
    check_threads(config);
    require(!config.contains("test_gt") && !config.contains("train_gt"), "no GT timing binding");
    json binding;
    auto index = load_index(config, binding);
    const Matrix window(config.at("queries"));
    require(window.n == 3072 && window.start == 0, "frozen query window");
    const auto queries = window.copy();
    Router gt10(config.at("router"), index->d, index->ntotal);
    Router gate(config.at("gate_router"), index->d, index->ntotal);
    Posting table(config.at("table"), index->ntotal);
    require(gate.gate && !gt10.gate && gate.ids.size() == 512, "frozen GATE and GT10 route types");
    require(!table.empty && table.b == 32, "original full B32");
    require(index->metric_type == faiss::METRIC_INNER_PRODUCT, "native raw IP");
    require(index->acsg.enterpoint >= 0 && index->acsg.enterpoint < index->ntotal, "NSG fixed entry");
    const std::array<Method, 3> methods{{
        {"NSG", "NSG", "", "", nullptr, nullptr},
        {"GT10+B32", "POST", gt10.name, "GT10", &gt10, &table},
        {"GATE", "GATE", gate.name, "", &gate, nullptr}
    }};
    auto execute = [&](const Arm& arm, int l, Batch& packet) {
        run_batch(*index, queries, l, methods[arm.method], packet);
    };

#ifdef VERIFY_DISPATCH
    json dispatch = json::array();
    for (int k : {1, 100}) {
        Batch gate_span(32, k), gate_scalar(32, k);
        for (const auto& arm : arms) {
            index->acsg.set_flat_ip_batch4_enabled(arm.span);
            ip_batches = 0;
            Batch local(32, k);
            Batch& result = arm.method == 2 ? (arm.span ? gate_span : gate_scalar) : local;
            execute(arm, 200, result);
            validate(result, index->ntotal);
            require((ip_batches > 0) == arm.span, "actual native Faiss raw-IP batch4 dispatch");
            dispatch.push_back({{"method", arm.name}, {"K", k}, {"L", 200},
                                {"queries", 32}, {"faiss_ip_batch4_calls", ip_batches}});
        }
        all_same(gate_span, gate_scalar);
    }
    return {{"status", "PASS_E213_DISPATCH"}, {"dataset", config.at("dataset")}, {"dispatch", dispatch}};
#else
    const fs::path root = config.at("output_dir");
    fresh_dir(root);
    fresh_json(root/"environment.json", {{"dataset", config.at("dataset")}, {"binding", binding},
        {"nsg_fixed_entry", index->acsg.enterpoint}, {"threads", process_threads()},
        {"cpu", sched_getcpu()}});
    int ordinal = 0;
    for (auto [k, l] : matrix) {
        const auto point = root/("K"+std::to_string(k)+"_L"+std::to_string(l));
        fresh_dir(point);
        Batch warm(256, k), destination(window.n, k);
        std::array<std::unique_ptr<Batch>, arms.size()> first;
        int order = 0;
        for (int rep = 0; rep < 2; ++rep) {
            for (size_t offset = 0; offset < arms.size(); ++offset) {
                const size_t i = (ordinal + (rep ? arms.size() - 1 - offset : offset)) % arms.size();
                const auto& arm = arms[i];
                check_threads(config);
                index->acsg.set_flat_ip_batch4_enabled(arm.span);
                execute(arm, l, warm);
                const double wall = timed(destination, [&](Batch& packet) { execute(arm, l, packet); });
                check_threads(config);
                validate(destination, index->ntotal);
                if (!rep) {
                    first[i] = std::make_unique<Batch>(destination);
                    destination.save(point/arm.name/"raw", false);
                } else {
                    all_same(*first[i], destination);
                }
                const json row{{"method", arm.name}, {"backend", arm.span ? "SPAN4" : "scalar"},
                    {"K", k}, {"L", l}, {"n", window.n}, {"rep", rep}, {"seconds", wall},
                    {"qps", window.n/wall}, {"order", ++order}, {"sha256", packet_sha(destination)},
                    {"cpu", sched_getcpu()}, {"threads", process_threads()}};
                fresh_json(point/arm.name/("round"+std::to_string(rep)+".json"), row);
                std::cout << row.dump() << std::endl;
            }
        }
        all_same(*first[2], *first[3]);
        ++ordinal;
    }
    json result{{"status", "PASS_E213_NATIVE"}, {"dataset", config.at("dataset")},
        {"points", matrix.size()*arms.size()}, {"batches", matrix.size()*arms.size()*2},
        {"gate_backend_parity_points", matrix.size()}, {"public_GT_read", false}};
    fresh_json(root/"complete.json", result);
    return result;
#endif
}
}

int main(int argc, char** argv) {
    try {
        e183::require(argc == 2, "benchmark config.json");
        std::cout << suite(e183::read_json(argv[1])).dump() << std::endl;
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "E213: " << error.what() << std::endl;
        return 1;
    }
}

// Thread-contract wrapper; the benchmark/search/timing implementation is unchanged.
#define AB_BENCHMARK_LIBRARY
#include "benchmark_with_nsg.cpp"
#include <cstdlib>

int main(int argc, char** argv) {
    try {
        require(argc == 3, "Usage: benchmark_single_thread_nsg config.json new_output");
        std::ifstream input(argv[1]);
        require(bool(input), "missing config");
        json config;
        input >> config;
        require(config.contains("threads") && config.at("threads") == 1,
                "formal evaluation requires explicit threads=1");
        json environment;
        for (const char* name : {"OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"}) {
            const char* value = std::getenv(name);
            require(value && std::string(value) == "1", std::string("formal evaluation requires ") + name + "=1");
            environment[name] = value;
        }
        omp_set_dynamic(0);
        omp_set_num_threads(1);
        int observed = 0;
        #pragma omp parallel
        {
            #pragma omp single
            observed = omp_get_num_threads();
        }
        require(observed == 1 && omp_get_max_threads() == 1,
                "single-thread OpenMP runtime contract failed");
        json contract = {{"status", "PASS"}, {"requested_threads", 1},
                         {"observed_openmp_threads", observed}, {"openmp_max_threads", omp_get_max_threads()},
                         {"openmp_dynamic", omp_get_dynamic()}, {"environment", environment},
                         {"policy", "All methods and baselines use one query thread; no conversion from parallel QPS"}};
        std::cout << json({{"stage", "single_thread_contract"}, {"contract", contract}}).dump() << std::endl;
        const int status = benchmark(config, argv[2]);
        write_json(fs::path(argv[2]) / "thread_contract.json", contract);
        return status;
    } catch (const std::exception& error) {
        std::cerr << error.what() << std::endl;
        return 1;
    }
}

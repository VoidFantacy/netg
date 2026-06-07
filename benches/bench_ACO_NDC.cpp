#include <iostream>
#include <argparse/argparse.hpp>
#include <benches/datasets/DataLoader.hpp>
#include <nlohmann/json.hpp>
#include <ACSG/IndexACSG.h>

#include <benches/utils/Timer.hpp>
#include <benches/utils/metrics.hpp>
#include <benches/utils/graph_properties.hpp>
#include <iostream>

std::tuple<std::unique_ptr<acsg::IndexACSG>, double> construct_ACSG(const DataLoader &data_loader,
                                                                    const nlohmann::json &parameters)
{
    int d = data_loader.dim();
    int R = parameters["R"];
    auto index = std::make_unique<acsg::IndexACSGFlat>(d, R);
    index->acsg.alpha = parameters["alpha"];
    index->acsg.beta = parameters["beta"];
    index->acsg.rho = parameters["rho"];
    index->acsg.lambda = parameters["lambda"];
    index->acsg.iterations = parameters["iterations"];
    index->acsg.thresholdrej = parameters["rejection"];

    index->verbose = true;
    // train

    // add
    double construction_time_sec;
    {
        auto [nb, xb] = data_loader.load_base();

        Timer timer;
        index->add(nb, xb.get());
        construction_time_sec = timer.elapsed_ms() * 1e-3;
        std::cout << "Time = " << construction_time_sec << " [s]" << std::endl;
    }

    return {std::move(index), construction_time_sec};
}

double train_ACO(const DataLoader &data_loader, acsg::IndexACSG &index)
{
    using idx_t = faiss::idx_t;
    std::cerr << "training" << std::endl;
    double train_time_sec;
    {
        auto [nq, xq] = data_loader.load_train();
        std::cerr << "nq:" << nq << std::endl;
        auto [k, gt] = data_loader.load_train_gt();
        std::cerr << "k:" << k << std::endl;
        Timer timer;
        index.antSearch(nq, xq.get(), k, gt.get());
        train_time_sec = timer.elapsed_ms() * 1e-3;
        std::cout << "Time = " << train_time_sec << " [s]" << std::endl;
    }
    return train_time_sec;
}

nlohmann::json measure_search_performance(acsg::IndexACSG &index,
                                          const DataLoader &data_loader)
{

    size_t d = data_loader.dim();
    auto [nb, xb] = data_loader.load_base();
    auto [nq, xq] = data_loader.load_query();
    auto [k, gt] = data_loader.load_gt();

    int query_size = 200;
    k = 10;
    printf("nq = %ld, d = %ld, k = %ld\n", nq, d, k);
    using idx_t = faiss::idx_t;

    nlohmann::json results;

    std::unique_ptr<idx_t[]> gt_I(new idx_t[query_size * k]);
    std::unique_ptr<float[]> gt_D(new float[query_size * k]);

    std::unique_ptr<idx_t[]> I(new idx_t[query_size * k]);
    std::unique_ptr<float[]> D(new float[query_size * k]);

    index.brute_force_search(nb, xb.get(), query_size, xq.get(), k, gt_D.get(), gt_I.get());

    for (int search_L : {1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024})
    {
        index.acsg.search_L = search_L;

        Timer timer;
        index.search_v1(query_size, xq.get(), k, D.get(), I.get());
        auto elapsed = timer.elapsed_ns() * 1e-9;

        float mean_redrr = 0;
        for (int i = 0; i < query_size; i++)
        {
            float rdrr = 0;
            for (size_t j = 0; j < k; j++)
            {
                if (D[i * k + j] == 0)
                    continue;
                /* code */
                rdrr += (D[i * k + j] / (gt_D[i * k + j] + 1e-8)) - 1;
            }
            rdrr = rdrr / k;
            mean_redrr += rdrr;
        }
        mean_redrr /= query_size;
        std::cout << "NDC = " << index.acsg.NDC << " [q/s], rderr = " << mean_redrr << std::endl;
        nlohmann::json result;
        result["search_L"] = search_L;
        result["NDC"] = index.acsg.NDC.load();
        result["rderr"] = mean_redrr;
        result["search_time"] = elapsed;
        results.push_back(result);
    }

    return results;
}

nlohmann::json measure_search_performance_ACO(acsg::IndexACSG &index,
                                              const DataLoader &data_loader)
{

    size_t d = data_loader.dim();
    auto [nb, xb] = data_loader.load_base();
    auto [nq, xq] = data_loader.load_query();
    auto [k, gt] = data_loader.load_gt();

    int query_size = 200;
    k = 10;
    printf("nq = %ld, d = %ld, k = %ld\n", nq, d, k);
    using idx_t = faiss::idx_t;
    nlohmann::json results;
    std::unique_ptr<idx_t[]> gt_I(new idx_t[query_size * k]);
    std::unique_ptr<float[]> gt_D(new float[query_size * k]);

    std::unique_ptr<idx_t[]> I(new idx_t[query_size * k]);
    std::unique_ptr<float[]> D(new float[query_size * k]);

    index.brute_force_search(nb, xb.get(), query_size, xq.get(), k, gt_D.get(), gt_I.get());

    for (int search_L : {1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024})
    {
        index.acsg.search_L = search_L;

        Timer timer;
        index.search_ACO(query_size, xq.get(), k, D.get(), I.get());
        auto elapsed = timer.elapsed_ns() * 1e-9;

        float mean_redrr = 0;
        for (int i = 0; i < query_size; i++)
        {
            float rdrr = 0;
            for (size_t j = 0; j < k; j++)
            {
                if (D[i * k + j] == 0)
                    continue;
                /* code */
                rdrr += (D[i * k + j] / (gt_D[i * k + j])) - 1;
            }
            rdrr = rdrr / k;
            mean_redrr += rdrr;
        }
        mean_redrr /= query_size;
        std::cout << "NDC = " << index.acsg.NDC << " [q/s], rderr = " << mean_redrr << std::endl;
        nlohmann::json result;
        result["search_L"] = search_L;
        result["NDC"] = index.acsg.NDC.load();
        result["rderr"] = mean_redrr;
        result["search_time"] = elapsed;
        results.push_back(result);
    }

    return results;
}

nlohmann::json acsg_properties(acsg::IndexACSG &index)
{
    const int n = index.ntotal;
    const int R = index.acsg.nsg_R;
    std::vector<int> neighbors(R * n);
    for (int i = 0; i < n; ++i)
    {
        for (int j = 0; j < R; ++j)
        {
            neighbors[i * R + j] = index.acsg.final_graph->at(i, j);
        }
    }
    const auto get_range = [&](int u) -> std::tuple<int, int>
    {
        return {u * R, (u + 1) * R};
    };
    return graph_properties(n, neighbors, get_range);
}

int main(int argc, char **argv)
{
    argparse::ArgumentParser program("bench_ACO");

    // 添加参数并指定默认值
    program.add_argument("--alpha").default_value(1.0).scan<'g', float>(); // 默认值.scan<'g', float>(); // 解析为浮点数
    program.add_argument("--beta").default_value(2.0).scan<'g', float>();
    program.add_argument("--rho").default_value(0.5).scan<'g', float>();
    program.add_argument("--lambda").default_value(0.5).scan<'g', float>();
    program.add_argument("--rejection").default_value(15).scan<'i', int>();
    program.add_argument("--iterations").default_value(10).scan<'i', int>();
    program.add_argument("--R").default_value(32).scan<'i', int>();
    program.add_argument("--dataset").required();   // 必须提供数据集路径
    program.add_argument("--fn_result").required(); // 必须提供结果文件名

    try
    {
        program.parse_args(argc, argv); // 解析命令行参数
    }
    catch (const std::runtime_error &err)
    {
        std::cerr << "Error: " << err.what() << std::endl;
        std::cerr << program;
        return 1;
    }

    // 获取参数值
    float alpha = program.get<float>("--alpha");
    float beta = program.get<float>("--beta");
    float rho = program.get<float>("--rho");
    float lambda = program.get<float>("--lambda");
    int rejection = program.get<int>("--rejection");
    int iterations = program.get<int>("--iterations");
    std::string dataset_name = program.get<std::string>("--dataset");
    std::string result_file = program.get<std::string>("--fn_result");

    std::cout << "Running ACO with parameters:\n";
    std::cout << "  Alpha: " << alpha << "\n";
    std::cout << "  Beta: " << beta << "\n";
    std::cout << "  Rho: " << rho << "\n";
    std::cout << "  lambda:" << lambda << "\n";
    std::cout << "  Dataset: " << dataset_name << "\n";
    std::cout << "  Result file: " << result_file << "\n";

    // 加载数据集
    DataLoader data_loader(dataset_name);
    int d = data_loader.dim();
    // 初始化蚁群算法

    nlohmann::json parameters;
    parameters["R"] = program.get<int>("--R");
    parameters["alpha"] = program.get<float>("--alpha");
    parameters["beta"] = program.get<float>("--beta");
    parameters["rho"] = program.get<float>("--rho");
    parameters["lambda"] = program.get<float>("--lambda");
    parameters["iterations"] = program.get<int>("--iterations");
    parameters["rejection"] = program.get<int>("--rejection");

    auto [index, construction_time] =
        construct_ACSG(data_loader, parameters);
    auto train_time = train_ACO(data_loader, *index);
    auto results_standard = measure_search_performance(*index, data_loader);
    auto results_aco = measure_search_performance_ACO(*index, data_loader);
    // auto brute_force_time = measure_search_performance_brute_force(*index, data_loader);

    std::string fn_aco = program.get<std::string>("--fn_result");

    nlohmann::json output_aco;
    output_aco["dataset"] = dataset_name;
    output_aco["method"] = "ACO_optimized";
    output_aco["parameters"] = parameters;
    output_aco["construction_time"] = construction_time;
    output_aco["train"] = train_time;
    output_aco["search_performances"] = results_standard;
    output_aco["search_performances_aco"] = results_aco;
    output_aco["properties"] = acsg_properties(*index);

    std::ofstream ofs_aco(fn_aco);
    ofs_aco << output_aco.dump(4) << std::endl;
    std::cout << "Saved the ACO optimized search result to \"" << fn_aco << "\"" << std::endl;
}
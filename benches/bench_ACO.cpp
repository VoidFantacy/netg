#include <iostream>
#include <argparse/argparse.hpp>
#include <benches/datasets/DataLoader.hpp>
#include <nlohmann/json.hpp>
#include <ACSG/IndexACSG.h>
#include <tuple>
#include <fstream>
#include <filesystem>
#include <benches/utils/Timer.hpp>

// 辅助函数：打印JSON类型信息
std::string json_type_str(const nlohmann::json& j) {
    if (j.is_null()) return "null";
    if (j.is_boolean()) return "boolean";
    if (j.is_number()) return "number";
    if (j.is_string()) return "string";
    if (j.is_array()) return "array";
    if (j.is_object()) return "object";
    return "unknown";
}

std::tuple<std::unique_ptr<acsg::IndexACSG>, double> construct_ACSG(const DataLoader &data_loader,
                                                                    const nlohmann::json &parameters)
{
    try {
        int d = data_loader.dim();
        int R = parameters["R"];
        auto index = std::make_unique<acsg::IndexACSGFlat>(d, R, data_loader.metric_type());
        
        // 设置 NSG 构建参数
        if (parameters.contains("L_build")) {
            index->nsg_L = parameters["L_build"];
        }
        if (parameters.contains("C")) {
            index->nsg_C = parameters["C"];
        }

        index->acsg.alpha = parameters["alpha"];
        index->acsg.beta = parameters["beta"];
        index->acsg.rho = parameters["rho"];
        index->acsg.lambda = parameters["lambda"];
        index->acsg.iterations = parameters["iterations"];
        index->acsg.thresholdrej = parameters["rejection"];

        index->verbose = true;

        double construction_time_sec;
        {
            auto [nb, xb] = data_loader.load_base();
            std::cerr << "Constructing ACSG with " << nb << " vectors (dim=" << d << ")\n";
            std::cerr << "Build Params: R=" << R 
                      << ", L_build=" << index->nsg_L 
                      << ", C=" << index->nsg_C << std::endl;

            Timer timer;
            index->add(nb, xb.get());
            construction_time_sec = timer.elapsed_ms() * 1e-3;
            std::cout << "Construction Time = " << construction_time_sec << " [s]" << std::endl;
        }

        return {std::move(index), construction_time_sec};
    } catch (const std::exception& e) {
        std::cerr << "ERROR in construct_ACSG: " << e.what() << "\n";
        throw;
    }
}

int main(int argc, char **argv)
{
    try {
        argparse::ArgumentParser program("build_ACO_index");

        program.add_argument("--alpha").default_value(1.0).scan<'g', float>();
        program.add_argument("--beta").default_value(2.0).scan<'g', float>();
        program.add_argument("--rho").default_value(0.5).scan<'g', float>();
        program.add_argument("--lambda").default_value(0.5).scan<'g', float>();
        program.add_argument("--rejection").default_value(15).scan<'i', int>();
        program.add_argument("--iterations").default_value(10).scan<'i', int>();
        
        // [关键修改] 将默认 L_build 从 50 提高到 100
        // R 保持 50 (论文参数), C 保持 512 (论文参数)
        program.add_argument("--R").default_value(50).scan<'i', int>().help("Graph degree (def: 50)");
        program.add_argument("--L_build").default_value(100).scan<'i', int>().help("Build search depth (def: 100, increased for connectivity)");
        program.add_argument("--C").default_value(512).scan<'i', int>().help("Build candidate pool (def: 512)");

        program.add_argument("--dataset").required();
        program.add_argument("--index_file").required();

        try {
            program.parse_args(argc, argv);
        } catch (const std::runtime_error &err) {
            std::cerr << "Argument parsing error: " << err.what() << std::endl;
            std::cerr << program;
            return 1;
        }

        float alpha = program.get<float>("--alpha");
        float beta = program.get<float>("--beta");
        float rho = program.get<float>("--rho");
        float lambda = program.get<float>("--lambda");
        int rejection = program.get<int>("--rejection");
        int iterations = program.get<int>("--iterations");
        std::string dataset_name = program.get<std::string>("--dataset");
        std::string index_file = program.get<std::string>("--index_file");
        int R = program.get<int>("--R");
        int L_build = program.get<int>("--L_build");
        int C = program.get<int>("--C");

        std::cout << "Building ACO index with parameters:\n";
        std::cout << "  Alpha: " << alpha << "\n";
        std::cout << "  Beta: " << beta << "\n";
        std::cout << "  Rho: " << rho << "\n";
        std::cout << "  Lambda: " << lambda << "\n";
        std::cout << "  Rejection: " << rejection << "\n";
        std::cout << "  Iterations: " << iterations << "\n";
        std::cout << "  R: " << R << "\n";
        std::cout << "  L_build: " << L_build << "\n";
        std::cout << "  C: " << C << "\n";
        std::cout << "  Dataset: " << dataset_name << "\n";
        std::cout << "  Index file: " << index_file << "\n";

        // 加载数据集
        DataLoader data_loader(dataset_name);
        // std::cout << "  loaded " <<  "\n"; // Removed empty print
        int d = data_loader.dim();
        std::cout << "Dataset info:\n";
        std::cout << "  Dimension: " << d << "\n";
        std::cout << "  Base vectors: " << std::get<0>(data_loader.load_base()) << "\n";

        // 初始化参数JSON
        nlohmann::json parameters;
        parameters["R"] = R;
        parameters["L_build"] = L_build; 
        parameters["C"] = C;             
        parameters["alpha"] = alpha;
        parameters["beta"] = beta;
        parameters["rho"] = rho;
        parameters["lambda"] = lambda;
        parameters["iterations"] = iterations;
        parameters["rejection"] = rejection;

        // 构建索引
        auto [index, construction_time] = construct_ACSG(data_loader, parameters);

        // 保存索引
        std::cout << "Saving index to: " << index_file << std::endl;
        index->save(index_file.c_str());
        std::cout << "Index saved successfully!" << std::endl;

        // 保存构建参数
        nlohmann::json build_info;
        build_info["parameters"] = parameters;
        build_info["construction_time"] = construction_time;
        build_info["dataset"] = dataset_name;
        build_info["metric"] = data_loader.metric_name();
        build_info["normalization"] = data_loader.normalization();
        build_info["artifact_version"] = data_loader.artifact_version();
        
        std::string build_info_file = index_file + ".info";
        std::ofstream info_ofs(build_info_file);
        info_ofs << build_info.dump(4) << std::endl;
        std::cout << "Build info saved to: " << build_info_file << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "FATAL ERROR: " << e.what() << "\n";
        return 1;
    }

    return 0;
}

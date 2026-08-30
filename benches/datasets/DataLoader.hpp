#pragma once

#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <nlohmann/json.hpp>
#include <regex>
#include <string>
#include <tuple>
#include <cassert>
#include <vector>
#include <cstring>
#include <algorithm>
#include <faiss/MetricType.h>

namespace
{
    // 获取文件中的向量维度
    size_t load_dim(const std::filesystem::path &filename)
    {
        std::ifstream ifs(filename, std::ios::binary);
        if (!ifs.is_open()) {
            std::cerr << "Error: Could not open file " << filename << std::endl;
            return 0;
        }
        int32_t d;
        ifs.read((char *)&d, sizeof(d));
        return static_cast<size_t>(d);
    }

    // 获取文件中的向量总数
    size_t get_file_size_in_vecs(const std::filesystem::path &filename, size_t dim, size_t element_size) {
        std::ifstream ifs(filename, std::ios::binary);
        if (!ifs.is_open()) return 0;
        ifs.seekg(0, std::ios_base::end);
        size_t file_byte_size = ifs.tellg();
        size_t vec_byte_size = sizeof(int) + dim * element_size; // header(4 bytes) + data
        return file_byte_size / vec_byte_size;
    }

    // 通用加载函数：支持从指定 offset 读取 count 个向量
    // 【修改点1】返回值改为 3 元组：<数量 n, 维度 d, 数据 ptr>
    template<typename T>
    std::tuple<size_t, size_t, std::unique_ptr<T[]>> load_vecs_range(
        const std::filesystem::path &filename, 
        size_t start_idx, 
        long count, 
        bool is_ivecs,
        bool is_bvecs = false)
    {
        std::ifstream ifs(filename, std::ios::binary);
        if (!ifs.is_open()) {
            throw std::runtime_error("Error: Could not open file: " + filename.string());
        }

        int d;
        ifs.read((char *)&d, sizeof(d)); // 读取维度

        // 计算向量大小和偏移量
        size_t element_size = is_ivecs ? sizeof(int) : (is_bvecs ? sizeof(unsigned char) : sizeof(float));
        size_t vec_byte_size = sizeof(int) + d * element_size; 

        // 确定文件总数
        ifs.seekg(0, std::ios_base::end);
        size_t total_vecs = ifs.tellg() / vec_byte_size;
        
        // 处理 count = -1 (读取剩余所有)
        size_t actual_count = (count < 0) ? (total_vecs - start_idx) : static_cast<size_t>(count);
        
        // 边界检查
        if (start_idx + actual_count > total_vecs) {
            actual_count = total_vecs - start_idx;
            std::cerr << "Warning: Requested count exceeds file size. Truncating to " << actual_count << std::endl;
        }

        // 定位到 start_idx
        ifs.seekg(start_idx * vec_byte_size, std::ios_base::beg);

        // 分配内存
        std::unique_ptr<T[]> x(new T[d * actual_count]);

        // 批量读取
        constexpr size_t batch_size = 8192;
        
        size_t buf_vec_size = sizeof(int) + d * element_size; 
        std::vector<char> buf(batch_size * buf_vec_size);

        size_t pos_x = 0;
        for (size_t i = 0; i < actual_count; i += batch_size)
        {
            size_t nvecs = std::min(actual_count - i, batch_size);
            ifs.read(buf.data(), nvecs * buf_vec_size);
            
            size_t pos_buf = 0;
            for (size_t j = 0; j < nvecs; ++j)
            {
                pos_buf += sizeof(int);
                
                if (is_bvecs) { 
                    unsigned char* ptr = reinterpret_cast<unsigned char*>(buf.data() + pos_buf);
                    for (int k = 0; k < d; ++k) x[pos_x + k] = static_cast<T>(ptr[k]);
                } else if (is_ivecs) { 
                     int* ptr = reinterpret_cast<int*>(buf.data() + pos_buf);
                     for (int k = 0; k < d; ++k) x[pos_x + k] = static_cast<T>(ptr[k]);
                } else { 
                    float* ptr = reinterpret_cast<float*>(buf.data() + pos_buf);
                    std::memcpy(&x[pos_x], ptr, d * sizeof(float));
                }

                pos_buf += d * element_size;
                pos_x += d;
            }
        }

        // 【修改点2】返回 {数量, 维度, 数据}
        return {actual_count, static_cast<size_t>(d), std::move(x)};
    }
} 

class DataLoader
{
    long n;
    size_t d;
    
    std::filesystem::path root_dir;
    std::filesystem::path dataset_dir;
    nlohmann::json dataset_settings;

    std::filesystem::path train_path;
    std::filesystem::path base_path;

public:
    DataLoader(const std::string &dataset_name, const std::string &settings_path = "./benches/datasets/settings.json");

    inline size_t dim() const { return d; }

    faiss::MetricType metric_type() const
    {
        const std::string metric = dataset_settings.value("metric", "l2");
        if (metric == "l2") return faiss::METRIC_L2;
        if (metric == "ip") return faiss::METRIC_INNER_PRODUCT;
        throw std::runtime_error("Unsupported metric in settings.json: " + metric);
    }

    std::string metric_name() const { return dataset_settings.value("metric", "l2"); }
    std::string normalization() const { return dataset_settings.value("normalization", "unspecified"); }
    std::string artifact_version() const { return dataset_settings.value("artifact_version", "legacy-unversioned"); }

    std::tuple<size_t, std::unique_ptr<float[]>> load_train(size_t max_samples = 50000) const
    {
        std::filesystem::path path_to_load = std::filesystem::exists(train_path) ? train_path : base_path;
        bool is_bvecs = (path_to_load.extension() == ".bvecs");
        size_t element_size = is_bvecs ? 1 : 4;
        size_t total = get_file_size_in_vecs(path_to_load, d, element_size);

        long load_count = -1;
        if (max_samples > 0 && total > max_samples) {
            std::cout << "⚠️ Training data too large (" << total << "). Sampling first " << max_samples << " vectors." << std::endl;
            load_count = (long)max_samples;
        } else {
            std::cout << "📖 Loading full training data (" << total << " vectors)..." << std::endl;
        }

        // 【修改点3】接收 3 个返回值，只返回 {n, x}
        auto [n_loaded, dim_loaded, x] = load_vecs_range<float>(path_to_load, 0, load_count, false, is_bvecs);
        return {n_loaded, std::move(x)};
    }

    std::tuple<size_t, std::unique_ptr<float[]>> load_base() const
    {
        bool is_bvecs = (base_path.extension() == ".bvecs");
        // 【修改点4】同上
        auto [n_loaded, dim_loaded, x] = load_vecs_range<float>(base_path, 0, n, false, is_bvecs);
        return {n_loaded, std::move(x)};
    }

    std::tuple<size_t, std::unique_ptr<float[]>> load_query(const std::string& type = "") const
    {
        std::string key = (type.empty()) ? "query_path" : type + "_query_path";
        std::filesystem::path full_path;
        bool do_split = false;
        bool is_second_half = false;

        if (dataset_settings.contains(key)) {
            full_path = dataset_dir / dataset_settings[key].get<std::string>();
        } else {
            if (type == "drl_train" || type == "drl_test") {
                if (!dataset_settings.contains("query_path")) throw std::runtime_error("query_path missing");
                full_path = dataset_dir / dataset_settings["query_path"].get<std::string>();
                do_split = true;
                is_second_half = (type == "drl_test");
                std::cout << "🔄 Auto-Splitting Query for " << type << "..." << std::endl;
            } else {
                throw std::runtime_error("Query path key not found: " + key);
            }
        }

        bool is_bvecs = (full_path.extension() == ".bvecs");
        
        // 【修改点5】统一接收 3 返回值，返回 {n, x}
        size_t start = 0;
        long count = -1;

        if (do_split) {
            size_t total = get_file_size_in_vecs(full_path, d, is_bvecs ? 1 : 4);
            size_t split_idx = total / 2;
            start = is_second_half ? split_idx : 0;
            count = is_second_half ? (total - split_idx) : split_idx;
            std::cout << "   -> Loading slice [" << start << ", " << start+count << ") from " << full_path.filename() << std::endl;
        } else {
            std::cout << "Loading query from: " << full_path << std::endl;
        }

        auto [n_loaded, dim_loaded, x] = load_vecs_range<float>(full_path, start, count, false, is_bvecs);
        return {n_loaded, std::move(x)};
    }

    // ==========================================
    // 修改重点：load_gt
    // ==========================================
    std::tuple<size_t, std::unique_ptr<int64_t[]>> load_gt(const std::string& type = "") const
    {
        std::string key = (type.empty()) ? "gt_path" : type + "_gt_path";
        std::filesystem::path full_path;
        bool do_split = false;
        bool is_second_half = false;

        if (dataset_settings.contains(key)) {
            full_path = dataset_dir / dataset_settings[key].get<std::string>();
        } else {
            if (type == "drl_train" || type == "drl_test" || type == "train") {
                if (!dataset_settings.contains("gt_path")) throw std::runtime_error("gt_path missing");
                full_path = dataset_dir / dataset_settings["gt_path"].get<std::string>();
                do_split = true;
                is_second_half = (type == "drl_test"); 
            } else {
                throw std::runtime_error("GT path key not found: " + key);
            }
        }

        size_t start = 0;
        long count = -1;

        if (do_split) {
            size_t total = get_file_size_in_vecs(full_path, d, 4);
            size_t split_idx = total / 2;
            start = is_second_half ? split_idx : 0;
            count = is_second_half ? (total - split_idx) : split_idx;
            std::cout << "   -> Loading GT slice [" << start << ", " << start+count << ") from " << full_path.filename() << std::endl;
        } else {
            std::cout << "Loading GT from: " << full_path << std::endl;
        }

        // 【关键修改点！】
        // 这里我们获取 {n, d, x}
        auto [n_loaded, dim_loaded, x] = load_vecs_range<int64_t>(full_path, start, count, true, false);
        
        // 【注意】这里返回 {dim_loaded, x} 而不是 n_loaded！
        // 因为外界期待的是 K (维度/邻居数)，例如 100
        return {dim_loaded, std::move(x)}; 
    }

    std::tuple<size_t, std::unique_ptr<int64_t[]>> load_train_gt() const
    {
        if (dataset_settings.contains("train_gt_path")) {
            return load_gt("train");
        } else {
            return load_gt("drl_train");
        }
    }

    void dump();
};

DataLoader::DataLoader(const std::string &dataset_name, const std::string &settings_path)
{
    std::ifstream ifs(settings_path);
    if (!ifs.is_open()) throw std::runtime_error("Could not open settings file: " + settings_path);
    
    nlohmann::json settings = nlohmann::json::parse(ifs);
    if (!settings["datasets"].contains(dataset_name)) throw std::runtime_error("Dataset not found: " + dataset_name);

    dataset_settings = settings["datasets"][dataset_name];
    
    std::string root_dir_str = settings["root_dir"].get<std::string>();
    root_dir = root_dir_str;
    
    std::string ds_dir_str = dataset_settings["dataset_dir"].get<std::string>();
    dataset_dir = root_dir / ds_dir_str;

    if (dataset_settings.contains("train_path")) {
        train_path = dataset_dir / dataset_settings["train_path"].get<std::string>();
    }
    
    if (dataset_settings.contains("base_path")) {
        base_path = dataset_dir / dataset_settings["base_path"].get<std::string>();
    } else {
        throw std::runtime_error("base_path missing");
    }

    n = dataset_settings.contains("nvecs") ? dataset_settings["nvecs"].get<long>() : -1;
    
    if (std::filesystem::exists(base_path)) {
        d = load_dim(base_path);
    } else if (std::filesystem::exists(train_path)) {
        d = load_dim(train_path);
    } else {
        d = 0; 
        std::cerr << "Warning: dimension could not be determined" << std::endl;
    }
}

void DataLoader::dump()
{
    std::cout << "DataLoader Configuration {\n";
    std::cout << "\tDataset: " << dataset_dir.filename().string() << "\n";
    std::cout << "\tDim: " << d << "\n";
    std::cout << "}\n";
}

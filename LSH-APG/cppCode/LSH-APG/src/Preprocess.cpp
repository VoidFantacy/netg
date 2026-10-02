#include "Preprocess.h"
#include <fstream>
#include <iostream>
#include <cmath>
#include <numeric>
#include <vector>
#include <cfloat>
#include <cstdlib>

Preprocess::Preprocess(const std::string& path, const std::string& ben_file_)
{
    // 仅保留关键路径信息打印
    std::cout << "[Preprocess] Loading Base Data: " << path << std::endl;
    load_data(path);
    data_file = path;
    ben_file = ben_file_;
}

Preprocess::Preprocess(const std::string& path, const std::string& ben_file_, float beta_)
{
    hasT = true;
    beta = beta_;
    std::cout << "[Preprocess] Loading Base Data: " << path << std::endl;
    load_data(path);
    data_file = path;
    ben_file = ben_file_;
}

// 核心加载逻辑 (原生支持 .fvecs)
void Preprocess::load_data(const std::string& path)
{
    std::ifstream in(path.c_str(), std::ios::binary);
    if (!in) {
        std::cerr << "❌ [FATAL] Cannot open file: " << path << std::endl;
        exit(1); // 遇到错误直接退出进程，防止死循环
    }

    // 读取维度
    unsigned dim;
    in.read((char*)&dim, 4);
    
    // 计算 N
    in.seekg(0, std::ios::end);
    size_t fsize = in.tellg();
    in.seekg(0, std::ios::beg);
    
    size_t row_size = 4 + dim * 4;
    size_t N = fsize / row_size;

    data.N = (unsigned)N;
    data.dim = dim;

    // 打印一次元数据即可
    std::cout << "   -> N=" << data.N << ", dim=" << data.dim << std::endl;

    data.val = new float* [data.N];
    for (unsigned i = 0; i < data.N; ++i) {
        data.val[i] = new float[data.dim];
        in.seekg(4, std::ios::cur);
        in.read((char*)data.val[i], sizeof(float) * data.dim);
    }

    data.query = nullptr; 
    in.close();
}

// 全部置空，防止误调用产生日志
void Preprocess::ben_make() {}
void Preprocess::ben_save() {}
void Preprocess::ben_correct() {}
void Preprocess::ben_correct_inverse() {}
void Preprocess::ben_load() {}
void Preprocess::ben_create() {}

void Preprocess::showDataset() {
    std::cout << "Dataset Info: N=" << data.N << " dim=" << data.dim << std::endl;
}

Preprocess::~Preprocess() {
    if (data.val) {
        for (unsigned i = 0; i < data.N; i++) delete[] data.val[i];
        delete[] data.val;
    }
}

Parameter::Parameter(Preprocess& prep, unsigned L_, unsigned K_, float rmin_) {
    N = prep.data.N;
    dim = prep.data.dim;
    L = L_;
    K = K_;
    MaxSize = 5;
    R_min = rmin_;
}
Parameter::~Parameter() {}
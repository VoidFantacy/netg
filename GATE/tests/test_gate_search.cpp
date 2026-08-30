#include <efanna2e/index_nsg.h>
#include <efanna2e/util.h>
#include <hnswlib/hnswlib.h>
#include <chrono>
#include <vector>
#include <iostream>
#include <fstream>
#include <cassert>
#include <cmath>
#include <iomanip>
#include <numeric>
#include <algorithm>
#include <set>
#include <thread>
#include <omp.h>
#include <stdlib.h>

// ==================== 数据加载 ====================

void load_data(const char* filename, float*& data, unsigned& num, unsigned& dim) {
  std::ifstream in(filename, std::ios::binary);
  if (!in.is_open()) {
    std::cerr << "Error: Cannot open file " << filename << std::endl;
    exit(-1);
  }
  in.read((char*)&dim, 4);
  in.seekg(0, std::ios::end);
  size_t fsize = (size_t)in.tellg();
  num = (unsigned)(fsize / (dim * 4 + 4));
  data = new float[num * dim];
  in.seekg(0, std::ios::beg);
  for (size_t i = 0; i < num; i++) {
    in.seekg(4, std::ios::cur);
    in.read((char*)(data + i * dim), dim * 4);
  }
  in.close();
  std::cout << "Loaded " << filename << " (" << num << "x" << dim << ")" << std::endl;
}

void load_gt(const char* filename, unsigned*& data, unsigned& num, unsigned& dim) {
  std::ifstream in(filename, std::ios::binary);
  if (!in.is_open()) {
    std::cerr << "Error: Cannot open GT file " << filename << std::endl;
    exit(-1);
  }
  in.read((char*)&dim, 4);
  in.seekg(0, std::ios::end);
  size_t fsize = (size_t)in.tellg();
  num = (unsigned)(fsize / (dim * 4 + 4));
  data = new unsigned[num * dim];
  in.seekg(0, std::ios::beg);
  for (size_t i = 0; i < num; i++) {
    in.seekg(4, std::ios::cur);
    in.read((char*)(data + i * dim), dim * 4);
  }
  in.close();
  std::cout << "Loaded GT " << filename << " (" << num << "x" << dim << ")" << std::endl;
}

// ==================== 核心评估: Intersection Recall@K ====================
// 计算 Top-K 结果与 GT Top-K 的重叠率
float calculate_intersection_recall(const std::vector<std::vector<unsigned>>& results, const unsigned* gt, unsigned gt_dim, unsigned K) {
    if (results.empty()) return 0.0f;
    size_t nq = results.size();
    size_t total_hit = 0;

    for (size_t i = 0; i < nq; ++i) {
        // 使用 set 加速查找 (GT 通常是排好序的，但为了通用我们用 set)
        // 注意：GT 文件可能有 100 个邻居，我们也只取前 K 个做对比
        std::set<unsigned> gt_set;
        for (unsigned j = 0; j < K && j < gt_dim; j++) {
            gt_set.insert(gt[i * gt_dim + j]);
        }
        
        unsigned hit = 0;
        for (unsigned val : results[i]) {
            if (gt_set.count(val)) {
                hit++;
            }
        }
        total_hit += hit;
    }
    // 平均召回率 = (总命中数 / K) / 查询数
    return (float)total_hit / (nq * K);
}

// ==================== 主程序 ====================

int main(int argc, char** argv) {
  // 1. 强制单线程 (Double Check)
  setenv("OMP_NUM_THREADS", "1", 1);
  omp_set_num_threads(1);

  if (argc < 9) {
    std::cout << "Usage: " << argv[0]
              << " <base> <query> <nsg> <L> <K> <hubs.txt> <hub_emb> <result>"
              << " [gt] [query_emb]" << std::endl;
    exit(-1);
  }

  // 加载数据
  float* data_load = NULL;
  unsigned points_num, dim;
  load_data(argv[1], data_load, points_num, dim);

  float* query_load = NULL;
  unsigned query_num, query_dim;
  load_data(argv[2], query_load, query_num, query_dim);

  // 加载 Hub Embedding Index (HNSW for routing)
  // 作者原始实现使用 CosSpace (真余弦距离)，embedding 维度 == query 维度
  // 单塔模型：直接用原始 query 搜索 hub embedding，无需 QueryEncoder
  unsigned emb_num, emb_dim;
  float* emb_data = nullptr;
  hnswlib::HierarchicalNSW<float>* cos_index = nullptr;
  hnswlib::CosSpace* space = nullptr;

  load_data(argv[7], emb_data, emb_num, emb_dim);
  space = new hnswlib::CosSpace(emb_dim);
  cos_index = new hnswlib::HierarchicalNSW<float>(space, emb_num, 16, 200);
  
  for (int i = 0; i < (int)emb_num; i++) {
    cos_index->addPoint(emb_data + i * emb_dim, i);
  }

  // emb_dim 必须等于 query_dim (单塔模型要求)
  if (emb_dim != query_dim) {
    std::cerr << "Warning: emb_dim (" << emb_dim << ") != query_dim (" << query_dim 
              << "). HNSW routing may be incorrect." << std::endl;
  }

  // 加载 NSG Index
  efanna2e::IndexNSG index(dim, points_num, efanna2e::L2, nullptr);
  index.Load(argv[3]);
  index.LoadKmeans(argv[6]);

  // 加载 GT
  unsigned* gt_load = NULL;
  unsigned gt_num, gt_dim_val;
  if (argc >= 10) load_gt(argv[9], gt_load, gt_num, gt_dim_val);

  unsigned K = (unsigned)atoi(argv[5]); // Recall@K (e.g. 100), passed via argv[5]

  // 对齐您的参数列表
  std::vector<unsigned> search_Ls = {
      1, 2, 4, 8, 16, 32, 64, 100, 128, 150, 200, 250, 300, 400, 512, 600, 800, 1024, 1200, 1500
  };
  
  int runs = 10; // 严格 10 次平均

  std::cout << "\n==================== GATE Fair Benchmark (Intersection R@" << K << ") ====================" << std::endl;
  std::cout << "Config: Runs=" << runs << " (No Warmup), Single Thread, L={10...1500}" << std::endl;
  std::cout << "--------------------------------------------------------------------------------" << std::endl;
  std::cout << std::setw(6) << "L" << " | "
            << std::setw(12) << "QPS" << " | "
            << std::setw(12) << "Recall" << " | "
            << std::setw(12) << "Time(ms)" 
            << std::endl;
  std::cout << "-------+--------------+--------------+--------------" << std::endl;

  std::vector<std::vector<unsigned>> res(query_num);
  for(unsigned i=0; i<query_num; ++i) res[i].resize(K);

  // 预分配 eps / hop_count，避免每次 query 堆分配
  std::vector<unsigned> eps;
  eps.reserve(8);
  std::vector<unsigned> hop_count(1, 0); // 给 Search 一个合法的写入地址

  // 打印 eps 调试信息
  std::cout << "[INFO] iter2_num=" << index.iter2_num
            << " iter2_eps.size()=" << index.iter2_eps.size() << std::endl;

  efanna2e::Parameters paras;

  for (unsigned L : search_Ls) {
      if (L < K) continue; // Skip invalid L

      paras.Set<unsigned>("L_search", L);
      paras.Set<unsigned>("P_search", L);

      double total_time_ms = 0.0;
      float last_recall = 0.0f;

      // --- 循环 10 次，无 warmup，无 sleep ---
      for (int r = 0; r < runs; r++) {

          auto start = std::chrono::high_resolution_clock::now();

          for (unsigned i = 0; i < query_num; i++) {
              eps.clear();

              // 1. Routing: 用原始 query 在 hub embedding 空间搜索入口点
              auto pq = cos_index->searchKnn(query_load + i * query_dim, 3);
              while (!pq.empty()) {
                  unsigned ep_id = (unsigned)pq.top().second;
                  pq.pop();
                  if (index.iter2_num > 0
                      && ep_id < (unsigned)index.iter2_eps.size()
                      && !index.iter2_eps[ep_id].empty()) {
                      // iter2_eps[ep_id] 是该 hub 的 entry point 列表
                      eps.push_back(index.iter2_eps[ep_id][0]);
                  }
              }

              // 2. Graph Search
              index.Search(query_load + i * dim, data_load, K, paras,
                           res[i].data(), hop_count.data(), eps);
          }

          auto end = std::chrono::high_resolution_clock::now();
          total_time_ms += std::chrono::duration<double, std::milli>(end - start).count();
      }

      double avg_time_ms = total_time_ms / runs;
      double qps = query_num / (avg_time_ms / 1000.0);

      if (gt_load)
          last_recall = calculate_intersection_recall(res, gt_load, gt_dim_val, K);

      std::cout << std::setw(6) << L << " | "
                << std::setw(12) << std::fixed << std::setprecision(1) << qps << " | "
                << std::setw(12) << std::setprecision(4) << last_recall << " | "
                << std::setw(12) << std::setprecision(2) << avg_time_ms
                << std::endl;
  }
  std::cout << "================================================================================" << std::endl;

  delete cos_index;
  delete space;
  delete[] data_load;
  delete[] query_load;
  delete[] emb_data;
  if(gt_load) delete[] gt_load;

  return 0;
}
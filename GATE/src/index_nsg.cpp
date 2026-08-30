#include "efanna2e/index_nsg.h"

#include <omp.h>
#include <bitset>
#include <chrono>
#include <cmath>
#include <queue>
#include <boost/dynamic_bitset.hpp>
#include <iostream> 
#include <fstream> 
#include <sstream> 
#include <cstring> // for memcpy

#include "efanna2e/exceptions.h"
#include "efanna2e/parameters.h"
#include "hnswlib/hnswlib.h"

namespace efanna2e {
#define _CONTROL_NUM 100

IndexNSG::IndexNSG(const size_t dimension, const size_t n, Metric m,
                   Index *initializer)
    : Index(dimension, n, m), initializer_{initializer} {
      counter.store(0);
      navigate_counter.store(0);
      vertex_visit_counter.resize(n);
      std::fill(vertex_visit_counter.begin(), vertex_visit_counter.end(), 0);
    }

IndexNSG::~IndexNSG() {
    if (distance_ != nullptr) {
        delete distance_;
        distance_ = nullptr;
    }
    if (initializer_ != nullptr) {
        delete initializer_;
        initializer_ = nullptr;
    }
    if (opt_graph_ != nullptr) {
        delete[] opt_graph_; // Fixed: delete[]
        opt_graph_ = nullptr;
    }
}

void IndexNSG::Save(const char *filename) {
  std::ofstream out(filename, std::ios::binary | std::ios::out);
  assert(final_graph_.size() == nd_);

  out.write((char *)&width, sizeof(unsigned));
  out.write((char *)&ep_, sizeof(unsigned));
  for (unsigned i = 0; i < nd_; i++) {
    unsigned GK = (unsigned)final_graph_[i].size();
    out.write((char *)&GK, sizeof(unsigned));
    out.write((char *)final_graph_[i].data(), GK * sizeof(unsigned));
  }
  out.close();
}

void IndexNSG::Load(const char *filename) {
  std::ifstream in(filename, std::ios::binary);
  in.read((char *)&width, sizeof(unsigned));
  in.read((char *)&ep_, sizeof(unsigned));
  unsigned cc = 0;
  while (!in.eof()) {
    unsigned k;
    in.read((char *)&k, sizeof(unsigned));
    if (in.eof()) break;
    cc += k;
    std::vector<unsigned> tmp(k);
    in.read((char *)tmp.data(), k * sizeof(unsigned));
    final_graph_.push_back(tmp);
  }
  cc /= nd_;
  std::cout << "[DEBUG] (IndexNSG::Load) NSG Graph loaded. Nodes: " << final_graph_.size() << std::endl;
}

// 【关键修复】兼容变长邻居表的读取函数
void IndexNSG::Load_nn_graph(const char *filename) {
  std::cout << "[DEBUG] (IndexNSG) Opening KNN Graph file: " << filename << std::endl;
  std::ifstream in(filename, std::ios::binary);
  if(!in.is_open()) {
      std::cerr << "[ERROR] Cannot open graph file: " << filename << std::endl;
      exit(-1);
  }

  final_graph_.clear();
  final_graph_.reserve(nd_); 
  
  unsigned long long total_edges = 0;
  unsigned count = 0;

  while (in.peek() != EOF) {
    unsigned k;
    if(!in.read((char *)&k, sizeof(unsigned))) break;
    
    std::vector<unsigned> tmp(k);
    if (k > 0) {
      if(!in.read((char *)tmp.data(), k * sizeof(unsigned))) {
          std::cerr << "[ERROR] Short read at node " << count << std::endl;
          break;
      }
    }
    final_graph_.push_back(tmp);
    total_edges += k;
    count++;
  }
  in.close();
  
  std::cout << "[DEBUG] Load_nn_graph Finished. Nodes: " << final_graph_.size() << ", Edges: " << total_edges << std::endl;
}

void IndexNSG::LoadTwoIterIndex(hnswlib::HierarchicalNSW<float>* cos_index) {
  this->two_iter_index = cos_index;
}

void IndexNSG::LoadEps(float* eps_load) {
  this->eps_data_ = eps_load;
}

// 【关键修复】加载文本格式的 Hub 信息
void IndexNSG::LoadKmeans(const char *filename) {
  std::cout << "[DEBUG] (IndexNSG::LoadKmeans) Loading from: " << filename << std::endl;
  std::ifstream in(filename); 
  if (!in.is_open()) {
      std::cerr << "[ERROR] Failed to open Kmeans file: " << filename << std::endl;
      exit(-1);
  }

  std::string line;
  // 1. Header
  {
    std::getline(in, line);
    std::istringstream iss(line);
    iss >> iter1_num >> iter2_num >> dim;
    std::cout << "[DEBUG] Header: iter1=" << iter1_num << ", iter2=" << iter2_num << ", dim=" << dim << std::endl;
    if (iter1_num == 0 || iter2_num == 0) {
        std::cerr << "[ERROR] Invalid header! iter1 or iter2 is 0." << std::endl;
        exit(-1);
    }
  }

  // 2. Hub Vectors
  iter1_centroids.resize(iter1_num);
  for (unsigned i = 0; i < iter1_num; i++) {
      std::getline(in, line);
      while(line.empty() && !in.eof()) std::getline(in, line); // skip empty lines
      
      std::istringstream iss(line);
      iter1_centroids[i].reserve(dim);
      for (unsigned j = 0; j < dim; j++) {
          float token;
          iss >> token;
          iter1_centroids[i].push_back(token);
      }
  }

  // 3. Entry Points (Hub -> Node ID)
  {
    iter2_eps.resize(iter1_num);
    for (unsigned i = 0; i < iter1_num; i++) {
        iter2_eps[i].reserve(iter2_num);
        // For flat structure, iter2_num usually 1, so we read 1 line per hub
        for(unsigned j=0; j<iter2_num; ++j) {
            std::getline(in, line);
            while(line.empty() && !in.eof()) std::getline(in, line);

            std::istringstream iss(line);
            unsigned ep;
            iss >> ep;
            iter2_eps[i].push_back(ep);
        }
    }
  }
  std::cout << "[DEBUG] Loaded " << iter2_eps.size() << " EP groups." << std::endl;

  ep_counter.resize(iter1_num * iter2_num);
  std::fill(ep_counter.begin(), ep_counter.end(), 0);
  in.close();
}

void IndexNSG::set_ep(int index) {
  if (index == -1) return;
  if (index < 0 || index >= (int)(iter1_num * iter2_num)) exit(0);
  auto iter1_index = index / iter2_num;
  auto iter2_index = index % iter2_num;
  ep_ = iter2_eps[iter1_index][iter2_index];
}

void IndexNSG::get_neighbors(const float *query, const Parameters &parameter,
                             std::vector<Neighbor> &retset,
                             std::vector<Neighbor> &fullset) {
  unsigned L = parameter.Get<unsigned>("L");

  retset.resize(L + 1);
  std::vector<unsigned> init_ids(L);
  
  boost::dynamic_bitset<> flags{nd_, 0};
  L = 0;
  for (unsigned i = 0; i < init_ids.size() && i < final_graph_[ep_].size(); i++) {
    init_ids[i] = final_graph_[ep_][i];
    flags[init_ids[i]] = true;
    L++;
  }
  while (L < init_ids.size()) {
    unsigned id = rand() % nd_;
    if (flags[id]) continue;
    init_ids[L] = id;
    L++;
    flags[id] = true;
  }

  L = 0;
  for (unsigned i = 0; i < init_ids.size(); i++) {
    unsigned id = init_ids[i];
    if (id >= nd_) continue;
    float dist = distance_->compare(data_ + dimension_ * (size_t)id, query,
                                    (unsigned)dimension_);
    retset[i] = Neighbor(id, dist, true);
    L++;
  }

  std::sort(retset.begin(), retset.begin() + L);
  int k = 0;
  while (k < (int)L) {
    int nk = L;

    if (retset[k].flag) {
      retset[k].flag = false;
      unsigned n = retset[k].id;

      for (unsigned m = 0; m < final_graph_[n].size(); ++m) {
        unsigned id = final_graph_[n][m];
        if (flags[id]) continue;
        flags[id] = 1;

        float dist = distance_->compare(query, data_ + dimension_ * (size_t)id,
                                        (unsigned)dimension_);
        Neighbor nn(id, dist, true);
        fullset.push_back(nn);
        if (dist >= retset[L - 1].distance) continue;
        int r = InsertIntoPool(retset.data(), L, nn);

        if (L + 1 < retset.size()) ++L;
        if (r < nk) nk = r;
      }
    }
    if (nk <= k) k = nk;
    else ++k;
  }
}

void IndexNSG::get_neighbors(const float *query, const Parameters &parameter,
                             boost::dynamic_bitset<> &flags,
                             std::vector<Neighbor> &retset,
                             std::vector<Neighbor> &fullset) {
  unsigned L = parameter.Get<unsigned>("L");

  retset.resize(L + 1);
  std::vector<unsigned> init_ids(L);

  L = 0;
  for (unsigned i = 0; i < init_ids.size() && i < final_graph_[ep_].size(); i++) {
    init_ids[i] = final_graph_[ep_][i];
    flags[init_ids[i]] = true;
    L++;
  }
  while (L < init_ids.size()) {
    unsigned id = rand() % nd_;
    if (flags[id]) continue;
    init_ids[L] = id;
    L++;
    flags[id] = true;
  }

  L = 0;
  for (unsigned i = 0; i < init_ids.size(); i++) {
    unsigned id = init_ids[i];
    if (id >= nd_) continue;
    float dist = distance_->compare(data_ + dimension_ * (size_t)id, query,
                                    (unsigned)dimension_);
    retset[i] = Neighbor(id, dist, true);
    fullset.push_back(retset[i]);
    L++;
  }

  std::sort(retset.begin(), retset.begin() + L);
  int k = 0;
  while (k < (int)L) {
    int nk = L;

    if (retset[k].flag) {
      retset[k].flag = false;
      unsigned n = retset[k].id;

      for (unsigned m = 0; m < final_graph_[n].size(); ++m) {
        unsigned id = final_graph_[n][m];
        if (flags[id]) continue;
        flags[id] = 1;

        float dist = distance_->compare(query, data_ + dimension_ * (size_t)id,
                                        (unsigned)dimension_);
        Neighbor nn(id, dist, true);
        fullset.push_back(nn);
        if (dist >= retset[L - 1].distance) continue;
        int r = InsertIntoPool(retset.data(), L, nn);

        if (L + 1 < retset.size()) ++L;
        if (r < nk) nk = r;
      }
    }
    if (nk <= k) k = nk;
    else ++k;
  }
}

void IndexNSG::init_graph(const Parameters &parameters) {
  float *center = new float[dimension_];
  for (unsigned j = 0; j < dimension_; j++) center[j] = 0;
  for (unsigned i = 0; i < nd_; i++) {
    for (unsigned j = 0; j < dimension_; j++) {
      center[j] += data_[i * dimension_ + j];
    }
  }
  for (unsigned j = 0; j < dimension_; j++) {
    center[j] /= nd_;
  }
  std::vector<Neighbor> tmp, pool;
  ep_ = rand() % nd_;
  get_neighbors(center, parameters, tmp, pool);
  ep_ = tmp[0].id;
  delete[] center; // Fixed delete[]
}

void IndexNSG::sync_prune(unsigned q, std::vector<Neighbor> &pool,
                          const Parameters &parameter,
                          boost::dynamic_bitset<> &flags,
                          SimpleNeighbor *cut_graph_) {
  unsigned range = parameter.Get<unsigned>("R");
  unsigned maxc = parameter.Get<unsigned>("C");
  width = range;
  unsigned start = 0;

  for (unsigned nn = 0; nn < final_graph_[q].size(); nn++) {
    unsigned id = final_graph_[q][nn];
    if (flags[id]) continue;
    float dist =
        distance_->compare(data_ + dimension_ * (size_t)q,
                           data_ + dimension_ * (size_t)id, (unsigned)dimension_);
    pool.push_back(Neighbor(id, dist, true));
  }

  std::sort(pool.begin(), pool.end());
  std::vector<Neighbor> result;
  if (pool[start].id == q) start++;
  result.push_back(pool[start]);

  while (result.size() < range && (++start) < pool.size() && start < maxc) {
    auto &p = pool[start];
    bool occlude = false;
    for (unsigned t = 0; t < result.size(); t++) {
      if (p.id == result[t].id) {
        occlude = true;
        break;
      }
      float djk = distance_->compare(data_ + dimension_ * (size_t)result[t].id,
                                     data_ + dimension_ * (size_t)p.id,
                                     (unsigned)dimension_);
      if (djk < p.distance) {
        occlude = true;
        break;
      }
    }
    if (!occlude) result.push_back(p);
  }

  SimpleNeighbor *des_pool = cut_graph_ + (size_t)q * (size_t)range;
  for (size_t t = 0; t < result.size(); t++) {
    des_pool[t].id = result[t].id;
    des_pool[t].distance = result[t].distance;
  }
  if (result.size() < range) {
    des_pool[result.size()].distance = -1;
  }
}

void IndexNSG::InterInsert(unsigned n, unsigned range,
                           std::vector<std::mutex> &locks,
                           SimpleNeighbor *cut_graph_) {
  SimpleNeighbor *src_pool = cut_graph_ + (size_t)n * (size_t)range;
  for (size_t i = 0; i < range; i++) {
    if (src_pool[i].distance == -1) break;

    SimpleNeighbor sn(n, src_pool[i].distance);
    size_t des = src_pool[i].id;
    SimpleNeighbor *des_pool = cut_graph_ + des * (size_t)range;

    std::vector<SimpleNeighbor> temp_pool;
    int dup = 0;
    {
      LockGuard guard(locks[des]);
      for (size_t j = 0; j < range; j++) {
        if (des_pool[j].distance == -1) break;
        if (n == des_pool[j].id) {
          dup = 1;
          break;
        }
        temp_pool.push_back(des_pool[j]);
      }
    }
    if (dup) continue;

    temp_pool.push_back(sn);
    if (temp_pool.size() > range) {
      std::vector<SimpleNeighbor> result;
      unsigned start = 0;
      std::sort(temp_pool.begin(), temp_pool.end());
      result.push_back(temp_pool[start]);
      while (result.size() < range && (++start) < temp_pool.size()) {
        auto &p = temp_pool[start];
        bool occlude = false;
        for (unsigned t = 0; t < result.size(); t++) {
          if (p.id == result[t].id) {
            occlude = true;
            break;
          }
          float djk = distance_->compare(data_ + dimension_ * (size_t)result[t].id,
                                         data_ + dimension_ * (size_t)p.id,
                                         (unsigned)dimension_);
          if (djk < p.distance) {
            occlude = true;
            break;
          }
        }
        if (!occlude) result.push_back(p);
      }
      {
        LockGuard guard(locks[des]);
        for (unsigned t = 0; t < result.size(); t++) {
          des_pool[t] = result[t];
        }
      }
    } else {
      LockGuard guard(locks[des]);
      for (unsigned t = 0; t < range; t++) {
        if (des_pool[t].distance == -1) {
          des_pool[t] = sn;
          if (t + 1 < range) des_pool[t + 1].distance = -1;
          break;
        }
      }
    }
  }
}

void IndexNSG::Link(const Parameters &parameters, SimpleNeighbor *cut_graph_) {
  unsigned range = parameters.Get<unsigned>("R");
  std::vector<std::mutex> locks(nd_);

#pragma omp parallel
  {
    std::vector<Neighbor> pool, tmp;
    boost::dynamic_bitset<> flags{nd_, 0};
#pragma omp for schedule(dynamic, 100)
    for (unsigned n = 0; n < nd_; ++n) {
      pool.clear();
      tmp.clear();
      flags.reset();
      get_neighbors(data_ + dimension_ * n, parameters, flags, tmp, pool);
      sync_prune(n, pool, parameters, flags, cut_graph_);
    }
  }

#pragma omp for schedule(dynamic, 100)
  for (unsigned n = 0; n < nd_; ++n) {
    InterInsert(n, range, locks, cut_graph_);
  }
}

void IndexNSG::Build(size_t n, const float *data, const Parameters &parameters) {
  std::string nn_graph_path = parameters.Get<std::string>("nn_graph_path");
  unsigned range = parameters.Get<unsigned>("R");
  
  std::cout << "[DEBUG] (IndexNSG) Build called. Loading NN Graph..." << std::endl;
  Load_nn_graph(nn_graph_path.c_str());
  
  data_ = data;
  init_graph(parameters);

  std::cout << "[DEBUG] (IndexNSG) Allocating cut_graph..." << std::endl;
  SimpleNeighbor *cut_graph_ = new SimpleNeighbor[nd_ * (size_t)range];
  Link(parameters, cut_graph_);
  final_graph_.resize(nd_);

  for (size_t i = 0; i < nd_; i++) {
    SimpleNeighbor *pool = cut_graph_ + i * (size_t)range;
    unsigned pool_size = 0;
    for (unsigned j = 0; j < range; j++) {
      if (pool[j].distance == -1) break;
      pool_size = j;
    }
    pool_size++;
    final_graph_[i].resize(pool_size);
    for (unsigned j = 0; j < pool_size; j++) {
      final_graph_[i][j] = pool[j].id;
    }
  }

  tree_grow(parameters);

  unsigned max = 0, min = 1e6, avg = 0;
  for (size_t i = 0; i < nd_; i++) {
    auto size = final_graph_[i].size();
    max = max < size ? size : max;
    min = min > size ? size : min;
    avg += size;
  }
  avg /= 1.0 * nd_;
  printf("Degree Statistics: Max = %d, Min = %d, Avg = %d\n", max, min, avg);

  has_built = true;
  delete[] cut_graph_; // Fixed delete[]
}

unsigned IndexNSG::get_opt_ep(const float* query) {
  unsigned window_size = 1;

  for (unsigned i = 0; i < iter1_centroids.size(); i++) {
    auto &centroid = iter1_centroids[i];
    _mm_prefetch(centroid.data(), _MM_HINT_T0);
  }

  std::vector<std::pair<float, unsigned>> centroid_eps;
  centroid_eps.reserve(iter1_centroids.size());

  for (unsigned i = 0; i < iter1_centroids.size(); i++) {
    auto &centroid = iter1_centroids[i];
    float dist = distance_->compare(centroid.data(), query, (unsigned)dimension_);
    centroid_eps.push_back({dist, i});
  }
  std::sort(centroid_eps.begin(), centroid_eps.end());

  for (unsigned i = 0; i < window_size; i++) {
    unsigned centroid_ep = centroid_eps[i].second;
    for (unsigned sub_centroid : iter2_eps[centroid_ep]) {
      _mm_prefetch(data_ + dimension_ * sub_centroid, _MM_HINT_T0);
    }
  }

  unsigned sub_centroid_ep = -1;
  float min_dist = 1e15;

  for (unsigned i = 0; i < window_size; i++) {
      unsigned centroid_ep = centroid_eps[i].second;
      for (unsigned sub_centroid : iter2_eps[centroid_ep]) {
        float dist = distance_->compare(data_ + dimension_ * sub_centroid, query, (unsigned)dimension_);
      
        if (dist < min_dist) {
          min_dist = dist;
          sub_centroid_ep = sub_centroid;
        }
    }
  }
  return sub_centroid_ep;
}

unsigned IndexNSG::get_opt_ep_with_opt_graph(const float* query) {
  DistanceFastL2 *dist_fast = (DistanceFastL2 *)distance_;
  unsigned centroid_ep = -1;
  float min_dist = 1e15;

  for (unsigned i = 0; i < iter1_centroids.size(); i++) {
    auto &centroid = iter1_centroids[i];
    float *data = centroid.data();
    float norm = *data;
    data++;
    float dist = dist_fast->compare(query, data, norm, (unsigned)dimension_);

    if (dist < min_dist) {
      centroid_ep = i;
      min_dist = dist;
    }
  }

  unsigned sub_centroid_ep = -1;
  min_dist = 1e15;
  for (unsigned sub_centroid : iter2_eps[centroid_ep]) {
    float *x = (float *)(opt_graph_ + node_size * sub_centroid);
    float norm_x = *x;
    x++;
    float dist = dist_fast->compare(x, query, norm_x, (unsigned)dimension_);
  
    if (dist < min_dist) {
      min_dist = dist;
      sub_centroid_ep = sub_centroid;
    }
  }
  return sub_centroid_ep;
}

// 【关键修复】Search: 加上了 iter2_num != 0 的检查和越界保护
void IndexNSG::Search(const float *query, const float *x, size_t K,
                      const Parameters &parameters, unsigned *indices, unsigned *hc, std::vector<unsigned>& eps) {
    // 获取搜索深度 L
    unsigned L = parameters.Get<unsigned>("L_search");
    std::vector<Neighbor> retset(L + 1);
    std::vector<unsigned> init_ids(L);
    boost::dynamic_bitset<> flags{nd_, 0};

    unsigned num_ids = 0;

    // ==========================================
    // 【修改核心】不再使用 queue 和 BFS，严格计算初始入口点的距离
    // ==========================================
    for (unsigned ep : eps) {
        if (num_ids >= L) break;
        if (!flags[ep]) {
            flags[ep] = 1;
            // 计算 Query 和该入口点的真实欧氏距离
            float dist = distance_->compare(query, x + ep * dimension_, dimension_);
            retset[num_ids] = Neighbor(ep, dist, true);
            init_ids[num_ids] = ep;
            num_ids++;
        }
    }

    // 对初始池子进行升序排序
    std::sort(retset.begin(), retset.begin() + num_ids);

    // ==========================================
    // 严谨的贪婪最佳优先搜索 (Greedy Best-First Search)
    // ==========================================
    int k = 0;
    unsigned hop_count = 0; // 用于记录跳数

    // 注意：这里的循环条件是 k < (int)num_ids，因为初始点可能不足 L 个
    while (k < (int)num_ids) {
        int updated_pos = L;

        if (retset[k].flag) {
            retset[k].flag = false;
            unsigned n = retset[k].id;
            hop_count++; // 记录一次节点扩展

            // 遍历当前节点的所有图上邻居
            for (unsigned m = 0; m < final_graph_[n].size(); ++m) {
                unsigned id = final_graph_[n][m];
                if (flags[id]) continue;
                flags[id] = 1;
                
                // 计算邻居距离
                float dist = distance_->compare(query, x + id * dimension_, dimension_);
                
                // 如果距离大于当前池子里最差的，并且池子已经满了，就直接丢弃
                if (dist >= retset[L - 1].distance && num_ids >= L) continue;

                Neighbor nn(id, dist, true);
                
                // 插入到有序池子中，返回插入的位置
                int r = InsertIntoPool(retset.data(), num_ids, nn);

                if (num_ids < L) num_ids++; // 如果池子没满，总数加1
                if (r < L) updated_pos = std::min(updated_pos, r);
            }
        }
        // 如果有更好的点插入在了当前 k 前面，就回退 k；否则继续看下一个
        k = (updated_pos <= k) ? updated_pos : (k + 1);
    }
    
    // ==========================================
    // 结果输出
    // ==========================================
    for (size_t i = 0; i < K; i++) {
        indices[i] = retset[i].id;
    }
    
    // 如果外部传入了 hc 指针，记录搜索跳数
    if (hc != nullptr) {
        hc[0] = hop_count;
    }
}

void IndexNSG::SearchWithOptGraph(const float *query, size_t K,
                                  const Parameters &parameters, unsigned *indices) {
  unsigned L = parameters.Get<unsigned>("L_search");
  DistanceFastL2 *dist_fast = (DistanceFastL2 *)distance_;

  std::vector<Neighbor> retset(L + 1);
  std::vector<unsigned> init_ids(L);

  auto ep = ep_;
  ep = get_opt_ep_with_opt_graph(query);

  boost::dynamic_bitset<> flags{nd_, 0};
  unsigned tmp_l = 0;
  unsigned *neighbors = (unsigned *)(opt_graph_ + node_size * ep + data_len);
  unsigned MaxM_ep = *neighbors;
  neighbors++;

  for (; tmp_l < L && tmp_l < MaxM_ep; tmp_l++) {
    init_ids[tmp_l] = neighbors[tmp_l];
    flags[init_ids[tmp_l]] = true;
  }

  while (tmp_l < L) {
    unsigned id = rand() % nd_;
    if (flags[id]) continue;
    flags[id] = true;
    init_ids[tmp_l] = id;
    tmp_l++;
  }

  for (unsigned i = 0; i < init_ids.size(); i++) {
    unsigned id = init_ids[i];
    if (id >= nd_) continue;
    _mm_prefetch(opt_graph_ + node_size * id, _MM_HINT_T0);
  }
  L = 0;
  for (unsigned i = 0; i < init_ids.size(); i++) {
    unsigned id = init_ids[i];
    if (id >= nd_) continue;
    float *x = (float *)(opt_graph_ + node_size * id);
    float norm_x = *x;
    x++;
    float dist = dist_fast->compare(x, query, norm_x, (unsigned)dimension_);
    retset[i] = Neighbor(id, dist, true);
    flags[id] = true;
    L++;
  }

  std::sort(retset.begin(), retset.begin() + L);
  int k = 0;
  while (k < (int)L) {
    int nk = L;

    if (retset[k].flag) {
      retset[k].flag = false;
      unsigned n = retset[k].id;

      _mm_prefetch(opt_graph_ + node_size * n + data_len, _MM_HINT_T0);
      unsigned *neighbors = (unsigned *)(opt_graph_ + node_size * n + data_len);
      unsigned MaxM = *neighbors;
      neighbors++;
      for (unsigned m = 0; m < MaxM; ++m)
        _mm_prefetch(opt_graph_ + node_size * neighbors[m], _MM_HINT_T0);
      for (unsigned m = 0; m < MaxM; ++m) {
        unsigned id = neighbors[m];
        if (flags[id]) continue;
        flags[id] = 1;
        float *data = (float *)(opt_graph_ + node_size * id);
        float norm = *data;
        data++;
        float dist = dist_fast->compare(query, data, norm, (unsigned)dimension_);
        if (dist >= retset[L - 1].distance) continue;
        Neighbor nn(id, dist, true);
        int r = InsertIntoPool(retset.data(), L, nn);

        if (r < nk) nk = r;
      }
    }
    if (nk <= k)
      k = nk;
    else
      ++k;
  }
  for (size_t i = 0; i < K; i++) {
    indices[i] = retset[i].id;
  }
}

void IndexNSG::OptimizeGraph(float *data) {
  data_ = data;
  data_len = (dimension_ + 1) * sizeof(float);
  neighbor_len = (width + 1) * sizeof(unsigned);
  node_size = data_len + neighbor_len;
  opt_graph_ = (char *)malloc(node_size * nd_);
  DistanceFastL2 *dist_fast = (DistanceFastL2 *)distance_;
  for (unsigned i = 0; i < nd_; i++) {
    char *cur_node_offset = opt_graph_ + i * node_size;
    float cur_norm = dist_fast->norm(data_ + i * dimension_, dimension_);
    std::memcpy(cur_node_offset, &cur_norm, sizeof(float));
    std::memcpy(cur_node_offset + sizeof(float), data_ + i * dimension_,
                data_len - sizeof(float));

    cur_node_offset += data_len;
    unsigned k = final_graph_[i].size();
    std::memcpy(cur_node_offset, &k, sizeof(unsigned));
    std::memcpy(cur_node_offset + sizeof(unsigned), final_graph_[i].data(),
                k * sizeof(unsigned));
    std::vector<unsigned>().swap(final_graph_[i]);
  }
  CompactGraph().swap(final_graph_);
}

void IndexNSG::DFS(boost::dynamic_bitset<> &flag, unsigned root, unsigned &cnt) {
  unsigned tmp = root;
  std::stack<unsigned> s;
  s.push(root);
  if (!flag[root]) cnt++;
  flag[root] = true;
  while (!s.empty()) {
    unsigned next = nd_ + 1;
    for (unsigned i = 0; i < final_graph_[tmp].size(); i++) {
      if (flag[final_graph_[tmp][i]] == false) {
        next = final_graph_[tmp][i];
        break;
      }
    }
    if (next == (nd_ + 1)) {
      s.pop();
      if (s.empty()) break;
      tmp = s.top();
      continue;
    }
    tmp = next;
    flag[tmp] = true;
    s.push(tmp);
    cnt++;
  }
}

void IndexNSG::findroot(boost::dynamic_bitset<> &flag, unsigned &root,
                        const Parameters &parameter) {
  unsigned id = nd_;
  for (unsigned i = 0; i < nd_; i++) {
    if (flag[i] == false) {
      id = i;
      break;
    }
  }

  if (id == nd_) return; 

  std::vector<Neighbor> tmp, pool;
  get_neighbors(data_ + dimension_ * id, parameter, tmp, pool);
  std::sort(pool.begin(), pool.end());

  unsigned found = 0;
  for (unsigned i = 0; i < pool.size(); i++) {
    if (flag[pool[i].id]) {
      root = pool[i].id;
      found = 1;
      break;
    }
  }
  if (found == 0) {
    while (true) {
      unsigned rid = rand() % nd_;
      if (flag[rid]) {
        root = rid;
        break;
      }
    }
  }
  final_graph_[root].push_back(id);
}

void IndexNSG::tree_grow(const Parameters &parameter) {
  unsigned root = ep_;
  boost::dynamic_bitset<> flags{nd_, 0};
  unsigned unlinked_cnt = 0;
  while (unlinked_cnt < nd_) {
    DFS(flags, root, unlinked_cnt);
    if (unlinked_cnt >= nd_) break;
    findroot(flags, root, parameter);
  }
  for (size_t i = 0; i < nd_; ++i) {
    if (final_graph_[i].size() > width) {
      width = final_graph_[i].size();
    }
  }
}

}

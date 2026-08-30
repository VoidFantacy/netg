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

void load_data(const char* filename, float*& data, unsigned& num, unsigned& dim) {
  std::ifstream in(filename, std::ios::binary);
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
}

void load_gt(const char* filename, unsigned*& data, unsigned& num, unsigned& dim) {
  std::ifstream in(filename, std::ios::binary);
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
}

int main(int argc, char** argv) {
  float* data_load = NULL;
  unsigned points_num, dim;
  load_data(argv[1], data_load, points_num, dim);

  float* query_load = NULL;
  unsigned query_num, query_dim;
  load_data(argv[2], query_load, query_num, query_dim);

  unsigned emb_num, emb_dim;
  float* emb_data = nullptr;
  load_data(argv[7], emb_data, emb_num, emb_dim);
  hnswlib::CosSpace* space = new hnswlib::CosSpace(emb_dim);
  hnswlib::HierarchicalNSW<float>* cos_index = new hnswlib::HierarchicalNSW<float>(space, emb_num, 16, 200);
  for (int i = 0; i < (int)emb_num; i++) {
    cos_index->addPoint(emb_data + i * emb_dim, i);
  }

  efanna2e::IndexNSG index(dim, points_num, efanna2e::L2, nullptr);
  index.Load(argv[3]);
  index.LoadKmeans(argv[6]);

  unsigned* gt_load = NULL;
  unsigned gt_num, gt_dim_val;
  load_gt(argv[9], gt_load, gt_num, gt_dim_val);

  unsigned K = 100;
  efanna2e::Parameters paras;
  paras.Set<unsigned>("L_search", 100);
  paras.Set<unsigned>("P_search", 100);

  std::vector<unsigned> res(K);
  unsigned hop_count = 0;
  std::vector<unsigned> eps;

  auto pq = cos_index->searchKnn(query_load + 0 * query_dim, 3);
  while (!pq.empty()) {
      unsigned ep_id = pq.top().second;
      pq.pop();
      if (index.iter2_num > 0 && ep_id < index.iter2_eps.size()) {
          unsigned ep = index.iter2_eps[ep_id / index.iter2_num][ep_id % index.iter2_num];
          eps.push_back(ep);
      }
  }

  std::cout << "eps size: " << eps.size() << std::endl;
  for (unsigned ep : eps) {
      std::cout << "ep: " << ep << std::endl;
  }

  index.Search(query_load + 0 * dim, data_load, K, paras, res.data(), &hop_count, eps);

  std::cout << "res[0]: " << res[0] << ", res[1]: " << res[1] << std::endl;
  std::cout << "gt[0]: " << gt_load[0] << ", gt[1]: " << gt_load[1] << std::endl;

  return 0;
}

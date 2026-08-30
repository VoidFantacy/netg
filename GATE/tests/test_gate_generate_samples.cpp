#include <efanna2e/index_nsg.h>
#include <efanna2e/util.h>
#include <chrono>
#include <vector>
#include <iostream>
#include <fstream>
#include <cassert>
#include <omp.h>

void load_data(const char* filename, float*& data, unsigned& num, unsigned& dim) {
  std::ifstream in(filename, std::ios::binary);
  if (!in.is_open()) {
    std::cerr << "open file error: " << filename << std::endl;
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
}

int main(int argc, char** argv) {
  if (argc != 8) {
    std::cout << "Usage: " << argv[0] << " <data_file> <query_file> <nsg_path> <hubs_txt> <search_L> <search_K> <output_dir>" << std::endl;
    exit(-1);
  }

  float* data_load = NULL;
  unsigned points_num, dim;
  load_data(argv[1], data_load, points_num, dim);

  float* query_load = NULL;
  unsigned query_num, query_dim;
  load_data(argv[2], query_load, query_num, query_dim);
  assert(dim == query_dim);

  unsigned L = (unsigned)atoi(argv[5]);
  unsigned K = (unsigned)atoi(argv[6]);

  std::cout << "Computing Ground Truth (Top-1 NN) internally using AVX..." << std::endl;
  unsigned* gt_load = new unsigned[query_num];
  efanna2e::DistanceL2 dist_func; // FIXED: Use DistanceL2 instead of DistanceFastL2
  
  #pragma omp parallel for
  for (unsigned i = 0; i < query_num; i++) {
    float min_dist = 1e30;
    unsigned min_idx = 0;
    for (unsigned j = 0; j < points_num; j++) {
      float dist = dist_func.compare(query_load + i * dim, data_load + j * dim, dim);
      if (dist < min_dist) {
        min_dist = dist;
        min_idx = j;
      }
    }
    gt_load[i] = min_idx;
  }
  std::cout << "GT computation done." << std::endl;

  efanna2e::IndexNSG index(dim, points_num, efanna2e::L2, nullptr);
  index.Load(argv[3]);
  index.LoadKmeans(argv[4]);

  efanna2e::Parameters paras;
  paras.Set<unsigned>("L_search", L);
  paras.Set<unsigned>("P_search", L);

  unsigned num_hubs = index.iter1_num * index.iter2_num;
  std::vector<unsigned> hub_eps;
  for (unsigned i = 0; i < index.iter1_num; i++) {
    for (unsigned j = 0; j < index.iter2_num; j++) {
      hub_eps.push_back(index.iter2_eps[i][j]);
    }
  }

  std::string out_dir = argv[7];
  std::ofstream out_pos(out_dir + "/pos_sample.txt");
  std::ofstream out_neg(out_dir + "/neg_sample.txt");

  std::cout << "Generating samples for " << query_num << " queries using " << num_hubs << " hubs..." << std::endl;

  for (unsigned i = 0; i < query_num; i++) {
    std::vector<unsigned> hop_counts(num_hubs, 999);
    unsigned gt_nn = gt_load[i]; 

    #pragma omp parallel for
    for (unsigned h = 0; h < num_hubs; h++) {
      std::vector<unsigned> tmp(K);
      unsigned hc = 0;
      std::vector<unsigned> eps = { hub_eps[h] };
      
      index.Search(query_load + i * dim, data_load, K, paras, tmp.data(), &hc, eps);
      
      bool found = false;
      for (unsigned k = 0; k < K; k++) {
        if (tmp[k] == gt_nn) {
          found = true;
          break;
        }
      }
      
      if (found) {
        hop_counts[h] = hc;
      } else {
        hop_counts[h] = 999;
      }
    }

    int min_hop = 999999;
    int max_hop = -1;
    for (unsigned h = 0; h < num_hubs; h++) {
      if (hop_counts[h] != 999) {
        if ((int)hop_counts[h] < min_hop) min_hop = hop_counts[h];
        if ((int)hop_counts[h] > max_hop) max_hop = hop_counts[h];
      }
    }

    std::vector<unsigned> pos_samples;
    if (min_hop != 999999) {
      for (unsigned h = 0; h < num_hubs; h++) {
        if ((int)hop_counts[h] == min_hop) {
          pos_samples.push_back(h);
        }
      }
    } else {
      pos_samples.push_back(0); 
    }

    std::vector<unsigned> neg_samples;
    int hop_bar = 0;
    if (max_hop != -1) {
      while (true) {
        int bar = max_hop - hop_bar;
        neg_samples.clear();
        for (unsigned h = 0; h < num_hubs; h++) {
          if (hop_counts[h] != 999 && (int)hop_counts[h] >= bar) {
            neg_samples.push_back(h);
          }
        }
        if (neg_samples.size() > 64 || bar <= min_hop + 1) {
          break;
        }
        hop_bar++;
      }
    } else {
      for (unsigned h = 0; h < num_hubs; h++) {
        neg_samples.push_back(h);
      }
    }

    for (size_t j = 0; j < pos_samples.size(); j++) {
      out_pos << pos_samples[j] << (j == pos_samples.size() - 1 ? "" : " ");
    }
    out_pos << "\n";

    for (size_t j = 0; j < neg_samples.size(); j++) {
      out_neg << neg_samples[j] << (j == neg_samples.size() - 1 ? "" : " ");
    }
    out_neg << "\n";

    if ((i + 1) % 100 == 0) {
      std::cout << "Processed " << (i + 1) << " queries\r" << std::flush;
    }
  }
  std::cout << "\nDone." << std::endl;

  out_pos.close();
  out_neg.close();

  delete[] data_load;
  delete[] query_load;
  delete[] gt_load;

  return 0;
}

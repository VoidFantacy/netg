#include <efanna2e/index_nsg.h>
#include <efanna2e/util.h>
#include <hnswlib/hnswlib.h>
#include <chrono>

void load_data(const char* filename, float*& data, unsigned& num,
               unsigned& dim) {  // load data with sift10K pattern
  std::ifstream in(filename, std::ios::binary);
  std::cout << "opening: " << filename << '\n';
  if (!in.is_open()) {
    std::cout << "open file error" << std::endl;
    exit(-1);
  }
  in.read((char*)&dim, 4);
  in.seekg(0, std::ios::end);
  std::ios::pos_type ss = in.tellg();
  size_t fsize = (size_t)ss;
  num = (unsigned)(fsize / (dim + 1) / 4);
  data = new float[num * dim * sizeof(float)];
  std::cout << "data dimension: " << dim << ", num: " << num << std::endl;

  in.seekg(0, std::ios::beg);
  for (size_t i = 0; i < num; i++) {
    in.seekg(4, std::ios::cur);
    in.read((char*)(data + i * dim), dim * 4);
  }
  in.close();
}

void save_result(const char* filename, std::vector<std::vector<unsigned> >& results) {
  std::ofstream out(filename, std::ios::binary | std::ios::out);

  for (unsigned i = 0; i < results.size(); i++) {
    unsigned GK = (unsigned)results[i].size();
    out.write((char*)&GK, sizeof(unsigned));
    out.write((char*)results[i].data(), GK * sizeof(unsigned));
  }
  out.close();
}

int main(int argc, char** argv) {
  // Fix 1: Correct argument count check (prog + 8 args = 9)
  if (argc != 9) {
    std::cout << argv[0]
              << " data_file query_file nsg_path search_L search_K result_path kmeans_path hop_count_path"
              << std::endl;
    exit(-1);
  }

  // 1. Load Base Data
  float* data_load = NULL;
  unsigned points_num, dim;
  load_data(argv[1], data_load, points_num, dim);

  // 2. Load Query Data
  float* query_load = NULL;
  unsigned query_num, query_dim;
  load_data(argv[2], query_load, query_num, query_dim);
  assert(dim == query_dim);

  // 3. Load K-Means Hubs (Centroids) - Fix 2: Missing Data Loading
  float* hubs_load = NULL;
  unsigned hubs_num, hubs_dim;
  load_data(argv[7], hubs_load, hubs_num, hubs_dim);
  assert(dim == hubs_dim);

  // 4. Build HNSW Index for Hubs - Fix 3: Define 'cos_index'
  // Using L2Space for K-Means centroids (geometric distance)
  hnswlib::L2Space space(dim); 
  hnswlib::HierarchicalNSW<float>* cos_index = new hnswlib::HierarchicalNSW<float>(&space, hubs_num, 16, 200);
  
  std::cout << "Building HNSW index for " << hubs_num << " hubs..." << std::endl;
  for (int i = 0; i < hubs_num; i++) {
    cos_index->addPoint(hubs_load + i * dim, i);
  }

  unsigned L = (unsigned)atoi(argv[4]);
  unsigned K = (unsigned)atoi(argv[5]);

  if (L < K) {
    std::cout << "search_L cannot be smaller than search_K!" << std::endl;
    exit(-1);
  }

  // 5. Load NSG Index - Fix 4: Missing Index Loading
  efanna2e::IndexNSG index(dim, points_num, efanna2e::L2, nullptr);
  std::cout << "Loading NSG index from " << argv[3] << "..." << std::endl;
  index.Load(argv[3]);
  
  std::cout << "Loading K-Means mapping from " << argv[7] << "..." << std::endl;
  index.LoadKmeans(argv[7]); // This populates iter2_eps

  efanna2e::Parameters paras;
  paras.Set<unsigned>("L_search", L);
  paras.Set<unsigned>("P_search", L);

  auto s = std::chrono::high_resolution_clock::now();
  std::vector<std::vector<unsigned> > res;
  res.reserve(query_num);
  std::vector<std::vector<unsigned> > hop_counts;
  
  hop_counts.reserve(query_num);

  std::cout << "Generating routing hops..." << std::endl;
  for (unsigned i = 0; i < query_num; i++) {
    std::vector<unsigned> tmp(K);
    std::vector<unsigned> hop_count(K);
    std::vector<unsigned> eps;
    hop_count[0] = i;

    // Search for nearest hubs using HNSW
    auto cos_eps = cos_index->searchKnn(query_load + i * dim, 3); // Now cos_index is defined
    while (!cos_eps.empty()) {
      unsigned ep_id = cos_eps.top().second;
      cos_eps.pop();
      
      // Map hub ID to graph node ID
      unsigned ep = index.iter2_eps[ep_id / index.iter2_num][ep_id % index.iter2_num];
      eps.push_back(ep);
    }

    index.Search(query_load + i * dim, data_load, K, paras, tmp.data(), hop_count.data(), eps);

    res.push_back(tmp);
    hop_counts.push_back(hop_count);
    
    if ((i + 1) % 1000 == 0) std::cout << i + 1 << "/" << query_num << " processed\r" << std::flush;
  }
  std::cout << "\nDone." << std::endl;

  save_result(argv[6], res);
  save_result(argv[8], hop_counts);
  
  // Cleanup
  delete cos_index;
  delete[] data_load;
  delete[] query_load;
  delete[] hubs_load;

  return 0;
}
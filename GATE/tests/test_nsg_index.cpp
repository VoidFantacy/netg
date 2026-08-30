#include <efanna2e/index_nsg.h>
#include <efanna2e/util.h>
#include <iostream>

void load_data(char* filename, float*& data, unsigned& num,
               unsigned& dim) {
  std::cout << "[DEBUG] >> Loading data from: " << filename << std::endl;
  std::ifstream in(filename, std::ios::binary);
  if (!in.is_open()) {
    std::cout << "open file error" << std::endl;
    exit(-1);
  }
  in.read((char*)&dim, 4);
  std::cout << "[DEBUG] >> Data Dim: " << dim << std::endl;
  
  in.seekg(0, std::ios::end);
  std::ios::pos_type ss = in.tellg();
  size_t fsize = (size_t)ss;
  num = (unsigned)(fsize / (dim + 1) / 4);
  std::cout << "[DEBUG] >> Data Points: " << num << std::endl;
  
  data = new float[(size_t)num * (size_t)dim];
  std::cout << "[DEBUG] >> Memory allocated for base data." << std::endl;

  in.seekg(0, std::ios::beg);
  for (size_t i = 0; i < num; i++) {
    in.seekg(4, std::ios::cur);
    in.read((char*)(data + i * dim), dim * 4);
    // 每加载 100万条打印一次，防止卡死不知道
    if ((i+1) % 2000000 == 0) std::cout << "[DEBUG] >> Loaded " << (i+1) << " vectors..." << std::endl;
  }
  in.close();
  std::cout << "[DEBUG] >> load_data finished." << std::endl;
}

int main(int argc, char** argv) {
  std::cout << "[DEBUG] Program started..." << std::endl;
  if (argc != 7) {
    std::cout << argv[0] << " data_file nn_graph_path L R C save_graph_file"
              << std::endl;
    exit(-1);
  }
  float* data_load = NULL;
  unsigned points_num, dim;
  
  // 1. 加载数据
  load_data(argv[1], data_load, points_num, dim);

  std::string nn_graph_path(argv[2]);
  unsigned L = (unsigned)atoi(argv[3]);
  unsigned R = (unsigned)atoi(argv[4]);
  unsigned C = (unsigned)atoi(argv[5]);
  
  std::cout << "[DEBUG] Params: L=" << L << ", R=" << R << ", C=" << C << std::endl;
  std::cout << "[DEBUG] Graph Path: " << nn_graph_path << std::endl;

  // 2. 内存对齐 (关键点)
  std::cout << "[DEBUG] Performing data_align..." << std::endl;
  std::cout << "[DEBUG] Ptr before: " << data_load << std::endl;
  // 关键修复代码在此
  data_load = efanna2e::data_align(data_load, points_num, dim);
  std::cout << "[DEBUG] Ptr after : " << data_load << " (Should be aligned)" << std::endl;

  // 3. 初始化索引
  std::cout << "[DEBUG] Initializing IndexNSG..." << std::endl;
  efanna2e::IndexNSG index(dim, points_num, efanna2e::L2, nullptr);

  auto s = std::chrono::high_resolution_clock::now();
  efanna2e::Parameters paras;
  paras.Set<unsigned>("L", L);
  paras.Set<unsigned>("R", R);
  paras.Set<unsigned>("C", C);
  paras.Set<std::string>("nn_graph_path", nn_graph_path);

  // 4. 开始构建 (最容易崩的地方)
  std::cout << "[DEBUG] Calling index.Build()... (Wait for Graph Loading)" << std::endl;
  index.Build(points_num, data_load, paras);
  std::cout << "[DEBUG] index.Build() finished successfully!" << std::endl;
  
  auto e = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> diff = e - s;

  std::cout << "indexing time: " << diff.count() << "\n";
  
  // 5. 保存
  std::cout << "[DEBUG] Saving index to " << argv[6] << "..." << std::endl;
  index.Save(argv[6]);
  std::cout << "[DEBUG] All Done." << std::endl;

  return 0;
}
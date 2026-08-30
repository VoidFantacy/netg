#include <iostream>
#include <vector>
#include <algorithm>
#include <memory>
#include <chrono>
#include <fstream>
#include <argparse/argparse.hpp>
#include <benches/datasets/DataLoader.hpp>
#include <nlohmann/json.hpp>
#include <ACSG/IndexACSG.h>
#include <benches/utils/Timer.hpp>
#include <benches/utils/metrics.hpp>
#include <benches/utils/graph_properties.hpp>
#include <atomic>
#include <queue>
#include <cmath>
#include <filesystem>
#include <faiss/utils/distances.h>
#include <iomanip>
#include <cstring>
#include <unordered_set>
#include <sstream> 
#include <random>
#include <limits> 
#include <faiss/IndexFlat.h> 
#include <numeric>

// 【核心修改 1】引入 HNSW 头文件用于高层极速路由
#include <hnswlib/hnswlib.h>

#ifdef USE_ONNXRUNTIME
#include <onnxruntime_cxx_api.h>
#endif

#include <faiss/VectorTransform.h> 
#include <faiss/index_io.h> 

using json = nlohmann::json;

// ==========================================
// 1. 基础工具与结构定义
// ==========================================

struct SearchMetrics {
    double qps;
    double recall;
};

// ==========================================
// 2. 核心搜索类 EntryPointSearcher
// ==========================================

class EntryPointSearcher {
public:
    enum Mode { MEDOID, ACO_WEIGHT, GRAVITY_ROUTING, HNSW_ROUTING };

    std::vector<int> combined_centers_; 
    std::vector<std::vector<int>> gravity_graph_;
    std::vector<std::vector<float>> center_vectors_reduced_; 
    std::vector<int> center_max_points_; 
    
    faiss::VectorTransform* pca_mat_ = nullptr;
    bool use_neural_router_ = false;
    int d_reduced_ = 0; 

    // === HNSW 导航图专用指针 ===
    hnswlib::SpaceInterface<float>* hnsw_space_ = nullptr;
    hnswlib::HierarchicalNSW<float>* hnsw_router_ = nullptr;
    bool hnsw_use_ip_ = false; // 标记当前路由是否使用 InnerProduct 空间

#ifdef USE_ONNXRUNTIME
    std::unique_ptr<Ort::Env> ort_env_;
    std::unique_ptr<Ort::Session> ort_session_;
    std::unique_ptr<Ort::AllocatorWithDefaultOptions> allocator_;
    std::unique_ptr<Ort::MemoryInfo> memory_info_; 
    
    std::vector<const char*> input_node_names_ptr_;
    std::vector<const char*> output_node_names_ptr_;
    std::vector<std::string> input_node_names_store_;
    std::vector<std::string> output_node_names_store_;
    
    std::vector<float> mean_; 
    std::vector<float> std_;  
    std::vector<float> inv_std_; 
#endif

    int global_max_gamma_local_idx_ = -1; 
    int aco_max_weight_node_ = -1;        
    acsg::IndexACSG* index_ptr_ = nullptr;

    ~EntryPointSearcher() { reset(); }

    void reset() {
        if (pca_mat_) { delete pca_mat_; pca_mat_ = nullptr; }
        if (hnsw_router_) { delete hnsw_router_; hnsw_router_ = nullptr; }
        if (hnsw_space_) { delete hnsw_space_; hnsw_space_ = nullptr; }
        hnsw_use_ip_ = false;
        use_neural_router_ = false;
        combined_centers_.clear();
        gravity_graph_.clear();
        center_vectors_reduced_.clear();
        center_max_points_.clear();
#ifdef USE_ONNXRUNTIME
        ort_session_.reset();
        ort_env_.reset();
#endif
    }

    bool load_hnsw(const std::string& hubs_file, const std::string& ids_file, int dim, acsg::IndexACSG* index, bool use_ip = false) {
        reset();
        index_ptr_ = index;

        std::ifstream f_hubs(hubs_file, std::ios::binary | std::ios::ate);
        std::ifstream f_ids(ids_file, std::ios::binary | std::ios::ate);
        if (!f_hubs || !f_ids) {
            std::cerr << "❌ HNSW Routing Files Missing!" << std::endl;
            return false;
        }

        size_t hubs_size = f_hubs.tellg();
        int hub_num = hubs_size / (dim * sizeof(float));
        f_hubs.seekg(0, std::ios::beg);
        std::vector<float> hubs(hub_num * dim);
        f_hubs.read(reinterpret_cast<char*>(hubs.data()), hubs_size);

        size_t ids_size = f_ids.tellg();
        f_ids.seekg(0, std::ios::beg);
        std::vector<int> ids(hub_num);
        f_ids.read(reinterpret_cast<char*>(ids.data()), ids_size);

        // 【关键修复】Task 5 的 Hub 已经 L2 归一化，需要 InnerProductSpace
        //   Task 2 的 raw Hub 未归一化，使用 L2Space
        hnsw_use_ip_ = use_ip;
        if (use_ip) {
            hnsw_space_ = new hnswlib::InnerProductSpace(dim);
        } else {
            hnsw_space_ = new hnswlib::L2Space(dim);
        }
        hnsw_router_ = new hnswlib::HierarchicalNSW<float>(hnsw_space_, hub_num, 16, 200);

        for (int i = 0; i < hub_num; ++i) {
            hnsw_router_->addPoint(hubs.data() + i * dim, ids[i]);
        }
        
        std::string space_name = use_ip ? "InnerProduct (cosine)" : "L2";
        std::cout << "✅ Loaded HNSW Router [" << space_name << "] (Hubs: " << hub_num << ", Dim: " << dim << ")" << std::endl;
        return true;
    }

    bool load(const std::string& entry_points_file, acsg::IndexACSG* index, const std::string& onnx_model_path) {
        reset(); 
        index_ptr_ = index;
        
        if (!index->acsg.weight.empty()) {
            auto& w = index->acsg.weight;
            aco_max_weight_node_ = std::distance(w.begin(), std::max_element(w.begin(), w.end()));
        } else {
            aco_max_weight_node_ = index->acsg.enterpoint;
        }

        if (entry_points_file.empty()) return true; 

        std::ifstream file(entry_points_file);
        if (!file) return false;
        json data; try { file >> data; } catch (...) { return false; }

        if (data.contains("combined_centers")) combined_centers_ = data["combined_centers"].get<std::vector<int>>();
        if (data.contains("knn_12k_graph")) gravity_graph_ = data["knn_12k_graph"].get<std::vector<std::vector<int>>>();
        if (data.contains("centers_reduced")) center_vectors_reduced_ = data["centers_reduced"].get<std::vector<std::vector<float>>>();
        
        if (!center_vectors_reduced_.empty()) d_reduced_ = center_vectors_reduced_[0].size();

        if (data.contains("global_max_gamma_local_idx")) global_max_gamma_local_idx_ = data["global_max_gamma_local_idx"];
        else global_max_gamma_local_idx_ = 0;
        if (data.contains("center_max_points")) center_max_points_ = data["center_max_points"].get<std::vector<int>>();

#ifdef USE_ONNXRUNTIME
        if (!onnx_model_path.empty() && std::filesystem::exists(onnx_model_path)) {
            try {
                ort_env_ = std::make_unique<Ort::Env>(ORT_LOGGING_LEVEL_WARNING, "NeuralRouter");
                Ort::SessionOptions session_options;
                session_options.SetIntraOpNumThreads(1); 
                session_options.SetInterOpNumThreads(1);
                session_options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
                
                ort_session_ = std::make_unique<Ort::Session>(*ort_env_, onnx_model_path.c_str(), session_options);
                allocator_ = std::make_unique<Ort::AllocatorWithDefaultOptions>();
                memory_info_ = std::make_unique<Ort::MemoryInfo>(Ort::MemoryInfo::CreateCpu(OrtAllocatorType::OrtArenaAllocator, OrtMemType::OrtMemTypeDefault));

                size_t num_input = ort_session_->GetInputCount();
                input_node_names_ptr_.resize(num_input);
                input_node_names_store_.resize(num_input);
                for (size_t i = 0; i < num_input; i++) {
                    auto name_ptr = ort_session_->GetInputNameAllocated(i, *allocator_);
                    input_node_names_store_[i] = name_ptr.get();
                    input_node_names_ptr_[i] = input_node_names_store_[i].c_str();
                }

                size_t num_output = ort_session_->GetOutputCount();
                output_node_names_ptr_.resize(num_output);
                output_node_names_store_.resize(num_output);
                for (size_t i = 0; i < num_output; i++) {
                    auto name_ptr = ort_session_->GetOutputNameAllocated(i, *allocator_);
                    output_node_names_store_[i] = name_ptr.get();
                    output_node_names_ptr_[i] = output_node_names_store_[i].c_str();
                }

                std::string dir_path = std::filesystem::path(onnx_model_path).parent_path().string();
                std::string norm_path = dir_path + "/ae_norm.json";
                std::ifstream f_norm(norm_path);
                if (f_norm) {
                    json j_norm; f_norm >> j_norm;
                    mean_ = j_norm["mean"].get<std::vector<float>>();
                    std_ = j_norm["std"].get<std::vector<float>>();
                    inv_std_.resize(std_.size());
                    for(size_t i=0; i<std_.size(); ++i) inv_std_[i] = 1.0f / (std_[i] + 1e-6f);
                    use_neural_router_ = true;
                }
            } catch (const std::exception& e) { std::cerr << "   ❌ ONNX Load Failed: " << e.what() << std::endl; }
        }
#endif
        if (!use_neural_router_) {
            std::string dir_path = std::filesystem::path(entry_points_file).parent_path().string();
            std::string pca_path = dir_path + "/pca_transform.bin";
            if (std::filesystem::exists(pca_path)) {
                pca_mat_ = faiss::read_VectorTransform(pca_path.c_str());
                d_reduced_ = pca_mat_->d_out;
            }
        }
        return true;
    }

    std::vector<float> encodeBatch(const float* queries, int nq, int d) {
        if (!use_neural_router_ && !pca_mat_) return {};
        
        std::vector<float> reduced_queries;
        reduced_queries.resize(nq * d_reduced_);

#ifdef USE_ONNXRUNTIME
        if (use_neural_router_) {
            std::vector<float> input_values(nq * d);
            for(int i=0; i<nq; ++i) {
                for(int k=0; k<d; ++k) {
                    input_values[i*d + k] = (queries[i*d+k] - mean_[k]) * inv_std_[k];
                }
            }

            std::vector<int64_t> input_shape = {nq, d};
            try {
                Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
                    *memory_info_, input_values.data(), input_values.size(), input_shape.data(), 2);
                
                auto output_tensors = ort_session_->Run(
                    Ort::RunOptions{nullptr}, input_node_names_ptr_.data(), &input_tensor, 1, output_node_names_ptr_.data(), 1);
                
                float* output_arr = output_tensors[0].GetTensorMutableData<float>();
                std::memcpy(reduced_queries.data(), output_arr, nq * d_reduced_ * sizeof(float));
            } catch (const std::exception& e) {
                std::cerr << "❌ Batch Inference Failed: " << e.what() << std::endl;
            }
            return reduced_queries;
        }
#endif
        if (pca_mat_) {
            std::vector<float> buffer(nq * d);
            std::memcpy(buffer.data(), queries, nq * d * sizeof(float));
            for(int i=0; i<nq; ++i) faiss::fvec_renorm_L2(d, 1, buffer.data() + i*d);
            pca_mat_->apply_noalloc(nq, buffer.data(), reduced_queries.data());
            return reduced_queries;
        }
        return {};
    }

    std::vector<int> searchOnGraphReduced(const float* query_reduced, int start_node, int ef) const { 
        std::priority_queue<std::pair<float, int>, std::vector<std::pair<float, int>>, std::greater<>> search_queue;
        std::priority_queue<std::pair<float, int>> top_candidates; 
        
        std::vector<bool> visited(gravity_graph_.size(), false);

        float d_val = faiss::fvec_L2sqr(center_vectors_reduced_[start_node].data(), query_reduced, d_reduced_);
        visited[start_node] = true;
        
        top_candidates.push({d_val, start_node});
        search_queue.push({d_val, start_node});
        
        float lower_bound = d_val;

        while(!search_queue.empty()) {
            auto [curr_dist, curr_id] = search_queue.top();
            search_queue.pop();
            if (curr_dist > lower_bound) break;

            for (int neighbor : gravity_graph_[curr_id]) {
                if (visited[neighbor]) continue;
                visited[neighbor] = true;
                float d_neighbor = faiss::fvec_L2sqr(center_vectors_reduced_[neighbor].data(), query_reduced, d_reduced_);
                
                if (top_candidates.size() < (size_t)ef || d_neighbor < lower_bound) {
                    top_candidates.push({d_neighbor, neighbor});
                    search_queue.push({d_neighbor, neighbor});
                    if (top_candidates.size() > (size_t)ef) top_candidates.pop();
                    if (!top_candidates.empty()) lower_bound = top_candidates.top().first;
                }
            }
        }

        std::vector<int> best_indices;
        while(!top_candidates.empty()) {
            best_indices.push_back(top_candidates.top().second);
            top_candidates.pop();
        }
        std::reverse(best_indices.begin(), best_indices.end());
        if (best_indices.size() > 3) best_indices.resize(3); 
        return best_indices;
    }
};

// ==========================================
// 3. 任务配置结构体
// ==========================================

struct TestTask {
    std::string name;
    EntryPointSearcher::Mode mode;
    std::string cluster_file;
    std::string model_file;
    std::string extra_file;
    bool is_baseline = false;
    bool use_ip = false; // HNSW 路由是否使用 InnerProduct 空间（Task 5 归一化 Hub 需要 true）
};

// ==========================================
// 4. 搜索流程控制 (含上帝视角诊断)
// ==========================================

SearchMetrics run_search_batch(
    acsg::IndexACSG& index, 
    const float* xq, int nq, int d, int k, 
    const std::unique_ptr<faiss::idx_t[]>& gt,
    EntryPointSearcher& searcher,
    EntryPointSearcher::Mode mode
) {
    std::unique_ptr<faiss::idx_t[]> I(new faiss::idx_t[nq * k]);
    std::unique_ptr<float[]> D(new float[nq * k]);
    std::vector<std::vector<acsg::EnterPoint>> all_eps(nq);

    // 【修改】只启动一个全局总计时器，包含路由 + 搜索端到端过程
    auto start_total = std::chrono::high_resolution_clock::now();

    // --- STEP 1: 路由 (单线程) ---
    if (mode == EntryPointSearcher::HNSW_ROUTING) {
        for (int i = 0; i < nq; ++i) {
            auto pq = searcher.hnsw_router_->searchKnn(xq + i * d, 3);
            while (!pq.empty()) {
                all_eps[i].emplace_back(pq.top().second, 1.0f);
                pq.pop();
            }
        }
    } 
    else if (mode == EntryPointSearcher::GRAVITY_ROUTING) {
        std::vector<float> reduced_all = searcher.encodeBatch(xq, nq, d);
        int d_red = searcher.d_reduced_;
        int start_node = searcher.global_max_gamma_local_idx_;
        if (start_node < 0) start_node = 0;

        for (int i = 0; i < nq; ++i) {
            std::vector<int> best_idxs = searcher.searchOnGraphReduced(reduced_all.data() + i * d_red, start_node, 10);
            for (int idx : best_idxs) {
                all_eps[i].emplace_back(searcher.combined_centers_[idx], 1.0f);
            }
        }
    } 
    else {
        for (int i = 0; i < nq; ++i) {
            if (mode == EntryPointSearcher::MEDOID) {
                all_eps[i].emplace_back(index.acsg.enterpoint, 1.0f);
            } else if (mode == EntryPointSearcher::ACO_WEIGHT) {
                int target = (!searcher.center_max_points_.empty()) ? searcher.center_max_points_[0] : searcher.aco_max_weight_node_;
                all_eps[i].emplace_back(target, 1.0f);
            }
        }
    }

    // --- STEP 2: 搜索 ---
    // 【性能优化】将 VisitedTable、DistanceComputer、retset 全部移到循环外复用
    //   - VisitedTable: advance() O(1) 重置
    //   - DistanceComputer: 避免虚函数表查找和堆分配
    //   - retset: 避免每次查询的 vector 堆分配/释放（~0.5-1μs/query）
    int search_internal_mode = 2; // ACSG底层固定走自定义多点起跑模式
    faiss::VisitedTable vt(index.ntotal);
    std::unique_ptr<faiss::DistanceComputer> dis(acsg::storage_distance_computer(index.storage));
    std::vector<acsg::Neighbor> retset_buf; // 外部缓冲区，避免 search_new 内部反复 new/delete
    for (int i = 0; i < nq; ++i) {
        faiss::idx_t* res_I = I.get() + i * k;
        float* res_D = D.get() + i * k;
        dis->set_query(xq + i * d);
        vt.advance();  // O(1) 重置
        index.acsg.search_new(*dis, k, res_I, res_D, vt, search_internal_mode, all_eps[i], &retset_buf);
    }
    
    // 【修改】计时结束
    auto end_total = std::chrono::high_resolution_clock::now();
    double total_time_us = std::chrono::duration<double, std::micro>(end_total - start_total).count();
    double wall_time_sec = total_time_us * 1e-6;

    SearchMetrics metrics;
    metrics.recall = recall_at_k(nq, k, k, I, 100, gt);
    metrics.qps = (wall_time_sec > 0) ? (nq / wall_time_sec) : 0.0;

    return metrics;
}

double calculate_std_dev(const std::vector<double>& v, double mean) {
    if (v.size() <= 1) return 0.0;
    double sum = 0.0;
    for (double x : v) sum += (x - mean) * (x - mean);
    return std::sqrt(sum / v.size());
}

// ==========================================
// 5. 主程序
// ==========================================

int main(int argc, char** argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    argparse::ArgumentParser program("test_full_benchmark");
    program.add_argument("--dataset").required();
    program.add_argument("--acpg_file").required();
    program.add_argument("--fn_result").required();
    program.add_argument("--cluster_pca").default_value(std::string(""));       
    program.add_argument("--cluster_neural_geo").default_value(std::string("")); 
    program.add_argument("--cluster_neural_topo").default_value(std::string(""));
    program.add_argument("--drl_model_config").default_value(std::string("")); 
    
    program.add_argument("--transformed_hubs").default_value(std::string(""));
    program.add_argument("--transformed_ids").default_value(std::string(""));

    // 【新增 1】接收原始 Hub 坐标文件，用于消融实验
    program.add_argument("--raw_hubs").default_value(std::string(""));

    program.add_argument("--test_scope").default_value(std::string("all")); 
    program.add_argument("--num_runs").default_value(5).scan<'i', int>(); 
    program.add_argument("--R").default_value(32).scan<'i', int>();
    program.add_argument("--search_Ls").default_value(std::string(""));
    program.add_argument("--top_k").default_value(1).scan<'i', int>(); 
    program.add_argument("--max_queries").default_value(10000).scan<'i', int>();

    try { program.parse_args(argc, argv); } catch (...) { return 1; }
    
    std::string dataset = program.get<std::string>("--dataset");
    std::string acpg_file = program.get<std::string>("--acpg_file");
    std::string result_file = program.get<std::string>("--fn_result");
    int num_runs = program.get<int>("--num_runs");
    std::string onnx_path = program.get<std::string>("--drl_model_config");
    std::string test_scope = program.get<std::string>("--test_scope");
    int max_q = program.get<int>("--max_queries");

    std::string f_pca = program.get<std::string>("--cluster_pca");
    std::string f_geo = program.get<std::string>("--cluster_neural_geo");
    std::string f_topo = program.get<std::string>("--cluster_neural_topo");
    std::string trans_hubs = program.get<std::string>("--transformed_hubs");
    std::string trans_ids = program.get<std::string>("--transformed_ids");

    // 【新增 2】提取路径
    std::string raw_hubs = program.get<std::string>("--raw_hubs");
    
    std::cout << "\n>>> Loading Data..." << std::endl;
    DataLoader data_loader(dataset);
    auto [nq, xq] = data_loader.load_query("drl_test");
    auto [k_gt, gt] = data_loader.load_gt("drl_test");
    int d = data_loader.dim();
    
    if (max_q > 0 && nq > (size_t)max_q) { std::cout << "⚠️ Truncating queries to " << max_q << std::endl; nq = max_q; }
    
    std::cout << "\n>>> Loading ACPG Index: " << acpg_file << std::endl;
    auto index = std::make_unique<acsg::IndexACSGFlat>();
    index->loadACPG(acpg_file.c_str());
    // 搜索阶段不需要 pheromone/weight，加载完立即释放（节省 ~85MB per 10M dataset）
    // 注意：kph_dpc_clustering 需要 weight，不能在 loadACPG 内部释放
    { std::vector<float>().swap(index->acsg.pheromone); }
    { std::vector<float>().swap(index->acsg.weight); }
    std::cout << "✅ Released pheromone & weight (search phase does not need them)" << std::endl;

    EntryPointSearcher searcher;
    std::vector<TestTask> tasks;

    // 添加测试任务
    if (test_scope == "all" || test_scope == "baselines" || test_scope == "comparison") {
        tasks.push_back({"0. Medoid (Baseline)", EntryPointSearcher::MEDOID, f_pca, "", "", true});
    }
    if (test_scope == "all" || test_scope == "baselines") {
        tasks.push_back({"1. ACO-Max (Global)", EntryPointSearcher::ACO_WEIGHT, f_pca, "", "", true});
    }
    
    // 【核心修改 3】真正的消融实验 Baseline：完全未经神经网络处理的原始 Hub HNSW 图
    if ((test_scope == "all" || test_scope == "routing" || test_scope == "comparison") && !raw_hubs.empty() && std::filesystem::exists(raw_hubs)) {
        // 注意：这里使用的是 raw_hubs，但是 ID 文件依然复用 trans_ids，做到完美控制变量！
        tasks.push_back({"2. Raw HNSW Routing (Ablation Baseline)", EntryPointSearcher::HNSW_ROUTING, raw_hubs, "", trans_ids, false, data_loader.metric_type() == faiss::METRIC_INNER_PRODUCT});
    }

    // 加入终极杀器：非对称 HNSW 路由任务 (Task 5)
    if ((test_scope == "all" || test_scope == "routing" || test_scope == "comparison") && !trans_hubs.empty() && std::filesystem::exists(trans_hubs)) {
        tasks.push_back({"5. Asym-Neural HNSW Routing (0ms inference)", EntryPointSearcher::HNSW_ROUTING, trans_hubs, "", trans_ids, false, true});
    }

    std::vector<int> search_Ls;
    {
        std::string sls = program.get<std::string>("--search_Ls");
        if (sls.empty()) {
            search_Ls = {1, 2, 4, 8, 16, 32, 64, 100, 128, 150, 200, 250, 300, 400, 512, 600, 800, 1024, 1200, 1500};
        } else {
            std::stringstream ss(sls);
            std::string token;
            while (std::getline(ss, token, ',')) {
                if (!token.empty()) search_Ls.push_back(std::stoi(token));
            }
        }
    }
    int top_k = program.get<int>("--top_k"); 
    json all_results = json::array();
    
    std::cout << "\n🚀 Starting Comprehensive Benchmarks (Runs: " << num_runs << " | Single Threaded)...\n" << std::endl;

    for (const auto& task : tasks) {
        std::cout << "================================================================================" << std::endl;
        std::cout << "🔥 Task: " << task.name << std::endl;
        
        if (task.mode == EntryPointSearcher::HNSW_ROUTING) {
            if (!searcher.load_hnsw(task.cluster_file, task.extra_file, d, index.get(), task.use_ip)) {
                std::cout << "⚠️ Failed to load HNSW router data." << std::endl;
                continue;
            }
        } else {
            if (!searcher.load(task.cluster_file, index.get(), task.model_file)) continue;
        }

        json method_res; method_res["method_name"] = task.name;
        json performance = json::array();
        
        std::cout << "   L |   Avg QPS (Std)  | Recall " << std::endl;
        std::cout << "-----+------------------+--------" << std::endl;
        
        for (int L : search_Ls) {
            index->acsg.search_L = L;
            
            std::vector<double> qps_history;
            double t_qps = 0, t_rec = 0;

            for (int r = 0; r < num_runs; ++r) {
                SearchMetrics m = run_search_batch(*index, xq.get(), nq, d, top_k, gt, searcher, task.mode);
                t_qps += m.qps; qps_history.push_back(m.qps);
                t_rec += m.recall;
            }

            SearchMetrics avg;
            avg.qps = t_qps / num_runs;
            avg.recall = t_rec / num_runs;
            double qps_std = calculate_std_dev(qps_history, avg.qps);

            std::cout << std::setw(4) << L << " | "
                      << std::setw(7) << std::fixed << std::setprecision(1) << avg.qps
                      << " (" << std::setw(5) << std::setprecision(1) << qps_std << ") | "
                      << std::setw(6) << std::setprecision(4) << avg.recall
                      << std::endl;

            performance.push_back({
                {"search_L", L}, {"qps", avg.qps}, {"qps_std", qps_std},
                {"recall", avg.recall}
            });
        }
        method_res["performance"] = performance;
        all_results.push_back(method_res);
    }
    
    json final_output;
    final_output["dataset"] = dataset;
    final_output["split"] = "held-out-test";
    final_output["metric"] = data_loader.metric_name();
    final_output["normalization"] = data_loader.normalization();
    final_output["artifact_version"] = data_loader.artifact_version();
    final_output["top_k"] = top_k;
    final_output["num_queries"] = nq;
    final_output["num_runs"] = num_runs;
    final_output["results"] = all_results;
    std::ofstream out(result_file); out << final_output.dump(4);
    std::cout << "\n✅ Benchmark finished. Saved to " << result_file << std::endl;
    return 0;
}

#include <iostream>
#include <fstream>
#include <vector>
#include <queue>
#include <unordered_set>
#include <algorithm>
#include <random>
#include <cmath>
#include <cstring>
#include <numeric>
#include <faiss/Index.h>
#include <faiss/index_io.h>  
#include <faiss/Clustering.h> 
#include <faiss/utils/distances.h>
#include <faiss/VectorTransform.h> 
#include <ACSG/IndexACSG.h>
#include <nlohmann/json.hpp>
#include <argparse/argparse.hpp> 
#include <omp.h>
#include <chrono>
#include <set>
#include <iomanip>
#include <filesystem>

#ifdef USE_ONNXRUNTIME
#include <onnxruntime_cxx_api.h>
#endif

using json = nlohmann::json;

class ProgressBar {
public:
    ProgressBar(int total, int width = 50) : total(total), width(width), count(0) {}
    void update() {
        count++;
        if (count % (std::max(1, total / 100)) == 0 || count == total) {
            float progress = (float)count / total;
            int pos = width * progress;
            std::cout << "[";
            for (int i = 0; i < width; ++i) {
                if (i < pos) std::cout << "=";
                else if (i == pos) std::cout << ">";
                else std::cout << " ";
            }
            std::cout << "] " << int(progress * 100.0) << " %\r";
            std::cout.flush();
        }
    }
    void finish() { std::cout << std::endl; }
private:
    int total;
    int width;
    int count;
};

class GraphProcessor {
private:
    std::vector<std::vector<float>> node_vectors_;          
    std::vector<std::vector<float>> node_vectors_reduced_;  
    int d_;          
    int d_reduced_ = 32;  

#ifdef USE_ONNXRUNTIME
    std::unique_ptr<Ort::Env> ort_env_;
    std::unique_ptr<Ort::Session> ort_session_;
    std::unique_ptr<Ort::AllocatorWithDefaultOptions> allocator_;
    std::vector<std::string> input_node_names_;
    std::vector<std::string> output_node_names_;
    std::vector<const char*> input_node_names_ptr_;
    std::vector<const char*> output_node_names_ptr_;
    std::vector<float> mean_; 
    std::vector<float> std_;
    bool use_neural_encoder_ = false;
#endif

    faiss::VectorTransform* pca_mat_ = nullptr;
    bool use_pca_encoder_ = false;

    std::vector<int> combined_centers_;       
    std::vector<float> combined_densities_;   
    std::vector<int> center_max_points_; 

    int global_max_gamma_local_idx_ = -1; 
    float global_max_gamma_val_ = -1.0f;

    std::vector<std::vector<int>> gravity_graph_;   
    
    std::unique_ptr<acsg::IndexACSG> acpg_index_;
    std::vector<std::vector<int>> entry_points_; 

    float rho_max_ = 0.0f;
    float avg_dist_ = 0.0f;

    inline float computeCenterDistance(int idx_i, int idx_j) const {
        int node_i = combined_centers_[idx_i];
        int node_j = combined_centers_[idx_j];
        return faiss::fvec_L2sqr(node_vectors_reduced_[node_i].data(), node_vectors_reduced_[node_j].data(), d_reduced_);
    }

    void initPCAEncoder(const std::string& pca_path) {
        if (pca_path.empty()) { std::cerr << "⚠️ PCA path is empty!" << std::endl; return; }
        std::cout << "\n>>> Initializing PCA Encoder: " << pca_path << std::endl;
        if (std::filesystem::exists(pca_path)) {
            pca_mat_ = faiss::read_VectorTransform(pca_path.c_str());
            use_pca_encoder_ = true;
            d_reduced_ = pca_mat_->d_out;
            std::cout << "✅ PCA loaded. Output dim: " << d_reduced_ << std::endl;
        } else {
            std::cerr << "⚠️ PCA Matrix not found at " << pca_path << std::endl;
        }
    }

    void initNeuralEncoder(const std::string& onnx_path) {
#ifdef USE_ONNXRUNTIME
        if (onnx_path.empty()) return;
        std::cout << "\n>>> Initializing Neural Encoder: " << onnx_path << std::endl;
        try {
            ort_env_ = std::make_unique<Ort::Env>(ORT_LOGGING_LEVEL_WARNING, "GraphProcessor");
            Ort::SessionOptions session_options;
            session_options.SetIntraOpNumThreads(omp_get_max_threads()); 
            session_options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
            
            ort_session_ = std::make_unique<Ort::Session>(*ort_env_, onnx_path.c_str(), session_options);
            allocator_ = std::make_unique<Ort::AllocatorWithDefaultOptions>();

            auto type_info = ort_session_->GetOutputTypeInfo(0);
            auto tensor_info = type_info.GetTensorTypeAndShapeInfo();
            d_reduced_ = tensor_info.GetShape()[1];
            std::cout << "🧠 Neural Model Output Dim Detected: " << d_reduced_ << std::endl;

            size_t num_input_nodes = ort_session_->GetInputCount();
            for (size_t i = 0; i < num_input_nodes; i++) {
                auto name_ptr = ort_session_->GetInputNameAllocated(i, *allocator_);
                input_node_names_.push_back(name_ptr.get());
                input_node_names_ptr_.push_back(input_node_names_.back().c_str());
            }

            size_t num_output_nodes = ort_session_->GetOutputCount();
            for (size_t i = 0; i < num_output_nodes; i++) {
                auto name_ptr = ort_session_->GetOutputNameAllocated(i, *allocator_);
                output_node_names_.push_back(name_ptr.get());
                output_node_names_ptr_.push_back(output_node_names_.back().c_str());
            }

            std::string dir_path = std::filesystem::path(onnx_path).parent_path().string(); // 【修正】这里之前写错了
            std::string norm_path = dir_path + "/ae_norm.json";
            std::ifstream f_norm(norm_path);
            if (f_norm) {
                json j_norm; f_norm >> j_norm;
                mean_ = j_norm["mean"].get<std::vector<float>>();
                std_ = j_norm["std"].get<std::vector<float>>();
                use_neural_encoder_ = true;
                std::cout << "✅ Loaded Normalization params." << std::endl;
            } else {
                std::cerr << "❌ Failed to load ae_norm.json from " << norm_path << std::endl;
            }
        } catch (const std::exception& e) {
            std::cerr << "❌ ONNX Init Failed: " << e.what() << std::endl;
        }
#endif
    }

    void applyEncoding() {
        size_t n = node_vectors_.size(); // 【修正】改为 size_t，匹配 loop 变量类型
        node_vectors_reduced_.resize(n);
        
        if (use_pca_encoder_) {
            std::cout << ">>> Encoding " << n << " nodes using PCA..." << std::endl;
            #pragma omp parallel for
            for (size_t i = 0; i < n; ++i) {
                std::vector<float> buffer = node_vectors_[i];
                faiss::fvec_renorm_L2(d_, 1, buffer.data()); 
                node_vectors_reduced_[i].resize(d_reduced_);
                pca_mat_->apply_noalloc(1, buffer.data(), node_vectors_reduced_[i].data());
            }
        } 
#ifdef USE_ONNXRUNTIME
        else if (use_neural_encoder_) {
            std::cout << ">>> Encoding " << n << " nodes using Neural Network (Batch Mode)..." << std::endl;
            
            // ⚠️ 智能量级检测
            bool need_l2_norm = false;
            double data_abs_sum = 0;
            double model_mean_sum = 0;
            int check_dim = std::min(d_, 10);
            int samples_checked = 0;
            
            for (size_t i = 0; i < std::min(n, (size_t)100); ++i) { 
                double vec_sum = 0;
                for(int k=0; k<check_dim; ++k) vec_sum += std::abs(node_vectors_[i][k]);
                if (vec_sum > 1e-5) { 
                    data_abs_sum += vec_sum;
                    samples_checked++;
                    if (samples_checked >= 5) break; 
                }
            }
            if (samples_checked == 0) samples_checked = 1; 

            for(int k=0; k<check_dim; ++k) model_mean_sum += std::abs(mean_[k]);
            
            double data_avg = data_abs_sum / (samples_checked * check_dim);
            double model_avg = model_mean_sum / check_dim;
            
            if (model_avg < 1.0 && data_avg > 10.0) {
                need_l2_norm = true;
                std::cout << "⚠️ [GraphProcessor] Auto L2-Norm triggered! (Data: " << data_avg 
                          << " >> Model: " << model_avg << ")" << std::endl;
            }

            ProgressBar bar(n);
            auto memory_info = Ort::MemoryInfo::CreateCpu(OrtAllocatorType::OrtArenaAllocator, OrtMemType::OrtMemTypeDefault);
            size_t batch_size = 4096; 
            
            for (size_t i = 0; i < n; i += batch_size) {
                size_t current_bs = std::min(batch_size, n - i);
                std::vector<float> input_values;
                input_values.reserve(current_bs * d_);
                
                for (size_t j = 0; j < current_bs; ++j) {
                    int node_idx = i + j;
                    
                    const float* src_ptr = node_vectors_[node_idx].data();
                    std::vector<float> temp_vec;
                    
                    if (need_l2_norm) {
                        temp_vec = node_vectors_[node_idx]; 
                        faiss::fvec_renorm_L2(d_, 1, temp_vec.data());
                        src_ptr = temp_vec.data();
                    }

                    for (int k = 0; k < d_; ++k) {
                        input_values.push_back((src_ptr[k] - mean_[k]) / std_[k]);
                    }
                }

                std::vector<int64_t> input_shape = {static_cast<int64_t>(current_bs), d_};
                try {
                    Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
                        memory_info, input_values.data(), input_values.size(), input_shape.data(), 2);
                    auto output_tensors = ort_session_->Run(
                        Ort::RunOptions{nullptr}, input_node_names_ptr_.data(), &input_tensor, 1, output_node_names_ptr_.data(), 1);
                    float* output_arr = output_tensors[0].GetTensorMutableData<float>();
                    for (size_t j = 0; j < current_bs; ++j) {
                        int node_idx = i + j;
                        node_vectors_reduced_[node_idx].assign(output_arr + j * d_reduced_, output_arr + (j + 1) * d_reduced_);
                    }
                } catch (const std::exception& e) {
                    std::cerr << "❌ Error in batch " << i << ": " << e.what() << std::endl;
                }
                for(size_t k=0; k<current_bs; ++k) bar.update();
            }
            bar.finish();
        }
#endif
        else {
            std::cout << "⚠️ No Encoder active. Using raw vectors (d=" << d_ << ")." << std::endl;
            node_vectors_reduced_ = node_vectors_;
            d_reduced_ = d_; 
        }
    }

    std::vector<std::unordered_set<int>> getConnectedComponents(const std::vector<std::vector<int>>& graph) {
        std::vector<std::unordered_set<int>> components;
        std::vector<bool> visited(graph.size(), false);
        for (size_t i = 0; i < graph.size(); ++i) {
            if (!visited[i]) {
                std::unordered_set<int> component;
                std::queue<int> q;
                q.push(i);
                visited[i] = true;
                component.insert(i);
                while (!q.empty()) {
                    int u = q.front(); q.pop();
                    for (int v : graph[u]) {
                        if (!visited[v]) {
                            visited[v] = true;
                            component.insert(v);
                            q.push(v);
                        }
                    }
                }
                components.push_back(component);
            }
        }
        return components;
    }

    void ensureConnectivity(std::vector<std::vector<int>>& graph) {
        auto components = getConnectedComponents(graph);
        if (components.size() <= 1) return;
        std::cout << "  [Connectivity] Merging " << components.size() << " components..." << std::endl;
        for (size_t i = 0; i < components.size() - 1; ++i) {
            int best_u = -1, best_v = -1;
            float min_dist = std::numeric_limits<float>::max();
            int limit = 0;
            for (int u : components[i]) {
                if(++limit > 50) break; 
                for (int v : components[i+1]) {
                    float d = computeCenterDistance(u, v);
                    if (d < min_dist) { min_dist = d; best_u = u; best_v = v; }
                }
            }
            if (best_u != -1) {
                graph[best_u].push_back(best_v);
                graph[best_v].push_back(best_u);
            }
        }
    }

public:
    ~GraphProcessor() { if(pca_mat_) delete pca_mat_; }

    bool loadData(const std::string& acpg_file, const std::string& cluster_file, 
                  const std::string& model_path, bool is_pca) {
        try {
            std::cout << "Loading ACPG Index..." << std::endl;
            acpg_index_ = std::make_unique<acsg::IndexACSG>();
            acpg_index_->loadACPG(acpg_file.c_str());
            auto flat = dynamic_cast<faiss::IndexFlat*>(acpg_index_->storage);
            if (!flat) return false;
            int n = acpg_index_->ntotal;
            d_ = acpg_index_->d;
            node_vectors_.resize(n);
            const float* xb = flat->get_xb();
            #pragma omp parallel for
            for (int i=0; i<n; ++i) {
                node_vectors_[i].resize(d_);
                std::memcpy(node_vectors_[i].data(), xb + i*d_, d_*sizeof(float));
            }
        } catch (...) { return false; }

        if (is_pca) initPCAEncoder(model_path);
        else initNeuralEncoder(model_path);
        
        applyEncoding();

        std::ifstream file(cluster_file);
        if (!file) return false;
        json data; file >> data;
        
        if (data.contains("combined_centers") && !data["combined_centers"].is_null()) {
            combined_centers_ = data["combined_centers"].get<std::vector<int>>();
        } 
        else if (data.contains("top_centers")) {
            std::vector<int> top = data["top_centers"].get<std::vector<int>>();
            std::vector<int> bottom = data["bottom_centers"].get<std::vector<int>>();
            
            std::unordered_set<int> seen;
            combined_centers_.clear();
            
            for (int id : top) {
                if (seen.find(id) == seen.end()) {
                    combined_centers_.push_back(id);
                    seen.insert(id);
                }
            }
            for (int id : bottom) {
                if (seen.find(id) == seen.end()) {
                    combined_centers_.push_back(id);
                    seen.insert(id);
                }
            }
            std::cout << "⚠️ Merged top/bottom centers. Order preserved (NO SORT)." << std::endl;
        } else {
            std::cerr << "❌ JSON Error: Missing 'combined_centers'." << std::endl;
            return false;
        }
        
        // ❌❌❌ 再次确认：删除了 sort！ ❌❌❌
        // std::sort(combined_centers_.begin(), combined_centers_.end());
        
        auto weights = acpg_index_->get_acpg_weights();
        combined_densities_.resize(combined_centers_.size());
        rho_max_ = 0.0f;
        global_max_gamma_val_ = -1.0f;
        
        for (size_t i=0; i<combined_centers_.size(); ++i) {
            int id = combined_centers_[i];
            float w = (static_cast<size_t>(id) < weights.size()) ? weights[id] : 1.0f;
            combined_densities_[i] = w;
            if (w > rho_max_) rho_max_ = w;
            if (w > global_max_gamma_val_) {
                global_max_gamma_val_ = w;
                global_max_gamma_local_idx_ = (int)i;
            }
        }
        
        double total_d = 0;
        int samples = 0;
        int n_sample = std::min(1000, (int)combined_centers_.size());
        for (int i=0; i<n_sample; ++i) {
            for (int j=i+1; j<n_sample; ++j) {
                total_d += std::sqrt(computeCenterDistance(i, j)); 
                samples++;
            }
        }
        avg_dist_ = samples > 0 ? (float)(total_d / samples) : 1.0f;
        std::cout << "✅ Loaded " << combined_centers_.size() << " centers." << std::endl;
        return true;
    }

    void loadExternalGraph(const std::string& graph_file) {
        std::cout << "\n>>> Loading Neural Graph from " << graph_file << std::endl;
        std::ifstream in(graph_file);
        if (!in) {
            std::cerr << "❌ Failed to open graph file. Falling back to Gravity Graph." << std::endl;
            buildGravityGraph(32);
            return;
        }

        int N, K;
        in >> N >> K;
        if (N != (int)combined_centers_.size()) {
            std::cerr << "⚠️ Mismatch in node count! Centers: " << combined_centers_.size() 
                      << ", Graph: " << N << ". Building Gravity Graph instead." << std::endl;
            buildGravityGraph(32);
            return;
        }

        gravity_graph_.resize(N);
        std::string line;
        std::getline(in, line); 

        int loaded_edges = 0;
        for (int i = 0; i < N; ++i) {
            std::getline(in, line);
            std::stringstream ss(line);
            int neighbor;
            while (ss >> neighbor) {
                if (neighbor >= 0 && neighbor < N && neighbor != i) {
                    gravity_graph_[i].push_back(neighbor);
                    loaded_edges++;
                }
            }
        }
        ensureConnectivity(gravity_graph_);
        std::cout << "✅ Loaded Neural Graph (" << N << " nodes, " << loaded_edges << " edges)." << std::endl;
    }

    void buildGravityGraph(int K) {
        std::cout << "\n>>> Building Standard Gravity Graph..." << std::endl;
        int n = combined_centers_.size();
        gravity_graph_.resize(n);
        float alpha = 1.2f; 
        float d_avg_sq = avg_dist_ * avg_dist_;
        float eps = 1e-5f;

        ProgressBar bar(n);
        #pragma omp parallel for schedule(dynamic)
        for (int i = 0; i < n; ++i) {
            float rho_i = combined_densities_[i];
            int k_grav = std::min((int)(K * std::pow(rho_i / rho_max_, alpha)), (int)(K * 0.8));
            int k_geo = K - k_grav;
            
            std::vector<std::pair<float, int>> geo_cands, grav_cands;
            for (int j = 0; j < n; ++j) {
                if (i == j) continue;
                float dist_sq = computeCenterDistance(i, j);
                geo_cands.emplace_back(dist_sq, j);
                float force = (rho_i * combined_densities_[j]) / (dist_sq / d_avg_sq + eps);
                grav_cands.emplace_back(force, j);
            }
            std::partial_sort(geo_cands.begin(), geo_cands.begin() + k_geo, geo_cands.end());
            std::partial_sort(grav_cands.begin(), grav_cands.begin() + k_grav, grav_cands.end(), [](auto& a, auto& b){return a.first > b.first;});

            std::set<int> neighbors;
            for (int k=0; k<k_geo; ++k) neighbors.insert(geo_cands[k].second);
            for (int k=0; k<k_grav; ++k) neighbors.insert(grav_cands[k].second);
            
            int fill = k_geo;
            while(neighbors.size() < (size_t)K && fill < (int)geo_cands.size()) neighbors.insert(geo_cands[fill++].second);
            
            gravity_graph_[i].assign(neighbors.begin(), neighbors.end());
            if (omp_get_thread_num() == 0) bar.update();
        }
        bar.finish();
        ensureConnectivity(gravity_graph_);
    }

    void generateCenterMaxList(int limit = 1024) {
        auto weights = acpg_index_->get_acpg_weights();
        center_max_points_.clear();
        std::vector<std::pair<float, int>> center_candidates;
        for (int id : combined_centers_) {
            float w = (static_cast<size_t>(id) < weights.size()) ? weights[id] : 0.0f;
            center_candidates.push_back({w, id});
        }
        std::sort(center_candidates.begin(), center_candidates.end(), [](auto& a, auto& b){return a.first > b.first;});
        for (auto& p : center_candidates) {
            if (center_max_points_.size() >= (size_t)limit) break;
            center_max_points_.push_back(p.second);
        }
    }

    void generateEntryPoints() {
        if (combined_centers_.empty()) return;
        entry_points_.resize(combined_centers_.size());
        #pragma omp parallel for
        for(size_t i=0; i<combined_centers_.size(); ++i) entry_points_[i] = {combined_centers_[i]};
    }

    void save(const std::string& output_dir) {
        json output;
        output["combined_centers"] = combined_centers_;
        output["entry_points"] = entry_points_;
        output["knn_12k_graph"] = gravity_graph_; 
        output["center_max_points"] = center_max_points_;
        
        std::vector<std::vector<float>> centers_reduced_vec;
        centers_reduced_vec.reserve(combined_centers_.size());
        for (int id : combined_centers_) centers_reduced_vec.push_back(node_vectors_reduced_[id]);
        output["centers_reduced"] = centers_reduced_vec;

        output["global_max_gamma_local_idx"] = global_max_gamma_local_idx_;
        
        std::ofstream f1(output_dir + "entry_points.json"); 
        f1 << output.dump(4);
        std::cout << "✅ Saved unified Graph to " << output_dir << "entry_points.json" << std::endl;
    }
};

int main(int argc, char** argv) {
    argparse::ArgumentParser program("graph_processor");
    program.add_argument("--acpg").required();
    program.add_argument("--cluster").required();
    program.add_argument("--out").required();
    program.add_argument("--model").default_value(std::string("")); 
    program.add_argument("--use_pca").default_value(false).implicit_value(true);
    program.add_argument("--neural_graph").default_value(std::string("")); 

    try {
        program.parse_args(argc, argv);
    } catch (const std::runtime_error& err) {
        std::cerr << err.what() << std::endl;
        std::cerr << program;
        return 1;
    }

    std::string acpg_file = program.get<std::string>("--acpg");
    std::string cluster_file = program.get<std::string>("--cluster");
    std::string output_dir = program.get<std::string>("--out");
    std::string model_path = program.get<std::string>("--model");
    bool is_pca = program.get<bool>("--use_pca");
    std::string neural_graph_path = program.get<std::string>("--neural_graph");

    if (output_dir.back() != '/') output_dir += "/";

    omp_set_dynamic(0);
    omp_set_num_threads(omp_get_max_threads());

    GraphProcessor processor;
    if (!processor.loadData(acpg_file, cluster_file, model_path, is_pca)) return 1;
    
    processor.generateCenterMaxList(1024);
    processor.generateEntryPoints(); 

    if (!neural_graph_path.empty()) {
        processor.loadExternalGraph(neural_graph_path);
    } else {
        processor.buildGravityGraph(32);
    }
    
    processor.save(output_dir);
    return 0;
}
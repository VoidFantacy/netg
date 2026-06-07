#include <ACSG/IndexACSG.h>
// IndexACSG.cpp 开头新增一行
#include <fstream>  
// 解决 std::ofstream/std::ifstream 类型未定义问题

#include <faiss/IndexNSG.h>

#include <omp.h>
#include <MRNN_Descent/IndexMRNNDescent.h>
#include <cinttypes>
#include <memory>
#include <stack>
#include <vector>
#include <algorithm>


#include <faiss/IndexFlat.h>
#include <faiss/impl/AuxIndexStructures.h>
#include <faiss/impl/FaissAssert.h>
#include <faiss/utils/Heap.h>
#include <faiss/utils/distances.h>
#include <iostream>
#include <string>     // 用于 std::to_string、std::string
#include <filesystem> // 用于文件大小检查（若用 C++17）
namespace fs = std::filesystem;  // 全局命名空间下的fs

namespace acsg
{
    using namespace faiss;

    IndexACSG::IndexACSG(int d, int R, MetricType metric) : Index(d, metric), acsg(R)
    {
        this->nsg_R = R; // <--- 【必须加上这一行】
    }

    IndexACSG::IndexACSG(Index *storage, int R)
        : Index(storage->d, storage->metric_type),
          acsg(R),
          storage(storage),
          build_type(1)
    {
        this->nsg_R = R;
    }

    IndexACSG::~IndexACSG()
    {
        if (own_fields)
        {
            delete storage;
        }
    }

    void IndexACSG::build(idx_t n, const float *x, idx_t *knn_graph, int R)
    {
        FAISS_THROW_IF_NOT_MSG(
            storage,
            "Please use IndexNSGFlat (or variants) instead of IndexNSG directly");
        FAISS_THROW_IF_NOT_MSG(
            !is_built && ntotal == 0, "The IndexNSG is already built");

        storage->add(n, x);
        ntotal = storage->ntotal;

        // check the knn graph

        const Graph<idx_t> knng(knn_graph, n, R);
        acsg.build(storage, n, knng, verbose);
        is_built = true;
    }
    void IndexACSG::add(idx_t n, const float *x)
    {

        FAISS_THROW_IF_NOT_MSG(
            storage,
            "Please use IndexACSGFlat (or variants) "
            "instead of IndexACSG directly");
        FAISS_THROW_IF_NOT(is_trained);

        FAISS_THROW_IF_NOT_MSG(
            !is_built && ntotal == 0,
            "ACSG does not support incremental addition");

        std::vector<idx_t> knng;
        if (build_type == 0)
        {
            auto index = mrnndescent::IndexMRNNDescent(storage);
            index.mrnndescent.S = 20;
            index.mrnndescent.R = 96;
            index.mrnndescent.tau = 15;
            index.mrnndescent.iter1 = 4;
            index.mrnndescent.iter2 = 15;
            index.verbose = true;

            index.add(n, x);
            ntotal = storage->ntotal;
            acsg.enterpoint = index.mrnndescent.ep_;
            auto graph = index.mrnndescent.final_graph;
            auto offsets = index.mrnndescent.offsets;
            int K = 0;
            for (size_t i = 0; i < ntotal; i++)
            {
                int offset = offsets[i];
                int m = offsets[i + 1] - offset;
                K = std::max(K, m);
            }
            knng.resize(ntotal * K);
            for (idx_t i = 0; i < ntotal; i++)
            {
                int offset = offsets[i];
                int m = offsets[i + 1] - offset;
                for (idx_t j = 0; j < K; j++)
                {
                    if (j < m)
                    {
                        knng[i * K + j] = graph[offset + j];
                    }
                    else
                    {
                        knng[i * K + j] = -1;
                    }
                }
            }
            const Graph<idx_t> knn_graph(knng.data(), n, K);
            acsg.build(storage, n, knn_graph, verbose);
        }
        else if (build_type == 1) //  build with nsg
        {
            if (verbose)
            {
                printf("nsg::build R=%d, L=%d, C=%d\n", nsg_R, nsg_L, nsg_C);
            }

            faiss::IndexNSG index(storage, nsg_R);
            index.nsg.R = nsg_R;
            index.nsg.L = nsg_L; 
            index.nsg.C = nsg_C;
            index.own_fields = false;
            index.verbose = verbose;
            // prevent IndexNSG from deleting the storage
            index.own_fields = false;
            index.add(n, x);

            std::vector<idx_t> knng;
            // storage->add is already implicit called in IndexNSG.add
            ntotal = storage->ntotal;
            FAISS_THROW_IF_NOT(ntotal == n);
            const auto &graph = *index.nsg.final_graph;
            knng.resize(ntotal * graph.K);
            for (int i = 0; i < ntotal; i++)
            { // 遍历所有节点
                for (int j = 0; j < graph.K; j++)
                { // 遍历每个节点的 K 个邻居
                    knng[i * graph.K + j] = graph.at(i, j);
                }
            }
            acsg.enterpoint = index.nsg.enterpoint;
            const Graph<idx_t> knn_graph(knng.data(), n, graph.K);
            acsg.build(storage, n, knn_graph, verbose);
        }

        if (acsg.final_graph) {
        std::cout << "🏗️ [Build Phase] Post-processing: Ensuring Graph Connectivity..." << std::endl;
        fix_connectivity();
        }

        is_built = true;
    }

    // 蚁群搜索训练函数：使用训练集数据优化ACO路径信息素
// 参数说明：
//   train_size: 训练样本数量
//   train_set: 训练样本数据（维度为d）
//   k: 搜索返回的近邻数
//   train_gt: 训练样本的真实近邻结果（用于评估路径准确性）
void IndexACSG::antSearch(idx_t train_size, const float *train_set, idx_t k, idx_t *train_gt)
    {
        // =========================================================
        // 🚨 优化配置：每轮最大训练样本数
        // 对于 100k 级别的查询集，每轮只采 5000 个足够收敛了
        const idx_t MAX_TRAIN_SAMPLE = 5000; 
        // =========================================================

        std::cout << "Ants are searching..." << std::endl;
        
        // 计算实际每轮跑多少个
        idx_t epoch_size = std::min(train_size, MAX_TRAIN_SAMPLE);

        std::cout << "\n=== ACO Algorithm Parameters ===" << std::endl;
        std::cout << "Alpha (Heuristic weight) : " << acsg.alpha << std::endl;
        std::cout << "Beta  (Pheromone weight) : " << acsg.beta << std::endl;
        std::cout << "Rho   (Evaporation rate) : " << acsg.rho << std::endl;
        std::cout << "Lambda                   : " << acsg.lambda << std::endl;
        std::cout << "Iterations               : " << iterations << std::endl;
        std::cout << "Ants per query           : " << new_ant_nums << std::endl;
        std::cout << "Configured Search L      : " << acsg.search_L << std::endl;
        std::cout << "Ground Truth K           : " << k << std::endl;
        std::cout << "Effective L (max(L, K))  : " << std::max(acsg.search_L, (int)k) << std::endl;
        std::cout << "Total Queries            : " << train_size << std::endl;
        std::cout << "Training Batch Size      : " << epoch_size << " (Stochastic Sampling)" << std::endl;
        std::cout << "================================\n" << std::endl;

        if (!train_set || !train_gt) {
            std::cerr << "Error: train_set or train_gt is nullptr!" << std::endl;
            return;
        }

        int L = std::max(acsg.search_L, (int)k); 
        
        // 初始化索引池 0 ~ N-1
        std::vector<idx_t> indices(train_size);
        for (idx_t i = 0; i < train_size; i++) indices[i] = i;

        std::random_device rd;
        std::mt19937 g(rd()); 

        // 优化：paths 只需要存当前 batch 的结果，不需要存全量
        // 大小 = batch_size * ants
        std::vector<std::tuple<std::vector<int>, double>> paths(epoch_size * new_ant_nums); 

        for (size_t iter = 0; iter < iterations; iter++)
        {
            std::cout << "Iteration " << iter + 1 << "/" << iterations << "..." << std::endl;
            
            // 每一轮都重新洗牌，实现随机采样
            std::shuffle(indices.begin(), indices.end(), g);

            idx_t check_period = InterruptCallback::get_period_hint(d * L);

            // ⚠️ 关键修改：循环只跑到 epoch_size，而不是 train_size
            for (idx_t i0 = 0; i0 < epoch_size; i0 += check_period)
            {
                idx_t i1 = std::min(i0 + check_period, epoch_size);

#pragma omp parallel
                {
                    VisitedTable vt(ntotal);
                    std::unique_ptr<DistanceComputer> dis(storage_distance_computer(storage));

#pragma omp for
                    for (idx_t j = i0; j < i1; j++)
                    {
                        // 1. 获取真实的查询 ID (从洗牌后的列表中取)
                        idx_t sample_idx = indices[j]; 
                        
                        // 2. 设置查询向量
                        dis->set_query(train_set + sample_idx * d);

                        for (int ant_id = 0; ant_id < new_ant_nums; ++ant_id) 
                        {
                            auto [path, accuracy] = acsg.ant_search(*dis, k, train_gt + sample_idx * k, vt);
                            
                            // 3. 存入 paths (注意：这里用 j 而不是 sample_idx，因为 paths 只有 batch 大小)
                            size_t local_path_idx = j * new_ant_nums + ant_id;
                            paths[local_path_idx] = {path, accuracy};
                            
                            vt.advance(); 
                        }
                    }
                }
                InterruptCallback::check();
            }

            // 更新信息素 (传入的是当前 Batch 的采样结果)
            update_pheromone(paths);
        }

        acsg.update_weight();
        
        std::cout << "\n=== Final Weight Distribution ===" << std::endl;
        acsg.print_weight_distribution();
    }


    void IndexACSG::update_pheromone(std::vector<std::tuple<std::vector<int>, double>>& paths)
    {
        std::cout << "Updating pheromones (Elite Strategy)..." << std::endl;
        
        // 1. 先计算全局真实平均误差 (用于监控)
        double total_loss = 0.0;
        double total_len = 0.0; // 新增
        #pragma omp parallel for reduction(+:total_loss)
        for (size_t i = 0; i < paths.size(); ++i) {
            total_loss += std::get<1>(paths[i]);
            total_len += std::get<0>(paths[i]).size(); // 累加路径长度
        }
        // 打印双指标
        std::cerr << "Avg Error: " << total_loss / paths.size() 
                << ", Avg Hops: " << total_len / paths.size() << std::endl;

        // 2. 全局挥发
        acsg.decrease_pheromone();

        // 3. 筛选精英路径 (Fix Imbalance / Negative Transfer)
        // 对路径按误差从小到大排序 (Accuracy在这里代表误差，越小越好)
        std::sort(paths.begin(), paths.end(), 
            [](const auto& a, const auto& b) {
                double err_a = std::get<1>(a);
                double err_b = std::get<1>(b);
                if (std::abs(err_a - err_b) > 1e-6) {
                    return err_a < err_b; // 误差明显不同，选误差小的
                }
                // 误差相同（都是0），选步数少的（路径长度在 tuple 的第0个位置）
                return std::get<0>(a).size() < std::get<0>(b).size();
            });

        // 只选取前 30% 的优质路径进行信息素更新
        // 这样可以剔除那些“走偏”的路径，防止错误信息素累积
        float elite_ratio = 0.3f; 
        size_t top_k = std::max((size_t)1, (size_t)(paths.size() * elite_ratio));
        
        std::cout << "Updating top " << top_k << " paths (" << (elite_ratio * 100) << "%)..." << std::endl;

        // 4. 只对精英路径增强信息素
        #pragma omp parallel for
        for (size_t i = 0; i < top_k; ++i)
        {
            const auto& [path, accuracy] = paths[i];
            acsg.update_pheromone(path, accuracy);
        }
    }

    void IndexACSG::train(idx_t n, const float *x)
    {
        FAISS_THROW_IF_NOT_MSG(
            storage,
            "Please use IndexNSGFlat (or variants) instead of IndexNSG directly");
        // nsg structure does not require training
        storage->train(n, x);
        is_trained = true;
    }

    void IndexACSG::search(
        idx_t n,
        const float *x,
        idx_t k,
        float *distances,
        idx_t *labels,
        const SearchParameters *params) const
    {
        FAISS_THROW_IF_NOT_MSG(
            !params, "search params not supported for this index");
        FAISS_THROW_IF_NOT_MSG(
            storage,
            "Please use IndexNSGFlat (or variants) instead of IndexNSG directly");

        int L = std::max(acsg.search_L, (int)k); // in case of search L = -1
        idx_t check_period = InterruptCallback::get_period_hint(d * L);

        for (idx_t i0 = 0; i0 < n; i0 += check_period)
        {
            idx_t i1 = std::min(i0 + check_period, n);

#pragma omp parallel
            {
                VisitedTable vt(ntotal);

                std::unique_ptr<DistanceComputer> dis(
                    storage_distance_computer(storage));

#pragma omp for
                for (idx_t i = i0; i < i1; i++)
                {
                    idx_t *idxi = labels + i * k;
                    float *simi = distances + i * k;
                    dis->set_query(x + i * d);

                    acsg.search(*dis, k, idxi, simi, vt);

                    vt.advance();
                }
            }
            InterruptCallback::check();
        }

        if (is_similarity_metric(metric_type))
        {
            // we need to revert the negated distances
            for (size_t i = 0; i < k * n; i++)
            {
                distances[i] = -distances[i];
            }
        }
    }
    void IndexACSG::search_ACO(
        idx_t n,
        const float *x,
        idx_t k,
        float *distances,
        idx_t *labels,
        const SearchParameters *params)
    {
        FAISS_THROW_IF_NOT_MSG(
            !params, "search params not supported for this index");
        FAISS_THROW_IF_NOT_MSG(
            storage,
            "Please use IndexNSGFlat (or variants) instead of IndexNSG directly");
        acsg.NDC = 0;
        int L = std::max(acsg.search_L, (int)k); // in case of search L = -1
        idx_t check_period = InterruptCallback::get_period_hint(d * L);

        for (idx_t i0 = 0; i0 < n; i0 += check_period)
        {
            idx_t i1 = std::min(i0 + check_period, n);

#pragma omp parallel
            {
                VisitedTable vt(ntotal);

                std::unique_ptr<DistanceComputer> dis(
                    storage_distance_computer(storage));

#pragma omp for
                for (idx_t i = i0; i < i1; i++)
                {
                    idx_t *idxi = labels + i * k;
                    float *simi = distances + i * k;
                    dis->set_query(x + i * d);
                    acsg.search_ACO(*dis, k, idxi, simi, vt);
                    vt.advance();
                }
            }
            InterruptCallback::check();
        }

     
    }

    void IndexACSG::search_v1(
        idx_t n,
        const float *x,
        idx_t k,
        float *distances,
        idx_t *labels,
        const SearchParameters *params)
    {
        FAISS_THROW_IF_NOT_MSG(
            !params, "search params not supported for this index");
        FAISS_THROW_IF_NOT_MSG(
            storage,
            "Please use IndexNSGFlat (or variants) instead of IndexNSG directly");

        int L = std::max(acsg.search_L, (int)k); // in case of search L = -1
        idx_t check_period = InterruptCallback::get_period_hint(d * L);
        acsg.NDC = 0;
        for (idx_t i0 = 0; i0 < n; i0 += check_period)
        {
            idx_t i1 = std::min(i0 + check_period, n);

#pragma omp parallel
            {
                VisitedTable vt(ntotal);

                std::unique_ptr<DistanceComputer> dis(
                    storage_distance_computer(storage));

#pragma omp for
                for (idx_t i = i0; i < i1; i++)
                {
                    idx_t *idxi = labels + i * k;
                    float *simi = distances + i * k;
                    dis->set_query(x + i * d);
                    acsg.search_v1(*dis, k, idxi, simi, vt);
                    vt.advance();
                }
            }
            InterruptCallback::check();
        }

        // float mean_rdrr = 0;
        // for (int i = 0; i < n; i++)
        // {
        //     float rdrr = 0;
        //     for (size_t j = 0; j < k; j++)
        //     {
        //         if (gt_distances[i * k + j] == 0)
        //             continue;
        //         /* code */
        //         rdrr += (distances[i * k + j] / gt_distances[i * k + j]) - 1;
        //     }
        //     rdrr = rdrr / k;
        //     mean_rdrr += rdrr;
        // }
        // mean_rdrr = mean_rdrr / n;
        // std::cout << "L = " << L << std::endl;
        // std::cout << "NDC = " << acsg.NDC << std::endl;
        // std::cout << "mean_rdrr = " << mean_rdrr << std::endl;

        if (is_similarity_metric(metric_type))
        {
            // we need to revert the negated distances
            for (size_t i = 0; i < k * n; i++)
            {
                distances[i] = -distances[i];
            }
        }
    }

    void IndexACSG::brute_force_search(
        idx_t nb,
        const float *xb,
        idx_t n,
        const float *x,
        idx_t k,
        float *distances,
        idx_t *labels,
        const SearchParameters *params)
    {
        FAISS_THROW_IF_NOT_MSG(
            !params, "search params not supported for this index");
        FAISS_THROW_IF_NOT_MSG(
            storage,
            "Please use IndexNSGFlat (or variants) instead of IndexNSG directly");

        std::cerr << "k = " << k << std::endl;
        acsg.NDC = 0;
        for (idx_t i = 0; i < n; i++)
        {

            std::unique_ptr<DistanceComputer> dis(
                storage_distance_computer(storage));

            idx_t *idxi = labels + i * k;
            float *simi = distances + i * k;
            dis->set_query(x + i * d);
            acsg.brute_force_search(*dis, k, idxi, simi, nb, xb);
        }
    }

    void IndexACSG::reset()
    {
        acsg.reset();
        storage->reset();
        ntotal = 0;
        is_built = false;
    }

    void IndexACSG::reconstruct(idx_t key, float *recons) const
    {
        storage->reconstruct(key, recons);
    }

    /**************************************************************
     * IndexNSGFlat implementation
     **************************************************************/

    IndexACSGFlat::IndexACSGFlat()
    {
        is_trained = true;
    }

    IndexACSGFlat::IndexACSGFlat(int d, int R, MetricType metric)
        : IndexACSG(new IndexFlat(d, metric), R)
    {
        own_fields = true;
        is_trained = true;
    }

    // 在类实现中添加 save 和 load 方法的具体实现
// IndexACSG::save 方法（无错误，保持之前的完整逻辑）
// 带参数打印的save方法  保存索引图
void IndexACSG::save(const char* filename) const {
    FAISS_THROW_IF_NOT_MSG(is_built, "Index must be built before saving");
    std::ofstream out(filename, std::ios::binary);
    if (!out) FAISS_THROW_MSG("Failed to open file for writing: " + std::string(filename));

    std::cout << "Saving index to " << filename << "..." << std::endl;

    // 1. 版本号
    const int VERSION = 1;
    out.write(reinterpret_cast<const char*>(&VERSION), sizeof(VERSION));
    if (!out.good()) { out.close(); FAISS_THROW_MSG("Failed to write version"); }

    // 2. 核心元数据
    out.write(reinterpret_cast<const char*>(&ntotal), sizeof(ntotal));
    out.write(reinterpret_cast<const char*>(&d), sizeof(d));
    out.write(reinterpret_cast<const char*>(&metric_type), sizeof(metric_type));
    out.write(reinterpret_cast<const char*>(&is_trained), sizeof(is_trained));
    out.write(reinterpret_cast<const char*>(&is_built), sizeof(is_built));
    out.write(reinterpret_cast<const char*>(&build_type), sizeof(build_type));

    if (!out.good()) { out.close(); FAISS_THROW_MSG("Failed to write base metadata"); }

    // 3. ACSG关键参数
    out.write(reinterpret_cast<const char*>(&acsg.alpha), sizeof(acsg.alpha));
    out.write(reinterpret_cast<const char*>(&acsg.beta), sizeof(acsg.beta));
    out.write(reinterpret_cast<const char*>(&acsg.rho), sizeof(acsg.rho));
    out.write(reinterpret_cast<const char*>(&acsg.lambda), sizeof(acsg.lambda));
    out.write(reinterpret_cast<const char*>(&acsg.iterations), sizeof(acsg.iterations));
    out.write(reinterpret_cast<const char*>(&acsg.thresholdrej), sizeof(int));
    out.write(reinterpret_cast<const char*>(&acsg.search_L), sizeof(acsg.search_L));
    out.write(reinterpret_cast<const char*>(&nsg_R), sizeof(nsg_R));
    out.write(reinterpret_cast<const char*>(&acsg.enterpoint), sizeof(int));
    out.write(reinterpret_cast<const char*>(&ant_nums), sizeof(ant_nums));

    // 仅校验大小匹配，不校验内容是否有效
    if (acsg.pheromone.size() != ntotal) {
        out.close();
        FAISS_THROW_MSG("Pheromone size mismatch: " + std::to_string(acsg.pheromone.size()) + 
                       " != " + std::to_string(ntotal));
    }
    if (acsg.weight.size() != ntotal) {
        out.close();
        FAISS_THROW_MSG("Weight size mismatch: " + std::to_string(acsg.weight.size()) + 
                       " != " + std::to_string(ntotal));
    }

    // 保存pheromone和weight
    size_t pheromone_size = acsg.pheromone.size();
    size_t weight_size = acsg.weight.size();
    out.write(reinterpret_cast<const char*>(&pheromone_size), sizeof(pheromone_size));
    out.write(reinterpret_cast<const char*>(acsg.pheromone.data()), pheromone_size * sizeof(float));
    out.write(reinterpret_cast<const char*>(&weight_size), sizeof(weight_size));
    out.write(reinterpret_cast<const char*>(acsg.weight.data()), weight_size * sizeof(float));

    if (!out.good()) { out.close(); FAISS_THROW_MSG("Failed to write ACSG params"); }

    // 4. 图结构：移除-1校验，直接写入所有邻居（包括-1）
    int graph_K = acsg.final_graph ? acsg.final_graph->K : 0;
    out.write(reinterpret_cast<const char*>(&graph_K), sizeof(graph_K));
    
    size_t neighbor_count = (graph_K > 0 && acsg.final_graph) ? (ntotal * graph_K) : 0;
    out.write(reinterpret_cast<const char*>(&neighbor_count), sizeof(neighbor_count));

    if (graph_K > 0 && acsg.final_graph) {
        // 直接写入所有邻居数据，包括-1（不校验）
        for (faiss::idx_t i = 0; i < ntotal; i++) {
            for (int j = 0; j < graph_K; j++) {
                int32_t neighbor = acsg.final_graph->at(i, j);
                out.write(reinterpret_cast<const char*>(&neighbor), sizeof(int32_t));
            }
        }
    }
    if (!out.good()) { out.close(); FAISS_THROW_MSG("Failed to write graph data"); }

    // 5. 向量数据
    if (!storage) { out.close(); FAISS_THROW_MSG("Storage is null"); }
    auto flat_index = dynamic_cast<faiss::IndexFlat*>(storage);
    if (!flat_index || flat_index->ntotal != ntotal || flat_index->d != d) {
        out.close();
        FAISS_THROW_MSG("Storage mismatch: flat_ntotal=" + std::to_string(flat_index->ntotal) 
                       + ", expected=" + std::to_string(ntotal));
    }
    
    size_t vec_count = ntotal * d;
    out.write(reinterpret_cast<const char*>(&vec_count), sizeof(vec_count));
    out.write(reinterpret_cast<const char*>(flat_index->get_xb()), vec_count * sizeof(float));

    if (!out.good()) { out.close(); FAISS_THROW_MSG("Failed to write vector data"); }

    out.close();
    if (out.fail()) FAISS_THROW_MSG("Save failed: " + std::string(filename));

    std::cout << "Index saved successfully (" << ntotal << " vectors, " << d << " dimensions)" << std::endl;
}

//加载索引图
void IndexACSG::load(const char* filename) {
    std::ifstream in(filename, std::ios::binary);
    if (!in) FAISS_THROW_MSG("Failed to open file for reading: " + std::string(filename));

    std::cout << "Loading index from " << filename << "..." << std::endl;

    // 1. 版本号校验
    int VERSION;
    in.read(reinterpret_cast<char*>(&VERSION), sizeof(VERSION));
    if (in.gcount() != sizeof(VERSION)) { in.close(); FAISS_THROW_MSG("Truncated version data"); }
    if (VERSION != 1) { in.close(); FAISS_THROW_MSG("Unsupported version: " + std::to_string(VERSION)); }

    // 2. 恢复核心元数据
    faiss::idx_t loaded_ntotal;
    int loaded_d;
    faiss::MetricType loaded_metric;
    bool loaded_is_trained, loaded_is_built;
    char loaded_build_type;

    in.read(reinterpret_cast<char*>(&loaded_ntotal), sizeof(loaded_ntotal));
    in.read(reinterpret_cast<char*>(&loaded_d), sizeof(loaded_d));
    in.read(reinterpret_cast<char*>(&loaded_metric), sizeof(loaded_metric));
    in.read(reinterpret_cast<char*>(&loaded_is_trained), sizeof(loaded_is_trained));
    in.read(reinterpret_cast<char*>(&loaded_is_built), sizeof(loaded_is_built));
    in.read(reinterpret_cast<char*>(&loaded_build_type), sizeof(loaded_build_type));

    if (loaded_ntotal <= 0 || loaded_d <= 0) {
        in.close();
        FAISS_THROW_MSG("Invalid loaded params: ntotal=" + std::to_string(loaded_ntotal) + ", d=" + std::to_string(loaded_d));
    }

    // 3. 恢复ACSG关键参数
    in.read(reinterpret_cast<char*>(&acsg.alpha), sizeof(acsg.alpha));
    in.read(reinterpret_cast<char*>(&acsg.beta), sizeof(acsg.beta));
    in.read(reinterpret_cast<char*>(&acsg.rho), sizeof(acsg.rho));
    in.read(reinterpret_cast<char*>(&acsg.lambda), sizeof(acsg.lambda));
    in.read(reinterpret_cast<char*>(&acsg.iterations), sizeof(acsg.iterations));
    in.read(reinterpret_cast<char*>(&acsg.thresholdrej), sizeof(int));
    in.read(reinterpret_cast<char*>(&acsg.search_L), sizeof(acsg.search_L));
    in.read(reinterpret_cast<char*>(&nsg_R), sizeof(nsg_R));
    in.read(reinterpret_cast<char*>(&acsg.enterpoint), sizeof(int));
    in.read(reinterpret_cast<char*>(&ant_nums), sizeof(ant_nums));

    // 恢复pheromone和weight并校验大小
    size_t loaded_pheromone_size, loaded_weight_size;
    in.read(reinterpret_cast<char*>(&loaded_pheromone_size), sizeof(loaded_pheromone_size));
    acsg.pheromone.resize(loaded_pheromone_size);
    in.read(reinterpret_cast<char*>(acsg.pheromone.data()), loaded_pheromone_size * sizeof(float));
    
    in.read(reinterpret_cast<char*>(&loaded_weight_size), sizeof(loaded_weight_size));
    acsg.weight.resize(loaded_weight_size);
    in.read(reinterpret_cast<char*>(acsg.weight.data()), loaded_weight_size * sizeof(float));

    // 校验pheromone和weight大小与ntotal一致
    if (acsg.pheromone.size() != loaded_ntotal) {
        in.close();
        FAISS_THROW_MSG("Pheromone size mismatch: loaded=" + std::to_string(acsg.pheromone.size()) + 
                       ", expected=" + std::to_string(loaded_ntotal));
    }
    if (acsg.weight.size() != loaded_ntotal) {
        in.close();
        FAISS_THROW_MSG("Weight size mismatch: loaded=" + std::to_string(acsg.weight.size()) + 
                       ", expected=" + std::to_string(loaded_ntotal));
    }

    // 校验入口点有效性
    if (acsg.enterpoint < 0 || acsg.enterpoint >= loaded_ntotal) {
        in.close();
        FAISS_THROW_MSG("Invalid loaded enterpoint: " + std::to_string(acsg.enterpoint)
                       + " (ntotal=" + std::to_string(loaded_ntotal) + ")");
    }

    // 4. 恢复图结构（核心修改：不因-1中断）
    int loaded_K;
    in.read(reinterpret_cast<char*>(&loaded_K), sizeof(loaded_K));
    size_t loaded_neighbor_count;
    in.read(reinterpret_cast<char*>(&loaded_neighbor_count), sizeof(loaded_neighbor_count));

    const size_t expected_neighbor_count = static_cast<size_t>(loaded_ntotal) * loaded_K;
    if (loaded_K > 0 && loaded_neighbor_count != expected_neighbor_count) {
        in.close();
        FAISS_THROW_MSG("Graph data mismatch: K=" + std::to_string(loaded_K) 
                       + ", neighbor_count=" + std::to_string(loaded_neighbor_count)
                       + ", expected=" + std::to_string(expected_neighbor_count));
    }

    if (loaded_K > 0) {
        acsg.final_graph = std::make_shared<Graph<int32_t>>(loaded_ntotal, loaded_K);
        if (!acsg.final_graph) { in.close(); FAISS_THROW_MSG("Failed to create graph"); }

        size_t read_count = 0;
        for (faiss::idx_t i = 0; i < loaded_ntotal; i++) {
            for (int j = 0; j < loaded_K; j++) {
                int32_t neighbor;
                in.read(reinterpret_cast<char*>(&neighbor), sizeof(int32_t));
                if (in.gcount() != sizeof(int32_t)) {
                    in.close();
                    FAISS_THROW_MSG("Truncated neighbor data at i=" + std::to_string(i) + ", j=" + std::to_string(j));
                }
                acsg.final_graph->at(i, j) = neighbor;
                read_count++;
            }
        }

        if (read_count != loaded_neighbor_count) {
            in.close();
            FAISS_THROW_MSG("Neighbor count mismatch: read=" + std::to_string(read_count) + 
                           ", expected=" + std::to_string(loaded_neighbor_count));
        }

        // 抽样检查无效邻居：仅警告，不中断
        const int sample_count = std::min(100, (int)loaded_ntotal);
        int invalid_count = 0;
        for (int i = 0; i < sample_count; ++i) {
            faiss::idx_t rand_node = rand() % loaded_ntotal;
            for (int j = 0; j < loaded_K; ++j) {
                int32_t neighbor = acsg.final_graph->at(rand_node, j);
                if (neighbor < 0 || neighbor >= (int32_t)loaded_ntotal) {
                    if (invalid_count < 5) {
                        std::cerr << "WARNING: Invalid neighbor at node " << rand_node 
                                  << ", j=" << j << ": " << neighbor << std::endl;
                    }
                    invalid_count++;
                }
            }
        }
        if (invalid_count > 0) {
            std::cerr << "WARNING: Found " << invalid_count << " invalid neighbors in sample. Continuing..." << std::endl;
        }
    } else {
        acsg.final_graph.reset();
    }

    // 5. 恢复向量数据
    if (storage && own_fields) { delete storage; storage = nullptr; }
    size_t loaded_vec_count;
    in.read(reinterpret_cast<char*>(&loaded_vec_count), sizeof(loaded_vec_count));

    size_t expected_vec_count = static_cast<size_t>(loaded_ntotal) * static_cast<size_t>(loaded_d);
    if (loaded_vec_count != expected_vec_count) {
        in.close();
        delete storage;
        FAISS_THROW_MSG("Vector data mismatch: loaded=" + std::to_string(loaded_vec_count) 
                       + ", expected=" + std::to_string(expected_vec_count));
    }

    storage = new faiss::IndexFlat(loaded_d, loaded_metric);
    own_fields = true;
    auto flat_index = dynamic_cast<faiss::IndexFlat*>(storage);
    if (!flat_index) {
        in.close();
        delete storage;
        FAISS_THROW_MSG("Failed to cast to IndexFlat");
    }

    // 直接写入 IndexFlat 内部存储，避免 temp_vec 中转导致峰值内存翻倍
    // （对于 deep10M/128d，temp_vec 会白白占用额外 ~5.4GB 峰值内存）
    // IndexFlat 继承自 IndexFlatCodes，向量以 uint8_t 存于 codes，通过 get_xb() 暴露为 float*
    flat_index->codes.resize(loaded_vec_count * sizeof(float));
    in.read(reinterpret_cast<char*>(flat_index->codes.data()), loaded_vec_count * sizeof(float));
    if (in.gcount() != static_cast<std::streamsize>(loaded_vec_count * sizeof(float))) {
        in.close();
        delete storage;
        FAISS_THROW_MSG("Truncated vector data: got " + std::to_string(in.gcount()) + " bytes");
    }
    flat_index->ntotal = loaded_ntotal;

    if (flat_index->ntotal != loaded_ntotal) {
        in.close();
        delete storage;
        FAISS_THROW_MSG("Vector add failed: flat_ntotal=" + std::to_string(flat_index->ntotal) 
                       + ", expected=" + std::to_string(loaded_ntotal));
    }

    // 6. 同步对象状态并初始化内部状态
    ntotal = loaded_ntotal;
    acsg.ntotal = loaded_ntotal;
    d = loaded_d;
    metric_type = loaded_metric;
    is_trained = loaded_is_trained;
    is_built = loaded_is_built;
    build_type = loaded_build_type;

    // 👇 关键：同步 acsg 内部的 is_built 状态
    acsg.is_built = loaded_is_built;

    acsg.NDC = 0;
    
    in.close();
    // ==============================================
    // 新增：加载完成后输出关键状态校验信息
    // ==============================================
    std::cout << "\n===== Index Load Status Check =====" << std::endl;
    std::cout << "1. Basic flags:" << std::endl;
    std::cout << "   - is_built: " << (is_built ? "true" : "false") << std::endl;
    std::cout << "   - is_trained: " << (is_trained ? "true" : "false") << std::endl;
    
    std::cout << "\n2. Core components:" << std::endl;
    std::cout << "   - final_graph: " << (acsg.final_graph ? "exists" : "nullptr") << std::endl;
    std::cout << "   - storage: " << (storage ? "exists" : "nullptr") << std::endl;
    if (storage) {
        auto flat = dynamic_cast<faiss::IndexFlat*>(storage);
        std::cout << "   - storage.ntotal: " << flat->ntotal << std::endl;
        std::cout << "   - storage.d: " << flat->d << std::endl;
    }
    
    std::cout << "\n3. Graph structure:" << std::endl;
    if (acsg.final_graph) {
        std::cout << "   - graph.N (nodes): " << acsg.final_graph->N << std::endl;
        std::cout << "   - graph.K (neighbors per node): " << acsg.final_graph->K << std::endl;
        std::cout << "   - nsg_R (expected K): " << nsg_R << std::endl;
        std::cout << "   - graph.N matches index.ntotal: " 
                  << (acsg.final_graph->N == ntotal ? "YES" : "NO") << std::endl;
        std::cout << "   - graph.K matches nsg_R: " 
                  << (acsg.final_graph->K == nsg_R ? "YES" : "NO") << std::endl;
    } else {
        std::cout << "   - No graph data available (final_graph is null)" << std::endl;
    }
    
    std::cout << "\n4. Other parameters:" << std::endl;
    std::cout << "   - ntotal (total vectors): " << ntotal << std::endl;
    std::cout << "   - d (dimension): " << d << std::endl;
    std::cout << "   - enterpoint: " << acsg.enterpoint << std::endl;
    std::cout << "====================================\n" << std::endl;

    std::cout << "Index loaded successfully (" << ntotal << " vectors, " << d << " dimensions)" << std::endl;
}

void IndexACSG::fix_connectivity() {
    if (!acsg.final_graph) return;

    // 获取当前时间用于随机数种子
    srand(time(NULL)); 

    idx_t N = ntotal;
    int K = acsg.final_graph->K;
    
    // 使用 vector<bool> 替代 boost::dynamic_bitset (避免依赖)
    std::vector<bool> visited(N, false);
    std::stack<idx_t> s;
    size_t visited_count = 0;

    std::cout << "\n🚑 [Connectivity Fix] Starting Surgical Repair..." << std::endl;
    std::cout << "   - Total Nodes: " << N << std::endl;
    std::cout << "   - Graph K: " << K << std::endl;

    // 1. 从全局入口点开始第一轮扫描
    idx_t root = acsg.enterpoint;
    s.push(root);
    visited[root] = true;
    visited_count++;

    int component_count = 1;

    while (true) {
        // --- Phase 1: 标准 DFS 遍历当前连通分量 ---
        while (!s.empty()) {
            idx_t u = s.top();
            s.pop();

            for (int i = 0; i < K; ++i) {
                idx_t v = acsg.final_graph->at(u, i);
                // 跳过无效边 (-1) 和已访问节点
                if (v >= 0 && v < N && !visited[v]) {
                    visited[v] = true;
                    visited_count++;
                    s.push(v);
                }
            }
        }

        // --- Phase 2: 检查是否全连通 ---
        if (visited_count >= N) {
            std::cout << "✅ [Connectivity Fix] SUCCESS! Graph is fully connected." << std::endl;
            std::cout << "   - Final Visited Count: " << visited_count << "/" << N << std::endl;
            std::cout << "   - Total Components Merged: " << component_count << std::endl;
            break;
        }

        // --- Phase 3: 发现孤岛，执行“接骨手术” ---
        // 这一步逻辑严格参考 GATE: 找一个未访问点，把它连回主大陆
        
        idx_t island_node = -1;
        // 寻找第一个未被访问的节点 (它是孤岛的代表)
        for (idx_t i = 0; i < N; ++i) {
            if (!visited[i]) {
                island_node = i;
                break;
            }
        }

        if (island_node != -1) {
            component_count++;
            
            // [GATE 逻辑对齐] 
            // GATE 会尝试找最近邻，如果找不到则随机找一个已访问节点。
            // 这里为了代码简洁且不依赖原始向量距离计算，直接采用 GATE 的 Fallback 策略：
            // -> "随机选择一个已访问的节点作为连接点 (Connector)"
            // 这样避免了所有孤岛都连向 enterpoint 导致的热点问题。
            
            idx_t connector_node = -1;
            int max_attempts = 1000;
            while(max_attempts--) {
                idx_t candidate = rand() % N;
                if (visited[candidate]) {
                    connector_node = candidate;
                    break;
                }
            }
            // 如果实在运气不好没随机到，就兜底用 enterpoint
            if (connector_node == -1) connector_node = acsg.enterpoint;

            if (component_count <= 10 || component_count % 100 == 0) {
                 std::cout << "⚠️ [Fix] Linking Island (Node " << island_node 
                           << ") <---> Main (Node " << connector_node << ")" 
                           << " | Progress: " << visited_count << "/" << N << std::endl;
            }

            // 💉 手术：建立双向连接
            // ACSG 是定长 K，必须调用安全加边函数
            add_edge_safe(connector_node, island_node); 
            add_edge_safe(island_node, connector_node);

            // 将该节点加入栈，继续 DFS，扫清这个新发现的孤岛
            visited[island_node] = true;
            visited_count++;
            s.push(island_node);
        }
    }
}

// [新增] 安全加边函数 (核心适配：处理 ACSG 的定长 K)
void IndexACSG::add_edge_safe(idx_t u, idx_t v) {
    if (u == v) return;
    int K = acsg.final_graph->K;
    
    // 1. 检查是否已经存在边 (避免重复边)
    for (int i = 0; i < K; ++i) {
        if (acsg.final_graph->at(u, i) == v) return;
    }

    // 2. 尝试找一个空位 (-1) 填入
    for (int i = 0; i < K; ++i) {
        if (acsg.final_graph->at(u, i) == -1) {
            acsg.final_graph->at(u, i) = v;
            return;
        }
    }

    // 3. [ACSG 特有逻辑] 如果满了，必须替换掉一个邻居
    // GATE 是动态数组可以直接 push_back，但我们是固定 K，所以必须牺牲一个旧邻居。
    // 为了连通性，这个牺牲是值得的。随机替换掉一个位置。
    int replace_idx = rand() % K;
    acsg.final_graph->at(u, replace_idx) = v;
}

//保存ACPG图 
void IndexACSG::saveACPG(const char* filename) const {
    FAISS_THROW_IF_NOT_MSG(is_built, "Index must be built before saving");
    std::ofstream out(filename, std::ios::binary);
    if (!out) FAISS_THROW_MSG("Failed to open file for writing: " + std::string(filename));

    std::cout << "Saving index to " << filename << "..." << std::endl;

    // 1. 版本号 - 升级到版本2以支持ACPG权重
    const int VERSION = 2;  // 从1改为2
    out.write(reinterpret_cast<const char*>(&VERSION), sizeof(VERSION));
    if (!out.good()) { out.close(); FAISS_THROW_MSG("Failed to write version"); }

    // 2. 核心元数据
    out.write(reinterpret_cast<const char*>(&ntotal), sizeof(ntotal));
    out.write(reinterpret_cast<const char*>(&d), sizeof(d));
    out.write(reinterpret_cast<const char*>(&metric_type), sizeof(metric_type));
    out.write(reinterpret_cast<const char*>(&is_trained), sizeof(is_trained));
    out.write(reinterpret_cast<const char*>(&is_built), sizeof(is_built));
    out.write(reinterpret_cast<const char*>(&build_type), sizeof(build_type));

    if (!out.good()) { out.close(); FAISS_THROW_MSG("Failed to write base metadata"); }

    // 3. ACSG关键参数
    out.write(reinterpret_cast<const char*>(&acsg.alpha), sizeof(acsg.alpha));
    out.write(reinterpret_cast<const char*>(&acsg.beta), sizeof(acsg.beta));
    out.write(reinterpret_cast<const char*>(&acsg.rho), sizeof(acsg.rho));
    out.write(reinterpret_cast<const char*>(&acsg.lambda), sizeof(acsg.lambda));
    out.write(reinterpret_cast<const char*>(&acsg.iterations), sizeof(acsg.iterations));
    out.write(reinterpret_cast<const char*>(&acsg.thresholdrej), sizeof(int));
    out.write(reinterpret_cast<const char*>(&acsg.search_L), sizeof(acsg.search_L));
    out.write(reinterpret_cast<const char*>(&nsg_R), sizeof(nsg_R));
    out.write(reinterpret_cast<const char*>(&acsg.enterpoint), sizeof(int));
    out.write(reinterpret_cast<const char*>(&ant_nums), sizeof(ant_nums));

    // 校验大小匹配
    if (acsg.pheromone.size() != ntotal) {
        out.close();
        FAISS_THROW_MSG("Pheromone size mismatch: " + std::to_string(acsg.pheromone.size()) + 
                       " != " + std::to_string(ntotal));
    }
    if (acsg.weight.size() != ntotal) {
        out.close();
        FAISS_THROW_MSG("Weight size mismatch: " + std::to_string(acsg.weight.size()) + 
                       " != " + std::to_string(ntotal));
    }

    // 保存pheromone和weight
    size_t pheromone_size = acsg.pheromone.size();
    size_t weight_size = acsg.weight.size();
    out.write(reinterpret_cast<const char*>(&pheromone_size), sizeof(pheromone_size));
    out.write(reinterpret_cast<const char*>(acsg.pheromone.data()), pheromone_size * sizeof(float));
    out.write(reinterpret_cast<const char*>(&weight_size), sizeof(weight_size));
    out.write(reinterpret_cast<const char*>(acsg.weight.data()), weight_size * sizeof(float));

    if (!out.good()) { out.close(); FAISS_THROW_MSG("Failed to write ACSG params"); }

    // 4. 图结构
    int graph_K = acsg.final_graph ? acsg.final_graph->K : 0;
    out.write(reinterpret_cast<const char*>(&graph_K), sizeof(graph_K));
    
    size_t neighbor_count = (graph_K > 0 && acsg.final_graph) ? (ntotal * graph_K) : 0;
    out.write(reinterpret_cast<const char*>(&neighbor_count), sizeof(neighbor_count));

    if (graph_K > 0 && acsg.final_graph) {
        for (faiss::idx_t i = 0; i < ntotal; i++) {
            for (int j = 0; j < graph_K; j++) {
                int32_t neighbor = acsg.final_graph->at(i, j);
                out.write(reinterpret_cast<const char*>(&neighbor), sizeof(int32_t));
            }
        }
    }
    if (!out.good()) { out.close(); FAISS_THROW_MSG("Failed to write graph data"); }

    // 5. 向量数据
    if (!storage) { out.close(); FAISS_THROW_MSG("Storage is null"); }
    auto flat_index = dynamic_cast<faiss::IndexFlat*>(storage);
    if (!flat_index || flat_index->ntotal != ntotal || flat_index->d != d) {
        out.close();
        FAISS_THROW_MSG("Storage mismatch: flat_ntotal=" + std::to_string(flat_index->ntotal) 
                       + ", expected=" + std::to_string(ntotal));
    }
    
    size_t vec_count = ntotal * d;
    out.write(reinterpret_cast<const char*>(&vec_count), sizeof(vec_count));
    out.write(reinterpret_cast<const char*>(flat_index->get_xb()), vec_count * sizeof(float));

    if (!out.good()) { out.close(); FAISS_THROW_MSG("Failed to write vector data"); }

    // 6. 新增：保存ACPG图的top入口点
    size_t top_enterpoints_size = acsg.top_enterpoints.size();
    out.write(reinterpret_cast<const char*>(&top_enterpoints_size), sizeof(top_enterpoints_size));
    
    for (const auto& ep : acsg.top_enterpoints) {
        out.write(reinterpret_cast<const char*>(&ep.id), sizeof(ep.id));
        out.write(reinterpret_cast<const char*>(&ep.weight), sizeof(ep.weight));
    }

    if (!out.good()) { out.close(); FAISS_THROW_MSG("Failed to write ACPG top enterpoints"); }

    out.close();
    if (out.fail()) FAISS_THROW_MSG("Save failed: " + std::string(filename));

    std::cout << "Index saved successfully (" << ntotal << " vectors, " << d << " dimensions)" 
              << " with ACPG weights and " << top_enterpoints_size << " top enterpoints" << std::endl;
}

//加载ACPG图
void IndexACSG::loadACPG(const char* filename) {
    std::ifstream in(filename, std::ios::binary);
    if (!in) FAISS_THROW_MSG("Failed to open file for reading: " + std::string(filename));

    std::cout << "Loading index from " << filename << "..." << std::endl;

    // 1. 版本号校验 - 支持版本1和2
    int VERSION;
    in.read(reinterpret_cast<char*>(&VERSION), sizeof(VERSION));
    if (in.gcount() != sizeof(VERSION)) { in.close(); FAISS_THROW_MSG("Truncated version data"); }
    if (VERSION != 1 && VERSION != 2) { 
        in.close(); 
        FAISS_THROW_MSG("Unsupported version: " + std::to_string(VERSION)); 
    }

    std::cout << "Loading index version: " << VERSION << std::endl;

    // 2. 恢复核心元数据
    faiss::idx_t loaded_ntotal;
    int loaded_d;
    faiss::MetricType loaded_metric;
    bool loaded_is_trained, loaded_is_built;
    char loaded_build_type;

    in.read(reinterpret_cast<char*>(&loaded_ntotal), sizeof(loaded_ntotal));
    in.read(reinterpret_cast<char*>(&loaded_d), sizeof(loaded_d));
    in.read(reinterpret_cast<char*>(&loaded_metric), sizeof(loaded_metric));
    in.read(reinterpret_cast<char*>(&loaded_is_trained), sizeof(loaded_is_trained));
    in.read(reinterpret_cast<char*>(&loaded_is_built), sizeof(loaded_is_built));
    in.read(reinterpret_cast<char*>(&loaded_build_type), sizeof(loaded_build_type));

    if (loaded_ntotal <= 0 || loaded_d <= 0) {
        in.close();
        FAISS_THROW_MSG("Invalid loaded params: ntotal=" + std::to_string(loaded_ntotal) + ", d=" + std::to_string(loaded_d));
    }

    // 3. 恢复ACSG关键参数
    in.read(reinterpret_cast<char*>(&acsg.alpha), sizeof(acsg.alpha));
    in.read(reinterpret_cast<char*>(&acsg.beta), sizeof(acsg.beta));
    in.read(reinterpret_cast<char*>(&acsg.rho), sizeof(acsg.rho));
    in.read(reinterpret_cast<char*>(&acsg.lambda), sizeof(acsg.lambda));
    in.read(reinterpret_cast<char*>(&acsg.iterations), sizeof(acsg.iterations));
    in.read(reinterpret_cast<char*>(&acsg.thresholdrej), sizeof(int));
    in.read(reinterpret_cast<char*>(&acsg.search_L), sizeof(acsg.search_L));
    in.read(reinterpret_cast<char*>(&nsg_R), sizeof(nsg_R));
    in.read(reinterpret_cast<char*>(&acsg.enterpoint), sizeof(int));
    in.read(reinterpret_cast<char*>(&ant_nums), sizeof(ant_nums));

    // 恢复pheromone和weight并校验大小
    size_t loaded_pheromone_size, loaded_weight_size;
    in.read(reinterpret_cast<char*>(&loaded_pheromone_size), sizeof(loaded_pheromone_size));
    acsg.pheromone.resize(loaded_pheromone_size);
    in.read(reinterpret_cast<char*>(acsg.pheromone.data()), loaded_pheromone_size * sizeof(float));
    
    in.read(reinterpret_cast<char*>(&loaded_weight_size), sizeof(loaded_weight_size));
    acsg.weight.resize(loaded_weight_size);
    in.read(reinterpret_cast<char*>(acsg.weight.data()), loaded_weight_size * sizeof(float));

    // 校验pheromone和weight大小与ntotal一致
    if (acsg.pheromone.size() != loaded_ntotal) {
        in.close();
        FAISS_THROW_MSG("Pheromone size mismatch: loaded=" + std::to_string(acsg.pheromone.size()) + 
                       ", expected=" + std::to_string(loaded_ntotal));
    }
    if (acsg.weight.size() != loaded_ntotal) {
        in.close();
        FAISS_THROW_MSG("Weight size mismatch: loaded=" + std::to_string(acsg.weight.size()) + 
                       ", expected=" + std::to_string(loaded_ntotal));
    }

    // 校验入口点有效性
    if (acsg.enterpoint < 0 || acsg.enterpoint >= loaded_ntotal) {
        in.close();
        FAISS_THROW_MSG("Invalid loaded enterpoint: " + std::to_string(acsg.enterpoint)
                       + " (ntotal=" + std::to_string(loaded_ntotal) + ")");
    }

    // 4. 恢复图结构
    int loaded_K;
    in.read(reinterpret_cast<char*>(&loaded_K), sizeof(loaded_K));
    size_t loaded_neighbor_count;
    in.read(reinterpret_cast<char*>(&loaded_neighbor_count), sizeof(loaded_neighbor_count));

    const size_t expected_neighbor_count = static_cast<size_t>(loaded_ntotal) * loaded_K;
    if (loaded_K > 0 && loaded_neighbor_count != expected_neighbor_count) {
        in.close();
        FAISS_THROW_MSG("Graph data mismatch: K=" + std::to_string(loaded_K) 
                       + ", neighbor_count=" + std::to_string(loaded_neighbor_count)
                       + ", expected=" + std::to_string(expected_neighbor_count));
    }

    if (loaded_K > 0) {
        acsg.final_graph = std::make_shared<Graph<int32_t>>(loaded_ntotal, loaded_K);
        if (!acsg.final_graph) { in.close(); FAISS_THROW_MSG("Failed to create graph"); }

        size_t read_count = 0;
        for (faiss::idx_t i = 0; i < loaded_ntotal; i++) {
            for (int j = 0; j < loaded_K; j++) {
                int32_t neighbor;
                in.read(reinterpret_cast<char*>(&neighbor), sizeof(int32_t));
                if (in.gcount() != sizeof(int32_t)) {
                    in.close();
                    FAISS_THROW_MSG("Truncated neighbor data at i=" + std::to_string(i) + ", j=" + std::to_string(j));
                }
                acsg.final_graph->at(i, j) = neighbor;
                read_count++;
            }
        }

        if (read_count != loaded_neighbor_count) {
            in.close();
            FAISS_THROW_MSG("Neighbor count mismatch: read=" + std::to_string(read_count) + 
                           ", expected=" + std::to_string(loaded_neighbor_count));
        }

        // 抽样检查无效邻居：仅警告，不中断
        const int sample_count = std::min(100, (int)loaded_ntotal);
        int invalid_count = 0;
        for (int i = 0; i < sample_count; ++i) {
            faiss::idx_t rand_node = rand() % loaded_ntotal;
            for (int j = 0; j < loaded_K; ++j) {
                int32_t neighbor = acsg.final_graph->at(rand_node, j);
                if (neighbor < 0 || neighbor >= (int32_t)loaded_ntotal) {
                    if (invalid_count < 5) {
                        std::cerr << "WARNING: Invalid neighbor at node " << rand_node 
                                  << ", j=" << j << ": " << neighbor << std::endl;
                    }
                    invalid_count++;
                }
            }
        }
        if (invalid_count > 0) {
            std::cerr << "WARNING: Found " << invalid_count << " invalid neighbors in sample. Continuing..." << std::endl;
        }
    } else {
        acsg.final_graph.reset();
    }

    // 5. 恢复向量数据
    if (storage && own_fields) { delete storage; storage = nullptr; }
    size_t loaded_vec_count;
    in.read(reinterpret_cast<char*>(&loaded_vec_count), sizeof(loaded_vec_count));

    size_t expected_vec_count = static_cast<size_t>(loaded_ntotal) * static_cast<size_t>(loaded_d);
    if (loaded_vec_count != expected_vec_count) {
        in.close();
        delete storage;
        FAISS_THROW_MSG("Vector data mismatch: loaded=" + std::to_string(loaded_vec_count) 
                       + ", expected=" + std::to_string(expected_vec_count));
    }

    storage = new faiss::IndexFlat(loaded_d, loaded_metric);
    own_fields = true;
    auto flat_index = dynamic_cast<faiss::IndexFlat*>(storage);
    if (!flat_index) {
        in.close();
        delete storage;
        FAISS_THROW_MSG("Failed to cast to IndexFlat");
    }

    // 直接写入 IndexFlat 内部存储，避免 temp_vec 中转导致峰值内存翻倍
    flat_index->codes.resize(loaded_vec_count * sizeof(float));
    in.read(reinterpret_cast<char*>(flat_index->codes.data()), loaded_vec_count * sizeof(float));
    if (in.gcount() != static_cast<std::streamsize>(loaded_vec_count * sizeof(float))) {
        in.close();
        delete storage;
        FAISS_THROW_MSG("Truncated vector data: got " + std::to_string(in.gcount()) + " bytes");
    }
    flat_index->ntotal = loaded_ntotal;

    if (flat_index->ntotal != loaded_ntotal) {
        in.close();
        delete storage;
        FAISS_THROW_MSG("Vector add failed: flat_ntotal=" + std::to_string(flat_index->ntotal) 
                       + ", expected=" + std::to_string(loaded_ntotal));
    }

    // 6. 新增：恢复ACPG图的top入口点（仅版本2支持）
    if (VERSION >= 2) {
        size_t loaded_top_enterpoints_size;
        in.read(reinterpret_cast<char*>(&loaded_top_enterpoints_size), sizeof(loaded_top_enterpoints_size));
        
        acsg.top_enterpoints.resize(loaded_top_enterpoints_size);
        for (size_t i = 0; i < loaded_top_enterpoints_size; i++) {
            EnterPoint ep;
            in.read(reinterpret_cast<char*>(&ep.id), sizeof(ep.id));
            in.read(reinterpret_cast<char*>(&ep.weight), sizeof(ep.weight));
            acsg.top_enterpoints[i] = ep;
        }
        std::cout << "Loaded " << loaded_top_enterpoints_size << " ACPG top enterpoints" << std::endl;
    } else {
        // 版本1没有保存top入口点，清空或重新计算
        acsg.top_enterpoints.clear();
        std::cout << "Version 1 index: ACPG top enterpoints not available" << std::endl;
    }

    // 7. 同步对象状态并初始化内部状态
    ntotal = loaded_ntotal;
    acsg.ntotal = loaded_ntotal;
    d = loaded_d;
    metric_type = loaded_metric;
    is_trained = loaded_is_trained;
    is_built = loaded_is_built;
    build_type = loaded_build_type;

    // 关键：同步 acsg 内部的 is_built 状态
    acsg.is_built = loaded_is_built;
    acsg.NDC = 0;
    
    in.close();

    // 输出状态校验信息
    std::cout << "\n===== Index Load Status Check =====" << std::endl;
    std::cout << "1. Basic flags:" << std::endl;
    std::cout << "   - is_built: " << (is_built ? "true" : "false") << std::endl;
    std::cout << "   - is_trained: " << (is_trained ? "true" : "false") << std::endl;
    
    std::cout << "\n2. Core components:" << std::endl;
    std::cout << "   - final_graph: " << (acsg.final_graph ? "exists" : "nullptr") << std::endl;
    std::cout << "   - storage: " << (storage ? "exists" : "nullptr") << std::endl;
    if (storage) {
        auto flat = dynamic_cast<faiss::IndexFlat*>(storage);
        std::cout << "   - storage.ntotal: " << flat->ntotal << std::endl;
        std::cout << "   - storage.d: " << flat->d << std::endl;
    }
    
    std::cout << "\n3. Graph structure:" << std::endl;
    if (acsg.final_graph) {
        std::cout << "   - graph.N (nodes): " << acsg.final_graph->N << std::endl;
        std::cout << "   - graph.K (neighbors per node): " << acsg.final_graph->K << std::endl;
        std::cout << "   - nsg_R (expected K): " << nsg_R << std::endl;
        std::cout << "   - graph.N matches index.ntotal: " 
                  << (acsg.final_graph->N == ntotal ? "YES" : "NO") << std::endl;
        std::cout << "   - graph.K matches nsg_R: " 
                  << (acsg.final_graph->K == nsg_R ? "YES" : "NO") << std::endl;
    } else {
        std::cout << "   - No graph data available (final_graph is null)" << std::endl;
    }
    
    std::cout << "\n4. ACPG weights:" << std::endl;
    std::cout << "   - weight array size: " << acsg.weight.size() << std::endl;
    std::cout << "   - pheromone array size: " << acsg.pheromone.size() << std::endl;
    std::cout << "   - top enterpoints count: " << acsg.top_enterpoints.size() << std::endl;
    if (!acsg.top_enterpoints.empty()) {
        std::cout << "   - top enterpoint example: ID=" << acsg.top_enterpoints[0].id 
                  << ", weight=" << acsg.top_enterpoints[0].weight << std::endl;
    }
    
    std::cout << "\n5. Other parameters:" << std::endl;
    std::cout << "   - ntotal (total vectors): " << ntotal << std::endl;
    std::cout << "   - d (dimension): " << d << std::endl;
    std::cout << "   - enterpoint: " << acsg.enterpoint << std::endl;
    std::cout << "====================================\n" << std::endl;

    std::cout << "Index loaded successfully (" << ntotal << " vectors, " << d << " dimensions)" << std::endl;
}
}
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include <memory>
#include <chrono>
#include <iostream>

#include "ACSG/IndexACSG.h"
#include "utils/metrics.hpp"

namespace py = pybind11;

class GraphSearcher {
private:
    std::unique_ptr<acsg::IndexACSG> index_;
    bool loaded_ = false;
    int dim_ = 0;
    int nb_ = 0;

public:
    GraphSearcher() = default;
    
    void load_index(const std::string& index_file) {
        index_ = std::make_unique<acsg::IndexACSG>();
        index_->loadACPG(index_file.c_str());
        
        dim_ = index_->d;      // 向量维度
        nb_ = index_->ntotal;  // 数据点总数
        loaded_ = true;
        
        std::cout << "索引加载成功: dim=" << dim_ 
                  << ", nb=" << nb_ << std::endl;
    }
    
    bool is_loaded() const { return loaded_; }
    int dimension() const { return dim_; }
    int total_points() const { return nb_; }
    
    // 修改：返回召回率和查询时间（秒）
    std::tuple<double, double> search(
        py::array_t<float, py::array::c_style | py::array::forcecast> query,
        const std::vector<long>& gt,
        int k = 100
    ) {
        if (!loaded_) {
            throw std::runtime_error("请先加载索引！");
        }
        
        // 参数检查
        if (query.ndim() != 1 || static_cast<size_t>(query.shape(0)) != dim_) {
            throw std::runtime_error("查询维度不匹配");
        }
        
        if (k <= 0 || k > nb_) {
            throw std::runtime_error("k值无效");
        }
        
        const float* q = query.data();
        
        // 设置距离计算器
        auto dis = acsg::storage_distance_computer(index_->storage);
        dis->set_query(q);
        
        // 准备结果存储
        faiss::VisitedTable vt(nb_);
        std::vector<long> I_vec(k);
        std::vector<float> D_vec(k);
        
        // 计时搜索
        auto start = std::chrono::high_resolution_clock::now();
        
        // 使用空的入口点向量
        std::vector<acsg::EnterPoint> empty_enterpoints;
        index_->acsg.search_L = 32;
        index_->acsg.search_new(
            *dis, k, I_vec.data(), D_vec.data(), vt, 
            0, empty_enterpoints
        );
        
        auto end = std::chrono::high_resolution_clock::now();
        double elapsed_seconds = std::chrono::duration<double>(end - start).count();
        
        // 计算召回率
        double recall = 0.0;
        if (!gt.empty()) {
            std::unique_ptr<long[]> I_ptr(new long[k]);
            std::unique_ptr<long[]> gt_ptr(new long[gt.size()]);
            
            std::copy(I_vec.begin(), I_vec.end(), I_ptr.get());
            std::copy(gt.begin(), gt.end(), gt_ptr.get());
            
            recall = recall_at_k(1, k, k, I_ptr, static_cast<int>(gt.size()), gt_ptr);
        }
        
        // 修改：返回召回率和查询时间（秒）
        return std::make_tuple(recall, elapsed_seconds);
    }
    
    // 批量搜索版本 - 同样修改返回时间
    std::tuple<double, double> search_batch(
        py::array_t<float, py::array::c_style | py::array::forcecast> queries,
        const std::vector<std::vector<long>>& gt_list,
        int k = 10
    ) {
        if (!loaded_) {
            throw std::runtime_error("请先加载索引！");
        }
        
        auto queries_buf = queries.request();
        if (queries_buf.ndim != 2 || static_cast<size_t>(queries_buf.shape[1]) != dim_) {
            throw std::runtime_error("查询矩阵形状应为 (n_queries, dim)");
        }
        
        int n_queries = queries_buf.shape[0];
        const float* queries_data = static_cast<float*>(queries_buf.ptr);
        
        // 准备结果存储
        std::vector<std::vector<long>> all_results(n_queries, std::vector<long>(k));
        
        double total_time = 0.0;
        int valid_queries = 0;
        
        #pragma omp parallel for reduction(+:total_time, valid_queries)
        for (int i = 0; i < n_queries; i++) {
            const float* q = queries_data + i * dim_;
            
            auto dis = acsg::storage_distance_computer(index_->storage);
            dis->set_query(q);
            
            faiss::VisitedTable vt(nb_);
            std::vector<long> I_vec(k);
            std::vector<float> D_vec(k);
            
            auto start = std::chrono::high_resolution_clock::now();
            
            std::vector<acsg::EnterPoint> empty_enterpoints;
            index_->acsg.search_L = 32;
            index_->acsg.search_new(
                *dis, k, I_vec.data(), D_vec.data(), vt,
                0, empty_enterpoints
            );
            
            auto end = std::chrono::high_resolution_clock::now();
            double query_time = std::chrono::duration<double>(end - start).count();
            total_time += query_time;
            valid_queries++;
            
            // 存储结果
            all_results[i] = I_vec;
        }
        
        // 计算总体召回率
        double total_recall = 0.0;
        if (!gt_list.empty() && gt_list.size() == static_cast<size_t>(n_queries)) {
            for (int i = 0; i < n_queries; i++) {
                if (!gt_list[i].empty()) {
                    std::unique_ptr<long[]> I_ptr(new long[k]);
                    std::unique_ptr<long[]> gt_ptr(new long[gt_list[i].size()]);
                    
                    std::copy(all_results[i].begin(), all_results[i].end(), I_ptr.get());
                    std::copy(gt_list[i].begin(), gt_list[i].end(), gt_ptr.get());
                    
                    total_recall += recall_at_k(1, k, k, I_ptr, static_cast<int>(gt_list[i].size()), gt_ptr);
                }
            }
            total_recall /= n_queries;
        }
        
        double avg_time = total_time / valid_queries;
        
        // 修改：返回平均召回率和平均查询时间
        return std::make_tuple(total_recall, avg_time);
    }

    std::tuple<std::vector<double>, std::vector<double>>
    search_batch_multiL(
        py::array_t<float, py::array::c_style | py::array::forcecast> queries,
        const std::vector<std::vector<long>>& gt_list,
        const std::vector<int>& search_L_list,
        int k = 10
    ) {
        if (!loaded_) {
            throw std::runtime_error("请先加载索引！");
        }

        auto queries_buf = queries.request();
        if (queries_buf.ndim != 2 || (size_t)queries_buf.shape[1] != dim_) {
            throw std::runtime_error("查询矩阵形状应为 (n_queries, dim)");
        }

        int n_queries = queries_buf.shape[0];
        const float* q_data = (float*)queries_buf.ptr;

        // ------- 返回指标 -------
        std::vector<double> recalls(search_L_list.size(), 0.0);
        std::vector<double> avg_times(search_L_list.size(), 0.0);

        // ============= 遍历所有 search_L =============
        for (size_t li = 0; li < search_L_list.size(); li++) {
            int L = search_L_list[li];
            printf(">>> 测试 search_L = %d\n", L);

            std::vector<std::vector<long>> all_results(n_queries, std::vector<long>(k));

            double total_time = 0.0;
            int valid_queries = 0;

            #pragma omp parallel for reduction(+:total_time, valid_queries)
            for (int qi = 0; qi < n_queries; qi++) {
                const float* q = q_data + qi * dim_;

                auto dis = acsg::storage_distance_computer(index_->storage);
                dis->set_query(q);

                faiss::VisitedTable vt(nb_);
                std::vector<long> I_vec(k);
                std::vector<float> D_vec(k);

                auto start = std::chrono::high_resolution_clock::now();

                index_->acsg.search_L = L;
                std::vector<acsg::EnterPoint> empty;

                index_->acsg.search_new(
                    *dis, k, I_vec.data(), D_vec.data(), vt,
                    0, empty
                );

                auto end = std::chrono::high_resolution_clock::now();
                double qtime = std::chrono::duration<double>(end - start).count();

                total_time += qtime;
                valid_queries++;

                all_results[qi] = I_vec;
            }

            // ====================== 计算召回率 ======================
            double total_recall = 0.0;

            if (!gt_list.empty() && gt_list.size() == (size_t)n_queries) {
                for (int qi = 0; qi < n_queries; qi++) {
                    const auto& gt_row = gt_list[qi];
                    if (gt_row.empty()) continue;

                    std::unique_ptr<long[]> I_ptr(new long[k]);
                    std::unique_ptr<long[]> gt_ptr(new long[gt_row.size()]);

                    memcpy(I_ptr.get(), all_results[qi].data(), sizeof(long) * k);
                    memcpy(gt_ptr.get(), gt_row.data(), sizeof(long) * gt_row.size());

                    total_recall += recall_at_k(
                        1, k,
                        k, I_ptr,
                        (int)gt_row.size(), gt_ptr
                    );
                }
                total_recall /= n_queries;
            }

            recalls[li] = total_recall;
            avg_times[li] = total_time / valid_queries;

            printf("search_L=%d | recall=%.4f | avg_time=%.6f s\n",
                L, total_recall, avg_times[li]);
        }

        return std::make_tuple(recalls, avg_times);
    }


};

// 修复符号比较的辅助函数
namespace {
    float recall_at_k_fixed(
        size_t nq, size_t k, size_t gt_k, 
        const std::unique_ptr<long[]>& I, 
        size_t n_gt, 
        const std::unique_ptr<long[]>& gt
    ) {
        size_t n_ok = 0;
        for (size_t i = 0; i < nq; ++i) {
            size_t found = 0;
            for (size_t j = 0; j < k; ++j) {
                long predicted_id = I[i * k + j];
                for (size_t jj = 0; jj < gt_k; ++jj) {
                    long true_id = gt[i * n_gt + jj];
                    if (predicted_id == true_id) {
                        found++;
                        break;
                    }
                }
            }
            n_ok += found;
        }
        return n_ok / float(nq * gt_k);
    }
}

PYBIND11_MODULE(graph_eval, m) {
    m.doc() = "ACSG图搜索评估模块";
    
    py::class_<GraphSearcher>(m, "GraphSearcher")
        .def(py::init<>())
        .def("load_index", &GraphSearcher::load_index, "加载ACSG索引文件")
        .def("is_loaded", &GraphSearcher::is_loaded, "检查索引是否已加载")
        .def("dimension", &GraphSearcher::dimension, "获取向量维度")
        .def("total_points", &GraphSearcher::total_points, "获取索引中的总点数")
        .def("search", &GraphSearcher::search, 
             py::arg("query"),
             py::arg("gt") = std::vector<long>{},
             py::arg("k") = 10,
             "单查询搜索，返回(召回率, 查询时间秒)")
        .def("search_batch", &GraphSearcher::search_batch,
             py::arg("queries"),
             py::arg("gt_list") = std::vector<std::vector<long>>{},
             py::arg("k") = 10,
             "批量查询搜索，返回(平均召回率, 平均查询时间秒)")
        .def("search_batch_multiL", &GraphSearcher::search_batch_multiL,
            py::arg("queries"),
            py::arg("gt_list"),
            py::arg("search_L_list"),
            py::arg("k") = 10,
            "批量测试多个 search_L，返回(recalls[], avg_times[])");

}
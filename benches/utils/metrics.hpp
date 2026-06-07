#pragma once

#include <faiss/Index.h>

#include <benches/utils/Timer.hpp>
#include <cassert>
#include <memory>
#include <unordered_set>

float recall_at_k(const size_t nq, const size_t k, const size_t stride_labels,
                  const std::unique_ptr<faiss::idx_t[]> &labels,
                  const size_t stride_gt,
                  const std::unique_ptr<faiss::idx_t[]> &gt)
{
    
    assert(k <= stride_labels);

    float mean_recall = 0;
    for (int i = 0; i < nq; ++i)
    {
        float recall = 0;
        std::unordered_set<faiss::idx_t> cur_query_res;
        std::unordered_set<faiss::idx_t> cur_query_gt;

        for (int j = 0; j < k; ++j)
        {
            

            cur_query_res.insert(labels[i * stride_labels + j]);
            cur_query_gt.insert(gt[i * stride_gt + j]);
        }
        for (const auto &id : cur_query_res)
        {
            if (cur_query_gt.count(id))
            {
                recall += 1.0f;
            }
        }
        recall = recall / k;
        mean_recall += recall;
    }
    mean_recall = mean_recall / nq;

    return mean_recall;
};

template <class T>
std::pair<double, double> compute_qps_recall(
    const T &index, const int nq,
    const std::unique_ptr<float[]> &xq, const int k,
    const std::unique_ptr<faiss::idx_t[]> &gt)
{

    static_assert(std::is_base_of<faiss::Index, T>::value);
    using idx_t = faiss::idx_t;

    std::unique_ptr<idx_t[]> I(new idx_t[nq * k]);
    std::unique_ptr<float[]> D(new float[nq * k]);

    Timer timer;
    index.search(nq, xq.get(), k, D.get(), I.get());
    auto elapsed = timer.elapsed_ns() * 1e-9;
    std::cerr << "Time:" << elapsed << "s" << std::endl;
    float qps = nq / elapsed;
    float r_at_k = recall_at_k(nq, k, k, I, 100, gt);
    std::cout << "QPS = " << qps << " [q/s], R@k = " << r_at_k << std::endl;
    return {qps, r_at_k};
}
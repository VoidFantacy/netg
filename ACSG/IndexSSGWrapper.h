#pragma once
/**
 * IndexSSGWrapper.h
 * NETG 框架的 SSG 适配层
 * 封装 efanna2e::IndexSSG，提供与 NETG test.cpp 兼容的接口
 */

#include <string>
#include <vector>
#include <memory>
#include <iostream>

#include "index_ssg.h"
#include "index_random.h"
#include "util.h"
#include "parameters.h"

namespace netg {

class IndexSSGWrapper {
public:
    IndexSSGWrapper() = default;
    ~IndexSSGWrapper() = default;

    /**
     * 加载 SSG 图并做内存优化（OptimizeGraph）
     * @param ssg_path  SSG 索引文件路径
     * @param data      原始 base 数据指针（OptimizeGraph 需要）
     * @param n         数据点数量
     * @param dim       向量维度
     */
    void load(const std::string& ssg_path,
              const float* data, size_t n, size_t dim,
              bool use_ip = false) {
        dim_  = dim;
        n_    = n;
        data_ = data;

        auto metric = use_ip ? efanna2e::INNER_PRODUCT : efanna2e::FAST_L2;

        init_index_ = std::make_unique<efanna2e::IndexRandom>(dim, n);
        index_ = std::make_unique<efanna2e::IndexSSG>(
            dim, n, metric,
            (efanna2e::Index*)init_index_.get());

        std::cerr << ">>> Loading SSG graph from: " << ssg_path << "\n";
        index_->Load(ssg_path.c_str());

        std::cerr << ">>> Optimizing SSG graph for fast search...\n";
        index_->OptimizeGraph(data);

        ep_ = index_->GetEP();
        std::cerr << "✅ SSG loaded. EP=" << ep_
                  << "  N=" << n << "  Dim=" << dim << "\n";
    }

    /**
     * NETG 核心接口：从多个 Hub 入口点出发做 beam search
     * @param hub_ids  HNSW 路由器返回的 Hub node IDs（top-3）
     */
    void search_with_eps(const float* query, size_t K, unsigned L,
                         const std::vector<unsigned>& hub_ids,
                         unsigned* result) const {
        index_->SearchWithHubEPs(query, K, L, hub_ids, result);
    }

    /** SSG 原版搜索：使用建图时产生的全部导航点 eps_（公平 Baseline） */
    void search(const float* query, size_t K, unsigned L,
                unsigned* result) const {
        efanna2e::Parameters params;
        params.Set<unsigned>("L_search", L);
        index_->SearchWithOptGraph(query, K, params, result);
    }

    unsigned get_ep()   const { return ep_; }
    size_t   ntotal()   const { return n_; }
    size_t   dim()      const { return dim_; }
    bool     is_ready() const { return index_ != nullptr; }

private:
    std::unique_ptr<efanna2e::IndexRandom> init_index_;
    std::unique_ptr<efanna2e::IndexSSG>    index_;
    const float* data_ = nullptr;
    size_t   dim_  = 0;
    size_t   n_    = 0;
    unsigned ep_   = 0;
};

} // namespace netg

#pragma once

#include <memory>
#include <mutex>
#include <unordered_map>
#include <vector>
#include <omp.h>
#include <faiss/Index.h>
#include <faiss/impl/AuxIndexStructures.h>
#include <faiss/impl/FaissAssert.h>
#include <faiss/utils/Heap.h>
#include <faiss/utils/random.h>
#include <atomic>
#include <iostream>

namespace acsg
{
    using namespace faiss;

    // 移除有问题的前向声明
    // struct faiss::DistanceComputer; // from AuxIndexStructures
    
    struct Neighbor
    {
        int id;
        float distance;
        bool flag;

        Neighbor() = default;
        Neighbor(int id, float distance, bool f)
            : id(id), distance(distance), flag(f) {}

        inline bool operator<(const Neighbor &other) const
        {
            return distance < other.distance;
        }
    };

    struct newNeighbor;
    struct Node;

    struct EnterPoint
    {
        int id;
        double weight;
        // 新增默认构造函数
        EnterPoint() : id(-1), weight(0.0) {}  
        
        EnterPoint(int id, double w) : id(id), weight(w) {}

        bool operator<(const EnterPoint &other) const
        {
            return weight > other.weight; // 使最小的元素在堆顶
        }
    };

    template <class node_t>
    struct Graph
    {
        node_t *data;    ///< the flattened adjacency matrix, size N-by-K
        int K;           ///< nb of neighbors per node
        int N;           ///< total nb of nodes
        bool own_fields; ///< the underlying data owned by itself or not

        // construct from a known graph
        Graph(node_t *data, int N, int K)
            : data(data), K(K), N(N), own_fields(false) {}

        // construct an empty graph
        // NOTE: the newly allocated data needs to be destroyed at destruction time
        Graph(int N, int K) : K(K), N(N), own_fields(true)
        {
            data = new node_t[N * K];
        }

        // copy constructor
        Graph(const Graph &g) : Graph(g.N, g.K)
        {
            memcpy(data, g.data, N * K * sizeof(node_t));
        }

        // release the allocated memory if needed
        ~Graph()
        {
            if (own_fields)
            {
                delete[] data;
            }
        }

        // access the j-th neighbor of node i
        inline node_t at(int i, int j) const
        {
            return data[i * K + j];
        }

        // access the j-th neighbor of node i by reference
        inline node_t &at(int i, int j)
        {
            return data[i * K + j];
        }
    };

    DistanceComputer *storage_distance_computer(const Index *storage);

    struct ACSG
    {
        /* data */
        using storage_idx_t = int32_t;

        int ntotal = 0; ///< nb of nodes

        // construction-time parameters
        int nsg_R; ///< nb of neighbors per node
        int nsg_L; ///< length of the search path at construction time
        int nsg_C; ///< candidate pool size at construction time

        float alpha = 1.4;
        float beta = 2.2;
        float rho = 0.15; // 蚁群算法参数
        float Q = 1;      // 信息素增强系数;
        float lambda = 0.5;
        int iterations; // 最大迭代次数

        int thresholdrej = 10;

        // search-time parameters
        int search_L = 32; ///< length of the search path

        int enterpoint; ///< enterpoint

        std::vector<EnterPoint> top_enterpoints;

        std::shared_ptr<Graph<int32_t>> final_graph;  // 用 int32_t 节省一半图内存（足够寻址 4B 节点）
        std::vector<float> pheromone;
        std::vector<float> weight;

        mutable std::atomic<int> NDC{0};  

        // 添加查询计数器（实例变量）
        std::atomic<int> query_counter{0};
        std::mutex output_mutex;

        // 获取距离计算次数
        int get_ndc() const { return NDC; }
    
        // 重置距离计算次数
        void reset_ndc() { NDC = 0; }
    
        // 设置距离计算次数（用于测试）
        void set_ndc(int value) { NDC = value; }

        // 重置查询计数器
        void reset_query_counter() {
            query_counter = 0;
        }

        bool is_built = false; ///< NSG is built or not

        explicit ACSG(int R = 32);

        // build NSG from a KNN graph
        void build(
            Index *storage,
            idx_t n,
            const Graph<idx_t> &knn_graph,
            bool verbose);

        // reset the graph
        void reset();
        void update_weight();

        // [新增] 打印权重分布统计
        void print_weight_distribution();

        // search interface
        void search(
            DistanceComputer &dis,
            int k,
            idx_t *I,
            float *D,
            VisitedTable &vt) const;
        void search_ACO(
            DistanceComputer &dis,
            int topk,
            idx_t *I,
            float *D,
            VisitedTable &vt);

        void search_DPC_ACO(
            DistanceComputer &dis,
            int topk,
            idx_t *I,
            float *D,
            VisitedTable &vt,
            const std::vector<EnterPoint> &custom_enterpoints);

        void search_v1(
            DistanceComputer &dis,
            int topk,
            idx_t *I,
            float *D,
            VisitedTable &vt);

        void brute_force_search(
            DistanceComputer &dis,
            int topk,
            idx_t *I,
            float *D,
            idx_t nb,
            const float *xb);
        void insert_with_binary_search(std::vector<float> &log_probabilities, float log_probability, int r);
        
        std::tuple<std::vector<int>, double> ant_search(faiss::DistanceComputer &dis, int k,
                                                        idx_t *gt,
                                                        faiss::VisitedTable &vt,
                                                        bool similarity_metric);

        int roulette_wheel_selection(const std::vector<float> &log_probabilities);

        void update_pheromone(const std::vector<int> &paths, const float recall);
        void decrease_pheromone();

        template <bool collect_fullset, class index_t>
        void search_on_graph(
            const Graph<index_t> &graph,
            DistanceComputer &dis,
            VisitedTable &vt,
            int ep,
            int pool_size,
            std::vector<Neighbor> &retset,
            std::vector<Node> &fullset) const;

        template <bool collect_fullset, class index_t>
        void search_on_graph_v1(
            const Graph<index_t> &graph,
            DistanceComputer &dis,
            VisitedTable &vt,
            int ep,
            int pool_size,
            std::vector<Neighbor> &retset,
            std::vector<Node> &fullset);

        template <bool collect_fullset, class index_t>
        void search_on_graph_v2(
            const Graph<index_t> &graph,
            DistanceComputer &dis,
            VisitedTable &vt,
            int ep,
            int pool_size,
            std::vector<Neighbor> &retset,
            std::vector<Node> &fullset);    

        template <bool collect_fullset, class index_t>
        void search_on_graph_ACO(const Graph<index_t> &graph,
                                 DistanceComputer &dis,
                                 VisitedTable &vt,
                                 int ep,
                                 int L,
                                 std::vector<Neighbor> &retset);
        
        template <bool collect_fullset, class index_t>
        void search_on_graph_DPC_ACO(const Graph<index_t> &graph,
                                DistanceComputer &dis,
                                VisitedTable &vt,
                                int ep,
                                int L,
                                std::vector<Neighbor> &retset,
                                const std::vector<EnterPoint> &custom_enterpoints);

        template <bool collect_fullset, class index_t>
        void search_on_graph_ACO_v1(const Graph<index_t> &graph,
                                    DistanceComputer &dis,
                                    VisitedTable &vt,
                                    int ep,
                                    int L,
                                    std::vector<Neighbor> &retset);

        // 新的搜索函数，支持多种模式
        // retset_buf: 可选外部缓冲区，避免每次查询的堆分配
        void search_new(
            DistanceComputer &dis,
            int topk,
            idx_t *I,
            float *D,
            VisitedTable &vt,
            int mode, // 0:随机入口点, 1:固定权重入口点, 2:自定义入口点
            const std::vector<EnterPoint> &custom_enterpoints = std::vector<EnterPoint>(),
            std::vector<Neighbor> *retset_buf = nullptr);

        // 新的图搜索函数模板
        template <bool collect_fullset, class index_t>
        void search_on_graph_new(
            const Graph<index_t> &graph,
            DistanceComputer &dis,
            VisitedTable &vt,
            int L,
            std::vector<Neighbor> &retset,
            const std::vector<EnterPoint> &enterpoints,
            int mode,
            int query_id);  // 添加query_id参数
    };
}

#include <faiss/Index.h>
#include <ACSG/ACSG.h>
#include <omp.h>
#include <cinttypes>
#include <memory>

#include <faiss/IndexFlat.h>
#include <faiss/impl/AuxIndexStructures.h>
#include <faiss/impl/FaissAssert.h>
#include <faiss/utils/Heap.h>
#include <faiss/utils/distances.h>
#include <iostream>

namespace acsg
{
    using namespace faiss;
    struct IndexACSG : Index
    {

        ACSG acsg;

        // construction-time parameters
        int nsg_R = 32;  //< nb of neighbors per node
        int nsg_L = 64;  ///< length of the search path at construction time
        int nsg_C = 132; ///< candidate pool size at construction time

        int iterations = 20;
        idx_t ant_nums = 3;
        idx_t new_ant_nums = 10;//蚁群搜索的蚂蚁个数

        /// the sequential storage
        bool own_fields = false;
        Index *storage = nullptr;

        /// the index is built or not
        bool is_built = false;
        char build_type = 1;
        std::string ssg_graph_path; // build_type==2 时的 SSG 图文件路径

        // 添加保存和加载方法
        void save(const char* filename) const;
        void load(const char* filename);

        void saveACPG(const char* filename) const;
        void loadACPG(const char* filename);

        explicit IndexACSG(int d = 0, int R = 32, MetricType metric = METRIC_L2);
        explicit IndexACSG(Index *storage, int R = 32);

        ~IndexACSG() override;

        void add(idx_t n, const float *x) override;

        void build(idx_t n, const float *x, idx_t *knn_graph, int R);

        /// Trains the storage if needed
        void train(idx_t n, const float *x) override;

        void antSearch(idx_t train_size, const float *train_set, idx_t k, idx_t *train_gt);

        void update_pheromone(std::vector<std::tuple<std::vector<int>, double>>& paths);

        // [新增] 修复图连通性的函数声明
        void fix_connectivity();

        // [新增] 辅助函数：在两个节点间加边
        void add_edge_safe(idx_t u, idx_t v);

        /// entry point for search
        void search(
            idx_t n,
            const float *x,
            idx_t k,
            float *distances,
            idx_t *labels,
            const SearchParameters *params = nullptr) const override;

        void search_ACO(
            idx_t n,
            const float *x,
            idx_t k,
            float *distances,
            idx_t *labels,
            const SearchParameters *params = nullptr);

        void search_v1(
            idx_t n,
            const float *x,
            idx_t k,
            float *distances,
            idx_t *labels,
            const SearchParameters *params = nullptr);

        void brute_force_search(
            idx_t nb,
            const float *xb,
            idx_t n,
            const float *x,
            idx_t k,
            float *distances,
            idx_t *labels,
            const SearchParameters *params = nullptr);

        void reconstruct(idx_t key, float *recons) const override;
        void reset() override;

        // 新增：ACPG图访问方法
        const std::vector<float>& get_acpg_weights() const { return acsg.weight; }
        const std::vector<float>& get_acpg_pheromones() const { return acsg.pheromone; }
        const std::vector<EnterPoint>& get_acpg_top_enterpoints() const { return acsg.top_enterpoints; }
         // 新增：获取ACPG图
        std::shared_ptr<Graph<int32_t>> get_acpg_graph() const { 
            return acsg.final_graph; 
        }
    
        // 获取完整的ACPG图信息
        struct ACPGGraphInfo {
            std::vector<float> weights;
            std::vector<float> pheromones;
            std::vector<EnterPoint> top_enterpoints;
            std::shared_ptr<Graph<int32_t>> graph;
            faiss::idx_t ntotal;
            int d;
        };
    
        ACPGGraphInfo get_acpg_graph_info() const {
            return {
                acsg.weight,
                acsg.pheromone,
                acsg.top_enterpoints,
                acsg.final_graph,
                ntotal,
                d
            };
        }

    };

    struct IndexACSGFlat : IndexACSG
    {
        IndexACSGFlat();
        IndexACSGFlat(int d, int R, MetricType metric = METRIC_L2);
    };
}
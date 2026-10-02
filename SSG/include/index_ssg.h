#ifndef EFANNA2E_INDEX_SSG_H
#define EFANNA2E_INDEX_SSG_H

#include <boost/dynamic_bitset.hpp>
#include <cassert>
#include <sstream>
#include <stack>
#include <string>
#include <unordered_map>

#include "index.h"
#include "neighbor.h"
#include "parameters.h"
#include "util.h"

namespace efanna2e {

class IndexSSG : public Index {
 public:
  explicit IndexSSG(const size_t dimension, const size_t n, Metric m,
                    Index *initializer);

  virtual ~IndexSSG();

  virtual void Save(const char *filename) override;
  virtual void Load(const char *filename) override;

  virtual void Build(size_t n, const float *data,
                     const Parameters &parameters) override;

  virtual void Search(const float *query, const float *x, size_t k,
                      const Parameters &parameters, unsigned *indices) override;
  void SearchWithOptGraph(const float *query, size_t K,
                          const Parameters &parameters, unsigned *indices);
  // NETG 扩展：支持多 Hub 入口点路由
  void SearchWithHubEPs(const float *query, size_t K, unsigned L,
                        const std::vector<unsigned> &hub_ids,
                        unsigned *indices);
  void OptimizeGraph(const float *data);
  // 获取默认入口点（NETG medoid baseline 用）
  unsigned GetEP() const { return eps_.empty() ? 0 : eps_[0]; }

 protected:
  typedef std::vector<std::vector<unsigned>> CompactGraph;
  typedef std::vector<SimpleNeighbors> LockGraph;
  typedef std::vector<nhood> KNNGraph;

  CompactGraph final_graph_;
  Index *initializer_;

  void init_graph(const Parameters &parameters);
  void get_neighbors(const float *query, const Parameters &parameter,
                     std::vector<Neighbor> &retset,
                     std::vector<Neighbor> &fullset);
  void get_neighbors(const unsigned q, const Parameters &parameter,
                     std::vector<Neighbor> &pool);
  void sync_prune(unsigned q, std::vector<Neighbor> &pool,
                  const Parameters &parameter, float threshold,
                  SimpleNeighbor *cut_graph_);
  void Link(const Parameters &parameters, SimpleNeighbor *cut_graph_);
  void InterInsert(unsigned n, unsigned range, float threshold,
                   std::vector<std::mutex> &locks, SimpleNeighbor *cut_graph_);
  void Load_nn_graph(const char *filename);
  void strong_connect(const Parameters &parameter);

  void DFS(boost::dynamic_bitset<> &flag,
           std::vector<std::pair<unsigned, unsigned>> &edges, unsigned root,
           unsigned &cnt);
  bool check_edge(unsigned u, unsigned t);
  void findroot(boost::dynamic_bitset<> &flag, unsigned &root,
                const Parameters &parameter);
  void DFS_expand(const Parameters &parameter);

 private:
  unsigned width;
  unsigned ep_; //not in use
  std::vector<unsigned> eps_;
  std::vector<std::mutex> locks;
  char *opt_graph_;
  size_t node_size;
  size_t data_len;
  size_t neighbor_len;
  KNNGraph nnd_graph;

  // ── 复用 visited 标记（替代每次 new boost::dynamic_bitset）──
  // 用版本号方案：O(1) 清零，无需 memset。
  // 单线程测试下安全，多线程需加锁或改为 thread_local。
  mutable std::vector<uint32_t> visited_;   // visited_[i] == visit_tag_ 表示已访问
  mutable uint32_t              visit_tag_ = 0;

  // ── 采样锚点：均匀采样一小批节点，搜索时快速找到离 query 最近的起点 ──
  std::vector<unsigned> sample_anchors_;

  // 内联方法：初始化（首次 / 溢出时 reset）
  void visited_init() const {
    ++visit_tag_;
    if (visit_tag_ == 0) {                  // uint32 溢出归零，重置数组
      std::fill(visited_.begin(), visited_.end(), 0u);
      visit_tag_ = 1;
    }
  }
  bool visited_get(unsigned id) const { return visited_[id] == visit_tag_; }
  void visited_set(unsigned id)  const { visited_[id] = visit_tag_; }
};

}  // namespace efanna2e

#endif  // EFANNA2E_INDEX_SSG_H

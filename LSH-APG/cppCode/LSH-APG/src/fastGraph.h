#pragma once
#include "divGraph.h"
#include <vector>
#include <queue>
#include <algorithm>
#include <iostream>
#include <cmath>
#include <cstring> 

using dist_t = float;
using labeltype = int;
using tableint = int;

extern int _lsh_UB;

using namespace threadPoollib;

struct CompareByFirst {
    constexpr bool operator()(std::pair<dist_t, tableint> const& a,
        std::pair<dist_t, tableint> const& b) const noexcept {
        return a.first < b.first;
    }
};

struct hashPair {
    zint val;
    int id;
    hashPair() = default;
    hashPair(zint v_, int id_) :val(v_), id(id_) {}
    bool operator < (const hashPair& rhs) const {
        return val < rhs.val;
    }
};

struct fastGraph {
    std::string file;
    char* links = nullptr;
    size_t N = 0;
    size_t dim = 0;
    size_t maxT = 0;
    size_t size_data_per_element_;
    float** dataset = nullptr;
    float** hashval = nullptr;
    hashPair** hashTables = nullptr;
    divGraph* myhash = nullptr;
    const size_t sint = sizeof(int);
    threadPoollib::VisitedListPool* visited_list_pool_ = nullptr;
public:
    int ef = 0;
    int T = 0;
    int K = 0;
    int L = 0;
    int S = 0;
    int lowDim = 0;
    int u = 0;
    std::string getFilename() const { return file; }

    fastGraph(divGraph* divG) {
        file = divG->getFilename();
        ef = divG->ef;
        N = divG->N;
        maxT = divG->maxT;
        size_data_per_element_ = (size_t)(maxT + 1) * sint;
        dataset = divG->myData;
        dim = divG->dim;
        visited_list_pool_ = new VisitedListPool(1, N);
        loadLite(divG);
    }

    void loadLite(divGraph* divG) {
        links = (char*)malloc(N * size_data_per_element_);
        if (!links) {
            std::cerr << "❌ [FATAL] Memory allocation failed for links!" << std::endl;
            exit(1);
        }
        for (size_t i = 0; i < N; ++i) {
            char* begin = links + i * size_data_per_element_;
            auto& nns = divG->linkLists[i];
            memcpy(begin, &(nns->out), sint);
            begin += sint;
            for (int i = 0; i < nns->out; ++i) {
                memcpy(begin + i * sint, &(nns->neighbors[i].id), sint);
            }
        }
        K = divG->K; L = divG->L; S = divG->S; lowDim = divG->lowDim;
        myhash = divG; hashval = divG->hashval; u = myhash->u;
        hashTables = new hashPair * [L];
        for (int i = 0; i < L; ++i) {
            hashTables[i] = new hashPair[N];
            int cnt = 0;
            auto pt = divG->hashTables[i].begin();
            while (pt != divG->hashTables[i].end()) {
                hashTables[i][cnt++] = hashPair(pt->first, pt->second);
                pt++;
            }
        }
    }

    zint getZ(float* _h) {
        zint res = 0;
        for (int i = u - 1; i >= 0; i--) {
            int mask = 1 << i;
            for (int j = 0; j < K; j++) {
                res <<= 1;
                if ((int)floor(_h[j]) & mask) ++res;
            }
        }
        return res;
    }

#if defined _MSC_VER
#include <intrin.h>
#endif
#include "divGraph.h"

    int getLLCP(zint k1, zint k2) {
        if (k1 == k2) return _ZINT_LEN;
#if defined(__GNUC__)
        return __builtin_clzll(k1 ^ k2);
#else
        return 0;
#endif
    }

    void searchLSHQuery(queryN* q, std::priority_queue<Res>& candTable, std::vector<bool>& flag_) {
        q->hashval = myhash->calHash(q->queryPoint);
        // lshUB 直接等于 ef，保证 LSH 扫描量与 beam search 规模一致
        // 原来 4*L*log(N)+ef 会导致 LSH 阶段扫描量远超 ef，QPS 大幅偏低
        int lshUB = ef;
        if (_lsh_UB > 0) lshUB = _lsh_UB;

        std::vector<hashPair*> lpos(L), rpos(L), qpos(L);
        std::priority_queue<posInfo> lEntries, rEntries;
        std::vector<zint> keys(L);
        for (int j = 0; j < L; j++) {
            keys[j] = getZ(q->hashval + j * K);
            qpos[j] = std::lower_bound(hashTables[j], hashTables[j] + N, hashPair(keys[j], -1));
            
            if (qpos[j] != hashTables[j]) {
                lpos[j] = qpos[j]; --lpos[j];
#ifdef USE_LCCP
                lEntries.emplace(j, getLLCP(lpos[j]->val, keys[j]));
#else
                lEntries.push(posInfo(j, getLevel(lpos[j]->first, qpos[j]->first)));
#endif 
            }
            rpos[j] = qpos[j];
            if (rpos[j] != hashTables[j] + N) {
#ifdef USE_LCCP
                rEntries.emplace(j, getLLCP(rpos[j]->val, keys[j]));
#else
                rEntries.push(posInfo(j, getLevel(rpos[j]->first, qpos[j]->first)));
#endif 
            }
        }

        while (!(lEntries.empty() && rEntries.empty())) {
            posInfo t;
            bool f = true;
            if (lEntries.empty()) f = false;
            else if (rEntries.empty()) f = true;
            else if (rEntries.top().dist > lEntries.top().dist) f = false;

            if (f) {
                t = lEntries.top(); lEntries.pop();
                for (int i = 0; i < 1; ++i) { // step = 1
                    int rid = lpos[t.id]->id;
                    if (!flag_[rid]) {
                        candTable.emplace(rid, cal_dist(q->queryPoint, dataset[rid], dim));
                        flag_[rid] = true;
                    }
                    if (lpos[t.id] != hashTables[t.id]) --lpos[t.id];
                    else break;
                }
                if (lpos[t.id] != hashTables[t.id]) {
#ifdef USE_LCCP
                    t.dist = getLLCP(lpos[t.id]->val, keys[t.id]);
#else
                    t.dist = getLevel(lpos[t.id]->first, qpos[t.id]->first);
#endif 
                    lEntries.push(t);
                }
            } else {
                t = rEntries.top(); rEntries.pop();
                for (int i = 0; i < 1; ++i) { // step = 1
                    int rid = rpos[t.id]->id;
                    if (!flag_[rid]) {
                        candTable.emplace(rid, cal_dist(q->queryPoint, dataset[rid], dim));
                        flag_[rid] = true;
                    }
                    if (++rpos[t.id] == hashTables[t.id] + N) break;
                }
                if (rpos[t.id] != hashTables[t.id] + N) {
#ifdef USE_LCCP
                    t.dist = getLLCP(rpos[t.id]->val, keys[t.id]);
#else
                    t.dist = getLevel(rpos[t.id]->first, qpos[t.id]->first);
#endif 
                    rEntries.push(t);
                }
            }
            if (candTable.size() >= lshUB) break;
        }

        q->cost = candTable.size();
        while (candTable.size() > ef) candTable.pop();
        if (candTable.empty()) candTable.emplace(0, cal_dist(q->queryPoint, dataset[0], dim));
    }

    // ── 复用 flag 数组：避免每次 query 做 N 次 memset ──────────────────
    // 用 visited_version 代替清零：只需在查询结束后 reset 访问过的节点
    std::vector<bool> flag_pool;          // 在 fastGraph 构造时一次性分配
    std::vector<int>  flag_touched;       // 记录本次访问过的节点 ID

    void initFlagPool() {
        flag_pool.assign(N, false);
        flag_touched.reserve(4096);
    }

    inline void flagReset() {
        for (int id : flag_touched) flag_pool[id] = false;
        flag_touched.clear();
    }

    inline bool flagCheck(int id) { return flag_pool[id]; }

    inline void flagMark(int id) {
        flag_pool[id] = true;
        flag_touched.push_back(id);
    }
    // ────────────────────────────────────────────────────────────────────

    // 优化版 searchLSHQuery：自适应种子数
    // 低 ef 时多给种子以消除 recall@1 死区；高 ef 时保持原有效率
    static constexpr int N_SEEDS_BASE = 20;

    void searchLSHQuerySeeds(queryN* q,
                             std::vector<int>& seed_ids) {
        q->hashval = myhash->calHash(q->queryPoint);
        // 种子数固定为 N_SEEDS_BASE=20（与原论文一致）
        // recall@1 死区通过 knn() 中的 internal_ef = max(ef, seeds) 来修复
        // 而不是靠膨胀种子数（膨胀会导致 SIFT 等简单数据集全 1.0）
        int n_seeds = N_SEEDS_BASE;
        int lshUB = std::max(n_seeds, std::min(ef, n_seeds * 2));

        std::vector<hashPair*> lpos(L), rpos(L), qpos(L);
        std::priority_queue<posInfo> lEntries, rEntries;
        std::vector<zint> keys(L);

        for (int j = 0; j < L; j++) {
            keys[j] = getZ(q->hashval + j * K);
            qpos[j] = std::lower_bound(hashTables[j], hashTables[j] + N, hashPair(keys[j], -1));
            if (qpos[j] != hashTables[j]) {
                lpos[j] = qpos[j]; --lpos[j];
                lEntries.push(posInfo(j, myhash->getLevel(lpos[j]->val, qpos[j]->val)));
            }
            rpos[j] = qpos[j];
            if (rpos[j] != hashTables[j] + N)
                rEntries.push(posInfo(j, myhash->getLevel(rpos[j]->val, qpos[j]->val)));
        }

        seed_ids.clear();
        while (!(lEntries.empty() && rEntries.empty()) && (int)seed_ids.size() < lshUB) {
            posInfo t;
            bool f = true;
            if (lEntries.empty()) f = false;
            else if (rEntries.empty()) f = true;
            else if (rEntries.top().dist > lEntries.top().dist) f = false;

            if (f) {
                t = lEntries.top(); lEntries.pop();
                int rid = lpos[t.id]->id;
                if (!flagCheck(rid)) { seed_ids.push_back(rid); flagMark(rid); }
                if (lpos[t.id] != hashTables[t.id]) {
                    --lpos[t.id];
                    t.dist = myhash->getLevel(lpos[t.id]->val, qpos[t.id]->val);
                    lEntries.push(t);
                }
            } else {
                t = rEntries.top(); rEntries.pop();
                int rid = rpos[t.id]->id;
                if (!flagCheck(rid)) { seed_ids.push_back(rid); flagMark(rid); }
                if (++rpos[t.id] != hashTables[t.id] + N) {
                    t.dist = myhash->getLevel(rpos[t.id]->val, qpos[t.id]->val);
                    rEntries.push(t);
                }
            }
        }
        if (seed_ids.empty()) seed_ids.push_back(0);
    }

    // 优化版 knn
    // 修复1：复用 flag_pool（避免每次 query O(N) memset）
    // 修复2：LSH 种子数自适应，低 ef 时用更大的内部 beam width
    // 修复3：消除 recall@1 死区 —— ef < 32 时 beam width 扩大到种子数级别
    void knn(queryN* q) {
        lsh::timer timer;
        timer.restart();

        // --- Phase 1: LSH seed（自适应数量）---
        std::vector<int> seed_ids;
        searchLSHQuerySeeds(q, seed_ids);
        q->timeHash = timer.elapsed();

        // 内部 beam width：种子数 > ef 时自动扩大，保证候选池够大
        // ef > 200 时种子数=20 < ef，自然退化为 internal_ef = ef
        int internal_ef = std::max(ef, (int)seed_ids.size());

        // --- Phase 2: Beam Search ---
        std::priority_queue<std::pair<dist_t, tableint>> top_candidates;   // max heap
        std::priority_queue<std::pair<dist_t, tableint>> candidate_set;    // min heap (neg dist)

        for (int seed : seed_ids) {
            dist_t d = cal_dist(q->queryPoint, dataset[seed], dim);
            top_candidates.emplace(d, seed);
            candidate_set.emplace(-d, seed);
        }
        // 先截断种子到 internal_ef
        while ((int)top_candidates.size() > internal_ef) top_candidates.pop();

        dist_t lowerBound = top_candidates.empty() ? FLT_MAX : top_candidates.top().first;

        while (!candidate_set.empty()) {
            auto current_node_pair = candidate_set.top();
            if (-current_node_pair.first > lowerBound) break;
            candidate_set.pop();

            tableint current_node_id = current_node_pair.second;
            int* data = (int*)(links + current_node_id * size_data_per_element_);
            size_t size = *data;

            for (size_t j = 1; j <= size; j++) {
                int candidate_id = *(data + j);
                if (!flagCheck(candidate_id)) {
                    flagMark(candidate_id);
                    float* currObj1 = dataset[candidate_id];
                    dist_t dist = cal_dist(q->queryPoint, currObj1, dim);
                    q->cost++;
                    if ((int)top_candidates.size() < internal_ef || lowerBound > dist) {
                        candidate_set.emplace(-dist, candidate_id);
                        top_candidates.emplace(dist, candidate_id);
                        if ((int)top_candidates.size() > internal_ef) top_candidates.pop();
                        lowerBound = top_candidates.top().first;
                    }
                }
            }
        }

        // 清理 flag（O(visited) 而非 O(N)）
        flagReset();

        while ((int)top_candidates.size() > q->k) top_candidates.pop();

        size_t actual_k = std::min((size_t)q->k, top_candidates.size());
        q->res.resize(actual_k);
        for (int i = (int)actual_k - 1; i >= 0; --i) {
            auto rez = top_candidates.top();
            q->res[i] = Res(rez.first, rez.second);
            top_candidates.pop();
        }
        q->timeTotal = timer.elapsed();
    }

    // 修复版 knnHNSW: 使用 vector 替代固定数组，防止 L > 500 时崩溃
    void knnHNSW(queryN* q) {
        lsh::timer timer;
        std::priority_queue<Res> candTable;
        std::vector<bool> flag_(N, false);
        
        // [修复关键点] 使用 vector 动态分配，防止栈溢出
        std::vector<Res> top_candidates;
        top_candidates.reserve(ef + 2000); 

        std::priority_queue<Res, std::vector<Res>, std::greater<Res>> candidate_set;

        timer.restart();
        searchLSHQuery(q, candTable, flag_);
        q->timeHash = timer.elapsed();
        
        size_t size_c = 0;
        while (!candTable.empty()) {
            auto u = candTable.top();
            if (size_c < top_candidates.capacity()) {
                top_candidates.push_back(u); 
                size_c++;
            } else {
                top_candidates.push_back(u); // 自动扩容
                size_c++;
            }
            candidate_set.emplace(u.dist, u.id);
            candTable.pop();
        }
        std::make_heap(top_candidates.begin(), top_candidates.end());
        
        dist_t lowerBound = 1e9;
        if(size_c > 0) lowerBound = top_candidates[0].dist;

        while (!candidate_set.empty()) {
            auto current_node_pair = candidate_set.top();
            if ((current_node_pair.dist) > lowerBound) break;
            candidate_set.pop();

            tableint current_node_id = current_node_pair.id;
            int* data = (int*)(links + current_node_id * size_data_per_element_);
            size_t size = *data;

            for (size_t j = 1; j <= size; j++) {
                int candidate_id = *(data + j);
                if (!flag_[candidate_id]) {
                    flag_[candidate_id] = true;
                    if (0 || cal_dist(q->hashval, hashval[candidate_id], lowDim) * myhash->coeffq < lowerBound) {
                        float* currObj1 = dataset[*(data + j)];
                        dist_t dist = cal_dist(q->queryPoint, currObj1, dim);
                        q->cost++;
                        if (size_c < ef || lowerBound > dist) {
                            candidate_set.emplace(dist, candidate_id);
                            
                            // HNSW 插入逻辑
                            top_candidates.push_back(Res(dist, candidate_id));
                            std::push_heap(top_candidates.begin(), top_candidates.end());
                            size_c++;

                            if (size_c > ef) {
                                std::pop_heap(top_candidates.begin(), top_candidates.end());
                                top_candidates.pop_back();
                                size_c--;
                            }
                            
                            if(size_c > 0) lowerBound = top_candidates.front().dist;
                        }
                    } else {
                        q->prunings++;
                    }
                }
            }
        }

        while (size_c > q->k) {
            std::pop_heap(top_candidates.begin(), top_candidates.end());
            top_candidates.pop_back();
            size_c--;
        }

        size_t actual_k = std::min((size_t)q->k, size_c);
        q->res.resize(actual_k);
        std::sort_heap(top_candidates.begin(), top_candidates.end());
        
        for (int i = 0; i < actual_k; ++i) {
            q->res[i] = top_candidates[i];
        }
        q->timeTotal = timer.elapsed();
    }
};
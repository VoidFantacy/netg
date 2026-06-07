import os

# 路径定义
BASE_DIR = "LSH-APG/cppCode/LSH-APG/src"
FAST_GRAPH_H = os.path.join(BASE_DIR, "fastGraph.h")
MAIN_CPP = os.path.join(BASE_DIR, "main.cpp")

print("=== 🚑 正在部署深度诊断代码 ===")

# =========================================================
# 1. 重写 fastGraph.h (加入内存检查 + 执行追踪)
# =========================================================
print(f"🔧 重写 {FAST_GRAPH_H} ...")
fast_graph_code = r'''#pragma once
#include "divGraph.h"
#include <vector>
#include <queue>
#include <algorithm>
#include <iostream>
#include <cstdio>

using dist_t = float;
using labeltype = int;
using tableint = int;

extern int _lsh_UB;

using namespace threadPoollib;

struct hashPair {
    zint val;
    int id;
    hashPair() = default;
    hashPair(zint v_, int id_) :val(v_), id(id_) {}
    bool operator < (const hashPair& rhs) const { return val < rhs.val; }
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

    fastGraph(divGraph* divG) {
        std::cerr << "[Init] Initializing fastGraph..." << std::endl;
        file = divG->getFilename();
        ef = divG->ef;
        N = divG->N;
        maxT = divG->maxT;
        size_data_per_element_ = (size_t)(maxT + 1) * sint;
        dataset = divG->myData;
        dim = divG->dim;
        visited_list_pool_ = new VisitedListPool(1, N);
        loadLite(divG);
        std::cerr << "[Init] fastGraph initialized successfully." << std::endl;
    }

    void loadLite(divGraph* divG){
        std::cerr << "[Init] Allocating links memory (" << N * size_data_per_element_ / 1024 / 1024 << " MB)..." << std::endl;
        links = (char*)malloc(N * size_data_per_element_);
        if (links == nullptr) {
            std::cerr << "❌ [FATAL] Memory allocation failed for 'links'!" << std::endl;
            exit(1);
        }
        
        for (size_t i = 0; i < N; ++i) {
            char* begin = links + i * size_data_per_element_;
            auto& nns = divG->linkLists[i];
            // Safety check
            if (nns == nullptr) {
                std::cerr << "❌ [FATAL] divGraph->linkLists[" << i << "] is NULL!" << std::endl;
                exit(1);
            }
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

    void searchLSHQuery(queryN * q, std::priority_queue<Res>& candTable, std::vector<bool>& flag_) {
        q->hashval = myhash->calHash(q->queryPoint);
        int lshUB = 4 * L * log(N) + ef;
        if(_lsh_UB > 0) lshUB = _lsh_UB;
        
        // Simplified Logic for Debugging
        // Using basic vectors to avoid complexity issues
        // ... (Omitting complex LCCP logic for brevity in debug view, keeping core)
        
        // RE-IMPLEMENTING ORIGINAL LCCP LOGIC for correctness
        std::vector<hashPair*> lpos(L), rpos(L), qpos(L);
        std::priority_queue<posInfo> lEntries, rEntries;
        std::vector<zint> keys(L);
        int step = 1;

        for (int j = 0; j < L; j++) {
            keys[j] = getZ(q->hashval + j * K);
            qpos[j] = std::lower_bound(hashTables[j], hashTables[j] + N, hashPair(keys[j], -1));
            
            if (qpos[j] != hashTables[j]) {
                lpos[j] = qpos[j]; --lpos[j];
                lEntries.emplace(j, getLLCP(lpos[j]->val, keys[j]));
            }
            rpos[j] = qpos[j];
            if (rpos[j] != hashTables[j]+N) {
                rEntries.emplace(j, getLLCP(rpos[j]->val, keys[j]));
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
                for (int i = 0; i < step; ++i) {
                    int rid = lpos[t.id]->id;
                    if (!flag_[rid]) {
                        candTable.emplace(rid, cal_dist(q->queryPoint, dataset[rid], dim));
                        flag_[rid] = true;
                    }
                    if (lpos[t.id] != hashTables[t.id]) --lpos[t.id];
                    else break;
                }
                if (lpos[t.id] != hashTables[t.id]) {
                    t.dist = getLLCP(lpos[t.id]->val, keys[t.id]);
                    lEntries.push(t);
                }
            } else {
                t = rEntries.top(); rEntries.pop();
                for (int i = 0; i < step; ++i) {
                    int rid = rpos[t.id]->id;
                    if (!flag_[rid]) {
                        candTable.emplace(rid, cal_dist(q->queryPoint, dataset[rid], dim));
                        flag_[rid] = true;
                    }
                    if (++rpos[t.id] == hashTables[t.id] + N) break;
                }
                if (rpos[t.id] != hashTables[t.id]+N) {
                    t.dist = getLLCP(rpos[t.id]->val, keys[t.id]);
                    rEntries.push(t);
                }
            }
            if (candTable.size() >= lshUB) break;
        }

        q->cost = candTable.size();
        while (candTable.size() > ef) candTable.pop();
        if (candTable.empty()) candTable.emplace(0, cal_dist(q->queryPoint, dataset[0], dim));
    }

    void knn(queryN* q) {
        lsh::timer timer;
        std::priority_queue<Res> candTable;
        std::vector<bool> flag_(N, false);
        
        // Safe dynamic vector
        std::vector<Res> top_candidates(ef + 2000);
        std::priority_queue<Res, std::vector<Res>, std::greater<Res>> candidate_set;

        timer.restart();
        searchLSHQuery(q, candTable, flag_);
        q->timeHash = timer.elapsed();

        size_t size_c = 0;
        while (!candTable.empty()) {
            auto u = candTable.top();
            if (size_c < top_candidates.size()) top_candidates[size_c++] = u;
            candidate_set.emplace(u.dist, u.id);
            candTable.pop();
        }
        std::make_heap(top_candidates.begin(), top_candidates.begin() + size_c);
        
        dist_t lowerBound = 1e9;
        if (size_c > 0) lowerBound = top_candidates[0].dist;

        while (!candidate_set.empty()) {
            auto current_node_pair = candidate_set.top();
            if ((current_node_pair.dist) > lowerBound) break;
            candidate_set.pop();

            tableint current_node_id = current_node_pair.id;
            // Check memory access
            if (current_node_id >= N) {
                std::cerr << "❌ [FATAL] Invalid node ID: " << current_node_id << std::endl;
                exit(1);
            }
            int* data = (int*)(links + current_node_id * size_data_per_element_);
            size_t size = *data;

            for (size_t j = 1; j <= size; j++) {
                int candidate_id = *(data + j);
                if (!flag_[candidate_id]) {
                    flag_[candidate_id] = true;
                    if (cal_dist(q->hashval, hashval[candidate_id], lowDim) * myhash->coeffq < lowerBound) {
                        float* currObj1 = dataset[*(data + j)];
                        dist_t dist = cal_dist(q->queryPoint, currObj1, dim);
                        q->cost++;
                        if (size_c < ef || lowerBound > dist) {
                            candidate_set.emplace(dist, candidate_id);
                            if (size_c == ef && dist < top_candidates[0].dist) {
                                std::pop_heap(top_candidates.begin(), top_candidates.begin() + size_c);
                                size_c--;
                                top_candidates[size_c++] = Res(dist, candidate_id);
                                std::push_heap(top_candidates.begin(), top_candidates.begin() + size_c);
                            } 
                            else if (size_c < ef) {
                                top_candidates[size_c++] = Res(dist, candidate_id);
                                std::push_heap(top_candidates.begin(), top_candidates.begin() + size_c);
                            }
                            if (size_c > 0) lowerBound = top_candidates[0].dist;
                        }
                    } else {
                        q->prunings++;
                    }
                }
            }
        }

        while (size_c > q->k) {
            std::pop_heap(top_candidates.begin(), top_candidates.begin() + size_c);
            size_c--;
        }

        // Safe result extraction
        size_t actual_k = (size_c < (size_t)q->k) ? size_c : (size_t)q->k;
        q->res.resize(actual_k);
        std::sort_heap(top_candidates.begin(), top_candidates.begin() + size_c);
        for (size_t i = 0; i < actual_k; ++i) {
            q->res[i] = top_candidates[i];
        }

        q->timeTotal = timer.elapsed();
    }

    // Alias
    void knnHNSW(queryN* q) { knn(q); }
};
'''
with open(FAST_GRAPH_H, "w") as f:
    f.write(fast_graph_code)


# =========================================================
# 2. 重写 main.cpp (强制 stderr 输出)
# =========================================================
print(f"🔧 重写 {MAIN_CPP} ...")
main_code = r'''#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <algorithm>
#include <set>
#include <thread>
#include <omp.h>
#include "alg.h"

int _lsh_UB = 0;

void load_data_fvecs(const char* filename, float*& data, unsigned& num, unsigned& dim) {
    std::cerr << "[LOG] Loading " << filename << "..." << std::endl;
    std::ifstream in(filename, std::ios::binary);
    if (!in.is_open()) {
        std::cerr << "❌ Error: Cannot open file " << filename << std::endl;
        exit(-1);
    }
    in.read((char*)&dim, 4);
    in.seekg(0, std::ios::end);
    size_t fsize = (size_t)in.tellg();
    num = (unsigned)(fsize / (dim * 4 + 4));
    data = new float[num * dim];
    in.seekg(0, std::ios::beg);
    for (size_t i = 0; i < num; i++) {
        in.seekg(4, std::ios::cur);
        in.read((char*)(data + i * dim), dim * 4);
    }
    in.close();
    std::cerr << "[LOG] Loaded " << num << " vectors." << std::endl;
}

void load_gt_ivecs(const char* filename, unsigned*& data, unsigned& num, unsigned& dim) {
    std::cerr << "[LOG] Loading GT " << filename << "..." << std::endl;
    std::ifstream in(filename, std::ios::binary);
    if (!in.is_open()) {
        std::cerr << "❌ Error: Cannot open GT file " << filename << std::endl;
        exit(-1);
    }
    in.read((char*)&dim, 4);
    in.seekg(0, std::ios::end);
    size_t fsize = (size_t)in.tellg();
    num = (unsigned)(fsize / (dim * 4 + 4));
    data = new unsigned[num * dim];
    in.seekg(0, std::ios::beg);
    for (size_t i = 0; i < num; i++) {
        in.seekg(4, std::ios::cur);
        in.read((char*)(data + i * dim), dim * 4);
    }
    in.close();
    std::cerr << "[LOG] Loaded GT " << num << " vectors." << std::endl;
}

float calculate_recall(const std::vector<std::vector<unsigned>>& results, const unsigned* gt, unsigned gt_dim, unsigned K) {
    if (results.empty()) return 0.0f;
    size_t nq = results.size();
    size_t total_hit = 0;
    for (size_t i = 0; i < nq; ++i) {
        std::set<unsigned> gt_set;
        for (unsigned j = 0; j < K && j < gt_dim; j++) {
            gt_set.insert(gt[i * gt_dim + j]);
        }
        unsigned hit = 0;
        for (unsigned val : results[i]) {
            if (gt_set.count(val)) hit++;
        }
        total_hit += hit;
    }
    return (float)total_hit / (nq * K);
}

int main(int argc, char const* argv[])
{
    omp_set_num_threads(1);

    if (argc < 5) {
        std::cerr << "Usage: ./lgo <dataset_name> <base_file> <query_file> <gt_file>" << std::endl;
        return -1;
    }

    std::string datasetName = argv[1];
    std::string baseFile = argv[2];
    std::string queryFile = argv[3];
    std::string gtFile = argv[4];

    // Preprocess
    Preprocess prep(baseFile, ""); 

    std::string index_fold = "./indexes/";
    std::string path = index_fold + datasetName + ".index";
    if (!GenericTool::CheckPathExistence(index_fold.c_str())) {
        GenericTool::EnsurePathExistence(index_fold.c_str());
    }

    unsigned L_build = 8, K_build = 10;
    Parameter param1(prep, L_build, K_build, 1.0f);
    
    divGraph* divG = nullptr;
    if (find_file(path + "_divGraph")) {
        std::cerr << "[LOG] Loading divGraph..." << std::endl;
        divG = new divGraph(&prep, path + "_divGraph", 0.9);
    } else {
        std::cerr << "[LOG] Building divGraph..." << std::endl;
        divG = new divGraph(prep, param1, path + "_divGraph", 24, 80, 0.95, 0.9);
    }

    std::cerr << "[LOG] Init FastGraph..." << std::endl;
    fastGraph* fsG = new fastGraph(divG);

    float* query_data = nullptr;
    unsigned query_num, query_dim;
    load_data_fvecs(queryFile.c_str(), query_data, query_num, query_dim);

    unsigned* gt_data = nullptr;
    unsigned gt_num, gt_dim_val;
    load_gt_ivecs(gtFile.c_str(), gt_data, gt_num, gt_dim_val);

    unsigned K_search = 100; 
    std::vector<int> search_Ls = {
        10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 
        128, 256, 512, 1024, 1500
    };
    int runs = 10; 

    std::cout << "\n==================== LSH-APG Benchmark ====================" << std::endl;
    std::cout << std::setw(6) << "L" << " | "
              << std::setw(12) << "QPS" << " | "
              << std::setw(12) << "Recall" << " | "
              << std::setw(12) << "Time(ms)" 
              << std::endl;
    std::cout << "-------+--------------+--------------+--------------" << std::endl;

    std::vector<std::vector<unsigned>> results(query_num);
    queryN qTemplate(0, 1.5f, K_search, prep, 0.1f);

    for (int L : search_Ls) {
        if (L < K_search) continue;

        std::cerr << "[DEBUG] >>> Start Testing L=" << L << std::endl;
        fsG->ef = L; 
        double total_time_ms = 0.0;
        
        for (int r = 0; r < runs; r++) {
            if (r==0) std::cerr << "   [Run 0] Processing..." << std::flush;
            auto start = std::chrono::high_resolution_clock::now();
            for (unsigned i = 0; i < query_num; i++) {
                if (r == 0 && i > 0 && i % 2000 == 0) std::cerr << "." << std::flush;
                
                results[i].clear();
                qTemplate.queryPoint = query_data + i * query_dim;
                qTemplate.res.clear();
                qTemplate.k = K_search; 
                fsG->knn(&qTemplate);
                
                results[i].resize(qTemplate.res.size());
                for(size_t j=0; j<qTemplate.res.size(); ++j) results[i][j] = qTemplate.res[j].id;
            }
            auto end = std::chrono::high_resolution_clock::now();
            total_time_ms += std::chrono::duration<double, std::milli>(end - start).count();
            if (r==0) std::cerr << " Done." << std::endl;
        }

        double avg_time_ms = total_time_ms / runs;
        double qps = query_num / (avg_time_ms / 1000.0);
        float recall = calculate_recall(results, gt_data, gt_dim_val, K_search);

        std::cout << std::setw(6) << L << " | "
                  << std::setw(12) << std::fixed << std::setprecision(1) << qps << " | "
                  << std::setw(12) << std::setprecision(4) << recall << " | "
                  << std::setw(12) << std::setprecision(2) << avg_time_ms 
                  << std::endl;

        if (L != search_Ls.back()) std::this_thread::sleep_for(std::chrono::seconds(5));
    }
    
    return 0;
}
'''
with open(MAIN_CPP, "w") as f:
    f.write(main_code)

print("✅ 文件写入完成！")
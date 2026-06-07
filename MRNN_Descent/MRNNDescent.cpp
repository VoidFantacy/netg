#include <faiss/impl/AuxIndexStructures.h>
#include <faiss/impl/DistanceComputer.h>
#include <iostream>
#include <MRNN_Descent/MRNNDescent.h>
#include <random>

#include <mutex>
#include <string>
#include <fstream>
#include <chrono>
#include <boost/dynamic_bitset.hpp>
#include <iostream>
#include <stack>

using LockGuard = std::lock_guard<std::mutex>;

namespace mrnndescent
{
    using namespace faiss;

    using storage_idx_t = NNDescent::storage_idx_t;

    namespace
    {

        DistanceComputer *storage_distance_computer(const Index *storage)
        {
            if (is_similarity_metric(storage->metric_type))
            {
                return new NegativeDistanceComputer(storage->get_distance_computer());
            }
            else
            {
                return storage->get_distance_computer();
            }
        }

    } // namespace
    MRNNDescent::~MRNNDescent() {}

    MRNNDescent::MRNNDescent(const int d) : d(d) {}

    void gen_random(std::mt19937 &rng, int *addr, const int size, const int N)
    {
        for (int i = 0; i < size; ++i)
        {
            addr[i] = rng() % (N - size);
        }
        std::sort(addr, addr + size);
        for (int i = 1; i < size; ++i)
        {
            if (addr[i] <= addr[i - 1])
            {
                addr[i] = addr[i - 1] + 1;
            }
        }
        int off = rng() % N;
        for (int i = 0; i < size; ++i)
        {
            addr[i] = (addr[i] + off) % N;
        }
    }

    void MRNNDescent::init_graph(faiss::DistanceComputer &qdis)
    {
        graph.reserve(ntotal);
        {
            std::mt19937 rng(random_seed * 6007);
            for (int i = 0; i < ntotal; i++)
            {
                graph.push_back(faiss::nndescent::Nhood(L, S, rng, (int)ntotal));
            }
        }
#pragma omp parallel
        {
            std::mt19937 rng(random_seed * 7741 + omp_get_thread_num());
#pragma omp for
            for (int i = 0; i < ntotal; i++)
            {
                std::vector<int> tmp(S);

                gen_random(rng, tmp.data(), S, ntotal);

                for (int j = 0; j < S; j++)
                {
                    int id = tmp[j];
                    if (id == i)
                    {
                        continue;
                    }
                    float dist = qdis.symmetric_dis(i, id);
                    graph[i].pool.push_back(faiss::nndescent::Neighbor(id, dist, true));
                }
                std::make_heap(graph[i].pool.begin(), graph[i].pool.end());
                graph[i].pool.reserve(L);
            }
        }
    }

    //     void MRNNDescent::join(DistanceComputer &qdis)
    //     {
    //         idx_t check_period = InterruptCallback::get_period_hint(d * search_L);
    //         for (idx_t i0 = 0; i0 < (idx_t)ntotal; i0 += check_period)
    //         {
    //             idx_t i1 = std::min(i0 + check_period, (idx_t)ntotal);
    // #pragma omp parallel for default(shared) schedule(dynamic, 100)
    //             for (idx_t n = i0; n < i1; n++)
    //             {
    //                 auto &node = graph[n];
    //                 for (int const i : node.nn_new)
    //                 {
    //                     for (int const j : node.nn_new)
    //                     {
    //                         if (i < j)
    //                         {
    //                             float dist = qdis.symmetric_dis(i, j);
    //                             graph[i].insert(j, dist);
    //                             graph[j].insert(i, dist);
    //                         }
    //                     }
    //                     for (int j : node.nn_old)
    //                     {
    //                         float dist = qdis.symmetric_dis(i, j);
    //                         graph[i].insert(j, dist);
    //                         graph[j].insert(i, dist);
    //                     }
    //                 }
    //             }
    //             InterruptCallback::check();
    //         }
    //     }

    void MRNNDescent::InterInsert(DistanceComputer &qdis)
    {
        std::vector<std::vector<faiss::nndescent::Neighbor>> reverse_pools(ntotal);
#pragma omp parallel for
        for (int u = 0; u < ntotal; ++u)
        {
            for (auto &&nn : graph[u].pool)
            {
                std::lock_guard<std::mutex> guard(graph[nn.id].lock);
                reverse_pools[nn.id].emplace_back(u, nn.distance, nn.flag);
            }
        }

#pragma omp parallel for
        for (int u = 0; u < ntotal; ++u)
        {
            auto &pool = graph[u].pool;
            for (auto &&nn : pool)
            {
                nn.flag = true;
            }
            auto &rpool = reverse_pools[u];
            rpool.insert(rpool.end(), pool.begin(), pool.end());
            pool.clear();
            std::sort(rpool.begin(), rpool.end());
            rpool.erase(std::unique(rpool.begin(), rpool.end(),
                                    [](faiss::nndescent::Neighbor &a,
                                       faiss::nndescent::Neighbor &b)
                                    {
                                        return a.id == b.id;
                                    }),
                        rpool.end());
            if (rpool.size() > R)
            {
                rpool.resize(R);
            }
        }

#pragma omp parallel for
        for (int u = 0; u < ntotal; ++u)
        {
            for (auto &&nn : reverse_pools[u])
            {
                std::lock_guard<std::mutex> guard(graph[nn.id].lock);
                graph[nn.id].pool.emplace_back(u, nn.distance, nn.flag);
            }
        }

#pragma omp parallel for
        for (int u = 0; u < ntotal; ++u)
        {
            auto &pool = graph[u].pool;
            std::sort(pool.begin(), pool.end());
            if (pool.size() > R)
            {
                pool.resize(R);
            }
        }
    }

    void MRNNDescent::mrnndescent(DistanceComputer &qdis, bool verbose)
    {
        for (size_t i = 0; i < iter1; i++)
        {
            std::cerr << "Iteration1 " << i << " start." << std::endl;
            auto iter1_start = std::chrono::high_resolution_clock::now();

            size_t prev_total_edges = 0;
            for (int n = 0; n < ntotal; ++n)
            {
                prev_total_edges += graph[n].pool.size();
            }
            for (size_t j = 0; j < iter2; j++)
            {
                sync_prune(qdis);
            }
            size_t new_total_edges = 0;
            for (int n = 0; n < ntotal; ++n)
            {
                new_total_edges += graph[n].pool.size();
            }

            double delta_edges = std::abs((double)new_total_edges - prev_total_edges);
            double change_rate = delta_edges / prev_total_edges;

            std::cerr << "Iteration1 " << i << " | Change rate: " << change_rate << std::endl;

            if (change_rate < 0.01)
            { // 变化率低于 1%，提前终止
                std::cerr << "Convergence reached at Iteration1 " << i
                          << " | Change rate: " << change_rate << std::endl;
                break;
            }

            if (i != iter1 - 1)
            {
                InterInsert(qdis);
            }

            auto iter1_end = std::chrono::high_resolution_clock::now();
            std::cerr << "Iteration1 " << i << " total time: "
                      << std::chrono::duration<double>(iter1_end - iter1_start).count()
                      << " s"
                      << std::endl;
        }
    }

    void MRNNDescent::sync_prune(DistanceComputer &qdis)
    {
#pragma omp parallel for
        for (int n = 0; n < ntotal; ++n)
        {
            auto &nn = graph[n];
            std::sort(nn.pool.begin(), nn.pool.end());
            nn.pool.erase(std::unique(nn.pool.begin(), nn.pool.end(),
                                      [](faiss::nndescent::Neighbor &a,
                                         faiss::nndescent::Neighbor &b)
                                      {
                                          return a.id == b.id;
                                      }),
                          nn.pool.end());
            nn.pool.shrink_to_fit(); // 避免越界访问
        }
#pragma omp parallel
        {
#pragma omp for
            for (int n = 0; n < ntotal; ++n)
            {
                auto &node = graph[n];
                auto &pool = node.pool;

                std::vector<faiss::nndescent::Neighbor> tmp_pool;
                {
                    std::lock_guard<std::mutex> guard(node.lock);
                    tmp_pool = pool; // 确保复制完整
                }

                std::vector<faiss::nndescent::Neighbor> result;
                unsigned start = 0;
                if (!pool.empty() && pool[0].id == n)
                    start++;

                if (start < pool.size())
                {
                    result.push_back(pool[start]); // 避免空访问
                }

                while (result.size() < R && (++start) < pool.size())
                {
                    auto &p = pool[start];
                    bool occlude = false;
                    for (auto &&other_nn : result)
                    {
                        if (!p.flag && !other_nn.flag)
                        {
                            continue;
                        }

                        if (p.id == other_nn.id)
                        {
                            occlude = true;
                            break;
                        }
                        float distance = qdis.symmetric_dis(p.id, other_nn.id);
                        if (distance < p.distance - 3 * tau)
                        {
                            occlude = true;
                            auto &nhood = graph[other_nn.id];
                            std::unique_lock<std::mutex> lock(nhood.lock, std::try_to_lock);
                            if (lock.owns_lock()) // 避免死锁
                            {
                                nhood.pool.emplace_back(p.id, distance, true);
                            }
                            break;
                        }
                    }
                    if (!occlude)
                    {
                        result.emplace_back(p);
                    }
                }
                // 更新新旧邻居
                for (auto &&nn : result)
                {
                    if (nn.flag)
                    {
                        nn.flag = false;
                    }
                }
                {
                    std::lock_guard<std::mutex> guard(node.lock);
                    pool.clear();
                    pool.insert(pool.end(), result.begin(), result.end());
                }
            }
        }
    }

    void MRNNDescent::build(Index *storage, const float *x, faiss::DistanceComputer &qdis, const int n, bool verbose)
    {
        if (has_built)
        {
            reset();
        }

        if (verbose)
        {
            printf("Parameters: S=%d, R=%d, tau=%f T1=%d, T2=%d\n", S, R, tau, iter1, iter2);
        }
        ntotal = n;
        init_graph(qdis);
        mrnndescent(qdis, verbose);
        auto tree_grow_starts = std::chrono::high_resolution_clock::now();
        tree_grow(x, storage);
        auto tree_grow_ends = std::chrono::high_resolution_clock::now();
        std::cerr << "tree_grow time: " << std::chrono::duration<double>(tree_grow_ends - tree_grow_starts).count() << " s" << std::endl;
        std::cerr << "iterations finished." << std::endl;
        offsets.resize(ntotal + 1);
        offsets[0] = 0;
        for (int u = 0; u < ntotal; u++)
        {
            offsets[u + 1] = offsets[u] + graph[u].pool.size();
        }

        final_graph.resize(offsets.back(), -1);
#pragma omp parallel for
        for (int u = 0; u < n; ++u)
        {
            auto &pool = graph[u].pool;
            int offset = offsets[u];
            for (int i = 0; i < pool.size(); ++i)
            {
                final_graph[offset + i] = pool[i].id;
            }
        }
        std::cerr << "MRNNDescent build finished." << std::endl;
        std::vector<faiss::nndescent::Nhood>().swap(graph);
        has_built = true;

        if (verbose)
        {
            printf("Added %d points into the index\n", ntotal);
        }
    }

    int insert_into_pool(faiss::nndescent::Neighbor *addr, int size, faiss::nndescent::Neighbor nn)
    {
        // find the location to insert
        int left = 0, right = size - 1;
        if (addr[left].distance > nn.distance)
        {
            memmove((char *)&addr[left + 1], &addr[left], size * sizeof(faiss::nndescent::Neighbor));
            addr[left] = nn;
            return left;
        }
        if (addr[right].distance < nn.distance)
        {
            addr[size] = nn;
            return size;
        }
        while (left < right - 1)
        {
            int mid = (left + right) / 2;
            if (addr[mid].distance > nn.distance)
                right = mid;
            else
                left = mid;
        }
        // check equal ID

        while (left > 0)
        {
            if (addr[left].distance < nn.distance)
                break;
            if (addr[left].id == nn.id)
                return size + 1;
            left--;
        }
        if (addr[left].id == nn.id || addr[right].id == nn.id)
            return size + 1;
        memmove((char *)&addr[right + 1],
                &addr[right],
                (size - right) * sizeof(faiss::nndescent::Neighbor));
        addr[right] = nn;
        return right;
    }

    void MRNNDescent::search(
        faiss::DistanceComputer &qdis,
        const int topk,
        idx_t *indices,
        float *dists,
        faiss::VisitedTable &vt) const
    {
        FAISS_THROW_IF_NOT_MSG(has_built, "The index is not build yet.");
        int L_2 = std::max(search_L, topk);
        // std::cerr << "L_2:" << L_2 << std::endl;
        // std::cerr << "topk:" << topk << std::endl;
        // candidate pool, the K best items is the result.
        std::vector<faiss::nndescent::Neighbor> retset(L_2 + 1);
        // Randomly choose L_2 points to initialize the candidate pool
        std::vector<int> init_ids(L_2);
        std::mt19937 rng(random_seed);
        init_ids.push_back(ep_);
        gen_random(rng, init_ids.data() + 1, L_2, ntotal);
        for (int i = 0; i < L_2; i++)
        {
            int id = init_ids[i];
            float dist = qdis(id);
            retset[i] = faiss::nndescent::Neighbor(id, dist, true);
        }
        // Maintain the candidate pool in ascending order
        std::sort(retset.begin(), retset.begin() + L_2);
        int k = 0;

        // Stop until the smallest position updated is >= L_2
        while (k < L_2)
        {
            int nk = L_2;

            if (retset[k].flag)
            {
                retset[k].flag = false;
                int cur_id = retset[k].id;
                int offset = offsets[cur_id];
                int K = offsets[cur_id + 1] - offset;
                for (int m = 0; m < K; ++m)
                {
                    int id = final_graph[offset + m];
                    if (vt.get(id))
                    {
                        continue;
                    }

                    vt.set(id);
                    float dist = qdis(id);
                    if (dist >= retset[L_2 - 1].distance)
                    {
                        continue;
                    }

                    faiss::nndescent::Neighbor nn(id, dist, true);
                    // std::cerr << "id:" << id << " dist:" << dist << std::endl;
                    int r = insert_into_pool(retset.data(), L_2, nn);
                    // std::cerr << "r:" << r << std::endl;
                    if (r < nk)
                        nk = r;
                }
            }
            if (nk <= k)
            {
                k = nk;
            }
            else
            {
                ++k;
            }
        }

        for (size_t i = 0; i < topk; i++)
        {
            indices[i] = retset[i].id;
            dists[i] = retset[i].distance;
        }

        vt.advance();
    }

    int MRNNDescent::DFS(faiss::VisitedTable &vt, int root, int cnt)
    {
        std::stack<int> stack;

        if (!vt.get(root))
        {
            vt.set(root);
            cnt++;
        }

        stack.push(root);

        while (!stack.empty())
        {
            int node = stack.top();
            stack.pop();

            for (auto &neigh : graph[node].pool)
            {
                int id = neigh.id;
                if (id != -1 && !vt.get(id))
                { // 仅访问未访问过的节点
                    vt.set(id);
                    stack.push(id);
                    cnt++;
                }
            }
        }

        // 统计 `vt` 中访问的节点总数
        int count_true = 0;
        for (size_t i = 0; i < ntotal; i++)
        {
            if (vt.get(i))
            {
                count_true++;
            }
        }

        std::cerr << "Final cnt: " << cnt << ", Visited count: " << count_true << ", ntotal: " << ntotal << std::endl;
        assert(cnt == count_true); // 确保 `cnt` 统计值与 `vt` 标志位匹配
        return cnt;
    }

    void MRNNDescent::get_neighbors(faiss::DistanceComputer &qdis, idx_t *indices, float *dists, int topk)
    {
        faiss::VisitedTable vt(ntotal);
        int L_2 = std::max(search_L, topk);
        std::vector<faiss::nndescent::Neighbor> retset(L_2 + 1);
        std::vector<int> init_ids(L_2);
        std::mt19937 rng(random_seed);
        gen_random(rng, init_ids.data(), L_2, ntotal);
        for (int i = 0; i < L_2; i++)
        {
            int id = init_ids[i];
            float dist = qdis(id);
            retset[i] = faiss::nndescent::Neighbor(id, dist, true);
        }

        // Maintain the candidate pool in ascending order
        std::sort(retset.begin(), retset.begin() + L_2);
        int k = 0;
        // Stop until the smallest position updated is >= L_2
        while (k < L_2)
        {
            int nk = L_2;

            if (retset[k].flag)
            {
                retset[k].flag = false;
                int cur_id = retset[k].id;
                auto &pool = graph[cur_id].pool;
                for (auto &node : pool)
                {
                    int id = node.id;
                    if (vt.get(id))
                    {
                        continue;
                    }

                    vt.set(id);
                    float dist = qdis(id);
                    if (dist >= retset[L_2 - 1].distance)
                    {
                        continue;
                    }

                    faiss::nndescent::Neighbor nn(id, dist, true);
                    int r = insert_into_pool(retset.data(), L_2, nn);

                    if (r < nk)
                        nk = r;
                }
            }
            if (nk <= k)
            {
                k = nk;
            }
            else
            {
                ++k;
            }
        }
        for (size_t i = 0; i < topk; i++)
        {
            indices[i] = retset[i].id;
            dists[i] = retset[i].distance;
        }

        vt.advance();
    }

    void MRNNDescent::findroot(faiss::VisitedTable &vt, int &root, Index *storage, const float *x)
    {
        unsigned id = ntotal;

        // 找到未连接的第一个结点
        for (int i = 0; i < ntotal; i++)
        {
            if (!vt.get(i))
            {
                id = i;
                break;
            }
        }
        if (id == ntotal)
            return; // 没有未连接的结点

        // 搜索 id 最近的一个已连接结点
        std::unique_ptr<idx_t[]> indices(new idx_t[1]);
        std::unique_ptr<float[]> dists(new float[1]);
        DistanceComputer *dis = storage_distance_computer(storage);
        dis->set_query(x + id * d);
        get_neighbors(*dis, indices.get(), dists.get(), 1);

        auto &pool = graph[indices[0]].pool;
        bool found = false;
        for (const auto &neighbor : pool)
        {
            if (vt.get(neighbor.id))
            {
                root = neighbor.id;
                found = true;
                break;
            }
        }

        // 如果找不到，随机选择一个已连接的点
        if (!found)
        {
            std::vector<int> connected_nodes;
            for (int i = 0; i < ntotal; i++)
            {
                if (vt.get(i))
                    connected_nodes.push_back(i);
            }
            if (!connected_nodes.empty())
            {
                static std::random_device rd;
                static std::mt19937 gen(rd());
                std::uniform_int_distribution<int> dist(0, connected_nodes.size() - 1);
                root = connected_nodes[dist(gen)];
            }
        }

        // 确保 root 有效
        if (root >= ntotal || root < 0)
            return;

        // 连接 root 和 id
        graph[root].pool.push_back(faiss::nndescent::Neighbor(id, dists[0], true));
    }

    void MRNNDescent::tree_grow(const float *x, Index *storage)
    {
        std::unique_ptr<float[]> center(new float[d]);
        std::unique_ptr<float[]> tmp(new float[d]);
        std::fill_n(center.get(), d, 0.0f);
#pragma omp parallel for
        for (int i = 0; i < ntotal; i++)
        {
            const float *tmp = x + i * d;
            for (int j = 0; j < d; j++)
            {
                center[j] += tmp[j];
            }
        }

#pragma omp parallel for
        for (int i = 0; i < d; i++)
        {
            center[i] /= ntotal;
        }

        // random initialize navigating point
        std::unique_ptr<idx_t[]> indices(new idx_t[1]);
        std::unique_ptr<float[]> dists(new float[1]);
        DistanceComputer *dis = storage_distance_computer(storage);
        dis->set_query(center.get());
        get_neighbors(*dis, indices.get(), dists.get(), 1);
        std::cerr << "ep_:" << indices[0] << std::endl;
        // set enterpoint
        ep_ = indices[0];
        int root = ep_;
        faiss::VisitedTable vt(ntotal);
        int linked_cnt = 0;
        while (linked_cnt < ntotal)
        {
            linked_cnt = DFS(vt, root, linked_cnt);
            if (linked_cnt >= ntotal)
                break;
            findroot(vt, root, storage, x);
        }
#pragma omp parallel for
        for (int u = 0; u < ntotal; ++u)
        {
            auto &pool = graph[u].pool;
            std::sort(pool.begin(), pool.end());
            if (pool.size() > R)
            {
                pool.resize(R);
            }
        }
        std::cerr << "Tree grow" << std::endl;
    }
    void MRNNDescent::reset()
    {
        has_built = false;
        ntotal = 0;
        final_graph.clear();
    }
}
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

// -*- c++ -*-

#pragma once

#include <algorithm>
#include <mutex>
#include <queue>
#include <random>
#include <unordered_set>
#include <vector>

#include <omp.h>

#include <faiss/faiss/Index.h>
#include <faiss/impl/FaissAssert.h>
#include <faiss/impl/platform_macros.h>
#include <faiss/utils/Heap.h>
#include <faiss/utils/random.h>
#include <faiss/impl/NNDescent.h>

namespace mrnndescent
{
    using namespace faiss;

    struct MRNNDescent
    {

        using KNNGraph = std::vector<nndescent::Nhood>;

        explicit MRNNDescent(const int d);

        ~MRNNDescent();

        void build(Index *storage, const float *x, DistanceComputer &qdis, const int n, bool verbose);

        void search(
            DistanceComputer &qdis,
            const int topk,
            idx_t *indices,
            float *dists,
            VisitedTable &vt) const;

        void reset();

        /// Initialize the KNN graph randomly
        void init_graph(DistanceComputer &qdis);

        /// Perform MRNNDescent algorithm
        void mrnndescent(DistanceComputer &qdis, bool verbose);

        /// Sample new neighbors for each node to peform local join later
        void sync_prune(DistanceComputer &qdis);

        void InterInsert(DistanceComputer &qdis);

        /// Sample a small number of points to evaluate the quality of KNNG built
        void findroot(faiss::VisitedTable &vt, int &root, Index *storage, const float *x);
        int DFS(faiss::VisitedTable &vt, int root, int cnt);
        void tree_grow(const float *x, Index *storage);
        void get_neighbors(faiss::DistanceComputer &qdis, idx_t *indices, float *dists, int topk);

        bool has_built = false;
        int iter1 = 4;
        int iter2 = 15;
        int S = 16; // number of sample neighbors to be updated for each node
        int R = 96; // size of reverse links, 0 means the reverse links will not be used
        double tau = 0.02;

        int search_L = 64;      // size of candidate pool in searching
        int random_seed = 2021; // random seed for generators

        int d;       // dimensions
        int L = 100; // size of the candidate pool in building

        int ntotal = 0;
        int ep_;

        KNNGraph graph;
        std::vector<int> final_graph;
        std::vector<int> offsets;
    };
} // namespace mrnndescent

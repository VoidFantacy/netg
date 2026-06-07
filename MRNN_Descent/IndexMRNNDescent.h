/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

// -*- c++ -*-

#pragma once

#include <vector>

#include <faiss/IndexFlat.h>
#include <faiss/impl/NNDescent.h>
#include <faiss/utils/utils.h>
#include <MRNN_Descent/MRNNDescent.h>

namespace mrnndescent
{

    /** The NNDescent index is a normal random-access index with an NNDescent
     * link structure built on top */
    using namespace faiss;

    struct IndexMRNNDescent : Index
    {
        // internal storage of vectors (32 bits)
        using storage_idx_t = NNDescent::storage_idx_t;

        /// Faiss results are 64-bit

        // the link structure
        MRNNDescent mrnndescent;

        // the sequential storage
        bool own_fields;
        Index *storage;

        explicit IndexMRNNDescent(int d = 0, int K = 32, MetricType metric = METRIC_L2);

        explicit IndexMRNNDescent(Index *storage, int K = 32);

        ~IndexMRNNDescent() override;

        void add(idx_t n, const float *x) override;

        /// Trains the storage if needed
        void train(idx_t n, const float *x) override;

        /// entry point for search
        void search(
            idx_t n,
            const float *x,
            idx_t k,
            float *distances,
            idx_t *labels,
            const SearchParameters *params = nullptr) const override;

        void reconstruct(idx_t key, float *recons) const override;

        void reset() override;
    };

} // namespace faiss

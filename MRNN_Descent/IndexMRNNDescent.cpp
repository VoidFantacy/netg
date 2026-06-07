/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

// -*- c++ -*-

#include <MRNN_Descent/IndexMRNNDescent.h>

#include "faiss/Index.h"
#include "faiss/impl/NNDescent.h"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <faiss/impl/DistanceComputer.h>

#ifdef __SSE__
#endif

#include <faiss/IndexFlat.h>
#include <faiss/impl/AuxIndexStructures.h>
#include <faiss/impl/FaissAssert.h>
#include <faiss/utils/Heap.h>
#include <faiss/utils/distances.h>
#include <faiss/utils/random.h>
#include <iostream>

extern "C"
{

    /* declare BLAS functions, see http://www.netlib.org/clapack/cblas/ */

    int sgemm_(
        const char *transa,
        const char *transb,
        FINTEGER *m,
        FINTEGER *n,
        FINTEGER *k,
        const float *alpha,
        const float *a,
        FINTEGER *lda,
        const float *b,
        FINTEGER *ldb,
        float *beta,
        float *c,
        FINTEGER *ldc);
}

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

    /**************************************************************
     * IndexMRNNDescent implementation
     *****************************************************
     *********/

    IndexMRNNDescent::IndexMRNNDescent(int d, int K, faiss::MetricType metric)
        : Index(d, metric), mrnndescent(d), own_fields(false), storage(nullptr)
    {
        // the default storage is IndexFlat
        storage = new IndexFlat(d, metric);
        own_fields = true;
    }

    IndexMRNNDescent::IndexMRNNDescent(Index *storage, int K)
        : Index(storage->d, storage->metric_type),
          mrnndescent(storage->d),
          own_fields(false),
          storage(storage) {}

    IndexMRNNDescent::~IndexMRNNDescent()
    {
        if (own_fields)
        {
            delete storage;
        }
    }

    void IndexMRNNDescent::train(idx_t n, const float *x)
    {
        FAISS_THROW_IF_NOT_MSG(
            storage,
            "Please use IndexMRNNDescentFlat (or variants) "
            "instead of IndexMRNNDescent directly");
        // nndescent structure does not require training
        storage->train(n, x);
        is_trained = true;
    }

    void IndexMRNNDescent::search(
        idx_t n,
        const float *x,
        idx_t k,
        float *distances,
        idx_t *labels,
        const faiss::SearchParameters *params) const
    {
        FAISS_THROW_IF_NOT_MSG(!params,
                               "search params not supported for this index");
        FAISS_THROW_IF_NOT_MSG(storage, "");
        // std::cout<< "搜索开始:" << "n=" << n <<std::endl;

        // 数据被分成若干个块进行处理
        idx_t check_period =
            InterruptCallback::get_period_hint(d * mrnndescent.search_L);

        for (idx_t i0 = 0; i0 < n; i0 += check_period)
        {
            idx_t i1 = std::min(i0 + check_period, n);

            // std::cout<< "处理i0到i1数据块:"<< i0 << "-" << i1 <<std::endl;

#pragma omp parallel
            {
                VisitedTable vt(ntotal);

                DistanceComputer *dis = storage_distance_computer(storage);

#pragma omp for
                // 处理i0到i1数据块
                for (idx_t i = i0; i < i1; i++)
                {
                    idx_t *idxi = labels + i * k;
                    float *simi = distances + i * k;
                    dis->set_query(x + i * d);
                    // std::cout<< "处理查询:"<< i <<std::endl;
                    mrnndescent.search(*dis, k, idxi, simi, vt);
                }
            }
            InterruptCallback::check();
        }

        if (metric_type == METRIC_INNER_PRODUCT)
        {
            // we need to revert the negated distances
            for (size_t i = 0; i < k * n; i++)
            {
                distances[i] = -distances[i];
            }
        }
    }

    void IndexMRNNDescent::add(idx_t n, const float *x)
    {
        FAISS_THROW_IF_NOT_MSG(
            storage,
            "Please use IndexMRNNDescentFlat (or variants) "
            "instead of IndexMRNNDescent directly");
        FAISS_THROW_IF_NOT(is_trained);

        if (ntotal != 0)
        {
            fprintf(stderr,
                    "WARNING NNDescent doest not support dynamic insertions,"
                    "multiple insertions would lead to re-building the index");
        }

        storage->add(n, x);
        d = storage->d;
        ntotal = n;
        std::unique_ptr<DistanceComputer> dis(storage_distance_computer(storage));
        mrnndescent.build(storage, x, *dis, ntotal, verbose);
    }

    void IndexMRNNDescent::reset()
    {
        mrnndescent.reset();
        storage->reset();
        ntotal = 0;
    }

    void IndexMRNNDescent::reconstruct(idx_t key, float *recons) const
    {
        storage->reconstruct(key, recons);
    }

} // namespace faiss

---
license: cc-by-4.0
task_categories:
- sentence-similarity
- text-retrieval
---

This repository contains the datasets presented in [VIBE: Vector Index Benchmark for Embeddings](https://huggingface.co/papers/2505.17810):

https://github.com/vector-index-bench/vibe

The datasets can be downloaded manually from this repository, but the benchmark framework also downloads them automatically.

## Datasets

### In-distribution datasets

| Name | Type | n | d | Distance |
|---|---|---|---|---|
| [agnews-mxbai-1024-euclidean](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/agnews-mxbai-1024-euclidean.hdf5) | Text | 769,382 | 1024 | euclidean |
| [arxiv-nomic-768-normalized](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/arxiv-nomic-768-normalized.hdf5) | Text | 1,344,643 | 768 | any |
| [dpr-jina-768-normalized](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/dpr-jina-768-normalized.hdf5) | Text | 20,969,760 | 768 | any |
| [glove-200-cosine](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/glove-200-cosine.hdf5) | Word | 1,192,514 | 200 | cosine |
| [gooaq-distilroberta-768-normalized](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/gooaq-distilroberta-768-normalized.hdf5) | Text | 1,475,024 | 768 | any |
| [imagenet-clip-512-normalized](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/imagenet-clip-512-normalized.hdf5) | Image | 1,281,167 | 512 | any |
| [inaturalist-resnet-2048-cosine](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/inaturalist-resnet-2048-cosine.hdf5) | Image | 499,000 | 2048 | cosine |
| [landmark-dino-768-cosine](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/landmark-dino-768-cosine.hdf5) | Image | 760,757 | 768 | cosine |
| [landmark-nomic-768-normalized](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/landmark-nomic-768-normalized.hdf5) | Image | 760,757 | 768 | any |
| [msmarco-qwen-1024-normalized](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/msmarco-qwen-1024-normalized.hdf5) | Text | 8,840,823 | 1024 | any |
| [yahoo-minilm-384-normalized](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/yahoo-minilm-384-normalized.hdf5) | Text | 677,305 | 384 | any |

### Out-of-distribution datasets

| Name | Type | n | d | Distance |
|---|---|---|---|---|
| [hotpotqa-harrier-640-normalized](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/hotpotqa-harrier-640-normalized.hdf5) | Text | 5,233,329 | 640 | any |
| [imagenet-align-640-normalized](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/imagenet-align-640-normalized.hdf5) | Text-to-Image | 1,281,167 | 640 | any |
| [laion-clip-512-normalized](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/laion-clip-512-normalized.hdf5) | Text-to-Image | 1,000,448 | 512 | any |
| [yandex-200-cosine](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/yandex-200-cosine.hdf5) | Text-to-Image | 1,000,000 | 200 | cosine |
| [cqadupstack-lemur-2048-ip](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/cqadupstack-lemur-2048-ip.hdf5) | Multi-vector | 457,149 | 2048 | IP |
| [cqadupstack-muvera-5120-ip](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/cqadupstack-muvera-5120-ip.hdf5) | Multi-vector | 457,149 | 5120 | IP |
| [yi-128-ip](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/yi-128-ip.hdf5) | Attention | 187,843 | 128 | IP |
| [llama-128-ip](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/llama-128-ip.hdf5) | Attention | 256,921 | 128 | IP |

### Deprecated datasets

Deprecated datasets will remain available, but their benchmark results will not be updated in the future.

| Name | Type | n | d | Distance |
|---|---|---|---|---|
| [ccnews-nomic-768-normalized](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/ccnews-nomic-768-normalized.hdf5) | Text | 495,328 | 768 | any |
| [celeba-resnet-2048-cosine](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/celeba-resnet-2048-cosine.hdf5) | Image | 201,599 | 2048 | cosine |
| [coco-nomic-768-normalized](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/coco-nomic-768-normalized.hdf5) | Text-to-Image | 282,360 | 768 | any |
| [codesearchnet-jina-768-cosine](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/codesearchnet-jina-768-cosine.hdf5) | Code | 1,374,067 | 768 | cosine |
| [simplewiki-openai-3072-normalized](https://huggingface.co/datasets/vector-index-bench/vibe/blob/main/simplewiki-openai-3072-normalized.hdf5) | Text | 260,372 | 3072 | any |

## Credit

The glove-200-cosine dataset uses embeddings from Glove (released under PDDL 1.0):
https://nlp.stanford.edu/projects/glove/

The laion-clip-512-normalized dataset uses a subset of embeddings from LAION-400M (released under CC-BY 4.0):
https://laion.ai/blog/laion-400-open-dataset/

The yandex-200-cosine dataset uses a subset of embeddings from Yandex Text2Image (released under CC-BY 4.0):
https://big-ann-benchmarks.com/neurips23.html

## Dataset structure

Each dataset is distributed as an HDF5 file.

The HDF5 files contain the following attributes:
- dimension: The dimensionality of the data.
- distance: The distance metric to use.
- point_type: The precision of the vectors, one of "float", "uint8", or "binary".

The HDF5 files contain the following HDF5 datasets:
- train: numpy array of size (n_corpus, dim) containing the embeddings used to build the vector index
- test: numpy array of size (n_test, dim) containing the test query embeddings
- neighbors: numpy array of size (n_test, 100) containing the IDs of the true 100 k-nn of each test query
- distances: numpy array of size (n_test, 100) containing the distances of the true 100 k-nn of each test query
- avg_distances: numpy array of size n_test containing the average distance from each test query to the corpus points

Additionally, the HDF5 files of OOD datasets contain the following HDF5 datasets:
- learn: numpy array of size (n_learn, dim) containing a larger sample from the query distribution
- learn_neighbors: numpy array of size (n_learn, 100) containing the true 100 k-nn (from the corpus) for each point in learn
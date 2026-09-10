# 📚 ann-declarative-recall-papers

A periodically updated list of ANN vector search papers on declarative recall through early termination, published in top data management venues.

## 🗺️ Roadmap

- [Why do we care about declarative recall and early termination?](#why-do-we-care-about-declarative-recall-and-early-termination)
- [Proposed solutions](#proposed-solutions)
- [What is this repository about?](#what-is-this-repository-about)
- [Works in top venues](#works-in-top-venues)
- [Contributing](#contributing)
- [Maintainer](#maintainer)

<a id="why-do-we-care-about-declarative-recall-and-early-termination"></a>

## 🤔 Why do we care about declarative recall and early termination?
Vector search is a backbone task in a wide variety of applications, including search engines, recommendation systems, retrieval-augmented generation, and more.
In recent years, vector search has been increasingly adopted in data management pipelines, and the number of users interested in vector search has grown significantly.

Despite its popularity, vector search forces users to face a fundamental trade-off between recall and latency.
Vector search algorithms typically come with a set of hyperparameters that can be tuned to navigate this trade-off.
However, this tuning process is cumbersome, as it requires a large amount of time and resources.
At the same time, hyperparameter tuning is usually based on average recall over a query workload, which can still lead to suboptimal results for individual queries.

This situation is problematic for users because it requires them to understand the explicit characteristics of the underlying vector search algorithm and perform a time-consuming tuning process that may still produce suboptimal results for specific queries.


<a id="proposed-solution-declarative-recall-through-early-termination"></a>

## 🛑 Proposed solutions
This challenge has led to a recent line of research on declarative recall methods through early termination.
Such methods operate on top of a given vector search index and are designed to terminate the search early once a given recall target is reached, without requiring users to understand the underlying vector search algorithm or perform a cumbersome tuning process.

With such methods, the interface of vector search is significantly simplified.
From the current vector search interface, which looks like this:

$\texttt{VectorSearch}(query, k, hyperparameters) \rightarrow results$

where the hyperparameters need specific tuning for each recall target and are different for each underlying vector search algorithm, we can move to a declarative recall interface, which looks like this:

$\texttt{VectorSearch}(query, k, recallTarget) \rightarrow results$

where the recall target is a declarative parameter that is independent of the underlying vector search algorithm and does not require any tuning process.



<a id="what-is-this-repository-about"></a>

## 🧾 What is this repository about?
Given the potential of declarative recall through early termination for vector search, this repository keeps track of relevant papers on this topic, especially papers published in top data management venues.
It contains a curated and periodically updated list of papers related to declarative recall and early termination for vector search, with a brief summary of each paper and links to the original works.


<a id="works-in-top-venues"></a>

## 🏆 Works in top venues
The table below summarizes the focusing in early termination and declarative recall for vector search.
Note that the list includes papers that natively support declarative recall (e.g., Quake, DARTH, Ada-ef, etc.) as well paper that might need slight modification or specific tuning to support that (e.g. LAET, SPANN, etc.).


### Main papers

| Paper name | Paper type | Index type | Venue | Brief summary |
| --- | --- | --- | --- | --- |
| [DARTH+: Approximate Nearest Neighbor Search with Declarative Recall and Quality Guarantees](https://hal.science/hal-05566027/) | Journal | k-nn Graph & IVF | Preprint, 2026 | Dynamic recall prediction through GBDT with probabilistic quality guarantees |
| [The Quest for Faster ANN Vector Search](https://openproceedings.org/2026/conf/edbt/paper-T4.pdf) | Tutorial | - | EDBT, 2026 | Tutorial including an overview of early termination methods [slides](https://helios2.mi.parisdescartes.fr/~themisp/publications/edbt26-FasterAnns-slides.pdf) |
| [ConANN: Conformal Approximate Nearest Neighbor Search](https://dl.acm.org/doi/10.14778/3772181.3772184) | Regular | IVF | PVLDB, 2026 | Early termination with conformal prediction for quality guarantees |
| [Ada-ef: Distribution-aware exploration for adaptive HNSW search](https://dl.acm.org/doi/10.1145/3786639) | Regular | k-NN Graph | SIGMOD, 2026 | Early termination based on efSearch prediction under inner product |
| [DARTH: Declarative recall through early termination for approximate nearest neighbor search](https://dl.acm.org/doi/10.1145/3749160) | Regular | k-nn Graph & IVF | SIGMOD, 2026 | Dynamic recall prediction through GBDT |
| [Quake: Adaptive indexing for vector search](https://www.usenix.org/system/files/osdi25-mohoney.pdf) | Regular | IVF | OSDI, 2025 | Early termination through IVF-partition recall estimation with volume overlaps |
| [LIRA: A learning-based query-aware partition framework for large-scale ann search](https://dl.acm.org/doi/10.1145/3696410.3714633) | Regular | IVF | WebConf, 2025 | Early termination through k-nn location probability prediction for IVF partitions |
| [Patience in proximity: a simple early termination strategy for HNSW graph traversal in approximate K-nearest neighbor search](https://dl.acm.org/doi/10.1007/978-3-031-88714-7_39) | Regular | k-NN Graph | ECIR, 2025 | Patience-based early termination |
| [Early exit strategies for approximate k-NN search in dense retrieval](https://dl.acm.org/doi/10.1145/3627673.3679903) | Regular | IVF | CIKM, 2024 | Patience-based early termination |
| [Auncel: Fast, approximate vector queries on very large unstructured datasets](https://www.usenix.org/conference/nsdi23/presentation/zhang-zili) | Regular | IVF | NSDI, 2023 | Early termination through k-NN error estimation |
| [Learned probing cardinality estimation for high-dimensional approximate NN search](https://ieeexplore.ieee.org/document/10184837) | Regular | IVF | ICDE, 2023 | Early termination through DL-based nprobe prediction |
| [ProS: data series progressive k-NN similarity search and classification with probabilistic quality guarantees](https://link.springer.com/article/10.1007/s00778-022-00771-z) | Journal | iSAX | The VLDB Journal, 2023 | Early termination through progressive predictions with probabilistic quality guarantees |
| [SPANN: Highly-efficient billion-scale approximate nearest neighborhood search](https://dl.acm.org/doi/abs/10.5555/3540261.3540659) | Regular | IVF | NeurIPS, 2021 | Early termination through distance-based thresholds |
| [LAET: Improving approximate nearest neighbor search through learned adaptive early termination](https://dl.acm.org/doi/10.1145/3318464.3380600) | Regular | k-NN graph & IVF | SIGMOD, 2020 | Early termination based on distance calculation prediction |
| [Progressive similarity search on time series data](https://ceur-ws.org/Vol-2322/BigVis_5.pdf) | Vision | iSAX | BigVis, 2019 | Early termination through progressive predictions |

### Honorable mentions and broader papers
The papers summarized below are not strictly focused on early termination and declarative recall, but they are relevant to the topic and provide useful insights and motivations for it.

| Paper name | Venue | Brief summary |
| --- | --- | --- |
| [A Super Fast K-means for Indexing Vector Embeddings](https://arxiv.org/abs/2603.20009) | Preprint, 2026 | A very optimized K-means algorithm for IVF that (among others) utilizes the idea of early termination to early terminate the K-Means procedure |
| [Filtered Vector Search: State-of-the-art and Research Opportunities](https://www.vldb.org/pvldb/vol18/p5488-caminal.pdf) (Tutorial)| PVLDB , 2026 | A comprehensive tutorial on filtered vector search, that provides some additional motivations for early termination methods [slides (13-15, 34-36)](https://storage.googleapis.com/gweb-research2023-media/pubtools/1024140.pdf) |
| [Towards Robustness: A Critique of Current Vector Database Assessments](https://arxiv.org/abs/2507.00379) | Preprint, 2025 | A critique of current vector search algorithm result quality assesment using the average recall across all queries, which motivates the need for query-adaptive early termination solutions |
| [The Many Facets of Approximate Similarity Search](https://ieeexplore.ieee.org/document/4492921) | SISAP, 2008 | A guide of several approximate similarity search quality assesment measures that go beyond the average recall metric |


<a id="contributing"></a>

## 🤝 Contributing
Contributions are welcome. If you know of a relevant paper that should be added, please open an issue with the paper details.


<a id="maintainer"></a>

## 🧑‍🔬 Maintainer
I maintain this repository and welcome suggestions for improvements.
I am [Manos Chatzakis](https://mchatzakis.github.io/), a PhD student at the University of Paris Cité, interested in high-dimensional indexing and search, with a focus on declarative recall and early termination methods for vector search.
I am the lead author of the DARTH and DARTH+ papers, as well as several upcoming papers in this area, and I am excited about the improvements this topic can bring to the vector search domain.

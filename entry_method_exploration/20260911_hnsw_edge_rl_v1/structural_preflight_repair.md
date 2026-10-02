# 训练前结构约束修正

首版预检在 WebVid HNSW 构建后、首次查询和首次优化前停止，原因是程序要求原节点出度至少2。独立解析已序列化图确认38/815节点原出度为1，但从入口的正向与反向可达节点均815；这是原 hnswlib 的合法图。

原protocol、源码、binary及首次冻结均保留。继任environment_v2仅将最少保留2条最近原边改为min(2,原出度)，仍保留完整BFS出树/入树，要求原图强连通，拒绝零出度或不合法边。没有新增边、改变画像或放宽检索收益门；奖励、两个seed、600步、split、随机对照、预算不变。原严格结构预检失败没有质量/训练结果，NSG及HNSW查询均0，只有一张原图的构建。v2重新完成预检后才允许新真实搜索。

有效入口为src/preflight_v2.py、src/train_v2.py、src/native_v2.py与bin/environment_v2.so；线上性能评测仍为原hnswlib编译的bin/evaluate，无训练hook。

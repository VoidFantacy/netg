# E96 HBKM 参数来源修正

原 protocol 保留原字节。准备阶段直接读取可复用 WebVid hub 的 manifest，确认它使用 two-level HBKM、k1=32、k2=16、Sinkhorn10、max_iters20、lambda=.01、seed42。协议中“8叉三层”与“复用已验 Web hub，并给 Y/LAION 同参数”两项存在冲突，前者是准备记录误读。以实物和 manifest 为准，明确全部三集使用两层32×16，Y/LAION 在任何 hub 构建前修正并锁定。Web 的 hub、已生成标签和进行中的训练不变；本修正不由质量、监控曲线或最终测试表现驱动。

直接证据：`gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/hbkm512_sinkhorn_seed42_v2/manifest.json`。原 hub SHA c401db1f0cb23ea66812a7b54b2579b974d0323c3688ad0659cd921e2d4c9479；原 ID SHA a0f3db4abd7cc7e4d4db852c396c8e9db7a9b810932e8d5d195d8b15f9d7b217。

同次源码精化：负样本严格执行作者 `combine_ep_gt.py::sample_neg`，先把999改为−1，再从最大值向下搜索阈值，直到负样本数>64或阈值等于修改后最小值+1；无命中的正负集合均为全512，依作者训练规则过滤。hidden Transformer 的内部 dropout 按作者缺省 .1，模型外 ReLU 后 dropout .05。独立 hnswlib 副本仅为构建随机层级生成器加互斥锁，消除并发 RNG 访问；搜索函数不改。

最终失败查询率定义为 Recall@10=0，即返回 top10 与精确 GT top10 交集为空；另输出 GT1 miss rate 作为补充，二者不混称。

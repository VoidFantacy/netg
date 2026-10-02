# E96 新 OOD 四类方法比较：准备记录

用户已授权 GATE、当前 GT10、NSG、全量 HNSW 在新 OOD 数据集上评测；最大搜索预算1500，每点三次计时平均。旧E95固定H增强分支仍停止，本轮是新数据上的基线评测。

拟采用 VIBE 的完整 yi-128-ip / llama-128-ip，公开版独立test1000，原始IP不归一化。先取得固定版本文件与生成代码，只检查身份、形状、learn/test去重和GT定义；正式模型/拆分协议在任何训练/方法查询前冻结。测试数据仅用于身份与独立性检查，不用于选择模型。全量HNSW的efSearch与NSG的L分别命名，最终比较完整Recall-QPS。

大文件在本目录，新增产物预算4GiB、剩余空间至少2GiB；预计两个原始HDF5共0.60GiB。保存完整源文件/日志/模型/输出，不清理既有资产。查询CPU15/进程与OMP/BLAS/MKL各1线程、方法串行；离线准备单列成本。无新系统配置或外部消息。

来源：https://huggingface.co/datasets/vector-index-bench/vibe ，固定revision 07b387891a221b7b073b83d2f752b76462e5fa03；https://github.com/vector-index-bench/vibe ；GATE https://github.com/jacksondca/gate ，原件/CPU-IP适配需分别记录。

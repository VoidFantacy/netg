# 计算路径判断的来源与限制

官方Faiss v1.15.0的[IndexFlat调用](https://github.com/facebookresearch/faiss/blob/v1.15.0/faiss/IndexFlat.cpp)、[距离分派](https://github.com/facebookresearch/faiss/blob/v1.15.0/faiss/utils/distances.cpp)和[结果容器分派](https://github.com/facebookresearch/faiss/blob/v1.15.0/faiss/impl/ResultHandler.h)给出本次两个固定因素。当前运行时参数已单独读取核对：128000、query block4096、database block1024、reservoir阈值100；未修改这些参数。

在没有IDSelector且query数不少于线程数时，当前代码的IP分派会用nq×d与128000比较；当前常规256批分别是Web131072和Y51200，1024批分别是524288和204800。这是对当前源码分支和参数的推断，尚无本实验性能结果。k100与k10分别触发reservoir与heap，不能只凭k变小就保证wall更短。

数学上同一实数内积全库top10可由top100截取；浮点实现的不同累加路径和并列规则使得逐位、逐ID身份仍须实测。已有156的短尾浮点差提醒我们，不能因函数都叫IndexFlatIP就假定两次输出逐位相同。

该检查检验工程费用，不新增检索方法或理论原创性。原费用参照仍按原实测有效保留；若共享优化成立，默认与省标签候选都应使用，之后重新测完整费用，不能从局部搜索吞吐直接乘算最终加速比。

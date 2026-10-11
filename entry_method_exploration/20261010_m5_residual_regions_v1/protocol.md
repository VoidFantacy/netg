# E174 M5残差候选区域扩展：冻结试验 v1

本轮用户“试试”授权的对象是M5扩展。原M5和GT10均保留，不切默认，不恢复E172，不重新训练。当前每dataset跨方法TRAIN历史超额；新增拟合、标签教师、模型/表/画像/图构建均0。编译、查询验证和报告费用单列。

## 假设与方法

原M5以跨模态训练query实际missing GT1/GT100建立冻结posting：每路由行最多8个ID，原三行并集最多24。原GT主搜索及原M5全C重评分/严格TopK合并均保留。新版本从同一份C的已付fresh scalar负IP分数中，每行选距离最小且不在原GT返回R的seed，平分沿原candidate arrival；最多3个seed去重，不补位。选seed的行来源不同不是不同basin证明。

按物理邻接槽轮转(seed0-slot0,seed1-slot0,seed2-slot0...)读取原NSG。跳过padding、非法ID、主搜索vt已见、全部原C和本次X重复；每个新ID用原scalar raw-IP评分，最多additional24或96次。局部不改主vt，所有C及X按arrival优先级严格合并；新X的priority晚于全部R/C。X非有限/失败保完整原M5返回与已付成本，不回退丢掉M5救回。预算不包括最多K个原R再评分；总直接候选≤48/120，最大读3×degree个槽。本版是一跳候选生成，不是暂停/恢复、续搜或新底图。

## 预锁范围

两集WebVid/Yandex，真实K=1/100各自搜索。实际L：WebVid [800,1000]；Yandex [1000,1200]。选择来自此前已曝光的预算债诊断及较小跨档质量差，不读取本轮角色响应选择。其他L不外推。两集各confirm_a全部4096作机制pilot，随后confirm_b全部4096作冻结确认，不按a结果取消b、更换参数、增加seed/阈值或扩大网格。a打开后成为本轮开发数据；b的向量/GT仅行政SHA身份预检，quality在全部b native完成后打开。两个角色原E172生成且原模型未拟合使用，历次实际消费审计另存；不单凭名字声称全项目未曝光，也不声称语义IID。

pilot_a9方法：GT, M5, M5REG24, M5REG96, M5FIRST96, MFDIRECT, MFREG96, GEODIRECT, GEOREG96。M5FIRST96每行选原C里first seed，其余完全相同；MF使用原已冻missing_frequency，GEO使用原已冻fullbase_geometry。所有模型先冻结，无重新学习。confirm_b固定5方法：GT, M5, M5REG96, MFREG96, GEOREG96。主候选唯一M5REG96，两集/两K共享策略。72 pilot点+40确认点=112点，336批正式wall；无adaptive质量门阻挡已授权探索。

每点3轮完整单线程CPU15 wall，方法按(KL ordinal+round)左旋，warmup256一次。完整wall包括正常输出分配/初始化/释放、原路由/NSG、query合法域guard、查表、R/C重评分、seed选择、邻接读取/过滤/去重、新评分/合并。加载、hash、GT评分、写盘及独立oracle不在wall内，不由dot预算声称同wall。较大L GT为真实费用参照，终局没有pending frontier，不称same-state continuation。

每point保存全4096 plain真实返回，全部direct独立线性merge和region完整candidate trace/线性merge audit；256事前均匀query plain/count bits及NDC。诊断counts只代表256，候选trace及GT rescue/damage对全部4096。timed输出不保留，audit不冒充逐timing bits证明。CountDC改变prefetch路径，只用于词/计数核验，不能作性能。

## 判定与停止

先验证实现、输入/角色/模型/主图身份及域/唯一性/strict merge；所有预锁方法全部运行后按原exact IP GT独立评分，给出paired rescue/damage、固定seed 2000次paired query bootstrap描述区间、三轮QPS范围及paired速度比。same-L区域/原M5与跨L区域/GT均报告；任何Recall升/QPS降记取舍。确认b主候选同L保全原M5，净新增救回、表外候选/目标覆盖及与MF/GEO信息控制分别核验。

本轮“尝试”完成条件是112点真实有限矩阵、完整必要核验和报告完成；不要求强造正收益。仅两角色都正且确认Recall区间下界>0、三轮都更快的具体离散比较可记较强局部双升证据；多比较不作为总体替换检验。未达成则停止此冻结一跳/预算/seed版本，不继续从a/b反馈调参。任何默认替换仍需独立更广范围，原GT10默认保持。

初始git分支research/state-20261002；HEAD96cf05d5410cf51272048cd1f90b4bb194e23c62。原E173、旧E172产物及主搜索源码只读。新资源总产物≤512MiB、min free1GiB、RSS≤64GiB、单job≤7200s。性能期不并发训练/GT/构图/编译/数值分析。

# E176：原 M5 成本优化与剩余遗漏补全的冻结曲线尝试

用户于2026-10-10授权“尝试一下，同样画出曲线图”，随后明确允许每数据集额外最多15分钟，覆盖合法训练窗响应生成与补全表编译。旧累计TRAIN Web21724.972836322秒、Y15589.205719895秒完整保留；本次增量单列，不清零、不恢复任何旧队列。

## 方法与信息来源

原NSG、GT10、原M5、原M5REG96保持E175源码、base/主图/metric/路由/原表身份。新M5OPT复用刚完成的原scalar主搜索R分数，保存原posting行到C索引；REGOPT96再保存旧posting支持seed原图行的最后有效slot界，保持原slot-major/route-minor候选顺序。元数据构建是非学习预处理，完整计startup、resident；所有返回必须逐词等于原M5或原REG96。

新增补全标签严格为 D(q,K,L)=GT_K(q)减去原M5最终返回。FIT使用旧合法20K训练窗，不读公共测试监督。K=1/100、L=200/400/800/1000/1200分别实际生成原GT10与原M5返回，以及每route的原C最佳候选。原C先排除原GT10返回、全三行首次出现去重；winner按已付原scalar分数和原C arrival，三route赢家不去重。

每K/L独立编译两个同预算模型：M5RES12以(route,winner)为键，WIDE12以route为键（winner=-1）；各键至少两个distinct TRAIN query支持、每键最多四目标、总在线额外目标≤12。两者均只拟合原M5成功C提交的query（status=2），与线上原C为空即不扩展的资格一致；零残差但status=2的query仍计键支持。采用相同剩余遗漏监督与确定性整数边际覆盖规则；全三route共享(q,target)覆盖状态。pair键未命中纯空，不回退route表。WIDE12是route-only同预算残差控制，不能称沿原GT10遗漏标签简单加宽的原M5。

线上保留完整原M5 C≤24。新表lookup、winner选择、排除原R/C/X重复、所有新scalar评分、严格原priority堆合并和输出均计时；主图遍历和visited不变，没有新搜索/图边/MLP。R分数复用的优化机会同时提供给原M5OPT，所有优化方法在正式wall前的全窗口untimed核验逐valid R word与独立fresh scalar一致。无法满足则停止版本，不静默把不一致称等价。

## 固定数据与矩阵

两数据集WebVid2.5M、Yandex official10M原raw-IP。公共各前10000，与E175同窗口、既有GT原定义；该窗口已曝光，只有public_test角色，不称新盲测或确认集。训练与公共query/源行身份及历史split互斥在preflight核验。

8方法固定顺序：NSG、GT、M5、M5OPT、M5REG96、REGOPT96、WIDE12、M5RES12。真实K1/K100、五L=200/400/800/1000/1200，共160点、480完整wall批次。不得按partial结果改方法、点、模型、样本、重复或停止标准。

FIT每dataset全部响应生成及compiler完整生命周期累计≤900秒，timeout/异常保留partial并停止该拟合版本，不根据partial选模型。两个dataset串行；全部模型编译完成并冻结，才读取公共评测响应。新监督不生成新的exact GT，继承标签成本保留；本次FIT响应与编表实际费用完整披露。

正式CPU15、实际进程/OpenMP/BLAS/MKL等threads=1；每次只有一个被测方法，没有并发拟合、编译、GT或数值分析。每K/L先完成各方法全窗口untimed scalar/linear oracle、main包/优化参考逐词核验，随后固定warmup256、三轮按(KL ordinal+round+offset) mod8旋转。QPS=n/完整normal Batch生命周期wall，包含分配/初始化/路由/DC/vt/原主搜索/全部补全/输出释放；加载/身份/oracle/count/写盘/GT评价均另列阶段成本。

完整plain每点保存10000条ID/距离/入口/profile。没有第二次全窗口native replay，也不捕捉正式timed packet；证据是全量untimed独立fresh-word/linear oracle、所有路由方法main包与本轮GT逐词对照、优化方法与原版最终包逐词对照，以及固定均匀256的独立count/plain核验。不能沿用E175的full-second-replay声明。

原REG96保存20点的完整128-word候选trace；两补全方法各保存20点的20-word轻trace：[winner0,winner1,winner2,nC,nX,nWinnerRows,m5_committed,extension_aborted,X0..X11]。OPT返回等价另核，不重复存REGOPT fulltrace。NDC仅256样本，实际辅助调用计入graph_ndc，核验用fresh DC不计正式调用。

资源：输出累计≤1536MiB（含新源/模型/FIT响应/raw/分析/图及根文档），最小free1GiB，RSS≤64GiB，每正式dataset query job≤10800秒。所有source/model SHA及大源既有完整SHA+本次精确stat前后闭合；大base/index live word按原加载合同核验，不能借路径签实际callback资格。

## 分析、图与终点

在全部native成功且active为空后才解码公共GT/返回，动态核160点/480轮。同L所有无重复方法对28×20=560；六个post/opt/reg/bank较小L对较大L GT共240；总800个离散描述比较。报告净成员rescue/damage、Recall百分点、逐轮QPS比中位与范围；2000次固定seed paired-query bootstrap为描述区间，没有总体多重校正，不能当可靠确认门。

主要判断分别比较：M5OPT对M5的等价省费；REGOPT96对M5OPT的新增质量费用；M5RES12对M5OPT及同budget WIDE12；小L候选对大L GT的实际偿债。仅严格Recall提高且完整QPS提高记观测双升，一升一降记取舍。两点QPS中位比和三轮配对比中位分开，跨L只用真实点、不插值证明。

主图四panel为Web/Y×Recall@1/100，展示NSG/GT/原M5/原REG96/M5RES12；机制图展示原M5/M5OPT/REGOPT96/WIDE12/M5RES12。每线五实际L，纵向三轮min–max，所有回退点保留，PNG/SVG与CSV均交付。图注说明已曝光公共10K、raw-IP、T1及误差含义。

终点为冻结矩阵、独立整数/费用/机制审计、曲线与完整报告交付后停止。若资源/拟合/语义失败，完整保留失败和缺失范围，不混接旧timing。默认仍GT10；该公共窗口尝试本身不授权默认替换、独立确认或后续无限调参。E173/E174/E175原件与旧STOP原范围均不回改。

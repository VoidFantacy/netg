# E60–E62之后的有界下一步（设计，未实现/未运行）

本稿不是查询许可闸门；用户已授权今天持续研究，下一串行会话可读当前证据后前瞻调整。当前会话完成三个完整阶段，在10:15前安全交接，不启动另一个CLI或代理。

## 证据与优先级

E60可行辅助正状态少；E61通过全fit成员归属重权扩大覆盖，却fit本身净负；E62只保留评分/拓扑均cal负，两者都能致损且有交互。暂停这三条同类扩展。E61每query质量1且m=10时A_missing=A_all，旧zero-hit并没有直接增权，原零命中群45/32条救回仅是共享变化。本轮不能把这个救回率当作可预测的收益。

优先备选：保持原GT10 raw-hub hard/soft归属a_q，改变query质量，不挑选遗漏成员。令z_q=1[原P在L128的GT10 hits=0]，w_q=(1+z_q)*N/(N+sum z)，Pnew=normalize(unit_raw_hub + sum_q w_q*a_q*unit_q)。固定增权2倍、全局质量N=20000；区别于直接把总query质量加大而减弱raw先验。baseline w=1必须恢复原P。随机query身份对照在相同20K中固定seed20260913无放回选同数量348/311条，采用相同质量分布/总量，但不保持其真实难度。不能据此声称完全控制难度分布。

先读history04、旧E09原manifest及`benches/run/build_utility_residual_prototypes.py`。E09以top32单入口signed utility和hardness调整残差，本备选沿原GT10几何归属，只改query质量；两者同属已有hard-query重权范畴，没有新颖性结论，旧E09的WebVid局部正信号不能抹掉。

建议只做原P、真实zero增权、随机身份三模型/集，fit20K+历史cal1024+历史audit1024。无新GT，复用E33完整40K实际基线及本日4096开发缓存；模型冻结前不读新模型反馈。cal只有真实模型可选：净命中>0、严格zero-hit失败数不增、mean totalNDC≤原P×1.01；audit只描述，随机对照不参与推荐选择。fit若净负/损伤集中应明确报告，不机械扩大权重。无门通过则停止此2倍版本，不扫描倍数、随机seed或测试集。

物理图仍普通HNSW构建，原NSG/base/GT/top3/raw-IP/H不变。每集最多3×22048路由+3×64三路parity，预留45000NSG、67000HNSW，双集90000NSG/134000HNSW，6build；输出<192MiB、free≥7GiB。单原生CPU15/线程1、库1，分析只在所有native job实际退出后运行。每图W/topology全字节及实际三路parity，独立复算query质量/归属/聚合、原P回归和所有返回mask；新动作反馈统一计开发训练。成本上限不足时留待监督者下一次串行会话，不扩矩阵。

这是备选E63的新合同草案，不能把它写成已实现。下一会话先运行handoff的只读preflight，再锁自己的protocol/config/src/input manifest；今天用户授权覆盖实际实现和实验，无需索要重复批准。

## 正式性能交付准备

今天的新方法图在`candidate_inventory.json`，包含真实遗漏画像A及S/T干预图和sham控制，各自适用加载方式明确。新的最终比较协议中先定义开发规则再冻结best_all和best_new；best_new不是过门声明。若之后仍没有改善，也需展示今日实际失败模型与NSG/Fast/GT10同批完整QPS–Recall/zero-hit曲线和增损查询，而不是只复用昨天结果。

E34重复validation2000不参与任何训练/动作接受/候选选型。20:00停止新训练，20:40停止新增查询，21:00交付；CPU15线程1、同机全批纯wall、五L五轮，计数/评分/I/O不入timer并保存aligned逐query。独立检查所有对比方法与输入身份、实际线程、重复wall、Pareto及零命中定义；不将缓存标签阶段wall或NDC代替性能。

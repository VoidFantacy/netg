# 诊断脚本下标修正

初版把E123的TargetService参照动作误取为arms[1]（实际GlobalCost），全动作恢复断言在首折立即失败，未写任何真实派生统计。原analyze.py、frozen.json、synthetic.json和run.log保留。v2按原config.locked.json中的名称读取TargetService索引3；不改E123/E124模型、原动作、标签或诊断协议。v2单独冻结/日志。

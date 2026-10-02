# E66派生JSON导出修复

首版analyze.py完整原始结果重评分和CSV写入后，selection的total_NDC布尔值为numpy.bool_，json.dumps拒绝保存。原脚本、log和四CSV保留；analyze_v2仅把该门值转为Python bool，并对既有CSV逐字复核而不覆盖。无新增ANN/训练/GT/模型或门改变。

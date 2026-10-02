# 分析前的路由恒等键扩展

E71同时比较同W、同query、同graph的ef10/ef30。继承的E67 verify_slots.py只以W/query作为跨L路由恒等键，当同画像以两个ef出现在新批次时会错误要求二者入口相同。该旧文件已经纳入prequery_freeze，保留其原字节。

在任何E71数值分析执行前新建verify_slots_v2.py，键增加mapping digest、source graph SHA、ef_search；相同完整路由身份跨L仍须slot/距离/真实入口/labels全部一致，不同ef不强制一致。analyze使用新模块，全部独立排序/去重/距离验收保持。尚未发生分析失败或输出修改，0新ANN/训练/GT；native binary、计时、源图和冻结配置均未变化。新增分析源在preanalysis_freeze记录。

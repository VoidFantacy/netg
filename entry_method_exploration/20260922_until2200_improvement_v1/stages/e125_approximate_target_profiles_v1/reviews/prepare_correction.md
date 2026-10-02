初版prepare在任何label/search/fit之前因列表推导漏写 for L in ls，抛出NameError。原源及prepare_frozen保留；v2只补该循环并允许复用已创建的空目录/相同复制文件，所有样本、预算、门及配置不变。无已完成结果被覆盖。

from pathlib import Path
import csv,json,hashlib,shutil,time
R=Path(__file__).resolve().parents[1];old=R/'analysis/delivery_v1';out=R/'analysis/delivery_v2';A=R/'analysis/final_v1'
assert not (out/'report_zh.md').exists()
rows=list(csv.DictReader((A/'same_L_deltas.csv').open()));cov=list(csv.DictReader((A/'candidate_coverage.csv').open()))
names={'deep10m_l2_v1':'Deep10M','sift10m_bigann_l2_v1':'SIFT10M','gist1m_l2_v1':'GIST1M','webvid2_5m_light_v1':'WebVid','yandex_t2i_official10M_ip_v1':'Yandex','coco':'COCO','flickr30k':'Flickr30k'}
fam={d:('soft' if d in ('deep10m_l2_v1','sift10m_bigann_l2_v1','webvid2_5m_light_v1') else 'hard') for d in names}
lead=['## 本轮核心判断与实际适用范围','',
'GT10 的入口方案可以迁移到非多模态数据。Deep 的完整 K1/K100 曲线有较清楚的吞吐优势；SIFT 的 K100 有优势，K1 在饱和召回端存在多值和交叉；GIST 的 K100 优势约为百分之一量级，三轮并非所有位置同向，K1表现混合。它更适合作为改善搜索效率的入口方案来评价；同L救回与新损伤须另计，不能从加速直接推断失败查询净减少。','',
'当前16K训练、K100/L200教师、B32静态遗漏表在Deep和SIFT上的新增召回很小，完整K100共同区间曲线低于各自GT10。GIST在部分K100区间有小幅收益，K1曲线总体付出额外时间。该残差版本尚不适合作为三套非多模态数据的通用增强；GT10本身的迁移收益与残差的迁移收益应分别保留。','',
'多模态中，WebVid与COCO的B32在K1/K100共同区间均改善，三轮描述同向；Flickr存在交叉，Yandex的K100曲线仍较低。这里的改善是已有测点折线及三轮复测证据，不能外推到新图、新种子和新查询。数据类型、库规模、训练分布、metric与容量密度没有单独因果配平。','',
'固定L200的失败修复见下表。K1列以原GT10失败查询为分母；K100列以原GT10遗漏成员为分母。Dee​​p、SIFT、Web取soft示例，其余取hard；全部家族和全L原表均在后文，未将不同家族拼成一条部署曲线。'.replace('Dee​​p','Deep'),'',
'| 数据 / 家族 | K1救回 / 原失败 | K100救回 / 原遗漏 | K100遗漏修复率 | ΔRecall@100 pp | 同L ΔQPS@100 % |','|---|---:|---:|---:|---:|---:|']
selected=[]
for d,lab in names.items():
 m=fam[d]+'-JOINT32';z=[next(x for x in rows if x['dataset']==d and x['method']==m and x['K']==str(k) and x['L']=='200') for k in (1,100)];a,b=z
 lead.append(f"| {lab} / {fam[d]} | {a['rescued_members']} / {a['reference_missing_members']} | {b['rescued_members']} / {b['reference_missing_members']} | {100*float(b['rescue_rate_on_missing']):.4f}% | {float(b['recall_delta_pp']):+.4f} | {float(b['qps_pct']):+.2f} |")
 selected.extend(z)
lead += ['', '在这三个非多模态数据的L200/K1示例中，B32没有救回原失败查询。全预算上Deep B32的K1最大净增为0.01pp、SIFT为0、GIST为0.30pp（GIST测试仅1000条，0.30pp即3条）。这些数值不能用本表的单点概括为所有失败均不可修复；完整范围已测试并保留。','',
'## 残差迁移弱的直接证据','',
'在K100/L200下，Deep-soft的29220个测试遗漏中，训练残差全局源仅包含195个，当前三路由未截断源包含86个，B32实际救回21个；SIFT-soft对应18468→140→62→25。即使当前训练源无限扩表，源外目标仍无法被这个固定候选来源补回。该上界只约束本轮训练来源，不约束新增教师或其他方法。','',
'GIST-hard对应10886→4242→1117→66，损失更多发生在路由关联和有限容量。Web-soft对应272967→173900→98679→20257，COCO-hard为46556→37606→25246→13715。同样约90个实际补算候选，命中遗漏的能力不同，是本轮可直接验证的差异；不能据此独断语义或模态是唯一原因。','',
'## 风险、成本与后续边界','',
'360个补全匹配点中的成员损伤共5个事件，来自2条不同query。WebVid的4个事件属近边界，但未证明特定原生舍入倒置原因；COCO的1个事件已有双方原生分数及精确有理数比较，确认一次1ULP次序倒置。全部严格ID损伤与原GT原样保留，不把近边界分类写成算法无损。','',
'本轮正式suite为18267.58秒（约5.07小时，内含1935次计时、预热、输出和核验），独立整数复算407.80秒；费用范围和各阶段嵌套关系列于后文。首次Deep教师的调度状态字符串修正保留了原失败收据和独立修正审查，已完成的32000次教师查询没有重跑；其26.80秒费用保留，未含在后续离线suite160.94秒内。','',
'当前保留E99生产默认。研究上保留WebVid/COCO的补全收益；非多模态优先保留GT10入口方案，残差只作为受来源覆盖和容量限制的候选。下一步若研究训练源更新、容量分配或线上困难查询识别，应另立问题；本轮七集固定矩阵到此收口。','']
text=(old/'report_zh.md').read_text();needle='## 先看结论与证据范围';text=text.replace(needle,'\n'.join(lead)+'\n'+needle,1)
text=text.replace('其中需继续核查的成员事件为 0。','分类器未标记额外的大间隙事件；4个近边界事件的特定原生舍入因果仍未证明。')
(out/'report_zh.md').write_text(text)
shutil.copy2(old/'summary.json',out/'summary.json')
(out/'review_provenance.json').write_text(json.dumps({'status':'ROOT_INTERPRETATION_ADDED_NO_NEW_MEASUREMENTS','parent_report':str(old/'report_zh.md'),'parent_sha256':hashlib.sha256((old/'report_zh.md').read_bytes()).hexdigest(),'report_sha256':hashlib.sha256((out/'report_zh.md').read_bytes()).hexdigest(),'scope':'Readability, fixed-L200 summaries and evidence interpretation; all original scientific measurements/CSV unchanged','selected_rows':selected,'created_unix':time.time()},indent=2)+'\n')
print('delivery_v2 ready')

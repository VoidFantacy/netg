#!/usr/bin/env python3
"""Render the finite offline diagnosis; figures never supply new performance."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import csv
import json
import hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT=Path(__file__).resolve().parent
A=ROOT/'analysis'
def rr(n):return list(csv.DictReader((A/f'{n}.csv').open()))
def num(r,k):return float(r[k])
def f(x,d=2):return f'{float(x):.{d}f}'
def table(header,rows):
    return ['| '+' | '.join(header)+' |','| '+' | '.join(['---']*len(header))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows]+['']

def main():
    ss=rr('dataset_summary');chain=rr('coverage_chain');cr=rr('cross_dataset_associations');within=rr('within_dataset_spearman');bins=rr('feature_quartiles')
    adjusted=rr('baseline_stratified_associations');sensitivity=rr('all_L_and_router_sensitivity')
    oldpoints=list(csv.DictReader((ROOT.parent/'20261017_gt10_residual_comprehensive_v1/analysis/final_v1/points.csv').open()))
    def speed(s,m):return f(next(r['qps'] for r in oldpoints if r['dataset']==s['dataset'] and r['method']==m and r['K']=='100' and r['L']=='200'))
    font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';font_manager.fontManager.addfont(font)
    plt.rcParams.update({'font.family':font_manager.FontProperties(fname=font).get_name(),'axes.unicode_minus':False,
        'axes.spines.top':False,'axes.spines.right':False,'font.size':10,'svg.fonttype':'none'})
    labels=[s['label'] for s in ss];y=np.arange(7)
    fig,ax=plt.subplots(1,2,figsize=(14,6.4),layout='constrained')
    ax[0].barh(y-.18,[num(s,'GT_K100_incomplete_pct') for s in ss],.33,color='#9caec0',label='GT10 未满100条查询 / 全部查询')
    ax[0].barh(y+.18,[num(s,'K100_improved_incomplete_pct') for s in ss],.33,color='#217c8a',label='残差改善查询 / 原未满100查询')
    ax[0].set(yticks=y,yticklabels=labels,xlim=(0,105),xlabel='比例（%；两柱分母不同，见图例）',title='失败很多，不代表残差容易修复')
    ax[0].invert_yaxis();ax[0].legend(fontsize=8,loc='upper left',bbox_to_anchor=(0,-.14),frameon=False)
    left=np.zeros(7)
    fields=[('unseen_source','训练残差源外','#cbd4dd'),('route_lost','源内、当前路由未覆盖','#8bafc3'),('capacity_lost','路由内、B32未选','#e0b36b'),('rescued','实际救回','#217c8a')]
    for key,label,color in fields:
        v=np.array([100*num(c,key)/num(c,'missing') for c in chain]);ax[1].barh(y,v,left=left,color=color,label=label);left+=v
    ax[1].set(yticks=y,yticklabels=labels,xlim=(0,100),xlabel='占原遗漏 GT 成员比例（%）',title='遗漏最终落在哪里：固定 L200 / K100 / B32')
    ax[1].invert_yaxis();ax[1].legend(fontsize=8,loc='upper left',bbox_to_anchor=(0,-.14),frameon=False,ncol=2)
    fig.suptitle('七集既有实际返回复算；固定 E183 简版家族，无新增 ANN / QPS 测量',fontsize=12)
    for ext in ('png','svg','pdf'):fig.savefig(A/f'failure_and_coverage.{ext}',dpi=180)
    plt.close(fig)
    features=[('background_separation_z','背景分离 z'),('GT100_direction_concentration','邻域方向集中度'),
        ('top100_relative_span','Top100相对跨度'),('GT100_mean_training_frequency','目标训练GT频次'),('GT100_mean_residual_frequency','目标训练残差频次')]
    fig,axes=plt.subplots(1,2,figsize=(13,5.3),layout='constrained')
    for ax,outcome,title in zip(axes,['K100_missing_count','K100_net_improved'],['与 GT10 遗漏数的关联','与残差是否改善查询的关联']):
        ar=np.full((7,len(features)),np.nan)
        for i,s in enumerate(ss):
            for j,(feat,_) in enumerate(features):
                v=next(r['spearman'] for r in within if r['dataset']==s['dataset'] and r['feature']==feat and r['outcome']==outcome)
                if v:ar[i,j]=float(v)
        im=ax.imshow(ar,vmin=-1,vmax=1,cmap='RdBu_r',aspect='auto')
        for i in range(7):
            for j in range(len(features)):ax.text(j,i,f'{ar[i,j]:+.2f}',ha='center',va='center',fontsize=9,color='white' if abs(ar[i,j])>.55 else '#172b3a')
        ax.set(yticks=np.arange(7),yticklabels=labels,xticks=np.arange(len(features)),xticklabels=[v[1] for v in features],title=title)
        ax.tick_params(axis='x',rotation=30)
    fig.colorbar(im,ax=axes,label='Spearman ρ（描述性相关，无因果含义）',shrink=.8)
    fig.suptitle('同一数据集内：几何难度与“残差能否补回”是两个问题',fontsize=12)
    for ext in ('png','svg','pdf'):fig.savefig(A/f'within_dataset_associations.{ext}',dpi=180)
    plt.close(fig)
    lines=['# 残差为什么只在部分数据集有效：空间分布与失败修复诊断','',
        '2026-10-24；E184 离线诊断。基底 HEAD `96cf05d5410cf51272048cd1f90b4bb194e23c62`，分支 `research/state-20261002`。新文件仍为本地工作，未提交或发布。', '',
        '**当前默认保留 E99 GT10（WebVid soft-t1 / Yandex hard）。空间结构与查询失败存在关联，但当前静态残差的跨集收益，更直接受“遗漏目标在训练中能否重复出现、当前路由能否覆盖、有限表能否保留”约束。不能概括成多模态天然有效、越小越有效或越聚集越有效。**', '',
        '这里的残差是 `GT_K − GT10实际返回` 的遗漏目标 posting 补全，不是向量量化残差。B32 每个路由行32槽，三个hub去重前最多96个候选；它补最终结果，不改变主图遍历。', '',
        '本轮重算 E183 56,000 条已有测试查询的 L200 实际返回，增加原向量几何诊断；没有训练、构图、ANN、新GT或QPS重测。E183 仍是最新性能证据。', '',
        '## 1. 各集到底失败多少、改进多少','',
        '固定 L200，Deep/SIFT/WebVid 用 soft，其余 hard，补全统一同家族B32。这个展示继承E183简版，不按本轮结果换赢家。K1是实际K1返回，未由K100包含GT1冒充。','']
    lines+=table(['数据集','查询数','K1失败率','K1救回 / 原失败','K100未满100查询','K100少于90查询','残差改善 / 原未满100查询','恢复100/100 / 原未满100'],[
        [s['label'],s['n'],f(s['GT_K1_failed_pct'])+'%',f"{s['B32_K1_rescued']}/{s['GT_K1_failed']}",f(s['GT_K100_incomplete_pct'])+'%',f(s['GT_K100_below90_pct'])+'%',
         f"{s['K100_improved_queries']}/{s['GT_K100_incomplete']} ({f(s['K100_improved_incomplete_pct'])}%)",f"{s['K100_full_repairs']}/{s['GT_K100_incomplete']} ({f(s['K100_full_repairs_of_incomplete_pct'])}%)"] for s in ss])
    lines+=['“未满100”包括只差一个成员；“改善”指逐query净命中数增加，不能等同整条失败解决。下表“遗漏率”和“修复率”以成员计，上表以查询计；所有主分析 L200 点成员损伤为0，其他L的历史边界损伤仍保留。','']
    lines+=table(['数据集','原遗漏成员率','被修复的遗漏成员','净 Recall 增量 pp','Recall@100：GT10→B32','完整QPS：GT10→B32','同L QPS变化'],[
        [s['label'],f(s['K100_missing_member_pct'],4)+'%',f(s['K100_member_repair_pct'],4)+'%',f(s['K100_net_recall_pp'],4),
         f"{f(s['GT_K100_recall_pct'],4)}% → {f(s['B32_K100_recall_pct'],4)}%",speed(s,'GT10-soft-t1' if s['router']=='soft' else 'GT10-hard')+' → '+speed(s,s['router']+'-JOINT32'),f(s['K100_QPS_delta_pct'])+'%'] for s in ss])
    lines+=['QPS全部引用E183三轮完整wall中位数；同L下降是补点费用，不能单独否定同Recall曲线收益。E183中WebVid/COCO两K共同Recall区间折线受益，Flickr交叉、Yandex K100较低，Deep/SIFT K100较低、GIST混合。折线不是新增等Recall实测，本轮未重新推导或重测前沿。','',
        '## 2. 失败率与修复率不是同一回事','',
        '例如COCO的K100遗漏成员率低于WebVid，却能修复更高比例的遗漏；Flickr的库更小，但修复率低于COCO。Deep/SIFT的Top1接近饱和，但仍有超过一半查询未找齐Top100。因此“剩余失败量很少”只能解释部分K1现象，解释不了全部K100差异。','',
        '在本次七集上，以下相关仅为七个异质数据集的描述；规模、metric、特征、训练密度和图没有配平。留一范围不是置信区间，也不提供跨总体显著性。','']
    lines+=table(['与K100成员修复率的跨集关联','Spearman ρ','留一集最小..最大'],[
        [r['feature'],f(r['spearman'],3),f(r['leave_one_dataset_out_min'],3)+' .. '+f(r['leave_one_dataset_out_max'],3)] for r in cr])
    lines+=['源覆盖与修复率不是两项独立的外部证据：救回必须位于源中，二者有结构性包含关系。相关系数用于描述差异，不能凭它宣称发现了因果机制或泛化预测器。','',
        '## 3. 真正的瓶颈分解','',
        '下面所有数字都是“query–GT成员事件”，不是不同base节点数。源为16K合法训练遗漏；路由为当前三个真实hub关联的未裁剪源；表为B32。','']
    lines+=table(['数据集','测试遗漏','曾在训练GT100','训练残差源内','当前路由源内','B32实际救回','源内比例'],[
        [s['label'],c['missing'],c['in_train_GT'],c['in_global_source'],c['in_routed_source'],c['rescued'],f(s['K100_missing_source_seen_pct'],3)+'%'] for s,c in zip(ss,chain)])
    lines+=['忽略并列/舍入损伤时，汇总净提升有以下**记账恒等式**，不是独立拟合出的解释模型：','',
        '`净ΔRecall = 原遗漏成员比例 × 源覆盖率 × 源内路由覆盖率 × 路由内表保留率 × 候选最终救回率 − 损伤比例`','',
        '在主分析L200中，候选覆盖的遗漏全部进入最终结果且损伤0，因此最后救回率为1。一般场景必须核对真实合并输出，不能默认等于1。','',
        '- Deep/SIFT：99%以上测试遗漏在当前训练残差源外。即使取出固定源的全部目标、不计费用，最多额外提升Recall 0.0195/0.0140pp；保持当前路由源时上限更低，为0.0086/0.0062pp。这里的“上限”针对固定源/当前GT10/L200的可补成员，不是已部署算法保证。只扩大当前B32无法填补源外遗漏。',
        '- GIST：源内覆盖约39%，但路由后只剩1117个，再经B32只补66个。源覆盖不足、路由关联和容量保留是不同损失；本集更应关注后两项，不能沿用Deep/SIFT的单一源外解释。',
        '- Yandex：训练残差源内仅约7.53%，最终修复0.51%；同时有来源与选择限制。不能把它说成“空间平坦”或全部归因千万级规模。',
        '- WebVid/COCO/Flickr：训练遗漏有较多重复目标，表有可复用内容，但容量、路由与原遗漏量仍决定实际收益；Flickr高源覆盖不等于比COCO高修复率。','',
        '全局/路由固定源的乐观Recall上限已在 [coverage_chain.csv](analysis/coverage_chain.csv) 逐集保存，不是插值性能点。','',
        '## 4. 与空间分布的关联：直接测了什么','',
        '使用全部原测试query及其原GT100目标向量，float64重评分原平方L2/负内积。每集另抽固定8192个base目标，用于背景分布与全局协方差；保留样本ID及样本向量SHA。未修改base/query归一化或GT。','',
        '- 背景分离z：GT100边界比均匀base样本背景均值好多少个标准差。z大表示该指标下分离更明显；不是论文原始relative contrast，不把IP当欧氏半径。',
        '- 邻域方向集中度：原GT100目标各自单位化后的均值长度；只作辅助几何统计，不改变实际搜索metric。',
        '- Top100相对跨度、query/目标范数：检查局部紧密程度及原IP的模长相关。',
        '- 样本协方差有效秩：`tr(C)^2/tr(C^2)`，C为中心化的总体形式样本协方差；它是各向异性摘要，不能称真实流形内在维数。','']
    lines+=table(['数据集','背景z中位数','GT100方向集中度中位数','样本协方差有效秩','训练残差singleton token','训练残差重复倍率'],[
        [s['label'],f(s['median_background_z'],3),f(s['median_GT100_direction_concentration'],3),f(s['base_sample_effective_rank'],2),f(s['train_residual_singleton_token_pct'],2)+'%',f(s['train_residual_repeat_factor'],3)] for s in ss])
    lines+=['不同metric/来源之间的z和有效秩只作描述，不按单个数值给所有数据集排序。下面在各数据集内关联，所有特征均为离线诊断，使用GT的量不能直接上线。','']
    selected_features=['background_separation_z','GT100_direction_concentration','GT100_mean_training_frequency','GT100_mean_residual_frequency']
    lines+=table(['数据集','z与遗漏数ρ','方向集中度与遗漏数ρ','z与残差改善ρ','训练GT频次与改善ρ','训练残差频次与改善ρ'],[
        [s['label']]+[f(next(r['spearman'] for r in within if r['dataset']==s['dataset'] and r['feature']==ft and r['outcome']==ot),3)
        for ft,ot in [('background_separation_z','K100_missing_count'),('GT100_direction_concentration','K100_missing_count'),
                      ('background_separation_z','K100_net_improved'),('GT100_mean_training_frequency','K100_net_improved'),('GT100_mean_residual_frequency','K100_net_improved')]] for s in ss])
    lines+=['与原遗漏数的关系回答“哪些query难”；与残差改善的关系回答“当前表能帮助哪些query”。Deep/SIFT的背景分离或邻域集中与遗漏数有负相关，而与残差改善的相关接近0；存在几何难度差异，也不保证具体遗漏ID能从静态训练表复用。GIST目标方向集中度较高、补全收益仍小，否定“更聚集就一定更适合残差”的简单解释。','',
        '完整四分位条件率在 [feature_quartiles.csv](analysis/feature_quartiles.csv)；按原遗漏数1–4、5–9、10–49、50+分层后比较特征高低半组的改善概率，见 [baseline_stratified_associations.csv](analysis/baseline_stratified_associations.csv)。只在两组各至少10条的层中标准化，报告覆盖查询数；它仍有层内混杂、选择条件和稀有事件限制，不是因果调整或部署效果。','',
        '**几何也不能被排除。** 粗略控制原遗漏量后，WebVid/COCO的高背景分离组，改善概率仍分别高8.17/11.50pp；同样分层下，高训练残差频次组分别高44.69/19.61pp。无条件ρ接近0可能掩盖“容易的query错误少、但同等错误下更好补”的相反作用；这仍是观察关联，不能宣称几何独立因果已被识别。','']
    lines+=table(['数据集','按遗漏量分层：高z−低z改善概率 pp','高残差频次−低频次改善概率 pp'],[
        [s['label']]+[f(next(r['standardized_delta_pp'] for r in adjusted if r['dataset']==s['dataset'] and r['feature']==ft),3)
        for ft in ['background_separation_z','GT100_mean_residual_frequency']] for s in ss])
    lines+=['这些差值比较的是各数据集全体query特征高低半组，在可比较的遗漏数量层内按层大小加权；两特征可纳入的查询数可能不同，应读原CSV中的included/total字段。','',
        '全预算敏感性：既有全部K100/L与hard/soft的B32成员修复率范围如下。它不是把各L当独立重复，也不是再择优；Deep/SIFT很低、Web/COCO较高的大体差异不依赖单个L200展示点。','']
    sensrows=[]
    for s in ss:
        vals=[100*int(r['rescued_members'])/int(r['reference_missing_members']) for r in sensitivity if r['dataset']==s['dataset'] and r['K']=='100' and int(r['reference_missing_members'])>0]
        sensrows.append([s['label'],f(min(vals),3)+'% .. '+f(max(vals),3)+'%'])
    lines+=table(['数据集','全部已测L / 已有家族B32修复率'],sensrows)
    lines+=[
        '![查询失败与覆盖链](analysis/failure_and_coverage.png)','',
        '![数据集内几何关联](analysis/within_dataset_associations.png)','',
        '## 5. 文献、现有规模控制与可证伪解释','',
        '[Hubs in Space (JMLR 2010)](https://www.jmlr.org/papers/v11/radovanovic10a.html)讨论某些目标反复成为其他点近邻的k-occurrence。它提示要看目标频次分布；这种统计hub与项目中H个真实图入口不同。本轮测的是训练query到base目标的近邻频次/遗漏频次，跨模态场景不直接满足论文同分布设定。','',
        '[On the Difficulty of Nearest Neighbor Search (ICML 2012)](https://icml.cc/2012/papers/580.pdf)用随机点与最近邻的距离对比描述难度，并给出LSH方面的理论分析。本轮借鉴“量化分离度”的思路，未套用其LSH结论去证明有限NSG或残差收益。','',
        'E182同源规模控制已显示：固定H815时K100=90%的折线QPS增益由24.33%降至16.41%；H按规模匹配后为14.07/17.75/17.71/16.41%，不再单调。改变H还改变路由及每hub训练密度；这是容量因素的证据，不是纯几何/纯规模因果分解。当前七集不能覆盖这项混杂。','',
        '**更符合现有证据的解释**：有限图搜索在某些query上产生稳定且可复用的遗漏目标；如果训练query与测试query在目标身份/路由上重复支持这些遗漏，静态表能集中有限槽位而受益。局部几何影响主搜失败，目标重复与路由集中影响补全机会，两者可以分离。这是结合观测的机制假说，未通过随机干预证明。','',
        '可证伪方向（尚未实施）：在固定合法训练源上，以目标重现率/路由分散度预测独立查询角色的修复；用源覆盖匹配的简单频次表作对照，检验几何结构是否仍有额外解释力。对源外主导的数据，应先证明新合法来源能提高目标覆盖；对GIST类则先证明路由/保留策略能利用已有源。全部线上选择、检索、补算费用最终仍须完整T1曲线验证，事后GT特征不是免费门控。','',
        '## 6. 核验、成本与结束边界','',
        '所有主分析整数与E183既有CSV一致；另用不导入主分析或NumPy的stdlib set/Counter脚本逐条复核56,000查询的K1/K100救损、训练源频次与覆盖分区。每集8条query直接对8192背景样本重算距离均值/方差，验证矩公式。该第二实现由同一执行者完成，不冒称独立审稿人或新GT证明。','',
        '小输入实际SHA与大base当前stat前后核对；完整大base SHA继承E183而非本轮重算。本次几何读取的8192样本有新SHA，GT目标向量也从原base直接读取。原图、模型、E183产物未写。','',
        '首个诊断尝试在Deep的布尔数组常量判断处因NumPy不支持布尔减法退出，已保存 [原失败日志](failed_run_v1.log)，修正为等值常量判断后按同协议重算；没有ANN/性能重测。失败尝试精确wall未记录，不能填0。成功诊断成本见 [receipt.json](analysis/receipt.json)，整数第二实现见 [integer_audit.json](analysis/integer_audit.json)；它们不是线上QPS。历史离线/性能成本保留，不重复计入。','',
        '局限：单图/单画像、已曝光测试、GIST仅1K；固定L200跨集难度不相等；全部L/已测家族敏感性另存；8192背景样本不是全库分布证明；秩相关是描述，未作多重检验或泛化校准；覆盖链有结构依赖；几何特征含GT、没有线上代价测量。不能由本轮归因编码器、模态、维度、图质量或得出新可靠Recall–QPS改善。','',
        '本诊断范围完成后停止，无新模型/性能队列，默认不变。', '',
        '复算：在仓库根目录运行 `.venv_cpu/bin/python entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analyze.py`，输出目录非空会拒绝覆盖；要另建版本，不删除旧结果。整数审计和报告脚本分别为 `audit_integers.py` / `build_report.py`。新分析依赖外部原向量/GT/实际返回，不能把只有Git文件的快照说成完整可运行包。','']
    (ROOT/'report_zh.md').write_text('\n'.join(lines))
    (ROOT/'README.md').write_text('# E184 残差、空间分布与失败修复诊断\n\n2026-10-24。只读E183实际返回及原向量的离线研究，未新增性能实验；默认E99 GT10保留。\n\n[中文报告](report_zh.md) · [冻结范围](protocol.md) · [逐集统计](analysis/dataset_summary.csv) · [56K查询](analysis/query_metrics.csv) · [覆盖链](analysis/coverage_chain.csv) · [特征分层](analysis/feature_quartiles.csv) · [核验](analysis/integer_audit.json) · [费用/状态](analysis/receipt.json)\n')
    manifest={str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in ROOT.rglob('*') if p.is_file() and p.name!='delivery_manifest.json' and 'source_before' not in p.parts}
    (ROOT/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('report and two figures rendered')

if __name__=='__main__':main()

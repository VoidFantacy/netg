from common import *
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();pts=list(csv.DictReader((O/'results/points.csv').open()));pairs=list(csv.DictReader((O/'results/paired.csv').open()));failure=list(csv.DictReader((O/'results/failure_queries.csv').open()));g=read(O/'results/gate.json');cost=read(O/'results/cost.json');v=read(O/'reviews/verification.json')
fig,ax=plt.subplots(2,3,figsize=(13,7.2),constrained_layout=True)
for di,ds in enumerate(DS):
 for col,ref in enumerate(['exact_P','compact10','own_approx']):
  a=ax[di,col];sel=[next(x for x in pairs if x['dataset']==ds and x['candidate']=='exact_'+b and x['reference']==(b if ref=='own_approx' else ref) and x['split']=='all') for b in BANKS]
  vals=[int(x['net_hits']) for x in sel];a.bar(['GT global','GT conditional','Joint'],vals,color=['#407caa','#d69542','#5d9e78']);a.axhline(0,color='black',lw=.6);a.set_title(('WebVid' if di==0 else 'Yandex')+' / versus '+ref);a.set_ylabel('Net GT10 hits');span=max(20,max(vals)-min(vals));a.set_ylim(min(0,min(vals))-.24*span,max(0,max(vals))+.25*span)
  for i,(val,x) in enumerate(zip(vals,sel)):a.text(i,val+(.04*span if val>=0 else -.04*span),f'{val:+d}\nfail {int(x["failure_change"]):+d}',ha='center',va='bottom' if val>=0 else 'top',fontsize=9)
fig.suptitle('E82: complete profile ranking, real NSG outcomes | historical aux7952, L128 | no QPS');fig.savefig(O/'figures/exact_utility.png',dpi=160);plt.close(fig)
names=['baseline10','compact10','target10','exact_target10','conditional10','exact_conditional10','joint10','exact_joint10','exact_P','exact_mode'];fig,ax=plt.subplots(1,2,figsize=(14,9),constrained_layout=True)
for di,ds in enumerate(DS):
 rows=[x for x in failure if x['dataset']==ds and x['changed_zero_status']=='True'][:24];mat=np.array([[int(x[m+'_hits']) for m in names] for x in rows]);im=ax[di].imshow(mat,cmap='viridis',vmin=0,vmax=10,aspect='auto');ax[di].set_xticks(range(len(names)),['P','Compact','GT','GT exact','Cond','Cond exact','Joint','Joint exact','P exact','Mode exact'],rotation=60,ha='right');ax[di].set_yticks(range(len(rows)),[x['source_row'] for x in rows]);ax[di].set_title('WebVid' if di==0 else 'Yandex');ax[di].set_ylabel('router_train source row')
 for i in range(len(rows)):
  for j in range(len(names)):ax[di].text(j,i,str(mat[i,j]),ha='center',va='center',color='white' if mat[i,j]<6 else 'black',fontsize=7)
fig.colorbar(im,ax=ax,label='GT10 hits (0 = failure)',shrink=.75);fig.suptitle('E82 failure queries: first 24 changed source rows per dataset; complete union retained in CSV\nHistorical auxiliary data, L128; no QPS and no final feedback');fig.savefig(O/'figures/failure_queries.png',dpi=150);plt.close(fig)
lines=['# E82 新目标画像完整排名的真实效用','',f'三种冻结bank、两数据集完整诊断完成。后续轻量近似候选：{g["bank_for_new_approximation"] or "无；六组原诊断门均未通过"}。原E79–E81门不变，整日21:00目标未完成。','', '| 数据 | 完整排名 | 相对精确P 命中/失败变化 | 相对compact | 相对自身近似 | 门 |','|---|---|---|---|---|---|']
for ds in DS:
 for b in BANKS:
  vals=[]
  for ref in ['exact_P','compact10',b]:
   x=next(x for x in pairs if x['dataset']==ds and x['candidate']=='exact_'+b and x['reference']==ref and x['split']=='all');vals.append(f'{int(x["net_hits"]):+d} / {int(x["failure_change"]):+d}')
  lines.append('| '+('WebVid' if ds==DS[0] else 'Yandex')+' | '+b+' | '+' | '.join(vals)+' | '+('PASS' if g['datasets_banks'][ds+'/'+b]['passed'] else 'FAIL')+' |')
lines += ['', '精确画像前三不是NSG效用oracle，也没有测完整在线扫描wall。上述是同L真实效用诊断，不能称QPS、前沿或最终改善。每bank对精确P和compact全量命中须正、两半非负、zero失败不增、graphNDC<=1.01，相对自身approx全量非负；全部门先冻结。完整两半、GT成员得失、逐query净命中正负、旧收益保留/丢失和新损伤均在CSV。','',f'新增{cost["NSG"]:,}次NSG，其中原P256行plain/count=512、3,593唯一缺口plain/count=7,186、原kernel64。47,712逻辑exact结果中43,800旧复用、319互alias；源缓存碰撞{v["source_collision_checks"]:,}逐字段一致。0HNSW/构图/新训练/GT/编译。双集native {cost["native_elapsed_seconds"]:.3f}s，其中load {cost["load_seconds"]:.3f}s；排名准备 {cost["rank_prepare_seconds"]:.3f}s，主评分{cost["analysis_seconds"]:.3f}s；绘图/文档另计，继承GT/P/旧训练成本未知。这些操作wall不是QPS。','',f'全部{v["set_scored_outputs"]:,}集合/mask独立评分、47,712复用来源与三入口逐行核验、256原P回放及64原kernel/全缺口plain-count通过。三个bank各两行完整标量排名检查，完整bank max聚合和源namespace/rows核验。所有ANN CPU15、实际进程及数值库1线程串行，工具实际terminal0后评分。','',f'失败并集{v["failure_union_queries"]}条dataset/source-row，{v["changed_failure_queries"]}条状态变化；全GT10/各方法三入口与返回ID保存，图仅展示每集前24变化例，全方法零命中行保留。','', '数据为历史router_train[2048:10000]辅助7952及固定两半，选择反馈计训练。P-fit20K含旧train/monitor，cal/audit历史使用；E34最终和held-out未打开。保留全部旧产物和seal，无新默认替换。','', '[前瞻协议](protocol.md) · [原值](results/points.csv) · [完整配对](results/paired.csv) · [收益保留](results/gain_retention.csv) · [质量门](results/gate.json) · [完整失败查询](results/failure_queries.csv) · [效用图](figures/exact_utility.png) · [失败图](figures/failure_queries.png) · [成本](results/cost.json) · [验收](reviews/verification.json)']
(O/'report.md').write_text('\n'.join(lines)+'\n');print(v)

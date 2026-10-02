from train import *

# Post-hoc fit-only differentiation. No optimizer step or search call.
assert read(O/'state.json')['status'] in ['EVALUATION_COMPLETE_ANALYSIS_PENDING','ANALYSIS_COMPLETE_PLOTS_AND_REPORT_PENDING']
def cosine(a,b):
    denom=np.linalg.norm(a)*np.linalg.norm(b)
    return None if denom==0 else float(np.dot(a,b)/denom)

records=[]
for ds in DS:
    qn,pn,tn,headroom=load_fit(ds)
    p=torch.from_numpy(pn)
    q=nn.functional.normalize(torch.from_numpy(qn),dim=1)
    n=len(q)
    for cell in CELLS:
        teacher,kind=cell.split('_')
        target=torch.from_numpy(tn[teacher].astype(np.int64))
        model=Transform(p)
        for checkpoint in ['initial','final']:
            if checkpoint=='final':
                model.load_state_dict(torch.load(O/'models'/ds/cell/'model.pt',weights_only=True,map_location='cpu'))
            contributions={}
            stats={}
            for group,mask in [('headroom',headroom),('no_headroom',~headroom)]:
                model.zero_grad()
                exported=model()
                w=exported.detach().requires_grad_(True)
                total=0.
                ix=np.flatnonzero(mask)
                for b in range(0,len(ix),1024):
                    ids=ix[b:b+1024]
                    z=q[ids]@w.T/.05
                    value=supervised_loss(z,target[ids],kind).sum()/n
                    value.backward();total+=value.item()
                exported.backward(w.grad)
                grad=model.fn.weight.grad.detach().numpy().ravel().copy()
                contributions[group]=grad
                stats[group]=dict(queries=int(mask.sum()),fraction=float(mask.mean()),
                    loss_contribution=total,mean_group_loss=total/mask.mean(),
                    parameter_gradient_norm=float(np.linalg.norm(grad)),
                    per_query_group_mean_gradient_norm=float(np.linalg.norm(grad)/mask.mean()))
            a,b=contributions['headroom'],contributions['no_headroom']
            total=a+b
            denom=np.dot(total,total)
            records.append(dict(dataset=ds,cell=cell,checkpoint=checkpoint,groups=stats,
                gradient_cosine=cosine(a,b),total_data_gradient_norm=float(np.linalg.norm(total)),
                headroom_projection_fraction=None if denom==0 else float(np.dot(a,total)/denom),
                no_headroom_projection_fraction=None if denom==0 else float(np.dot(b,total)/denom),
                excludes_regularization=True,optimizer_steps=0,NSG_calls=0))
geometry=[]
for ds in DS:
    c=read(O/'inputs'/ds/'fit/config.json');h,d=c['hub_count'],c['dim']
    p=np.fromfile(E24/'models'/ds/'gt10_hard/W.f32',np.float32).reshape(h,d).astype(float)
    delta={cell:np.fromfile(O/'models'/ds/cell/'W.f32',np.float32).reshape(h,d).astype(float)-p for cell in CELLS}
    for teacher in ['cost','keep']:
        a=delta[teacher+'_ce'].ravel();b=delta[teacher+'_margin'].ravel()
        scale=float(np.dot(a,b)/np.dot(a,a))
        residual=b-scale*a
        geometry.append(dict(dataset=ds,teacher=teacher,ce_margin_direction_cosine=cosine(a,b),
            margin_to_ce_norm_ratio=float(np.linalg.norm(b)/np.linalg.norm(a)),
            best_scalar_projection=scale,unexplained_margin_displacement_fraction=float(np.dot(residual,residual)/np.dot(b,b)),
            measured_only_geometry=True,counterfactual_QPS=None))
dump(O/'results/gradient_diagnostics.json',dict(status='PASS',scope='Post-hoc fit-only; gradient projections are not causal performance attribution',records=records,geometry=geometry,optimizer_steps=0,NSG_calls=0))
print('gradient diagnostics complete',flush=True)

from train import *
import itertools

torch.manual_seed(29)
z = torch.randn(5, 8, requires_grad=True)
comb = torch.tensor(list(itertools.combinations(range(8), 3)))
t = comb[torch.tensor([1, 8, 19, 40, 55])]
all_scores = z[:, comb].sum(2)
ce_ref = torch.logsumexp(all_scores, 1) - z.gather(1, t).sum(1)
miss = 3-(comb[None,:,:,None] == t[:,None,None,:]).any(3).sum(2)
margin_ref = (all_scores+.1*miss).max(1).values-z.gather(1,t).sum(1)
for kind, ref in [('ce',ce_ref),('margin',margin_ref)]:
    observed = supervised_loss(z,t,kind)
    assert torch.allclose(observed,ref,atol=1e-12,rtol=1e-12)
    ga = torch.autograd.grad(observed.sum(),z,retain_graph=True)[0]
    gb = torch.autograd.grad(ref.sum(),z,retain_graph=True)[0]
    assert torch.allclose(ga,gb,atol=1e-12,rtol=1e-12)
    assert torch.allclose(ga.sum(1),torch.zeros(5),atol=1e-12)
    assert torch.autograd.gradcheck(lambda zz: supervised_loss(zz,t,kind),(z,))
    assert torch.allclose(supervised_loss(z+100,t,kind),observed,atol=1e-12,rtol=1e-12)
pred = z.topk(3,1).indices
missing = 3-(pred[:,:,None]==t[:,None,:]).any(2).sum(1)
assert (supervised_loss(z,t,'margin') >= .1*missing-1e-12).all()
good = torch.full((5,8),-1.)
good.scatter_(1,t,1.)
assert torch.allclose(supervised_loss(good,t,'margin'),torch.zeros(5))
bad = good.clone()
bad[0,t[0,0]]=-2.
assert supervised_loss(bad,t,'margin')[0]>.1
for val in [torch.randn(2,821)*100,torch.tensor([[1000.,-1000.,-900.,-800.]])]:
    val.requires_grad_(True)
    tt=torch.tensor([[0,1,2]]).repeat(len(val),1)
    for kind in ['ce','margin']:
        loss=supervised_loss(val,tt,kind).sum()
        grad=torch.autograd.grad(loss,val,retain_graph=True)[0]
        assert torch.isfinite(loss) and torch.isfinite(grad).all()
p=nn.functional.normalize(torch.randn(11,7),dim=1)
assert torch.allclose(Transform(p)(),p,atol=1e-14)
dump(O/'reviews/objective_tests.json',dict(status='PASS',full_enumeration=True,gradient_reference=True,
    finite_difference=True,shift_invariance=True,teacher_member_error_upper_bound=True,
    zero_margin_condition=True,extreme_values_finite=True,zero_residual_identity=True))
print('objective tests PASS')

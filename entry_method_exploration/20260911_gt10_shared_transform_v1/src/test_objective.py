from train import *
import itertools
torch.manual_seed(721)
z=torch.randn(4,8,requires_grad=True);comb=torch.tensor(list(itertools.combinations(range(8),3)))
reference=torch.logsumexp(z[:,comb].sum(2),1);current=logz3(z)
assert torch.allclose(reference,current,atol=1e-12,rtol=1e-12)
ga=torch.autograd.grad(current.sum(),z,retain_graph=True)[0];gb=torch.autograd.grad(reference.sum(),z)[0]
assert torch.allclose(ga,gb,atol=1e-12,rtol=1e-12);assert torch.allclose(ga.sum(1),torch.full((4,),3.))
assert torch.allclose(logz3(z+123),current+369,atol=1e-12,rtol=1e-12)
assert torch.equal(torch.sort(comb[z[:,comb].sum(2).argmax(1)],1).values,torch.sort(z.topk(3,1).indices,1).values)
assert torch.autograd.gradcheck(logz3,(torch.randn(2,5,requires_grad=True),))
for v in [torch.tensor([[1000.,-1000.,-900.,-800.]],requires_grad=True),torch.randn(3,821,requires_grad=True)*20]:
 l=logz3(v).sum();g=torch.autograd.grad(l,v)[0];assert torch.isfinite(l) and torch.isfinite(g).all()
p=nn.functional.normalize(torch.randn(11,7),dim=1)
for f in ['linear','mlp','free']:
 m=Transform(p,f);assert torch.allclose(m(),p,atol=1e-14);assert torch.allclose(m().norm(dim=1),torch.ones(11),atol=1e-14)
dump(O/'reviews/objective_tests.json',dict(status='PASS',enumeration_normalizer=True,enumeration_gradient=True,finite_difference_gradient=True,shift_invariance=True,MAP_top3=True,extreme_logits_finite=True,zero_residual_identity=True))
print('objective tests PASS')

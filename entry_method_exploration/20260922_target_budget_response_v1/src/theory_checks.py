"""Numerical witnesses for the declared budget-transfer argument."""
from common import *

assert not (RUN/'reviews/theory_checks.json').exists()
rng = np.random.default_rng(20260922)
checks = 0
for actions in [2,7,100]:
    low = rng.random((1000,actions))
    high = rng.random((1000,actions))
    low -= low[:,:1]
    high -= high[:,:1]
    selected = low.argmax(1)
    drift = np.max(np.abs(high-low),axis=1)
    regret = high.max(1)-high[np.arange(1000),selected]
    assert np.all(regret <= 2*drift+1e-12)
    any_action = rng.integers(actions,size=1000)
    old_regret = low.max(1)-low[np.arange(1000),any_action]
    new_regret = high.max(1)-high[np.arange(1000),any_action]
    assert np.all(new_regret <= old_regret+2*drift+1e-12)
    checks += 2000
low = np.array([.2,.4])
high = np.array([.9,.8])
assert np.all(high>=low) and low.argmax()!=high.argmax()
dump(RUN/'reviews/theory_checks.json',dict(status='PASS',synthetic_inequality_checks=checks,
    nondecreasing_response_preference_reversal=dict(low=low.tolist(),high=high.tolist(),
        low_choice=int(low.argmax()),high_choice=int(high.argmax())),
    scope='abstract response table, not a new native graph counterexample',
    source=identity(Path(__file__))))
dump(RUN/'reviews/pre_response_information_design.json',dict(created_unix=time.time(),
    files=[identity(RUN/p) for p in ['protocol.md','theory.md','src/information.py']],
    response_analysis_exists=(RUN/'analysis/response.json').exists()))
print('PASS: 6000 transfer inequalities and monotone-response preference reversal')

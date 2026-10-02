from common import *

# The original prepare.py is frozen with the training provenance. Keep its bytes.
# This explicit supplemental check records the actual E28 additional-manifest name.
# The same checks were first executed inline before the first E29 search.
items=read(E28/'reviews/protected_additional_before.json')
for item in items:assert identity(item['path'])==item
destination=O/'reviews/protected_additional_before.json'
if destination.exists():
    assert read(destination)==items
else:
    dump(destination,items)
preflight=O/'reviews/evaluation_preflight.json'
if preflight.exists():
    assert read(preflight)['status']=='PASS'
else:
    dump(preflight,dict(status='PASS',additional_old_assets=len(items),
        formal_cpu=15,formal_threads=1,provenance='E28 additional manifest explicitly checked before queries'))
print('additional input protection PASS',flush=True)

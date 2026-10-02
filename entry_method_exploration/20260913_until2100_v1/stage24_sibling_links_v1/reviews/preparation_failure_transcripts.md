# E83 preparation failures, preserved without reexecution

First original tool session21302 exited1 (supervisor tool44), src/prepare.py line41 -> common.freeze -> identity -> sha -> Path.open:

```
IsADirectoryError: [Errno 21] Is a directory: '/data/netg/ACSG/entry_method_exploration/20260913_until2100_v1/stage24_sibling_links_v1/src/__pycache__'
```

No graph installation or ANN had happened. Existing model.json and additions.json plans retained. Original source remains.

Second original tool session79879 exited1 (supervisor tool45), src/resume_prepare.py line57 -> dump(results/construction.json) -> json.dumps(allow_nan=False):

```
TypeError: Object of type int64 is not JSON serializable
```

All four physical graphs and query configs had already been written; all graph/byte checks had passed in that execution. No ANN. Existing graphs retained and independently checked by finalize_prepare.py, without reinstall. Lost in-memory first/second preparation and per-install timers remain unknown. These are terminal exception excerpts, not recreated full stack transcripts. Full original tool outputs remain in session record.

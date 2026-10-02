# Remote publication of the 2026-10-02 snapshot

The user separately authorized publication after local snapshot commit
96cf05d5410cf51272048cd1f90b4bb194e23c62. The snapshot README describes
the preceding local-only task; this publication is its authorized follow-up.

This branch uses the existing remote research commit
6e1134fbab1dba4971f2a361b528df1f44242db0 as its parent, rather than the
local main history, which contains historical multi-GB dataset blobs.
All 22345 manifest files, the three administrative self-excluded records,
and the upstream Faiss gitlink are copied with the same blob IDs and modes.
Large local data and historical build content are not included in this tree.
The original local snapshot commit and main are preserved.

No experiments, training, graph construction, or default changes occurred.

# Invalid raw-IP staging artifacts

The files without `.unit` / `.unit_ip` in their names were generated during
the first LAION staging attempt and are retained only for provenance. They
must not be referenced by `settings.json`, a manifest, an NSG, or an
evaluation.

Evidence: exact raw-IP search on the complete 10,004,480-row base reproduced
the public top-100 GT at only 0.994375 set recall for the first 32 queries;
raw L2 reached 0.9909375. Explicitly L2-normalizing every base and query row
before IP search reached exactly 1.0. Therefore the authoritative artifact
version is `roargraph-laion10m-unit-ip-acsg-v1`.

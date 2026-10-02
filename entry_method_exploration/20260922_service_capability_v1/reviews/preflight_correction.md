# Pre-training determinism correction

The first preflight failed `array_equal(rep['centers'], other['centers'])` when
rebuilding features after changing only outer-query labels. All deployable
feature arrays checked before centers were bit-identical, but threaded KMeans
reductions are not guaranteed bitwise repeatable. No model training or outer
policy evaluation had started. Original features.py is retained alongside this
note. PCA/KMeans fitting now uses threadpool_limits(1), making the representation
construction reproducible while retaining the locked statistical algorithm,
seed, roles and hyperparameters. The same strict equality test is rerun; its
result is recorded in preflight.json. This is not an outcome-dependent retune.

Dependency setup initially failed because the inherited pip index used an
untrusted HTTP mirror. The second attempt used HTTPS pypi.org. TabM 0.0.3 and its
mandatory rtdl_num_embeddings 0.0.12 import dependency were installed with
--no-deps into this version only. The original virtual environment was not
upgraded. No numeric feature embeddings are used by the control.

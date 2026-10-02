from common import *
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

def representation(data, roles, fold):
    support = np.asarray(roles['support'])
    fitting = np.asarray(roles['fit'])
    tr = np.r_[support, fitting]
    q = unit(data['q'].astype('f8'))
    pca = PCA(n_components=32, svd_solver='full').fit(q[tr])
    km = KMeans(n_clusters=16, n_init=1, max_iter=50, random_state=20260922 + fold).fit(q[support])
    cluster = km.predict(q)
    utility, dr, dt, tref = targets(data, support)
    response = np.concatenate([dr[:, 1:], dt[:, 1:]], axis=-1)
    mean = response[support].mean(0)
    cluster_response = np.stack([(response[support][cluster[support] == k].sum(0) + 16 * mean) /
                                ((cluster[support] == k).sum() + 16) for k in range(16)])
    capability = (cluster_response - mean).transpose(1, 0, 2).reshape(len(data['hubs']), -1)
    hv, pv = unit(data['hv'].astype('f8')), unit(data['profiles'].astype('f8'))
    geom = np.concatenate([pca.transform(hv), pca.transform(pv), mean], axis=1)
    bank, hmean, hscale = standardize(np.c_[geom, capability])
    xq, qmean, qscale = standardize(q, tr)
    cosine = np.stack([q @ hv.T, q @ pv.T], -1).astype('f4')
    prior = (mean[:, :2] - 0.1 * mean[:, 2:]).astype('f4')
    cluster_scores = (cluster_response[:, :, :2] - 0.1 * cluster_response[:, :, 2:])[cluster].astype('f4')
    return dict(q=xq, bank=bank, cosine=cosine, prior=prior, utility=utility,
                dr=dr, dt=dt, tref=tref, cluster=cluster, cluster_scores=cluster_scores,
                cluster_counts=np.bincount(cluster[support], minlength=16),
                raw_mean=mean, raw_capability=capability, qmean=qmean, qscale=qscale,
                hmean=hmean, hscale=hscale, pca_mean=pca.mean_, pca_components=pca.components_,
                centers=km.cluster_centers_)

def pair_matrix(rep, rows):
    h = len(rep['bank'])
    return np.concatenate([np.repeat(rep['q'][rows], h, axis=0),
                           np.tile(rep['bank'], (len(rows), 1)),
                           rep['cosine'][rows].reshape(-1, 2)], axis=1)

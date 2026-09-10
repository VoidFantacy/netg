import sys
import numpy as np
import scipy
from scipy.sparse import issparse, csr_matrix
from typing import Tuple, Union
from numpy.typing import NDArray
from sklearn.svm import LinearSVC, SVC
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.preprocessing import StandardScaler

from .base import Model

class NodeLinearModel(Model):
    def __init__(self, **kwargs):
        self.w = None
        self.b = None
        self.dead = False
        self.initialized = False
        self.regularization = None
        self.scaler = None

    def init_params(self, X:Union[NDArray[np.float64], csr_matrix], y:NDArray, init_type:str):
        self.initialized = True
        if init_type == 'rnd_init':
            self.__rnd_init(X)
        elif init_type == 'median_split':
            self.__median_init(X)
        elif init_type == "kmeans":
            self.__kmeans_init(X)
        else:
            raise ValueError("Decision node initialization is not supported")

    def __kmeans_init(self, X):
        kmeans = KMeans(n_clusters=2, max_iter=500, n_init=20)
        kmeans.fit(X)
        centroid1, centroid2 = kmeans.cluster_centers_
        w = centroid2 - centroid1
        midpoint = (centroid1 + centroid2) / 2
        b = -1 * np.dot(w, midpoint)
        self.w = csr_matrix(w.reshape(1, -1)) if issparse(X) else w.reshape(1, -1)
        self.b = b.reshape(1,)

    def __median_init(self, X):
        w_init = np.random.uniform(low=-1, high=1, size=(1, X.shape[1]))
        w_init = csr_matrix(w_init)
        w_init = w_init / scipy.sparse.linalg.norm(w_init, 'fro')
        X_pr_coef = X @ w_init.T
        self.w = w_init
        if issparse(X_pr_coef):
            X_pr_coef = X_pr_coef.toarray().ravel()
        else:
            self.w = self.w.toarray()
        bias = np.median(X_pr_coef, axis=0)
        self.b = -np.array([float(bias)])

    def __rnd_init(self, X:Union[NDArray[np.float64], csr_matrix]):
        w_uni = np.random.uniform(low=-1, high=1, size=(1, X.shape[1]))
        self.w = w_uni / np.linalg.norm(w_uni, ord=2)
        if issparse(X):
            self.w = csr_matrix(self.w)
        self.b = np.zeros((1,))
    
    def set_w(self, w:Union[NDArray[np.float64], csr_matrix]):
        self.w = w

    def set_b(self, b: NDArray[np.float64]):
        self.b = b
    
    def get_params(self):
        return (self.w, self.b)
    
    def set_params(self, param_tuple):
        # expects tuple of two elements where first is weight, second is bias      
        assert param_tuple[0].ndim == 2 and param_tuple[1].ndim == 1 and isinstance(param_tuple[0], (np.ndarray, csr_matrix)), f"param[0] should be weight of shape (1, D), param[1] should be bias of shape (1,1)"
        self.w = param_tuple[0]
        self.b = param_tuple[1]

    def predict(self, X:Union[NDArray[np.float64], csr_matrix]) -> NDArray[np.int64]:
        if self.scaler:
            X = self.scaler.transform(X)
        scores = X @ self.w.T + self.b
        scores = np.array(scores).ravel() 
        return (scores >= 0).astype(np.int64)
    
    def _calc_regularization(self, C):
        if self.dead:
            return 0
        if issparse(self.w):
            return 1/C * abs(self.w).sum()
        else:
            return 1/C * np.linalg.norm(self.w.ravel(), ord=1)

    def train(self, X:Union[NDArray[np.float64], csr_matrix], y:NDArray[np.int64], C:float, sample_weight=None, **kwargs):
        assert isinstance(y, np.ndarray) and y.ndim == 1, "y must be 1D"
        
        penalty = kwargs.get('penalty', 'l1')
        loss = kwargs.get('loss', 'squared_hinge')
        dual = kwargs.get('dual', False)
        tol = kwargs.get('tol', 1e-4)
        max_iter = kwargs.get('max_iter', 100)
        solver = kwargs.get('solver', 'liblinear')
        model_type = kwargs.get('model', 'logistic')
        R_i = kwargs.get('R_i', 1)
        alpha = kwargs.get('alpha', 0)
        scale = kwargs.get('scale', False)
            
        if scale:
            self.scaler = StandardScaler()
            X = self.scaler.fit_transform(X)

        assert R_i > 0, "R_i should be > 0"
        if alpha is not None:
            C = C / (R_i**alpha)

        self.dead = False

        if len(y) == 0 or np.all(y == y[0]):
            self.dead = True
            self.w = csr_matrix((1, X.shape[1]), dtype=np.float64) if issparse(X) else np.zeros((1, X.shape[1]), dtype=np.float64)
            self.b = np.array([[1.0]]) if (len(y) == 0 or y[0] > 0) else np.array([[-1.0]])
            self.regularization = self._calc_regularization(C)
            return
        
        if model_type == 'logistic':
            lin_classifier = LogisticRegression(
                penalty=penalty, dual=dual, C=C, tol=tol, 
                warm_start=False, max_iter=max_iter, solver=solver, n_jobs=1
            )   
        elif model_type == 'svc':
            lin_classifier = LinearSVC(
                loss=loss, penalty=penalty, dual=dual, C=C, 
                tol=tol, max_iter=max_iter, verbose=0
            )
        else:
            raise ValueError("Model type not supported")
        
        lin_classifier.fit(X, y, sample_weight=sample_weight)
        
        if issparse(X):
            self.w = csr_matrix(lin_classifier.coef_)
            count_nnz = self.w.nnz
        else:
            self.w = np.array(lin_classifier.coef_)
            count_nnz = np.count_nonzero(self.w)
            
        self.b = lin_classifier.intercept_
        if count_nnz == 0:
            self.dead = True
        
        self.regularization = self._calc_regularization(C)

    def param_count(self) -> Tuple[np.int64, np.int64]:
        if issparse(self.w):
            return self.w.shape[0] * self.w.shape[1], self.w.nnz
        return self.w.shape[0] * self.w.shape[1], np.count_nonzero(self.w)
    
    def get_weight_metric(self):
        return self.regularization if self.regularization is not None else 0.0


class NodeUnivariateModel(Model):
    def __init__(self, **kwargs):
        self.feat_idx = None
        self.b = None
        self.dead = False
        self.initialized = False
        self.regularization = None

    def init_params(self, X:Union[NDArray[np.float64], csr_matrix], y:NDArray, init_type: str):
        self.initialized = True
        if init_type == "rnd_init":
            self.feat_idx = np.random.randint(low=0, high=X.shape[1])
            col = X[:, self.feat_idx].toarray().ravel() if issparse(X) else X[:, self.feat_idx]
            unique_vals = list(set(col))
            # Prevent ValueError if selected feature is completely uniform
            if len(unique_vals) >= 2:
                self.b = np.random.choice(unique_vals, replace=False, size=2).mean()
            else:
                self.b = unique_vals[0] if unique_vals else 0.0
        else:
            raise ValueError("Decision node initialization is not supported")

    def set_feat_idx(self, feat_idx: int):
        self.feat_idx = feat_idx
    
    def set_bias(self, b: float):
        self.b = b
        
    def get_params(self):
        return (self.feat_idx, self.b)
    
    def set_params(self, param_tuple):
        # expects tuple of two elements where first is weight, second is bias
        assert isinstance(param_tuple[0], int) and isinstance(param_tuple[1], float), "param[0] should be feat_idx of type int, param[1] should be bias of type float"
        self.feat_idx = param_tuple[0]
        self.b = param_tuple[1]

    def predict(self, X:Union[NDArray[np.float64], csr_matrix]) -> NDArray[np.int64]:
        if self.feat_idx is None:
            return np.ones(X.shape[0]).astype(int) if self.b > 0 else np.zeros(X.shape[0]).astype(np.int64)
        col = X[:, self.feat_idx].toarray().ravel() if issparse(X) else X[:, self.feat_idx]
        return (col >= self.b).astype(np.int64)

    def train(self, X:Union[NDArray[np.float64], csr_matrix], y:NDArray[np.int64], C: float, sample_weight:NDArray[np.float64], **kwargs):
        assert isinstance(y, np.ndarray) and y.ndim == 1, "y must be 1D"
        """
            X:NDArray[np.float64] - training samples
            y:NDArray - targets
            C:float - regularization coefficient
            sample_weight:NDArray - NDArray or None, weights of each sample
        """
        
        if len(y) == 0:
            self.feat_idx = None
            self.b = 1
            self.dead = True
            self.regularization = 0
            return
        
        b_index, b_value, b_score = 0, 0, sys.maxsize
        
        if issparse(X):
            total_w0 = np.sum(sample_weight[y == 0])
            total_w1 = np.sum(sample_weight[y == 1])
            
            # Calculate baseline minimum score
            if total_w1 <= total_w0:
                childdir = 'l'
                minallscore = total_w1
            else:
                childdir = 'r'
                minallscore = total_w0

            if minallscore <= C:
                self.feat_idx = None
                self.b = -1.0 if childdir == 'l' else 1.0
                self.dead = True
                self.regularization = 0.0
                return

            X_csc = X.tocsc()
            
            for index in range(X_csc.shape[1]):
                ptr_start = X_csc.indptr[index]
                ptr_end = X_csc.indptr[index+1]
                
                if ptr_start == ptr_end:
                    continue
                    
                data_j = X_csc.data[ptr_start:ptr_end]
                rows_j = X_csc.indices[ptr_start:ptr_end]
                y_j = y[rows_j]
                w_j = sample_weight[rows_j]

                val_dict = {}
                
                # Calculate the exact weight of the implicit 0.0 values
                nz_w0 = np.sum(w_j[y_j == 0])
                nz_w1 = np.sum(w_j[y_j == 1])
                z_w0 = total_w0 - nz_w0
                z_w1 = total_w1 - nz_w1
                
                if z_w0 > 0 or z_w1 > 0:
                    val_dict[0.0] = [z_w0, z_w1]

                for v, lbl, w in zip(data_j, y_j, w_j):
                    if v not in val_dict:
                        val_dict[v] = [0.0, 0.0]
                    val_dict[v][lbl] += w

                unique_vals = sorted(val_dict.keys())
                
                w_L_1 = 0.0
                w_R_0 = total_w0

                for i in range(len(unique_vals) - 1):
                    val = unique_vals[i]
                    w0, w1 = val_dict[val]

                    w_L_1 += w1
                    w_R_0 -= w0

                    curr_score = w_L_1 + w_R_0
                    s_value = float(unique_vals[i] + unique_vals[i+1]) / 2.0

                    if curr_score < b_score:
                        b_index, b_value, b_score = index, s_value, curr_score
        else:
            order = np.argsort(X, axis=0, kind='stable')
            minallscore = X.shape[0]
            
            for index in range(X.shape[1]):
                y_train, X_train = y[order[:, index]], X[order[:, index]]
                sample_weight_train = sample_weight[order[:, index]]
                
                if index == 0:
                    alllscore = np.sum(sample_weight[y == 1]) 
                    allrscore = np.sum(sample_weight) - alllscore 
                    if alllscore <= allrscore:
                        childdir = 'l'
                        minallscore = alllscore
                    else:
                        childdir = 'r'
                        minallscore = allrscore
                    if minallscore <= C:
                        self.feat_idx = None
                        self.b = -1 if childdir == 'l' else 1
                        self.dead = True
                        self.regularization = 0
                        return

                firstsplit = True
                prevj = 0
                for j in range(len(X_train) - 1):
                    if X_train[j, index] != X_train[j + 1, index]:
                        if firstsplit:
                            y_left, y_right = y_train[:j + 1], y_train[j + 1:]
                            w_left, w_right = sample_weight_train[:j + 1], sample_weight_train[j + 1:]
                            rscore = np.sum(w_right[y_right == 0])
                            alllscore = np.sum(w_left[y_left == 1])
                            firstsplit = False
                        else:
                            y_chunk = y_train[prevj + 1:j + 1]
                            w_chunk = sample_weight_train[prevj + 1:j + 1]
                            wrongs = np.sum(w_chunk[y_chunk == 1])
                            alllscore += wrongs
                            rscore -= np.sum(w_chunk[y_chunk == 0])

                        curr_score = alllscore + rscore
                        s_value = float(X_train[j, index] + X_train[j + 1, index]) / 2
                        prevj = j
                        if curr_score < b_score:
                            b_index, b_value, b_score = index, s_value, curr_score

        if b_score + C >= minallscore: 
            self.feat_idx = None
            self.dead = True
            self.b = -1 if childdir == 'l' else 1
            self.regularization = 0
        else:
            self.feat_idx = b_index
            self.b = b_value
            self.dead = False
            self.regularization = C
            

    def param_count(self):
        return 2, 2
        
    def get_weight_metric(self):
        if self.dead or self.regularization is None:
            return 0.0
        return self.regularization
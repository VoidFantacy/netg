import numpy as np
from typing import Tuple, Union
from numpy.typing import NDArray
from scipy.sparse import issparse, csr_matrix
from scipy.linalg import cho_factor, cho_solve
from scipy.spatial.distance import cdist
from scipy.sparse.linalg import LinearOperator, cg
from sklearn.svm import LinearSVC, SVC
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import rbf_kernel
from collections import defaultdict, namedtuple
from random import randint

from .base import Model

class LeafMajorityClassificationModel(Model): #uses one hot encoded input


    def __init__(self, **kwargs):
        self.proba_distr = None
        self.oneclass = False
        self.classes = None
        self.initialized = False
        self.regularization = None


    def predict(self, X:Union[NDArray[np.float64], csr_matrix])->NDArray[np.int64]:
        """
            predicts one-hot encoded class
        """
        y_idx = np.argmax(self.proba_distr)
        y_pred = np.zeros(len(self.proba_distr))
        y_pred[y_idx] = 1
        pred = np.tile(y_pred, (X.shape[0], 1))
        return pred
       

    def predict_proba(self, X:Union[NDArray[np.float64], csr_matrix])->NDArray[np.int64]:
        pred = np.tile(self.proba_distr, (X.shape[0], 1))
        return pred


    def set_proba_distr(self, distr:NDArray):
        assert len(distr)>1, "size of distr should be equal to number of classes (at least 2)"
        self.proba_distr = distr


    def init_params(self, X:Union[NDArray[np.float64], csr_matrix], y:NDArray[np.int64], init_type):
        self.initialized = True
        if init_type == "rnd_init":
            self.__rnd_init(y)
        else:
            raise ValueError("In the leaf nodes, initialization is not supported")


    def __rnd_init(self, y):
        assert isinstance(y, np.ndarray) or issparse(y), "In leaf nodes, make sure y is np.array or csr_matrix"
        if y.ndim == 1:
            cls = np.random.randint(low = 0, high = 2)
            self.proba_distr = np.zeros(2)
            self.proba_distr[cls] = 1
        else:
            lbl = randint(0, y.shape[1]-1)
            self.proba_distr = np.repeat(0, y.shape[1])
            self.proba_distr[lbl] = 1


    def train(self, X:Union[NDArray[np.float64], csr_matrix], y:NDArray[np.int64], **kwargs):
        assert isinstance(y, np.ndarray) or issparse(y), "In leaf nodes, make sure y is np.array or csr_matrix"
        if y.ndim == 1: # if 0vs1 binary classification
            y_train = np.zeros((y.shape[0], 2))
            y_train[np.arange(y.shape[0]), y] = 1
        else:
            y_train = y
        y_t = np.argmax(y_train, 1)
        classes_array = np.unique(y_t)
        if len(classes_array) == 1:
            self.oneclass = True
        else:
            self.oneclass = False
        self.classes = classes_array
        self.proba_distr = np.mean(y_train, axis = 0)
        self.regularization = 0


    def param_count(self):
        return 1,1
    
    def get_weight_metric(self):
        if self.regularization is None:
            return 0.0
        return self.regularization
    

class LeafKernelClassification(Model):


    def __init__(self, gamma, kernel = rbf_kernel, **kwargs):
        self.proba_distr = None
        self.classes = None
        self.w = None
        self.b = None
        self.initialized = False
        self.kernel = kernel
        self.sv = None
        self.scaler = None
        self.gamma = gamma
        self.top2_classes = None
        self.regularization = None


    def init_params(self, X:Union[NDArray[np.float64], csr_matrix], y:NDArray, init_type:str):
        self.initialized = True
        if init_type == 'rnd_init':
            self.__rnd_init(X, y)
        else:
            raise ValueError("Decision node initialization is not supported")


    def __rnd_init(self, X:Union[NDArray[np.float64], csr_matrix], y:NDArray):
        # w_uni = np.random.randn(1, X.shape[1])
        if issparse(X):
            n_elements = X.shape[0] * X.shape[1]
            mean_val = X.sum() / n_elements
            var = (X.power(2).sum() / n_elements) - (mean_val ** 2)
        else:
            var = X.var()
        if var < 1e-10: var = 1
        self.gamma = 1/(X.shape[1]*var)
        N = X.shape[0]
        num_support = max(1, int(N/4))
        support_indices = np.random.choice(N, num_support, replace=False)

        self.sv = X[support_indices]  # Support vectors
        w_uni = np.random.uniform(low=-1, high=1, size=(1, num_support))
        norm = np.linalg.norm(w_uni, ord=2)
        
        self.w = w_uni / (norm if norm > 0 else 1.0)
        self.classes = np.unique(y)
        self.top2_classes = self.classes[:2]
        
        if issparse(X):
            self.w = csr_matrix(self.w)
        self.b = np.zeros((1,))
    

    def set_w(self, w:Union[NDArray[np.float64], csr_matrix]):
        assert w.ndim == 2 and w.shape[0] == 1
        self.w = w


    def set_b(self, b: NDArray[np.float64]):
        assert b.shape == (1,1)
        self.b = b


    def predict(self, X:Union[NDArray[np.float64], csr_matrix])->NDArray[np.int64]:
        if len(self.classes) == 1:
            y_pred = np.zeros((X.shape[0], 3))
            y_pred[:,] = np.array([-1, self.classes[0], 1])
            return y_pred
        
        if self.scaler:
            X = self.scaler.transform(X)
        K_XS = self.kernel(X, self.sv, gamma = self.gamma)
        scores = K_XS @ self.w.T + self.b
        y_pred = np.zeros((scores.shape[0], len(self.top2_classes)+1))
        y_pred[:,:len(self.top2_classes)] = self.top2_classes
        y_pred[:,[len(self.top2_classes)]] = scores
        return y_pred


    def train(self, X:Union[NDArray[np.float64], csr_matrix], y:NDArray[np.int64], C:float, **kwargs):
        assert isinstance(y, np.ndarray) or issparse(y), "In leaf nodes, make sure y is np.array or csr_matrix"
        """
            X:NDArray[np.float64] - training samples
            y:NDArray - targets
            C:float - regularization coefficient
            sample_weight:NDArray - NDArray or None, weights of each sample
            tol:float=1e-4 - tol of classifier (def 1e-4)
            max_iter:int=100 - max iterations of classifier
        """
        tol = kwargs.get('tol', 1e-4)
        max_iter = kwargs.get('max_iter', -1)
        R_i = kwargs.get("R_i", 1)
        alpha = kwargs.get('alpha', 0)
        scale = kwargs.get('scale', False)
        self.gamma = kwargs['gamma']
            
        if self.gamma == 'scale':
            if issparse(X):
                n_elements = X.shape[0] * X.shape[1]
                mean_val = X.sum() / n_elements
                var = (X.power(2).sum() / n_elements) - (mean_val ** 2)
            else:
                var = X.var()
            self.gamma = 1 / (X.shape[1] * var) if var > 1e-10 else 1/X.shape[1]
            
        if scale:
            self.scaler = StandardScaler()
            X = self.scaler.fit_transform(X)

        assert R_i > 0, "R_i should be bigger than 1"
        C = C/(R_i**alpha)

        if y.ndim == 1: # if 0vs1 binary classification
            y_train = np.zeros((y.shape[0], 2))
            y_train[np.arange(y.shape[0]), y] = 1
            y = y_train
        y_label = np.argmax(y, axis = 1)
        
        self.proba_distr = np.mean(y, axis = 0)
        self.classes = np.arange(self.proba_distr.shape[0])[self.proba_distr > 0]

        if len(self.classes) == 1:
            self.top2_classes = self.classes
            if issparse(X):
                # self.w = csr_matrix((1, self.sv.shape[0]), dtype = np.float64)
                self.w = csr_matrix((1, 2), dtype = np.float64)
            else:
                # self.w = np.zeros((1, self.sv.shape[0]), dtype = np.float64)
                self.w = np.zeros((1, 2), dtype = np.float64)
            self.b = None
            self.regularization = 0
            return
        
        self.top2_classes = np.argsort(self.proba_distr)[-2:] #sort in increasing order, pick last 2 (highest count)
        self.top2_classes.sort() #SVC sorts classes, class[0] is -1 and class[1] is +1
        
        mask = np.logical_or(y_label == self.top2_classes[0], y_label == self.top2_classes[1])
        y = y_label[mask]
        X = X[mask]
        K_X = self.kernel(X, X, gamma = self.gamma)
        
        svc = SVC(
            C = C,
            kernel = 'precomputed',
            gamma = self.gamma,
            shrinking = True,
            probability=False,
            tol = tol,
            max_iter = max_iter,
            decision_function_shape = 'ovo')
        
        svc.fit(K_X, y)
        self.sv = X[svc.support_,:]
        self.w = csr_matrix(svc.dual_coef_) if issparse(X) else np.array(svc.dual_coef_)
        self.b = svc.intercept_
        
        K_sv = K_X[np.ix_(svc.support_, svc.support_)]
        w_dense = self.w.toarray() if issparse(self.w) else self.w
        self.regularization = 1/C * 0.5 * (w_dense @ K_sv @ w_dense.T)[0, 0]
        del K_X
        del K_sv
        return


    def param_count(self)->Tuple[np.int64, np.int64]:
        if issparse(self.w):
            return self.w.shape[0]*self.w.shape[1], self.w.nnz
        else:
            return self.w.shape[0]*self.w.shape[1], np.count_nonzero(self.w)
    
    
    def get_weight_metric(self):
        if not np.any(self.w.toarray() if issparse(self.w) else self.w) or self.regularization is None:
            return 0.0
        return self.regularization



class LeafMajorityRegressionModel(Model): #uses one hot encoded input


    def __init__(self, **kwargs):
        self.w = None
        self.proba_distr = None
        self.sparse_hist = False
        self.initialized = False
        self.regularization = None
        self.is_1d = False


    def predict(self, X:Union[NDArray[np.float64], csr_matrix])->Union[NDArray[np.float64], csr_matrix]:
        pred = np.tile(self.proba_distr, (X.shape[0], 1))
        if self.is_1d:
            pred = pred.ravel()
        if self.sparse_hist:
            return csr_matrix(pred)
        return pred


    def set_proba_distr(self, distr:Union[NDArray[np.float64], csr_matrix]):
        self.proba_distr = distr


    def init_params(self, X:Union[NDArray[np.float64], csr_matrix], y:NDArray[np.int64], init_type):
        self.initialized = True
        self.is_1d = isinstance(y, np.ndarray) and y.ndim == 1
        if init_type == "rnd_init":
            self.__rnd_init(y)
        else:
            raise ValueError("In the leaf nodes, initialization is not supported")


    def __rnd_init(self, y):
        assert isinstance(y, np.ndarray) or issparse(y), "In leaf nodes, make sure y is np.array or csr_matrix"
        #not clear how to initialize
        indx = np.random.choice(y.shape[0])
        if self.is_1d:
            self.proba_distr = y[indx]
        else:
            self.proba_distr = np.asarray(y[indx].todense()).ravel() if issparse(y) else y[indx]


    def train(self, X:Union[NDArray[np.float64], csr_matrix], y:Union[NDArray[np.float64], csr_matrix], **kwargs):
        assert isinstance(y, np.ndarray) or issparse(y), "In leaf nodes, make sure y is np.array or csr_matrix"
        self.is_1d = isinstance(y, np.ndarray) and y.ndim == 1
        if self.is_1d:
            y = y.reshape(-1, 1)
        assert y.ndim==2, "In leaf nodes, y.ndim must be 2"
        # y_train = np.array(y)
        if issparse(y):
            self.sparse_hist = True
            self.proba_distr = np.asarray(y.mean(axis = 0)).ravel()
        else:
            self.sparse_hist = False
            self.proba_distr = np.mean(y, axis = 0)
        self.regularization = 0


    def param_count(self):
        distr = np.atleast_1d(self.proba_distr)
        return len(distr), np.count_nonzero(distr)

    
    def get_weight_metric(self):
        if self.regularization is None:
            return 0.0
        return self.regularization
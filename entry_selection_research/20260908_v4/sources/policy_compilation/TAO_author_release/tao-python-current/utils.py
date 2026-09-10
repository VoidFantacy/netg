import numpy as np
import tao_tree
from scipy.spatial.distance import cdist
import models


def mse_loss(y_true, y_pred):
    assert y_true.ndim == y_pred.ndim, "Dimension of y_true and y_pred must match"
    squared_errors = (y_true - y_pred)**2
    if y_true.ndim == 2:
        dim = y_true.shape[1]
        return squared_errors.sum(axis=1) / dim
    else:
        return squared_errors

def misclass_loss(y_true, y_pred):
    assert y_true.ndim == y_pred.ndim, "Dimension of y_true and y_pred must match"
    if y_true.ndim > 1:
        return (y_true.argmax(axis = 1)!=y_pred.argmax(axis = 1)).astype(int)
    return (y_true != y_pred).astype(int)

def calculate_loss(node, X:np.ndarray, y:np.ndarray, loss):
    dim = y.shape[1] if y.ndim > 1 else 1
    if loss.__name__ == "hinge_loss":
        dim = 3
    y_pred = tao_tree.predict(X=X, tree_node=node, target_dim=dim)
    return loss(y,y_pred)


def hinge_loss(y_true, y_pred):

    ### designed for kernel leaves tree ###
    # L(y, f(x)) = max(0, 1 - y*f(x))
    # y_true should be one-hot encoded
    # y_pred (n_samples, 3) -> [class_-1, class_1, f(x)], if class_-1 == -1, then only 1 class is present in the leaf

    eps = 3 #try to chane this
    loss_value = eps*np.ones(y_true.shape[0])
    y_true_label = np.argmax(y_true, axis = 1) #from one-hot to labels
    mask_present = np.any(y_true_label.reshape(-1,1) == y_pred[:,:2], axis = 1) # samples with classes present in the leave kernel svms
    y_true_label[y_true_label == y_pred[:,0]] = -1
    y_true_label[y_true_label == y_pred[:,1]] = 1
    ls = 1 - y_true_label[mask_present]*y_pred[mask_present][:,2]
    ls[ls<0] = 0
    loss_value[mask_present] = ls

    return loss_value

def calculate_err_kernel_leaves(dtree, X, y):
    y_label = np.argmax(y, axis = 1)
    # if isinstance(dtree.get_rbfs[dtree.get_depth][0].get_model, models.LeafKernelClassificationOneVSOne):
    #     y_pred = tree.predict(X=X, tree_node=dtree.get_root, target_dim=y.shape[1])
    #     y_pred_label = y_pred.argmax(axis = 1)
    #     return (y_pred_label != y_label).astype(int)
    y_pred = tao_tree.predict(X=X, tree_node=dtree.get_root, target_dim=3)
    y_pred_label = np.where(y_pred[:, 2] >= 0, y_pred[:, 1], y_pred[:, 0])
    return (y_pred_label != y_label).astype(int)


def compute_rbf_kernel(X, gamma):
    K = cdist(X, X, metric='sqeuclidean')
    K *= -gamma
    np.exp(K, out=K)
    return K
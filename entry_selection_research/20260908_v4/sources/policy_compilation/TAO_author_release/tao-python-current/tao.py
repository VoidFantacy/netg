import numpy as np
import tao_tree
import utils
from tempfile import mkdtemp
import joblib
from joblib import Parallel, delayed
import pickle
from typing import Dict
import os
import copy
from time import perf_counter
import gc


def tao_main(X_train, y_train, X_test, y_test,
            dtree,
            loss,
            node_args,
            leaf_args,
            n_cpus=1,
            sequential=None,
            max_iter=30,
            tol=1e-6,
            wait_iter = 3,
            postprocess=True,
            tree_logg_folder=None,
            logg_progress=False,
            strict_update=False):
    """
    Parameters
    ----------
    X_train : train set in np.float64 or sparse format
    y_train : target data of the train set
    X_test : test set in np.float64 or sparse format
    y_test : target data of the test set
    dtree : object of type tree.Tree
    loss : loss function from utils
    node_args : dict with node hyper parameters
    leaf_args : dict with leaf hyper parameters
    n_cpus : number of cpus for parallelization (default 1)
    max_iter : maximum number of iterations (default 30)
    tol : tolerance of the algorithm (defaul 1e-6) when train loss drops below it for wait_iter iterations algortihm stops (default 1e-6)
    wait_iter : number of iterations with loss difference between two consecutive iterations below tol after which algorithm stops (default 3)
    postprocess : if True tree is pruned after algorithm is finished (default True)
    tree_logg_folder : if not None tree is save after each tao iteration in pickle format (default None)
    logg_progress : if True logg every iteration of TAO
    strict_update : if True, a decision node update is rejected if it does not improve the exact loss (default False)
    """
    if sequential is None:
        sequential = ()
    assert isinstance(sequential, tuple), "sequential is a tuple of levels to run sequentially"
    assert wait_iter>0, "wait_iter must be bigger than 0"
    if tree_logg_folder is not None:
        assert os.path.isdir(tree_logg_folder), "tree_logg_folder does not exist"
    L = utils.calculate_loss(dtree.get_root, X_train, y_train, loss)
    # L = np.full(X_train.shape[0], np.inf)
    assert L.shape[0] == X_train.shape[0], "Dimension of L and X_train must match"

    X_train_ref = X_train
    if n_cpus > 1 and X_train.shape[0] > 1e6:
        filename = os.path.join(mkdtemp(), 'X_train.mmap')
        joblib.dump(X_train, filename)
        X_train_ref = joblib.load(filename, mmap_mode='r')
        
    tao_iter = 0
    hold_val = 0
    train_loss, test_loss, obj_value = [], [], []

    if tree_logg_folder is not None and logg_progress:
        pickle.dump(dtree, open(f"{tree_logg_folder}/dtree_{tao_iter}.pkl", "wb"))
    
    tr_loss = L.sum()/L.shape[0]
    ts_loss = utils.calculate_loss(dtree.get_root, X_test, y_test, loss).sum()/X_test.shape[0]
    # ts_err = np.full(X_test.shape[0], np.inf).sum()/X_test.shape[0]
    print("\t\t\tInitial train loss: ", tr_loss)
    print("\t\t\tInitial test loss: ", ts_loss)
    train_loss.append(tr_loss)
    test_loss.append(ts_loss)
    
    train_time_reduced_set_arr = []
    train_time_model_arr = []
    train_time_leaves_arr = []
    
    prev_leaf_indexes = [None] * len(dtree.get_rbfs[dtree.get_depth])

    while tao_iter < max_iter and hold_val < wait_iter:
        DEPTH = dtree.get_depth
        train_time_reduced_set = 0
        train_time_dmodel = 0
        train_time_l = 0
        dnode_weight_reg = 0
        leaf_weight_reg = 0
        print("\n\t\t\tTAO iteration: ", tao_iter)
        for cur_depth in range(DEPTH, 0, -1):
            print(" \t\t\tTAO Depth: ", cur_depth)
            if cur_depth == DEPTH: # train over leaves
                tasks = []
                for node_i, tree_leaf in enumerate(dtree.get_rbfs[cur_depth]):
                    
                    curr_indexes = tree_leaf.get_indexes
                    prev_indexes = prev_leaf_indexes[node_i]
                    
                    # Skip Condition: If the length and elements are identical, skip training
                    if prev_indexes is not None and len(curr_indexes) == len(prev_indexes) and np.all(curr_indexes == prev_indexes):
                        leaf_weight_reg += tree_leaf.get_model.get_weight_metric()
                        continue
                    
                    # 2. Update the cache for the next iteration
                    prev_leaf_indexes[node_i] = curr_indexes.copy()
                    
                    if len(curr_indexes) > 0:
                        # leaf_args["R_i"] = len(curr_indexes)
                        if n_cpus > 1 and cur_depth not in sequential:
                            tasks.append(
                                delayed(train_leaf_joblib)(
                                    tree_leaf.get_model,
                                    X_train_ref,
                                    y_train,
                                    curr_indexes,
                                    leaf_args,
                                    loss,
                                    node_i
                                )
                            )
                        else:
                            start = perf_counter()
                            train_leaf(leaf_model = tree_leaf.get_model,
                                        X_train = X_train,
                                        y_train = y_train,
                                        idxs = curr_indexes, 
                                        leaf_args = leaf_args,
                                        loss_fn = loss,
                                        L = L)
                            end = perf_counter()
                            train_time_l += end - start
                            leaf_weight_reg += tree_leaf.get_model.get_weight_metric()
                if n_cpus > 1:
                    results = Parallel(n_jobs=n_cpus, prefer="processes")(tasks)
                    for res in results:
                        if res is None: continue
                        joblib_model, idxs, l_val, node_idx = res
                        dtree.get_rbfs[cur_depth][node_idx].set_model(joblib_model)
                        L[idxs] = l_val
                        leaf_weight_reg += joblib_model.get_weight_metric()


            else: # train over internal nodes
                tasks = []
                for node_i, tree_node in enumerate(dtree.get_rbfs[cur_depth]):
                    if len(tree_node.get_indexes)>0:
                        # node_args["R_i"] = len(tree_node.get_indexes)
                        if n_cpus > 1 and cur_depth not in sequential:
                            tasks.append(
                                delayed(train_decision_node_joblib)(
                                    tree_node,
                                    X_train_ref,
                                    y_train,
                                    node_args,
                                    loss,
                                    L,
                                    node_i,
                                    strict_update,
                                    tao_iter
                                )
                            )
                        else:
                            time_reduced_set, time_model_train = train_decision_node(tree_node = tree_node,
                                                X_train = X_train,
                                                y_train = y_train,
                                                node_args = node_args,
                                                loss_fn = loss,
                                                L = L,
                                                strict_update = strict_update,
                                                tao_iter = tao_iter)
                            train_time_reduced_set += time_reduced_set
                            train_time_dmodel += time_model_train
                            dnode_weight_reg += tree_node.get_model.get_weight_metric()

                if n_cpus > 1:
                    results = Parallel(n_jobs=n_cpus, prefer="processes")(tasks)
                    for res in results:
                        if res is None: continue
                        joblib_model, left_change, right_change, node_idx = res
                        dtree.get_rbfs[cur_depth][node_idx].set_model(joblib_model)
                        if left_change is not None:
                            left_idxs_care, left_loss_val = left_change
                            L[left_idxs_care] = left_loss_val
                        if right_change is not None:
                            right_idxs_care, right_loss_val = right_change
                            L[right_idxs_care] = right_loss_val
                        dnode_weight_reg += joblib_model.get_weight_metric()
            # gc.collect()

        train_time_leaves_arr.append(train_time_l)
        train_time_reduced_set_arr.append(train_time_reduced_set)
        train_time_model_arr.append(train_time_dmodel)
        # book-keeping: identify which points belongs to which node
        tao_tree.update_indexes(tnode = dtree.get_root, 
                            X_train = X_train,
                            idxs = np.arange(0, X_train.shape[0]),
                            isdead = False)      

        # calculate global loss and test/train accuracy for this iteration
        tr_loss = L.sum()/L.shape[0]
        ts_loss = utils.calculate_loss(dtree.get_root, X_test, y_test, loss).sum()/X_test.shape[0]
        train_loss.append(tr_loss)
        test_loss.append(ts_loss)
        obj_value.append(tr_loss*L.shape[0] + dnode_weight_reg + leaf_weight_reg)
        print("\t\t\tTrain loss value: ", tr_loss)
        print("\t\t\tTest loss value: ", ts_loss)
        if loss.__name__ == "hinge_loss":
            print("\t\t\tTrain error: ", utils.calculate_err_kernel_leaves(dtree, X_train, y_train).sum()/X_train.shape[0])
            print("\t\t\tTest error: ", utils.calculate_err_kernel_leaves(dtree, X_test, y_test).sum()/X_test.shape[0])
        # elif loss.__name__ != "misclass_loss":
        #     print("\t\t\tTrain error: ", utils.calculate_loss(dtree.get_root, X_train, y_train, utils.misclass_loss).sum()/X_train.shape[0])
        #     print("\t\t\tTest error: ", utils.calculate_loss(dtree.get_root, X_test, y_test, utils.misclass_loss).sum()/X_test.shape[0])
        
        tao_iter += 1
        if tree_logg_folder is not None and logg_progress:
            pickle.dump(dtree, open(f"{tree_logg_folder}/dtree_{tao_iter}.pkl", "wb"))
    
        loss_value_diff = abs(train_loss[-1]-train_loss[-2])
        if tol is not None and loss_value_diff < tol:
            hold_val += 1
        else:
            hold_val = 0

    if tree_logg_folder is not None:
        pickle.dump(dtree, open(f"{tree_logg_folder}/dtree_final.pkl", "wb"))

    if postprocess:
        # postprocessing remove dead nodes (weights are zero or no data at that node)
        dtree.set_root(tao_tree.remove_dead_nodes(dtree.get_root))
        new_depth = dtree.calculate_depth()
        dtree.set_depth(new_depth)
        dtree.upd_rbfs()
        tao_tree.update_indexes(tnode = dtree.get_root, 
                            X_train = X_train,
                            idxs = np.arange(0, X_train.shape[0]),
                            isdead = False)
        if tree_logg_folder is not None:
            pickle.dump(dtree, open(f"{tree_logg_folder}/dtree_final_pruned.pkl", "wb"))
    
    return train_loss[1:], test_loss[1:], obj_value, train_time_reduced_set_arr, train_time_model_arr, train_time_leaves_arr



def train_leaf_joblib(leaf_model, X_train:np.ndarray, y_train:np.ndarray, idxs:np.ndarray, leaf_args:Dict, loss_fn, node_idx: int):
    X_train_leaf, y_train_leaf = X_train[idxs], y_train[idxs]
    leaf_model.train(X_train_leaf, y_train_leaf, **leaf_args, R_i = len(idxs))
    y_pred = leaf_model.predict(X_train_leaf)
    loss_val = loss_fn(y_train_leaf, y_pred)
    # if loss_val.max() < 1e-5:
    #     loss_val *= 1e3
    return leaf_model, idxs, loss_val, node_idx



def train_leaf(leaf_model, X_train:np.ndarray, y_train:np.ndarray, idxs:np.ndarray, leaf_args:Dict, loss_fn, L:np.ndarray):
    X_train_leaf, y_train_leaf = X_train[idxs], y_train[idxs]
    leaf_model.train(X_train_leaf, y_train_leaf, **leaf_args, R_i = len(idxs))
    y_pred = leaf_model.predict(X_train_leaf)
    loss_val = loss_fn(y_train_leaf, y_pred)
    # if loss_val.max() < 1e-5:
    #     loss_val *= 1e3
    L[idxs] = loss_val
    return 



def train_decision_node_joblib(tree_node, X_train:np.ndarray, y_train:np.ndarray, node_args:Dict, loss_fn, L:np.ndarray, node_idx: int, strict_update:bool, tao_iter:int):
    target_dim = y_train.shape[1] if y_train.ndim>1 else 1
    if loss_fn.__name__ == "hinge_loss": target_dim = 3
    ####################### Generate pseudolabels #####################################
    right_change = None
    left_change = None
    left_idxs = tree_node.get_left.get_indexes
    right_idxs = tree_node.get_right.get_indexes
    dnode_idxs = np.concatenate((left_idxs, right_idxs)) #global indices
    if len(dnode_idxs) == 0:
        return tree_node.get_model, left_change, right_change, node_idx
    if np.all(L[dnode_idxs] == 0) and tao_iter>0:
        return tree_node.get_model, left_change, right_change, node_idx

    X_train_dnode = X_train[dnode_idxs]

    L_left_subtree = np.zeros(len(dnode_idxs), dtype = np.float64)
    L_right_subtree = np.zeros(len(dnode_idxs), dtype = np.float64)
    y_right_subtree_pred = None
    y_left_subtree_pred = None
    if len(left_idxs)>0:
        L_left_subtree[:len(left_idxs)] = L[left_idxs]
        # L_left_subtree[:len(left_idxs)] = L.get.remote(left_idxs)
        y_right_subtree_pred = tao_tree.predict(X_train[left_idxs], tree_node.get_right, target_dim=target_dim) #predictions of right subtree on samples from left subtree's reduced set
        L_right_subtree[:len(left_idxs)] = loss_fn(y_train[left_idxs], y_right_subtree_pred)
    if len(right_idxs)>0:
        L_right_subtree[-len(right_idxs):] = L[right_idxs]
        # L_right_subtree[-len(right_idxs):] = L.get.remote[right_idxs]
        y_left_subtree_pred = tao_tree.predict(X_train[right_idxs], tree_node.get_left, target_dim=target_dim) #predictions of left subtree on samples from right subtree's reduced set
        L_left_subtree[-len(right_idxs):] = loss_fn(y_train[right_idxs], y_left_subtree_pred)

    # dnode pred: 0 -> left, 1 -> right
    #L_---_subtree -> [-----left_idxs----]+[----right_idxs----]

    L_diff = L_left_subtree - L_right_subtree
    mask_care_points = (L_diff!=0)
    
    if np.any(mask_care_points)>0:
        L_diff_care = L_diff[mask_care_points]
        
        X_train_dnode_surr = X_train_dnode[mask_care_points]
        y_train_dnode_surr = (L_diff_care>0).astype(int)#if left subtree loss > right subtree loss -> label=1 (send to right subtree)
        
        sample_weights = np.abs(L_diff_care)
        # sample_weights = sample_weights/sample_weights.max() #mean can be used
        sample_weights = sample_weights/sample_weights.mean() #mean can be used
        
        idxs_care_points = dnode_idxs[mask_care_points]
        old_loss_sum = np.sum(L[idxs_care_points])
        # old_w = copy.deepcopy(tree_node.get_model.w)
        # old_b = copy.deepcopy(tree_node.get_model.b)
        old_params = copy.deepcopy(tree_node.get_model.get_params())
        # sample_weights = sample_weights/sample_weights.mean() #mean can be used

        # if np.any(np.isnan(sample_weights)):
        #     raise ValueError(f"Contains nan: {sample_weights},{L_diff_care},{L_left_subtree},{L_right_subtree},{y_right_subtree_pred},{y_left_subtree_pred}")

        ####################################### Train decision node ######################################
        tree_node.get_model.train(X = X_train_dnode_surr,
                                y = y_train_dnode_surr,
                                sample_weight = sample_weights,
                                R_i = len(dnode_idxs),
                                **node_args)
        
        ####################################### Update L or Rollback ################################################
        y_pred = tree_node.get_model.predict(X_train_dnode_surr) #1 -> send right, 0 -> send left
        
        idxs_care_points = dnode_idxs[mask_care_points] #care points indices for this dnode
        
        L_right_subtree_care = L_right_subtree[mask_care_points]
        L_left_subtree_care = L_left_subtree[mask_care_points]
        
        new_loss_sum = np.sum(L_right_subtree_care[y_pred == 1]) + np.sum(L_left_subtree_care[y_pred == 0])
        
        if new_loss_sum > old_loss_sum and not tree_node.get_model.dead and strict_update:
            # REJECT: Surrogate optimization failed to improve exact loss. Revert weights.
            # tree_node.get_model.set_w(old_w)
            # tree_node.get_model.set_b(old_b)
            tree_node.get_model.set_params(old_params)
        else:
            right_subtree_mask = (y_pred==1)
            if np.any(right_subtree_mask):
                right_idxs_care = idxs_care_points[right_subtree_mask]
                right_change = (right_idxs_care, L_right_subtree_care[right_subtree_mask])
            
            left_subtree_mask = (y_pred==0)
            if np.any(left_subtree_mask):
                left_idxs_care = idxs_care_points[left_subtree_mask]
                left_change = (left_idxs_care, L_left_subtree_care[left_subtree_mask])
    else:
        tree_node.get_model.train(X = X_train[[0]],
                                y = np.array([]),
                                sample_weight = np.array([]),
                                R_i = len(dnode_idxs),
                                **node_args)
    
    return tree_node.get_model, left_change, right_change, node_idx




def train_decision_node(tree_node, X_train:np.ndarray, y_train:np.ndarray, node_args:Dict, loss_fn, L:np.ndarray, strict_update:bool, tao_iter:int):
    target_dim = y_train.shape[1] if y_train.ndim>1 else 1
    if loss_fn.__name__ == "hinge_loss": target_dim = 3
    time_reduced_set = 0
    time_model_train = 0
    ####################### Generate pseudolabels #####################################
    left_idxs = tree_node.get_left.get_indexes
    right_idxs = tree_node.get_right.get_indexes
    dnode_idxs = np.concatenate((left_idxs, right_idxs)) #global indices
    if len(dnode_idxs) == 0:
        return time_reduced_set, time_model_train
    if np.all(L[dnode_idxs] == 0) and tao_iter>0:
        return time_reduced_set, time_model_train
    
    t_start_reduced = perf_counter()

    X_train_dnode = X_train[dnode_idxs]

    L_left_subtree = np.zeros(len(dnode_idxs), dtype = np.float64)
    L_right_subtree = np.zeros(len(dnode_idxs), dtype = np.float64)
    if len(left_idxs)>0:
        L_left_subtree[:len(left_idxs)] = L[left_idxs]
        # L_left_subtree[:len(left_idxs)] = L.get.remote(left_idxs)
        y_right_subtree_pred = tao_tree.predict(X_train[left_idxs], tree_node.get_right, target_dim=target_dim) #predictions of right subtree on samples from left subtree's reduced set
        L_right_subtree[:len(left_idxs)] = loss_fn(y_train[left_idxs], y_right_subtree_pred)
    if len(right_idxs)>0:
        L_right_subtree[-len(right_idxs):] = L[right_idxs]
        # L_right_subtree[-len(right_idxs):] = L.get.remote[right_idxs]
        y_left_subtree_pred = tao_tree.predict(X_train[right_idxs], tree_node.get_left, target_dim=target_dim) #predictions of left subtree on samples from right subtree's reduced set
        L_left_subtree[-len(right_idxs):] = loss_fn(y_train[right_idxs], y_left_subtree_pred)

    # dnode pred: 0 -> left, 1 -> right
    #L_---_subtree -> [-----left_idxs----]+[----right_idxs----]

    L_diff = L_left_subtree - L_right_subtree
    mask_care_points = (L_diff!=0)
    
    if np.any(mask_care_points):        
        L_diff_care = L_diff[mask_care_points]
        
        X_train_dnode_surr = X_train_dnode[mask_care_points]
        y_train_dnode_surr = (L_diff_care>0).astype(int)#if left subtree loss > right subtree loss -> label=1 (send to right subtree)
        
        sample_weights = np.abs(L_diff_care)
        # sample_weights = sample_weights/sample_weights.max() #mean can be used
        sample_weights = sample_weights/sample_weights.mean() #mean can be used
        
        idxs_care_points = dnode_idxs[mask_care_points]
        old_loss_sum = np.sum(L[idxs_care_points])
        # old_w = copy.deepcopy(tree_node.get_model.w)
        # old_b = copy.deepcopy(tree_node.get_model.b)
        old_params = copy.deepcopy(tree_node.get_model.get_params())
        
        t_end_reduced = perf_counter()
        time_reduced_set = t_end_reduced - t_start_reduced
        ####################################### Train decision node ######################################
        
        t_start_train = perf_counter()
        tree_node.get_model.train(X = X_train_dnode_surr,
                                y = y_train_dnode_surr,
                                sample_weight = sample_weights,
                                R_i = len(dnode_idxs),
                                **node_args)
        
        t_end_train = perf_counter()
        time_model_train = t_end_train - t_start_train
        
        ####################################### Update L or Rollback ################################################
        y_pred = tree_node.get_model.predict(X_train_dnode_surr) #1 -> send right, 0 -> send left
        
        idxs_care_points = dnode_idxs[mask_care_points] #care points indices for this dnode
        
        L_right_subtree_care = L_right_subtree[mask_care_points]
        L_left_subtree_care = L_left_subtree[mask_care_points]
        
        new_loss_sum = np.sum(L_right_subtree_care[y_pred == 1]) + np.sum(L_left_subtree_care[y_pred == 0])
        
        if new_loss_sum > old_loss_sum and not tree_node.get_model.dead and strict_update:
            # REJECT: Surrogate optimization failed to improve exact loss. Revert weights.
            # tree_node.get_model.set_w(old_w)
            # tree_node.get_model.set_b(old_b)
            tree_node.get_model.set_params(old_params)
        else:
            right_subtree_mask = (y_pred==1)
            if np.any(right_subtree_mask):
                right_idxs_care = idxs_care_points[right_subtree_mask]
                L[right_idxs_care] = L_right_subtree_care[right_subtree_mask]
            
            left_subtree_mask = (y_pred==0)
            if np.any(left_subtree_mask):
                left_idxs_care = idxs_care_points[left_subtree_mask]
                L[left_idxs_care] = L_left_subtree_care[left_subtree_mask]
    else:
        
        tree_node.get_model.train(X = X_train[[0]],
                                y = np.array([]),
                                sample_weight = np.array([]),
                                R_i = len(dnode_idxs),
                                **node_args)
    
    return time_reduced_set, time_model_train
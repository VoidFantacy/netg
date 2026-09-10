import models
import numpy as np
import copy
from scipy.sparse import isspmatrix, csr_matrix, issparse
from sklearn.cluster import KMeans 
from numpy.typing import NDArray
from typing import Union
import utils
from collections import deque


class TreeNode:

    def __init__(self, model=None, left=None, right=None, isleaf=False, indexes=[], isdead=False):
        self.__model = model
        self.__left = left
        self.__right = right
        self.isleaf = isleaf
        self.__indexes = indexes
        self.isdead = isdead # look when node is considered to be dead (Intro to ML book)

    @property
    def get_model(self):
        return self.__model

    @property
    def get_left(self):
        return self.__left

    @property
    def get_right(self):
        return self.__right

    @property
    def get_indexes(self):
        return self.__indexes

    def set_model(self, new_model):
        self.__model = copy.deepcopy(new_model)

    def set_left(self, new_left):
        self.__left = new_left

    def set_right(self, new_right):
        self.__right = new_right

    def set_indexes(self, new_idxs):
        self.__indexes = new_idxs

    def append_idx(self, idx):
        self.__indexes.append(idx)



class Tree:

    def __init__(self, root, rbfs, depth, node_type, leaf_type):
        self.__root = root
        self.__rbfs = rbfs
        self.__depth = depth
        self.__leaf_parent_list = None
        self.node_type = node_type
        self.leaf_type = leaf_type

    @property
    def get_root(self):
        return self.__root

    @property
    def get_leaf_parent_list(self):
        return self.__leaf_parent_list

    @property
    def get_rbfs(self):
        return self.__rbfs

    @property
    def get_depth(self):
        return self.__depth
    
    @property
    def get_leaf_count(self):
        return len(self.__rbfs[self.__depth])

    def set_root(self, new_root):
        self.__root = new_root

    def set_rbfs(self, new_rbfs):
        self.__rbfs = new_rbfs

    def set_depth(self, new_depth):
        self.__depth = new_depth
    
    def calculate_depth(self):
        def __helper(tnode, level):
            if tnode.isleaf:
                return level
            lh,rh = -10, -10
            if tnode.get_left:
                lh = __helper(tnode.get_left, level+1)
            if tnode.get_right:
                rh = __helper(tnode.get_right, level+1)
            return max(lh, rh)
        return __helper(self.__root, 1)

    def __upd_rbfs_helper(self, tnode, rbfs, curr_depth, leaf_parent_list):
        if tnode.isleaf:
            rbfs[self.__depth].append(tnode)
        else:
            rbfs[curr_depth].append(tnode)
            # if tnode.get_left.isleaf:
            #     leaf_parent_list.append((tnode, 'left', tnode.get_left)) #(tnode, tnode.get_left, tnode.set_left)
            self.__upd_rbfs_helper(tnode.get_left, rbfs, curr_depth + 1, leaf_parent_list)
            # if tnode.get_right.isleaf:
            #     leaf_parent_list.append((tnode, 'right', tnode.get_right)) #(tnode, tnode.get_left, tnode.set_left)
            self.__upd_rbfs_helper(tnode.get_right, rbfs, curr_depth + 1, leaf_parent_list)

    def upd_rbfs(self):
        rbfs = {}
        leaf_parent_list = []
        for i in range(1, self.__depth + 1):
            rbfs[i] = []
        self.__upd_rbfs_helper(self.__root, rbfs, 1, leaf_parent_list)
        self.__rbfs = rbfs
        # self.__leaf_parent_list = leaf_parent_list


def update_indexes(tnode:TreeNode, X_train:Union[NDArray[np.float64], csr_matrix], idxs:NDArray[np.int64], isdead:bool=False):
    assert isinstance(idxs, np.ndarray), "idxs must be np array"
    if len(idxs) == 0: 
        isdead = True
    queue = deque([(tnode, idxs, isdead)])
    while queue:
        node, idxs, isdead = queue.popleft()
        node.isdead = isdead
        node.set_indexes(idxs)
        if not node.isleaf:
            if isdead:
                queue.append((node.get_left, np.array([], dtype = int), True))
                queue.append((node.get_right, np.array([], dtype = int), True))
            else:
                pred = node.get_model.predict(X_train[idxs]) #array 0 or 1 (left or right)
                # left_idxs = [idxs[x] for x in range(0, len(idxs)) if pred[x] == 0]
                mask = pred.astype(bool)
                left_idxs = idxs[~mask]
                if len(left_idxs)>0:
                    queue.append((node.get_left, left_idxs, False))
                else:
                    queue.append((node.get_left, np.array([], dtype = int), True))
                right_idxs = idxs[mask]
                if len(right_idxs)>0:
                    queue.append((node.get_right, right_idxs, False))
                else:
                    queue.append((node.get_right, np.array([], dtype = int), True))


#==================================================Node init======================================================
def _kmeans_init(dnode:TreeNode, X_train:Union[NDArray[np.float64], csr_matrix], y_train:NDArray[np.float64]):
    if dnode.isleaf:
        dnode.get_model.init_params(X_train, y_train, init_type = 'rnd_init')
    else:
        # Check if the incoming subset is too small for K-Means
        if len(X_train) < 2:
            dnode.get_model.init_params(X_train, y_train, init_type = 'rnd_init')
        else:
            dnode.get_model.init_params(X_train, y_train, init_type = 'kmeans')
            
        pred_mask = dnode.get_model.predict(X_train).astype(bool)
        
        # If the K-Means hyperplane routed everything to one side, force a random split
        if len(X_train) >= 2 and (not np.any(pred_mask) or np.all(pred_mask)):
            dnode.get_model.init_params(X_train, y_train, init_type = 'rnd_init')
            pred_mask = dnode.get_model.predict(X_train).astype(bool)

        left_idxs = ~pred_mask
        _kmeans_init(dnode.get_left, X_train[left_idxs], y_train[left_idxs])
        
        right_idxs = pred_mask
        _kmeans_init(dnode.get_right, X_train[right_idxs], y_train[right_idxs])


def _random_init(dnode:TreeNode, X_train:Union[NDArray[np.float64], csr_matrix], y_train:NDArray[np.float64]):
    if dnode.isleaf:
        # dnode.get_model.init_params(X_train, y_train, init_type = 'rnd_init')
        pass
    else:
        dnode.get_model.init_params(X_train, y_train, init_type = 'rnd_init')
        _random_init(dnode.get_left, X_train, y_train)
        _random_init(dnode.get_right, X_train, y_train)


def _median_init(dnode:TreeNode, X_train:Union[NDArray[np.float64], csr_matrix], y_train:NDArray[np.float64]):
    if dnode.isleaf:
        # dnode.get_model.init_params(X_train, y_train, init_type = 'rnd_init')
        pass
    else:
        dnode.get_model.init_params(X_train, y_train, init_type = 'median_split')
        pred_mask = dnode.get_model.predict(X_train).astype(bool)
        left_idxs = ~pred_mask
        if len(left_idxs)>0:
            _median_init(dnode.get_left, X_train[left_idxs], y_train[left_idxs])
        right_idxs = pred_mask
        if len(right_idxs)>0:
            _median_init(dnode.get_right, X_train[right_idxs], y_train[right_idxs])

#==================================Tree structure initialization======================================================

def get_complete_tree(X_train, y_train, depth, init_type, node_type, leaf_type, **kwargs):
    gamma_dnode = kwargs.get('gamma_dnode', None)
    gamma_leaf = kwargs.get('gamma_leaf', None)
    kernel_dnode = kwargs.get('kernel_dnode', None)
    kernel_leaf = kwargs.get('kernel_leaf', None)
    def _gen_complete_tree_helper(curr_depth, node_type, leaf_type):
        if curr_depth == depth:
            leaf_model = models.get_leaf_model(leaf_type, gamma=gamma_leaf, kernel=kernel_leaf)
            leaf = TreeNode(isleaf=True, model=leaf_model)
            return leaf
        if curr_depth < depth:
            node_model = models.get_node_model(node_type, gamma=gamma_dnode, kernel=kernel_dnode)
            node = TreeNode(model=node_model)
            node_left = _gen_complete_tree_helper(curr_depth + 1, node_type, leaf_type)
            node.set_left(node_left)
            node_right = _gen_complete_tree_helper(curr_depth + 1, node_type, leaf_type)
            node.set_right(node_right)
        return node
    root = _gen_complete_tree_helper(1, node_type, leaf_type)
    dtree = Tree(root=root, rbfs=dict(), depth=depth, node_type = node_type, leaf_type=leaf_type)
    dtree.upd_rbfs()
    
    if init_type == "kmeans":
        _kmeans_init(root, X_train, y_train)
    elif init_type == "rnd_init":
        _random_init(root, X_train, y_train)
    elif init_type == "median_split":
        _median_init(root, X_train, y_train)
    else:
        raise ValueError("Node init is not supported")
    update_indexes(root, X_train, np.arange(0, X_train.shape[0]))
    for leaf_node in dtree.get_rbfs[dtree.get_depth]:
        if not leaf_node.get_model.initialized:
            idxs = leaf_node.get_indexes
            if len(idxs) > 1:
                leaf_node.get_model.init_params(X_train[idxs], y_train[idxs], "rnd_init")
            else:
                leaf_node.get_model.init_params(X_train[:10], y_train[:10], "rnd_init")
    
    return dtree


def get_nested_dichotomy(X_train, y_train, depth, node_args, leaf_args, node_type, leaf_type, **kwargs):
    """
    Generates a nested dichotomy using oblique or kernel decision nodes for classification.
    Uses the models factory to dynamically instantiate nodes and leaves.
    """
    gamma_dnode = kwargs.get('gamma_dnode', None)
    gamma_leaf = kwargs.get('gamma_leaf', None)
    kernel_dnode = kwargs.get('kernel_dnode', None)
    kernel_leaf = kwargs.get('kernel_leaf', None)
    class_threshold = kwargs.get('class_threshold', 1)

    y_train_cls = np.argmax(y_train, axis=1)

    def _gen_recursive_split(idxs, curr_depth):
        node = TreeNode()
        node.isdead = False
        node.set_indexes(idxs)
        X_node = X_train[idxs]
        y_node = y_train[idxs]
        y_node_cl = y_train_cls[idxs]
        cls = np.unique(y_node_cl)

        # Base Case: Reach maximum depth or class purity threshold
        if cls.shape[0] <= class_threshold or curr_depth == depth:
            node.isleaf = True
            leaf_model = models.get_leaf_model(leaf_type, gamma=gamma_leaf, kernel=kernel_leaf)
            
            # Copy leaf_args to prevent mutating the shared dictionary across recursive branches
            current_leaf_args = leaf_args.copy()
            
            leaf_model.train(X_node, y_node,  R_i = X_node.shape[0], **current_leaf_args)
            node.set_model(leaf_model)
            return node
            
        # Recursive Case: Internal Node
        node_model = models.get_node_model(node_type, gamma=gamma_dnode, kernel=kernel_dnode)
        
        current_node_args = node_args.copy()
        
        # Split available classes randomly into two halves for the dichotomy
        np.random.shuffle(cls)
        mid = len(cls) // 2
        cl1 = cls[mid:]
        
        y_binary = np.zeros(y_node.shape[0], dtype=np.int64)
        y_binary[np.isin(y_node_cl, cl1)] = 1
        
        # Fit the decision node to split the data
        node_model.train(X=X_node, y=y_binary, sample_weight=np.ones(y_node.shape[0], dtype=np.float64), R_i = X_node.shape[0], **current_node_args)
        pred = node_model.predict(X_node)
        mask_right = pred.astype(bool)
        
        # Failsafe: If the split sends 100% of data to one side, force early leaf creation
        if mask_right.sum() == 0 or mask_right.sum() == len(pred):
            node.isleaf = True
            leaf_model = models.get_leaf_model(leaf_type, gamma=gamma_leaf, kernel=kernel_leaf)
            
            current_leaf_args = leaf_args.copy()
            
            leaf_model.train(X_node, y_node, R_i = X_node.shape[0], **current_leaf_args)
            node.set_model(leaf_model)
            return node
            
        mask_left = ~mask_right
        node.set_model(node_model)
        
        # Recurse down left and right branches
        node.set_left(_gen_recursive_split(idxs[mask_left], curr_depth + 1))
        node.set_right(_gen_recursive_split(idxs[mask_right], curr_depth + 1))
        
        return node

    root = _gen_recursive_split(np.arange(X_train.shape[0]), curr_depth=1)
    dtree = Tree(root=root, rbfs=dict(), depth=depth, node_type=node_type, leaf_type=leaf_type)
    dtree.upd_rbfs()

    return dtree


def get_cart_tree(X_train, y_train, tao_node_type, model):
    """
    Converts a trained scikit-learn DecisionTreeClassifier into the custom TAO Tree format.
    Currently supports classification and constant leaves.
    """
    n_input = X_train.shape[1]

    def train_leaf(node, X_train, y_train):
        if node.isleaf:
            X_tr_leaf = X_train[node.get_indexes]
            y_tr_leaf = y_train[node.get_indexes]
            node.get_model.train(X_tr_leaf, y_tr_leaf)
            return
        train_leaf(node.get_left, X_train, y_train)
        train_leaf(node.get_right, X_train, y_train)

    def helper(featindices, thresholds, counter, curr_depth):
        # scikit-learn uses -2 in the feature array to denote a leaf node
        if featindices[counter] < 0:
            leaf_model = models.get_leaf_model("majority_classification") 
            leaf_model.init_params(X=X_train, y=y_train, init_type='rnd_init')
            return TreeNode(model=leaf_model, isleaf=True), counter

        node_model = models.get_node_model(tao_node_type)
        
        if tao_node_type == "univariate":
            node_model.set_bias(thresholds[counter])
            node_model.set_feat_idx(featindices[counter])
        elif tao_node_type == "linear": 
            w, b = np.zeros((1, n_input)), np.zeros((1, 1))
            fid, b[0, 0] = featindices[counter], -thresholds[counter]
            w[0, fid] = 1.0
            node_model.set_b(b)
            node_model.set_w(csr_matrix(w))
        else:
            raise ValueError(f"CART conversion only supports 'univariate' and 'linear' nodes, got: {tao_node_type}")

        node = TreeNode(model=node_model)
        counter += 1
        
        node_left, counter = helper(featindices, thresholds, counter, curr_depth + 1)
        node.set_left(node_left)
        
        counter += 1
        node_right, counter = helper(featindices, thresholds, counter, curr_depth + 1)
        node.set_right(node_right)
        
        return node, counter

    featindex = model.tree_.feature
    splitval = model.tree_.threshold
    depth = model.get_depth() + 1
    
    y_pred = model.predict(X_train)
    print(y_pred.shape)
    print('\t\t\t*** CART train error:', utils.misclass_loss(np.argmax(y_train, 1), y_pred), " depth: ", depth)

    root, count = helper(featindex, splitval, counter=0, curr_depth=1)
    
    # Route data down the initialized tree structure
    update_indexes(root, X_train, np.arange(0, X_train.shape[0]))
    train_leaf(root, X_train, y_train)
    
    dtree = Tree(root=root, rbfs=dict(), depth=depth, node_type=tao_node_type, leaf_type="majority_classification")
    dtree.upd_rbfs()
    
    print("\t\t\t*** TAO init train error: ", utils.calculate_loss(root, X_train, y_train, utils.misclass_loss), " node count: ", count)
    return dtree


def get_kmeans_initialized_tree(X_train, y_train, centroids, assignments, random_state=None, leaf_type="majority_regression"):
    """
    Initializes a TAO tree using hierarchical bisecting K-Means on flat K-Means centroids.
    Tree is oblique with majority_regression leaves
    
    Parameters:
    - X_train: The raw training data (N, D). Can be dense or sparse.
    - y_train: The target values (N, ...), used to initialize the leaf regressors.
    - centroids: The free K-means centroids (K, D).
    - assignments: The cluster assignments for each point in X_train (N,).
    - leaf_type: The type of leaf estimator
    
    Returns:
    - dtree: A fully initialized Tree object ready for TAO optimization.
    """
    K = centroids.shape[0]
    
    # Calculate the weight (mass) of each centroid
    weights = np.bincount(assignments, minlength=K).astype(np.float64)
    
    # Pre-map data indices to centroids for O(1) routing lookups
    # centroid_to_data[k] contains an array of raw data indices belonging to centroid k
    centroid_to_data = {i: np.where(assignments == i)[0] for i in range(K)}
    
    def _build_node(curr_centroid_indices, curr_depth):
        # Aggregate the raw data indices (reduced set) for this specific node
        if len(curr_centroid_indices) == 0:
            raise ValueError(
                f"Pathological tree state detected at depth {curr_depth}: _build_node received 0 centroids. "
                f"This indicates a severe routing failure or corrupted parent split."
            )
        
        curr_data_indices = np.concatenate([centroid_to_data[c] for c in curr_centroid_indices])
            
        # Base Case: Only one centroid left (pure node)
        if len(curr_centroid_indices) == 1:
            leaf_model = models.get_leaf_model("majority_regression")
            
            # STRICT ERROR ENFORCEMENT: Empty Cluster Detection
            if len(curr_data_indices) == 0:
                centroid_id = curr_centroid_indices[0]
                raise ValueError(
                    f"Pathological K-Means state detected: Centroid {centroid_id} "
                    f"has exactly 0 data points assigned to it in the provided labels.\n"
                    f"This means the upstream flat K-Means collapsed an empty cluster, "
                    f"likely because K is too large for the dataset. Please reduce K or "
                    f"verify your flat K-Means output."
                )
            
            node = TreeNode(isleaf=True, model=leaf_model, indexes=curr_data_indices)
            return node, curr_depth
            
        # Recursive Case: Bisect the subset of centroids
        subset_centroids = centroids[curr_centroid_indices]
        subset_weights = weights[curr_centroid_indices]
        
        # Weighted K-Means with k=2
        bisector = KMeans(n_clusters=2, n_init=10, random_state=random_state)
        bisector.fit(subset_centroids, sample_weight=subset_weights)
        
        # Get the split geometry (M1 and M2)
        M1, M2 = bisector.cluster_centers_
        
        # Calculate separating hyperplane parameters (w and b)
        # We define w = M2 - M1. 
        # In NodeLinearModel: scores = X @ w.T + b. 
        # A score >= 0 routes to the Right (1), which corresponds to M2.
        w = M2 - M1
        midpoint = (M1 + M2) / 2.0
        b = -1.0 * np.dot(w, midpoint)
        
        # Instantiate and populate the NodeLinearModel
        node_model = models.get_node_model("linear")
        node_model.initialized = True
        node_model.dead = False
        
        if issparse(X_train):
            node_model.set_w(csr_matrix(w.reshape(1, -1)))
        else:
            node_model.set_w(w.reshape(1, -1))
        node_model.set_b(np.array([[b]]))
        
        # Route centroids to Left (0) and Right (1)
        # Route centroids to Left (0) and Right (1)
        split_labels = bisector.labels_
        left_centroids = [curr_centroid_indices[i] for i in range(len(curr_centroid_indices)) if split_labels[i] == 0]
        right_centroids = [curr_centroid_indices[i] for i in range(len(curr_centroid_indices)) if split_labels[i] == 1]
        
        # STRICT ERROR ENFORCEMENT
        if len(left_centroids) == 0 or len(right_centroids) == 0:
            raise ValueError(
                f"Pathological K-Means split detected: A child node received 0 centroids.\n"
                f"This mathematically implies degenerate inputs. Check for duplicate "
                f"centroid coordinates or extreme numerical underflow.\n"
                f"Centroids passed to this node: {curr_centroid_indices}\n"
                f"Coordinates:\n{subset_centroids}"
            )
            
        # Construct the tree node and attach the reduced set
        node = TreeNode(isleaf=False, model=node_model, indexes=curr_data_indices)
        
        # Recurse for children
        left_child, left_depth = _build_node(left_centroids, curr_depth + 1)
        right_child, right_depth = _build_node(right_centroids, curr_depth + 1)
        
        node.set_left(left_child)
        node.set_right(right_child)
        
        return node, max(left_depth, right_depth)

    # Begin top-down construction using all K centroid indices (0 to K-1)
    initial_centroids = list(range(K))
    root_node, tree_depth = _build_node(initial_centroids, curr_depth=1)
    
    # Wrap in the main Tree class expected by tao.py
    dtree = Tree(
        root=root_node,
        rbfs=dict(),
        depth=tree_depth,
        node_type="linear",
        leaf_type=leaf_type
    )
    
    # Populate the level-wise references required by TAO
    dtree.upd_rbfs()
    
    return dtree


def get_bisecting_kmeans_tree(X_train, y_train, n_clusters, strategy="biggest_inertia", random_state=None):
    """
    Initializes a TAO tree using a strict top-down Bisecting K-Means algorithm, 
    mirroring sklearn.cluster.BisectingKMeans. Tree is oblique with majority_regression leaves
    
    Parameters:
    - X_train: Raw training data (N, D).
    - y_train: Target values (N, ...).
    - n_clusters: The final number of leaf nodes desired.
    - strategy: "biggest_inertia" or "largest_cluster".
    - random_state: Seed for the internal k=2 KMeans splits.
    
    Returns:
    - dtree: A fully initialized Tree object ready for TAO.
    """
    if strategy not in ["biggest_inertia", "largest_cluster"]:
        raise ValueError("Strategy must be 'biggest_inertia' or 'largest_cluster'")
        
    N = X_train.shape[0]
    
    # Helper to calculate the inertia (SSE) of a specific data subset
    def _calculate_inertia(indices):
        if len(indices) == 0:
            return 0.0
        X_sub = X_train[indices]
        # For sparse matrices, computing variance/inertia requires dense operations or specific sparse math
        if issparse(X_sub):
            mean_vec = np.asarray(X_sub.mean(axis=0))
            
            # SSE = sum(||x||^2) - N * ||mu||^2
            sq_sum = X_sub.power(2).sum()
            mean_sq_sum = len(indices) * np.sum(mean_vec ** 2)
            
            # Return max(0, val) to prevent floating point inaccuracies from yielding negative zero
            return max(0.0, sq_sum - mean_sq_sum)
        else:
            mean_vec = np.mean(X_sub, axis=0)
            return np.sum((X_sub - mean_vec) ** 2)

    # 1. Initialize the root state
    all_indices = np.arange(N)
    root_node = TreeNode(isleaf=True, indexes=all_indices)
    
    # Track active leaves: list of tuples (TreeNode, indices, inertia)
    active_leaves = [(root_node, all_indices, _calculate_inertia(all_indices))]
    
    # 2. Iteratively bisect until we reach n_clusters
    while len(active_leaves) < n_clusters:
        # Determine which node to split based on the selected strategy
        if strategy == "biggest_inertia":
            # Sort by inertia (descending), pick the highest
            active_leaves.sort(key=lambda x: x[2], reverse=True)
        elif strategy == "largest_cluster":
            # Sort by number of points (descending), pick the largest
            active_leaves.sort(key=lambda x: len(x[1]), reverse=True)
            
        # Pop the candidate node to bisect
        node_to_split, current_indices, _ = active_leaves.pop(0)
        
        # Failsafe: Cannot split a node with less than 2 points
        if len(current_indices) < 2:
            raise ValueError(
                f"Cannot bisect a node with {len(current_indices)} points. "
                f"The requested n_clusters ({n_clusters}) likely exceeds the number of distinct data points."
            )
            
        X_subset = X_train[current_indices]
        
        # Perform 2-Means on the subset
        bisector = KMeans(n_clusters=2, n_init=10, random_state=random_state)
        bisector.fit(X_subset)
        
        M1, M2 = bisector.cluster_centers_
        split_labels = bisector.labels_
        
        # Separate indices into left (0) and right (1)
        mask = split_labels.astype(bool)
        left_indices = current_indices[~mask]
        right_indices = current_indices[mask]
        
        # Failsafe: Pathological split resulted in an empty child
        if len(left_indices) == 0 or len(right_indices) == 0:
            raise ValueError(
                f"Pathological K-Means split: Bisecting KMeans produced an empty child node.\n"
                f"Left indices: {len(left_indices)}, Right indices: {len(right_indices)}.\n"
                f"This indicates severe convergence failure or entirely overlapping duplicate data points."
            )
            
        # 3. Morph the chosen leaf into a decision node
        node_to_split.isleaf = False
        
        # Calculate separating hyperplane (w, b)
        w = M2 - M1
        midpoint = (M1 + M2) / 2.0
        b = -1.0 * np.dot(w, midpoint)
        
        node_model = models.get_node_model("linear")
        node_model.initialized = True
        node_model.dead = False
        if issparse(X_train):
            node_model.set_w(csr_matrix(w.reshape(1, -1)))
        else:
            node_model.set_w(w.reshape(1, -1))
        node_model.set_b(np.array([[b]]))
        
        node_to_split.set_model(node_model)
        
        # 4. Create new child leaves
        left_child = TreeNode(isleaf=True, indexes=left_indices)
        right_child = TreeNode(isleaf=True, indexes=right_indices)
        
        node_to_split.set_left(left_child)
        node_to_split.set_right(right_child)
        
        # Add the new children to the active tracking list
        active_leaves.append((left_child, left_indices, _calculate_inertia(left_indices)))
        active_leaves.append((right_child, right_indices, _calculate_inertia(right_indices)))

    # 5. Initialize the final leaf models with the target data
    # Calculate depth simultaneously by traversing the built tree
    def _init_leaves_and_get_depth(node, curr_depth):
        if node.isleaf:
            leaf_indices = node.get_indexes
            
            # STRICT ERROR ENFORCEMENT
            if len(leaf_indices) == 0:
                raise ValueError(
                    f"Pathological tree structure at depth {curr_depth}: "
                    f"A leaf node contains exactly 0 data points. This violates strict bisection guarantees."
                )
                
            leaf_model = models.get_leaf_model("majority_regression")
            leaf_model.train(X_train[leaf_indices], y_train[leaf_indices])
            node.set_model(leaf_model)
            return curr_depth
            
        left_depth = _init_leaves_and_get_depth(node.get_left, curr_depth + 1)
        right_depth = _init_leaves_and_get_depth(node.get_right, curr_depth + 1)
        return max(left_depth, right_depth)

    tree_depth = _init_leaves_and_get_depth(root_node, 1)

    # 6. Wrap in the TAO Tree architecture
    dtree = Tree(
        root=root_node,
        rbfs=dict(),
        depth=tree_depth,
        node_type="linear",
        leaf_type="majority_regression"
    )
    
    dtree.upd_rbfs()
    
    return dtree

#=============================================Pruning=======================================================
# don't forget to call upd_rbfs after this function
def remove_dead_nodes(tnode):
    if tnode.isleaf:
        return tnode

    if tnode.get_right.isdead:
        return remove_dead_nodes(tnode.get_left)
    if tnode.get_left.isdead:
        return remove_dead_nodes(tnode.get_right)

    tnode.set_left(remove_dead_nodes(tnode.get_left))
    tnode.set_right(remove_dead_nodes(tnode.get_right))

    return tnode
    

#=========================================================Inference=========================================

def predict(X: Union[NDArray[np.float64], csr_matrix], tree_node, target_dim: int, sparse_output: bool = False):
    assert isinstance(X, (np.ndarray, csr_matrix)), "X must be a numpy array or a sparse matrix"
    assert isinstance(tree_node, TreeNode), "tree_node must be an instance of TreeNode"
    assert isinstance(target_dim, int) and target_dim > 0, "target_dim must be a positive integer"
    n_samples = X.shape[0]
    
    queue = deque([(tree_node, np.arange(n_samples))])
    
    if sparse_output:
        out_rows, out_cols, out_data = [], [], []
        target_dim = max(1, target_dim)
    else:
        # Pre-allocate dense arrays
        predicts = np.zeros((n_samples, target_dim)) if target_dim > 1 else np.zeros(n_samples)

    while queue:
        node, idxs = queue.popleft()
        
        if node.isleaf:
            if len(idxs) > 0:
                # Leaf evaluation
                pred = node.get_model.predict(X[idxs])
                
                if sparse_output:
                    # Handle Sparse Outputs via COO Accumulation
                    if issparse(pred):
                        pred_coo = pred.tocoo()
                        out_rows.extend(idxs[pred_coo.row])
                        out_cols.extend(pred_coo.col)
                        out_data.extend(pred_coo.data)
                    else:
                        # If the leaf returns a dense array, extract non-zeros
                        pred = np.atleast_2d(pred).T if pred.ndim == 1 else pred
                        r, c = np.nonzero(pred)
                        out_rows.extend(idxs[r])
                        out_cols.extend(c)
                        out_data.extend(pred[r, c])
                else:
                    # Handle Dense Outputs
                    if issparse(pred):
                        predicts[idxs] = pred.toarray()
                    else:
                        # Ravel to handle (N, 1) to (N,) assignments safely
                        predicts[idxs] = pred.ravel() if target_dim == 1 else pred

        else:
            node_pred = node.get_model.predict(X[idxs])
            
            if issparse(node_pred):
                node_pred = node_pred.toarray().ravel()
            
            mask = node_pred.astype(bool)
            
            left_idxs = idxs[~mask]
            if len(left_idxs) > 0:
                queue.append((node.get_left, left_idxs))
                
            right_idxs = idxs[mask]
            if len(right_idxs) > 0:
                queue.append((node.get_right, right_idxs))

    if sparse_output:
        return csr_matrix((out_data, (out_rows, out_cols)), shape=(n_samples, target_dim))
    
    return predicts


def predict_probability(X:Union[NDArray[np.float64], csr_matrix], tree_node:TreeNode, target_dim:int, sparse_output:bool = False):
    """
    sparse_output:bool - if True produces sparse output
    returns histogram of a leaf from root-to-leaf path of a sample point
    """
    assert isinstance(X, (np.ndarray, csr_matrix)), "X must be a numpy array or a sparse matrix"
    assert isinstance(tree_node, TreeNode), "tree_node must be an instance of TreeNode"
    assert isinstance(target_dim, int) and target_dim > 0, "target_dim must be a positive integer"
    n_samples = X.shape[0]
    
    if sparse_output:
        out_rows, out_cols, out_data = [], [], []
        target_dim = max(1, target_dim)
    else:
        # Pre-allocate dense arrays
        predicts = np.zeros((n_samples, target_dim)) if target_dim > 1 else np.zeros(n_samples)
    queue = deque([(tree_node, np.arange(n_samples))])
    while queue:
        node, idxs = queue.popleft()
        if node.isleaf:
            if len(idxs)>0:
                pred= node.get_model.predict_proba(X[idxs])
                if sparse_output:
                    # Handle Sparse Outputs via COO Accumulation
                    if issparse(pred):
                        pred_coo = pred.tocoo()
                        out_rows.extend(idxs[pred_coo.row])
                        out_cols.extend(pred_coo.col)
                        out_data.extend(pred_coo.data)
                    else:
                        # If the leaf returns a dense array, extract non-zeros
                        pred = np.atleast_2d(pred).T if pred.ndim == 1 else pred
                        r, c = np.nonzero(pred)
                        out_rows.extend(idxs[r])
                        out_cols.extend(c)
                        out_data.extend(pred[r, c])
                else:
                    # Handle Dense Outputs
                    if issparse(pred):
                        predicts[idxs] = pred.toarray()
                    else:
                        # Ravel to handle (N, 1) to (N,) assignments safely
                        predicts[idxs] = pred.ravel() if target_dim == 1 else pred
        else:
            node_pred = node.get_model.predict(X[idxs])            
            if issparse(node_pred):
                node_pred = node_pred.toarray().ravel()
            mask = node_pred.astype(bool)
            
            left_idxs = idxs[~mask]
            if len(left_idxs)>0:
                queue.append((node.get_left, left_idxs))
            right_idxs = idxs[mask]
            if len(right_idxs)>0:
                queue.append((node.get_right, right_idxs))
    
    if sparse_output:
        return csr_matrix((out_data, (out_rows, out_cols)), shape=(n_samples, target_dim))
    
    return predicts
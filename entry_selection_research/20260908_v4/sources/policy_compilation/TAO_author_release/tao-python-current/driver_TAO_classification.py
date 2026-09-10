import os
import numpy as np
import tao
import tao_tree
import utils
import sys
import argparse
import random
import json
from pathlib import Path
from scipy.sparse import csr_matrix
from sklearn.tree import DecisionTreeClassifier

def create_unique_folder(base_name):
    original_path = Path(base_name)
    path = original_path
    counter = 1
    
    while True:
        try:
            path.mkdir(parents=True, exist_ok=False)
            return path
            
        except FileExistsError:
            path = original_path.with_name(f"{original_path.name} ({counter})")
            counter += 1


def load_saved_california_housing(filepath="datasets/CaliforniaHousing.npz"):
    """
    Loads the pre-scaled California Housing train and test sets.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cannot find '{filepath}'. Make sure the file is in the same directory.")
        
    with np.load(filepath) as data:
        X_train = data['X_train']
        X_test = data['X_test']
        y_train = data['y_train']
        y_test = data['y_test']
        
    print("Successfully loaded California Housing data.")
    return (X_train, y_train, X_test, y_test), "CaliforniaHousing"


def load_saved_mnist(filepath="datasets/MNIST.npz"):
    """
    Loads the MNIST train and test sets.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cannot find '{filepath}'. Make sure the file is in the same directory.")
        
    with np.load(filepath) as data:
        X_train = data['X_train']
        X_test = data['X_test']
        y_train = data['y_train']
        y_test = data['y_test']
        
    print("Successfully loaded MNIST data.")
    return (X_train, y_train, X_test, y_test), "MNIST"


if __name__ == "__main__":
    
    (X_train, y_train, X_test, y_test), name = load_saved_mnist(filepath="datasets/MNIST.npz")

    parser = argparse.ArgumentParser(description="Parse tree model hyperparameters.")

    parser.add_argument("--C_dnode", type=float, default=10,
                        help="Regularization parameter for decision nodes (default: 10)")
    parser.add_argument("--depth", type=int, default=3,
                        help="Tree depth (default: 3)")
    parser.add_argument("--alpha", type=float, default=0,
                        help="Alpha parameter (default: 0)")

    args = parser.parse_args()

    print("Parsed arguments:")
    print(f"  C_dnode = {args.C_dnode}")
    print(f"  depth   = {args.depth}")
    print(f"  alpha   = {args.alpha}")
    
    C_dnode = args.C_dnode
    depth = args.depth
    alpha = args.alpha
    
    loss = utils.misclass_loss #loss type
    n_cpus = 1 #number of CPU
    max_iter_tao = 20 #number of tao iterations
    scale = False #to scale reduced sets separately
    strict_update = True
    init_type = "median_split" #type of initial split
    node_type = "linear" #type of decision nodes
    leaf_type = "majority_classification" #type of leaf nodes
    
    
    node_args = {
        "C":C_dnode,
        "alpha": alpha,
        "max_iter": 300,
        "scale": scale,
    }
    
    leaf_args = {}
    
    sequential = (1,depth-1)
    
    np.random.seed(42)
    random.seed(42)
    dtree = tao_tree.get_complete_tree(
                X_train,        
                y_train, 
                depth=depth, 
                init_type=init_type, 
                node_type=node_type, 
                leaf_type=leaf_type
                )
    
    Path("experiments").mkdir(parents=True, exist_ok=True)
    folder_path = create_unique_folder(f"experiments/{name}")
    
    tao_metrics = tao.tao_main(
                X_train,y_train,X_test,y_test,
                dtree=dtree,
                loss=loss,
                n_cpus=n_cpus,
                sequential = sequential,
                max_iter=max_iter_tao,
                tol=1e-5,
                node_args=node_args,
                leaf_args=leaf_args,
                postprocess=True,
                tree_logg_folder=folder_path,
                logg_progress=False,
                strict_update=strict_update)
    
    train_loss = tao_metrics[0]
    test_loss = tao_metrics[1]
    obj_value = tao_metrics[2]
    train_time_reduced_set_arr = tao_metrics[3]
    train_time_model_arr = tao_metrics[4]
    train_time_leaves_arr = tao_metrics[5]

    depth = dtree.get_depth
    leaf_count = dtree.get_leaf_count
    
    results = {
        "loss": loss.__name__,
        "init_type": init_type,
        "node_type": node_type,
        "leaf_type": leaf_type,
        "strict_update": strict_update,
        "node_args": node_args,
        "leaf_args": leaf_args,
        "depth": int(depth),
        "leaf_count": int(leaf_count),
        "train_loss": train_loss,
        "test_loss": test_loss,
        "obj_value": obj_value,
    }
    
    output_file = f"{folder_path}/results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=4)
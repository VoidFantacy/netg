from .decision_node import NodeLinearModel, NodeUnivariateModel
from .leaf import (
    LeafMajorityClassificationModel,
    LeafKernelClassification,
    LeafMajorityRegressionModel
)

NODE_REGISTRY = {
    "linear": NodeLinearModel,
    "univariate": NodeUnivariateModel,
}

LEAF_REGISTRY = {
    "majority_classification": LeafMajorityClassificationModel,
    "kernel_classification": LeafKernelClassification,
    "majority_regression": LeafMajorityRegressionModel,
}

def get_node_model(node_type: str, **kwargs):
    if node_type not in NODE_REGISTRY:
        raise ValueError(f"Unsupported node type: {node_type}. Available: {list(NODE_REGISTRY.keys())}")
    return NODE_REGISTRY[node_type](**kwargs)

def get_leaf_model(leaf_type: str, **kwargs):
    if leaf_type not in LEAF_REGISTRY:
        raise ValueError(f"Unsupported leaf type: {leaf_type}. Available: {list(LEAF_REGISTRY.keys())}")
    return LEAF_REGISTRY[leaf_type](**kwargs)
from abc import ABC, abstractmethod
from typing import Tuple

class Model(ABC):

    @abstractmethod
    def init_params(self, X, y, init_type: str):
        pass

    @abstractmethod
    def predict(self, X):
        pass

    @abstractmethod
    def train(self, X, y, sample_weight=None, **kwargs):
        pass

    @abstractmethod
    def param_count(self) -> Tuple[int, int]:
        pass
    
    @abstractmethod
    def get_weight_metric(self):
        pass
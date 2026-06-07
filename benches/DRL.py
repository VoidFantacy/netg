import subprocess
import os
import datetime
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import json
import random
from typing import List, Tuple, Dict, Any
from collections import defaultdict
import gymnasium as gym
from gymnasium import spaces
import time
from dataclasses import dataclass
import sys
import struct
from sklearn.decomposition import PCA
from sklearn.metrics import pairwise_distances

# 尝试导入C++模块
try:
    import importlib.util
    module_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 'build', 'benches', 
        'graph_eval.cpython-38-x86_64-linux-gnu.so'
    )
    module_path = os.path.abspath(module_path)
    
    if os.path.exists(module_path):
        spec = importlib.util.spec_from_file_location("graph_eval", module_path)
        graph_eval = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(graph_eval)
        GraphSearcher = graph_eval.GraphSearcher
        CPP_MODULE_AVAILABLE = True
        print(f"✅ C++模块加载成功")
    else:
        print(f"❌ 模块文件不存在: {module_path}")        
        CPP_MODULE_AVAILABLE = False
except ImportError as e:
    print(f"⚠️  C++模块加载失败: {e}")
    CPP_MODULE_AVAILABLE = False

# --- 全局数据容器 ---
GLOBAL_DATA = {}

@dataclass
class TrainingConfig:
    """训练配置参数"""
    hidden_dims: List[int] = None
    dropout_rate: float = 0.0
    
    # 训练参数
    batch_size: int = 4096
    ppo_epochs: int = 10
    learning_rate: float = 1e-4
    clip_epsilon: float = 0.1
    entropy_coef: float = 0.01
    
    gamma: float = 0.99
    gae_lambda: float = 0.95
    
    # BC 参数
    bc_epochs: int = 50
    bc_lr: float = 1e-3
    
    # 环境参数
    max_steps: int = 40
    
    max_queries_per_dataset: int = 5000
    max_timesteps_per_dataset: int = 300000 
    
    pca_dim: int = 48
    
    # --- 奖励参数 ---
    distance_improvement_scale: float = 10.0
    step_penalty: float = -0.05
    
    # 分级奖励配置
    max_rank_reward: float = 60.0  # Rank 1 (Top 1) 的奖励
    min_rank_reward: float = 30.0  # Rank 10 (Top 10) 的奖励
    
    terminal_proximity_scale: float = 50.0 
    
    success_top_k: int = 10
    
    def __post_init__(self):
        if self.hidden_dims is None:
            self.hidden_dims = [256, 128, 64]


class DatasetReader:
    @staticmethod
    def read_fvecs(filename: str, max_vectors: int = None) -> np.ndarray:
        if not os.path.exists(filename): raise FileNotFoundError(f"文件不存在: {filename}")
        file_size = os.path.getsize(filename)
        with open(filename, 'rb') as f:
            dim_bytes = f.read(4)
            dim = struct.unpack('I', dim_bytes)[0]
            vector_size = 4 + 4 * dim
            n_vecs = file_size // vector_size
            if max_vectors: n_vecs = min(n_vecs, max_vectors)
            f.seek(0)
            raw_data = f.read(n_vecs * vector_size)
        data = np.frombuffer(raw_data, dtype=np.float32)
        data = data.reshape(-1, dim + 1)
        return data[:, 1:].copy()
    
    @staticmethod
    def read_ivecs(filename: str, max_vectors: int = None) -> np.ndarray:
        if not os.path.exists(filename): raise FileNotFoundError(f"文件不存在: {filename}")
        file_size = os.path.getsize(filename)
        with open(filename, 'rb') as f:
            dim_bytes = f.read(4)
            dim = struct.unpack('I', dim_bytes)[0]
            vector_size = 4 + 4 * dim
            n_vecs = file_size // vector_size
            if max_vectors: n_vecs = min(n_vecs, max_vectors)
            f.seek(0)
            raw_data = f.read(n_vecs * vector_size)
        data = np.frombuffer(raw_data, dtype=np.int32)
        data = data.reshape(-1, dim + 1)
        return data[:, 1:].copy()


class ACPGReader:
    @staticmethod
    def load(filename: str) -> Dict[str, Any]:
        if not os.path.exists(filename): raise FileNotFoundError(f"文件不存在: {filename}")
        file_size = os.path.getsize(filename)
        is_binary = True
        if file_size < 100 * 1024 * 1024: 
            with open(filename, 'rb') as f:
                if f.read(1) == b'{': is_binary = False
        return ACPGReader._read_binary(filename) if is_binary else ACPGReader._read_json(filename)

    @staticmethod
    def _read_binary(filename: str) -> Dict[str, Any]:
        print(f"读取ACPG二进制文件: {filename}")
        with open(filename, 'rb') as f:
            version = struct.unpack('<i', f.read(4))[0]
            ntotal = struct.unpack('<q', f.read(8))[0]
            d = struct.unpack('<i', f.read(4))[0]
            f.read(7) 
            f.seek(4*9 + 8, 1)
            ph_size = struct.unpack('<Q', f.read(8))[0]
            pheromone = np.frombuffer(f.read(ph_size * 4), dtype=np.float32)
            w_size = struct.unpack('<Q', f.read(8))[0]
            weight = np.frombuffer(f.read(w_size * 4), dtype=np.float32)
            graph_K = struct.unpack('<i', f.read(4))[0]
            nb_count = struct.unpack('<Q', f.read(8))[0]
            if nb_count > 0: f.seek(nb_count * 8, 1)
            vec_count = struct.unpack('<Q', f.read(8))[0]
            vectors = np.frombuffer(f.read(vec_count * 4), dtype=np.float32).reshape(ntotal, d)
            return {'ntotal': ntotal, 'd': d, 'pheromone': pheromone, 'weight': weight, 'vectors': vectors}

    @staticmethod
    def _read_json(filename: str) -> Dict[str, Any]:
        print(f"读取ACPG JSON文件: {filename}")
        with open(filename, 'r') as f: data = json.load(f)
        ntotal = data.get('ntotal', 0)
        d = data.get('d', 0)
        vectors = np.array(data.get('vectors', []), dtype=np.float32).reshape(ntotal, d)
        return {
            'ntotal': ntotal, 'd': d,
            'weight': np.array(data.get('weight', []), dtype=np.float32),
            'pheromone': np.array(data.get('pheromone', []), dtype=np.float32),
            'vectors': vectors
        }


class LightweightPolicyNetwork(nn.Module):
    def __init__(self, state_dim: int, action_dim: int, config: TrainingConfig):
        super().__init__()
        layers = []
        input_dim = state_dim
        for hidden_dim in config.hidden_dims:
            layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.Tanh(), 
            ])
            input_dim = hidden_dim
        self.feature_extractor = nn.Sequential(*layers)
        self.actor = nn.Linear(input_dim, action_dim)
        self.critic = nn.Linear(input_dim, 1)
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.orthogonal_(module.weight, gain=np.sqrt(2))
            if module.bias is not None: module.bias.data.zero_()

    def forward(self, state):
        features = self.feature_extractor(state)
        return self.actor(features), self.critic(features)


class PCAManager:
    def __init__(self, target_dim: int = 48):
        self.target_dim = target_dim
        self.pca = None
    
    def fit_transform(self, vectors: np.ndarray) -> np.ndarray:
        if self.target_dim >= vectors.shape[1]: 
            self.target_dim = vectors.shape[1]
            return vectors
        self.pca = PCA(n_components=self.target_dim, random_state=42)
        return self.pca.fit_transform(vectors)
    
    def transform(self, vectors: np.ndarray) -> np.ndarray:
        if self.pca is None: return vectors[:, :self.target_dim]
        return self.pca.transform(vectors)


class OptimizedGraphSearchEnv(gym.Env):
    def __init__(self, config: TrainingConfig = None):
        super().__init__()
        self.config = config or TrainingConfig()
        
        self.node_vectors_original = GLOBAL_DATA['vectors']
        self.gamma_values = GLOBAL_DATA['weights']
        self.pheromone_values = GLOBAL_DATA['pheromones']
        self.neighbors = GLOBAL_DATA['neighbors']
        self.knn_num_nodes = len(self.neighbors)
        self.node_vectors_pca = GLOBAL_DATA['node_vectors_pca']
        self.queries_original = GLOBAL_DATA['queries_orig']
        self.queries_pca = GLOBAL_DATA['queries']
        # 获取 Top-K GT (用于训练时的宽泛成功判定)
        self.graph_ground_truths_topk = GLOBAL_DATA['graph_ground_truths_topk']
        # 获取 Top-1 GT (用于严格的距离对比)
        self.min_distances = GLOBAL_DATA['min_distances']
        
        self.curriculum_starts = GLOBAL_DATA['curriculum_starts']
        self.top_gamma_nodes = GLOBAL_DATA['top_gamma_nodes']
        self.incoming_edges = GLOBAL_DATA['incoming_edges']
        self.dist_scale = GLOBAL_DATA['dist_scale']
        
        self.gamma_mean = np.mean(self.gamma_values)
        self.gamma_std = np.std(self.gamma_values) + 1e-6
        self.ph_mean = np.mean(self.pheromone_values)
        self.ph_std = np.std(self.pheromone_values) + 1e-6
        
        # 状态空间
        self.max_neighbors = 20  
        self.node_feat_dim = 5  
        self.state_size = self.config.pca_dim + (self.max_neighbors + 1) * self.node_feat_dim
        
        self.observation_space = spaces.Dict({
            "state": spaces.Box(low=-10.0, high=10.0, shape=(self.state_size,), dtype=np.float32),
            "mask": spaces.Box(low=0.0, high=1.0, shape=(self.max_neighbors,), dtype=np.float32)
        })
        self.action_space = spaces.Discrete(self.max_neighbors)
        
        self.total_episodes = 0
        self.current_query_idx = 0
        self.mode = "normal"
        self.force_greedy = False
        self.reset()

    def get_state_size(self): return self.state_size

    def reset(self):
        self.total_episodes += 1
        self.current_query_idx = random.randint(0, len(self.queries_original) - 1)
        
        # 目标集合: Top-K (默认为10)
        self.target_nodes = self.graph_ground_truths_topk[self.current_query_idx]
        self.target_set = set(self.target_nodes)
        
        self.optimal_dist = self.min_distances[self.current_query_idx]
        
        total_eps = self.total_episodes
        rand_val = random.random()
        
        if rand_val < 0.2:
            potential_starts = []
            target_list = list(self.target_set)
            for target in target_list[:5]:
                for u in self.incoming_edges[target]:
                    try:
                        if self.neighbors[u].index(target) < self.max_neighbors:
                            potential_starts.append(u)
                    except ValueError: pass
                if potential_starts: break
            
            self.current_node = random.choice(potential_starts) if potential_starts else self.curriculum_starts[self.current_query_idx, 0]
            self.mode = "1hop"
            self.force_greedy = True
        elif rand_val < 0.5:
            self.current_node = random.choice(self.curriculum_starts[self.current_query_idx, :5])
            self.mode = "easy"
            self.force_greedy = False
        else:
            if random.random() < 0.5:
                self.current_node = random.choice(self.top_gamma_nodes)
            else:
                self.current_node = random.randint(0, self.knn_num_nodes - 1)
            self.mode = "normal"
            self.force_greedy = False
            
        self.query_vec_pca = self.queries_pca[self.current_query_idx]
        self.query_vec_orig = self.queries_original[self.current_query_idx]
        self.steps_taken = 0
        self.visited_nodes = {self.current_node}
        
        curr_vec = self.node_vectors_original[self.current_node]
        self.current_dist_to_target = np.linalg.norm(self.query_vec_orig - curr_vec)
        self.episode_initial_dist = self.current_dist_to_target
        self.prev_dist = self.current_dist_to_target
        
        self._sort_neighbors()
        return self._get_observation_dict()

    def _sort_neighbors(self):
        current_neighbors = self.neighbors[self.current_node]
        neighbor_dists = []
        for n_idx in current_neighbors:
            if n_idx == -1:
                neighbor_dists.append((float('inf'), n_idx))
            else:
                vec = self.node_vectors_original[n_idx]
                dist = np.linalg.norm(self.query_vec_orig - vec)
                neighbor_dists.append((dist, n_idx))
        
        sorted_neighbors = sorted(neighbor_dists, key=lambda x: x[0])
        self.sorted_neighbor_indices = [x[1] for x in sorted_neighbors]

    def _get_node_features(self, node_idx: int, is_current: bool, neighbor_pos: int) -> List[float]:
        if node_idx == -1 or node_idx >= self.knn_num_nodes:
            return [0.0] * self.node_feat_dim
            
        feats = list(self.node_vectors_pca[node_idx])
        
        node_vec_orig = self.node_vectors_original[node_idx]
        diff_orig = self.query_vec_orig - node_vec_orig
        dist_orig = np.linalg.norm(diff_orig)
        scaled_dist = np.log1p(dist_orig) 
        
        improvement = (self.current_dist_to_target - dist_orig) / self.dist_scale
        
        interaction = [
            -scaled_dist,  
            improvement, 
            1.0 if is_current else 0.0,
            1.0 if node_idx in self.visited_nodes else 0.0,
            (self.gamma_values[node_idx] - self.gamma_mean) / self.gamma_std
        ]
        return interaction

    def _get_observation_dict(self):
        obs_vec = list(self.query_vec_pca)
        nodes = [(self.current_node, True, 0)]
        padded_neighbors = self.sorted_neighbor_indices[:self.max_neighbors]
        for i, n in enumerate(padded_neighbors): nodes.append((n, False, i))
        while len(nodes) < (self.max_neighbors + 1): nodes.append((-1, False, 0))
            
        for idx, is_curr, pos in nodes:
            obs_vec.extend(self._get_node_features(idx, is_curr, pos))
            
        state = np.array(obs_vec, dtype=np.float32)
        mask = self.get_action_mask()
        return {"state": state, "mask": mask}

    def step(self, action: int):
        if action >= len(self.sorted_neighbor_indices) or action >= self.max_neighbors:
            next_node = self.current_node 
        else:
            next_node = self.sorted_neighbor_indices[action]
        
        self.current_node = next_node
        self.visited_nodes.add(self.current_node)
        self.steps_taken += 1
        self._sort_neighbors()
        
        curr_vec = self.node_vectors_original[self.current_node]
        new_dist = np.linalg.norm(self.query_vec_orig - curr_vec)
        
        # 1. 归一化距离改进奖励
        dist_improvement = (self.prev_dist - new_dist) / self.dist_scale
        reward = dist_improvement * self.config.distance_improvement_scale
        
        # 2. 步数惩罚
        reward += self.config.step_penalty
        
        # 3. 成功判定 & 分级奖励
        # 检查当前节点是否在 Target Set (Top-K) 中
        success = (self.current_node in self.target_set)
        
        if success:
            # 获取该节点在 GT 中的排名 (0 ~ K-1)
            # target_nodes 是按距离排序的 GT 列表
            rank_idx = np.where(self.target_nodes == self.current_node)[0][0]
            
            # 计算分级奖励：Rank 0 -> 60, Rank 9 -> 30 (线性插值)
            # Reward = Max - (Max - Min) * (Rank / (K-1))
            k_minus_1 = max(1, self.config.success_top_k - 1)
            rank_factor = rank_idx / k_minus_1
            rank_reward = self.config.max_rank_reward - (self.config.max_rank_reward - self.config.min_rank_reward) * rank_factor
            
            reward += rank_reward
            
        self.prev_dist = new_dist
        self.current_dist_to_target = new_dist
        
        # 训练时只要找到 Top-K 就结束，方便学习
        done = self.steps_taken >= self.config.max_steps or success
        
        if done and not success:
            if self.episode_initial_dist > 1e-6:
                reduction_ratio = max(0.0, (self.episode_initial_dist - new_dist) / self.episode_initial_dist)
                reward += reduction_ratio * self.config.terminal_proximity_scale
        
        info = {
            'success': success, 
            'mode': self.mode,
            'init_dist': self.episode_initial_dist,
            'final_dist': new_dist,
            'optimal_dist': self.optimal_dist,
            'final_node': self.current_node # 用于评估 Recall@1
        }
        return self._get_observation_dict(), reward, done, False, info

    def get_action_mask(self):
        mask = np.zeros(self.max_neighbors, dtype=np.float32)
        limit = min(len(self.sorted_neighbor_indices), self.max_neighbors)
        for i in range(limit):
            n_idx = self.sorted_neighbor_indices[i]
            if n_idx == -1: continue
            is_visited = n_idx in self.visited_nodes
            if self.force_greedy:
                vec = self.node_vectors_original[n_idx]
                dist = np.linalg.norm(self.query_vec_orig - vec)
                if dist < self.current_dist_to_target and not is_visited:
                    mask[i] = 1.0
            else:
                if not is_visited: mask[i] = 1.0
        if np.sum(mask) == 0: mask[:limit] = 1.0 
        return mask
    
    def get_state_size(self): return self.state_size
    
    def get_greedy_action(self):
        mask = self.get_action_mask()
        for i in range(len(mask)):
            if mask[i] == 1.0: return i
        return 0

class Agent:
    def __init__(self, state_dim, action_dim, config):
        self.config = config
        self.policy = LightweightPolicyNetwork(state_dim, action_dim, config)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=config.learning_rate)
        self.obs_buf, self.act_buf, self.logp_buf, self.rew_buf = [], [], [], []
        self.val_buf, self.mask_buf, self.done_buf = [], [], []
        
    def pretrain_bc(self, env, epochs=50):
        print(f"\n🧠 开始行为克隆预训练 (BC)...")
        bc_optimizer = optim.Adam(self.policy.parameters(), lr=self.config.bc_lr)
        loss_fn = nn.CrossEntropyLoss()
        
        obs_list, act_list, mask_list = [], [], []
        print(f"   收集数据中...")
        while len(obs_list) < 5000:
            obs_dict = env.reset()
            done = False
            steps = 0
            while not done and steps < 50:
                target = env.get_greedy_action()
                obs_list.append(obs_dict['state'])
                mask_list.append(obs_dict['mask'])
                act_list.append(target)
                obs_dict, _, done, _, _ = env.step(target)
                steps += 1
        
        obs_t = torch.as_tensor(np.array(obs_list), dtype=torch.float32)
        act_t = torch.as_tensor(np.array(act_list), dtype=torch.long)
        mask_t = torch.as_tensor(np.array(mask_list), dtype=torch.float32)
        
        dataset = torch.utils.data.TensorDataset(obs_t, act_t, mask_t)
        loader = torch.utils.data.DataLoader(dataset, batch_size=1024, shuffle=True)
        
        for ep in range(epochs):
            total_loss, correct, total = 0, 0, 0
            for b_s, b_a, b_m in loader:
                logits, _ = self.policy(b_s)
                logits.masked_fill_((b_m == 0), -1e10)
                loss = loss_fn(logits, b_a)
                bc_optimizer.zero_grad()
                loss.backward()
                bc_optimizer.step()
                total_loss += loss.item()
                preds = torch.argmax(logits, dim=1)
                correct += (preds == b_a).sum().item()
                total += b_a.size(0)
            
            acc = correct / total
            if (ep+1) % 5 == 0:
                print(f"   BC Epoch {ep+1} | Loss: {total_loss/len(loader):.4f} | Acc: {acc:.2%}")
            if acc > 0.98: break
        print("✅ BC 完成")

    def store(self, obs, act, logp, rew, val, mask, done):
        self.obs_buf.append(obs['state'])
        self.act_buf.append(act)
        self.logp_buf.append(logp)
        self.rew_buf.append(rew)
        self.val_buf.append(val)
        self.mask_buf.append(mask)
        self.done_buf.append(done)

    def update(self, last_val=0):
        obs = torch.as_tensor(np.array(self.obs_buf), dtype=torch.float32)
        act = torch.as_tensor(np.array(self.act_buf), dtype=torch.long)
        logp = torch.as_tensor(np.array(self.logp_buf), dtype=torch.float32)
        rew = torch.as_tensor(np.array(self.rew_buf), dtype=torch.float32)
        val = torch.as_tensor(np.array(self.val_buf), dtype=torch.float32)
        mask = torch.as_tensor(np.array(self.mask_buf), dtype=torch.float32)
        dones = torch.as_tensor(np.array(self.done_buf), dtype=torch.float32)
        
        adv = np.zeros(len(rew), dtype=np.float32)
        gae = 0
        vals = np.append(val.numpy(), last_val)
        
        for t in reversed(range(len(rew))):
            delta = rew[t] + self.config.gamma * vals[t+1] * (1 - dones[t]) - vals[t]
            gae = delta + self.config.gamma * self.config.gae_lambda * (1 - dones[t]) * gae
            adv[t] = gae
            
        adv = torch.as_tensor(adv, dtype=torch.float32)
        ret = adv + val
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        
        dataset = torch.utils.data.TensorDataset(obs, act, logp, ret, adv, mask)
        loader = torch.utils.data.DataLoader(dataset, batch_size=2048, shuffle=True)
        
        for _ in range(self.config.ppo_epochs):
            for b_obs, b_act, b_logp, b_ret, b_adv, b_mask in loader:
                logits, values = self.policy(b_obs)
                values = values.squeeze()
                logits = logits.masked_fill((b_mask == 0), -1e10)
                dist = torch.distributions.Categorical(logits=logits)
                ratio = torch.exp(dist.log_prob(b_act) - b_logp)
                surr1 = ratio * b_adv
                surr2 = torch.clamp(ratio, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon) * b_adv
                loss = -torch.min(surr1, surr2).mean() + \
                       0.5 * ((values.squeeze() - b_ret) ** 2).mean() - \
                       self.config.entropy_coef * dist.entropy().mean()
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), 0.5)
                self.optimizer.step()
        
        self.obs_buf, self.act_buf, self.logp_buf, self.rew_buf = [], [], [], []
        self.val_buf, self.mask_buf, self.done_buf = [], [], []

def run_greedy_search(env, query_vec_orig, start_node):
    """
    运行纯贪心搜索作为基线 comparison
    """
    current_node = start_node
    visited = {current_node}
    
    current_vec = env.node_vectors_original[current_node]
    current_dist = np.linalg.norm(query_vec_orig - current_vec)
    
    steps = 0
    while steps < env.config.max_steps:
        # 获取邻居
        neighbors = env.neighbors[current_node]
        best_neighbor = -1
        best_dist = current_dist
        
        found_better = False
        for n_idx in neighbors:
            if n_idx == -1 or n_idx in visited: continue
            
            n_vec = env.node_vectors_original[n_idx]
            d = np.linalg.norm(query_vec_orig - n_vec)
            if d < best_dist:
                best_dist = d
                best_neighbor = n_idx
                found_better = True
        
        if found_better:
            current_node = best_neighbor
            current_dist = best_dist
            visited.add(current_node)
            steps += 1
        else:
            break # 陷入局部最优，无法移动
            
    return current_node, steps

def evaluate_performance(env, agent, num_episodes=500):
    print(f"\n⚡ 开始推理测试 ({num_episodes} episodes)...")
    print(f"   注意：测试标准为 Recall@1 (必须找到全局最近邻)")
    
    drl_success_top1 = 0
    greedy_success_top1 = 0
    
    total_steps_drl = 0
    total_steps_greedy = 0
    
    total_time_drl = 0.0
    total_time_greedy = 0.0
    
    env.mode = "normal" 
    env.force_greedy = False 
    
    for _ in range(num_episodes):
        obs_dict = env.reset()
        
        # 记录查询和起点，供贪心算法使用
        query_vec_orig = env.query_vec_orig
        start_node = env.current_node
        
        # 获取 Top-1 真实目标
        gt_top1 = env.graph_ground_truths_topk[env.current_query_idx][0]
        
        # --- DRL Search ---
        t_start = time.time()
        done = False
        drl_final_node = start_node
        drl_steps = 0
        
        while not done:
            mask = env.get_action_mask()
            # 注意：这里转换 tensor 也算在推理时间里，因为是部署必需的
            obs_tensor = torch.as_tensor(obs_dict['state'], dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                logits, _ = agent.policy(obs_tensor)
                logits = logits.squeeze(0)
                logits.masked_fill_((torch.as_tensor(mask) == 0), -1e10)
                action = torch.argmax(logits).item()
            
            obs_dict, _, done, _, info = env.step(action)
            drl_final_node = info['final_node']
            drl_steps += 1
        total_time_drl += (time.time() - t_start)
        
        # DRL 判定：只有找到 Top-1 才算赢
        if drl_final_node == gt_top1:
            drl_success_top1 += 1
        total_steps_drl += drl_steps
        
        # --- Greedy Search Comparison ---
        t_start = time.time()
        greedy_final_node, greedy_steps = run_greedy_search(env, query_vec_orig, start_node)
        total_time_greedy += (time.time() - t_start)
        
        if greedy_final_node == gt_top1:
            greedy_success_top1 += 1
        total_steps_greedy += greedy_steps
        
    drl_acc = drl_success_top1 / num_episodes
    greedy_acc = greedy_success_top1 / num_episodes
    
    avg_steps_drl = total_steps_drl / num_episodes
    avg_steps_greedy = total_steps_greedy / num_episodes
    
    avg_time_drl = (total_time_drl / num_episodes) * 1000 # ms
    avg_time_greedy = (total_time_greedy / num_episodes) * 1000 # ms
    
    print(f"\n📊 最终对比 (Recall@1) & 耗时 (500 queries):")
    print(f"   🤖 DRL Agent: Success={drl_acc:.2%} | Steps={avg_steps_drl:.2f} | Time={avg_time_drl:.2f}ms/query | Total={total_time_drl:.4f}s")
    print(f"   🏃 Greedy   : Success={greedy_acc:.2%} | Steps={avg_steps_greedy:.2f} | Time={avg_time_greedy:.2f}ms/query | Total={total_time_greedy:.4f}s")
    
    # 评价
    print(f"\n📝 方法评价:")
    if avg_time_drl > 0 and avg_time_greedy > 0:
        if drl_acc > greedy_acc:
            print(f"   - 精度优势: DRL比贪心算法高 {(drl_acc - greedy_acc)*100:.2f} pp")
        else:
            print(f"   - 精度劣势: DRL比贪心算法低 {(greedy_acc - drl_acc)*100:.2f} pp")
            
        if avg_time_drl < avg_time_greedy:
            print(f"   - 速度优势: DRL比贪心算法快 {(avg_time_greedy/avg_time_drl):.2f}x")
        else:
            print(f"   - 速度劣势: DRL比贪心算法慢 {(avg_time_drl/avg_time_greedy):.2f}x (通常因为模型推理开销)")
            
    return drl_acc

def train_dataset(dataset_name):
    base_root = "/path/to/ACSG"
    data_root = f"{base_root}/benches/datasets"
    ds_map = {
        "sift100K": ("SIFT100K", "sift_query.fvecs", "sift_groundtruth_100k.ivecs"),
        "sift1M": ("SIFT1M", "sift_query.fvecs", "sift_groundtruth.ivecs"),
        "glove": ("GLOVE", "glove_query.fvecs", "glove_groundtruth.ivecs"),
        "gist": ("GIST", "gist_query.fvecs", "gist_groundtruth.ivecs"),
        "deep": ("DEEP", "deep_query.fvecs", "deep_groundtruth.ivecs")
    }
    if dataset_name not in ds_map: return
    dir_name, q_name, gt_name = ds_map[dataset_name]
    
    files = {
        'acpg': f"{base_root}/acpg/{dataset_name}_index/acpg_nsg.json",
        'knn': f"{base_root}/graph_processing/{dataset_name}_results/knn_12k_graph.json",
        'entry': f"{base_root}/graph_processing/{dataset_name}_results/entry_points.json",
        'query': f"{data_root}/{dir_name}/{q_name}",
        'gt': f"{data_root}/{dir_name}/{gt_name}"
    }
    for k, v in files.items(): 
        if not os.path.exists(v): return

    print(f"📥 加载全局数据 ({dataset_name})...")
    acpg_data = ACPGReader.load(files['acpg'])
    with open(files['entry'], 'r') as f: combined_centers = json.load(f).get('combined_centers', [])
    
    GLOBAL_DATA['vectors'] = acpg_data['vectors'][combined_centers]
    GLOBAL_DATA['weights'] = acpg_data['weight'][combined_centers]
    GLOBAL_DATA['pheromones'] = acpg_data['pheromone'][combined_centers]
    
    with open(files['knn'], 'r') as f: knn_data = json.load(f)
    GLOBAL_DATA['neighbors'] = knn_data.get('knn_12k_graph', knn_data.get('neighbors'))
    
    incoming = defaultdict(list)
    for u, nbrs in enumerate(GLOBAL_DATA['neighbors']):
        for v in nbrs: 
            if v != -1: incoming[v].append(u)
    GLOBAL_DATA['incoming_edges'] = incoming
    
    vecs = GLOBAL_DATA['vectors']
    idx = np.random.choice(len(vecs), min(2000, len(vecs)), replace=False)
    if len(idx) % 2 != 0: idx = idx[:-1]
    v = vecs[idx]
    dist_scale = np.mean(np.linalg.norm(v[:len(v)//2] - v[len(v)//2:], axis=1))
    GLOBAL_DATA['dist_scale'] = max(1.0, dist_scale)
    print(f"📊 Avg Dist: {dist_scale:.2f}")
    
    config = TrainingConfig()
    pca = PCAManager(target_dim=config.pca_dim)
    GLOBAL_DATA['node_vectors_pca'] = pca.fit_transform(GLOBAL_DATA['vectors'])
    GLOBAL_DATA['top_gamma_nodes'] = np.argsort(GLOBAL_DATA['weights'])[-100:].tolist()
    
    queries = DatasetReader.read_fvecs(files['query'], config.max_queries_per_dataset)
    GLOBAL_DATA['queries_orig'] = queries
    GLOBAL_DATA['queries'] = pca.transform(queries)
    
    dists = pairwise_distances(queries, GLOBAL_DATA['vectors'])
    # 关键：计算 Top-K
    GLOBAL_DATA['graph_ground_truths_topk'] = np.argsort(dists, axis=1)[:, :config.success_top_k]
    GLOBAL_DATA['min_distances'] = dists[np.arange(dists.shape[0]), GLOBAL_DATA['graph_ground_truths_topk'][:, 0]]
    GLOBAL_DATA['curriculum_starts'] = np.argsort(dists, axis=1)[:, :20]
    
    env = OptimizedGraphSearchEnv(config)
    agent = Agent(env.get_state_size(), env.action_space.n, config)
    
    agent.pretrain_bc(env, epochs=30)
    
    print(f"🚀 开始 PPO 训练...")
    obs_dict = env.reset()
    global_step = 0
    ep_count = 0
    ep_rew = 0
    
    while global_step < config.max_timesteps_per_dataset:
        obs = obs_dict['state']
        mask = obs_dict['mask']
        obs_tensor = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            logits, val = agent.policy(obs_tensor)
            logits = logits.squeeze(0)
            logits.masked_fill_((torch.as_tensor(mask) == 0), -1e10)
            dist = torch.distributions.Categorical(logits=logits)
            action = dist.sample()
            logp = dist.log_prob(action)
        
        next_obs_dict, rew, done, _, info = env.step(action.item())
        
        agent.store(obs_dict, action.item(), logp.item(), rew, val.item(), mask, done)
        
        obs_dict = next_obs_dict
        ep_rew += rew
        global_step += 1
        
        if len(agent.obs_buf) >= config.batch_size:
            with torch.no_grad():
                _, last_val = agent.policy(torch.as_tensor(obs_dict['state'], dtype=torch.float32).unsqueeze(0))
                last_val = last_val.item()
            agent.update(last_val)
            
        if done:
            ep_count += 1
            if ep_count % 50 == 0:
                print(f"Step {global_step} | Ep {ep_count} | Mode: {info['mode']} | Reward: {ep_rew:.2f} | Success: {info['success']}")
            ep_rew = 0
            obs_dict = env.reset()

    output_dir = f"{base_root}/drl/{dataset_name}_results"
    os.makedirs(output_dir, exist_ok=True)
    torch.save(agent.policy.state_dict(), f"{output_dir}/drl_search_model.pth")
    dummy = torch.randn(1, env.get_state_size())
    torch.onnx.export(agent.policy, dummy, f"{output_dir}/drl_policy.onnx", 
                      input_names=['state'], output_names=['logits', 'val'],
                      dynamic_axes={'state': {0: 'batch'}, 'logits': {0: 'batch'}})
    print(f"✅ 模型已保存至 {output_dir}")
    
    evaluate_performance(env, agent, 500)

if __name__ == "__main__":
    os.environ["OMP_NUM_THREADS"] = "16"
    torch.set_num_threads(4)
    datasets = ["sift100K", "sift1M", "glove", "gist", "deep"]
    for ds in datasets: train_dataset(ds)
import torch
import torch.nn.functional as F
from torch import nn


class InfoNCE(nn.Module):
    """
    标准 InfoNCE 对比损失（多负样本版本）。

    forward 参数：
        query_emb : [B, D]        —— 已 L2 归一化的 Query 编码
        pos_emb   : [B, D]        —— 已 L2 归一化的正样本 Hub 编码
        neg_embs  : [B, N, D]     —— 已 L2 归一化的 N 个负样本 Hub 编码
                    也接受 [B, D]（单负样本，自动 unsqueeze）

    Loss = -log( exp(sim(q, pos)/τ) / (exp(sim(q, pos)/τ) + Σ exp(sim(q, neg_i)/τ)) )
    等价于 CrossEntropy(logits, label=0)，其中 logits[0] 对应正样本。
    """
    def __init__(self, temperature=0.07):
        super(InfoNCE, self).__init__()
        self.temperature = temperature

    def forward(self, query_emb, pos_emb, neg_embs):
        # L2 归一化，保证余弦相似度用点积即可
        query_emb = F.normalize(query_emb, dim=-1)           # [B, D]
        pos_emb   = F.normalize(pos_emb,   dim=-1)           # [B, D]

        # 兼容单负样本输入
        if neg_embs.dim() == 2:
            neg_embs = neg_embs.unsqueeze(1)                 # [B, 1, D]
        neg_embs = F.normalize(neg_embs, dim=-1)             # [B, N, D]

        # 正样本相似度 [B, 1]
        pos_sim = (query_emb * pos_emb).sum(dim=-1, keepdim=True) / self.temperature

        # 负样本相似度 [B, N]：bmm([B,N,D], [B,D,1]) -> [B,N,1] -> [B,N]
        neg_sim = torch.bmm(
            neg_embs,                        # [B, N, D]
            query_emb.unsqueeze(-1)          # [B, D, 1]
        ).squeeze(-1) / self.temperature     # [B, N]

        # 拼接 logits：第 0 列是正样本（label=0）
        logits = torch.cat([pos_sim, neg_sim], dim=1)        # [B, 1+N]
        labels = torch.zeros(logits.shape[0], dtype=torch.long, device=query_emb.device)

        loss = F.cross_entropy(logits, labels)
        return loss

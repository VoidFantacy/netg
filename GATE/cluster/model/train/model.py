import torch
import torch.nn as nn
import torch.nn.functional as F

from cluster.model.train.fusion import TransformerFusion


class Model(nn.Module):
    """Hub Tower: 融合 node_feature + graph_feature → hub embedding"""
    def __init__(self, input_dim, hidden_dim, output_dim, dropout, num_layers=2, num_heads=4):
        super(Model, self).__init__()
        # graph_feature 与 node_feature 维度相同（均为 input_dim）
        # TransformerFusion: x1=graph_feature 经 fc1 投影，x2=node_feature 作主特征
        self.fusion = TransformerFusion(input_dim, input_dim, hidden_dim)

        self.linear1  = nn.Linear(hidden_dim, hidden_dim)
        self.relu1    = nn.ReLU()
        self.dropout1 = nn.Dropout(dropout)

        # TransformerEncoder 不能放进 nn.Sequential，需在 forward 中单独调用
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim, nhead=num_heads,
            dim_feedforward=hidden_dim * 4, dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.relu2    = nn.ReLU()
        self.dropout2 = nn.Dropout(dropout)

        self.linear2  = nn.Linear(hidden_dim, hidden_dim)
        self.relu3    = nn.ReLU()
        self.dropout3 = nn.Dropout(dropout)

        self.linear3  = nn.Linear(hidden_dim, output_dim)

    def forward(self, node_feature, graph_feature):
        # 与作者一致: node_feature 作 x1（经 fc1 投影），graph_feature 作 x2（主特征）
        # TransformerFusion 取 x[:, -1, :] 即 x2 位置的输出
        x = self.fusion(node_feature, graph_feature)          # [B, hidden_dim]
        x = self.dropout1(self.relu1(self.linear1(x)))        # [B, hidden_dim]
        x = x.unsqueeze(1)                                    # [B, 1, hidden_dim]
        x = self.transformer(x)                               # [B, 1, hidden_dim]
        x = x.squeeze(1)                                      # [B, hidden_dim]
        x = self.dropout2(self.relu2(x))
        x = self.dropout3(self.relu3(self.linear2(x)))
        x = self.linear3(x)                                   # [B, output_dim]
        return x


class QueryEncoder(nn.Module):
    """Query Tower: 将 query 向量编码到与 hub embedding 相同的空间"""
    def __init__(self, input_dim, hidden_dim, output_dim, dropout):
        super(QueryEncoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, query):
        return self.encoder(query)

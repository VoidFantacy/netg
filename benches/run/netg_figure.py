# -*- coding: utf-8 -*-
"""
NETG: Offline Topological Distillation Pipeline - Figure 1 (v7)
- Panel 1: ACO amber lines are curved with arrows (FancyArrowPatch)
- Panel 2: 5 hubs spaced out, no DASP, no overlap
- Panel 3: green arrow curves below void, labels repositioned
Run:    python draw.py
"""

import matplotlib.pyplot as plt
from matplotlib.patches import (FancyArrowPatch, Ellipse, FancyBboxPatch,
                                 Rectangle, Circle)
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patheffects as pe
import networkx as nx
import numpy as np

# ============================================================
# 风格
# ============================================================
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 13,
    'axes.unicode_minus': False,
})

NAVY      = '#1f3a5f'
AMBER     = '#e0a040'
GRAY_E    = '#a0a0a0'
GRAY_N    = '#c8c8c8'
GRAY_LT   = '#dddddd'
RED       = '#c44545'
RED_DK    = '#7a2222'
GREEN     = '#2ea54a'
CARD_EDGE = '#d0d0d0'
CARD_BG   = '#fafafa'

# ============================================================
# 数据：泊松圆盘采样（有机分布）
# ------------------------------------------------------------
# 关键：sample 区域的 aspect 要匹配 cell aspect（计算见下文）
# figsize=(18, 6.8)，cell W/H ≈ 1.13，所以采样区也用 1.13 的 aspect
# ============================================================
np.random.seed(11)

def poisson_disk_sample(n_target, x_range, y_range, min_dist=0.25,
                         max_attempts=3000):
    pts = []
    attempts = 0
    while len(pts) < n_target and attempts < max_attempts:
        x = np.random.uniform(*x_range)
        y = np.random.uniform(*y_range)
        ok = True
        for px, py in pts:
            if (x - px) ** 2 + (y - py) ** 2 < min_dist ** 2:
                ok = False
                break
        if ok:
            pts.append((x, y))
        attempts += 1
    return np.array(pts)

# 采样区与 XLIM/YLIM 一致比例
SAMPLE_X = (-1.32, 1.32)
SAMPLE_Y = (-1.10, 1.10)
coords = poisson_disk_sample(
    n_target=90, x_range=SAMPLE_X, y_range=SAMPLE_Y, min_dist=0.235)
n_nodes = len(coords)
pos = {i: tuple(coords[i]) for i in range(n_nodes)}

# kNN 建边
G = nx.Graph()
G.add_nodes_from(range(n_nodes))
for i in range(n_nodes):
    d = np.linalg.norm(coords - coords[i], axis=1)
    nbrs = np.argsort(d)[1:5]
    for j in nbrs:
        G.add_edge(i, int(j))


# ============================================================
# 工具
# ============================================================
def add_card(ax, pad=0.012):
    rect = FancyBboxPatch(
        (pad, pad), 1 - 2*pad, 1 - 2*pad,
        boxstyle="round,pad=0.0,rounding_size=0.018",
        linewidth=0.8, edgecolor=CARD_EDGE, facecolor='white',
        transform=ax.transAxes, zorder=0, clip_on=False)
    ax.add_patch(rect)


def panel_header(ax, idx, title):
    circ = Circle((0.05, 0.94), 0.026,
                  transform=ax.transAxes, color=NAVY,
                  zorder=10, clip_on=False)
    ax.add_patch(circ)
    ax.text(0.05, 0.94, str(idx), transform=ax.transAxes,
            ha='center', va='center', color='white',
            fontsize=15.5, fontweight='bold', zorder=11)
    ax.text(0.092, 0.94, title, transform=ax.transAxes,
            ha='left', va='center', color=NAVY,
            fontsize=18, fontweight='bold', zorder=11)


def panel_caption(ax, text):
    ax.text(0.5, 0.04, text, transform=ax.transAxes,
            ha='center', va='center', fontsize=13.5,
            color='#444')


def clean_axes(ax):
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def draw_mini_graph_around(ax, center, n_satellites=5, radius=0.022,
                           sat_size=12, edge_color='#aaa', sat_color=GRAY_N,
                           seed=0, x_squash=1.0, y_squash=0.5):
    rng = np.random.default_rng(seed)
    angles = np.linspace(0, 2*np.pi, n_satellites, endpoint=False)
    angles += rng.uniform(-0.3, 0.3, n_satellites)
    radii = radius * rng.uniform(0.7, 1.1, n_satellites)
    for a, r in zip(angles, radii):
        sx = center[0] + r * np.cos(a) * x_squash
        sy = center[1] + r * np.sin(a) * y_squash
        ax.plot([center[0], sx], [center[1], sy],
                color=edge_color, lw=0.6, alpha=0.6, zorder=2.5)
        ax.scatter(sx, sy, s=sat_size, color=sat_color,
                   edgecolors='#888', linewidths=0.3, zorder=3)


def draw_mini_mlp(ax, x, y, w, h, dashed=True):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.005,rounding_size=0.008",
        linewidth=0.7, edgecolor='#aaa', facecolor='#f5f5f5',
        linestyle='--' if dashed else '-', zorder=5)
    ax.add_patch(box)
    layer_sizes = [3, 4, 3]
    layer_xs = np.linspace(x + w*0.18, x + w*0.55, len(layer_sizes))
    nodes_pos = []
    for li, (lx, ls) in enumerate(zip(layer_xs, layer_sizes)):
        ys = np.linspace(y + h*0.25, y + h*0.75, ls)
        nodes_pos.append([(lx, yy) for yy in ys])
    for li in range(len(nodes_pos) - 1):
        for n1 in nodes_pos[li]:
            for n2 in nodes_pos[li + 1]:
                ax.plot([n1[0], n2[0]], [n1[1], n2[1]],
                        color='#bbb', lw=0.4, zorder=6)
    for layer in nodes_pos:
        for nx_, ny_ in layer:
            ax.scatter(nx_, ny_, s=18, color='#d8d8d8',
                       edgecolors='#888', linewidths=0.4, zorder=7)


def fit_oval_to_points(pts, padding=0.10):
    cx = (pts[:, 0].min() + pts[:, 0].max()) / 2
    cy = (pts[:, 1].min() + pts[:, 1].max()) / 2
    w = (pts[:, 0].max() - pts[:, 0].min()) + padding * 2
    h = (pts[:, 1].max() - pts[:, 1].min()) + padding * 2
    return cx, cy, max(w, 0.4), max(h, 0.4)


# ============================================================
# Figure 主体
# ------------------------------------------------------------
# 关键：figsize 选择让 cell aspect 与 data aspect 匹配
# 使得 set_aspect('equal') 后 axes 能完整填满 cell（card 不缩水）
# ============================================================
fig = plt.figure(figsize=(18, 6.8), facecolor='white')
gs = fig.add_gridspec(
    4, 3,
    height_ratios=[0.10, 1, 0.085, 0.09],
    hspace=0.04, wspace=0.022,
    left=0.012, right=0.988, top=0.985, bottom=0.012
)

# ---------- 总标题 ----------
ax_title = fig.add_subplot(gs[0, :])
ax_title.axis('off')
ax_title.text(0.5, 0.5, 'NETG: Offline Topological Distillation Pipeline',
              ha='center', va='center', fontsize=27,
              fontweight='bold', color=NAVY, transform=ax_title.transAxes)

# 共享坐标
XLIM = (-1.45, 1.45)
YLIM = (-1.28, 1.28)

# ===========================================================
# Panel 1: ACO Backbone Mining
# ===========================================================
ax1 = fig.add_subplot(gs[1, 0])
clean_axes(ax1)
add_card(ax1)
panel_header(ax1, 1, 'ACO Path Mining')
ax1.set_xlim(*XLIM); ax1.set_ylim(*YLIM)
ax1.set_aspect('equal', adjustable='box')

nx.draw_networkx_edges(G, pos, ax=ax1, edge_color=GRAY_E,
                       width=0.85, alpha=0.65)
nx.draw_networkx_nodes(G, pos, ax=ax1, node_size=70,
                       node_color=GRAY_N, edgecolors='#666',
                       linewidths=0.6)

# 4 条 ACO 主干（弯曲 + 箭头）
def find_diverse_long_paths(G, n_paths=4, min_len=8, seed=2):
    rng = np.random.default_rng(seed)
    paths = []
    used_nodes = set()
    for _ in range(80):
        s, t = rng.choice(n_nodes, 2, replace=False)
        try:
            p = nx.shortest_path(G, source=int(s), target=int(t))
        except nx.NetworkXNoPath:
            continue
        if len(p) < min_len:
            continue
        overlap = len(set(p) & used_nodes)
        if overlap < len(p) * 0.5:
            paths.append(p)
            used_nodes.update(p)
            if len(paths) >= n_paths:
                break
    return paths

backbones = find_diverse_long_paths(G, n_paths=4, min_len=7)
for path in backbones:
    # 用 FancyArrowPatch + connectionstyle 画弯曲带箭头的 ACO 路径
    for i in range(len(path) - 1):
        p_start = pos[path[i]]
        p_end = pos[path[i + 1]]
        # 交替弯曲方向，增加有机感
        rad = 0.25 if i % 2 == 0 else -0.25
        arr = FancyArrowPatch(
            p_start, p_end,
            arrowstyle='-|>', color=AMBER, lw=2.2, alpha=0.92,
            mutation_scale=10, shrinkA=4, shrinkB=4,
            connectionstyle=f"arc3,rad={rad}", zorder=4)
        ax1.add_patch(arr)

# 高 w_i 节点（在主干交叉点附近高亮）
backbone_node_count = {}
for path in backbones:
    for n in path:
        backbone_node_count[n] = backbone_node_count.get(n, 0) + 1
hot_nodes = [n for n, c in backbone_node_count.items() if c >= 2][:3]
for n in hot_nodes:
    ax1.scatter(*pos[n], s=140, facecolor=AMBER,
                edgecolor='#8a5a14', linewidth=1.0, zorder=6)

panel_caption(ax1, r'Pheromone $w_i$ accumulates' + '\n' +
                   r'along high-traffic routing paths.')

# ===========================================================
# Panel 2: Topological Hub Selection
# ===========================================================
ax2 = fig.add_subplot(gs[1, 1])
clean_axes(ax2)
add_card(ax2)
panel_header(ax2, 2, 'Topological Hub Selection')
ax2.set_xlim(*XLIM); ax2.set_ylim(*YLIM)
ax2.set_aspect('equal', adjustable='box')

nx.draw_networkx_edges(G, pos, ax=ax2, edge_color=GRAY_LT,
                       width=0.5, alpha=0.6)

# 5 个 hub 锚点（适中间距）
hub_anchors = [
    (-0.95, 0.70),  ( 0.30, 0.75), ( 1.05, 0.45),
    (-0.55, -0.55), ( 0.80, -0.60),
]
hubs = []
used = set()
for tx, ty in hub_anchors:
    d = np.linalg.norm(coords - np.array([tx, ty]), axis=1)
    for cand in np.argsort(d):
        if int(cand) not in used:
            hubs.append(int(cand))
            used.add(int(cand))
            break

# Voronoi 分配
hub_coords = np.array([coords[h] for h in hubs])
hub_members = {h: [] for h in hubs}
for i in range(n_nodes):
    if i in hubs:
        continue
    d = np.linalg.norm(hub_coords - coords[i], axis=1)
    nearest_hub = hubs[int(np.argmin(d))]
    hub_members[nearest_hub].append(i)

# 底层灰节点
nx.draw_networkx_nodes(G, pos, ax=ax2, node_size=38,
                       node_color=GRAY_N, edgecolors='#aaa',
                       linewidths=0.4, alpha=0.85)

# === 三级聚类中心体系（大/中/小）===
# 大 hub: 5 个主聚类中心
hub_pos_dict = {h: pos[h] for h in hubs}
nx.draw_networkx_nodes(G, hub_pos_dict, ax=ax2, nodelist=hubs,
                       node_size=480, node_color=NAVY,
                       edgecolors='white', linewidths=2.0)
for h in hubs:
    txt = ax2.text(pos[h][0], pos[h][1] + 0.16, 'Hub',
                   ha='center', va='bottom',
                   fontsize=13, color=NAVY, fontweight='bold', zorder=8)
    txt.set_path_effects([pe.withStroke(linewidth=3, foreground='white')])

# 中 hub: 每个大 hub 簇里选 1 个中等距离节点
mid_hubs = []
for h, members in hub_members.items():
    if len(members) < 5:
        continue
    d_to_hub = sorted([(m, np.linalg.norm(coords[h] - coords[m]))
                       for m in members], key=lambda x: x[1])
    # 取 1/3 位置的节点
    idx = len(d_to_hub) // 3
    mid_hubs.append(d_to_hub[idx][0])

for mh in mid_hubs:
    ax2.scatter(*pos[mh], s=240, color='#3d6a8f', alpha=0.85,
                edgecolors='white', linewidths=1.2, zorder=6)

# 小 hub: 每个大 hub 簇里选 1~2 个更远的节点
small_hubs = []
for h, members in hub_members.items():
    if len(members) < 4:
        continue
    d_to_hub = sorted([(m, np.linalg.norm(coords[h] - coords[m]))
                       for m in members], key=lambda x: x[1])
    # 取 2/3 位置和末尾附近
    used_in_mid = set(mid_hubs)
    candidates = [(m, d) for m, d in d_to_hub if m not in used_in_mid]
    if len(candidates) >= 3:
        idx1 = len(candidates) * 2 // 3
        small_hubs.append(candidates[idx1][0])
    if len(candidates) >= 5:
        idx2 = len(candidates) - 2
        small_hubs.append(candidates[idx2][0])

for sh in small_hubs:
    ax2.scatter(*pos[sh], s=120, color='#7a9db5', alpha=0.9,
                edgecolors='white', linewidths=0.8, zorder=6)

# === DPC 层级指向：小 → 最近中/大，中 → 最近大 ===
# 所有中心及其 tier (大=3, 中=2, 小=1)
all_centers = []
for h in hubs:
    all_centers.append((h, 3))
for mh in mid_hubs:
    all_centers.append((mh, 2))
for sh in small_hubs:
    all_centers.append((sh, 1))

# 每个中心指向离自己最近的、比自己大一级(或更高)的中心
for node, tier in all_centers:
    if tier == 3:
        continue  # 最大级不指向任何人
    # 找所有 tier 比自己大的中心
    higher = [(n, t) for n, t in all_centers if t > tier]
    if not higher:
        continue
    # 找最近的
    node_coord = coords[node]
    min_dist = float('inf')
    target = None
    for n, t in higher:
        d = np.linalg.norm(node_coord - coords[n])
        if d < min_dist:
            min_dist = d
            target = n
    if target is not None:
        arr = FancyArrowPatch(
            pos[node], pos[target],
            arrowstyle='-|>', color=NAVY, lw=1.4, alpha=0.6,
            mutation_scale=11, shrinkA=7, shrinkB=11,
            connectionstyle="arc3,rad=0.12",
            linestyle='--', zorder=5)
        ax2.add_patch(arr)

panel_caption(ax2, 'Density peaks on high-traffic routing paths,\n'
                   'not geometric centroids.')

# ===========================================================
# Panel 3: Asymmetric Metric Learning
# ===========================================================
ax3 = fig.add_subplot(gs[1, 2])
clean_axes(ax3)
add_card(ax3)
panel_header(ax3, 3, 'Asymmetric Metric Learning')
ax3.set_xlim(0, 1); ax3.set_ylim(0, 1)


def draw_subpanel(ax, y_top, y_bot, label, mode):
    box = FancyBboxPatch(
        (0.04, y_bot), 0.92, y_top - y_bot,
        boxstyle="round,pad=0.0,rounding_size=0.012",
        linewidth=0.7, edgecolor='#bbb',
        facecolor=CARD_BG, zorder=1)
    ax.add_patch(box)
    ax.text(0.07, y_top - 0.025, label, fontsize=11.5, color='#333',
            fontweight='bold', zorder=10)

    cy = (y_top + y_bot) / 2 - 0.012
    q_pos = (0.10, cy)
    A_pos = (0.27, cy + 0.022)
    B_pos = (0.90, cy - 0.018)

    # ---- Geometric Void：清晰椭圆，居中 ----
    void_cx, void_cy = 0.575, cy + 0.005
    void_w, void_h = 0.30, 0.13
    void = Ellipse((void_cx, void_cy), width=void_w, height=void_h,
                   facecolor='#cfcfcf', alpha=0.55,
                   edgecolor='#888', linewidth=0.9,
                   linestyle=(0, (3, 2)), zorder=2)
    ax.add_patch(void)
    # Void 标签贴顶（远离绿箭头路径）
    ax.text(void_cx, void_cy + void_h/2 - 0.012, 'Sparse Gap',
            ha='center', va='center',
            fontsize=9.5, color='#555', style='italic', zorder=3)

    # ---- Hub 周围小图（不会进入 void） ----
    draw_mini_graph_around(ax, A_pos, n_satellites=5,
                           radius=0.022, sat_size=12,
                           seed=10 if mode == 'before' else 11)
    draw_mini_graph_around(ax, B_pos, n_satellites=5,
                           radius=0.022, sat_size=12,
                           seed=20 if mode == 'before' else 21)

    # ---- Query / Hub-A / Hub-B ----
    ax.scatter(*q_pos, marker='D', s=240, color=RED,
               edgecolors=RED_DK, linewidths=1.3, zorder=5)
    txt = ax.text(q_pos[0], q_pos[1] + 0.058, 'Query q',
                  ha='center', fontsize=11, color=RED,
                  fontweight='bold', zorder=6, fontstyle='italic')
    txt.set_path_effects([pe.withStroke(linewidth=3, foreground=CARD_BG)])

    ax.scatter(*A_pos, s=400, color=NAVY, edgecolors='white',
               linewidths=1.8, zorder=5)
    txt = ax.text(A_pos[0], A_pos[1] + 0.062, 'Hub-A',
                  ha='center', fontsize=11, color=NAVY,
                  fontweight='bold', zorder=6)
    txt.set_path_effects([pe.withStroke(linewidth=3, foreground=CARD_BG)])

    ax.scatter(*B_pos, s=400, color=NAVY, edgecolors='white',
               linewidths=1.8, zorder=5)
    txt = ax.text(B_pos[0], B_pos[1] + 0.062, 'Hub-B',
                  ha='center', fontsize=11, color=NAVY,
                  fontweight='bold', zorder=6)
    txt.set_path_effects([pe.withStroke(linewidth=3, foreground=CARD_BG)])

    if mode == 'before':
        # 红虚线 q -> Hub-A
        arr = FancyArrowPatch(q_pos, A_pos,
                              arrowstyle='-|>', color=RED, lw=2.2,
                              linestyle='--', mutation_scale=16,
                              shrinkA=10, shrinkB=14, zorder=4)
        ax.add_patch(arr)
        ax.text((q_pos[0] + A_pos[0]) / 2, q_pos[1] - 0.058,
                'rank=1\n(nearest, suboptimal)',
                ha='center', fontsize=9, color=RED, zorder=6,
                fontweight='bold')

        # 灰色虚线 q -> Hub-B（弧形绕过 void 上方）
        arr2 = FancyArrowPatch(q_pos, B_pos,
                               arrowstyle='->', color='#bbb', lw=1.0,
                               linestyle=':', mutation_scale=10,
                               shrinkA=10, shrinkB=14, zorder=3,
                               connectionstyle="arc3,rad=0.30")
        ax.add_patch(arr2)
        ax.text(B_pos[0], B_pos[1] + 0.10, 'true optimal entry',
                ha='center', fontsize=9, color='#888', style='italic')

    else:  # after
        # 绿色实线 q -> Hub-B (向下弧形，绕过 void 下方)
        arr = FancyArrowPatch(q_pos, B_pos,
                              arrowstyle='-|>', color=GREEN, lw=3.0,
                              mutation_scale=20,
                              shrinkA=10, shrinkB=14, zorder=4,
                              connectionstyle="arc3,rad=-0.18")
        ax.add_patch(arr)
        # rank=1 标签放在弧形最低点附近
        ax.text(0.55, cy - 0.075,
                r'rank=1 under $\phi_\theta$',
                ha='center', fontsize=11, color=GREEN,
                fontweight='bold', zorder=6,
                path_effects=[pe.withStroke(linewidth=3, foreground='white')])

        ax.text(q_pos[0], q_pos[1] - 0.072,
                'q unchanged\n(identity)',
                ha='center', fontsize=9, color='#555', style='italic')
        ax.text(B_pos[0], B_pos[1] - 0.075,
                r'$\phi_\theta$(Hub-B)' + '\nre-ranked to top-1',
                ha='center', fontsize=9, color='#555')


draw_subpanel(ax3, 0.88, 0.53, 'Before: Raw Euclidean Metric', 'before')

ax3.annotate('', xy=(0.5, 0.50), xytext=(0.5, 0.53),
             arrowprops=dict(arrowstyle='-|>', color=NAVY, lw=2.4,
                             mutation_scale=24))
ax3.text(0.535, 0.515, r'$\phi_\theta$ projection (offline)',
         fontsize=11, color=NAVY, va='center', fontweight='bold')

draw_subpanel(ax3, 0.48, 0.13, 'After: Learned Asymmetric Metric', 'after')

ax3.text(0.30, 0.075,
         'Void unchanged — asymmetric metric\n'
         're-ranks the optimal hub to top-1.',
         ha='center', fontsize=10, color='#333',
         transform=ax3.transAxes)

draw_mini_mlp(ax3, x=0.62, y=0.025, w=0.22, h=0.085, dashed=True)
ax3.text(0.86, 0.067, 'discarded\nat inference',
         ha='left', va='center', fontsize=8.5,
         color='#888', style='italic', zorder=8)

# ===========================================================
# Legend
# ===========================================================
ax_leg = fig.add_subplot(gs[2, :])
ax_leg.set_xlim(0, 1); ax_leg.set_ylim(0, 1)
ax_leg.axis('off')

legend_items = [
    ('●', NAVY, 24, 'Hub'),
    ('◆', RED, 19, 'Query'),
    ('▮', '#cfcfcf', 22, 'Sparse Gap'),
    ('▬', AMBER, 24, 'ACO trail'),
]
total_x_span = 0.36
start_x = (1 - total_x_span) / 2
spacing = total_x_span / len(legend_items)
y_pos = 0.5
for i, (sym, col, sz, lbl) in enumerate(legend_items):
    cx = start_x + i * spacing
    ax_leg.text(cx, y_pos, sym, color=col, fontsize=sz,
                ha='left', va='center', transform=ax_leg.transAxes)
    ax_leg.text(cx + 0.020, y_pos, lbl, fontsize=13.5,
                color='#333', ha='left', va='center',
                transform=ax_leg.transAxes)

# ===========================================================
# 底部 Online Serving 横条
# ===========================================================
ax_bar = fig.add_subplot(gs[3, :])
ax_bar.set_xlim(0, 1); ax_bar.set_ylim(0, 1)
ax_bar.axis('off')
bar = FancyBboxPatch(
    (0.005, 0.05), 0.99, 0.9,
    boxstyle="round,pad=0.0,rounding_size=0.06",
    facecolor=NAVY, edgecolor='none')
ax_bar.add_patch(bar)
ax_bar.text(
    0.5, 0.5,
    r'$\bf{Online\ Serving:}$    query (raw space)    $\longrightarrow$    '
    r'$\bf{Micro\!-\!HNSW}$ on projected hubs '
    r'(cache-friendly, zero neural cost)    $\longrightarrow$    '
    'greedy search on base graph',
    ha='center', va='center', color='white', fontsize=15)

# ===========================================================
# 输出
# ===========================================================
fig.savefig('netg_figure.pdf', bbox_inches='tight', dpi=300)
fig.savefig('netg_figure.png', bbox_inches='tight', dpi=200)
fig.savefig('netg_figure.svg', bbox_inches='tight')
print('Done. Output: netg_figure.pdf + netg_figure.png + netg_figure.svg')
plt.show()

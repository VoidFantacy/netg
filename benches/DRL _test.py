import os
import json
import random
import datetime
import numpy as np
import matplotlib.pyplot as plt
import torch
from typing import Dict, Any, List, Tuple

# 导入主程序中的核心类
from graph_drl import (
    CPUGraphSearchAgent,
    OptimizedGraphSearchEnv,
    TrainingConfig,
    DATASET_PATHS
)


class SearchLTester:
    """search_L参数性能测试器"""
    
    def __init__(self, model_path: str, dataset: str):
        """
        初始化测试器
        :param model_path: 训练好的模型路径
        :param dataset: 测试数据集名称
        """
        self.model_path = model_path
        self.dataset = dataset
        self.agent = None
        self.env = None
        self.config = None
        
        # 验证输入
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        if dataset not in DATASET_PATHS:
            raise ValueError(f"未知数据集: {dataset}，支持的数据集: {list(DATASET_PATHS.keys())}")
        
        # 初始化环境和智能体
        self._init_env_and_agent()
    
    def _init_env_and_agent(self) -> None:
        """初始化环境和智能体"""
        print(f"初始化测试环境和智能体...")
        
        # 加载模型检查点获取配置
        checkpoint = torch.load(self.model_path, map_location='cpu')
        self.config = checkpoint.get('config', TrainingConfig())
        
        # 获取数据集路径配置
        dataset_config = DATASET_PATHS[self.dataset]
        base_root = "/path/to/ACSG"
        data_root = "/path/to/ACSG/benches/datasets"
        
        # 重建环境所需文件路径
        acpg_file = f"{base_root}/acpg/{self.dataset}_index/acpg_nsg.json"
        knn_12k_file = f"{base_root}/graph_processing/{self.dataset}_results/knn_12k_graph.json"
        entry_points_file = f"{base_root}/graph_processing/{self.dataset}_results/entry_points.json"
        query_path = f"{data_root}/{dataset_config['dataset_dir']}/{dataset_config['query_path']}"
        gt_path = f"{data_root}/{dataset_config['dataset_dir']}/{dataset_config['gt_path']}"
        
        # 验证环境文件
        required_files = [acpg_file, knn_12k_file, entry_points_file, query_path, gt_path]
        for file in required_files:
            if not os.path.exists(file):
                raise FileNotFoundError(f"环境依赖文件缺失: {file}")
        
        # 创建环境
        self.env = OptimizedGraphSearchEnv(
            acpg_file=acpg_file,
            knn_12k_file=knn_12k_file,
            entry_points_file=entry_points_file,
            query_path=query_path,
            gt_path=gt_path,
            config=self.config,
            cpp_index_file=acpg_file
        )
        
        # 创建智能体并加载模型
        self.agent = CPUGraphSearchAgent(self.env, self.config)
        self.agent.load_model(self.model_path)
        
        print(f"环境和智能体初始化完成:")
        print(f"  - 数据集: {self.dataset}")
        print(f"  - 模型路径: {self.model_path}")
        print(f"  - 向量维度: {self.env.vector_dim}")
        print(f"  - 初始入口点: 原始ID={self.env.initial_node['original_id']}")
    
    def test_search_L_performance(self, 
                                test_query_count: int = 50,
                                search_L_values: List[int] = None) -> Dict[str, Any]:
        """
        测试不同search_L参数的性能
        :param test_query_count: 测试查询数量
        :param search_L_values: search_L参数值列表
        :return: 测试结果字典
        """
        if search_L_values is None:
            search_L_values = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
        
        print(f"\n{'='*60}")
        print(f"开始search_L参数性能测试 (数据集: {self.dataset})")
        print(f"测试查询数: {test_query_count}")
        print(f"search_L参数范围: {search_L_values}")
        print(f"{'='*60}")
        
        # 随机选择测试查询
        all_queries = range(len(self.env.queries))
        test_query_indices = random.sample(list(all_queries), min(test_query_count, len(all_queries)))
        
        # 初始化结果容器
        results = {
            'dataset': self.dataset,
            'vector_dim': self.env.vector_dim,
            'test_query_count': test_query_count,
            'search_L_results': {},
            'summary': {
                'best_qps': 0.0,
                'best_search_L': 0,
                'best_recall': 0.0,
                'qps_range': [0.0, 0.0],
                'recall_range': [0.0, 0.0]
            }
        }
        
        # 为每个search_L参数测试性能
        for search_L in search_L_values:
            print(f"\n🔧 测试 search_L = {search_L}")
            
            # 设置search_L参数
            self.env.cpp_evaluator.searcher.set_search_L(search_L)
            
            # 测试当前search_L的性能
            search_L_results = self._test_single_search_L(test_query_indices, search_L)
            results['search_L_results'][str(search_L)] = search_L_results
            
            # 输出当前search_L结果
            print(f"  - 平均QPS: {search_L_results['avg_qps']:.2f}")
            print(f"  - 平均召回率: {search_L_results['avg_recall']:.4f}")
            print(f"  - 平均搜索时间: {search_L_results['avg_search_time']:.4f}s")
        
        # 计算总结统计
        self._calculate_summary(results)
        
        # 输出总结和可视化
        self._print_summary(results)
        self._plot_results(results)
        self._save_results(results)
        
        return results
    
    def _test_single_search_L(self, query_indices: List[int], search_L: int) -> Dict[str, Any]:
        """测试单个search_L参数的性能"""
        total_qps = 0.0
        total_recall = 0.0
        total_search_time = 0.0
        valid_queries = 0
        
        for query_idx in query_indices:
            try:
                # 设置查询
                self.env.set_query_by_index(query_idx)
                
                # 执行搜索并测量时间
                start_time = datetime.datetime.now()
                search_result = self.agent.search(query_idx=query_idx)
                end_time = datetime.datetime.now()
                
                # 计算性能指标
                search_time = (end_time - start_time).total_seconds()
                recall = search_result['reward_breakdown'].get('recall', 0.0)
                qps = 1.0 / search_time if search_time > 0 else 0.0
                
                # 累计统计
                total_qps += qps
                total_recall += recall
                total_search_time += search_time
                valid_queries += 1
                
            except Exception as e:
                print(f"  查询 {query_idx} 测试失败: {e}")
                continue
        
        # 计算平均值
        if valid_queries > 0:
            return {
                'avg_qps': total_qps / valid_queries,
                'avg_recall': total_recall / valid_queries,
                'avg_search_time': total_search_time / valid_queries,
                'valid_queries': valid_queries,
                'search_L': search_L
            }
        else:
            return {
                'avg_qps': 0.0,
                'avg_recall': 0.0,
                'avg_search_time': 0.0,
                'valid_queries': 0,
                'search_L': search_L
            }
    
    def _calculate_summary(self, results: Dict[str, Any]) -> None:
        """计算性能总结"""
        qps_values = []
        recall_values = []
        search_L_values = []
        
        for search_L_str, search_L_result in results['search_L_results'].items():
            search_L = int(search_L_str)
            qps = search_L_result['avg_qps']
            recall = search_L_result['avg_recall']
            
            qps_values.append(qps)
            recall_values.append(recall)
            search_L_values.append(search_L)
        
        if qps_values:
            # 找到最佳QPS和对应的search_L
            best_idx = np.argmax(qps_values)
            results['summary']['best_qps'] = qps_values[best_idx]
            results['summary']['best_search_L'] = search_L_values[best_idx]
            results['summary']['best_recall'] = recall_values[best_idx]
            results['summary']['qps_range'] = [min(qps_values), max(qps_values)]
            results['summary']['recall_range'] = [min(recall_values), max(recall_values)]
    
    def _print_summary(self, results: Dict[str, Any]) -> None:
        """打印测试总结"""
        print(f"\n{'='*60}")
        print("search_L参数性能测试总结")
        print(f"{'='*60}")
        
        summary = results['summary']
        print(f"最佳性能配置:")
        print(f"  - 最佳search_L: {summary['best_search_L']}")
        print(f"  - 最高QPS: {summary['best_qps']:.2f} 查询/秒")
        print(f"  - 对应召回率: {summary['best_recall']:.4f}")
        
        print(f"\n性能范围:")
        print(f"  - QPS范围: {summary['qps_range'][0]:.2f} - {summary['qps_range'][1]:.2f}")
        print(f"  - 召回率范围: {summary['recall_range'][0]:.4f} - {summary['recall_range'][1]:.4f}")
        
        # 输出所有search_L的性能表格
        print(f"\n详细性能数据:")
        print(f"{'search_L':>8} {'QPS':>10} {'召回率':>8} {'搜索时间(s)':>12}")
        print(f"{'-'*45}")
        
        search_L_results = results['search_L_results']
        for search_L in sorted(map(int, search_L_results.keys())):
            result = search_L_results[str(search_L)]
            print(f"{search_L:>8} {result['avg_qps']:>10.2f} {result['avg_recall']:>8.4f} {result['avg_search_time']:>12.4f}")
    
    def _plot_results(self, results: Dict[str, Any]) -> None:
        """绘制测试结果图表"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 提取数据
        search_L_values = []
        qps_values = []
        recall_values = []
        time_values = []
        
        search_L_results = results['search_L_results']
        for search_L in sorted(map(int, search_L_results.keys())):
            result = search_L_results[str(search_L)]
            search_L_values.append(search_L)
            qps_values.append(result['avg_qps'])
            recall_values.append(result['avg_recall'])
            time_values.append(result['avg_search_time'])
        
        # 1. QPS vs search_L
        ax1.plot(search_L_values, qps_values, 'o-', linewidth=2, markersize=6, color='#2E86AB')
        ax1.set_xscale('log', base=2)
        ax1.set_xlabel('search_L参数 (对数尺度)')
        ax1.set_ylabel('QPS (查询数/秒)')
        ax1.set_title(f'QPS vs search_L (数据集: {self.dataset})')
        ax1.grid(True, alpha=0.3)
        
        # 标记最佳点
        best_search_L = results['summary']['best_search_L']
        best_qps = results['summary']['best_qps']
        ax1.plot(best_search_L, best_qps, 'ro', markersize=10, label=f'最佳: search_L={best_search_L}, QPS={best_qps:.1f}')
        ax1.legend()
        
        # 2. 召回率和搜索时间 vs search_L
        ax2_twin = ax2.twinx()
        
        # 召回率曲线
        recall_line = ax2.plot(search_L_values, recall_values, 's-', linewidth=2, markersize=6, 
                              color='#A23B72', label='召回率')
        ax2.set_xscale('log', base=2)
        ax2.set_xlabel('search_L参数 (对数尺度)')
        ax2.set_ylabel('召回率', color='#A23B72')
        ax2.tick_params(axis='y', labelcolor='#A23B72')
        ax2.set_ylim(0, 1.0)
        
        # 搜索时间曲线
        time_line = ax2_twin.plot(search_L_values, time_values, '^-', linewidth=2, markersize=6, 
                                 color='#F18F01', label='搜索时间')
        ax2_twin.set_ylabel('搜索时间 (秒)', color='#F18F01')
        ax2_twin.tick_params(axis='y', labelcolor='#F18F01')
        
        # 合并图例
        lines = recall_line + time_line
        labels = [l.get_label() for l in lines]
        ax2.legend(lines, labels, loc='upper left')
        
        ax2.set_title(f'召回率和搜索时间 vs search_L (数据集: {self.dataset})')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图表
        output_dir = f"search_L_test_results/{self.dataset}"
        os.makedirs(output_dir, exist_ok=True)
        plot_path = f"{output_dir}/search_L_performance.png"
        plt.savefig(plot_path, dpi=200, bbox_inches='tight')
        plt.close()
        
        print(f"📊 性能图表已保存: {plot_path}")
    
    def _save_results(self, results: Dict[str, Any]) -> None:
        """保存测试结果到JSON文件"""
        output_dir = f"search_L_test_results/{self.dataset}"
        os.makedirs(output_dir, exist_ok=True)
        result_path = f"{output_dir}/search_L_test_results.json"
        
        # 添加测试配置信息
        results['test_config'] = {
            'dataset': self.dataset,
            'model_path': self.model_path,
            'test_query_count': results['test_query_count'],
            'vector_dim': self.env.vector_dim,
            'test_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"📄 测试结果已保存: {result_path}")


def main(model_path: str, test_query_count: int = 50):
    """
    自动在指定的6个数据集上运行search_L参数测试
    :param model_path: 训练好的模型文件路径（.pth）
    :param test_query_count: 每个数据集的测试查询数量
    """
    # 指定需要测试的6个数据集
    DATASETS_TO_TEST = ["sift1M", "sift10M", "deep", "glove", "sift100K", "gist"]
    
    # search_L参数范围
    SEARCH_L_VALUES = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
    
    # 设置随机种子确保可复现
    torch.manual_seed(42)
    np.random.seed(42)
    random.seed(42)
    
    print(f"{'='*80}")
    print(f"开始批量search_L参数测试（共 {len(DATASETS_TO_TEST)} 个数据集）")
    print(f"模型路径: {model_path}")
    print(f"每个数据集测试查询数: {test_query_count}")
    print(f"search_L参数范围: {SEARCH_L_VALUES}")
    print(f"数据集列表: {DATASETS_TO_TEST}")
    print(f"{'='*80}\n")
    
    # 遍历所有数据集执行测试
    all_results = {}
    
    for dataset in DATASETS_TO_TEST:
        print(f"\n{'#'*80}")
        print(f"开始测试数据集: {dataset}")
        print(f"{'#'*80}")
        
        try:
            tester = SearchLTester(
                model_path=model_path,
                dataset=dataset
            )
            results = tester.test_search_L_performance(
                test_query_count=test_query_count,
                search_L_values=SEARCH_L_VALUES
            )
            all_results[dataset] = results
            print(f"\n✅ 数据集 {dataset} 测试完成!")
        except Exception as e:
            print(f"\n❌ 数据集 {dataset} 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            print(f"继续测试下一个数据集...\n")
    
    # 生成跨数据集的总结报告
    _generate_cross_dataset_summary(all_results)
    
    print(f"\n{'='*80}")
    print(f"所有数据集测试结束! 结果已保存至 search_L_test_results 目录")
    print(f"{'='*80}")


def _generate_cross_dataset_summary(all_results: Dict[str, Any]) -> None:
    """生成跨数据集的总结报告"""
    print(f"\n{'='*80}")
    print("跨数据集search_L性能总结")
    print(f"{'='*80}")
    
    print(f"{'数据集':<12} {'最佳search_L':>12} {'最高QPS':>10} {'对应召回率':>12}")
    print(f"{'-'*50}")
    
    for dataset, results in all_results.items():
        summary = results['summary']
        print(f"{dataset:<12} {summary['best_search_L']:>12} {summary['best_qps']:>10.1f} {summary['best_recall']:>12.4f}")
    
    # 保存跨数据集总结
    output_dir = "search_L_test_results"
    os.makedirs(output_dir, exist_ok=True)
    summary_path = f"{output_dir}/cross_dataset_summary.json"
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 跨数据集总结已保存: {summary_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='自动在多个数据集上测试search_L参数性能')
    parser.add_argument('--model', required=True, help='训练好的模型文件路径（.pth）')
    parser.add_argument('--queries', type=int, default=50, help='每个数据集的测试查询数量（默认50）')
    
    args = parser.parse_args()
    
    # 调用main函数，自动在6个数据集上运行
    main(
        model_path=args.model,
        test_query_count=args.queries
    )
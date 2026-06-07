import json
import os
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# 设置英文字体和样式
plt.rcParams['font.family'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_results_from_directory(base_dir):
    """
    Load all result files from directory structure - only read four_methods_search_results.json
    """
    results = defaultdict(dict)
    
    # Dataset list
    datasets = ['deep', 'gist', 'glove', 'sift1M', 'sift10M', 'sift100K']
    
    for dataset in datasets:
        dataset_dir = os.path.join(base_dir, f"{dataset}_results")
        if not os.path.exists(dataset_dir):
            continue
            
        # Only load four_methods_search_results.json
        four_methods_file = os.path.join(dataset_dir, "four_methods_search_results.json")
        if os.path.exists(four_methods_file):
            try:
                with open(four_methods_file, 'r') as f:
                    results[dataset] = json.load(f)
                print(f"✅ Successfully loaded {dataset} dataset")
            except Exception as e:
                print(f"❌ Failed to load {dataset} dataset: {e}")
    
    return results

def extract_method_data(dataset_data, method_name):
    """
    Extract data for specified method from dataset data
    """
    method_data = []
    
    method_key = f"search_{method_name}"
    
    if method_key in dataset_data:
        for point in dataset_data[method_key]:
            if all(key in point for key in ['r@k', 'qps', 'search_L']):
                method_data.append({
                    'recall': point['r@k'],
                    'qps': point['qps'],
                    'search_L': point['search_L'],
                    'dataset': dataset_data.get('dataset', 'unknown')
                })
    
    return method_data

def plot_qps_vs_searchL(results, output_dir="qps_vs_searchL_plots"):
    """
    Plot QPS vs search_L curves
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Method list with corresponding colors and markers
    methods = {
        'standard': {'color': 'blue', 'marker': 'o', 'label': 'Standard', 'linestyle': '-'},
        'aco': {'color': 'red', 'marker': 's', 'label': 'ACO', 'linestyle': '--'},
        'dpc_aco': {'color': 'green', 'marker': '^', 'label': 'DPC+ACO', 'linestyle': '-.'}
    }
    
    # Create separate plot for each dataset
    for dataset, dataset_data in results.items():
        plt.figure(figsize=(10, 6))
        
        has_valid_data = False
        
        for method_name, style in methods.items():
            method_data = extract_method_data(dataset_data, method_name)
            
            if method_data and len(method_data) > 1:  # Ensure enough data points
                # Sort by search_L
                method_data.sort(key=lambda x: x['search_L'])
                
                search_Ls = [point['search_L'] for point in method_data]
                qps_values = [point['qps'] for point in method_data]
                
                # Plot curve
                plt.plot(search_Ls, qps_values, 
                        color=style['color'], 
                        marker=style['marker'],
                        markersize=6,
                        linewidth=2,
                        linestyle=style['linestyle'],
                        label=style['label'])
                
                has_valid_data = True
                print(f"  📊 {style['label']}: {len(method_data)} data points")
        
        if not has_valid_data:
            plt.close()
            print(f"⚠️  {dataset} dataset has no valid data, skipping")
            continue
        
        plt.xlabel('Search_L', fontsize=12)
        plt.ylabel('Queries Per Second (QPS)', fontsize=12)
        plt.title(f'{dataset.upper()} Dataset - QPS vs Search_L', fontsize=14, fontweight='bold')
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        
        # Set x-axis to log scale
        plt.xscale('log')
        plt.yscale('linear')
        
        # Automatically adjust y-axis range
        all_qps = []
        for method_name in methods.keys():
            method_data = extract_method_data(dataset_data, method_name)
            if method_data:
                all_qps.extend([point['qps'] for point in method_data])
        
        if all_qps:
            y_min = min(all_qps) * 0.8
            y_max = max(all_qps) * 1.2
            plt.ylim(y_min, y_max)
        
        # Save plot
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'{dataset}_qps_vs_searchL.png'), dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(output_dir, f'{dataset}_qps_vs_searchL.pdf'), bbox_inches='tight')
        plt.close()
        
        print(f"✅ Generated QPS vs Search_L plot for {dataset} dataset")

def plot_recall_vs_searchL(results, output_dir="recall_vs_searchL_plots"):
    """
    Plot Recall vs search_L curves
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Method list with corresponding colors and markers
    methods = {
        'standard': {'color': 'blue', 'marker': 'o', 'label': 'Standard', 'linestyle': '-'},
        'aco': {'color': 'red', 'marker': 's', 'label': 'ACO', 'linestyle': '--'},
        'dpc_aco': {'color': 'green', 'marker': '^', 'label': 'DPC+ACO', 'linestyle': '-.'}
    }
    
    # Create separate plot for each dataset
    for dataset, dataset_data in results.items():
        plt.figure(figsize=(10, 6))
        
        has_valid_data = False
        
        for method_name, style in methods.items():
            method_data = extract_method_data(dataset_data, method_name)
            
            if method_data and len(method_data) > 1:
                # Sort by search_L
                method_data.sort(key=lambda x: x['search_L'])
                
                search_Ls = [point['search_L'] for point in method_data]
                recalls = [point['recall'] for point in method_data]
                
                # Plot curve
                plt.plot(search_Ls, recalls, 
                        color=style['color'], 
                        marker=style['marker'],
                        markersize=6,
                        linewidth=2,
                        linestyle=style['linestyle'],
                        label=style['label'])
                
                has_valid_data = True
        
        if not has_valid_data:
            plt.close()
            continue
        
        plt.xlabel('Search_L', fontsize=12)
        plt.ylabel('Recall@K', fontsize=12)
        plt.title(f'{dataset.upper()} Dataset - Recall vs Search_L', fontsize=14, fontweight='bold')
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.ylim(0.9, 1.0)
        
        # Set x-axis to log scale
        plt.xscale('log')
        
        # Save plot
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'{dataset}_recall_vs_searchL.png'), dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(output_dir, f'{dataset}_recall_vs_searchL.pdf'), bbox_inches='tight')
        plt.close()
        
        print(f"✅ Generated Recall vs Search_L plot for {dataset} dataset")

def plot_comparison_all_methods(results, output_dir="comparison_plots"):
    """
    Plot comprehensive comparison of all methods
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Method list with corresponding colors and markers
    methods = {
        'standard': {'color': 'blue', 'marker': 'o', 'label': 'Standard', 'linestyle': '-'},
        'aco': {'color': 'red', 'marker': 's', 'label': 'ACO', 'linestyle': '--'},
        'dpc_aco': {'color': 'green', 'marker': '^', 'label': 'DPC+ACO', 'linestyle': '-.'}
    }
    
    # Create separate plot for each dataset
    for dataset, dataset_data in results.items():
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        has_valid_data = False
        
        for method_name, style in methods.items():
            method_data = extract_method_data(dataset_data, method_name)
            
            if method_data and len(method_data) > 1:
                # Sort by search_L
                method_data.sort(key=lambda x: x['search_L'])
                
                search_Ls = [point['search_L'] for point in method_data]
                qps_values = [point['qps'] for point in method_data]
                recalls = [point['recall'] for point in method_data]
                
                # Plot QPS vs Search_L in left subplot
                ax1.plot(search_Ls, qps_values, 
                        color=style['color'], 
                        marker=style['marker'],
                        markersize=5,
                        linewidth=2,
                        linestyle=style['linestyle'],
                        label=style['label'])
                
                # Plot Recall vs Search_L in right subplot
                ax2.plot(search_Ls, recalls, 
                        color=style['color'], 
                        marker=style['marker'],
                        markersize=5,
                        linewidth=2,
                        linestyle=style['linestyle'],
                        label=style['label'])
                
                has_valid_data = True
        
        if not has_valid_data:
            plt.close(fig)
            continue
        
        # Configure left subplot
        ax1.set_xlabel('Search_L', fontsize=11)
        ax1.set_ylabel('Queries Per Second (QPS)', fontsize=11)
        ax1.set_title('QPS vs Search_L', fontsize=12, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.set_xscale('log')
        
        # Configure right subplot
        ax2.set_xlabel('Search_L', fontsize=11)
        ax2.set_ylabel('Recall@K', fontsize=11)
        ax2.set_title('Recall vs Search_L', fontsize=12, fontweight='bold')
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3)
        ax2.set_xscale('log')
        ax2.set_ylim(0.9, 1.0)
        
        # Add overall title
        fig.suptitle(f'{dataset.upper()} Dataset - Method Performance Comparison', fontsize=14, fontweight='bold')
        
        # Save plot
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'{dataset}_comparison.png'), dpi=300, bbox_inches='tight')
        plt.savefig(os.path.join(output_dir, f'{dataset}_comparison.pdf'), bbox_inches='tight')
        plt.close()
        
        print(f"✅ Generated comprehensive comparison plot for {dataset} dataset")

def generate_summary_table(results, output_dir="summary_tables"):
    """
    Generate performance summary table
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    methods = ['standard', 'aco', 'dpc_aco']
    
    summary_data = []
    
    for dataset, dataset_data in results.items():
        dataset_summary = {'dataset': dataset}
        
        for method in methods:
            method_data = extract_method_data(dataset_data, method)
            
            if method_data:
                # Find point with highest QPS
                best_qps_point = max(method_data, key=lambda x: x['qps'])
                dataset_summary[f'{method}_best_qps'] = best_qps_point['qps']
                dataset_summary[f'{method}_recall_at_best_qps'] = best_qps_point['recall']
                dataset_summary[f'{method}_searchL_at_best_qps'] = best_qps_point['search_L']
                
                # Find point with highest recall
                best_recall_point = max(method_data, key=lambda x: x['recall'])
                dataset_summary[f'{method}_best_recall'] = best_recall_point['recall']
                dataset_summary[f'{method}_qps_at_best_recall'] = best_recall_point['qps']
                dataset_summary[f'{method}_searchL_at_best_recall'] = best_recall_point['search_L']
            else:
                for key in [f'{method}_best_qps', f'{method}_recall_at_best_qps', f'{method}_searchL_at_best_qps',
                           f'{method}_best_recall', f'{method}_qps_at_best_recall', f'{method}_searchL_at_best_recall']:
                    dataset_summary[key] = 'N/A'
        
        summary_data.append(dataset_summary)
    
    # Save summary table as JSON
    with open(os.path.join(output_dir, 'performance_summary.json'), 'w') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    # Print simplified text table
    print("\n" + "="*130)
    print("Performance Summary")
    print("="*130)
    print(f"{'Dataset':<10} {'Method':<12} {'Best QPS':<12} {'Recall':<10} {'Search_L':<10} {'Best Recall':<12} {'QPS':<12} {'Search_L':<10}")
    print("-"*130)
    
    for dataset_summary in summary_data:
        dataset = dataset_summary['dataset']
        for method in methods:
            if f'{method}_best_qps' in dataset_summary and dataset_summary[f'{method}_best_qps'] != 'N/A':
                print(f"{dataset:<10} {method:<12} "
                      f"{dataset_summary[f'{method}_best_qps']:<12.2f} "
                      f"{dataset_summary[f'{method}_recall_at_best_qps']:<10.4f} "
                      f"{dataset_summary[f'{method}_searchL_at_best_qps']:<10} "
                      f"{dataset_summary[f'{method}_best_recall']:<12.4f} "
                      f"{dataset_summary[f'{method}_qps_at_best_recall']:<12.2f} "
                      f"{dataset_summary[f'{method}_searchL_at_best_recall']:<10}")
    
    print("="*130)

def main():
    """
    Main function
    """
    # Base directory
    base_directory = "/path/to/ACSG/test"  
    
    print("📊 Starting to load and analyze result data...")
    print(f"Search directory: {base_directory}")
    
    # Load all results
    all_results = load_results_from_directory(base_directory)
    
    if not all_results:
        print("❌ No result files found, please check directory structure")
        return
    
    print(f"\n✅ Successfully loaded {len(all_results)} datasets")
    
    # Create multiple output directories
    output_dirs = {
        'qps_vs_searchL': 'qps_vs_searchL_plots',
        'recall_vs_searchL': 'recall_vs_searchL_plots', 
        'comparison': 'comparison_plots',
        'summary': 'summary_tables'
    }
    
    for dir_name in output_dirs.values():
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    
    # Generate different types of plots
    print("\n📈 Generating QPS vs Search_L plots...")
    plot_qps_vs_searchL(all_results, output_dirs['qps_vs_searchL'])
    
    print("\n📈 Generating Recall vs Search_L plots...")
    plot_recall_vs_searchL(all_results, output_dirs['recall_vs_searchL'])
    
    print("\n📈 Generating comprehensive comparison plots...")
    plot_comparison_all_methods(all_results, output_dirs['comparison'])
    
    # Generate performance summary table
    print("\n📊 Generating performance summary table...")
    generate_summary_table(all_results, output_dirs['summary'])
    
    print(f"\n🎉 All plots and tables generated successfully!")
    print("📁 Output directory structure:")
    for dir_type, dir_path in output_dirs.items():
        print(f"   - {dir_path}: {dir_type} related files")

if __name__ == "__main__":
    main()
import h5py
import numpy as np

def read_sift10m_mat(mat_path):
    """读取.mat文件，根据原始形状动态判断是否需要转置，确保最终形状为(N, 128)"""
    try:
        with h5py.File(mat_path, 'r') as f:
            print("文件中的变量名列表：", list(f.keys()))
            feature_var = 'fea'  # 实际变量名
            
            # 1. 转换为numpy数组
            features_raw = np.array(f[feature_var])
            print(f"原始特征形状（转换为numpy后）：{features_raw.shape}")
            
            # 2. 判断是否需要转置：
            #    - 如果原始形状是(128, N) → 需要转置为(N, 128)
            #    - 如果原始形状是(N, 128) → 无需转置
            if features_raw.shape[0] == 128:
                features = features_raw.T  # 转置
                print("检测到原始形状为(128, N)，已转置为(N, 128)")
            elif features_raw.shape[1] == 128:
                features = features_raw  # 不转置
                print("检测到原始形状已为(N, 128)，无需转置")
            else:
                raise ValueError(f"特征形状不符合预期，原始形状为{features_raw.shape}，无法确定维度")
            
            print(f"最终特征形状：{features.shape}")
            return features.astype(np.float32)
    
    except Exception as e:
        raise Exception(f"读取失败：{e}")


def save_as_fvecs(features, fvecs_path):
    """保存为.fvecs格式（确保特征维度为128）"""
    n_samples, dim = features.shape
    assert dim == 128, f"维度错误：当前特征维度是{dim}，必须为128"
    
    with open(fvecs_path, 'wb') as f:
        # 写入每个向量的维度（128）
        f.write(np.array([dim], dtype=np.int32).repeat(n_samples).tobytes())
        # 写入特征数据
        f.write(features.tobytes())
    print(f"保存成功：{fvecs_path}（{n_samples}个样本，128维）")


if __name__ == "__main__":
    mat_file_path = "SIFT10Mfeatures.mat"
    fvecs_save_path = "sift10m_base.fvecs"
    
    # 读取特征（自动判断是否转置）
    sift_features = read_sift10m_mat(mat_file_path)
    
    # 保存为.fvecs
    save_as_fvecs(sift_features, fvecs_save_path)
    
    print("处理完成！")
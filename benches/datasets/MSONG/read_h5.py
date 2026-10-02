import h5py

# 指定你的 .h5 文件路径
file_path = 'benches/datasets/MSONG/TRAXLZU12903D05F94.h5'

try:
    # 打开 HDF5 文件
    with h5py.File(file_path, 'r') as hdf5_file:
        # 获取 HDF5 文件中的所有顶层对象（数据集、组等）的名称
        top_level_keys = list(hdf5_file.keys())

        # 遍历顶层对象
        for key in top_level_keys:
            obj = hdf5_file[key]
            if isinstance(obj, h5py.Group):
                print(f"Group: {key}")

                # 查看组内的子对象（数据集或子组）
                sub_keys = list(obj.keys())
                for sub_key in sub_keys:
                    sub_obj = obj[sub_key]
                    if isinstance(sub_obj, h5py.Dataset):
                        print(f"  Dataset: {sub_key} (shape: {sub_obj.shape}, dtype: {sub_obj.dtype})")
                    elif isinstance(sub_obj, h5py.Group):
                        print(f"  Subgroup: {sub_key}")
                    else:
                        print(f"  Unknown object: {sub_key} (type: {type(sub_obj)})")

except Exception as e:
    print(f"Error reading HDF5 file: {e}")
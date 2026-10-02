#include <iostream>
#include <fstream>
#include <H5Cpp.h>

using namespace H5;

void write_fvecs(const std::string& output_file, const float* data, int num_vectors, int dim) {
    std::ofstream fout(output_file, std::ios::binary);
    if (!fout) {
        std::cerr << "Error opening output file: " << output_file << std::endl;
        return;
    }

    for (int i = 0; i < num_vectors; ++i) {
        fout.write(reinterpret_cast<const char*>(&dim), sizeof(int));
        fout.write(reinterpret_cast<const char*>(data + i * dim), dim * sizeof(float));
    }

    fout.close();
}

int main() {
    std::string input_h5_file = "your_file.h5";
    std::string dataset_name = "your_dataset_name";
    std::string output_fvecs_file = "output.fvecs";

    try {
        // 打开 HDF5 文件
        H5File file(input_h5_file, H5F_ACC_RDONLY);

        // 打开数据集
        DataSet dataset = file.openDataSet(dataset_name);

        // 获取数据集的数据类型和空间
        DataSpace dataspace = dataset.getSpace();
        int rank = dataspace.getSimpleExtentNdims();

        // 获取数据集的维度
        hsize_t dims[rank];
        dataspace.getSimpleExtentDims(dims, NULL);

        if (rank != 2) {
            std::cerr << "Dataset rank is not 2." << std::endl;
            return -1;
        }

        int num_vectors = dims[0];
        int dim = dims[1];

        // 读取数据
        float *data = new float[num_vectors * dim];
        dataset.read(data, PredType::NATIVE_FLOAT);

        // 将数据写入 fvecs 文件
        write_fvecs(output_fvecs_file, data, num_vectors, dim);

        // 释放内存
        delete[] data;

    } catch (FileIException &error) {
        error.printErrorStack();
        return -1;
    } catch (DataSetIException &error) {
        error.printErrorStack();
        return -1;
    } catch (DataSpaceIException &error) {
        error.printErrorStack();
        return -1;
    } catch (DataTypeIException &error) {
        error.printErrorStack();
        return -1;
    }

    return 0;
}

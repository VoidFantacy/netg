#include <iostream>
#include <fstream>
#include <memory>
#include <cstring>
#include <algorithm>

int main() {
    std::string inputFilename = "siftsmall_query.fvecs";
    std::ifstream ifs(inputFilename, std::ios::binary);
    if (!ifs.is_open()) {
        std::cerr << "无法打开输入文件!" << std::endl;
        exit(1);
    }

    int d;
    int n = -1;

    // 读取第一个向量的维度信息
    ifs.read((char*)&d, sizeof(d));

    // 计算文件大小并推断向量数量
    ifs.seekg(0, std::ios_base::end);
    n = ifs.tellg();
    if(n % ((d + 1) * sizeof(float)) == 0) {
        n /= (d + 1) * sizeof(float);
    } else {
        std::cerr << "文件大小与预期不匹配!" << std::endl;
        exit(1);
    }

    ifs.seekg(0, std::ios_base::beg);

    // 分配存储向量数据的内存
    std::unique_ptr<float[]> x(new float[d * n]);

    // 逐块读取数据并跳过维度信息
    constexpr size_t batch_size = 8192;
    std::unique_ptr<float[]> buf(new float[(d + 1) * batch_size]);
    size_t pos_x = 0;

    for (size_t i = 0; i < n; i += batch_size) {
        size_t nvecs = std::min(batch_size, n - i);
        ifs.read((char*)buf.get(), sizeof(float) * (d + 1) * nvecs);
        size_t pos_buf = 0;
        for (size_t j = 0; j < nvecs; ++j) {
            std::memmove(&x[pos_x], &buf[pos_buf + 1], d * sizeof(float));
            pos_x += d;
            pos_buf += d + 1;
        }
    }

    ifs.close();

    // 输出向量数据
    for (size_t i = 0; i < n; ++i) {
        std::cout << "Vector " << i << ": ";
        for (int j = 0; j < d; ++j) {
            std::cout << x[i * d + j] << " ";
        }
        std::cout << std::endl;
    }

    return 0;
}

#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>

#include <iostream>
#include <fstream>
#include <vector>
#include <sstream>

std::vector<std::string> split(const std::string &s, char delimiter) {
    std::vector<std::string> tokens;
    std::string token;
    std::stringstream ss(s);  // 将字符串s绑定到字符串流上

    while (std::getline(ss, token, delimiter)) {  // 使用分隔符分割字符串
        tokens.push_back(token);  // 将分割后的字符串添加到tokens中
    }

    return tokens;
}

void writeFvecs(const std::string& outputFilename, const std::vector<std::vector<float>>& vectors) {
    std::ofstream outputFile(outputFilename, std::ios::binary);
    if (!outputFile.is_open()) {
        std::cerr << "无法打开输出文件!" << std::endl;
        exit(1);
    }

    for (const auto& vector : vectors) {
        int dim = vector.size();
        outputFile.write(reinterpret_cast<const char*>(&dim), sizeof(int));  // 写入维度
        outputFile.write(reinterpret_cast<const char*>(vector.data()), dim * sizeof(float));  // 写入向量数据
    }

    outputFile.close();
}

std::vector<std::vector<float>> readTxt(const std::string& inputFilename) {
    std::ifstream inputFile(inputFilename);
    if (!inputFile.is_open()) {
        std::cerr << "无法打开输入文件!" << std::endl;
        exit(1);
    }

    std::vector<std::vector<float>> vectors;
    std::string line;

    while (std::getline(inputFile, line)) {  // 读取每一行
        std::vector<std::string> data = split(line, ' ');
        std::vector<float> vector;
        for (int i = 1; i < data.size(); i++)
        {
            vector.push_back(std::stof(data[i]));
        }
        
        vectors.push_back(vector);
    }

    inputFile.close();
    return vectors;
}

int main() {
    std::string inputFilename = "glove.twitter.27B.200d.txt";
    std::string outputFilename = "glove27B_200d_base.fvecs";

    // std::vector<std::vector<float>> vectors = readTxt(inputFilename);  // 读取文本文件
    // writeFvecs(outputFilename, vectors);  // 写入二进制文件

    // std::cout << "文件已转换为fvecs格式。" << std::endl;

    std::ifstream ifs(outputFilename, std::ios::binary);
    if (!ifs.is_open()) {
        std::cerr << "无法打开输出文件!" << std::endl;
        exit(1);
    }
    std::cerr << "成功打开输出文件!" << std::endl;
    ifs.close();
    return 0;
}


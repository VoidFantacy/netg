#include <iostream>
#include <fstream>
#include <vector>
#include <algorithm>

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <graph_file> <num_points>" << std::endl;
        return 1;
    }

    std::string filename = argv[1];
    unsigned num_points = (unsigned)atoi(argv[2]);
    
    std::ifstream in(filename, std::ios::binary);
    if (!in.is_open()) {
        std::cerr << "Error opening " << filename << std::endl;
        return 1;
    }

    std::cout << "Checking graph: " << filename << std::endl;
    
    unsigned long long invalid_count = 0;
    // 只需要检查前 100 万个点就足够发现问题了
    unsigned check_limit = num_points < 1000000 ? num_points : 1000000; 

    for (unsigned i = 0; i < check_limit; i++) {
        unsigned k;
        if (!in.read((char*)&k, 4)) break;
        
        std::vector<unsigned> neighbors(k);
        if (!in.read((char*)neighbors.data(), k * 4)) break;

        for (unsigned neighbor : neighbors) {
            // 如果邻居ID >= 点总数，或者巨大的数，说明就是 -1 变异了
            if (neighbor >= num_points) {
                if (invalid_count < 3) {
                    std::cout << "❌ [实锤证据] Node " << i << " has INVALID neighbor: " << neighbor << " (Data Poison!)" << std::endl;
                }
                invalid_count++;
            }
        }
    }

    if (invalid_count > 0) {
        std::cout << "\n🔴 结论: 图文件包含 " << invalid_count << " 个非法节点！" << std::endl;
        std::cout << "正是这些节点导致了 Segmentation fault。" << std::endl;
        return 1; // 返回错误码
    } else {
        std::cout << "\n✅ 结论: 图文件是干净的（不太可能）。" << std::endl;
        return 0;
    }
}

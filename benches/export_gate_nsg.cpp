#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

#include <argparse/argparse.hpp>

#include <ACSG/IndexACSG.h>

int main(int argc, char** argv) {
    argparse::ArgumentParser program("export_gate_nsg");
    program.add_argument("--index_file").required();
    program.add_argument("--output_file").required();
    try {
        program.parse_args(argc, argv);
    } catch (const std::exception& error) {
        std::cerr << error.what() << "\n" << program;
        return 2;
    }

    const std::filesystem::path index_file = program.get<std::string>("--index_file");
    const std::filesystem::path output_file = program.get<std::string>("--output_file");
    const std::filesystem::path partial_file = output_file.string() + ".partial";
    if (std::filesystem::exists(output_file) || std::filesystem::exists(partial_file)) {
        throw std::runtime_error("refusing to overwrite existing output: " + output_file.string());
    }
    if (!output_file.parent_path().empty()) {
        std::filesystem::create_directories(output_file.parent_path());
    }

    acsg::IndexACSGFlat index;
    index.loadACPG(index_file.c_str());
    const auto graph = index.get_acpg_graph();
    if (!graph || graph->N != index.ntotal || graph->K <= 0) {
        throw std::runtime_error("loaded index has no compatible graph");
    }

    std::ofstream out(partial_file, std::ios::binary);
    if (!out) throw std::runtime_error("cannot create output: " + partial_file.string());
    const uint32_t width = static_cast<uint32_t>(graph->K);
    const uint32_t entrypoint = static_cast<uint32_t>(index.acsg.enterpoint);
    out.write(reinterpret_cast<const char*>(&width), sizeof(width));
    out.write(reinterpret_cast<const char*>(&entrypoint), sizeof(entrypoint));

    uint64_t valid_edges = 0;
    uint64_t invalid_slots = 0;
    uint64_t duplicate_slots = 0;
    uint64_t zero_degree_nodes = 0;
    uint32_t min_degree = width;
    uint32_t max_degree = 0;
    std::vector<uint32_t> neighbors;
    neighbors.reserve(graph->K);
    for (faiss::idx_t node = 0; node < graph->N; ++node) {
        neighbors.clear();
        std::unordered_set<int32_t> seen;
        for (int offset = 0; offset < graph->K; ++offset) {
            const int32_t neighbor = graph->at(node, offset);
            if (neighbor < 0 || neighbor >= graph->N) {
                ++invalid_slots;
                continue;
            }
            if (!seen.insert(neighbor).second) {
                ++duplicate_slots;
            }
            neighbors.push_back(static_cast<uint32_t>(neighbor));
        }
        const uint32_t degree = static_cast<uint32_t>(neighbors.size());
        if (degree == 0) ++zero_degree_nodes;
        min_degree = std::min(min_degree, degree);
        max_degree = std::max(max_degree, degree);
        out.write(reinterpret_cast<const char*>(&degree), sizeof(degree));
        out.write(reinterpret_cast<const char*>(neighbors.data()), degree * sizeof(uint32_t));
        valid_edges += degree;
    }
    out.close();
    if (!out) {
        throw std::runtime_error("failed while writing: " + partial_file.string());
    }
    std::filesystem::rename(partial_file, output_file);

    std::cout << "GATE_NSG_EXPORT_COMPLETE"
              << " nodes=" << graph->N
              << " width=" << width
              << " entrypoint=" << entrypoint
              << " valid_edges=" << valid_edges
              << " invalid_slots=" << invalid_slots
              << " duplicate_slots=" << duplicate_slots
              << " zero_degree_nodes=" << zero_degree_nodes
              << " min_degree=" << min_degree
              << " max_degree=" << max_degree
              << " output=" << output_file.string() << '\n';
    return 0;
}

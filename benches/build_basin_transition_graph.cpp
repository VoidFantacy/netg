#include <algorithm>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

#include <argparse/argparse.hpp>
#include <nlohmann/json.hpp>

#include <ACSG/IndexACSG.h>

using json = nlohmann::json;
using Clock = std::chrono::steady_clock;

namespace {

std::vector<int32_t> load_i32(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary | std::ios::ate);
    if (!in) throw std::runtime_error("cannot open int32 file: " + path.string());
    const auto bytes = static_cast<size_t>(in.tellg());
    if (bytes == 0 || bytes % sizeof(int32_t) != 0) {
        throw std::runtime_error("invalid int32 file size: " + path.string());
    }
    in.seekg(0);
    std::vector<int32_t> values(bytes / sizeof(int32_t));
    in.read(reinterpret_cast<char*>(values.data()), static_cast<std::streamsize>(bytes));
    if (!in) throw std::runtime_error("failed to read int32 file: " + path.string());
    return values;
}

template <typename T>
void write_binary_atomic(const std::filesystem::path& path, const std::vector<T>& values) {
    const auto partial = std::filesystem::path(path.string() + ".partial");
    std::ofstream out(partial, std::ios::binary);
    if (!out) throw std::runtime_error("cannot create output: " + partial.string());
    out.write(reinterpret_cast<const char*>(values.data()),
              static_cast<std::streamsize>(values.size() * sizeof(T)));
    out.close();
    if (!out) throw std::runtime_error("failed while writing: " + partial.string());
    std::filesystem::rename(partial, path);
}

}  // namespace

int main(int argc, char** argv) {
    argparse::ArgumentParser program("build_basin_transition_graph");
    program.add_argument("--index_file").required();
    program.add_argument("--hub_ids").required();
    program.add_argument("--output_dir").required();
    program.add_argument("--dataset").required();
    program.add_argument("--artifact_version").required();
    program.add_argument("--build_seed").scan<'i', int>().required();
    try {
        program.parse_args(argc, argv);
    } catch (const std::exception& error) {
        std::cerr << error.what() << "\n" << program;
        return 2;
    }

    const std::filesystem::path index_file = program.get<std::string>("--index_file");
    const std::filesystem::path hub_ids_file = program.get<std::string>("--hub_ids");
    const std::filesystem::path output_dir = program.get<std::string>("--output_dir");
    if (std::filesystem::exists(output_dir)) {
        throw std::runtime_error("refusing to overwrite output directory: " + output_dir.string());
    }
    std::filesystem::create_directories(output_dir);

    const auto total_begin = Clock::now();
    acsg::IndexACSGFlat index;
    const auto load_begin = Clock::now();
    index.loadACPG(index_file.c_str());
    const auto load_end = Clock::now();
    const auto graph = index.get_acpg_graph();
    if (!graph || graph->N != index.ntotal || graph->K <= 0) {
        throw std::runtime_error("loaded index has no compatible frozen graph");
    }

    const auto hubs = load_i32(hub_ids_file);
    if (hubs.size() > static_cast<size_t>(std::numeric_limits<int32_t>::max())) {
        throw std::runtime_error("too many hubs");
    }
    std::unordered_set<int32_t> unique_hubs;
    for (const int32_t hub : hubs) {
        if (hub < 0 || hub >= graph->N) {
            throw std::runtime_error("hub id outside graph: " + std::to_string(hub));
        }
        if (!unique_hubs.insert(hub).second) {
            throw std::runtime_error("duplicate hub id: " + std::to_string(hub));
        }
    }

    const size_t node_count = static_cast<size_t>(graph->N);
    const size_t hub_count = hubs.size();
    std::vector<int32_t> labels(node_count, -1);
    std::vector<int32_t> queue(node_count);
    size_t head = 0;
    size_t tail = 0;
    for (size_t basin = 0; basin < hub_count; ++basin) {
        labels[static_cast<size_t>(hubs[basin])] = static_cast<int32_t>(basin);
        queue[tail++] = hubs[basin];
    }

    const auto bfs_begin = Clock::now();
    uint32_t max_hop = 0;
    while (head < tail) {
        const size_t level_end = tail;
        while (head < level_end) {
            const int32_t node = queue[head++];
            const int32_t basin = labels[static_cast<size_t>(node)];
            for (int offset = 0; offset < graph->K; ++offset) {
                const int32_t neighbor = graph->at(node, offset);
                if (neighbor < 0 || neighbor >= graph->N) continue;
                auto& neighbor_label = labels[static_cast<size_t>(neighbor)];
                if (neighbor_label == -1) {
                    neighbor_label = basin;
                    queue[tail++] = neighbor;
                }
            }
        }
        if (head < tail) ++max_hop;
    }
    const auto bfs_end = Clock::now();

    std::vector<uint64_t> basin_sizes(hub_count, 0);
    uint64_t unlabeled_nodes = 0;
    for (const int32_t label : labels) {
        if (label < 0) {
            ++unlabeled_nodes;
        } else {
            ++basin_sizes[static_cast<size_t>(label)];
        }
    }

    const auto count_begin = Clock::now();
    std::vector<uint64_t> transitions(hub_count * hub_count, 0);
    uint64_t valid_edges = 0;
    uint64_t invalid_slots = 0;
    uint64_t unlabeled_edges = 0;
    uint64_t cross_basin_edges = 0;
    for (faiss::idx_t node = 0; node < graph->N; ++node) {
        const int32_t source = labels[static_cast<size_t>(node)];
        for (int offset = 0; offset < graph->K; ++offset) {
            const int32_t neighbor = graph->at(node, offset);
            if (neighbor < 0 || neighbor >= graph->N) {
                ++invalid_slots;
                continue;
            }
            ++valid_edges;
            const int32_t target = labels[static_cast<size_t>(neighbor)];
            if (source < 0 || target < 0) {
                ++unlabeled_edges;
                continue;
            }
            ++transitions[static_cast<size_t>(source) * hub_count + static_cast<size_t>(target)];
            if (source != target) ++cross_basin_edges;
        }
    }
    const auto count_end = Clock::now();

    const auto counts_path = output_dir / "transition_counts.u64";
    const auto sizes_path = output_dir / "basin_sizes.u64";
    write_binary_atomic(counts_path, transitions);
    write_binary_atomic(sizes_path, basin_sizes);

    const auto total_end = Clock::now();
    const auto seconds = [](const auto begin, const auto end) {
        return std::chrono::duration<double>(end - begin).count();
    };
    json manifest = {
        {"schema_version", 1},
        {"status", "complete"},
        {"framework_version", "btg_falsification_v1"},
        {"core_mechanism", "directed transition counts between multi-source graph-BFS QGT basins"},
        {"component_role", "diagnostic_core_mechanism"},
        {"dataset", program.get<std::string>("--dataset")},
        {"artifact_version", program.get<std::string>("--artifact_version")},
        {"selection_split", "none_graph_only"},
        {"build_seed", program.get<int>("--build_seed")},
        {"heldout_accessed", false},
        {"index_file", index_file.string()},
        {"hub_ids_file", hub_ids_file.string()},
        {"node_count", node_count},
        {"graph_width", graph->K},
        {"hub_count", hub_count},
        {"basin_assignment", "deterministic multi-source FIFO BFS over outgoing frozen-NSG edges; hub-file order breaks equal-hop ties"},
        {"max_bfs_hop", max_hop},
        {"labeled_nodes", tail},
        {"unlabeled_nodes", unlabeled_nodes},
        {"valid_edges", valid_edges},
        {"invalid_slots", invalid_slots},
        {"unlabeled_edges", unlabeled_edges},
        {"cross_basin_edges", cross_basin_edges},
        {"transition_counts_file", counts_path.string()},
        {"basin_sizes_file", sizes_path.string()},
        {"index_load_wall_seconds", seconds(load_begin, load_end)},
        {"basin_bfs_wall_seconds", seconds(bfs_begin, bfs_end)},
        {"transition_count_wall_seconds", seconds(count_begin, count_end)},
        {"total_wall_seconds", seconds(total_begin, total_end)}
    };
    const auto manifest_partial = output_dir / "manifest.json.partial";
    std::ofstream manifest_out(manifest_partial);
    manifest_out << manifest.dump(2) << '\n';
    manifest_out.close();
    if (!manifest_out) throw std::runtime_error("failed to write manifest");
    std::filesystem::rename(manifest_partial, output_dir / "manifest.json");

    std::cout << "BTG_BUILD_COMPLETE"
              << " dataset=" << manifest["dataset"].get<std::string>()
              << " nodes=" << node_count
              << " hubs=" << hub_count
              << " labeled=" << tail
              << " max_hop=" << max_hop
              << " valid_edges=" << valid_edges
              << " cross_edges=" << cross_basin_edges
              << " wall_seconds=" << seconds(total_begin, total_end)
              << '\n';
    return 0;
}

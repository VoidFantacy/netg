#include <efanna2e/index_nsg.h>
#include <efanna2e/util.h>

#include <omp.h>
#include <sys/stat.h>

#include <algorithm>
#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct FloatVectors {
  unsigned count = 0;
  unsigned dim = 0;
  std::vector<float> values;
};

FloatVectors LoadFvecs(const std::string& path, unsigned limit = 0) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open fvecs: " + path);
  int first_dim = 0;
  input.read(reinterpret_cast<char*>(&first_dim), sizeof(first_dim));
  if (!input || first_dim <= 0) throw std::runtime_error("invalid fvecs header: " + path);
  input.seekg(0, std::ios::end);
  const std::streamoff bytes = input.tellg();
  const std::streamoff record_bytes = sizeof(int) + sizeof(float) * first_dim;
  if (bytes <= 0 || bytes % record_bytes != 0) {
    throw std::runtime_error("invalid fvecs byte size: " + path);
  }
  const unsigned available = static_cast<unsigned>(bytes / record_bytes);
  const unsigned count = limit == 0 ? available : std::min(limit, available);
  FloatVectors output;
  output.count = count;
  output.dim = static_cast<unsigned>(first_dim);
  output.values.resize(static_cast<size_t>(count) * output.dim);
  input.seekg(0, std::ios::beg);
  for (unsigned row = 0; row < count; ++row) {
    int dim = 0;
    input.read(reinterpret_cast<char*>(&dim), sizeof(dim));
    if (!input || dim != first_dim) throw std::runtime_error("inconsistent fvecs dimension: " + path);
    input.read(reinterpret_cast<char*>(output.values.data() + static_cast<size_t>(row) * output.dim),
               sizeof(float) * output.dim);
    if (!input) throw std::runtime_error("truncated fvecs: " + path);
  }
  return output;
}

std::vector<unsigned> LoadTop1Ivecs(const std::string& path, unsigned expected_count) {
  std::ifstream input(path, std::ios::binary);
  if (!input) throw std::runtime_error("cannot open ivecs: " + path);
  std::vector<unsigned> result(expected_count);
  int expected_dim = -1;
  for (unsigned row = 0; row < expected_count; ++row) {
    int dim = 0;
    input.read(reinterpret_cast<char*>(&dim), sizeof(dim));
    if (!input || dim <= 0) throw std::runtime_error("truncated/invalid ivecs: " + path);
    if (expected_dim < 0) expected_dim = dim;
    if (dim != expected_dim) throw std::runtime_error("inconsistent ivecs dimension: " + path);
    input.read(reinterpret_cast<char*>(&result[row]), sizeof(unsigned));
    if (!input) throw std::runtime_error("truncated ivecs payload: " + path);
    input.seekg(static_cast<std::streamoff>(dim - 1) * sizeof(unsigned), std::ios::cur);
  }
  return result;
}

bool Exists(const std::string& path) {
  struct stat info;
  return stat(path.c_str(), &info) == 0;
}

void EnsureNewOutputDirectory(const std::string& path) {
  if (Exists(path)) throw std::runtime_error("refusing to reuse output path: " + path);
  if (mkdir(path.c_str(), 0755) != 0) {
    throw std::runtime_error("cannot create output directory " + path + ": " + std::strerror(errno));
  }
}

void WriteLine(std::ofstream& output, const std::vector<unsigned>& values) {
  for (size_t index = 0; index < values.size(); ++index) {
    if (index) output << ' ';
    output << values[index];
  }
  output << '\n';
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 11) {
    std::cerr << "Usage: " << argv[0]
              << " <base.fvecs> <query.fvecs> <gt.ivecs> <nsg> <hubs.txt>"
              << " <metric:ip|l2> <search_L> <search_K> <max_queries> <new_output_dir>\n";
    return 2;
  }

  try {
    const std::string base_path = argv[1];
    const std::string query_path = argv[2];
    const std::string gt_path = argv[3];
    const std::string nsg_path = argv[4];
    const std::string hubs_path = argv[5];
    const std::string metric_name = argv[6];
    const unsigned search_l = static_cast<unsigned>(std::stoul(argv[7]));
    const unsigned search_k = static_cast<unsigned>(std::stoul(argv[8]));
    const unsigned max_queries = static_cast<unsigned>(std::stoul(argv[9]));
    const std::string output_dir = argv[10];
    if (search_l < search_k || search_k == 0 || max_queries == 0) {
      throw std::runtime_error("require search_L >= search_K > 0 and max_queries > 0");
    }
    efanna2e::Metric metric;
    if (metric_name == "ip") {
      metric = efanna2e::INNER_PRODUCT;
    } else if (metric_name == "l2") {
      metric = efanna2e::L2;
    } else {
      throw std::runtime_error("metric must be ip or l2");
    }
    EnsureNewOutputDirectory(output_dir);

    std::cout << "Loading base vectors..." << std::endl;
    FloatVectors base = LoadFvecs(base_path);
    std::cout << "Loading up to " << max_queries << " independent training queries..." << std::endl;
    FloatVectors queries = LoadFvecs(query_path, max_queries);
    if (queries.dim != base.dim) throw std::runtime_error("base/query dimension mismatch");
    std::vector<unsigned> top1_gt = LoadTop1Ivecs(gt_path, queries.count);
    for (unsigned id : top1_gt) {
      if (id >= base.count) throw std::runtime_error("GT ID outside base range");
    }

    efanna2e::IndexNSG index(base.dim, base.count, metric, nullptr);
    index.Load(nsg_path.c_str());
    index.LoadKmeans(hubs_path.c_str());
    const unsigned num_hubs = index.iter1_num * index.iter2_num;
    if (num_hubs == 0) throw std::runtime_error("hubs.txt contains no entry points");
    std::vector<unsigned> hub_eps;
    hub_eps.reserve(num_hubs);
    for (unsigned first = 0; first < index.iter1_num; ++first) {
      if (index.iter2_eps[first].size() != index.iter2_num) {
        throw std::runtime_error("inconsistent hubs.txt hierarchy");
      }
      for (unsigned second = 0; second < index.iter2_num; ++second) {
        const unsigned ep = index.iter2_eps[first][second];
        if (ep >= base.count) throw std::runtime_error("hub entry ID outside base range");
        hub_eps.push_back(ep);
      }
    }

    efanna2e::Parameters parameters;
    parameters.Set<unsigned>("L_search", search_l);
    parameters.Set<unsigned>("P_search", search_l);
    std::ofstream positive(output_dir + "/pos_sample.txt");
    std::ofstream negative(output_dir + "/neg_sample.txt");
    if (!positive || !negative) throw std::runtime_error("cannot open sample output files");

    unsigned no_hit_queries = 0;
    unsigned long long positive_total = 0;
    unsigned long long negative_total = 0;
    std::cout << "Generating contract samples: queries=" << queries.count
              << " hubs=" << num_hubs << " metric=" << metric_name
              << " L=" << search_l << " K=" << search_k
              << " omp_threads=" << omp_get_max_threads() << std::endl;

    for (unsigned query_id = 0; query_id < queries.count; ++query_id) {
      std::vector<unsigned> hop_counts(num_hubs, std::numeric_limits<unsigned>::max());
      const float* query = queries.values.data() + static_cast<size_t>(query_id) * queries.dim;
      const unsigned gt = top1_gt[query_id];

#pragma omp parallel for schedule(static)
      for (int hub = 0; hub < static_cast<int>(num_hubs); ++hub) {
        std::vector<unsigned> result(search_k);
        unsigned expansions = 0;
        std::vector<unsigned> entries(1, hub_eps[hub]);
        index.Search(query, base.values.data(), search_k, parameters,
                     result.data(), &expansions, entries);
        if (std::find(result.begin(), result.end(), gt) != result.end()) {
          hop_counts[hub] = expansions;
        }
      }

      unsigned min_hop = std::numeric_limits<unsigned>::max();
      unsigned max_hop = 0;
      for (unsigned hop : hop_counts) {
        if (hop != std::numeric_limits<unsigned>::max()) {
          min_hop = std::min(min_hop, hop);
          max_hop = std::max(max_hop, hop);
        }
      }

      std::vector<unsigned> positives;
      std::vector<unsigned> negatives;
      if (min_hop == std::numeric_limits<unsigned>::max()) {
        ++no_hit_queries;
        positives.push_back(0);  // Preserve the public GATE fallback contract.
        negatives.resize(num_hubs);
        std::iota(negatives.begin(), negatives.end(), 0);
      } else {
        for (unsigned hub = 0; hub < num_hubs; ++hub) {
          if (hop_counts[hub] == min_hop) positives.push_back(hub);
        }
        unsigned hop_bar = 0;
        while (true) {
          const unsigned bar = max_hop > hop_bar ? max_hop - hop_bar : 0;
          negatives.clear();
          for (unsigned hub = 0; hub < num_hubs; ++hub) {
            const unsigned hop = hop_counts[hub];
            if (hop != std::numeric_limits<unsigned>::max() && hop >= bar) {
              negatives.push_back(hub);
            }
          }
          if (negatives.size() > 64 || bar <= min_hop + 1) break;
          ++hop_bar;
        }
      }
      WriteLine(positive, positives);
      WriteLine(negative, negatives);
      positive_total += positives.size();
      negative_total += negatives.size();
      if ((query_id + 1) % 25 == 0 || query_id + 1 == queries.count) {
        std::cout << "Processed " << query_id + 1 << "/" << queries.count
                  << " no_hit=" << no_hit_queries << std::endl;
      }
    }
    positive.close();
    negative.close();

    std::ofstream manifest(output_dir + "/manifest.json");
    manifest << "{\n"
             << "  \"schema_version\": 1,\n"
             << "  \"purpose\": \"GATE training samples on an independent split\",\n"
             << "  \"base\": \"" << base_path << "\",\n"
             << "  \"query\": \"" << query_path << "\",\n"
             << "  \"gt\": \"" << gt_path << "\",\n"
             << "  \"nsg\": \"" << nsg_path << "\",\n"
             << "  \"hubs\": \"" << hubs_path << "\",\n"
             << "  \"metric\": \"" << metric_name << "\",\n"
             << "  \"query_count\": " << queries.count << ",\n"
             << "  \"hub_count\": " << num_hubs << ",\n"
             << "  \"search_L\": " << search_l << ",\n"
             << "  \"search_K\": " << search_k << ",\n"
             << "  \"no_hit_queries\": " << no_hit_queries << ",\n"
             << "  \"positive_assignments\": " << positive_total << ",\n"
             << "  \"negative_assignments\": " << negative_total << "\n"
             << "}\n";
    if (!manifest) throw std::runtime_error("failed to write manifest");
    std::cout << "Done. no_hit=" << no_hit_queries
              << " positive_assignments=" << positive_total
              << " negative_assignments=" << negative_total << std::endl;
  } catch (const std::exception& error) {
    std::cerr << "ERROR: " << error.what() << std::endl;
    return 1;
  }
  return 0;
}

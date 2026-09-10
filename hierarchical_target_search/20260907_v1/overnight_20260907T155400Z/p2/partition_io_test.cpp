#define main partition_tool_main
#include "partition_graph.cpp"
#undef main
int main(int argc,char** argv) {
    if(argc!=2)return 2;
    MappedGraph graph(argv[1]);
    if(graph.h.n!=6||graph.h.d!=2||graph.h.k!=64||graph.h.adjacency_offset!=143)return 3;
    std::vector<int32_t> original(6*64);
    for(size_t i=0;i<original.size();++i)original[i]=neighbor_at(graph.adjacency,i);
    CSR csr=symmetrize(graph.adjacency,6,64,2);check_csr_exact(csr,original,64);
    json hashes=json::object();
    for(size_t n:{0,3,55,56,63,64,65,127,128,129,1000,65536}) {
        std::vector<uint8_t> values(n);for(size_t i=0;i<n;++i)values[i]=i%251;
        hashes[std::to_string(n)]=sha256_bytes(values.data(),values.size());
    }
    std::cout<<"IO_TEST_JSON "<<json({{"status","PASS_NATIVE_V1_UNALIGNED_MMAP"},{"fixture_bytes",graph.h.bytes},
        {"adjacency_offset",graph.h.adjacency_offset},{"csr_exact",true},{"hashes",hashes}}).dump()<<std::endl;
}

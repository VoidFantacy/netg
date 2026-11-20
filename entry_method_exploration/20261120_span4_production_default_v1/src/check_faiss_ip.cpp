#include <faiss/utils/distances.h>
#include <array>
#include <vector>
#include <random>
#include <cstdint>
#include <cstring>
#include <iostream>

int main() {
    std::mt19937 gen(1107);
    std::uniform_real_distribution<float> vals(-2.f, 2.f);
    size_t diff=0,cases=0;
    for (size_t d=1;d<=2048;++d) {
        std::vector<float> q(d);
        std::array<std::vector<float>,4> neighbors;
        for (auto& row:neighbors) row.resize(d);
        bool reported=false;
        for (int trial=0;trial<16;++trial) {
            for (float& v:q) v=vals(gen);
            for (auto& row:neighbors) for (float& v:row) v=vals(gen);
            float x[4];
            faiss::fvec_inner_product_batch_4(q.data(),neighbors[0].data(),neighbors[1].data(),
                neighbors[2].data(),neighbors[3].data(),d,x[0],x[1],x[2],x[3]);
            for (int k=0;k<4;++k) {
                float scalar=faiss::fvec_inner_product(q.data(),neighbors[k].data(),d);
                ++cases;
                if (std::memcmp(&scalar,&x[k],sizeof(float))==0) continue;
                ++diff;
                if (!reported) std::cout<<d<<" "<<scalar<<" "<<x[k]<<"\n";
                reported=true;
            }
        }
    }
    std::cout<<"products="<<cases<<" different="<<diff<<"\n";
}

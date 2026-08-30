#include <cmath>
#include <iostream>

#include <efanna2e/distance.h>

int main() {
    // GATE's SIMD distance kernels require dimensions aligned to 8 floats.
    const float query[] = {1.0f, 2.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
    const float better_ip[] = {2.0f, 3.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
    const float worse_ip[] = {-1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
    efanna2e::DistanceNegativeInnerProduct distance;
    const float better = distance.compare(query, better_ip, 8);
    const float worse = distance.compare(query, worse_ip, 8);
    if (!(better < worse) || std::fabs(better + 8.0f) > 1e-6f) {
        std::cerr << "negative-IP ordering contract failed\n";
        return 1;
    }
    std::cout << "GATE_IP_METRIC_CONTRACT_OK\n";
    return 0;
}

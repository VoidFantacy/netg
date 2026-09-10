#include "ACSG/RegionalSearch.h"
#include <iostream>
int main() {
    int l, region_count, regional, uniform, active;
    while (std::cin >> l >> region_count >> regional >> uniform >> active) {
        acsg::regional::Route route; route.active = active;
        for (int i=0; i<active; ++i) std::cin >> route.regions[i] >> route.weights[i];
        std::array<int,5> caps{};
        const int nq=acsg::regional::allocate(route,l,region_count,regional,uniform,caps);
        std::cout << nq;
        for(int i=0; i<nq; ++i) std::cout << " " << caps[i];
        std::cout << "\n";
    }
}

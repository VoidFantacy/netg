#pragma once

#include <ACSG/ACSG.h>
#include <algorithm>
#include <cstring>

namespace acsg {
namespace detail {

// Preserve the legacy binary search and equal-distance ordering. Only the
// live prefix needs to move while the rest of the pool contains empty slots.
// capacity >= 1; 1 <= live_count <= capacity; storage has capacity + 1 slots.
inline int insert_into_pool_live(
        Neighbor* addr, int capacity, int live_count, Neighbor nn) {
    int left = 0, right = capacity - 1;
    if (addr[left].distance > nn.distance) {
        std::memmove(addr + 1, addr, live_count * sizeof(Neighbor));
        addr[0] = nn;
        return 0;
    }
    if (addr[right].distance < nn.distance) {
        addr[capacity] = nn;
        return capacity;
    }
    while (left < right - 1) {
        int mid = (left + right) / 2;
        if (addr[mid].distance > nn.distance) {
            right = mid;
        } else {
            left = mid;
        }
    }
    while (left > 0) {
        if (addr[left].distance < nn.distance) {
            break;
        }
        if (addr[left].id == nn.id) {
            return capacity + 1;
        }
        --left;
    }
    if (addr[left].id == nn.id || addr[right].id == nn.id) {
        return capacity + 1;
    }
    std::memmove(addr + right + 1, addr + right,
                 std::max(0, live_count - right) * sizeof(Neighbor));
    addr[right] = nn;
    return right;
}

} // namespace detail
} // namespace acsg

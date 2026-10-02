#pragma once
using acsg::Neighbor;
    inline int legacy_insert(Neighbor *addr, int K, Neighbor nn)
    {
        // find the location to insert
        int left = 0, right = K - 1;
        if (addr[left].distance > nn.distance)
        {
            memmove(&addr[left + 1], &addr[left], K * sizeof(Neighbor));
            addr[left] = nn;
            return left;
        }
        if (addr[right].distance < nn.distance)
        {
            addr[K] = nn;
            return K;
        }
        while (left < right - 1)
        {
            int mid = (left + right) / 2;
            if (addr[mid].distance > nn.distance)
            {
                right = mid;
            }
            else
            {
                left = mid;
            }
        }
        // check equal ID

        while (left > 0)
        {
            if (addr[left].distance < nn.distance)
            {
                break;
            }
            if (addr[left].id == nn.id)
            {
                return K + 1;
            }
            left--;
        }
        if (addr[left].id == nn.id || addr[right].id == nn.id)
        {
            return K + 1;
        }
        memmove(&addr[right + 1], &addr[right], (K - right) * sizeof(Neighbor));
        addr[right] = nn;
        return right;
    }

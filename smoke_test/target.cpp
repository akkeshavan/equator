#include <stdint.h>

extern "C" int32_t compute_offset(int32_t base, int32_t delta, uint32_t mask) {
    if (delta < 0) return -1;
    int32_t shifted = (base + delta) >> 2;
    return shifted & (int32_t)(mask & 0x7FFFFFFF);
}

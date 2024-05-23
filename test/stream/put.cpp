#include "hls_stream.h"

extern "C" void put(
    hls::stream<char>& channel,
    char* dst,
    const unsigned size
) {
    for (unsigned i = 0; i < size; i++) {
        #pragma HLS PIPELINE II=1
        dst[i] = channel.read();
    }
}

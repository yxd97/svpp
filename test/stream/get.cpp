#include "hls_stream.h"

extern "C" void get(
    const char* src,
    hls::stream<char>& channel,
    const unsigned size
) {
    for (unsigned i = 0; i < size; i++) {
        #pragma HLS PIPELINE II=1
        channel.write(src[i]);
    }
}

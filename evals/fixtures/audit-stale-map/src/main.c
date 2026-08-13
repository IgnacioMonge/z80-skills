#include <stdint.h>

static uint8_t buffer[8];

void copy_packet(const uint8_t *source, uint8_t count) {
    uint8_t index;

    for (index = 0; index <= count; ++index) {
        buffer[index] = source[index];
    }
}

void receive_full_packet(const uint8_t *source) {
    copy_packet(source, sizeof(buffer));
}

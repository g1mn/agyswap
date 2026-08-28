#ifndef RING_BUFFER_H
#define RING_BUFFER_H

struct RingBuffer {
    unsigned char *data;
    unsigned int capacity;
};

int ring_push(struct RingBuffer *rb, unsigned char byte);
int ring_pop(struct RingBuffer *rb);

#endif

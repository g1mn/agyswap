#include "ring_buffer.h"

class RingBufferView {
public:
    explicit RingBufferView(RingBuffer *rb) : rb_(rb) {}

    unsigned int capacity() const {
        return rb_->capacity;
    }

    virtual bool isEmpty() const {
        return rb_->capacity == 0;
    }

private:
    RingBuffer *rb_;
};

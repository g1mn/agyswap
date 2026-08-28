#include <stdlib.h>

struct MemBlock {
    void *ptr;
    size_t size;
};

static inline int is_free(struct MemBlock *b) {
    return b->ptr == NULL;
}

int pool_alloc(size_t size) {
    if (size == 0) {
        return -1;
    }
    return 0;
}

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdbool.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>

// MorphAssembly VM v0.6

#define STACK_SIZE 1024
#define MAX_CONTEXTS 16

// Opcode Definitions
#define OP_NOP    0x00
#define OP_PUSH   0x01
#define OP_POP    0x02
#define OP_ADD    0x03
#define OP_SUB    0x04
#define OP_JMP    0x05
#define OP_JZ     0x06
#define OP_EQ     0x07
#define OP_DUP    0x08
#define OP_PRINT  0x09
#define OP_LOAD   0x0A
#define OP_STORE  0x0B
#define OP_BREAK  0x10
#define OP_SYSCALL 0x11
#define OP_SPAWN  0x20
#define OP_YIELD  0x21
#define OP_JOIN   0x22

// Syscall IDs
#define SYS_EXIT  0
#define SYS_OPEN  1
#define SYS_CLOSE 2
#define SYS_READ  3
#define SYS_WRITE 4
#define SYS_SBRK  5

// Context Structure (Fragment)
typedef struct {
    uint64_t ip;
    uint64_t stack[STACK_SIZE];
    uint64_t sp;
    bool active;
    bool joined; // If true, another context is waiting for this to finish? Or this is waiting?
                 // Simple join: Context X waits for Context Y.
                 // Let's keep it simple: No explicit join waiting logic in struct yet, just simple round robin.
} Context;

// VM State
typedef struct {
    uint8_t *code;
    size_t code_size;

    // Global Memory
    uint8_t *heap;
    size_t heap_capacity;

    // Scheduler
    Context contexts[MAX_CONTEXTS];
    int current_context_id;
    int active_count;
} VM;

VM vm;
bool debug_mode = false;
bool step_mode = false;

void error(const char *msg) {
    fprintf(stderr, "Error [Ctx %d]: %s\n", vm.current_context_id, msg);
    exit(1);
}

// Context Helpers
Context* current_ctx() {
    return &vm.contexts[vm.current_context_id];
}

void push(uint64_t value) {
    Context *c = current_ctx();
    if (c->sp >= STACK_SIZE) error("Stack Overflow");
    c->stack[c->sp++] = value;
}

uint64_t pop() {
    Context *c = current_ctx();
    if (c->sp == 0) error("Stack Underflow");
    return c->stack[--c->sp];
}

uint64_t peek() {
    Context *c = current_ctx();
    if (c->sp == 0) error("Stack Underflow");
    return c->stack[c->sp - 1];
}

// Scheduler
void schedule() {
    int start = vm.current_context_id;
    int next = (start + 1) % MAX_CONTEXTS;

    while (next != start) {
        if (vm.contexts[next].active) {
            vm.current_context_id = next;
            return;
        }
        next = (next + 1) % MAX_CONTEXTS;
    }
    // No other active context found, stay on current (if active)
    if (!vm.contexts[start].active) {
        // All dead
        exit(0);
    }
}

// Debugger Shell
void debug_shell() {
    char cmd[256];
    printf("\n--- Debugger (Ctx: %d, IP: %lu) ---\n", vm.current_context_id, current_ctx()->ip);

    while (1) {
        printf("(dbg) ");
        if (!fgets(cmd, sizeof(cmd), stdin)) break;
        cmd[strcspn(cmd, "\n")] = 0;

        if (strcmp(cmd, "s") == 0 || strcmp(cmd, "step") == 0) {
            step_mode = true;
            break;
        } else if (strcmp(cmd, "c") == 0 || strcmp(cmd, "continue") == 0) {
            step_mode = false;
            break;
        } else if (strcmp(cmd, "st") == 0 || strcmp(cmd, "stack") == 0) {
            Context *c = current_ctx();
            printf("Stack [%lu]:\n", c->sp);
            for (int i = 0; i < c->sp; i++) {
                printf("  [%d] %lu (0x%lX)\n", i, c->stack[i], c->stack[i]);
            }
        } else if (strncmp(cmd, "m", 1) == 0) {
            uint64_t addr = 0;
            int len = 16;
            sscanf(cmd + 1, "%lu %d", &addr, &len);
            if (vm.heap_capacity < 8 && len > 0) { printf("Heap too small\n"); continue; }
            if (addr + len > vm.heap_capacity) len = vm.heap_capacity - addr;

            printf("Memory [%lu..%lu]:\n", addr, addr+len);
            for (int i = 0; i < len; i++) {
                printf("%02X ", vm.heap[addr+i]);
                if ((i+1)%16 == 0) printf("\n");
            }
            printf("\n");
        } else if (strcmp(cmd, "q") == 0 || strcmp(cmd, "quit") == 0) {
            exit(0);
        } else {
            printf("Commands: s, c, st, m <addr> <len>, q\n");
        }
    }
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s [--debug] <binary_file>\n", argv[0]);
        return 1;
    }

    const char *filename;
    if (strcmp(argv[1], "--debug") == 0 || strcmp(argv[1], "-d") == 0) {
        debug_mode = true;
        filename = argv[2];
        printf("Debugger Mode Enabled.\n");
    } else {
        filename = argv[1];
    }

    FILE *f = fopen(filename, "rb");
    if (!f) error("Could not open file");
    fseek(f, 0, SEEK_END);
    vm.code_size = ftell(f);
    fseek(f, 0, SEEK_SET);
    vm.code = malloc(vm.code_size);
    if (!vm.code) error("Memory allocation failed");
    if (fread(vm.code, 1, vm.code_size, f) != vm.code_size) error("Read failed");
    fclose(f);

    // Init Global State
    vm.heap = NULL;
    vm.heap_capacity = 0;

    // Init Main Context (ID 0)
    for (int i=0; i<MAX_CONTEXTS; i++) vm.contexts[i].active = false;
    vm.contexts[0].active = true;
    vm.contexts[0].ip = 0;
    vm.contexts[0].sp = 0;
    vm.current_context_id = 0;
    vm.active_count = 1;

    // Execution Loop
    while (vm.active_count > 0) {
        Context *ctx = current_ctx();

        // Check bounds
        if (ctx->ip >= vm.code_size) {
            // Implicit exit of context if it runs out of code
            ctx->active = false;
            vm.active_count--;
            schedule();
            continue;
        }

        if (debug_mode && step_mode) debug_shell();

        uint8_t opcode = vm.code[ctx->ip++];

        switch (opcode) {
            case OP_NOP: break;
            case OP_PUSH: {
                if (ctx->ip + 8 > vm.code_size) error("Unexpected EOF in PUSH");
                uint64_t val = 0;
                for (int i = 0; i < 8; i++) val |= ((uint64_t)vm.code[ctx->ip++]) << (i * 8);
                push(val);
                break;
            }
            case OP_POP: pop(); break;
            case OP_ADD: { uint64_t b = pop(); uint64_t a = pop(); push(a + b); break; }
            case OP_SUB: { uint64_t b = pop(); uint64_t a = pop(); push(a - b); break; }
            case OP_JMP: {
                int32_t offset = 0;
                for (int i = 0; i < 4; i++) offset |= ((uint32_t)vm.code[ctx->ip++]) << (i * 8);
                ctx->ip += offset;
                break;
            }
            case OP_JZ: {
                int32_t offset = 0;
                for (int i = 0; i < 4; i++) offset |= ((uint32_t)vm.code[ctx->ip++]) << (i * 8);
                if (pop() == 0) ctx->ip += offset;
                break;
            }
            case OP_EQ: { uint64_t b = pop(); uint64_t a = pop(); push(a == b ? 1 : 0); break; }
            case OP_DUP: push(peek()); break;
            case OP_PRINT: printf("%lu\n", pop()); break;
            case OP_LOAD: {
                uint64_t addr = pop();
                if (vm.heap_capacity < 8 || addr > vm.heap_capacity - 8) error("Heap Out of Bounds (LOAD)");
                uint64_t val = 0;
                for(int i=0; i<8; i++) val |= ((uint64_t)vm.heap[addr + i]) << (i*8);
                push(val);
                break;
            }
            case OP_STORE: {
                uint64_t addr = pop();
                uint64_t val = pop();
                if (vm.heap_capacity < 8 || addr > vm.heap_capacity - 8) error("Heap Out of Bounds (STORE)");
                for(int i=0; i<8; i++) vm.heap[addr + i] = (val >> (i*8)) & 0xFF;
                break;
            }
            case OP_BREAK: {
                if (debug_mode) { printf("[BREAK] Ctx: %d IP: %lu\n", vm.current_context_id, ctx->ip - 1); debug_shell(); }
                break;
            }

            // --- CONCURRENCY OPCODES ---
            case OP_SPAWN: {
                uint64_t func_addr = pop();
                int new_id = -1;
                for (int i=0; i<MAX_CONTEXTS; i++) {
                    if (!vm.contexts[i].active) { new_id = i; break; }
                }
                if (new_id == -1) error("Max Contexts Exceeded");

                vm.contexts[new_id].active = true;
                vm.contexts[new_id].ip = func_addr;
                vm.contexts[new_id].sp = 0;
                vm.active_count++;
                // Push ID of new thread to parent? Maybe.
                break;
            }
            case OP_YIELD: {
                schedule();
                break;
            }

            case OP_SYSCALL: {
                uint64_t id = pop();
                switch (id) {
                    case SYS_EXIT: {
                        uint64_t code = pop();
                        // Exit Process or Context?
                        // Syscall EXIT usually means Process Exit.
                        // To exit just the thread, we should implementation a THREAD_EXIT opcode or syscall.
                        // But for now, let's say EXIT terminates EVERYTHING.
                        exit((int)code);
                        break;
                    }
                    case SYS_OPEN: {
                        uint64_t mode = pop();
                        uint64_t ptr = pop();
                        if (ptr >= vm.heap_capacity) error("Heap Ptr Out of Bounds");
                        bool safe = false;
                        for (size_t i = ptr; i < vm.heap_capacity; i++) { if (vm.heap[i] == '\0') { safe = true; break; } }
                        if (!safe) error("String unsafe");
                        char *filename = (char*)&vm.heap[ptr];
                        int flags = (mode == 1) ? (O_WRONLY | O_CREAT | O_TRUNC) : O_RDONLY;
                        push((uint64_t)open(filename, flags, 0644));
                        break;
                    }
                    case SYS_CLOSE: close((int)pop()); break;
                    case SYS_READ: {
                        uint64_t len = pop(); uint64_t ptr = pop(); uint64_t fd = pop();
                        if (ptr + len > vm.heap_capacity) error("Heap Bounds");
                        push((uint64_t)read((int)fd, &vm.heap[ptr], len));
                        break;
                    }
                    case SYS_WRITE: {
                        uint64_t len = pop(); uint64_t ptr = pop(); uint64_t fd = pop();
                        if (ptr + len > vm.heap_capacity) error("Heap Bounds");
                        write((int)fd, &vm.heap[ptr], len);
                        break;
                    }
                    case SYS_SBRK: {
                        uint64_t inc = pop();
                        uint64_t old = vm.heap_capacity;
                        uint8_t *n = realloc(vm.heap, vm.heap_capacity + inc);
                        if (!n) error("SBRK Fail");
                        memset(n + vm.heap_capacity, 0, inc);
                        vm.heap = n;
                        vm.heap_capacity += inc;
                        push(old);
                        break;
                    }
                    default: error("Unknown Syscall");
                }
                break;
            }
            default: error("Unknown Opcode");
        }
    }

    free(vm.code);
    if (vm.heap) free(vm.heap);
    return 0;
}

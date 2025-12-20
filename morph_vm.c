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

// Syscall IDs
#define SYS_EXIT  0
#define SYS_OPEN  1
#define SYS_CLOSE 2
#define SYS_READ  3
#define SYS_WRITE 4
#define SYS_SBRK  5

// VM State
typedef struct {
    uint8_t *code;
    size_t code_size;
    uint64_t ip; // Instruction Pointer

    uint64_t stack[STACK_SIZE];
    uint64_t sp; // Stack Pointer (index of next empty slot)

    uint8_t *heap;
    size_t heap_capacity;
} VM;

VM vm;
bool debug_mode = false;
bool step_mode = false;

void error(const char *msg) {
    fprintf(stderr, "Error: %s\n", msg);
    exit(1);
}

void push(uint64_t value) {
    if (vm.sp >= STACK_SIZE) error("Stack Overflow");
    vm.stack[vm.sp++] = value;
}

uint64_t pop() {
    if (vm.sp == 0) error("Stack Underflow");
    return vm.stack[--vm.sp];
}

uint64_t peek() {
    if (vm.sp == 0) error("Stack Underflow");
    return vm.stack[vm.sp - 1];
}

// Debugger Shell
void debug_shell() {
    char cmd[256];
    printf("\n--- Debugger (IP: %lu) ---\n", vm.ip);

    while (1) {
        printf("(dbg) ");
        if (!fgets(cmd, sizeof(cmd), stdin)) break;

        // Remove newline
        cmd[strcspn(cmd, "\n")] = 0;

        if (strcmp(cmd, "s") == 0 || strcmp(cmd, "step") == 0) {
            step_mode = true;
            break;
        } else if (strcmp(cmd, "c") == 0 || strcmp(cmd, "continue") == 0) {
            step_mode = false;
            break;
        } else if (strcmp(cmd, "st") == 0 || strcmp(cmd, "stack") == 0) {
            printf("Stack [%lu]:\n", vm.sp);
            for (int i = 0; i < vm.sp; i++) {
                printf("  [%d] %lu (0x%lX)\n", i, vm.stack[i], vm.stack[i]);
            }
        } else if (strncmp(cmd, "m", 1) == 0) {
            // usage: m <addr> <len>
            uint64_t addr = 0;
            int len = 16;
            sscanf(cmd + 1, "%lu %d", &addr, &len);
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
            printf("Commands: s (step), c (continue), st (stack), m <addr> <len> (memory), q (quit)\n");
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

    // Load Binary
    FILE *f = fopen(filename, "rb");
    if (!f) error("Could not open file");
    fseek(f, 0, SEEK_END);
    vm.code_size = ftell(f);
    fseek(f, 0, SEEK_SET);
    vm.code = malloc(vm.code_size);
    if (!vm.code) error("Memory allocation failed");
    if (fread(vm.code, 1, vm.code_size, f) != vm.code_size) error("Read failed");
    fclose(f);

    // Init VM
    vm.ip = 0;
    vm.sp = 0;
    vm.heap = NULL;
    vm.heap_capacity = 0;

    // Execution Loop
    while (vm.ip < vm.code_size) {
        // Debugger Hook
        if (debug_mode && step_mode) {
            debug_shell();
        }

        uint8_t opcode = vm.code[vm.ip++];

        switch (opcode) {
            case OP_NOP:
                break;
            case OP_PUSH: {
                if (vm.ip + 8 > vm.code_size) error("Unexpected EOF in PUSH");
                uint64_t val = 0;
                // Read 64-bit integer (Little Endian)
                for (int i = 0; i < 8; i++) {
                    val |= ((uint64_t)vm.code[vm.ip++]) << (i * 8);
                }
                push(val);
                break;
            }
            case OP_POP:
                pop();
                break;
            case OP_ADD: {
                uint64_t b = pop();
                uint64_t a = pop();
                push(a + b);
                break;
            }
            case OP_SUB: {
                uint64_t b = pop();
                uint64_t a = pop();
                push(a - b);
                break;
            }
            case OP_JMP: {
                if (vm.ip + 4 > vm.code_size) error("Unexpected EOF in JMP");
                int32_t offset = 0;
                for (int i = 0; i < 4; i++) {
                    offset |= ((uint32_t)vm.code[vm.ip++]) << (i * 8);
                }
                vm.ip += offset; // Relative jump
                break;
            }
            case OP_JZ: {
                if (vm.ip + 4 > vm.code_size) error("Unexpected EOF in JZ");
                int32_t offset = 0;
                for (int i = 0; i < 4; i++) {
                    offset |= ((uint32_t)vm.code[vm.ip++]) << (i * 8);
                }
                uint64_t a = pop();
                if (a == 0) {
                    vm.ip += offset;
                }
                break;
            }
            case OP_EQ: {
                uint64_t b = pop();
                uint64_t a = pop();
                push(a == b ? 1 : 0);
                break;
            }
            case OP_DUP:
                push(peek());
                break;
            case OP_PRINT:
                printf("%lu\n", pop());
                break;
            case OP_LOAD: {
                uint64_t addr = pop();
                if (vm.heap_capacity < 8 || addr > vm.heap_capacity - 8) error("Heap Out of Bounds (LOAD)");

                uint64_t val = 0;
                for(int i=0; i<8; i++) {
                    val |= ((uint64_t)vm.heap[addr + i]) << (i*8);
                }
                push(val);
                break;
            }
            case OP_STORE: {
                uint64_t addr = pop();
                uint64_t val = pop();
                if (vm.heap_capacity < 8 || addr > vm.heap_capacity - 8) error("Heap Out of Bounds (STORE)");
                for(int i=0; i<8; i++) {
                    vm.heap[addr + i] = (val >> (i*8)) & 0xFF;
                }
                break;
            }
            case OP_BREAK: {
                if (debug_mode) {
                    printf("[BREAK] Hit breakpoint at IP: %lu\n", vm.ip - 1);
                    debug_shell();
                }
                break;
            }
            case OP_SYSCALL: {
                uint64_t id = pop();
                switch (id) {
                    case SYS_EXIT: {
                        uint64_t code = pop();
                        exit((int)code);
                        break;
                    }
                    case SYS_OPEN: {
                        uint64_t mode = pop();
                        uint64_t ptr = pop();
                        if (ptr >= vm.heap_capacity) error("Heap Ptr Out of Bounds");
                        // Scan for null terminator
                        bool safe = false;
                        for (size_t i = ptr; i < vm.heap_capacity; i++) {
                            if (vm.heap[i] == '\0') {
                                safe = true;
                                break;
                            }
                        }
                        if (!safe) error("String not null-terminated or out of bounds");
                        char *filename = (char*)&vm.heap[ptr];
                        int flags = (mode == 1) ? (O_WRONLY | O_CREAT | O_TRUNC) : O_RDONLY;
                        int fd = open(filename, flags, 0644);
                        push((uint64_t)fd);
                        break;
                    }
                    case SYS_CLOSE: {
                        uint64_t fd = pop();
                        close((int)fd);
                        break;
                    }
                    case SYS_READ: {
                        uint64_t len = pop();
                        uint64_t ptr = pop();
                        uint64_t fd = pop();
                        if (ptr > vm.heap_capacity || len > vm.heap_capacity || ptr + len > vm.heap_capacity) error("Heap Buffer Out of Bounds");
                        ssize_t n = read((int)fd, &vm.heap[ptr], len);
                        push((uint64_t)n);
                        break;
                    }
                    case SYS_WRITE: {
                        uint64_t len = pop();
                        uint64_t ptr = pop();
                        uint64_t fd = pop();
                        if (ptr > vm.heap_capacity || len > vm.heap_capacity || ptr + len > vm.heap_capacity) error("Heap Buffer Out of Bounds");
                        write((int)fd, &vm.heap[ptr], len);
                        break;
                    }
                    case SYS_SBRK: {
                        uint64_t increment = pop();
                        uint64_t old_break = vm.heap_capacity;
                        size_t new_size = vm.heap_capacity + increment;
                        uint8_t *new_heap = realloc(vm.heap, new_size);
                        if (!new_heap) error("SBRK Memory Allocation Failed");

                        // Initialize new memory to 0
                        memset(new_heap + vm.heap_capacity, 0, increment);

                        vm.heap = new_heap;
                        vm.heap_capacity = new_size;
                        push(old_break);
                        break;
                    }
                    default:
                        printf("Unknown Syscall ID: %lu\n", id);
                        exit(1);
                }
                break;
            }
            default:
                printf("Unknown Opcode: 0x%02X at %lu\n", opcode, vm.ip - 1);
                exit(1);
        }
    }

    free(vm.code);
    if (vm.heap) free(vm.heap);
    return 0;
}

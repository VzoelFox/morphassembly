#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

// MorphAssembly Test Generator

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
#define OP_AND    0x12
#define OP_OR     0x13
#define OP_XOR    0x14
#define OP_NOT    0x15
#define OP_SHL    0x16
#define OP_SHR    0x17
#define OP_SPAWN  0x20
#define OP_YIELD  0x21
#define OP_JOIN   0x22

// Syscall IDs
#define SYS_EXIT  0
#define SYS_THREAD_EXIT 6

FILE *f;

void emit_u8(uint8_t v) {
    fwrite(&v, 1, 1, f);
}

void emit_u32(uint32_t v) {
    fwrite(&v, 4, 1, f);
}

void emit_u64(uint64_t v) {
    fwrite(&v, 8, 1, f);
}

int main() {
    f = fopen("test.bin", "wb");
    if (!f) return 1;

    printf("Generating Comprehensive Test for Bitwise and Concurrency...\n");

    // --- Header ---
    uint32_t magic = 0x4D4F5250;
    fwrite(&magic, 4, 1, f);
    emit_u8(0x01); // Version
    emit_u8(0x00); emit_u8(0x00); emit_u8(0x00); // Reserved

    // --- PART 1: Bitwise Operations Test ---
    // 1. AND: 5 & 3 = 1
    emit_u8(OP_PUSH); emit_u64(5);
    emit_u8(OP_PUSH); emit_u64(3);
    emit_u8(OP_AND);
    emit_u8(OP_PRINT);
    // 2. OR: 5 | 3 = 7
    emit_u8(OP_PUSH); emit_u64(5);
    emit_u8(OP_PUSH); emit_u64(3);
    emit_u8(OP_OR);
    emit_u8(OP_PRINT);
    // 3. XOR: 5 ^ 3 = 6
    emit_u8(OP_PUSH); emit_u64(5);
    emit_u8(OP_PUSH); emit_u64(3);
    emit_u8(OP_XOR);
    emit_u8(OP_PRINT);
    // 4. NOT: ~5
    emit_u8(OP_PUSH); emit_u64(5);
    emit_u8(OP_NOT);
    emit_u8(OP_PRINT);
    // 5. SHL: 5 << 2 = 20
    emit_u8(OP_PUSH); emit_u64(5);
    emit_u8(OP_PUSH); emit_u64(2);
    emit_u8(OP_SHL);
    emit_u8(OP_PRINT);
    // 6. SHR: 20 >> 2 = 5
    emit_u8(OP_PUSH); emit_u64(20);
    emit_u8(OP_PUSH); emit_u64(2);
    emit_u8(OP_SHR);
    emit_u8(OP_PRINT);

    // --- PART 2: Concurrency (JOIN) Test ---

    // The concurrency test needs to jump over its worker function.
    // Let's calculate the start address of the main logic and the worker function.
    long bitwise_tests_end_pos = ftell(f);

    // Worker function size:
    // PUSH 888, PRINT (10) + PUSH 999, PRINT (10) + PUSH SYS_THREAD_EXIT, SYSCALL (10) = 30 bytes
    long worker_size = 30;

    // The JMP instruction is 5 bytes. It will be placed right after the bitwise tests.
    // The worker function will be placed after the JMP.
    // The main concurrency logic will be placed after the worker function.

    // The address of the worker will be the end of the bitwise tests + size of the JMP instruction.
    long worker_address = bitwise_tests_end_pos + 5;

    // The JMP needs to jump *over* the worker function. So the offset is the worker's size.
    emit_u8(OP_JMP);
    emit_u32((uint32_t)worker_size);

    // Write the Worker Function (at calculated worker_address)
    emit_u8(OP_PUSH); emit_u64(888);
    emit_u8(OP_PRINT);
    emit_u8(OP_PUSH); emit_u64(999);
    emit_u8(OP_PRINT);
    emit_u8(OP_PUSH); emit_u64(SYS_THREAD_EXIT);
    emit_u8(OP_SYSCALL);

    // Write the Main Concurrency Logic
    emit_u8(OP_PUSH); emit_u64(111); // "Main Start"
    emit_u8(OP_PRINT);

    emit_u8(OP_PUSH); emit_u64(worker_address); // Worker address
    emit_u8(OP_SPAWN);                          // Returns child ID

    emit_u8(OP_DUP);                            // Dup the ID for printing
    emit_u8(OP_PRINT);                          // Print the ID

    emit_u8(OP_JOIN);                           // Wait for worker to finish

    emit_u8(OP_PUSH); emit_u64(222);            // "Main After Join"
    emit_u8(OP_PRINT);

    // --- Final Exit ---
    emit_u8(OP_PUSH); emit_u64(0);
    emit_u8(OP_PUSH); emit_u64(SYS_EXIT);
    emit_u8(OP_SYSCALL);

    fclose(f);
    printf("Generated test.bin\n");
    return 0;
}

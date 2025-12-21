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

    printf("Generating Concurrency (JOIN) Test...\n");

    // --- Header ---
    uint32_t magic = 0x4D4F5250;
    fwrite(&magic, 4, 1, f);
    emit_u8(0x01); // Version
    emit_u8(0x00); emit_u8(0x00); emit_u8(0x00); // Reserved

    // --- Worker Function Size Calculation ---
    // PUSH 888, PRINT (10) + PUSH 999, PRINT (10) + PUSH SYS_THREAD_EXIT, SYSCALL (10) = 30 bytes
    long worker_size = 30;

    // JMP over worker. IP starts at 13 (after JMP instr). Target is 13 + 30 = 43. Offset is 30.
    long worker_address = 13;

    // --- JMP to Main ---
    emit_u8(OP_JMP);
    emit_u32((uint32_t)worker_size);

    // --- Worker Function ---
    emit_u8(OP_PUSH); emit_u64(888);
    emit_u8(OP_PRINT);
    emit_u8(OP_PUSH); emit_u64(999);
    emit_u8(OP_PRINT);
    emit_u8(OP_PUSH); emit_u64(SYS_THREAD_EXIT);
    emit_u8(OP_SYSCALL);

    // --- Main Logic ---
    emit_u8(OP_PUSH); emit_u64(111);
    emit_u8(OP_PRINT);
    emit_u8(OP_PUSH); emit_u64(worker_address);
    emit_u8(OP_SPAWN);
    emit_u8(OP_DUP);
    emit_u8(OP_PRINT);
    emit_u8(OP_JOIN);
    emit_u8(OP_PUSH); emit_u64(222);
    emit_u8(OP_PRINT);

    // --- Final Exit ---
    emit_u8(OP_PUSH); emit_u64(0);
    emit_u8(OP_PUSH); emit_u64(SYS_EXIT);
    emit_u8(OP_SYSCALL);

    fclose(f);
    printf("Generated test.bin\n");
    return 0;
}

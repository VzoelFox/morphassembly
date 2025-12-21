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

    printf("Generating final JOIN test with Thread Exit...\n");

    // --- Final Structure ---
    // 1. Header (8 bytes)
    // 2. JMP (5 bytes) -> Jumps over worker
    // 3. Worker (30 bytes)
    // 4. Main (...)

    // --- Calculate Worker Size ---
    // PUSH 888, PRINT: 10 bytes
    // PUSH 999, PRINT: 10 bytes
    // PUSH SYS_THREAD_EXIT, SYSCALL: 10 bytes
    // TOTAL Worker: 30 bytes

    // --- Calculate JMP Offset ---
    // JMP is at file position 8.
    // After JMP instruction is read, IP will be 8 + 5 = 13.
    // Worker code starts at 13.
    // Main code starts at 13 + 30 = 43.
    // The JMP needs to go from IP=13 to address 43.
    // Offset = 43 - 13 = 30.

    // --- Generation ---
    // Header
    uint32_t magic = 0x4D4F5250;
    fwrite(&magic, 4, 1, f);
    emit_u8(0x01);
    emit_u8(0x00); emit_u8(0x00); emit_u8(0x00);

    // JMP to Main
    emit_u8(OP_JMP);
    emit_u32(30); // Jump over the worker code (30 bytes)

    // Worker Function (starts at address 13)
    emit_u8(OP_PUSH); emit_u64(888);
    emit_u8(OP_PRINT);
    emit_u8(OP_PUSH); emit_u64(999);
    emit_u8(OP_PRINT);
    emit_u8(OP_PUSH); emit_u64(SYS_THREAD_EXIT); // Push syscall ID
    emit_u8(OP_SYSCALL);                         // Exit this thread

    // Main Function (starts at address 43)
    emit_u8(OP_PUSH); emit_u64(111); // "Main Start"
    emit_u8(OP_PRINT);

    emit_u8(OP_PUSH); emit_u64(13);  // Worker address
    emit_u8(OP_SPAWN);               // Returns child ID

    emit_u8(OP_DUP);                 // Dup the ID for printing
    emit_u8(OP_PRINT);               // Print the ID

    emit_u8(OP_JOIN);                // Wait for worker to finish

    emit_u8(OP_PUSH); emit_u64(222); // "Main After Join"
    emit_u8(OP_PRINT);

    emit_u8(OP_PUSH); emit_u64(0);        // Exit code
    emit_u8(OP_PUSH); emit_u64(SYS_EXIT); // Syscall ID
    emit_u8(OP_SYSCALL);                 // Exit whole VM

    fclose(f);
    printf("Generated test.bin\n");
    return 0;
}

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

// Syscall IDs
#define SYS_EXIT  0
#define SYS_SBRK  5

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

    printf("Generating Concurrency Test with Header...\n");

    // --- Header ---
    // Magic: "MORP" (0x4D4F5250)
    // Version: 0x01
    // Padding/Reserved: 3 bytes
    uint32_t magic = 0x4D4F5250;
    fwrite(&magic, 4, 1, f);
    emit_u8(0x01); // Version
    emit_u8(0x00); // Reserved
    emit_u8(0x00); // Reserved
    emit_u8(0x00); // Reserved
    // Total Header Size = 8 bytes.
    // Code starts at offset 8.

    // Strategy:
    // 1. Jump to Main
    // 2. Define Worker Function
    // 3. Main Function

    // Offset math:
    // Current file pos = 8.
    // Instruction: JMP (1) + Offset (4) = 5 bytes.
    // Next instruction (Worker) starts at 8 + 5 = 13.

    // Worker logic same as before.
    // Worker Body:
    // PUSH 888 (9) + PRINT (1) = 10
    // YIELD (1)
    // PUSH 999 (9) + PRINT (1) = 10
    // YIELD (1) + JMP (1) + Offset(-6) (4) = 6
    // Total Worker Size = 10 + 1 + 10 + 6 = 27 bytes.

    // Worker starts at 13. Ends at 13 + 27 = 40.
    // Main starts at 40.

    // JMP at 8 wants to go to 40.
    // JMP is at 8. IP after JMP read (opcode+operand) is 8 + 1 + 4 = 13.
    // Target 40.
    // Offset = 40 - 13 = 27.

    // --- JMP to Main ---
    emit_u8(OP_JMP);
    emit_u32(27); // Jump over Worker to Main

    // --- Worker Function (Address: 13) ---
    // Print 888 (Worker 1)
    emit_u8(OP_PUSH); emit_u64(888);
    emit_u8(OP_PRINT);

    // Yield
    emit_u8(OP_YIELD);

    // Print 999 (Worker 2)
    emit_u8(OP_PUSH); emit_u64(999);
    emit_u8(OP_PRINT);

    // Loop forever
    emit_u8(OP_YIELD);
    emit_u8(OP_JMP); emit_u32(-6);

    // --- Main Function (Address: 40) ---

    // SBRK (Init Heap)
    emit_u8(OP_PUSH); emit_u64(1024);
    emit_u8(OP_PUSH); emit_u64(SYS_SBRK);
    emit_u8(OP_SYSCALL);
    emit_u8(OP_POP);

    // Print 111 (Main 1)
    emit_u8(OP_PUSH); emit_u64(111);
    emit_u8(OP_PRINT);

    // Spawn Worker (Address 13)
    emit_u8(OP_PUSH); emit_u64(13); // Address of Worker
    emit_u8(OP_SPAWN);

    // Yield (Let Worker run)
    emit_u8(OP_YIELD);

    // Print 222 (Main 2)
    emit_u8(OP_PUSH); emit_u64(222);
    emit_u8(OP_PRINT);

    // Yield (Let Worker run again)
    emit_u8(OP_YIELD);

    // Print 333 (Main 3)
    emit_u8(OP_PUSH); emit_u64(333);
    emit_u8(OP_PRINT);

    // Exit All
    emit_u8(OP_PUSH); emit_u64(0);
    emit_u8(OP_PUSH); emit_u64(SYS_EXIT);
    emit_u8(OP_SYSCALL);

    fclose(f);
    printf("Generated test.bin with Header\n");
    return 0;
}

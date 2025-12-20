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

    printf("Generating Concurrency Test...\n");

    // Strategy:
    // 1. Jump to Main
    // 2. Define Worker Function (at some offset)
    // 3. Main Function

    // --- Header: Jump to Main ---
    emit_u8(OP_JMP);
    // Offset will be calculated: Worker is approx 20 bytes?
    // Let's assume Worker starts at byte 5 (after JMP+Offset)
    // Worker size:
    // PUSH 888 -> 9 bytes
    // PRINT -> 1 byte
    // YIELD -> 1 byte
    // PUSH 999 -> 9 bytes
    // PRINT -> 1 byte
    // EXIT -> ? (Implicitly handled by loop or SYS_EXIT)
    // Let's say Worker is at offset 5.
    // Worker Body Length: 27 bytes (Calculated: 9+1+1+9+1+1+5).
    // So Jump Target should be 5 + 27 = 32.
    // VM IP logic: IP is at 5 when executing jump. Target = 5 + offset.
    // 32 = 5 + offset -> offset = 27.
    emit_u32(27);

    // --- Worker Function (Address: 5) ---
    // Print 888 (Worker 1)
    emit_u8(OP_PUSH); emit_u64(888);
    emit_u8(OP_PRINT);

    // Yield
    emit_u8(OP_YIELD);

    // Print 999 (Worker 2)
    emit_u8(OP_PUSH); emit_u64(999);
    emit_u8(OP_PRINT);

    // Exit Context (Using SYS_EXIT logic or custom logic?)
    // In our VM, if code runs out, it exits context.
    // Let's just end here. (Or loop forever to be safe? No, let's test implicit exit)
    // But we need to make sure we don't fall through to Main if we were placed differently.
    // Since we are at Address 5, and Main is at 35 + 5 = 40, we are safe if we stop.
    // To be explicit, let's just JMP to self or something.
    // Actually, VM stops context if ip >= code_size. But we are in middle of code.
    // So we MUST have an explicit "Stop Context" instruction.
    // SYS_EXIT exits process.
    // We don't have OP_CTX_EXIT.
    // Workaround: JMP to end of file?
    // Let's implement a JMP that goes to a "Safe Exit Zone" at the very end.
    // For now, let's just use SYS_EXIT(0) which kills everything, to prove Worker finished.
    // But wait, we want Main to print too.
    // Let's make Worker loop 0 times?
    // Hack: Use a dummy "Context Exit" by jumping to a known "Dead Zone" or just PUSH 0, JZ to self (infinite loop idle).
    // Let's use Infinite Loop for Worker end: JMP -5 (back to start of loop?)
    // Better: Infinite Yield Loop.
    // LOOP: YIELD; JMP LOOP;
    emit_u8(OP_YIELD);
    emit_u8(OP_JMP); emit_u32(-6); // Jump back to YIELD (1 + 1 + 4 = 6 bytes back?)
    // YIELD (1), JMP (1), Offset (4). Total 6. -6 points to YIELD.

    // --- Main Function (Address: 40) ---
    // Update JMP at top:
    // Start (0) -> JMP(1) -> Offset(4). Next instruction is at 5.
    // We want to jump to 40.
    // Offset = 40 - 5 = 35. (So my guess was correct).

    // Main:
    // SBRK (Init Heap)
    emit_u8(OP_PUSH); emit_u64(1024);
    emit_u8(OP_PUSH); emit_u64(SYS_SBRK);
    emit_u8(OP_SYSCALL);
    emit_u8(OP_POP);

    // Print 111 (Main 1)
    emit_u8(OP_PUSH); emit_u64(111);
    emit_u8(OP_PRINT);

    // Spawn Worker (Address 5)
    emit_u8(OP_PUSH); emit_u64(5); // Address of Worker
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
    printf("Generated test.bin\n");
    return 0;
}

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
#define OP_OPEN   0x0C
#define OP_WRITE  0x0D
#define OP_CLOSE  0x0E
#define OP_READ   0x0F
#define OP_EXIT   0xFF

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

    // Program:
    // 1. Calculate 10 + 20
    // 2. Print Result (30)
    // 3. Store result to Heap[0]
    // 4. Load from Heap[0]
    // 5. Print Result (30)
    // 6. Test JZ: Push 0, JZ to Exit, else Print 999 (Should Jump)
    // 7. Exit with code 0

    // 1. Calculate 10 + 20
    emit_u8(OP_PUSH); emit_u64(10);
    emit_u8(OP_PUSH); emit_u64(20);
    emit_u8(OP_ADD);

    // 2. Print Result (30)
    emit_u8(OP_DUP); // Keep copy for Store
    emit_u8(OP_PRINT);

    // 3. Store result (30) to Heap[0]
    // Stack: [30]
    // STORE: Pop Address, Pop Value.
    // We need: [Address, Value] on stack?
    // ISA: "Pop Alamat, Pop Nilai".
    // Stack is LIFO.
    // If we want to store 30 to addr 0.
    // We need Stack Top: [0 (Addr), 30 (Val)] ?
    // Pop Addr -> 0. Pop Val -> 30.
    // So we push Val, then Push Addr.
    // Current Stack: [30].
    // We need to Push 0.
    emit_u8(OP_PUSH); emit_u64(0); // Addr
    emit_u8(OP_STORE);
    // Stack is now empty (if we didn't DUP earlier properly, but we DUP'd and printed one, so one 30 left?
    // Wait:
    // PUSH 10
    // PUSH 20
    // ADD -> Stack: [30]
    // DUP -> Stack: [30, 30]
    // PRINT -> Pops 30 -> Prints 30. Stack: [30]
    // PUSH 0 -> Stack: [30, 0]
    // STORE -> Pop Addr (0), Pop Val (30). Heap[0] = 30. Stack: []

    // 4. Load from Heap[0]
    // Stack: []
    // LOAD: Pop Alamat. Push Value.
    emit_u8(OP_PUSH); emit_u64(0); // Addr
    emit_u8(OP_LOAD);
    // Stack: [30]

    // 5. Print Result (30)
    emit_u8(OP_PRINT); // Stack: []

    // 6. Test JZ
    // We want to skip printing 999.
    // Push 0 (Condition)
    emit_u8(OP_PUSH); emit_u64(0);
    // JZ offset.
    // We need to calculate offset.
    // Instructions to skip:
    //   PUSH 999 (1 + 8 = 9 bytes)
    //   PRINT (1 byte)
    // Total 10 bytes.
    // JZ consumes 4 bytes offset *after* opcode.
    // IP points to next instruction after JZ opcode + 4 bytes?
    // In VM: `vm.ip += offset`.
    // VM implementation:
    // case OP_JZ: read offset (4 bytes).
    //   Pop a. if a==0, vm.ip += offset.
    //   After reading offset, vm.ip is pointing to NEXT instruction.
    //   So offset 10 means "skip 10 bytes from here".
    emit_u8(OP_JZ); emit_u32(10);

    // Block to skip
    emit_u8(OP_PUSH); emit_u64(999);
    emit_u8(OP_PRINT);

    // Target of Jump
    // 7. Exit(0)
    emit_u8(OP_PUSH); emit_u64(0);
    emit_u8(OP_EXIT);

    fclose(f);
    printf("Generated test.bin\n");
    return 0;
}

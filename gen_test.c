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

// Helper to store string bytes into Heap at specific address
void emit_string_to_heap(uint64_t start_addr, const char *str) {
    size_t len = strlen(str);
    for (size_t i = 0; i <= len; i++) { // Include null terminator
        // Stack: [Val, Addr] -> STORE -> Heap[Addr] = Val
        emit_u8(OP_PUSH); emit_u64((uint64_t)str[i]); // Val (char)
        emit_u8(OP_PUSH); emit_u64(start_addr + i);   // Addr
        emit_u8(OP_STORE);
    }
}

int main() {
    f = fopen("test.bin", "wb");
    if (!f) return 1;

    printf("Generating I/O Test...\n");

    // 1. Prepare Filename "data.txt" at Heap[0]
    emit_string_to_heap(0, "data.txt");

    // 2. Prepare Content "Morph" at Heap[64]
    emit_string_to_heap(64, "Morph");

    // 3. OPEN "data.txt" for Write (Mode 1)
    // Stack: [Ptr, Mode] -> OPEN -> Push FD
    emit_u8(OP_PUSH); emit_u64(0); // Ptr to filename
    emit_u8(OP_PUSH); emit_u64(1); // Mode 1 (Write)
    emit_u8(OP_OPEN);

    // Stack: [FD]

    // 4. WRITE "Morph" to File
    emit_u8(OP_DUP);                // Stack: [FD, FD]
    emit_u8(OP_PUSH); emit_u64(64); // PtrData ("Morph")
    emit_u8(OP_PUSH); emit_u64(5);  // Len ("Morph")
    emit_u8(OP_WRITE);              // Pops Len, Ptr, FD. Stack: [FD]

    // 5. CLOSE File
    // Stack: [FD] -> CLOSE -> Stack: []
    emit_u8(OP_CLOSE);

    // 6. OPEN "data.txt" for Read (Mode 0)
    emit_u8(OP_PUSH); emit_u64(0); // Ptr
    emit_u8(OP_PUSH); emit_u64(0); // Mode 0 (Read)
    emit_u8(OP_OPEN);
    // Stack: [FD]

    // 7. READ into Heap[128]
    // Stack: [FD]
    // We need [FD, Ptr, Len]
    // READ pops: [Len, PtrBuffer, FD].
    // So stack order: [FD, Ptr, Len] (Top)
    emit_u8(OP_DUP); // Keep FD for close? Yes. Stack: [FD, FD]
    emit_u8(OP_PUSH); emit_u64(128); // Ptr Buffer
    emit_u8(OP_PUSH); emit_u64(5);   // Len
    emit_u8(OP_READ);
    // VM: READ pops Len, Ptr, FD. Performs read. Pushes ReadCount.
    // Stack: [FD, ReadCount]

    // 8. Print ReadCount (Should be 5)
    emit_u8(OP_PRINT);
    // Stack: [FD]

    // 9. CLOSE File
    emit_u8(OP_CLOSE);
    // Stack: []

    // 10. Verify Data: Print first char of Heap[128] ('M' = 77)
    emit_u8(OP_PUSH); emit_u64(128); // Addr
    emit_u8(OP_LOAD);
    // Stack: [77 (Ascii M)]
    emit_u8(OP_PRINT);

    // 11. Exit
    emit_u8(OP_PUSH); emit_u64(0);
    emit_u8(OP_EXIT);

    fclose(f);
    printf("Generated test.bin\n");
    return 0;
}

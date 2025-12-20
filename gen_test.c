#include <stdio.h>
#include <stdint.h>
#include <string.h>

// Opcodes
#define OP_NOP   0x00
#define OP_PUSH  0x01
#define OP_POP   0x02
#define OP_ADD   0x03
#define OP_SUB   0x04
#define OP_JMP   0x05
#define OP_JZ    0x06
#define OP_EQ    0x07
#define OP_DUP   0x08
#define OP_PRINT 0x09
#define OP_LOAD  0x0A
#define OP_STORE 0x0B
#define OP_OPEN  0x0C
#define OP_WRITE 0x0D
#define OP_CLOSE 0x0E
#define OP_READ  0x0F
#define OP_EXIT  0xFF

void emit8(FILE *f, uint8_t val) {
    fwrite(&val, 1, 1, f);
}

void emit64(FILE *f, uint64_t val) {
    // Little Endian
    fwrite(&val, 8, 1, f);
}

void store_byte_op(FILE *f, uint64_t addr, uint8_t val) {
    // PUSH val
    emit8(f, OP_PUSH);
    emit64(f, (uint64_t)val);
    // PUSH addr
    emit8(f, OP_PUSH);
    emit64(f, addr);
    // STORE
    emit8(f, OP_STORE);
}

int main() {
    FILE *f = fopen("read_write_test.bin", "wb");
    if (!f) return 1;

    // 1. Prepare Filename "output.txt" at Addr 0
    const char *fname = "output.txt";
    // Write including null terminator? Yes.
    for (int i = 0; i <= strlen(fname); i++) {
        store_byte_op(f, (uint64_t)i, fname[i]);
    }

    // 2. OPEN FILE (Read Mode)
    // Push Ptr Filename (0)
    emit8(f, OP_PUSH);
    emit64(f, 0);
    // Push Mode (0 = Read)
    emit8(f, OP_PUSH);
    emit64(f, 0);
    // OPEN
    emit8(f, OP_OPEN);

    // 3. READ FILE
    // DUP (Keep FD)
    emit8(f, OP_DUP);
    // Push Ptr Buffer (200)
    emit8(f, OP_PUSH);
    emit64(f, 200);
    // Push Length (10)
    emit8(f, OP_PUSH);
    emit64(f, 10);
    // READ
    emit8(f, OP_READ);

    // 4. PRINT COUNT
    // DUP
    emit8(f, OP_DUP);
    // PRINT
    emit8(f, OP_PRINT);

    // 5. DISCARD COUNT
    // POP
    emit8(f, OP_POP);

    // 6. WRITE TO STDOUT
    // Push FD 1 (STDOUT)
    emit8(f, OP_PUSH);
    emit64(f, 1);
    // Push Ptr Buffer (200)
    emit8(f, OP_PUSH);
    emit64(f, 200);
    // Push Length (6) - Hardcoded in original sample
    emit8(f, OP_PUSH);
    emit64(f, 6);
    // WRITE
    emit8(f, OP_WRITE);

    // 7. CLOSE
    // OP_CLOSE (Pops FD)
    emit8(f, OP_CLOSE);

    // 8. EXIT
    // Push Exit Code 0
    emit8(f, OP_PUSH);
    emit64(f, 0);
    emit8(f, OP_EXIT);

    fclose(f);
    printf("Generated read_write_test.bin\n");
    return 0;
}

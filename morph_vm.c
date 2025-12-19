#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>

// VM Configuration
#define MEM_SIZE (64 * 1024 + 8192) // 64KB Heap + 8KB Stack/Code padding
#define STACK_OFFSET 4096
#define HEAP_OFFSET 8192

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

// Helper to read 64-bit integer from memory (Little Endian)
uint64_t read_u64(uint8_t *mem, uint64_t addr) {
    uint64_t val = 0;
    for (int i = 0; i < 8; i++) {
        val |= ((uint64_t)mem[addr + i]) << (i * 8);
    }
    return val;
}

// Helper to write 64-bit integer to memory
void write_u64(uint8_t *mem, uint64_t addr, uint64_t val) {
    for (int i = 0; i < 8; i++) {
        mem[addr + i] = (val >> (i * 8)) & 0xFF;
    }
}

// Helper to read 32-bit integer (for Jump offsets)
int32_t read_i32(uint8_t *mem, uint64_t addr) {
    uint32_t val = 0;
    for (int i = 0; i < 4; i++) {
        val |= ((uint32_t)mem[addr + i]) << (i * 8);
    }
    return (int32_t)val;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: %s <program.bin>\n", argv[0]);
        return 1;
    }

    // Initialize Memory
    uint8_t *memory = calloc(MEM_SIZE, 1);
    if (!memory) {
        perror("Failed to allocate VM memory");
        return 1;
    }

    // Load Program
    int fd = open(argv[1], O_RDONLY);
    if (fd < 0) {
        perror("Failed to open program file");
        free(memory);
        return 1;
    }
    ssize_t bytes_read = read(fd, memory, STACK_OFFSET); // Load code into first 4KB
    close(fd);

    if (bytes_read <= 0) {
        fprintf(stderr, "Failed to read program or empty file.\n");
        free(memory);
        return 1;
    }

    // Registers
    uint64_t ip = 0;                    // Instruction Pointer (starts at 0)
    uint64_t sp = STACK_OFFSET;         // Stack Pointer (Ascending Stack start)
    uint64_t hp = HEAP_OFFSET;          // Heap Base Address

    int running = 1;
    int exit_code = 0;

    while (running) {
        if (ip >= STACK_OFFSET) {
            fprintf(stderr, "Error: IP out of code bounds (IP=%lu)\n", ip);
            break;
        }

        uint8_t opcode = memory[ip];

        switch (opcode) {
            case OP_NOP:
                ip++;
                break;

            case OP_PUSH: {
                // Format: [OP] [U64]
                uint64_t val = read_u64(memory, ip + 1);
                write_u64(memory, sp, val);
                sp += 8;
                ip += 9;
                break;
            }

            case OP_POP:
                if (sp <= STACK_OFFSET) { fprintf(stderr, "Stack Underflow\n"); running = 0; break; }
                sp -= 8;
                ip++;
                break;

            case OP_ADD: {
                if (sp < STACK_OFFSET + 16) { fprintf(stderr, "Stack Underflow (ADD)\n"); running = 0; break; }
                sp -= 16;
                uint64_t a = read_u64(memory, sp);
                uint64_t b = read_u64(memory, sp + 8);
                uint64_t res = a + b;
                write_u64(memory, sp, res);
                sp += 8;
                ip++;
                break;
            }

            case OP_SUB: {
                if (sp < STACK_OFFSET + 16) { fprintf(stderr, "Stack Underflow (SUB)\n"); running = 0; break; }
                sp -= 16;
                uint64_t a = read_u64(memory, sp);
                uint64_t b = read_u64(memory, sp + 8);
                // Note: Previous ASM was Pop A, Pop B, Push (B - A) or (A - B)?
                // build_vm.py: mov eax [r14] (A), mov ebx [r14+8] (B). sub rax, rbx.
                // Wait, in build_vm.py:
                // sp -= 16. A is at [sp]. B is at [sp+8].
                // sub rax (A), rbx (B) -> A - B.
                // The ISA says: "Pop A, Pop B, Push (B - A)".
                // If Stack is [A, B] (Top), Pop A, Pop B.
                // The python implementation did: sub r14, 16. A=[r14], B=[r14+8].
                // Before sub: Stack was [..., A, B] (Top).
                // So [r14-16] was A? No.
                // Let's trace build_vm:
                // PUSH 1 -> [sp]=1, sp+=8.
                // PUSH 2 -> [sp]=2, sp+=8.
                // Stack in mem: [1, 2]. sp points after 2.
                // SUB:
                // sub sp, 16. sp points to 1.
                // mov rax, [sp] (which is 1).
                // mov rbx, [sp+8] (which is 2).
                // sub rax, rbx -> 1 - 2 = -1.
                // mov [sp], rax (-1).
                // sp += 8.
                // Stack: [-1].
                // So it calculated Bottom - Top. (First pushed - Last pushed).
                // ISA says: "Pop A, Pop B". Usually Pop A gets Top (2). Pop B gets Next (1).
                // Result B - A = 1 - 2 = -1.
                // My C code:
                // sp -= 16. A = mem[sp] (Bottom/First), B = mem[sp+8] (Top/Second).
                // res = A - B.
                // Matches build_vm behavior.
                uint64_t res = a - b;
                write_u64(memory, sp, res);
                sp += 8;
                ip++;
                break;
            }

            case OP_JMP: {
                int32_t offset = read_i32(memory, ip + 1);
                // ip is current instruction address. Relative jump from *start* of instruction or end?
                // build_vm.py: add r15, rax. r15 is current IP.
                // In build_vm.py, the offset is calculated relative to (label_loop_start - (len(code)+5)).
                // It seems the jump is relative to the *next* instruction or the current one?
                // "JMP 4-byte (Int32) Lompat relatif (IP += offset)."
                // My C loop does ip++ for 1-byte ops.
                // Here I should do ip += offset?
                // But wait, the offset in the binary is usually calculated relative to the *end* of the JMP instruction or the beginning?
                // In `build_vm.py`: `code += b'\xE9' + p32(label_loop_start - (len(code) + 5))`
                // E9 is x86 JMP relative to *next instruction*.
                // BUT, the custom VM opcodes (0x05) are interpreted.
                // `HANDLER: JMP`: movsxd rax, [r15+1]; add r15, rax.
                // It adds the 32-bit immediate *value* to the *current* IP (r15 points to 0x05 byte).
                // So NewIP = OldIP + Offset.
                ip += offset;
                // Note: Infinite loop if offset is 0.
                break;
            }

            case OP_JZ: {
                sp -= 8;
                uint64_t cond = read_u64(memory, sp);
                if (cond == 0) {
                    int32_t offset = read_i32(memory, ip + 1);
                    ip += offset;
                } else {
                    ip += 5; // Skip Op(1) + Offset(4)
                }
                break;
            }

            case OP_EQ: {
                sp -= 16;
                uint64_t a = read_u64(memory, sp);
                uint64_t b = read_u64(memory, sp + 8);
                uint64_t res = (a == b) ? 1 : 0;
                write_u64(memory, sp, res);
                sp += 8;
                ip++;
                break;
            }

            case OP_DUP: {
                // Duplicate top of stack
                // Top is at sp - 8
                if (sp < STACK_OFFSET + 8) { fprintf(stderr, "Stack Underflow (DUP)\n"); running = 0; break; }
                uint64_t val = read_u64(memory, sp - 8);
                write_u64(memory, sp, val);
                sp += 8;
                ip++;
                break;
            }

            case OP_PRINT: {
                // Pop and print
                sp -= 8;
                uint64_t val = read_u64(memory, sp);
                printf("%lu\n", val);
                fflush(stdout);
                ip++;
                break;
            }

            case OP_LOAD: {
                // Pop Addr, Push [HP + Addr]
                sp -= 8;
                uint64_t addr = read_u64(memory, sp);
                uint64_t final_addr = hp + addr;
                if (final_addr >= MEM_SIZE) { fprintf(stderr, "Heap Segfault Read\n"); running = 0; break; }
                uint64_t val = read_u64(memory, final_addr);
                write_u64(memory, sp, val); // Reuse stack slot
                sp += 8;
                ip++;
                break;
            }

            case OP_STORE: {
                // Pop Addr, Pop Val, Store Val to [HP + Addr]
                sp -= 8;
                uint64_t addr = read_u64(memory, sp);
                sp -= 8;
                uint64_t val = read_u64(memory, sp);
                uint64_t final_addr = hp + addr;
                if (final_addr >= MEM_SIZE) { fprintf(stderr, "Heap Segfault Write\n"); running = 0; break; }
                // In ISA: "Store Val to [HP + Addr]"?
                // build_vm.py: Store byte(val) ? No, it stores 64-bit?
                // `HANDLER: STORE`: mov r14-8 (addr), mov r14-16 (val). mov [r12+addr], val.
                // Yes, stores 8 bytes (since register move).
                // Wait, `build_sample.py` used it to store individual bytes of filename string?
                // `store_byte` function in sample.py pushes VAL then ADDR then STORE.
                // But it pushes `p64(val)`. So it stores a 64-bit integer.
                // If I store 'o' (0x6F), it stores 0x000000000000006F.
                // If I store 'u' at addr+1, it overwrites the previous bytes?
                // `build_sample.py`: `store_byte(i, char)`. `i` increments by 1.
                // So it writes 64-bit at 0, then 64-bit at 1 (overlapping!).
                // This writes 8 bytes.
                // Writing at 0: [6F, 00, 00, 00, 00, 00, 00, 00]
                // Writing at 1: [ .., 75, 00, 00, 00, 00, 00, 00]
                // Effectively it works for strings if we only care about the LSB and write sequentially?
                // Actually, this is extremely inefficient/buggy for strings, but it works for the sample because we write char by char.
                // But writing 64-bit value to address X clears X+1...X+7?
                // Yes.
                // So `output.txt` string creation in sample.py:
                // i=0: writes 'o' at 0..7.
                // i=1: writes 'u' at 1..8. (Overwrites 0's MSBs, but 'o' is at 0 so it's safe).
                // This relies on Little Endian behavior.
                // It effectively builds the string byte by byte.
                // I will implement 64-bit store to match.
                 write_u64(memory, final_addr, val); // BUT wait.
                 // If I use `write_u64` it writes 8 bytes.
                 // Correct.
                ip++;
                break;
            }

            case OP_OPEN: {
                // Pop Mode, Pop Ptr Filename -> Push FD
                sp -= 8;
                uint64_t mode = read_u64(memory, sp);
                sp -= 8;
                uint64_t addr = read_u64(memory, sp);

                // Security Check: Filename address
                if (hp + addr >= MEM_SIZE) {
                     fprintf(stderr, "Segfault: Filename ptr out of bounds\n");
                     running = 0; break;
                }

                char *fname = (char*)(memory + hp + addr);
                // Simple validation: ensure we don't read past end of memory looking for null terminator
                int safe = 0;
                for (uint64_t i = hp + addr; i < MEM_SIZE; i++) {
                    if (memory[i] == '\0') { safe = 1; break; }
                }
                if (!safe) {
                    fprintf(stderr, "Segfault: Filename not null-terminated within bounds\n");
                    running = 0; break;
                }

                int flags = (mode == 1) ? (O_WRONLY | O_CREAT | O_TRUNC) : O_RDONLY;
                int file_fd = open(fname, flags, 0644);

                // Push FD
                write_u64(memory, sp, (uint64_t)file_fd); // Handle error? -1 cast to u64
                sp += 8;
                ip++;
                break;
            }

            case OP_WRITE: {
                // Pop Len, Pop PtrData, Pop FD
                sp -= 8;
                uint64_t len = read_u64(memory, sp);
                sp -= 8;
                uint64_t addr = read_u64(memory, sp);
                sp -= 8;
                uint64_t file_fd = read_u64(memory, sp);

                // Security Check: Buffer bounds
                if (hp + addr + len > MEM_SIZE || hp + addr + len < hp + addr) { // Check overflow too
                     fprintf(stderr, "Segfault: Write buffer out of bounds\n");
                     running = 0; break;
                }

                void *buf = (void*)(memory + hp + addr);
                write((int)file_fd, buf, len);

                ip++;
                break;
            }

            case OP_CLOSE: {
                // Pop FD
                sp -= 8;
                uint64_t file_fd = read_u64(memory, sp);
                close((int)file_fd);
                ip++;
                break;
            }

            case OP_READ: {
                // Pop Len, Pop PtrBuffer, Pop FD -> Push Count
                sp -= 8;
                uint64_t len = read_u64(memory, sp);
                sp -= 8;
                uint64_t addr = read_u64(memory, sp);
                sp -= 8;
                uint64_t file_fd = read_u64(memory, sp);

                // Security Check: Buffer bounds
                if (hp + addr + len > MEM_SIZE || hp + addr + len < hp + addr) {
                     fprintf(stderr, "Segfault: Read buffer out of bounds\n");
                     running = 0; break;
                }

                void *buf = (void*)(memory + hp + addr);
                ssize_t count = read((int)file_fd, buf, len);

                write_u64(memory, sp, (uint64_t)count);
                sp += 8;
                ip++;
                break;
            }

            case OP_EXIT: {
                sp -= 8;
                exit_code = (int)read_u64(memory, sp);
                running = 0;
                break;
            }

            default:
                fprintf(stderr, "Unknown Opcode: 0x%02X at IP %lu\n", opcode, ip);
                running = 0;
                exit_code = 1;
                break;
        }
    }

    free(memory);
    return exit_code;
}

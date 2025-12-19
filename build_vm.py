import struct
import sys

# Konfigurasi ELF64
# Kita butuh buffer memory yang cukup besar untuk Stack VM.
# Kita akan alokasikan area statis di segmen .bss (setelah code) untuk Stack.

def p64(val):
    return struct.pack('<Q', val)

def p32(val):
    return struct.pack('<i', val) # Signed 32-bit for Offsets

def u32(val):
    return struct.pack('<I', val) # Unsigned 32-bit

def p16(val):
    return struct.pack('<H', val)

def p8(val):
    return struct.pack('B', val)

# 1. ELF Header
elf_header = b''
elf_header += b'\x7FELF'              # Magic
elf_header += b'\x02'                 # Class: 64-bit
elf_header += b'\x01'                 # Data: Little Endian
elf_header += b'\x01'                 # Version: 1
elf_header += b'\x00'                 # ABI: System V
elf_header += b'\x00' * 8             # Padding
elf_header += p16(2)                  # Type: EXEC
elf_header += p16(0x3E)               # Machine: x86-64
elf_header += u32(1)                  # Version
elf_header += p64(0x400078)           # Entry Point (start of code)
elf_header += p64(64)                 # Phdr Offset (follows ELF header)
elf_header += p64(0)                  # Shdr Offset
elf_header += u32(0)                  # Flags
elf_header += p16(64)                 # EH Size
elf_header += p16(56)                 # Phdr Size
elf_header += p16(1)                  # Phdr Count
elf_header += p16(0)                  # Shdr Size
elf_header += p16(0)                  # Shdr Count
elf_header += p16(0)                  # String Table Index

# 2. Code Generation
# ------------------
# Register Allocation:
# R15: Code Pointer (Current IP - Absolute Address in Buffer)
# R14: Stack Pointer (VM Stack)
# R13: Buffer Base (Start of Code Buffer)

code = b''

# --- Initial Setup ---
# 1. Open File
# mov eax, 2 (open)
code += b'\xB8\x02\x00\x00\x00'
# lea rdi, [rel filename] (Placeholder)
code += b'\x48\x8D\x3D\x00\x00\x00\x00'
off_filename = len(code) - 4
# xor rsi, rsi (O_RDONLY)
code += b'\x48\x31\xF6'
# xor rdx, rdx
code += b'\x48\x31\xD2'
# syscall
code += b'\x0F\x05'

# Check Error (Open)
# test rax, rax
code += b'\x48\x85\xC0'
# js error_handler (Placeholder)
code += b'\x0F\x88\x00\x00\x00\x00' # Long Jump (JJS) to be safe
off_err_open = len(code) - 4

# Save FD
# mov r12d, eax
code += b'\x41\x89\xC4'

# 2. Read File content to Buffer (Start of BSS/Data)
# mov edi, r12d
code += b'\x44\x89\xE7'
# mov eax, 0 (read)
code += b'\xB8\x00\x00\x00\x00'
# lea rsi, [rel buffer] (Placeholder)
code += b'\x48\x8D\x35\x00\x00\x00\x00'
off_buffer_read = len(code) - 4
# mov edx, 4096 (Max code size)
code += b'\xBA\x00\x10\x00\x00'
# syscall
code += b'\x0F\x05'

# Check Error (Read) - if 0 or negative
# test rax, rax
code += b'\x48\x85\xC0'
# jle error_handler
code += b'\x0F\x8E\x00\x00\x00\x00'
off_err_read = len(code) - 4

# Close File (Good practice)
# mov edi, r12d
code += b'\x44\x89\xE7'
# mov eax, 3 (close)
code += b'\xB8\x03\x00\x00\x00'
# syscall
code += b'\x0F\x05'


# --- VM Initialization ---
# R13 = Buffer Base
# lea r13, [rel buffer]
code += b'\x4C\x8D\x2D\x00\x00\x00\x00'
off_buffer_init = len(code) - 4

# R15 = IP (Starts at Buffer Base)
# mov r15, r13
code += b'\x4D\x89\xEF'

# R14 = Stack Pointer (Use High Memory / End of Buffer + Stack Space)
# lea r14, [r13 + 4096] (Start of stack area)
code += b'\x4D\x8D\xB5\x00\x10\x00\x00'


# --- Main Loop (Fetch-Decode-Execute) ---
label_loop_start = len(code)

# Fetch Byte: movzx eax, byte ptr [r15]
code += b'\x41\x0F\xB6\x07'

# --- Dispatcher (Switch Case) ---

# Case 0xFF: EXIT
# cmp al, 0xFF
code += b'\x3C\xFF'
# je label_exit
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_exit = len(code) - 4

# Case 0x01: PUSH (9 bytes instruction)
# cmp al, 0x01
code += b'\x3C\x01'
# je label_push
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_push = len(code) - 4

# Case 0x02: POP
# cmp al, 0x02
code += b'\x3C\x02'
# je label_pop
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_pop = len(code) - 4

# Case 0x03: ADD
# cmp al, 0x03
code += b'\x3C\x03'
# je label_add
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_add = len(code) - 4

# Case 0x04: SUB
# cmp al, 0x04
code += b'\x3C\x04'
# je label_sub
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_sub = len(code) - 4

# Case 0x05: JMP (5 bytes instruction: Op + 4 byte offset)
# cmp al, 0x05
code += b'\x3C\x05'
# je label_jmp
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_jmp = len(code) - 4

# Case 0x06: JZ (5 bytes instruction)
# cmp al, 0x06
code += b'\x3C\x06'
# je label_jz
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_jz = len(code) - 4

# Case 0x07: EQ
# cmp al, 0x07
code += b'\x3C\x07'
# je label_eq
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_eq = len(code) - 4

# Case 0x08: DUP
# cmp al, 0x08
code += b'\x3C\x08'
# je label_dup
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_dup = len(code) - 4

# Default: Skip / NOP / Error (Just loop next byte)
# inc r15
code += b'\x49\xFF\xC7'
# jmp loop_start
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))


# --- Handlers ---

# HANDLER: PUSH
label_push = len(code)
# Value at [r15+1] (64-bit)
# mov rax, [r15+1]
code += b'\x49\x8B\x47\x01'
# Push to VM Stack: mov [r14], rax; add r14, 8
code += b'\x49\x89\x06'
code += b'\x49\x83\xC6\x08'
# Advance IP by 9
code += b'\x49\x83\xC7\x09'
# Jmp Loop
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: POP
label_pop = len(code)
# sub r14, 8
code += b'\x49\x83\xEE\x08'
# Advance IP by 1
code += b'\x49\xFF\xC7'
# Jmp Loop
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: ADD
label_add = len(code)
# sub r14, 16 (Back 2 items)
code += b'\x49\x83\xEE\x10'
# mov rax, [r14] (Val 1)
code += b'\x41\x8B\x06'
# mov rbx, [r14+8] (Val 2)
code += b'\x41\x8B\x5E\x08'
# add rax, rbx
code += b'\x48\x01\xD8'
# mov [r14], rax (Push Result)
code += b'\x49\x89\x06'
# add r14, 8 (Adjust SP to point to next empty)
code += b'\x49\x83\xC6\x08'
# Advance IP by 1
code += b'\x49\xFF\xC7'
# Jmp Loop
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: SUB (Val2 - Val1) Note: Stack grows up. Top is Val2?
# Order: Push A, Push B. Stack: [A, B]. Pop -> B, Pop -> A. Result A - B.
# Implementation:
label_sub = len(code)
# sub r14, 16
code += b'\x49\x83\xEE\x10'
# mov rax, [r14] (A)
code += b'\x41\x8B\x06'
# mov rbx, [r14+8] (B)
code += b'\x41\x8B\x5E\x08'
# sub rax, rbx (A - B)
code += b'\x48\x29\xD8'
# mov [r14], rax
code += b'\x49\x89\x06'
# add r14, 8
code += b'\x49\x83\xC6\x08'
# Advance IP
code += b'\x49\xFF\xC7'
# Jmp Loop
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: EQ
label_eq = len(code)
# sub r14, 16
code += b'\x49\x83\xEE\x10'
# mov rax, [r14]
code += b'\x41\x8B\x06'
# mov rbx, [r14+8]
code += b'\x41\x8B\x5E\x08'
# cmp rax, rbx
code += b'\x48\x39\xD8'
# sete al
code += b'\x0F\x94\xC0'
# movzx rax, al
code += b'\x48\x0F\xB6\xC0'
# mov [r14], rax
code += b'\x49\x89\x06'
# add r14, 8
code += b'\x49\x83\xC6\x08'
# Advance IP
code += b'\x49\xFF\xC7'
# Jmp Loop
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: DUP
label_dup = len(code)
# mov rax, [r14-8] (Peek Top)
code += b'\x49\x8B\x46\xF8'
# mov [r14], rax (Push)
code += b'\x49\x89\x06'
# add r14, 8
code += b'\x49\x83\xC6\x08'
# Advance IP
code += b'\x49\xFF\xC7'
# Jmp Loop
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: JMP
label_jmp = len(code)
# Read offset (signed 32-bit) at [r15+1]
# movsxd rax, dword ptr [r15+1]
code += b'\x49\x63\x47\x01'
# add r15, rax (Apply Jump)
code += b'\x49\x01\xC7'
# Do NOT advance IP manually, jump includes the instruction size adjustment usually?
# Let's say JMP offset is relative to START of instruction.
# So if offset is 0, infinite loop.
# Jmp Loop
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: JZ
label_jz = len(code)
# Pop Check
# sub r14, 8
code += b'\x49\x83\xEE\x08'
# mov rax, [r14]
code += b'\x41\x8B\x06'
# test rax, rax
code += b'\x48\x85\xC0'
# jnz no_jump
code += b'\x75\x0C'
# DO JUMP:
# movsxd rax, dword ptr [r15+1]
code += b'\x49\x63\x47\x01'
# add r15, rax
code += b'\x49\x01\xC7'
# jmp loop_start
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# NO JUMP:
# Advance IP by 5 (Op + 4 byte)
code += b'\x49\x83\xC7\x05'
# jmp loop_start
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: EXIT
label_exit = len(code)
# Pop exit code
# sub r14, 8
code += b'\x49\x83\xEE\x08'
# mov rdi, [r14]
code += b'\x41\x8B\x3E'
# mov eax, 60
code += b'\xB8\x3C\x00\x00\x00'
# syscall
code += b'\x0F\x05'


# ERROR HANDLER
label_error = len(code)
# mov rdi, 1
code += b'\xBF\x01\x00\x00\x00'
# mov eax, 60
code += b'\xB8\x3C\x00\x00\x00'
# syscall
code += b'\x0F\x05'


# --- Patching Offsets ---
def patch(data, pos, target_addr_relative):
    # Target Addr Relative means: Target - (Pos + 4)
    offset = target_addr_relative - (pos + 4)
    return data[:pos] + p32(offset) + data[pos+4:]

def patch_lea(data, pos, target_pos):
    # LEA is relative to RIP (next instruction)
    offset = target_pos - (pos + 4)
    return data[:pos] + p32(offset) + data[pos+4:]

# Patch Dispatcher Jumps
code = patch(code, off_je_push, label_push)
code = patch(code, off_je_pop, label_pop)
code = patch(code, off_je_add, label_add)
code = patch(code, off_je_sub, label_sub)
code = patch(code, off_je_jmp, label_jmp)
code = patch(code, off_je_jz, label_jz)
code = patch(code, off_je_eq, label_eq)
code = patch(code, off_je_dup, label_dup)
code = patch(code, off_je_exit, label_exit)

# Patch Error Checks
code = patch(code, off_err_open, label_error)
code = patch(code, off_err_read, label_error)

# Data Section
pos_data = len(code)
filename_str = b"loop_program.bin\x00"
code += filename_str

pos_buffer = len(code)
# Buffer space is technically "after" code.
# The `pos_buffer` is where the buffer starts in the file image, or just used for calculating VAddr offsets.
# ELF loads segments. We need to make sure the buffer is in a writable segment.
# In this simple ELF, we put everything in one RWE segment.

# Patch LEA (Data References)
code = patch_lea(code, off_filename, pos_data)
code = patch_lea(code, off_buffer_read, pos_buffer)
code = patch_lea(code, off_buffer_init, pos_buffer)


# Finalizing ELF
total_size = 120 + len(code)
mem_size = total_size + 4096 + 4096 # Code + Buffer + Stack

# Build Program Header
phdr = b''
phdr += p32(1)                  # Type: LOAD
phdr += p32(7)                  # Flags: R W E
phdr += p64(0)                  # Offset
phdr += p64(0x400000)           # VAddr
phdr += p64(0x400000)           # PAddr
phdr += p64(total_size)         # FileSize
phdr += p64(mem_size)           # MemSize
phdr += p64(0x1000)             # Align

# Write to file
with open('morph_vm', 'wb') as f:
    f.write(elf_header)
    f.write(phdr)
    f.write(code)

print(f"VM v0.2 built successfully. Size: {total_size} bytes.")

import struct
import sys

# Konfigurasi ELF64

def p64(val):
    return struct.pack('<Q', val)

def p32(val):
    return struct.pack('<i', val)

def u32(val):
    return struct.pack('<I', val)

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
# R15: Code Pointer (Current IP)
# R14: Stack Pointer (VM Stack)
# R13: Buffer Base (Start of Code Buffer / Global Base)

code = b''

# --- Initial Setup ---
# 1. Open File
# mov eax, 2 (open)
code += b'\xB8\x02\x00\x00\x00'
# lea rdi, [rel filename]
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
# js error_handler
code += b'\x0F\x88\x00\x00\x00\x00'
off_err_open = len(code) - 4

# Save FD
# mov r12d, eax
code += b'\x41\x89\xC4'

# 2. Read File content to Buffer
# mov edi, r12d
code += b'\x44\x89\xE7'
# mov eax, 0 (read)
code += b'\xB8\x00\x00\x00\x00'
# lea rsi, [rel buffer]
code += b'\x48\x8D\x35\x00\x00\x00\x00'
off_buffer_read = len(code) - 4
# mov edx, 4096 (Max code size)
code += b'\xBA\x00\x10\x00\x00'
# syscall
code += b'\x0F\x05'

# Check Error (Read)
# test rax, rax
code += b'\x48\x85\xC0'
# jle error_handler
code += b'\x0F\x8E\x00\x00\x00\x00'
off_err_read = len(code) - 4

# Close File
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

# R14 = Stack Pointer (End of Buffer + Stack Space)
# lea r14, [r13 + 4096]
code += b'\x4D\x8D\xB5\x00\x10\x00\x00'


# --- Main Loop ---
label_loop_start = len(code)

# Fetch Byte: movzx eax, byte ptr [r15]
code += b'\x41\x0F\xB6\x07'

# --- Dispatcher ---
# Case 0xFF: EXIT
code += b'\x3C\xFF'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_exit = len(code) - 4

# Case 0x01: PUSH
code += b'\x3C\x01'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_push = len(code) - 4

# Case 0x02: POP
code += b'\x3C\x02'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_pop = len(code) - 4

# Case 0x03: ADD
code += b'\x3C\x03'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_add = len(code) - 4

# Case 0x04: SUB
code += b'\x3C\x04'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_sub = len(code) - 4

# Case 0x05: JMP
code += b'\x3C\x05'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_jmp = len(code) - 4

# Case 0x06: JZ
code += b'\x3C\x06'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_jz = len(code) - 4

# Case 0x07: EQ
code += b'\x3C\x07'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_eq = len(code) - 4

# Case 0x08: DUP
code += b'\x3C\x08'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_dup = len(code) - 4

# Case 0x09: PRINT
code += b'\x3C\x09'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_print = len(code) - 4

# Default: Skip
# inc r15
code += b'\x49\xFF\xC7'
# jmp loop_start
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))


# --- Handlers ---

# HANDLER: PUSH
label_push = len(code)
code += b'\x49\x8B\x47\x01' # mov rax, [r15+1]
code += b'\x49\x89\x06'     # mov [r14], rax
code += b'\x49\x83\xC6\x08' # add r14, 8
code += b'\x49\x83\xC7\x09' # add r15, 9
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: POP
label_pop = len(code)
code += b'\x49\x83\xEE\x08' # sub r14, 8
code += b'\x49\xFF\xC7'     # inc r15
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: ADD
label_add = len(code)
code += b'\x49\x83\xEE\x10' # sub r14, 16
code += b'\x41\x8B\x06'     # mov eax, [r14]
code += b'\x41\x8B\x5E\x08' # mov ebx, [r14+8]
code += b'\x48\x01\xD8'     # add rax, rbx
code += b'\x49\x89\x06'     # mov [r14], rax
code += b'\x49\x83\xC6\x08' # add r14, 8
code += b'\x49\xFF\xC7'     # inc r15
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: SUB
label_sub = len(code)
code += b'\x49\x83\xEE\x10' # sub r14, 16
code += b'\x41\x8B\x06'     # mov eax, [r14] (A)
code += b'\x41\x8B\x5E\x08' # mov ebx, [r14+8] (B)
code += b'\x48\x29\xD8'     # sub rax, rbx (A - B)
code += b'\x49\x89\x06'     # mov [r14], rax
code += b'\x49\x83\xC6\x08' # add r14, 8
code += b'\x49\xFF\xC7'     # inc r15
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: EQ
label_eq = len(code)
code += b'\x49\x83\xEE\x10' # sub r14, 16
code += b'\x41\x8B\x06'     # mov rax, [r14]
code += b'\x41\x8B\x5E\x08' # mov rbx, [r14+8]
code += b'\x48\x39\xD8'     # cmp rax, rbx
code += b'\x0F\x94\xC0'     # sete al
code += b'\x48\x0F\xB6\xC0' # movzx rax, al
code += b'\x49\x89\x06'     # mov [r14], rax
code += b'\x49\x83\xC6\x08' # add r14, 8
code += b'\x49\xFF\xC7'     # inc r15
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: DUP
label_dup = len(code)
code += b'\x49\x8B\x46\xF8' # mov rax, [r14-8]
code += b'\x49\x89\x06'     # mov [r14], rax
code += b'\x49\x83\xC6\x08' # add r14, 8
code += b'\x49\xFF\xC7'     # inc r15
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: JMP
label_jmp = len(code)
code += b'\x49\x63\x47\x01' # movsxd rax, [r15+1]
code += b'\x49\x01\xC7'     # add r15, rax
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: JZ
label_jz = len(code)
code += b'\x49\x83\xEE\x08' # sub r14, 8
code += b'\x41\x8B\x06'     # mov rax, [r14]
code += b'\x48\x85\xC0'     # test rax, rax
code += b'\x75\x0C'         # jnz no_jump (+12)
# DO JUMP:
code += b'\x49\x63\x47\x01' # movsxd rax, [r15+1]
code += b'\x49\x01\xC7'     # add r15, rax
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))
# NO JUMP:
code += b'\x49\x83\xC7\x05' # add r15, 5
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))

# HANDLER: PRINT (FIXED JUMPS)
label_print = len(code)
# Pop Number
code += b'\x49\x83\xEE\x08' # sub r14, 8
code += b'\x41\x8B\x06'     # mov eax, [r14]

# r10 = End of buffer (r14 + 32)
code += b'\x4D\x8D\x56\x20'
# mov r11, r10 (Save End)
code += b'\x4D\x89\xD3'
# mov byte [r10], 10 (\n)
code += b'\x41\xC6\x02\x0A'
# dec r10
code += b'\x49\xFF\xCA'

# Handle 0
# test eax, eax
code += b'\x85\xC0'

# Placeholder for JNZ loop_itoa
off_jnz_loop_itoa_start = len(code)
code += b'\x75\x00' # JNZ +0

# Zero case
code += b'\x41\xC6\x02\x30' # mov byte [r10], '0'
code += b'\x49\xFF\xCA'     # dec r10

# Placeholder for JMP do_write
off_jmp_do_write = len(code)
code += b'\xEB\x00' # JMP +0

# Loop Itoa Start
label_loop_itoa = len(code)
# Patch JNZ loop_itoa (at start) to point here
# JNZ is at off_jnz_loop_itoa_start.
# Target is label_loop_itoa.
# Offset = Target - (Pos + 2)
offset = label_loop_itoa - (off_jnz_loop_itoa_start + 2)
code_list = bytearray(code)
code_list[off_jnz_loop_itoa_start + 1] = offset
code = bytes(code_list)


# mov ebx, 10
code += b'\xBB\x0A\x00\x00\x00'
# xor edx, edx
code += b'\x31\xD2'
# div ebx
code += b'\xF7\xF3'
# add dl, '0'
code += b'\x80\xC2\x30'
# mov [r10], dl
code += b'\x41\x88\x12'
# dec r10
code += b'\x49\xFF\xCA'
# test eax, eax
code += b'\x85\xC0'
# jnz loop_itoa
# JNZ back to label_loop_itoa
offset = label_loop_itoa - (len(code) + 2)
# Convert negative offset to signed byte
if offset < 0:
    offset = 256 + offset
code += b'\x75' + p8(offset)

# DO WRITE
label_do_write = len(code)
# Patch JMP do_write
offset = label_do_write - (off_jmp_do_write + 2)
code_list = bytearray(code)
code_list[off_jmp_do_write + 1] = offset
code = bytes(code_list)

# inc r10 (Start of string)
code += b'\x49\xFF\xC2'
# mov rsi, r10
code += b'\x4C\x89\xD6'
# Length calculation: r11 - r10 + 1
code += b'\x4C\x89\xDA' # mov rdx, r11
code += b'\x4C\x29\xD2' # sub rdx, r10
code += b'\x48\xFF\xC2' # inc rdx

# mov edi, 1 (stdout)
code += b'\xBF\x01\x00\x00\x00'
# mov eax, 1 (write)
code += b'\xB8\x01\x00\x00\x00'
# syscall
code += b'\x0F\x05'

# Finish PRINT
# inc r15
code += b'\x49\xFF\xC7'
# jmp loop_start
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))


# HANDLER: EXIT
label_exit = len(code)
code += b'\x49\x83\xEE\x08' # sub r14, 8
code += b'\x41\x8B\x3E'     # mov rdi, [r14]
code += b'\xB8\x3C\x00\x00\x00' # mov eax, 60
code += b'\x0F\x05'

# ERROR HANDLER
label_error = len(code)
code += b'\xBF\x01\x00\x00\x00' # mov rdi, 1
code += b'\xB8\x3C\x00\x00\x00' # mov eax, 60
code += b'\x0F\x05'


# --- Patching Offsets ---
def patch(data, pos, target_addr_relative):
    offset = target_addr_relative - (pos + 4)
    return data[:pos] + p32(offset) + data[pos+4:]

def patch_lea(data, pos, target_pos):
    offset = target_pos - (pos + 4)
    return data[:pos] + p32(offset) + data[pos+4:]

# Patch Dispatcher
code = patch(code, off_je_push, label_push)
code = patch(code, off_je_pop, label_pop)
code = patch(code, off_je_add, label_add)
code = patch(code, off_je_sub, label_sub)
code = patch(code, off_je_jmp, label_jmp)
code = patch(code, off_je_jz, label_jz)
code = patch(code, off_je_eq, label_eq)
code = patch(code, off_je_dup, label_dup)
code = patch(code, off_je_print, label_print)
code = patch(code, off_je_exit, label_exit)

# Patch Error
code = patch(code, off_err_open, label_error)
code = patch(code, off_err_read, label_error)

# Data Section
pos_data = len(code)
filename_str = b"print_test.bin\x00"
code += filename_str

pos_buffer = len(code)

# Patch LEA
code = patch_lea(code, off_filename, pos_data)
code = patch_lea(code, off_buffer_read, pos_buffer)
code = patch_lea(code, off_buffer_init, pos_buffer)


# Finalizing ELF
total_size = 120 + len(code)
mem_size = total_size + 8192 # More stack space

phdr = b''
phdr += p32(1)
phdr += p32(7)
phdr += p64(0)
phdr += p64(0x400000)
phdr += p64(0x400000)
phdr += p64(total_size)
phdr += p64(mem_size)
phdr += p64(0x1000)

with open('morph_vm', 'wb') as f:
    f.write(elf_header)
    f.write(phdr)
    f.write(code)

print(f"VM v0.3 built successfully. Size: {total_size} bytes.")

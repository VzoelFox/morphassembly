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
# R12: Heap Pointer (Start of Heap Memory)

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
# R13 = Buffer Base (Code Start)
# lea r13, [rel buffer]
code += b'\x4C\x8D\x2D\x00\x00\x00\x00'
off_buffer_init = len(code) - 4

# R15 = IP (Starts at Buffer Base)
# mov r15, r13
code += b'\x4D\x89\xEF'

# R14 = Stack Pointer (End of Code Buffer + Stack Space)
# Stack starts at 4KB after Code.
# lea r14, [r13 + 4096]
code += b'\x4D\x8D\xB5\x00\x10\x00\x00'

# R12 = Heap Pointer (After Stack)
# Stack size = 4KB. Heap starts at 8KB from Code Base.
# lea r12, [r13 + 8192]
code += b'\x4D\x8D\xA5\x00\x20\x00\x00'


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

# Case 0x0A: LOAD
code += b'\x3C\x0A'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_load = len(code) - 4

# Case 0x0B: STORE
code += b'\x3C\x0B'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_store = len(code) - 4

# Case 0x0C: OPEN
code += b'\x3C\x0C'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_open = len(code) - 4

# Case 0x0D: WRITE
code += b'\x3C\x0D'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_write = len(code) - 4

# Case 0x0E: CLOSE
code += b'\x3C\x0E'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_close = len(code) - 4

# Case 0x0F: READ
code += b'\x3C\x0F'
code += b'\x0F\x84\x00\x00\x00\x00'
off_je_read = len(code) - 4

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


# HANDLER: LOAD
label_load = len(code)
code += b'\x49\x83\xEE\x08'
code += b'\x41\x8B\x1E'
code += b'\x49\x8B\x04\x1C'
code += b'\x49\x89\x06'
code += b'\x49\x83\xC6\x08'
code += b'\x49\xFF\xC7'
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))


# HANDLER: STORE
label_store = len(code)
code += b'\x49\x83\xEE\x08'
code += b'\x41\x8B\x1E'
code += b'\x49\x83\xEE\x08'
code += b'\x49\x8B\x06'
code += b'\x49\x89\x04\x1C'
code += b'\x49\xFF\xC7'
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))


# HANDLER: OPEN
label_open = len(code)
# Pop Mode
code += b'\x49\x83\xEE\x08'
code += b'\x49\x8B\x36'
# Check Mode
code += b'\x48\x83\xFE\x01' # cmp rsi, 1
code += b'\x75\x0A'         # jne +10
# Set Write Flags
code += b'\xBE\x41\x02\x00\x00' # mov esi, 0x241
code += b'\xBA\xA4\x01\x00\x00' # mov edx, 0644
# Pop Filename Ptr
code += b'\x49\x83\xEE\x08'
code += b'\x41\x8B\x1E'
code += b'\x49\x8D\x3C\x1C' # lea rdi, [r12 + rbx] (Fix applied)
# Syscall Open
code += b'\xB8\x02\x00\x00\x00'
code += b'\x0F\x05'
# Push FD
code += b'\x49\x89\x06'
code += b'\x49\x83\xC6\x08'
code += b'\x49\xFF\xC7'
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))


# HANDLER: WRITE
label_write = len(code)
# Pop Len (RDX)
code += b'\x49\x83\xEE\x08'
code += b'\x49\x8B\x16'
# Pop PtrData (RSI)
code += b'\x49\x83\xEE\x08'
code += b'\x41\x8B\x1E'
code += b'\x49\x8D\x34\x1C' # lea rsi, [r12 + rbx] (Fix applied)
# Pop FD (RDI)
code += b'\x49\x83\xEE\x08'
code += b'\x49\x8B\x3E'
# Syscall Write
code += b'\xB8\x01\x00\x00\x00'
code += b'\x0F\x05'
code += b'\x49\xFF\xC7'
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))


# HANDLER: CLOSE
label_close = len(code)
code += b'\x49\x83\xEE\x08'
code += b'\x49\x8B\x3E'
code += b'\xB8\x03\x00\x00\x00'
code += b'\x0F\x05'
code += b'\x49\xFF\xC7'
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))


# HANDLER: READ
# Pop Length, Pop PtrBuffer, Pop FD -> Read -> Push Count
label_read = len(code)
# Pop Length (RDX)
code += b'\x49\x83\xEE\x08'
code += b'\x49\x8B\x16'     # mov rdx, [r14]
# Pop PtrBuffer (RSI)
code += b'\x49\x83\xEE\x08'
code += b'\x41\x8B\x1E'     # mov ebx, [r14]
code += b'\x49\x8D\x34\x1C' # lea rsi, [r12 + rbx] (Uses R12 heap base)
# Pop FD (RDI)
code += b'\x49\x83\xEE\x08'
code += b'\x49\x8B\x3E'     # mov rdi, [r14]
# Syscall Read (rax = 0)
code += b'\xB8\x00\x00\x00\x00'
code += b'\x0F\x05'
# Push Result (Count)
code += b'\x49\x89\x06'     # mov [r14], rax
code += b'\x49\x83\xC6\x08' # add r14, 8
# Next
code += b'\x49\xFF\xC7'
code += b'\xE9' + p32(label_loop_start - (len(code) + 5))


# HANDLER: PRINT
label_print = len(code)
code += b'\x49\x83\xEE\x08' # sub r14, 8
code += b'\x41\x8B\x06'     # mov eax, [r14]
code += b'\x4D\x8D\x56\x20'
code += b'\x4D\x89\xD3'
code += b'\x41\xC6\x02\x0A'
code += b'\x49\xFF\xCA'
code += b'\x85\xC0'
off_jnz_loop_itoa_start = len(code)
code += b'\x75\x00'
code += b'\x41\xC6\x02\x30'
code += b'\x49\xFF\xCA'
off_jmp_do_write = len(code)
code += b'\xEB\x00'
label_loop_itoa = len(code)
offset = label_loop_itoa - (off_jnz_loop_itoa_start + 2)
code_list = bytearray(code)
code_list[off_jnz_loop_itoa_start + 1] = offset
code = bytes(code_list)
code += b'\xBB\x0A\x00\x00\x00'
code += b'\x31\xD2'
code += b'\xF7\xF3'
code += b'\x80\xC2\x30'
code += b'\x41\x88\x12'
code += b'\x49\xFF\xCA'
code += b'\x85\xC0'
offset = label_loop_itoa - (len(code) + 2)
if offset < 0: offset = 256 + offset
code += b'\x75' + p8(offset)
label_do_write = len(code)
offset = label_do_write - (off_jmp_do_write + 2)
code_list = bytearray(code)
code_list[off_jmp_do_write + 1] = offset
code = bytes(code_list)
code += b'\x49\xFF\xC2'
code += b'\x4C\x89\xD6'
code += b'\x4C\x89\xDA'
code += b'\x4C\x29\xD2'
code += b'\x48\xFF\xC2'
code += b'\xBF\x01\x00\x00\x00'
code += b'\xB8\x01\x00\x00\x00'
code += b'\x0F\x05'
code += b'\x49\xFF\xC7'
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
code = patch(code, off_je_load, label_load)
code = patch(code, off_je_store, label_store)
code = patch(code, off_je_open, label_open)
code = patch(code, off_je_write, label_write)
code = patch(code, off_je_close, label_close)
code = patch(code, off_je_read, label_read)
code = patch(code, off_je_exit, label_exit)

# Patch Error
code = patch(code, off_err_open, label_error)
code = patch(code, off_err_read, label_error)

# Data Section
pos_data = len(code)
filename_str = b"read_write_test.bin\x00"
code += filename_str

pos_buffer = len(code)

# Patch LEA
code = patch_lea(code, off_filename, pos_data)
code = patch_lea(code, off_buffer_read, pos_buffer)
code = patch_lea(code, off_buffer_init, pos_buffer)


# Finalizing ELF
total_size = 120 + len(code)
# Memory Layout: Code + Stack(4K) + Heap(64K)
mem_size = total_size + 4096 + 65536

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

print(f"VM v0.6 built successfully. Size: {total_size} bytes.")

import struct
import sys

# Konfigurasi ELF64
# Base Address: 0x400000
# Header Size: 64 (ELF) + 56 (PH) = 120 (0x78)
# Entry Point: 0x400078

def p64(val):
    return struct.pack('<Q', val)

def p32(val):
    return struct.pack('<I', val)

def p16(val):
    return struct.pack('<H', val)

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
elf_header += p32(1)                  # Version
elf_header += p64(0x400078)           # Entry Point (start of code)
elf_header += p64(64)                 # Phdr Offset (follows ELF header)
elf_header += p64(0)                  # Shdr Offset
elf_header += p32(0)                  # Flags
elf_header += p16(64)                 # EH Size
elf_header += p16(56)                 # Phdr Size
elf_header += p16(1)                  # Phdr Count
elf_header += p16(0)                  # Shdr Size
elf_header += p16(0)                  # Shdr Count
elf_header += p16(0)                  # String Table Index

# 2. Program Header
# Size will be calculated later

# 3. Machine Code Logic
# ---------------------
# Layout Estimasi (akan berubah karena ada error handling)
# 00: Open
# 14: Check Error (Baru!)
# ...: Read
# ...: Logic
# ...: Data

code = b''

# -- Open --
# mov eax, 2
code += b'\xB8\x02\x00\x00\x00'
# lea rdi, [rel filename] -> Target Offset filename.
# Kita gunakan placeholder `\x90` (NOP) untuk offset LEA, akan kita patch nanti setelah tahu ukuran kode.
# Instruction: 48 8D 3D [OFFSET 4 byte]
code += b'\x48\x8D\x3D\x00\x00\x00\x00'
lea_filename_offset_pos = len(code) - 4 # Posisi di byte array untuk di-patch

# xor rsi, rsi
code += b'\x48\x31\xF6'
# xor rdx, rdx
code += b'\x48\x31\xD2'
# syscall
code += b'\x0F\x05'

# -- Error Check (Open) --
# cmp rax, 0
# js error_handler
# Instruksi: 48 83 F8 00 (cmp rax, 0) -> atau `test rax, rax` (48 85 C0) lebih pendek
code += b'\x48\x85\xC0' # test rax, rax
# js error_handler (78)
# Target: error_handler label.
# Placeholder offset 1 byte (short jump)
code += b'\x78\x00'
js_error_offset_pos = len(code) - 1

# -- Save FD & Read --
# mov edi, eax
code += b'\x89\xC7'
# mov eax, 0 (read)
code += b'\xB8\x00\x00\x00\x00'

# lea rsi, [rel buffer]
code += b'\x48\x8D\x35\x00\x00\x00\x00'
lea_buffer_offset_pos = len(code) - 4

# mov edx, 100
code += b'\xBA\x64\x00\x00\x00'
# syscall
code += b'\x0F\x05'

# -- Logic --
# lea rbx, [rel buffer]
code += b'\x48\x8D\x1D\x00\x00\x00\x00'
lea_buffer_logic_pos = len(code) - 4

# mov al, [rbx]
code += b'\x8A\x03'
# cmp al, 1 (PUSH)
code += b'\x3C\x01'

# jne +11 (to exit_zero)
code += b'\x75\x00'
jne_exit_zero_pos = len(code) - 1

# -- PUSH Handler --
# mov rdi, [rbx+1]
code += b'\x48\x8B\x7B\x01'
# mov eax, 60 (exit)
code += b'\xB8\x3C\x00\x00\x00'
# syscall
code += b'\x0F\x05'

# -- Exit Zero Label (Target for JNE) --
pos_exit_zero = len(code)
# Patch JNE
offset = pos_exit_zero - (jne_exit_zero_pos + 1)
code_list = bytearray(code)
code_list[jne_exit_zero_pos] = offset
code = bytes(code_list)

# xor rdi, rdi
code += b'\x48\x31\xFF'
# mov eax, 60
code += b'\xB8\x3C\x00\x00\x00'
# syscall
code += b'\x0F\x05'

# -- Error Handler Label (Target for JS) --
pos_error = len(code)
# Patch JS
offset = pos_error - (js_error_offset_pos + 1)
code_list = bytearray(code)
code_list[js_error_offset_pos] = offset
code = bytes(code_list)

# Exit(1)
# mov rdi, 1
code += b'\xBF\x01\x00\x00\x00'
# mov eax, 60
code += b'\xB8\x3C\x00\x00\x00'
# syscall
code += b'\x0F\x05'


# -- Data Section --
pos_data = len(code)
filename_str = b"first_program.bin\x00"
code += filename_str
pos_buffer = len(code)

# -- Patching LEA Offsets --
code_list = bytearray(code)

# 1. Patch LEA Filename
# Instruction: 48 8D 3D [Offset]
# Next RIP = lea_filename_offset_pos + 4
# Target = pos_data
offset_filename = pos_data - (lea_filename_offset_pos + 4)
code_list[lea_filename_offset_pos : lea_filename_offset_pos+4] = p32(offset_filename)

# 2. Patch LEA Buffer (Read)
# Next RIP = lea_buffer_offset_pos + 4
# Target = pos_buffer
offset_buf1 = pos_buffer - (lea_buffer_offset_pos + 4)
code_list[lea_buffer_offset_pos : lea_buffer_offset_pos+4] = p32(offset_buf1)

# 3. Patch LEA Buffer (Logic)
# Next RIP = lea_buffer_logic_pos + 4
# Target = pos_buffer
offset_buf2 = pos_buffer - (lea_buffer_logic_pos + 4)
code_list[lea_buffer_logic_pos : lea_buffer_logic_pos+4] = p32(offset_buf2)

code = bytes(code_list)

# Total Size
total_size = 120 + len(code)
mem_size = total_size + 100 # Add buffer space

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

print(f"VM built successfully. Size: {total_size} bytes.")

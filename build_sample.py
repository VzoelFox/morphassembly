import struct

def p64(val):
    return struct.pack('<Q', val)

def p8(val):
    return struct.pack('B', val)

# Opcode Definitions (sesuai ISA.md)
OP_NOP = 0x00
OP_PUSH = 0x01
OP_POP = 0x02
OP_ADD = 0x03
OP_SUB = 0x04
OP_EXIT = 0xFF

# Program: PUSH 42, EXIT
# Catatan: VM v0.0.1 hanya mengeksekusi instruksi pertama jika itu PUSH, lalu exit dengan nilai tersebut.
# Ini adalah Proof of Concept.

bytecode = b''

# Instruction 1: PUSH 42
bytecode += p8(OP_PUSH)
bytecode += p64(42)

# Instruction 2: EXIT
bytecode += p8(OP_EXIT)

filename = 'first_program.bin'
with open(filename, 'wb') as f:
    f.write(bytecode)

print(f"Sample program '{filename}' created.")

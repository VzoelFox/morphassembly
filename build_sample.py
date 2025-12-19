import struct

def p64(val):
    return struct.pack('<Q', val)

def p32(val):
    return struct.pack('<i', val)

def p8(val):
    return struct.pack('B', val)

# Opcode Definitions
OP_PUSH = 0x01
OP_POP  = 0x02
OP_ADD  = 0x03
OP_SUB  = 0x04
OP_JMP  = 0x05
OP_JZ   = 0x06
OP_EQ   = 0x07
OP_DUP  = 0x08
OP_PRINT= 0x09
OP_EXIT = 0xFF

bytecode = b''

# Program: Print Number Test
# PUSH 123456
# PRINT
# PUSH 0
# PRINT
# PUSH 7
# PRINT
# PUSH 0
# EXIT

bytecode += p8(OP_PUSH) + p64(123456)
bytecode += p8(OP_PRINT)

bytecode += p8(OP_PUSH) + p64(0)
bytecode += p8(OP_PRINT)

bytecode += p8(OP_PUSH) + p64(7)
bytecode += p8(OP_PRINT)

bytecode += p8(OP_PUSH) + p64(0)
bytecode += p8(OP_EXIT)

filename = 'print_test.bin'
with open(filename, 'wb') as f:
    f.write(bytecode)

print(f"Sample program '{filename}' created.")

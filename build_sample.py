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
OP_LOAD = 0x0A
OP_STORE= 0x0B
OP_OPEN = 0x0C
OP_WRITE= 0x0D
OP_CLOSE= 0x0E
OP_EXIT = 0xFF

bytecode = b''

# Program: Storage Test (File I/O)
# 1. Prepare String "Hello\n" in Heap at Address 0
# 'H'(72), 'e'(101), 'l'(108), 'l'(108), 'o'(111), '\n'(10)
# Store manually using loop or one by one.
# To be honest/no shortcut: I will store one by one.

def store_byte(addr, val):
    b = b''
    b += p8(OP_PUSH) + p64(val)
    b += p8(OP_PUSH) + p64(addr)
    b += p8(OP_STORE)
    return b

bytecode += store_byte(0, 72)
bytecode += store_byte(1, 101)
bytecode += store_byte(2, 108)
bytecode += store_byte(3, 108)
bytecode += store_byte(4, 111)
bytecode += store_byte(5, 10)

# 2. Prepare Filename "output.txt\0" in Heap at Address 100
# 'o'(111), 'u'(117), 't'(116), 'p'(112), 'u'(117), 't'(116), '.'(46), 't'(116), 'x'(120), 't'(116), \0(0)
fname = b"output.txt\x00"
for i, char in enumerate(fname):
    bytecode += store_byte(100 + i, char)

# 3. OPEN FILE
# Push Filename Pointer (100)
bytecode += p8(OP_PUSH) + p64(100)
# Push Mode (1 = Write)
bytecode += p8(OP_PUSH) + p64(1)
# OPEN
bytecode += p8(OP_OPEN)
# Stack now has FD. Let's DUP it to keep it for CLOSE later?
# Or just use it for WRITE then CLOSE (FD is on stack? NO, OPEN pushes FD).
# Let's DUP for Safety if we want multiple writes.
bytecode += p8(OP_DUP)

# 4. WRITE FILE
# Stack: [FD, FD]
# Push Data Ptr (0)
bytecode += p8(OP_PUSH) + p64(0)
# Push Length (6)
bytecode += p8(OP_PUSH) + p64(6)
# WRITE (Pops Len, Ptr, FD)
bytecode += p8(OP_WRITE)

# Stack: [FD]
# 5. CLOSE FILE
bytecode += p8(OP_CLOSE)

# 6. EXIT
bytecode += p8(OP_PUSH) + p64(0)
bytecode += p8(OP_EXIT)

filename = 'storage_test.bin'
with open(filename, 'wb') as f:
    f.write(bytecode)

print(f"Sample program '{filename}' created.")

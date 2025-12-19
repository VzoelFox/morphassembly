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
OP_EXIT = 0xFF

bytecode = b''

# Program: Memory Manipulation (Overwrite, Swap, Delete)

# --- TEST 1: Overwrite ---
# Store 111 at Addr 0
bytecode += p8(OP_PUSH) + p64(111)
bytecode += p8(OP_PUSH) + p64(0)
bytecode += p8(OP_STORE)

# Overwrite with 222 at Addr 0
bytecode += p8(OP_PUSH) + p64(222)
bytecode += p8(OP_PUSH) + p64(0)
bytecode += p8(OP_STORE)

# Read & Print (Expect 222)
bytecode += p8(OP_PUSH) + p64(0)
bytecode += p8(OP_LOAD)
bytecode += p8(OP_PRINT)


# --- TEST 2: Swap (Manual via Stack) ---
# Var A (Addr 16) = 10
bytecode += p8(OP_PUSH) + p64(10)
bytecode += p8(OP_PUSH) + p64(16)
bytecode += p8(OP_STORE)

# Var B (Addr 24) = 20
bytecode += p8(OP_PUSH) + p64(20)
bytecode += p8(OP_PUSH) + p64(24)
bytecode += p8(OP_STORE)

# Swap Process:
# Load A (Stack: 10)
bytecode += p8(OP_PUSH) + p64(16)
bytecode += p8(OP_LOAD)

# Load B (Stack: 10, 20)
bytecode += p8(OP_PUSH) + p64(24)
bytecode += p8(OP_LOAD)

# Store Top (20) to A (Addr 16) -> Stack: 10
bytecode += p8(OP_PUSH) + p64(16)
bytecode += p8(OP_STORE)

# Store Next (10) to B (Addr 24) -> Stack: Empty
bytecode += p8(OP_PUSH) + p64(24)
bytecode += p8(OP_STORE)

# Verify Swap
# Print A (Expect 20)
bytecode += p8(OP_PUSH) + p64(16)
bytecode += p8(OP_LOAD)
bytecode += p8(OP_PRINT)

# Print B (Expect 10)
bytecode += p8(OP_PUSH) + p64(24)
bytecode += p8(OP_LOAD)
bytecode += p8(OP_PRINT)


# --- TEST 3: Zeroing (Delete) ---
# Set A (Addr 16) to 0
bytecode += p8(OP_PUSH) + p64(0)
bytecode += p8(OP_PUSH) + p64(16)
bytecode += p8(OP_STORE)

# Print A (Expect 0)
bytecode += p8(OP_PUSH) + p64(16)
bytecode += p8(OP_LOAD)
bytecode += p8(OP_PRINT)


# Exit
bytecode += p8(OP_PUSH) + p64(0)
bytecode += p8(OP_EXIT)

filename = 'memory_swap_test.bin'
with open(filename, 'wb') as f:
    f.write(bytecode)

print(f"Sample program '{filename}' created.")

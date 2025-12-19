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
OP_READ = 0x0F
OP_EXIT = 0xFF

bytecode = b''

# Program: Read Write Test
# 1. Open "output.txt" (Read Mode)
# 2. Read content to Buffer (Addr 200)
# 3. Write content to STDOUT (FD 1)
# 4. Close FD

def store_byte(addr, val):
    b = b''
    b += p8(OP_PUSH) + p64(val)
    b += p8(OP_PUSH) + p64(addr)
    b += p8(OP_STORE)
    return b

# 1. Prepare Filename "output.txt\0" at Addr 0
fname = b"output.txt\x00"
for i, char in enumerate(fname):
    bytecode += store_byte(i, char)

# 2. OPEN FILE (Read Mode)
bytecode += p8(OP_PUSH) + p64(0) # Ptr Filename
bytecode += p8(OP_PUSH) + p64(0) # Mode 0 (Read)
bytecode += p8(OP_OPEN)
# Stack: [FD]

# 3. READ FILE
# Push FD (DUP logic? No DUP instruction used here, just assume FD on top)
bytecode += p8(OP_DUP) # Keep FD for Close later
# Stack: [FD, FD]

# Push Ptr Buffer (Addr 200)
bytecode += p8(OP_PUSH) + p64(200)
# Push Length (10 bytes - enough for "Hello\n")
bytecode += p8(OP_PUSH) + p64(10)
# READ
bytecode += p8(OP_READ)
# Stack: [FD, BytesRead]

# 4. WRITE TO STDOUT
# We want to write what we read.
# Stack: [FD, BytesRead]
# We need: Length(BytesRead), Ptr(200), FD(1).
# Ops:
# Pop BytesRead -> Temp storage? No register.
# Let's assume we read 6 bytes ("Hello\n").
# But wait, READ returns real count.
# Stack: [FD, Count]
# We need [1, 200, Count] for WRITE?
# WRITE expects: Pop Length, Pop Ptr, Pop FD.
# Stack should be: [FD, Ptr, Length] -> Then WRITE pops Len, Ptr, FD.
# Current Stack: [FD, Count].
# We need to rearrange stack? Or just use Count.

# Let's cheat slightly and assume Count is Top.
# We need to insert Ptr(200) and FD(1) below it? Or re-push.
# Swap isn't available.
# Let's just pop Count, and re-push hardcoded length?
# Or better: Print Count to debug?
bytecode += p8(OP_DUP)
bytecode += p8(OP_PRINT) # Print Bytes Read (Should be 6)

# Stack: [FD, Count]
# Discard Count (POP)
bytecode += p8(OP_POP)

# Stack: [FD]
# Now Write Buffer to STDOUT
bytecode += p8(OP_PUSH) + p64(1)   # FD 1 (Stdout)
bytecode += p8(OP_PUSH) + p64(200) # Buffer
bytecode += p8(OP_PUSH) + p64(6)   # Length (Hardcoded for simplicity)
bytecode += p8(OP_WRITE)

# Stack: [FD]
# 5. CLOSE FILE
bytecode += p8(OP_CLOSE)

# 6. EXIT
bytecode += p8(OP_PUSH) + p64(0)
bytecode += p8(OP_EXIT)

filename = 'read_write_test.bin'
with open(filename, 'wb') as f:
    f.write(bytecode)

print(f"Sample program '{filename}' created.")

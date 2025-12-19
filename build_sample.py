import struct

def p64(val):
    return struct.pack('<Q', val)

def p32(val):
    return struct.pack('<i', val)

def p8(val):
    return struct.pack('B', val)

# Opcode Definitions (sesuai ISA.md)
OP_PUSH = 0x01
OP_POP  = 0x02
OP_ADD  = 0x03
OP_SUB  = 0x04
OP_JMP  = 0x05
OP_JZ   = 0x06
OP_EQ   = 0x07
OP_DUP  = 0x08
OP_EXIT = 0xFF

bytecode = b''

# Program: Countdown Loop 3 -> 0
#
# 0: PUSH 3
# 9: LABEL_LOOP:
# 9: DUP
# 10: PUSH 0
# 19: EQ
# 20: JZ +14 (Jump to LABEL_SUB if NOT zero/equal? Wait logic check)
#     Current JZ Logic: Pop A. If A == 0, Jump.
#     EQ Logic: Push 1 if Equal, 0 if Not.
#     So: if 3 == 0 -> EQ pushes 0. JZ pops 0 (True) -> Jumps.
#     Wait, if 3 != 0 -> EQ pushes 0. JZ pops 0 -> Jumps.
#     My Logic is inverted or I am confused.
#     EQ: 3 == 0 ? False (0).
#     JZ: If 0, JUMP.
#     So if NOT EQUAL, it Jumps?
#     We want: If EQUAL (to 0), EXIT.
#     So if EQ pushes 1 (Equal), we want to Jump. JZ jumps on 0.
#     We need JNZ (Jump Not Zero) or invert the check.
#     Or check PUSH 0; EQ; -> 0 (False). JZ jumps.
#     Let's use SUB logic directly?
#     PUSH 3.
#     LOOP:
#     DUP
#     PUSH 0
#     EQ (3==0 -> 0).
#     SUB 1 (0-1 = -1). JZ... messy.
#
#     Let's stick to simple:
#     If Top == 0, Exit.
#     We only have JZ (Jump if 0).
#     We want: Jump if 1 (True).
#     Workaround: Compare with 0 (False). EQ.
#     If Top == 0 (True). EQ pushes 1.
#     If Top != 0 (False). EQ pushes 0.
#     Then JZ (Jump if 0).
#     So if Top != 0, EQ -> 0. JZ -> Jumps.
#     This means "Jump if Not Zero".
#     So we can use this to LOOP back.

# Revised Logic (Jump if Not Zero):
# PUSH 3
# LABEL_Start:
#   DUP
#   PUSH 0
#   EQ          (Stack: 1 if Zero, 0 if Not Zero)
#   JZ LABEL_LOGIC (If 0/NotZero, Jump to Logic)
#   EXIT        (If 1/Zero, Fallthrough to Exit)
#
# LABEL_LOGIC:
#   PUSH 1
#   SUB
#   JMP LABEL_Start


# Offset Calculations are tricky manually.
# Let's construct bytearray and measure.

# Instruction 1: PUSH 3
start_code = b''
start_code += p8(OP_PUSH) + p64(3)

loop_start_offset = len(start_code)

# Loop Body
loop_body = b''
# DUP
loop_body += p8(OP_DUP)
# PUSH 0
loop_body += p8(OP_PUSH) + p64(0)
# EQ
loop_body += p8(OP_EQ)
# JZ [OFFSET_LOGIC]
# We don't know offset yet. Placeholder 5 bytes.
jz_instruction_idx = len(loop_body)
loop_body += p8(OP_JZ) + p32(0)

# EXIT (Fallthrough)
# EXIT
loop_body += p8(OP_EXIT)

# LABEL_LOGIC
logic_start_idx = len(loop_body)

# PUSH 1
loop_body += p8(OP_PUSH) + p64(1)
# SUB
loop_body += p8(OP_SUB)
# JMP [OFFSET_LOOP_START]
# JMP to start of Loop Body? Or Start of PUSH 3?
# Loop Start is DUP (index 0 of loop_body).
# Current Pos is end of loop_body + 5 bytes (JMP instr).
# Offset = Target - CurrentPos_Start_Of_Instr
jmp_target = 0 # Relative to start of loop_body
current_instr_pos_relative = len(loop_body)
offset_back = jmp_target - current_instr_pos_relative
loop_body += p8(OP_JMP) + p32(offset_back)


# Now fix JZ Offset
# JZ is at jz_instruction_idx.
# Target is logic_start_idx.
# Offset = logic_start_idx - jz_instruction_idx
jz_offset = logic_start_idx - jz_instruction_idx
# Reconstruct JZ
jz_code = p8(OP_JZ) + p32(jz_offset)
# Patch loop body
loop_body = loop_body[:jz_instruction_idx] + jz_code + loop_body[jz_instruction_idx+5:]

full_code = start_code + loop_body

filename = 'loop_program.bin'
with open(filename, 'wb') as f:
    f.write(full_code)

print(f"Sample program '{filename}' created.")

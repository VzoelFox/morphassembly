# MorphAssembly Instruction Set Architecture (ISA) v0.2

Dokumen ini mendefinisikan esensi dari mesin virtual MorphAssembly.

## Struktur Mesin Virtual (VM)

### Tipe Data
- Semua operasi berbasis **integer 64-bit**.

### Register
VM memiliki register internal untuk operasi:
- `IP` (Instruction Pointer): Menunjuk ke instruksi yang sedang dieksekusi.
- `SP` (Stack Pointer): Menunjuk ke puncak stack.

### Stack
- Stack digunakan untuk operasi aritmatika dan penyimpanan sementara.

## Opcode (Daftar Instruksi)

Setiap instruksi dimulai dengan 1 byte Opcode.

| Opcode (Hex) | Mnemonic | Operan | Deskripsi |
| :--- | :--- | :--- | :--- |
| `0x00` | **NOP** | - | No Operation. |
| `0x01` | **PUSH** | 8-byte (Int64) | Masukkan angka 64-bit ke dalam stack. |
| `0x02` | **POP** | - | Hapus angka teratas dari stack. |
| `0x03` | **ADD** | - | Pop A, Pop B, Push (A + B). |
| `0x04` | **SUB** | - | Pop A, Pop B, Push (B - A). |
| `0x05` | **JMP** | 4-byte (Int32) | Lompat relatif (IP += offset). |
| `0x06` | **JZ** | 4-byte (Int32) | Pop A. Jika A == 0, Lompat relatif (IP += offset). |
| `0x07` | **EQ** | - | Pop A, Pop B. Push 1 jika A == B, else 0. |
| `0x08` | **DUP** | - | Duplikasi nilai teratas stack. |
| `0xFF` | **EXIT** | - | Hentikan program. Exit Code = Pop Stack. |

## Contoh Program (Loop)

Program hitung mundur 3 ke 0:

```
PUSH 3
LABEL_LOOP:
  DUP         ; Stack: [3, 3]
  PUSH 0      ; Stack: [3, 3, 0]
  EQ          ; Stack: [3, 0] (Karena 3 != 0)
  JZ CONTINUE ; Jika 0 (false), lanjut. Jika 1 (true/equal), kita tidak jump (eh terbalik logika JZ, nanti disesuaikan).

  ; Logika harusnya:
  ; DUP
  ; PUSH 0
  ; EQ
  ; JNZ EXIT_LOOP (Kalau Equal, keluar)
  ; ...
```
(Detail implementasi di `build_sample.py`)

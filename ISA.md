# MorphAssembly Instruction Set Architecture (ISA) v0.1

Dokumen ini mendefinisikan esensi dari mesin virtual MorphAssembly.

## Struktur Mesin Virtual (VM)

### Tipe Data
- Semua operasi berbasis **integer 64-bit**.

### Register
VM memiliki register internal untuk operasi:
- `IP` (Instruction Pointer): Menunjuk ke instruksi yang sedang dieksekusi.
- `SP` (Stack Pointer): Menunjuk ke puncak stack.
- `R0` - `R3`: Register umum (General Purpose Registers).

### Stack
- Stack digunakan untuk operasi aritmatika dan penyimpanan sementara.
- Tumbuh dari alamat tinggi ke rendah (atau implementasi sederhana: array fix).

## Opcode (Daftar Instruksi)

Setiap instruksi panjangnya 1 byte (Opcode) + Operan (jika ada).

| Opcode (Hex) | Mnemonic | Operan | Deskripsi |
| :--- | :--- | :--- | :--- |
| `0x00` | **NOP** | - | No Operation. Tidak melakukan apa-apa. |
| `0x01` | **PUSH** | 1 (64-bit Int) | Masukkan angka 64-bit ke dalam stack. |
| `0x02` | **POP** | - | Hapus angka teratas dari stack. |
| `0x03` | **ADD** | - | Ambil 2 angka teratas stack, jumlahkan, push hasilnya. |
| `0x04` | **SUB** | - | Ambil 2 angka teratas stack, kurangi, push hasilnya. |
| `0xFF` | **EXIT** | - | Hentikan program. Menggunakan nilai top stack sebagai exit code. |

## Contoh Program (Binary Layout)

Program untuk menghitung 10 + 20:

```
ADDR  BYTE    MNEMONIC
----  ----    --------
0000  01      PUSH
0001  0A      10 (low byte) ... (64-bit little endian)
0009  01      PUSH
000A  14      20 (low byte) ...
0012  03      ADD
0013  FF      EXIT
```

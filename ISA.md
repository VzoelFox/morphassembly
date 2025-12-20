# MorphAssembly Instruction Set Architecture (ISA) v0.6

Dokumen ini mendefinisikan esensi dari mesin virtual MorphAssembly.

## Struktur Mesin Virtual (VM)

### Tipe Data
- Semua operasi berbasis **integer 64-bit**.

### Register
VM memiliki register internal untuk operasi:
- `IP` (Instruction Pointer): Menunjuk ke instruksi yang sedang dieksekusi.
- `SP` (Stack Pointer): Menunjuk ke puncak stack.
- `HP` (Heap Pointer / Base): Alamat awal memori data (Linear Memory).

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
| `0x09` | **PRINT**| - | Pop nilai teratas stack, cetak sebagai Angka Desimal. |
| `0x0A` | **LOAD** | - | Pop Alamat. Push nilai dari [HP + Alamat]. |
| `0x0B` | **STORE**| - | Pop Alamat, Pop Nilai. Simpan Nilai ke [HP + Alamat]. |
| `0x0C` | **OPEN** | - | Pop Mode, Pop Ptr Filename. Buka File. Push FD. |
| `0x0D` | **WRITE**| - | Pop Length, Pop Ptr Data, Pop FD. Tulis ke File. |
| `0x0E` | **CLOSE**| - | Pop FD. Tutup File. |
| `0x0F` | **READ** | - | Pop Length, Pop Ptr Buffer, Pop FD. Baca File. Push ReadCount. |
| `0x10` | **BREAK**| - | Pause eksekusi dan masuk ke Debugger Mode (jika aktif). |
| `0xFF` | **EXIT** | - | Hentikan program. Exit Code = Pop Stack. |

## Detail IO File
- **OPEN**: Mode 0 = Read Only, Mode 1 = Write Only (Create/Truncate).
- **READ**: Membaca dari FD ke Buffer (Heap). Mendorong jumlah byte yang berhasil dibaca ke Stack.
- **WRITE**: Menulis dari Buffer (Heap) ke FD.

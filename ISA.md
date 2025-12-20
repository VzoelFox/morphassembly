# MorphAssembly Instruction Set Architecture (ISA) v0.6

Dokumen ini mendefinisikan esensi dari mesin virtual MorphAssembly.

## Struktur Mesin Virtual (VM)

### Tipe Data
- Semua operasi berbasis **integer 64-bit**.

### Register
VM memiliki register internal untuk operasi:
- `IP` (Instruction Pointer): Menunjuk ke instruksi yang sedang dieksekusi.
- `SP` (Stack Pointer): Menunjuk ke puncak stack.
- `HP` (Heap Pointer / Base): Alamat awal memori data (Dynamic Linear Memory).

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
| `0x10` | **BREAK**| - | Pause eksekusi dan masuk ke Debugger Mode (jika aktif). |
| `0x11` | **SYSCALL**| - | Pop ID, Jalankan System Call. |
| `0x20` | **SPAWN** | - | Pop Address. Spawn new Context at Address. |
| `0x21` | **YIELD** | - | Serahkan sisa time-slice ke Context lain (Cooperative Multitasking). |
| `0x22` | **JOIN**  | - | Menunggu Context lain selesai (Belum diimplementasikan penuh). |

## System Calls (SYSCALL)

Argumen diambil dari Stack (Pop) sesuai urutan yang dibutuhkan.
*Catatan: Stack LIFO, jadi push argumen terakhir terlebih dahulu.*

| ID | Nama | Argumen (Top of Stack -> Bottom) | Deskripsi |
| :--- | :--- | :--- | :--- |
| `0` | **EXIT** | `Code` | Keluar program dengan Exit Code. |
| `1` | **OPEN** | `Mode`, `PtrFilename` | Buka file. Push FD ke Stack. |
| `2` | **CLOSE**| `FD` | Tutup file descriptor. |
| `3` | **READ** | `Len`, `PtrBuffer`, `FD` | Baca file. Push BytesRead ke Stack. |
| `4` | **WRITE**| `Len`, `PtrData`, `FD` | Tulis ke file. |
| `5` | **SBRK** | `Increment` | Tambah ukuran Heap sebesar `Increment` bytes. Push alamat awal area baru (Old Break). |

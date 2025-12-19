# MorphAssembly (Versi C)

MorphAssembly adalah proyek eksperimental untuk membangun **Virtual Machine (VM)** berbasis Stack dengan filosofi "Tanpa Jalan Pintas". Versi ini (v0.6) diimplementasikan dalam C untuk stabilitas, performa, dan kepatuhan standar.

## Struktur Proyek

- `morph_vm.c`: Implementasi Virtual Machine dalam C.
- `gen_test.c`: Generator bytecode (Assembler sederhana) untuk keperluan pengujian.
- `ISA.md`: Definisi Instruction Set Architecture (v0.6).
- `test.bin`: Bytecode biner hasil generate (dibuat oleh `gen_test`).

## Fitur (v0.6)

- **Arsitektur**: Stack-based, integer 64-bit.
- **Memori**: Linear Memory 64KB (Heap).
- **Instruction Set**:
  - Aritmatika: `ADD`, `SUB`, `EQ`
  - Stack: `PUSH`, `POP`, `DUP`
  - Kontrol Alur: `JMP`, `JZ`
  - I/O: `PRINT`, `OPEN`, `READ`, `WRITE`, `CLOSE`
  - Memori: `LOAD`, `STORE`

## Cara Kompilasi dan Menjalankan

### 1. Kompilasi VM dan Generator

```bash
gcc -o morph_vm morph_vm.c
gcc -o gen_test gen_test.c
```

### 2. Generate Bytecode Tes

Perintah ini akan membuat file `test.bin`.

```bash
./gen_test
```

### 3. Jalankan VM

```bash
./morph_vm test.bin
```

### Output yang Diharapkan

```
30
30
```

## Lisensi
MIT

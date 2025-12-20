# MorphAssembly (Versi C)

MorphAssembly adalah proyek eksperimental untuk membangun **Virtual Machine (VM)** agnostik sistem.
Versi ini (v0.6 C-Rewrite) telah ditulis ulang sepenuhnya menggunakan **C Standar** untuk stabilitas dan kemudahan pengembangan, menggantikan metode "Assembly Manual" berbasis Python sebelumnya.

## Filosofi
- **Kejujuran Teknis**: VM mensimulasikan memori, stack, dan register secara eksplisit dalam kode C.
- **Portabilitas**: Dapat dikompilasi di sistem manapun yang memiliki compiler C (GCC/Clang) dan standar POSIX (untuk File I/O).

## Struktur Proyek
- `morph_vm.c`: Source code utama Virtual Machine. Mengimplementasikan siklus Fetch-Decode-Execute dan manajemen memori.
- `gen_test.c`: Program utilitas untuk menghasilkan file bytecode biner (`read_write_test.bin`) sebagai contoh.
- `ISA.md`: Definisi Instruction Set Architecture.

## Cara Kompilasi dan Menjalankan

### 1. Kompilasi VM dan Generator

### 1. Build VM dan Generator
Gunakan GCC untuk mengompilasi source code.
```bash
gcc -o morph_vm morph_vm.c
gcc -o gen_test gen_test.c
```

### 2. Buat Program Contoh
Jalankan generator untuk membuat file biner `read_write_test.bin`.
```bash
./gen_test
```
*Note: Program ini akan mencoba membaca file `output.txt`, jadi pastikan file tersebut ada.*
```bash
echo "Hello World" > output.txt
```

### 3. Jalankan VM
Jalankan VM dengan memberikan file biner sebagai argumen.
```bash
./morph_vm read_write_test.bin
```

**Output yang diharapkan:**
```
10      (Jumlah byte yang berhasil dibaca dari permintaan 10 byte)
Hello   (6 byte pertama dari buffer yang ditulis ke stdout)
```

## Arsitektur (v0.6)
- **Memory**: Linear Memory (Code + Stack + Heap).
- **Stack**: Ascending Stack (Tumbuh ke atas / alamat lebih tinggi).
- **IO**: Mendukung `OPEN`, `READ`, `WRITE`, `CLOSE` (POSIX wrapper), dan `PRINT` (Stdout).

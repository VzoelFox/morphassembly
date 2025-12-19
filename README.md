# MorphAssembly

MorphAssembly adalah proyek eksperimental untuk membangun **Virtual Machine (VM)** agnostik sistem secara bertahap, dimulai dari level terendah (pure binary/hex).

## Filosofi
Proyek ini mematuhi prinsip "Tanpa Jalan Pintas".
- VM awal dibangun dengan menulis kode mesin x86_64 secara manual (tanpa compiler C/C++/Rust).
- Setiap instruksi didefinisikan secara eksplisit.
- Mengutamakan kejujuran dalam kapabilitas ("jangan bilang bisa jika tidak bisa").

## Struktur Proyek
- `ISA.md`: Definisi Instruction Set Architecture (Opcode & Logika).
- `build_vm.py`: Script Python yang berfungsi sebagai "Assembler Manual" untuk menghasilkan executable VM (`morph_vm`) dari kode hex mentah.
- `build_sample.py`: Script untuk membuat program contoh MorphAssembly (`first_program.bin`).

## Cara Menggunakan

### 1. Build VM
Karena kita tidak menggunakan compiler, kita menggunakan generator hex untuk membuat executable Linux.
```bash
python3 build_vm.py
chmod +x morph_vm
```

### 2. Buat Program Contoh
Buat file bytecode `first_program.bin` yang berisi instruksi untuk VM.
Contoh ini membuat program yang melakukan `PUSH 42` dan `EXIT`.
```bash
python3 build_sample.py
```

### 3. Jalankan
Jalankan VM. VM akan otomatis mencari `first_program.bin` di direktori yang sama, membacanya, dan mengeksekusinya.
Hasil eksekusi (untuk saat ini) dikembalikan sebagai Exit Code proses.
```bash
./morph_vm
echo "Exit Code: $?"
```
Harusnya outputnya: `Exit Code: 42`.

Jika file tidak ditemukan, VM akan exit dengan kode `1`.

## Status Saat Ini (v0.0.1)
- **Proof of Concept**: VM berhasil membaca file biner eksternal dan mengeksekusi instruksi dasar.
- **Support**: Hanya instruksi `PUSH` (sebagai demonstrasi passing data) dan `EXIT`.
- **Robustness**: Error handling dasar untuk pembukaan file.

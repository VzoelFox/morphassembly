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
- `build_sample.py`: Script untuk membuat program contoh MorphAssembly (Bytecode).

## Fitur Utama (v0.4)
- **Core**: Stack-based architecture dengan register internal minimal.
- **Compute**: Aritmatika (`ADD`, `SUB`), Logika (`EQ`), Stack (`PUSH`, `POP`, `DUP`).
- **Flow Control**: `JMP`, `JZ` (Conditional Branching).
- **IO**: `PRINT` (Mencetak angka desimal ke STDOUT).
- **Memory**: Linear Memory Model (`LOAD`, `STORE`) untuk manipulasi data (RAM).

## Cara Menggunakan

### 1. Build VM
VM dibangun langsung dari definisi Python ke ELF64 Binary.
```bash
python3 build_vm.py
chmod +x morph_vm
```

### 2. Buat Program Contoh
Saat ini, script dikonfigurasi untuk membuat tes manipulasi memori (`memory_swap_test.bin`).
```bash
python3 build_sample.py
```

### 3. Jalankan
Jalankan VM. VM akan otomatis mencari `memory_swap_test.bin` di direktori yang sama.
```bash
./morph_vm
```
**Output yang diharapkan (Memory Test):**
```
222  (Overwrite Test)
20   (Swap Result A)
10   (Swap Result B)
0    (Zeroing Test)
```

## Status Saat Ini (v0.4)
- **Linear Memory**: VM memiliki akses ke area Heap (64KB) untuk menyimpan variabel.
- **Robustness**: Error handling untuk file tidak ditemukan, dan perbaikan logika jump offset dinamis.

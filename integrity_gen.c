#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sha256.h"

void hash_file(const char *filepath, uint8_t *hash_out) {
    FILE *f = fopen(filepath, "rb");
    if (!f) {
        fprintf(stderr, "Error: Tidak dapat membuka file %s untuk hashing\n", filepath);
        exit(1);
    }

    SHA256_CTX ctx;
    sha256_init(&ctx);

    uint8_t buffer[1024];
    size_t bytes;
    while ((bytes = fread(buffer, 1, sizeof(buffer), f)) > 0) {
        sha256_update(&ctx, buffer, bytes);
    }

    sha256_final(&ctx, hash_out);
    fclose(f);
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        printf("Penggunaan: %s <source_file> <bin_file> <output_chk>\n", argv[0]);
        return 1;
    }

    const char *source_path = argv[1];
    const char *bin_path = argv[2];
    const char *out_path = argv[3];

    uint8_t source_hash[32];
    uint8_t bin_hash[32];

    printf("Hashing Kode Sumber: %s\n", source_path);
    hash_file(source_path, source_hash);

    printf("Hashing Bytecode: %s\n", bin_path);
    hash_file(bin_path, bin_hash);

    FILE *out = fopen(out_path, "wb");
    if (!out) {
        fprintf(stderr, "Error: Tidak dapat menulis ke %s\n", out_path);
        return 1;
    }

    // Write Source Hash (32 bytes)
    fwrite(source_hash, 1, 32, out);
    // Write Bin Hash (32 bytes)
    fwrite(bin_hash, 1, 32, out);

    fclose(out);
    printf("Manifest Integritas ditulis ke %s\n", out_path);

    return 0;
}

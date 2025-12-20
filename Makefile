CC = gcc
CFLAGS = -Wall -Wextra

all: morph_vm gen_test integrity_gen

morph_vm: morph_vm.c sha256.c
	$(CC) $(CFLAGS) -o morph_vm morph_vm.c sha256.c

gen_test: gen_test.c
	$(CC) $(CFLAGS) -o gen_test gen_test.c

integrity_gen: integrity_gen.c sha256.c
	$(CC) $(CFLAGS) -o integrity_gen integrity_gen.c sha256.c

clean:
	rm -f morph_vm gen_test integrity_gen *.o test.bin integrity.chk

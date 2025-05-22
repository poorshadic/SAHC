#include "Enclave.h"
#include "Enclave_t.h" /* print_string */
#include <stdarg.h>
#include <stdio.h> /* vsnprintf */
#include <string.h>

int printf(const char* fmt, ...){
    char buf[BUFSIZ] = { '\0' };
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, BUFSIZ, fmt, ap);
    va_end(ap);
    ocall_print_string(buf);
    return (int)strnlen(buf, BUFSIZ - 1) + 1;
}

void process_data(const uint8_t* data, size_t len) {
	printf("READ %ld bytes: ", len);
	for(size_t i = 0; i < len; ++i)
		printf("0x%02X ", data[i]);
	printf("\n");
}


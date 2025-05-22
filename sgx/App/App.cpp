#include <stdio.h>
#include <vector>
#include <string>
#include <curl/curl.h>
#include "sgx_urts.h"
#include "Enclave_u.h"

#define ENCLAVE_FILENAME "enclave.signed.so"

/* OCall functions */
void ocall_print_string(const char *str)
{
    /* Proxy/Bridge will check the length and null-terminate
     * the input string to prevent buffer overflow.
     */
    printf("%s", str);
}


static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    std::vector<uint8_t>* buffer = (std::vector<uint8_t>*)userp;
    size_t totalSize = size * nmemb;
    buffer->insert(buffer->end(), (uint8_t*)contents, (uint8_t*)contents + totalSize);
    return totalSize;
}

int main() {
    sgx_enclave_id_t eid;
    sgx_status_t ret;

    ret = sgx_create_enclave(ENCLAVE_FILENAME, SGX_DEBUG_FLAG, NULL, NULL, &eid, NULL);
    if (ret != SGX_SUCCESS) {
        printf("Failed to create enclave, error: 0x%x\n", ret);
        return 1;
    }

    std::string url = "http://172.17.0.1:9000/";
    std::vector<uint8_t> data;

    curl_global_init(CURL_GLOBAL_DEFAULT);
    CURL* curl = curl_easy_init();

    if (!curl) {
        printf("Failed to init CURL\n");
        sgx_destroy_enclave(eid);
        return 1;
    }

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &data);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);

    CURLcode res = curl_easy_perform(curl);
    if (res != CURLE_OK) {
        printf("CURL download failed: %s\n", curl_easy_strerror(res));
        curl_easy_cleanup(curl);
        sgx_destroy_enclave(eid);
        return 1;
    }

    curl_easy_cleanup(curl);
    curl_global_cleanup();

    // Call enclave function
    ret = process_data(eid, data.data(), data.size());
    if (ret != SGX_SUCCESS) {
        printf("Enclave call failed: 0x%x\n", ret);
        sgx_destroy_enclave(eid);
        return 1;
    }

    sgx_destroy_enclave(eid);
    return 0;
}

import base64

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
from minio import Minio
from minio import S3Error
import os
import sys
import json
import csv

client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)

with open("../sgx/Enclave/EnclavePublic.pem", "rb") as enclave_public:
    pubkey = RSA.importKey(enclave_public.read())
    cypher = PKCS1_OAEP.new(pubkey)

my_map = list()

def get_fields(file):
    file_type = file.split(".")[-1].lower()
    with open(file, "r") as f:
        data = f.read()
    if file_type == "json":
        json_data = json.loads(data)
        return list(json_data.keys())
    elif file_type == "csv":
        return data.splitlines()[0].split(',')
    else:
        raise Exception("Invalid type")


def main():

    for file in sys.argv[1:]:
        aes_key = get_random_bytes(32)
        nonce = get_random_bytes(16)
        cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)

        bucket_name = file.split(".")[0]
        file_name = ".".join(file.split(".")[1::])
        file_name_enc = file_name + ".enc"

        with open(file, "rb") as f:
            cypher_text = cipher_aes.encrypt(f.read())
        with open(file_name_enc, "wb") as f:
            f.write(cypher_text)

        aes_key_enc = cypher.encrypt(aes_key)
        nonce_enc = cypher.encrypt(nonce)

        my_map.append({
            "bucket": bucket_name,
            "object": file_name_enc,
            "key": base64.b64encode(aes_key_enc).decode("ascii"),
            "nonce": base64.b64encode(nonce_enc).decode("ascii"),
            "fields": get_fields(file),
        })

    # Gen another key
    aes_key = get_random_bytes(32)
    nonce = get_random_bytes(16)
    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    # Encrypt my_map
    with open("map.json.enc", "wb") as my_map_file_enc:
        json_my_map_str = json.dumps(my_map)
        json_my_map_bytes = bytes(json_my_map_str, "utf-8")
        cypher_text = cipher_aes.encrypt(json_my_map_bytes)
        my_map_file_enc.write(cypher_text)

    aes_key_enc = cypher.encrypt(aes_key)
    nonce_enc = cypher.encrypt(nonce)

    with open("key.enc", "wb") as key_file:
        key_file.write(aes_key_enc)
    with open("nonce.enc", "wb") as nonce_file:
        nonce_file.write(nonce_enc)

    my_map.append({
        "bucket": "map",
        "object": "map.json.enc",
    })
    my_map.append({
        "bucket": "map",
        "object": "key.enc",
    })
    my_map.append({
        "bucket": "map",
        "object": "nonce.enc",
    })

    for entry in my_map:
        try:
            if not client.bucket_exists(entry["bucket"]):
                client.make_bucket(entry["bucket"])
            client.fput_object(entry["bucket"], entry["object"], entry["object"])
        except S3Error as e:
            print("Error uploading: ", e)
        finally:
            os.remove(entry["object"])


if __name__ == "__main__":
    main()

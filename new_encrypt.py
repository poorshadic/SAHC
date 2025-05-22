"""

Performs the initial push of data to minio

"""


from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
from minio import Minio
from minio.error import S3Error
import os

# === 1. Carregar chave pública da enclave ===
with open("keys/sgx_public.pem", "rb") as f:
    pub_key = RSA.import_key(f.read())
    cipher_rsa = PKCS1_OAEP.new(pub_key)

# === 2. Abrir e ler o ficheiro (por exemplo, JSON) ===
with open("json1.json", "rb") as f:
    dados = f.read()

# === 3. Gerar chave AES e nonce ===
aes_key = get_random_bytes(32)  # AES-256
nonce = get_random_bytes(12)    # Recomendado para AES-GCM

# === 4. Encriptar os dados com AES-GCM ===
cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
ciphertext, tag = cipher_aes.encrypt_and_digest(dados)

# === 5. Encriptar a chave AES com RSA (chave pública da enclave) ===
encrypted_aes_key = cipher_rsa.encrypt(aes_key)

# === 6. Montar o conteúdo final ===
# [tamanho_chave_rsa (2 bytes)] + [chave_aes_encriptada] + [nonce (12B)] + [tag (16B)] + [dados_encriptados]
with open("temp.enc", "wb") as f:
    f.write(len(encrypted_aes_key).to_bytes(2, byteorder='big'))
    f.write(encrypted_aes_key)
    f.write(nonce)
    f.write(tag)
    f.write(ciphertext)

# === 7. Enviar para o MinIO ===
client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)

bucket_name = "dados-laboratorio"  # bucket existente
object_name = "json1.json.enc"  # nome do ficheiro no MinIO

try:
    client.fput_object(bucket_name, object_name, "temp.enc")
    print("✔️ Upload concluído.")
except S3Error as e:
    print("Erro no upload:", e)

os.remove("temp.enc")

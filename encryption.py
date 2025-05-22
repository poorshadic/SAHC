from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP # para adaptive attacks
from minio import Minio
from minio.error import S3Error
import os


# 1. Carregar chave publica da enclave
with open("keys/sgx_public.pem", "rb") as f:
    pub_key = RSA.import_key(f.read()) #criação do objeto chave
    cipher_rsa = PKCS1_OAEP.new(pub_key) #criação de ficheiro de encriptação

# 2. Abrir e ler o ficheiro CSV (binary)
with open("json1.json", "rb") as f:
    dados_medicos = f.read()

# 3. Gerar ficheiro encriptado (binary)
dados_encriptados = cipher_rsa.encrypt(dados_medicos)

# 4. Enviar para o MinIO
client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)

bucket_name = "map" #usar nome de bucket existente
object_name = "map.json.enc" #definir nome do ficheiro a guardar


# 1. Criar ficheiro temp.enc com os dados cifrados
with open("temp.enc", "wb") as f:
    f.write(dados_encriptados)

# 2. Fazer upload para o MinIO
try:
    client.fput_object(bucket_name, object_name, "temp.enc")
    print("✔️ Upload concluído.")
except S3Error as e:
    print("Erro no upload:", e)

os.remove("temp.enc")
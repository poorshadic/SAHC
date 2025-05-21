from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from minio import Minio
import json

# 1. Conectar ao MinIO
client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# 2. Carregar chave privada da enclave
with open("keys/sgx_private.pem", "rb") as f:
    private_key = RSA.import_key(f.read())
    cipher_rsa = PKCS1_OAEP.new(private_key)

# 3. Fazer download do map.enc do bucket "map"
response = client.get_object("map", "map.enc")
dados_encriptados = response.read()
response.close()

# 4. Desencriptar o conteúdo do mapa
dados_desencriptados = cipher_rsa.decrypt(dados_encriptados)

# 5. Guardar como ficheiro JSON local (ex: mapa.json)
with open("mapa.json", "wb") as f:
    f.write(dados_desencriptados)

print("✔️ Mapa desencriptado e guardado como 'mapa.json'")

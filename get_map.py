from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from minio import Minio
import io

# === CONFIGURAÇÃO ===
bucket_name = "map"
object_name = "map.json.enc"
ficheiro_saida = "mapa.json"
chave_privada_path = "keys/sgx_private.pem"

# === 1. Conectar ao MinIO ===
client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)

# === 2. Carregar a chave privada da enclave ===
with open(chave_privada_path, "rb") as f:
    private_key = RSA.import_key(f.read())
    cipher_rsa = PKCS1_OAEP.new(private_key)

# === 3. Fazer download do ficheiro cifrado e criar stream de leitura
response = client.get_object(bucket_name, object_name)
data_stream = io.BytesIO(response.read())  # cria "ficheiro em memória"
response.close()

# === 4. Ler sequencialmente como com open(..., 'rb')
with data_stream as f:
    key_len_bytes = f.read(2)  # primeiros 2 bytes = tamanho da chave AES cifrada
    key_len = int.from_bytes(key_len_bytes, byteorder='big')

    encrypted_aes_key = f.read(key_len)  # chave AES cifrada (com RSA)
    nonce = f.read(12)                   # nonce para AES-GCM
    tag = f.read(16)                     # tag de integridade
    ciphertext = f.read()                # resto = dados cifrados com AES

# === 5. Desencriptar a chave AES
aes_key = cipher_rsa.decrypt(encrypted_aes_key)

# === 6. Desencriptar os dados com AES-GCM
cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
dados_desencriptados = cipher_aes.decrypt_and_verify(ciphertext, tag)

# === 7. Guardar o conteúdo original
with open(ficheiro_saida, "wb") as f_out:
    f_out.write(dados_desencriptados)

print(f"✔️ Ficheiro '{object_name}' desencriptado e guardado como '{ficheiro_saida}'")

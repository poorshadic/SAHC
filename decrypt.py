from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# 1. Carregar a chave privada (da enclave ou simulada)
with open("keys/sgx_private.pem", "rb") as f:
    private_key = RSA.import_key(f.read())
    cipher_rsa = PKCS1_OAEP.new(private_key)

# 2. Ler os dados encriptados do ficheiro exames.enc
with open("exames.enc", "rb") as f:
    dados_encriptados = f.read()

# 3. Desencriptar os dados
dados_originais = cipher_rsa.decrypt(dados_encriptados)

# 4. Guardar os dados recuperados num novo ficheiro CSV
with open("exames_recuperado.csv", "wb") as f:
    f.write(dados_originais)

print("✔️ Ficheiro desencriptado e guardado como 'exames_recuperado.csv'")

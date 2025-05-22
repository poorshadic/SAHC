from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP

# === Configuração ===
ficheiro_entrada = "exames.csv.enc"              # Ficheiro cifrado
ficheiro_saida = "exames_recuperado.csv"     # Ficheiro final recuperado
chave_privada_path = "keys/sgx_private.pem"  # Caminho da chave privada

# === 1. Carregar a chave privada da enclave ===
with open(chave_privada_path, "rb") as f:
    private_key = RSA.import_key(f.read())
    cipher_rsa = PKCS1_OAEP.new(private_key)

# === 2. Ler o ficheiro cifrado ===
with open(ficheiro_entrada, "rb") as f:
    key_len_bytes = f.read(2)  # primeiros 2 bytes = tamanho da chave AES cifrada
    key_len = int.from_bytes(key_len_bytes, byteorder='big')

    encrypted_aes_key = f.read(key_len)  # chave AES cifrada (com RSA)
    nonce = f.read(12)                   # nonce para AES-GCM
    tag = f.read(16)                     # tag de integridade
    ciphertext = f.read()                # resto = dados cifrados com AES

# === 3. Desencriptar a chave AES com a chave privada RSA ===
aes_key = cipher_rsa.decrypt(encrypted_aes_key)

# === 4. Usar a chave AES para desencriptar os dados ===
cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
dados_originais = cipher_aes.decrypt_and_verify(ciphertext, tag)

# === 5. Guardar os dados restaurados no ficheiro original ===
with open(ficheiro_saida, "wb") as f_out:
    f_out.write(dados_originais)

print(f"✔️ Ficheiro desencriptado com sucesso: {ficheiro_saida}")

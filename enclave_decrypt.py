"""

Old tests

"""


import os
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP

# 1. Carregar a chave privada RSA (da enclave ou simulada)
with open("keys/sgx_private.pem", "rb") as f:
    private_key = RSA.import_key(f.read())
    cipher_rsa = PKCS1_OAEP.new(private_key)

# 2. Caminho da pasta com ficheiros .enc
pasta = "caminho/para/pasta"  # Substitui pelo caminho correto

# 3. Listar todos os ficheiros encriptados
ficheiros = [f for f in os.listdir(pasta) if f.endswith(".enc")]

for ficheiro in ficheiros:
    caminho_ficheiro = os.path.join(pasta, ficheiro)

    with open(caminho_ficheiro, "rb") as f:
        # === 1. Ler o tamanho da chave AES cifrada (2 bytes)
        key_len_bytes = f.read(2)
        key_len = int.from_bytes(key_len_bytes, byteorder='big')

        # === 2. Ler a chave AES cifrada (com RSA)
        encrypted_aes_key = f.read(key_len)

        # === 3. Ler nonce (12 bytes) e tag (16 bytes)
        nonce = f.read(12)
        tag = f.read(16)

        # === 4. Ler os dados cifrados
        ciphertext = f.read()

    try:
        # === 5. Desencriptar a chave AES com a chave RSA privada
        aes_key = cipher_rsa.decrypt(encrypted_aes_key)

        # === 6. Usar AES-GCM para desencriptar os dados
        cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
        dados_originais = cipher_aes.decrypt_and_verify(ciphertext, tag)

        # === 7. Nome do ficheiro original (sem .enc)
        ficheiro_original = ficheiro[:-4]  # remove '.enc'
        caminho_saida = os.path.join(pasta, ficheiro_original)

        with open(caminho_saida, "wb") as f_out:
            f_out.write(dados_originais)

        print(f"✔️ {ficheiro} desencriptado com sucesso → {ficheiro_original}")

    except Exception as e:
        print(f"❌ Erro ao desencriptar {ficheiro}: {e}")

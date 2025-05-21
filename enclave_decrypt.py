import os
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# Pasta onde estão os ficheiros .enc
pasta = "caminho/para/pasta"  # substitui pelo caminho correto

# 1. Carregar a chave privada (da enclave ou simulada)
with open("keys/sgx_private.pem", "rb") as f:
    private_key = RSA.import_key(f.read())
    cipher_rsa = PKCS1_OAEP.new(private_key)

# 2. Listar todos os ficheiros na pasta
ficheiros = os.listdir(pasta)

# 3. Filtrar ficheiros que terminem com '.enc'
ficheiros_enc = [f for f in ficheiros if f.endswith(".enc")]

# 4. Desencriptar cada ficheiro e guardar sem o '.enc'
for ficheiro_enc in ficheiros_enc:
    caminho_ficheiro_enc = os.path.join(pasta, ficheiro_enc)

    with open(caminho_ficheiro_enc, "rb") as f:
        dados_encriptados = f.read()

    try:
        dados_originais = cipher_rsa.decrypt(dados_encriptados)
    except Exception as e:
        print(f"Erro ao desencriptar {ficheiro_enc}: {e}")
        continue

    # Remover o ".enc" do nome do ficheiro, mantendo a extensão original (.csv ou .json)
    ficheiro_descriptografado = ficheiro_enc[:-4]
    caminho_ficheiro_descriptografado = os.path.join(pasta, ficheiro_descriptografado)

    with open(caminho_ficheiro_descriptografado, "wb") as f:
        f.write(dados_originais)

    print(f"✔️ {ficheiro_enc} desencriptado e guardado como {ficheiro_descriptografado}")

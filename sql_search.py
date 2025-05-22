import json
import re
from minio import Minio
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
import os
import io

# === CONFIGURAÇÃO ===
mapa_path = "mapa.json"
pasta_resultados = "resultados_query"
chave_privada_path = "keys/sgx_private.pem"

# Ligação MinIO
client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)

# === 1. Interpretar a query (formato: select AÇÃO(DADO)) ===
def parse_query(query):
    regex = r"select\s+(\w+)\s*\(\s*(\w+)\s*\)"
    match = re.match(regex, query.strip(), re.IGNORECASE)
    if not match:
        raise ValueError("Query inválida. Use o formato: select AÇÃO(DADO)")
    operacao = match.group(1).lower()
    dado = match.group(2)
    return operacao, dado

# === 2. Desencriptar ficheiro .enc com estrutura híbrida ===
def desencriptar_ficheiro_enc(dados_encriptados, chave_privada):
    cipher_rsa = PKCS1_OAEP.new(chave_privada)

    with io.BytesIO(dados_encriptados) as f:
        key_len_bytes = f.read(2)
        key_len = int.from_bytes(key_len_bytes, byteorder='big')
        encrypted_aes_key = f.read(key_len)
        nonce = f.read(12)
        tag = f.read(16)
        ciphertext = f.read()

    aes_key = cipher_rsa.decrypt(encrypted_aes_key)
    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    dados_originais = cipher_aes.decrypt_and_verify(ciphertext, tag)
    return dados_originais

# === 3. Processar a query ===
def carregar_ficheiros_relevantes(query):
    # Extrair campo da query
    _, campo = parse_query(query)

    # Carregar mapa
    with open(mapa_path, "r", encoding="utf-8") as f:
        mapa = json.load(f)

    # Carregar chave privada da enclave
    with open(chave_privada_path, "rb") as f:
        chave_privada = RSA.import_key(f.read())

    # Criar pasta se necessário
    os.makedirs(pasta_resultados, exist_ok=True)

    # Filtrar ficheiros que contêm o campo desejado
    for entrada in mapa:
        if campo.lower() in [c.lower() for c in entrada["campos"]]:
            bucket = entrada["bucket"]
            objeto = entrada["object"]
            print(f"🔍 A carregar: {objeto} de {bucket}...")

            try:
                response = client.get_object(bucket, objeto)
                dados_encriptados = response.read()
                response.close()

                dados_desencriptados = desencriptar_ficheiro_enc(dados_encriptados, chave_privada)

                # Determinar nome do ficheiro original
                nome_final = objeto[:-4]  # remove ".enc"
                caminho_saida = os.path.join(pasta_resultados, nome_final)

                with open(caminho_saida, "wb") as f_out:
                    f_out.write(dados_desencriptados)

                print(f"✔️ Guardado: {caminho_saida}")

            except Exception as e:
                print(f"❌ Erro com {objeto}: {e}")

# === Exemplo de uso ===
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("❌ Uso: python3 carregar_ficheiros.py \"select AÇÃO(CAMPO)\"")
        exit(1)

    query = sys.argv[1]
    carregar_ficheiros_relevantes(query)








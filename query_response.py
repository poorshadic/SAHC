import re
import json
import csv
import os
import sys
import io
from minio import Minio
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP

# === CONFIGURAÇÃO ===
mapa_path = "mapa.json"
pasta_resultados = "resultados_query"
chave_privada_path = "keys/sgx_private.pem"

# === MINIO ===
client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)

# === 1. Parse da query ===
def parse_query(query):
    regex = r"select\s+(\w+)\s*\(\s*(\w+)\s*\)"
    match = re.match(regex, query.strip(), re.IGNORECASE)
    if not match:
        raise ValueError("Query inválida. Use o formato: select AÇÃO(CAMPO)")
    operacao = match.group(1).lower()
    campo = match.group(2)
    if operacao not in ("sum", "avg", "count"):
        raise ValueError(f"Ação não suportada: {operacao}")
    return operacao, campo

# === 2. Desencriptar ficheiro .enc ===
def desencriptar_ficheiro_enc(dados_encriptados, chave_privada):
    cipher_rsa = PKCS1_OAEP.new(chave_privada)
    with io.BytesIO(dados_encriptados) as f:
        key_len = int.from_bytes(f.read(2), byteorder='big')
        encrypted_aes_key = f.read(key_len)
        nonce = f.read(12)
        tag = f.read(16)
        ciphertext = f.read()
    aes_key = cipher_rsa.decrypt(encrypted_aes_key)
    cipher_aes = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    dados_originais = cipher_aes.decrypt_and_verify(ciphertext, tag)
    return dados_originais

# === 3. Obter os ficheiros relevantes e desencriptar ===
def preparar_ficheiros_para_query(campo):
    with open(mapa_path, "r", encoding="utf-8") as f:
        mapa = json.load(f)
    with open(chave_privada_path, "rb") as f:
        chave_privada = RSA.import_key(f.read())
    os.makedirs(pasta_resultados, exist_ok=True)
    caminhos = []

    for entrada in mapa:
        if campo.lower() in [c.lower() for c in entrada["campos"]]:
            bucket = entrada["bucket"]
            objeto = entrada["object"]
            print(f"📦 A obter: {objeto} de {bucket}...")

            try:
                response = client.get_object(bucket, objeto)
                dados_encriptados = response.read()
                response.close()

                dados_desencriptados = desencriptar_ficheiro_enc(dados_encriptados, chave_privada)
                nome_final = objeto[:-4]  # remove ".enc"
                caminho_saida = os.path.join(pasta_resultados, nome_final)

                with open(caminho_saida, "wb") as f_out:
                    f_out.write(dados_desencriptados)

                print(f"✅ Guardado: {caminho_saida}")
                caminhos.append(caminho_saida)

            except Exception as e:
                print(f"❌ Erro com {objeto}: {e}")

    return caminhos

# === 4. Extrair valores do campo nos ficheiros ===
def extrair_dados(caminhos, campo):
    valores = []
    for caminho in caminhos:
        if caminho.endswith(".csv"):
            with open(caminho, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                if campo not in reader.fieldnames:
                    continue
                for row in reader:
                    val = row.get(campo)
                    if val:
                        try:
                            valores.append(float(val))
                        except ValueError:
                            pass
        elif caminho.endswith(".json"):
            with open(caminho, encoding='utf-8') as jsonfile:
                try:
                    dados = json.load(jsonfile)
                    if isinstance(dados, dict):
                        dados = [dados]
                    for item in dados:
                        val = item.get(campo)
                        if val:
                            try:
                                valores.append(float(val))
                            except ValueError:
                                pass
                except Exception:
                    pass
    return valores

# === 5. Calcular resultado final ===
def calcular(valores, operacao):
    if not valores:
        return None
    if operacao == "sum":
        return sum(valores)
    elif operacao == "count":
        return len(valores)
    elif operacao == "avg":
        return sum(valores) / len(valores)
    else:
        return None

# === MAIN ===
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Uso: python3 orquestrador.py \"select AÇÃO(CAMPO)\"")
        sys.exit(1)

    query = sys.argv[1]

    try:
        operacao, campo = parse_query(query)
        ficheiros = preparar_ficheiros_para_query(campo)
        valores = extrair_dados(ficheiros, campo)
        resultado = calcular(valores, operacao)

        if resultado is None:
            print("⚠️ Nenhum dado encontrado para a query.")
        else:
            print(f"\n🎯 Resultado da query '{query}': {resultado}")
    except Exception as e:
        print(f"❌ Erro ao processar a query: {e}")

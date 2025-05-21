import re
import csv
import json
import os

def parse_query(query):
    """
    Extrai a ação e o dado da query do tipo 'select AÇÃO (DADO)'
    Exemplo: 'select SUM(colestrol)' -> ('sum', 'colestrol')
    """
    regex = r"select\s+(\w+)\s*\(\s*(\w+)\s*\)"
    match = re.match(regex, query.strip(), re.IGNORECASE)
    if not match:
        raise ValueError("Query inválida. Use o formato: select AÇÃO(DADO)")
    operacao = match.group(1).lower()
    dado = match.group(2)
    if operacao not in ("sum", "avg", "count"):
        raise ValueError(f"Ação desconhecida: {operacao}")
    return operacao, dado

def extrair_dado_csv(caminho_ficheiro, dado):
    valores = []
    with open(caminho_ficheiro, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        if dado not in reader.fieldnames:
            return valores
        for row in reader:
            val = row.get(dado)
            if val is not None and val != '':
                try:
                    valores.append(float(val))
                except ValueError:
                    pass
    return valores

def extrair_dado_json(caminho_ficheiro, dado):
    valores = []
    with open(caminho_ficheiro, encoding='utf-8') as jsonfile:
        try:
            dados = json.load(jsonfile)
            for item in dados:
                val = item.get(dado)
                if val is not None and val != '':
                    try:
                        valores.append(float(val))
                    except ValueError:
                        pass
        except Exception:
            pass
    return valores

def extrair_dado_arquivo(caminho_ficheiro, dado):
    if caminho_ficheiro.endswith(".csv"):
        return extrair_dado_csv(caminho_ficheiro, dado)
    elif caminho_ficheiro.endswith(".json"):
        return extrair_dado_json(caminho_ficheiro, dado)
    else:
        return []

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
        raise ValueError(f"Operação desconhecida: {operacao}")

def processar_query(pasta_resultados, query):
    operacao, dado = parse_query(query)
    todos_valores = []
    for ficheiro in os.listdir(pasta_resultados):
        caminho = os.path.join(pasta_resultados, ficheiro)
        valores = extrair_dado_arquivo(caminho, dado)
        todos_valores.extend(valores)
    resultado = calcular(todos_valores, operacao)
    return resultado

# --- Exemplo de uso ---

pasta_resultados = "caminho/para/pasta/desencriptados"

query1 = "select SUM(colestrol)"
query2 = "select AVG(colestrol)"
query3 = "select COUNT(colestrol)"

print(processar_query(pasta_resultados, query1))
print(processar_query(pasta_resultados, query2))
print(processar_query(pasta_resultados, query3))

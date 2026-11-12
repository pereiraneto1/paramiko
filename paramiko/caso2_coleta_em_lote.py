
import conexao
import json
import csv

# 1. Ler o inventario.json
with open('inventario.json', 'r', encoding='utf-8') as arquivo:
    dispositivos = json.load(arquivo)

# Comandos a serem executados em cada dispositivo
comandos = ["whoami", "hostname", "uname -r", "uptime -p"]

# 2. Criar e abrir o arquivo CSV para gravação
with open('inventario_coletado.csv', 'w', newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)
    
    # Cabeçalho do CSV
    writer.writerow(["host", "ip", "whoami", "hostname", "uname_r", "uptime_p", "status"])

    # 3. Iterar por cada dispositivo no inventário
    for disp in dispositivos:
        host = disp.get("host", "Desconhecido")
        ip = disp.get("ip", "N/A")
        
        print(f"\n[+] Conectando em {host} ({ip})...")
        
        try:
            # Tenta conectar ao equipamento
            cliente = conexao.conectar(disp)
            
            # Dicionário para armazenar as saídas dos comandos
            resultados = {}
            
            for cmd in comandos:
                codigo, saída, erro = conexao.executar(cliente, cmd)
                # Salva apenas o texto retornado (removendo quebras de linha extras)
                resultados[cmd] = saída.strip() if codigo == 0 else f"ERRO: {erro.strip()}"
            
            # (Opcional) Fechar conexão se a biblioteca permitir: cliente.close()
            
            # Escreve a linha de sucesso no CSV
            writer.writerow([
                host, 
                ip, 
                resultados.get("whoami", ""), 
                resultados.get("hostname", ""), 
                resultados.get("uname -r", ""), 
                resultados.get("uptime -p", ""), 
                "OK"
            ])
            print(f"[✓] Coleta em {host} realizada com sucesso!")

        except Exception as e:
            # Trata a falha, registra no CSV e continua para o próximo dispositivo
            print(f"[X] Falha ao conectar em {host}: {e}")
            writer.writerow([host, ip, "", "", "", "", f"FALHA: {e}"])

print("\n--- Coleta concluída! Arquivo 'inventario_coletado.csv' gerado. ---")


#segundo codigo (professor)
import csv
import json
import conexao

# Lendo o arquivo JSON com o inventário
with open("inventario.json", "r", encoding="utf-8") as arquivo:
    dados = json.load(arquivo)

# Lista de comandos (incluindo um comando inexistente conforme solicitado)
comandos = ["whoami", "hostname", "uname -r", "uptime -p"]

# O bloco 'with' do CSV deve envolver a escrita dos dados para o arquivo não fechar antes da hora
with open("inventario.csv", "w", newline="", encoding="utf-8") as arquivo_csv:
    escritor = csv.writer(arquivo_csv)

    # O cabeçalho precisa incluir a coluna 'nome' para alinhar com as colunas de saída
    cabecalho = ["nome"] + comandos
    escritor.writerow(cabecalho)

    for maquina in dados:
        linha = []
        print(f"Conectado em {maquina['nome']}")
        
        cliente = conexao.conectar(maquina)
        linha.append(maquina["nome"])
        
        try:
            for comando in comandos:
                codigo, saida, erro = conexao.executar(cliente, comando)
                
                # Se o comando for executado com sucesso, salva a saída; se der erro, salva a mensagem de erro
                if codigo == 0:
                    resultado = saida.strip()
                else:
                    resultado = f"ERRO ({codigo}): {erro.strip()}"
                
                linha.append(resultado)

            escritor.writerow(linha)
        finally:
            # Encerra a conexão SSH com a máquina atual
            cliente.close()


import conexao
import json

#Conectar-se ao equipamento R1 do inventário.
with open('inventario.json', 'r', encoding='utf-8') as arquivo:
    dados = json.load(arquivo)

#print(dados[0] ["host"])

cliente=conexao.conectar(dados[0])

#Executar whoami, hostname e uptime -p.

#codigo,saida,erro=conexao.executar(cliente,"whoami")
#print(f"codigo: {codigo}")
#print(f"saida: {saida}")
#print(f"erro: {erro}")
# Lista de todos os comandos exigidos no caso
comandos = [
    "whoami",
    "hostname",
    "uptime -p",
    "comando-inexistente" # Teste de comando inexistente[cite: 1]
]
# Executa e exibe o resultado para cada comando[cite: 1, 3]
for cmd in comandos:
    print(f"\n--- Executando: {cmd} ---")
    codigo, saída, erro = conexao.executar(cliente, cmd)

    print(f"codigo: {codigo}")
    print(f"saida:  {saída}")
    print(f"erro:   {erro}")
    print("=================")
#Exibir, para cada comando.
#Executar também um comando inexistente.
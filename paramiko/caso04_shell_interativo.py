import time
from conexao import conectar, executar

# Dispositivo R1 usando a chave privada configurada no Caso 3
dispositivo = {
    "nome": "R1",
    "host": "127.0.0.1",
    "porta": 22,
    "usuario": "r1",
    "chave": "/home/jose/.ssh/id_ed25519",
}


def ler(canal, pausa=0.6):
    """Aguarda e lê tudo o que o equipamento enviou no canal interativo."""
    time.sleep(pausa)
    dados = ""
    while canal.recv_ready():
        dados += canal.recv(65535).decode(errors="ignore")
        time.sleep(0.1)
    return dados


sequencia = [
    "cd /tmp",
    "pwd",
    "export AMBIENTE=PRODUCAO",
    "echo $AMBIENTE",
]

cliente = conectar(dispositivo)

try:
    print("=== 1. SESSAO INTERATIVA (invoke_shell) ===")
    canal = cliente.invoke_shell()
    ler(canal)  # Descarta o banner inicial do terminal

    for cmd in sequencia:
        canal.send(cmd + "\n")
        saida_interativa = ler(canal)
        print(saida_interativa.strip())

    canal.close()

    print("\n=== 2. UM COMANDO POR CHAMADA (exec_command) ===")
    for cmd in sequencia:
        codigo, saida, erro = executar(cliente, cmd)
        print(f"$ {cmd} -> {saida!r}")

finally:
    cliente.close()
import os
from conexao import conectar, executar

os.environ.setdefault("SSH_SENHA", "Redes@2026")

bastion = {
    "nome": "BASTION",
    "host": "127.0.0.1",
    "porta": 22,
    "usuario": "bastion",
}

alvo = {
    "nome": "R1-INTERNO",
    "host": "127.0.0.1",
    "porta": 2222,
    "usuario": "r1",
}

cliente_bastion = conectar(bastion)
cliente_alvo = None

try:
    transporte = cliente_bastion.get_transport()
    # Túnel: o bastion abre uma conexão TCP até o destino interno (porta 2222)
    canal = transporte.open_channel(
        "direct-tcpip",
        dest_addr=(alvo["host"], alvo["porta"]),
        src_addr=("127.0.0.1", 0),
    )

    # A sessão SSH com o equipamento interno trafega DENTRO do túnel
    cliente_alvo = conectar(alvo, sock=canal)

    print("whoami        :", executar(cliente_alvo, "whoami")[1])
    print("hostname      :", executar(cliente_alvo, "hostname")[1])

    # Comprovação: mostra a ligação que chegou ao servidor interno
    _, quem, _ = executar(cliente_alvo, "echo $SSH_CONNECTION")
    print("SSH_CONNECTION:", quem)
finally:
    if cliente_alvo:
        cliente_alvo.close()
    cliente_bastion.close()
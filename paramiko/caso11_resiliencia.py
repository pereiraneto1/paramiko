import os
import socket
import time
import paramiko
from conexao import conectar, executar

os.environ.setdefault("SSH_SENHA", "Redes@2026")

INVENTARIO_TESTE = [
    {"nome": "SAUDAVEL", "host": "127.0.0.1", "porta": 22, "usuario": "r1"},
    {"nome": "SENHA-ERRADA", "host": "127.0.0.1", "porta": 22, "usuario": "r1"},
    {"nome": "PORTA-FECHADA", "host": "127.0.0.1", "porta": 2299, "usuario": "r1"},
    {"nome": "SEM-RESPOSTA", "host": "10.255.255.1", "porta": 22, "usuario": "r1"},
]

TENTATIVAS = 3
ESPERA_BASE = 2  # segundos


def classificar(erro):
    """Devolve (categoria, causa provável, vale a pena repetir?)."""
    if isinstance(erro, paramiko.AuthenticationException):
        return "AUTENTICACAO", "usuario/senha/chave invalidos", False
    if isinstance(erro, paramiko.ssh_exception.NoValidConnectionsError):
        return "CONEXAO RECUSADA", "servico SSH parado ou porta bloqueada", False
    if isinstance(erro, (socket.timeout, TimeoutError)):
        return "TIMEOUT", "equipamento desligado, rota ausente ou firewall", True
    if isinstance(erro, socket.gaierror):
        return "NOME INVALIDO", "DNS ou endereco incorreto", False
    if isinstance(erro, paramiko.SSHException):
        return "ERRO SSH", f"falha de protocolo: {erro}", True
    return "INESPERADO", f"{type(erro).__name__}: {erro}", False


def conectar_com_retry(disp):
    ultima = None
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            # Simula senha incorreta apenas no item de teste SENHA-ERRADA
            if disp["nome"] == "SENHA-ERRADA":
                os.environ["SSH_SENHA"] = "SenhaErrada!999"
            else:
                os.environ["SSH_SENHA"] = "Redes@2026"

            return conectar(disp, timeout=4), tentativa
        except Exception as e:
            categoria, causa, repetir = classificar(e)
            ultima = (categoria, causa, tentativa)
            if not repetir:
                break  # não insiste em erro permanente
            if tentativa < TENTATIVAS:
                espera = ESPERA_BASE * (2 ** (tentativa - 1))  # 2s, 4s...
                print(
                    f"  [{disp['nome']}] tentativa {tentativa} falhou ({categoria}); "
                    f"nova tentativa em {espera}s"
                )
                time.sleep(espera)
    return None, ultima


if __name__ == "__main__":
    relatorio = []
    for disp in INVENTARIO_TESTE:
        cliente, info = conectar_com_retry(disp)
        if cliente:
            _, saida, _ = executar(cliente, "hostname")
            cliente.close()
            relatorio.append((disp["nome"], "OK", f"hostname={saida} (tentativa {info})"))
        else:
            categoria, causa, tentativas = info
            relatorio.append((disp["nome"], categoria, f"{causa} (tentativas: {tentativas})"))

    linhas_saida = ["\n=== RELATORIO FINAL ==="]
    for nome, estado, detalhe in relatorio:
        linhas_saida.append(f"{nome:<15} {estado:<18} {detalhe}")

    texto_final = "\n".join(linhas_saida)
    print(texto_final)

    with open("relatorio_resiliencia.txt", "w", encoding="utf-8") as f:
        f.write(texto_final.strip() + "\n")
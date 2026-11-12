import json
import re
from conexao import conectar, executar

ARQUIVO = "~/dispositivo.cfg"


def validar(chave, valor):
    """Valida a entrada para evitar injeção de comandos no shell remoto."""
    padrao = r"[A-Za-z0-9_.\-]+"
    if not (re.fullmatch(padrao, chave) and re.fullmatch(padrao, valor)):
        raise ValueError(f"Valor invalido: {chave}={valor}")


def aplicar(disp, chave, valor):
    # Garante compatibilidade caso o inventario.json use 'chave_privada' ou 'chave'
    disp_conn = dict(disp)
    if "chave_privada" in disp_conn and "chave" not in disp_conn:
        disp_conn["chave"] = disp_conn["chave_privada"]

    cliente = conectar(disp_conn)
    try:
        # (a) Cópia de segurança antes de qualquer alteração
        executar(cliente, f"cp {ARQUIVO} {ARQUIVO}.bak")

        # (b) Alteração idempotente: atualiza se a chave existe, acrescenta se não existe
        comando = (
            f"if grep -q '^{chave}=' {ARQUIVO}; then "
            f"sed -i 's/^{chave}=.*/{chave}={valor}/' {ARQUIVO}; "
            f"else echo '{chave}={valor}' >> {ARQUIVO}; fi"
        )
        codigo, _, erro = executar(cliente, comando)
        if codigo != 0:
            raise RuntimeError(f"falha ao aplicar: {erro}")

        # (c) Verificação em duas camadas: linha exata existe e é única
        _, saida, _ = executar(cliente, f"grep -c '^{chave}=' {ARQUIVO}")
        codigo_exato, _, _ = executar(cliente, f"grep -qx '{chave}={valor}' {ARQUIVO}")

        if codigo_exato != 0 or saida != "1":
            # (d) Reversão automática (rollback) se a verificação falhar
            executar(cliente, f"cp {ARQUIVO}.bak {ARQUIVO}")
            return "REVERTIDO (verificacao falhou)"

        return "APLICADO"
    finally:
        cliente.close()


if __name__ == "__main__":
    chave, valor = "ntp_server", "10.0.0.50"
    validar(chave, valor)

    with open("inventario.json", encoding="utf-8") as f:
        inventario = json.load(f)

    for disp in inventario:
        try:
            print(f"{disp['nome']}: {aplicar(disp, chave, valor)}")
        except Exception as e:
            print(f"{disp['nome']}: FALHA ({type(e).__name__}: {e})")
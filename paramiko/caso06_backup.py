import hashlib
import json
import os
from datetime import datetime
from conexao import conectar, executar


def calcular_sha256(conteudo_bytes):
    """Calcula o hash SHA-256 para verificar a integridade do ficheiro."""
    return hashlib.sha256(conteudo_bytes).hexdigest()


def fazer_backup(disp, pasta_destino):
    # Garante compatibilidade com o campo 'chave' no inventario.json
    disp_conn = dict(disp)
    if "chave_privada" in disp_conn and "chave" not in disp_conn:
        disp_conn["chave"] = disp_conn["chave_privada"]

    cliente = conectar(disp_conn)
    try:
        # 1. Obtém o hash SHA-256 no dispositivo remoto para conferência
        codigo_hash, saida_hash, _ = executar(cliente, "sha256sum ~/dispositivo.cfg")
        hash_remoto = saida_hash.split()[0] if codigo_hash == 0 and saida_hash else None

        # 2. Transfere o ficheiro via SFTP (canal seguro do Paramiko)
        sftp = cliente.open_sftp()
        try:
            # Obtém o caminho absoluto remoto do ficheiro
            _, caminho_remoto, _ = executar(cliente, "realpath ~/dispositivo.cfg")
            arquivo_local = os.path.join(pasta_destino, f"{disp['nome']}.cfg")
            sftp.get(caminho_remoto.strip(), arquivo_local)
        finally:
            sftp.close()

        # 3. Valida a integridade do ficheiro transferido localmente
        with open(arquivo_local, "rb") as f:
            conteudo = f.read()

        hash_local = calcular_sha256(conteudo)
        if hash_remoto and hash_local != hash_remoto:
            return f"FALHA DE INTEGRIDADE (hash divergente em {arquivo_local})"

        tamanho = len(conteudo)
        return f"OK -> {arquivo_local} ({tamanho} bytes | SHA-256: {hash_local[:12]}...)"
    finally:
        cliente.close()


if __name__ == "__main__":
    with open("inventario.json", encoding="utf-8") as f:
        inventario = json.load(f)

    # Cria uma pasta com carimbo de data/hora (ex: backups/2026-11-12_20-36-00)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    pasta_backup = os.path.join("backups", timestamp)
    os.makedirs(pasta_backup, exist_ok=True)

    print(f"Iniciando rotina de backup em: {pasta_backup}\n")

    for disp in inventario:
        try:
            resultado = fazer_backup(disp, pasta_backup)
            print(f"{disp['nome']}: {resultado}")
        except Exception as e:
            print(f"{disp['nome']}: FALHA ({type(e).__name__}: {e})")
import difflib
import json
from conexao import conectar

IGNORAR = ("hostname=",)  # linhas que são únicas por equipamento


def normalizar(linhas):
    return [l.strip() for l in linhas if l.strip() and not l.startswith(IGNORAR)]


def ler_remoto(disp):
    disp_conn = dict(disp)
    if "chave_privada" in disp_conn and "chave" not in disp_conn:
        disp_conn["chave"] = disp_conn["chave_privada"]

    cliente = conectar(disp_conn)
    try:
        sftp = cliente.open_sftp()
        try:
            with sftp.open("dispositivo.cfg") as arquivo:
                return arquivo.read().decode().splitlines()
        finally:
            sftp.close()
    finally:
        cliente.close()


if __name__ == "__main__":
    with open("referencia.cfg", encoding="utf-8") as f:
        referencia = normalizar(f.read().splitlines())

    with open("inventario.json", encoding="utf-8") as f:
        inventario = json.load(f)

    nao_conformes = 0
    linhas_relatorio = []

    for disp in inventario:
        try:
            atual = normalizar(ler_remoto(disp))
            diff = list(
                difflib.unified_diff(
                    sorted(referencia),
                    sorted(atual),
                    fromfile="referencia",
                    tofile=disp["nome"],
                    lineterm="",
                )
            )
            if diff:
                nao_conformes += 1
                bloco = f"[{disp['nome']}] NAO CONFORME\n" + "\n".join("  " + l for l in diff)
            else:
                bloco = f"[{disp['nome']}] CONFORME"

            print(bloco)
            linhas_relatorio.append(bloco)
        except Exception as e:
            erro_msg = f"[{disp['nome']}] FALHA ({type(e).__name__}: {e})"
            print(erro_msg)
            linhas_relatorio.append(erro_msg)

    resumo = f"\nResumo: {nao_conformes} de {len(inventario)} equipamento(s) fora de conformidade."
    print(resumo)
    linhas_relatorio.append(resumo)

    with open("relatorio_auditoria.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_relatorio) + "\n")
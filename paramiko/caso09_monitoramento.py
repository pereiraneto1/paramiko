from concurrent.futures import ThreadPoolExecutor
import json
from conexao import conectar, executar

LIMITE_DISCO = 80   # percentual
LIMITE_CARGA = 2.0  # carga média de 1 minuto


def verificar(disp):
    resultado = {
        "nome": disp["nome"],
        "disco": None,
        "carga": None,
        "sshd": None,
        "alertas": [],
        "estado": "OK",
    }

    disp_conn = dict(disp)
    if "chave_privada" in disp_conn and "chave" not in disp_conn:
        disp_conn["chave"] = disp_conn["chave_privada"]

    try:
        cliente = conectar(disp_conn)
    except Exception as e:
        resultado["estado"] = "FALHA"
        resultado["alertas"].append(f"inacessivel ({type(e).__name__})")
        return resultado

    try:
        _, disco, _ = executar(cliente, "df --output=pcent / | tail -1 | tr -d ' %'")
        _, carga, _ = executar(cliente, "cut -d' ' -f1 /proc/loadavg")
        codigo, _, _ = executar(cliente, "pgrep -x sshd > /dev/null")

        resultado["disco"] = int(disco)
        resultado["carga"] = float(carga)
        resultado["sshd"] = "ativo" if codigo == 0 else "parado"

        if resultado["disco"] > LIMITE_DISCO:
            resultado["alertas"].append(f"disco em {resultado['disco']}%")
        if resultado["carga"] > LIMITE_CARGA:
            resultado["alertas"].append(f"carga alta ({resultado['carga']})")
        if resultado["sshd"] != "ativo":
            resultado["alertas"].append("servico sshd parado")

        if resultado["alertas"]:
            resultado["estado"] = "ALERTA"
    except Exception as e:
        resultado["estado"] = "FALHA"
        resultado["alertas"].append(f"erro na coleta ({type(e).__name__})")
    finally:
        cliente.close()

    return resultado


if __name__ == "__main__":
    with open("inventario.json", encoding="utf-8") as f:
        inventario = json.load(f)

    with ThreadPoolExecutor(max_workers=10) as pool:
        resultados = list(pool.map(verificar, inventario))

    print(f"{'DISP':<6}{'ESTADO':<9}{'DISCO':<8}{'CARGA':<8}{'SSHD':<9}ALERTAS")
    print("-" * 70)
    for r in resultados:
        disco = f"{r['disco']}%" if r["disco"] is not None else "-"
        carga = str(r["carga"]) if r["carga"] is not None else "-"
        sshd = r["sshd"] or "-"
        print(f"{r['nome']:<6}{r['estado']:<9}{disco:<8}{carga:<8}{sshd:<9}{'; '.join(r['alertas'])}")
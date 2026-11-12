import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from conexao import conectar, executar


def consultar_dispositivo(disp):
    """Conecta a um dispositivo e recolhe o estado e tempo de resposta."""
    inicio = time.perf_counter()

    disp_conn = dict(disp)
    if "chave_privada" in disp_conn and "chave" not in disp_conn:
        disp_conn["chave"] = disp_conn["chave_privada"]

    cliente = conectar(disp_conn)
    try:
        # Simula uma consulta de auditoria (uptime + configuração atual)
        _, hostname, _ = executar(cliente, "hostname")
        _, uptime, _ = executar(cliente, "uptime -p")
        _, ntp, _ = executar(cliente, "grep '^ntp_server=' ~/dispositivo.cfg")

        duracao = time.perf_counter() - inicio
        return {
            "nome": disp["nome"],
            "status": "OK",
            "hostname": hostname.strip(),
            "uptime": uptime.strip(),
            "ntp": ntp.strip(),
            "tempo_s": round(duracao, 3),
        }
    finally:
        cliente.close()


def executar_sequencial(inventario):
    inicio = time.perf_counter()
    resultados = []
    for disp in inventario:
        try:
            resultados.append(consultar_dispositivo(disp))
        except Exception as e:
            resultados.append({"nome": disp["nome"], "status": f"ERRO ({e})"})
    total = time.perf_counter() - inicio
    return resultados, round(total, 3)


def executar_paralelo(inventario, max_workers=5):
    inicio = time.perf_counter()
    resultados = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {
            executor.submit(consultar_dispositivo, disp): disp["nome"]
            for disp in inventario
        }
        for futuro in as_completed(futuros):
            nome_disp = futuros[futuro]
            try:
                resultados.append(futuro.result())
            except Exception as e:
                resultados.append({"nome": nome_disp, "status": f"ERRO ({e})"})

    total = time.perf_counter() - inicio
    # Ordena pelo nome do dispositivo para manter a apresentação limpa
    resultados.sort(key=lambda x: x["nome"])
    return resultados, round(total, 3)


if __name__ == "__main__":
    with open("inventario.json", encoding="utf-8") as f:
        inventario = json.load(f)

    print("=== 1. EXECUCAO SEQUENCIAL (um por vez) ===")
    res_seq, tempo_seq = executar_sequencial(inventario)
    for r in res_seq:
        print(f"  {r}")
    print(f"Tempo total sequencial: {tempo_seq}s\n")

    print("=== 2. EXECUCAO PARALELA (ThreadPoolExecutor) ===")
    res_par, tempo_par = executar_paralelo(inventario, max_workers=3)
    for r in res_par:
        print(f"  {r}")
    print(f"Tempo total paralelo:   {tempo_par}s")

    if tempo_par > 0:
        ganho = tempo_seq / tempo_par
        print(f"\nGanho de velocidade (speedup): {ganho:.2f}x mais rapido")
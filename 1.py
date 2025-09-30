#!/usr/bin/env python3
import csv
import subprocess
import socket
import sys
from datetime import datetime
import requests

TARGETS = ["8.8.8.8", "bing.com", "microsoft.com"]
CSV_FILE = "results_legivel.csv"

def stamp():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def traduzir(test, result, target, info=""):
    if test == "ping":
        if result == "OK":
            return f"Ping para {target}: Funcionou normalmente."
        else:
            return f"Ping para {target}: Falhou (tempo limite ou inacessível)."
    elif test == "dns":
        if result == "OK":
            return f"DNS para {target}: Resolvido com sucesso → {info}."
        else:
            return f"DNS para {target}: Falhou ({info})."
    elif test == "http":
        if result == "OK":
            return f"Acesso HTTP a {target}: Funcionou (resposta {info[:30]}...)."
        else:
            return f"Acesso HTTP a {target}: Falhou ({info})."
    return f"{test} em {target}: {result}"

def ping(host, count=2):
    try:
        out = subprocess.run(
            ["ping", "-c", str(count), host] if sys.platform != "win32" else ["ping", "-n", str(count), host],
            capture_output=True, text=True, timeout=8
        )
        return out.returncode == 0, ""
    except Exception as e:
        return False, str(e)

def dns_lookup(host):
    try:
        ips = socket.gethostbyname_ex(host)[2]
        return True, ",".join(ips)
    except Exception as e:
        return False, str(e)

def http_check(url):
    try:
        r = requests.get(url, timeout=8, allow_redirects=True, headers={"User-Agent":"support-check/1.0"})
        ok = r.status_code == 200
        snippet = (r.text[:60].replace("\n"," ").replace("\r"," "))
        return ok, f"{r.status_code} {snippet}"
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    # cria arquivo CSV com cabeçalho
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Data/Hora","Alvo","Teste","Resultado Técnico","Tradução Legível"])

    for t in TARGETS:
        ts = stamp()

        ok, info = ping(t)
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([ts, t, "ping", "OK" if ok else "FAIL", traduzir("ping","OK" if ok else "FAIL", t, info)])

        if not t.replace(".", "").isdigit():
            ok, info = dns_lookup(t)
            with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([ts, t, "dns", "OK" if ok else "FAIL", traduzir("dns","OK" if ok else "FAIL", t, info)])

            url = "https://" + t if not t.startswith("http") else t
            ok, info = http_check(url)
            with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([ts, url, "http", "OK" if ok else "FAIL", traduzir("http","OK" if ok else "FAIL", t, info)])

    print("✅ Concluído. Resultados em", CSV_FILE)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=========================================================
  ARSENAL DE AUDITORÍA Y ANÁLISIS  -  Termux Edition
  Uso EXCLUSIVO en redes/dispositivos propios o con
  autorización por escrito. El uso no autorizado es delito.
=========================================================
"""

import os
import sys
import json
import shutil
import logging
import hashlib
import ipaddress
import subprocess
from datetime import datetime
from pathlib import Path

# ============ CONFIG ============
VERSION = "1.1"
AUTOR   = "MARTIN"
BASE    = Path.home() / "arsenal"
LOGS    = BASE / "logs"
OUTS    = BASE / "salidas"
CONF    = BASE / "config"
REPO    = BASE / "repo"
for d in (LOGS, OUTS, CONF, REPO):
    d.mkdir(parents=True, exist_ok=True)

SESSION  = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOGS / f"auditoria_{SESSION}.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# ============ COLORES ============
G="\033[92m"; R="\033[91m"; Y="\033[93m"; B="\033[94m"
C="\033[96m"; M="\033[95m"; W="\033[97m"
DIM="\033[2m"; BOLD="\033[1m"; RESET="\033[0m"

# ============ UTILIDADES ============
def log(msg, level="info"):
    getattr(logging, level)(str(msg))

def clear():
    os.system("clear")

def pausa():
    input(f"\n{DIM}Presioná ENTER para volver al menú...{RESET}")

def banner(titulo=""):
    clear()
    print(f"{C}{'='*55}{RESET}")
    print(f"{BOLD}{W}   ARSENAL DE AUDITORÍA  {DIM}v{VERSION}{RESET}")
    print(f"{C}{'='*55}{RESET}")
    if titulo:
        print(f"{M}  >> {titulo}{RESET}")
        print(f"{C}{'-'*55}{RESET}")

def check_tool(name):
    return shutil.which(name) is not None

def pedir_ip():
    while True:
        s = input(f"{C}IP / rango (ej 192.168.1.1 o 192.168.1.0/24): {RESET}").strip()
        try:
            if "/" in s:
                ipaddress.ip_network(s, strict=False)
            else:
                ipaddress.ip_address(s)
            return s
        except ValueError:
            print(f"{R}[!] Formato inválido.{RESET}")

def guardar(nombre, contenido):
    p = OUTS / nombre
    p.write_text(contenido, encoding="utf-8")
    log(f"Guardado: {p}")
    return p

def run(cmd, guardar_como=None, timeout=300, cwd=None):
    """Ejecuta un comando. Si cwd no es None, corre en ese directorio."""
    log(f"CMD: {' '.join(cmd)}")
    if not check_tool(cmd[0]):
        msg = f"[!] '{cmd[0]}' no está instalado. Instalalo con: pkg install {cmd[0]}"
        log(msg, "warning")
        return msg
    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=cwd
        )
        salida = res.stdout + res.stderr
        if guardar_como:
            guardar(guardar_como, salida)
        return salida if salida.strip() else "[i] Sin salida."
    except subprocess.TimeoutExpired:
        log(f"Timeout: {cmd}", "error")
        return "[!] Timeout alcanzado."
    except Exception as e:
        log(f"Error: {e}", "error")
        return f"[!] Error: {e}"

def pedir_confirmacion(msg):
    r = input(f"{Y}{msg} (s/n): {RESET}").strip().lower()
    return r == "s"

# ============ AVISO DE AUTORIZACIÓN ============
def aviso_autorizacion():
    clear()
    print(f"{R}{BOLD}")
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║   AVISO DE USO RESPONSABLE                       ║")
    print("  ╠══════════════════════════════════════════════════╣")
    print("  ║  Esta herramienta es para auditoría en redes     ║")
    print("  ║  PROPIAS o con AUTORIZACIÓN POR ESCRITO.         ║")
    print("  ║  Usarla contra redes ajenas es DELITO.           ║")
    print("  ║  (Ley 26.388 art. 153 bis - Argentina)           ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print(f"{RESET}")
    log("Aviso de autorización mostrado.")
    r = input(f"{C}¿Tenés autorización para auditar la red objetivo? (s/n): {RESET}").strip().lower()
    if r != "s":
        print(f"{R}Cerrando. Usá esto solo con permiso.{RESET}")
        log("Usuario rechazó autorización. Saliendo.", "warning")
        sys.exit(0)
    scope = input(f"{C}Describí brevemente el scope: {RESET}").strip()
    log(f"Scope declarado: {scope}")
    (CONF / f"scope_{SESSION}.txt").write_text(
        f"Sesión: {SESSION}\nScope: {scope}\nAutorizado por usuario: sí\n",
        encoding="utf-8"
    )

# ============ SUBMENÚS ============
def menu_escaneo():
    while True:
        banner("ESCANEO DE RED")
        print(f"  {C}[1]{RESET} Ping a un host")
        print(f"  {C}[2]{RESET} Nmap rápido (puertos comunes)")
        print(f"  {C}[3]{RESET} Nmap completo (-p-)")
        print(f"  {C}[4]{RESET} Nmap detección de versiones (-sV)")
        print(f"  {C}[5]{RESET} Descubrir hosts en la red (-sn)")
        print(f"  {C}[6]{RESET} Análisis ARP local")
        print(f"  {C}[0]{RESET} Volver")
        op = input(f"\n{C}Opción: {RESET}").strip()

        if op == "1":
            ip = pedir_ip()
            print(run(["ping", "-c", "4", ip], f"ping_{ip}_{SESSION}.txt"))
        elif op == "2":
            ip = pedir_ip()
            print(run(["nmap", "-F", ip], f"nmap_fast_{ip}_{SESSION}.txt"))
        elif op == "3":
            ip = pedir_ip()
            if pedir_confirmacion("Esto tarda varios minutos. ¿Continuar?"):
                print(run(["nmap", "-p-", ip], f"nmap_full_{ip}_{SESSION}.txt", timeout=1800))
        elif op == "4":
            ip = pedir_ip()
            print(run(["nmap", "-sV", ip], f"nmap_sv_{ip}_{SESSION}.txt", timeout=900))
        elif op == "5":
            ip = pedir_ip()
            print(run(["nmap", "-sn", ip], f"nmap_sn_{SESSION}.txt"))
        elif op == "6":
            print(run(["arp", "-a"], f"arp_{SESSION}.txt"))
        elif op == "0":
            return
        else:
            print(f"{R}Opción inválida.{RESET}")
            continue
        pausa()

def menu_web():
    while True:
        banner("ANÁLISIS WEB / SSL")
        print(f"  {C}[1]{RESET} Headers HTTP (curl -I)")
        print(f"  {C}[2]{RESET} Certificado SSL/TLS (openssl)")
        print(f"  {C}[3]{RESET} Whois de dominio/IP")
        print(f"  {C}[4]{RESET} DNS (dig / nslookup)")
        print(f"  {C}[5]{RESET} Traceroute")
        print(f"  {C}[0]{RESET} Volver")
        op = input(f"\n{C}Opción: {RESET}").strip()

        if op == "1":
            url = input(f"{C}URL (ej https://ejemplo.com): {RESET}").strip()
            print(run(["curl", "-s", "-I", url], f"headers_{SESSION}.txt"))
        elif op == "2":
            host = input(f"{C}Host (ej ejemplo.com): {RESET}").strip()
            print(run(
                ["openssl", "s_client", "-connect", f"{host}:443", "-servername", host],
                f"ssl_{host}_{SESSION}.txt", timeout=30
            ))
        elif op == "3":
            obj = input(f"{C}Dominio o IP: {RESET}").strip()
            print(run(["whois", obj], f"whois_{obj}_{SESSION}.txt"))
        elif op == "4":
            obj = input(f"{C}Dominio: {RESET}").strip()
            if check_tool("dig"):
                print(run(["dig", obj], f"dns_{obj}_{SESSION}.txt"))
            else:
                print(run(["nslookup", obj], f"dns_{obj}_{SESSION}.txt"))
        elif op == "5":
            obj = input(f"{C}Host/IP: {RESET}").strip()
            print(run(["traceroute", obj], f"traceroute_{obj}_{SESSION}.txt"))
        elif op == "0":
            return
        else:
            print(f"{R}Opción inválida.{RESET}")
            continue
        pausa()

def menu_cripto():
    while True:
        banner("CRIPTOGRAFÍA / INTEGRIDAD")
        print(f"  {C}[1]{RESET} MD5 de archivo")
        print(f"  {C}[2]{RESET} SHA256 de archivo")
        print(f"  {C}[3]{RESET} Verificar hash de binario")
        print(f"  {C}[4]{RESET} Generar hash de texto")
        print(f"  {C}[0]{RESET} Volver")
        op = input(f"\n{C}Opción: {RESET}").strip()

        if op == "1":
            f = input(f"{C}Ruta del archivo: {RESET}").strip()
            print(run(["md5sum", f], f"md5_{SESSION}.txt"))
        elif op == "2":
            f = input(f"{C}Ruta del archivo: {RESET}").strip()
            print(run(["sha256sum", f], f"sha256_{SESSION}.txt"))
        elif op == "3":
            f = input(f"{C}Ruta del binario: {RESET}").strip()
            h = input(f"{C}Hash esperado: {RESET}").strip().lower()
            out = run(["sha256sum", f])
            real = out.split()[0] if out and " " in out else ""
            print(f"{G}OK{RESET}" if real == h else f"{R}NO COINCIDE{RESET}")
        elif op == "4":
            txt = input(f"{C}Texto: {RESET}").strip()
            print(f"MD5:    {hashlib.md5(txt.encode()).hexdigest()}")
            print(f"SHA256: {hashlib.sha256(txt.encode()).hexdigest()}")
        elif op == "0":
            return
        else:
            print(f"{R}Opción inválida.{RESET}")
            continue
        pausa()

def menu_rtsp():
    banner("MONITOREO RTSP (cámaras IP)")
    print(f"{Y}[!] Solo cámaras propias o con autorización.{RESET}\n")
    ip = pedir_ip()
    print(f"\n{DIM}Verificando puerto 554...{RESET}\n")
    resultado = f"RTSP check sobre {ip}\n"
    out = run(["nc", "-z", "-w", "2", ip, "554"], timeout=10)
    resultado += f"Puerto 554 -> {out}\n"
    if "succeeded" in out.lower() or "open" in out.lower():
        print(f"{G}[+] Puerto 554 abierto. Verificá con cliente RTSP autorizado.{RESET}")
    else:
        print(f"{Y}[i] Puerto 554 cerrado o filtrado.{RESET}")
    guardar(f"rtsp_{ip}_{SESSION}.txt", resultado)
    pausa()

def menu_sockets():
    while True:
        banner("SOCKETS / NETCAT")
        print(f"  {C}[1]{RESET} Escuchar en un puerto local")
        print(f"  {C}[2]{RESET} Conectar a host:puerto")
        print(f"  {C}[3]{RESET} Ver puertos en escucha (ss/netstat)")
        print(f"  {C}[0]{RESET} Volver")
        op = input(f"\n{C}Opción: {RESET}").strip()

        if op == "1":
            p = input(f"{C}Puerto: {RESET}").strip()
            if pedir_confirmacion("¿Tenés autorización para recibir conexiones?"):
                print(run(["nc", "-lvp", p], f"nc_listen_{p}_{SESSION}.txt"))
        elif op == "2":
            ip = pedir_ip()
            p = input(f"{C}Puerto: {RESET}").strip()
            print(run(["nc", "-zv", ip, p], f"nc_{ip}_{p}_{SESSION}.txt", timeout=10))
        elif op == "3":
            if check_tool("ss"):
                print(run(["ss", "-tuln"], f"sockets_{SESSION}.txt"))
            else:
                print(run(["netstat", "-tuln"], f"sockets_{SESSION}.txt"))
        elif op == "0":
            return
        else:
            print(f"{R}Opción inválida.{RESET}")
            continue
        pausa()

def menu_wifi():
    banner("AUDITORÍA WI-FI")
    print(f"{Y}[!] En Termux sin root solo info de interfaces.{RESET}")
    print(f"{Y}    Modo monitor real requiere root + adaptador externo.{RESET}\n")
    salida = ""
    if check_tool("termux-wifi-connectioninfo"):
        salida += run(["termux-wifi-connectioninfo"]) + "\n"
    if check_tool("ifconfig"):
        salida += run(["ifconfig"])
    elif check_tool("ip"):
        salida += run(["ip", "addr"])
    print(salida)
    guardar(f"wifi_{SESSION}.txt", salida)
    pausa()

def menu_wordlists():
    while True:
        banner("GESTIÓN DE WORDLISTS")
        print(f"  {C}[1]{RESET} Listar wordlists disponibles")
        print(f"  {C}[2]{RESET} Crear wordlist básica")
        print(f"  {C}[0]{RESET} Volver")
        op = input(f"\n{C}Opción: {RESET}").strip()
        wl_dir = BASE / "wordlists"
        wl_dir.mkdir(exist_ok=True)

        if op == "1":
            archivos = list(wl_dir.iterdir())
            if not archivos:
                print(f"{DIM}No hay wordlists todavía.{RESET}")
            for f in archivos:
                print(f"  - {f.name}")
        elif op == "2":
            print(f"{Y}[!] Uso solo en labs autorizados.{RESET}")
            base = input(f"{C}Palabra base (ej 'admin'): {RESET}").strip()
            anio = input(f"{C}Año base (ej 2024): {RESET}").strip()
            salida = []
            for s in ["", "123", "1234", "!", "@", "2024", "2025"]:
                salida.append(f"{base}{s}")
                salida.append(f"{base.capitalize()}{s}")
            if anio.isdigit():
                for s in range(int(anio)-2, int(anio)+3):
                    salida.append(f"{base}{s}")
            p = wl_dir / f"wl_{base}_{SESSION}.txt"
            p.write_text("\n".join(salida), encoding="utf-8")
            print(f"{G}[+] Guardada en {p} ({len(salida)} entradas){RESET}")
        elif op == "0":
            return
        else:
            print(f"{R}Opción inválida.{RESET}")
            continue
        pausa()

def menu_ia():
    banner("CHAT IA")
    key_file = CONF / "ia_api_key.txt"
    if not key_file.exists():
        print(f"{Y}No hay API key configurada.{RESET}")
        print(f"{DIM}Se usa Groq (free tier). Obtené una en console.groq.com{RESET}")
        key = input(f"{C}Pegá tu API key: {RESET}").strip()
        if not key:
            pausa(); return
        key_file.write_text(key, encoding="utf-8")
        os.chmod(key_file, 0o600)
    key = key_file.read_text(encoding="utf-8").strip()
    modelo = modelo = "openai/gpt-oss-20b"
    print(f"{DIM}Modelo: {modelo} | escribí 'salir' para volver{RESET}\n")

    historial = [{
        "role": "system",
        "content": ("Sos un asistente de ciberseguridad para un laboratorio "
                    "autorizado. Respondés en español, breve y técnico. "
                    "No das instrucciones para atacar sistemas sin autorización.")
    }]

    while True:
        try:
            pregunta = input(f"{C}Vos> {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if pregunta.lower() in ("salir", "exit", "quit", ""):
            break
        historial.append({"role": "user", "content": pregunta})
        log(f"IA pregunta: {pregunta}")
        payload = {"model": modelo, "messages": historial}
        cmd = [
            "curl", "-s", "https://api.groq.com/openai/v1/chat/completions",
            "-H", f"Authorization: Bearer {key}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if not res.stdout.strip():
                print(f"{R}[!] Sin respuesta de Groq. ¿Hay internet?{RESET}")
                historial.pop()
                continue
            data = json.loads(res.stdout)
            if "error" in data:
                err = data["error"].get("message", "desconocido")
                print(f"{R}[!] Error de Groq: {err}{RESET}")
                historial.pop()
                continue
            if "choices" not in data:
                print(f"{R}[!] Respuesta inesperada de Groq:{RESET}")
                print(f"{DIM}{res.stdout[:400]}{RESET}")
                historial.pop()
                continue
            respuesta = data["choices"][0]["message"]["content"]
            historial.append({"role": "assistant", "content": respuesta})
            print(f"\n{G}IA>{RESET} {respuesta}\n")
            log(f"IA respuesta: {respuesta[:300]}")
        except subprocess.TimeoutExpired:
            print(f"{R}[!] Timeout. La IA tardó demasiado.{RESET}")
            historial.pop()
        except json.JSONDecodeError:
            print(f"{R}[!] Groq devolvió algo que no es JSON:{RESET}")
            print(f"{DIM}{res.stdout[:400]}{RESET}")
            historial.pop()
        except Exception as e:
            print(f"{R}[!] Error: {e}{RESET}")
            log(f"Error IA: {e}", "error")
            historial.pop()

# ============ GITHUB SYNC ============
def menu_github():
    TOKEN_FILE = CONF / "github_token.txt"
    URL_FILE   = CONF / "github_url.txt"

    while True:
        banner("SINCRONIZACIÓN CON GITHUB")
        print(f"  {C}[1]{RESET} Configurar repo (URL + token)")
        print(f"  {C}[2]{RESET} Inicializar repo local (primera vez)")
        print(f"  {C}[3]{RESET} Ver estado actual")
        print(f"  {C}[4]{RESET} Subir cambios (commit + push)")
        print(f"  {C}[5]{RESET} Bajar cambios (pull)")
        print(f"  {C}[6]{RESET} Ver historial de commits")
        print(f"  {C}[7]{RESET} Clonar repo existente")
        print(f"  {C}[0]{RESET} Volver")
        op = input(f"\n{C}Opción: {RESET}").strip()

        if op == "1":
            print(f"{DIM}Ej URL: https://github.com/tuuser/arsenal.git{RESET}")
            url = input(f"{C}URL del repo: {RESET}").strip()
            print(f"{DIM}Token: github.com/settings/tokens -> scope 'repo'{RESET}")
            token = input(f"{C}Token (ENTER para mantener el actual): {RESET}").strip()
            if url:
                URL_FILE.write_text(url, encoding="utf-8")
            if token:
                TOKEN_FILE.write_text(token, encoding="utf-8")
                os.chmod(TOKEN_FILE, 0o600)
            print(f"{G}[+] Configuración guardada.{RESET}")
            log("GitHub configurado.")

        elif op == "2":
            if not URL_FILE.exists():
                print(f"{R}[!] Primero configurá el repo (opción 1).{RESET}")
                pausa(); continue
            src = Path(__file__).resolve()
            shutil.copy(src, REPO / "arsenal.py")
            (REPO / "README.md").write_text(
                "# Arsenal de Auditoría\n\n"
                "Herramienta de auditoría para uso en redes propias o autorizadas.\n\n"
                "## Instalación en Termux\n"
                "```bash\npkg install python nmap netcat-openbsd curl openssl git\npython arsenal.py\n```\n",
                encoding="utf-8"
            )
            if not (REPO / ".git").exists():
                run(["git", "init"], cwd=str(REPO))
                run(["git", "branch", "-M", "main"], cwd=str(REPO))
            print(f"{G}[+] Repo inicializado en {REPO}{RESET}")
            log("Repo git inicializado.")

        elif op == "3":
            print(run(["git", "status"], cwd=str(REPO)))

        elif op == "4":
            if not TOKEN_FILE.exists() or not URL_FILE.exists():
                print(f"{R}[!] Configurá el repo primero (opción 1).{RESET}")
                pausa(); continue
            if not (REPO / ".git").exists():
                print(f"{R}[!] Inicializá el repo primero (opción 2).{RESET}")
                pausa(); continue
            src = Path(__file__).resolve()
            shutil.copy(src, REPO / "arsenal.py")
            msg = input(f"{C}Mensaje del commit: {RESET}").strip()
            if not msg:
                msg = f"update {datetime.now():%Y-%m-%d %H:%M}"
            url = URL_FILE.read_text().strip()
            token = TOKEN_FILE.read_text().strip()
            # URL autenticada solo en memoria
            if url.startswith("https://") and token:
                auth_url = url.replace("https://", f"https://{token}@", 1)
            else:
                auth_url = url
            run(["git", "add", "."], cwd=str(REPO))
            run(["git", "commit", "-m", msg], cwd=str(REPO))
            # limpiar remoto previo y setear el autenticado
            remotos = run(["git", "remote"], cwd=str(REPO))
            if "origin" in remotos:
                run(["git", "remote", "remove", "origin"], cwd=str(REPO))
            run(["git", "remote", "add", "origin", auth_url], cwd=str(REPO))
            print(run(["git", "push", "-u", "origin", "main"], timeout=180, cwd=str(REPO)))
            log(f"Push realizado: {msg}")

        elif op == "5":
            if not (REPO / ".git").exists():
                print(f"{R}[!] No hay repo local. Usá opción 2 o 7.{RESET}")
                pausa(); continue
            out = run(["git", "pull", "origin", "main"], timeout=180, cwd=str(REPO))
            print(out)
            if "Already up to date" in out or "Ya está actualizado" in out:
                print(f"{DIM}Sin cambios remotos.{RESET}")
            else:
                if (REPO / "arsenal.py").exists():
                    shutil.copy(REPO / "arsenal.py", Path.home() / "arsenal.py")
                    print(f"{G}[+] arsenal.py actualizado en ~/arsenal.py{RESET}")
            log("Pull realizado.")

        elif op == "6":
            print(run(["git", "log", "--oneline", "-20"], cwd=str(REPO)))

        elif op == "7":
            if not URL_FILE.exists():
                print(f"{R}[!] Configurá la URL primero (opción 1).{RESET}")
                pausa(); continue
            url = URL_FILE.read_text().strip()
            if (REPO / ".git").exists():
                print(f"{Y}[!] Ya hay un repo en {REPO}. Borralo si querés clonar.{RESET}")
            else:
                print(run(["git", "clone", url, "repo"], timeout=300, cwd=str(BASE)))

        elif op == "0":
            return
        else:
            print(f"{R}Opción inválida.{RESET}")
            continue
        pausa()

# ============ REPORTES / LOGS ============
def generar_reporte():
    banner("REPORTE DE SESIÓN")
    if not LOG_FILE.exists():
        print(f"{R}No hay logs de esta sesión.{RESET}")
        pausa(); return
    contenido = LOG_FILE.read_text(encoding="utf-8")
    lineas = [l for l in contenido.splitlines() if "CMD:" in l or "Aviso" in l or "Scope" in l]
    salidas = list(OUTS.glob(f"*{SESSION}*.txt"))
    reporte = [
        "# Reporte de Auditoría",
        "",
        f"- **Sesión:** {SESSION}",
        f"- **Autor:** {AUTOR}",
        f"- **Herramienta:** Arsenal v{VERSION}",
        f"- **Fecha:** {datetime.now():%Y-%m-%d %H:%M}",
        "",
        "## Comandos ejecutados",
        "",
    ]
    for l in lineas:
        reporte.append(f"- `{l}`")
    reporte += ["", "## Archivos de salida", ""]
    for s in salidas:
        reporte.append(f"- `{s.name}` ({s.stat().st_size} bytes)")
    reporte += [
        "",
        "## Aviso",
        "",
        "Este reporte fue generado en un entorno autorizado.",
    ]
    p = OUTS / f"reporte_{SESSION}.md"
    p.write_text("\n".join(reporte), encoding="utf-8")
    print(f"{G}[+] Reporte generado: {p}{RESET}")
    log(f"Reporte generado: {p}")
    pausa()

def ver_logs():
    banner("HISTORIAL DE LOGS")
    archivos = sorted(LOGS.glob("auditoria_*.log"), reverse=True)[:10]
    if not archivos:
        print(f"{DIM}No hay logs todavía.{RESET}")
        pausa(); return
    for i, f in enumerate(archivos, 1):
        print(f"  {C}[{i}]{RESET} {f.name}  {DIM}({f.stat().st_size} bytes){RESET}")
    op = input(f"\n{C}Ver cuál (número) o ENTER para volver: {RESET}").strip()
    if op.isdigit() and 1 <= int(op) <= len(archivos):
        print(archivos[int(op)-1].read_text(encoding="utf-8"))
    pausa()

# ============ MENÚ PRINCIPAL ============
def main():
    aviso_autorizacion()
    while True:
        banner()
        print(f"  {C}[1]{RESET}  {W}Escaneo de Red{RESET}       {DIM}-> Puertos, hosts, ARP{RESET}")
        print(f"  {C}[2]{RESET}  {W}Análisis Web / SSL{RESET}   {DIM}-> Headers, SSL, whois, DNS{RESET}")
        print(f"  {C}[3]{RESET}  {W}Criptografía{RESET}         {DIM}-> Hashes e integridad{RESET}")
        print(f"  {C}[4]{RESET}  {W}Monitoreo RTSP{RESET}       {DIM}-> Cámaras IP (autorizado){RESET}")
        print(f"  {C}[5]{RESET}  {W}Sockets / Netcat{RESET}     {DIM}-> Escucha y captura local{RESET}")
        print(f"  {C}[6]{RESET}  {W}Auditoría Wi-Fi{RESET}      {DIM}-> Interfaces inalámbricas{RESET}")
        print(f"  {C}[7]{RESET}  {W}Wordlists{RESET}            {DIM}-> Gestión de diccionarios{RESET}")
        print(f"  {C}[8]{RESET}  {W}Chat IA{RESET}              {DIM}-> Asistente de seguridad{RESET}")
        print(f"  {C}[9]{RESET}  {W}GitHub Sync{RESET}          {DIM}-> Subir/bajar a VS Code{RESET}")
        print(f"  {C}[10]{RESET} {W}Generar Reporte{RESET}      {DIM}-> Exportar sesión a .md{RESET}")
        print(f"  {C}[11]{RESET} {W}Ver Historial de Logs{RESET} {DIM}-> Últimas sesiones{RESET}")
        print(f"  {C}[0]{RESET}  {W}Salir{RESET}")
        print(f"{C}{'-'*55}{RESET}")
        op = input(f"{C}Seleccioná opción [0-11]: {RESET}").strip()
        log(f"Menú principal: opción {op}")

        if   op == "1":  menu_escaneo()
        elif op == "2":  menu_web()
        elif op == "3":  menu_cripto()
        elif op == "4":  menu_rtsp()
        elif op == "5":  menu_sockets()
        elif op == "6":  menu_wifi()
        elif op == "7":  menu_wordlists()
        elif op == "8":  menu_ia()
        elif op == "9":  menu_github()
        elif op == "10": generar_reporte()
        elif op == "11": ver_logs()
        elif op == "0":
            log("Sesión finalizada por el usuario.")
            print(f"\n{G}Sesión guardada en {LOG_FILE}{RESET}")
            print(f"{DIM}Logs:   {LOGS}{RESET}")
            print(f"{DIM}Salidas: {OUTS}{RESET}")
            break
        else:
            print(f"{R}Opción inválida.{RESET}")
            pausa()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Y}Interrumpido. Logs en {LOG_FILE}{RESET}")
        sys.exit(0)

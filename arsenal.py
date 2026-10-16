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
import builtins
from datetime import datetime
from pathlib import Path

# ============ TERMIOS (para Ctrl+X) ============
try:
    import tty
    import termios
    TIENE_TERMIOS = True
except ImportError:
    TIENE_TERMIOS = False

# ============ INPUT RAW CON CTRL+X ============
_input_original = builtins.input
PALABRAS_ESCAPE = ("0", "atras", "atrás", "volver", "back", "b", "q", "salir", "exit")

def input_raw(prompt=""):
    """Lee input carácter a carácter. Ctrl+X sale del script."""
    sys.stdout.write(prompt)
    sys.stdout.flush()

    if not TIENE_TERMIOS or not sys.stdin.isatty():
        return _input_original()

    fd = sys.stdin.fileno()
    try:
        old_attrs = termios.tcgetattr(fd)
    except Exception:
        return _input_original()

    buffer = []
    salir = False
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if not ch:
                raise EOFError
            if ch == '\x18':          # Ctrl+X -> salir
                salir = True
                break
            elif ch == '\x03':        # Ctrl+C -> KeyboardInterrupt
                sys.stdout.write('\n')
                sys.stdout.flush()
                raise KeyboardInterrupt
            elif ch == '\x04':        # Ctrl+D
                if not buffer:
                    raise EOFError
            elif ch in ('\r', '\n'):  # Enter
                sys.stdout.write('\n')
                sys.stdout.flush()
                break
            elif ch in ('\x7f', '\b'):  # Backspace
                if buffer:
                    buffer.pop()
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            elif ch == '\x1b':        # Secuencia de flecha / ESC
                sys.stdin.read(2)
            elif ch >= ' ':           # Carácter normal
                buffer.append(ch)
                sys.stdout.write(ch)
                sys.stdout.flush()
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)
        except Exception:
            pass

    if salir:
        print(f"\n{Y}Saliendo del script...{RESET}")
        try:
            log("Ctrl+X: salida manual")
        except Exception:
            pass
        sys.exit(0)

    return ''.join(buffer)

def _input_seguro(prompt=""):
    r = input_raw(prompt)
    if r.strip().lower() in PALABRAS_ESCAPE:
        raise KeyboardInterrupt
    return r

def _input_menu(prompt=""):
    """Para el menú principal: solo 0/salir/exit/q cierran."""
    r = input_raw(prompt)
    if r.strip().lower() in ("0", "salir", "exit", "q"):
        raise KeyboardInterrupt
    return r

builtins.input = _input_seguro

# ============ CONFIG ============
VERSION = "1.9"
AUTOR   = "salo-9090"
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

# ============ BASE DE FABRICANTES (OUI) ============
OUI_DB = {
    "00:1a:2b": "Cisco", "00:0c:29": "VMware", "00:50:56": "VMware",
    "b0:be:76": "TP-Link", "7c:8b:ca": "TP-Link", "a4:2b:b0": "TP-Link",
    "f4:f2:6d": "TP-Link", "c4:e9:84": "TP-Link", "50:c7:bf": "TP-Link",
    "14:cc:20": "TP-Link", "9c:a2:f4": "TP-Link",
    "84:16:f9": "Huawei", "00:e0:fc": "Huawei", "04:bd:70": "Huawei",
    "8c:34:fd": "Huawei", "5c:7d:5e": "Huawei",
    "00:1f:9f": "Sagemcom", "2c:39:96": "Sagemcom", "44:32:c8": "Sagemcom",
    "d8:47:32": "Technicolor", "38:43:7d": "Technicolor",
    "d4:6e:5c": "Huawei", "20:0d:b0": "Arris", "84:26:15": "Arris",
    "00:1b:63": "Apple", "00:1f:f3": "Apple", "00:23:df": "Apple",
    "3c:07:54": "Apple", "40:6c:8f": "Apple", "48:60:bc": "Apple",
    "68:a8:6d": "Apple", "88:e9:fe": "Apple", "a4:c3:61": "Apple",
    "bc:52:b7": "Apple", "f0:18:98": "Apple", "dc:a9:04": "Apple",
    "ac:bc:32": "Apple", "d0:81:7a": "Apple", "04:0c:ce": "Apple",
    "00:12:fb": "Samsung", "00:15:99": "Samsung", "00:16:32": "Samsung",
    "28:39:5e": "Samsung", "38:aa:3c": "Samsung", "5c:0a:5b": "Samsung",
    "78:1f:db": "Samsung", "8c:71:f8": "Samsung", "ac:5f:3e": "Samsung",
    "e8:50:8b": "Samsung", "f4:0e:22": "Samsung", "cc:07:ab": "Samsung",
    "28:6c:07": "Xiaomi", "34:80:b3": "Xiaomi", "50:64:2b": "Xiaomi",
    "64:b4:73": "Xiaomi", "78:11:dc": "Xiaomi", "8c:be:be": "Xiaomi",
    "9c:99:a0": "Xiaomi", "ac:c1:ee": "Xiaomi", "f0:b4:29": "Xiaomi",
    "fc:64:ba": "Xiaomi", "04:cf:8c": "Xiaomi", "68:ab:bc": "Xiaomi",
    "44:19:b6": "Hikvision", "bc:ad:28": "Hikvision", "c0:56:e3": "Hikvision",
    "4c:bd:8f": "Hikvision", "54:c4:15": "Hikvision", "e0:ca:3c": "Hikvision",
    "3c:ef:8c": "Dahua", "90:02:a9": "Dahua", "4c:11:bf": "Dahua",
    "e0:50:8b": "Dahua", "08:57:00": "Dahua",
    "00:62:6e": "Xiongmai", "00:12:12": "Xiongmai", "34:ce:00": "Xiongmai",
    "8c:e7:48": "Reolink", "ec:71:db": "Reolink", "d8:af:f1": "Reolink",
    "f0:81:73": "Tapo/TP-Link", "54:af:97": "Tapo/TP-Link",
    "b0:c5:54": "Ezviz", "a4:14:37": "Ezviz", "44:47:cc": "Ezviz",
    "00:1b:a9": "Brother", "30:05:5c": "Brother", "00:80:77": "Brother",
    "00:00:48": "Epson", "a4:ee:57": "Epson", "44:d2:44": "Epson",
    "00:1e:0b": "HP", "3c:d9:2b": "HP", "9c:b6:54": "HP",
    "00:17:c8": "Sony", "fc:f1:52": "Sony", "30:f9:ed": "Sony",
    "00:1a:8c": "Sony", "ac:9b:0a": "Sony",
    "00:1c:43": "Samsung TV", "5c:49:7d": "Samsung TV", "8c:79:f5": "Samsung TV",
    "2c:54:cf": "LG", "a8:23:fe": "LG",
    "b8:27:eb": "Raspberry Pi", "dc:a6:32": "Raspberry Pi", "e4:5f:01": "Raspberry Pi",
    "52:54:00": "QEMU/KVM", "08:00:27": "VirtualBox",
}

def fabricante(mac):
    if not mac or mac == "desconocida":
        return "?"
    return OUI_DB.get(mac.lower()[:8], "Desconocido")

def tipo_por_puertos(puertos):
    p = set(puertos)
    if any(x in p for x in ["554", "8554", "34567", "37777"]):
        return "Cámara IP"
    if "9100" in p or "515" in p or "631" in p:
        return "Impresora"
    if "3389" in p or ("445" in p and "135" in p):
        return "PC Windows"
    if "22" in p and "80" in p and "443" in p and "8080" in p:
        return "Router / Server"
    if "53" in p or ("80" in p and "443" in p and "22" not in p):
        return "Router"
    if "22" in p and "80" not in p:
        return "Linux / Server"
    if "5000" in p or "7000" in p:
        return "Apple (AirPlay)"
    if "1900" in p or "8008" in p or "8009" in p:
        return "Chromecast"
    if "5353" in p:
        return "Dispositivo mDNS"
    if "8080" in p or "8081" in p or "8443" in p:
        return "Panel web / IoT"
    if "80" in p or "443" in p:
        return "Dispositivo web"
    return "Desconocido"

def obtener_mac(ip):
    salida = run(["ip", "neigh", "show", ip], timeout=10)
    for linea in salida.splitlines():
        if "lladdr" in linea:
            partes = linea.split()
            return partes[partes.index("lladdr") + 1]
    salida = run(["arp", "-n", ip], timeout=10)
    for linea in salida.splitlines():
        if ip in linea:
            for token in linea.split():
                if ":" in token and len(token) >= 11:
                    return token
    return "desconocida"

def identificar_dispositivo(ip):
    mac = obtener_mac(ip)
    fab = fabricante(mac) if mac != "desconocida" else "?"
    puertos_info = "21,22,23,53,80,135,139,443,445,515,554,631,1900,3389,5000,8008,8009,8080,8081,8443,8554,9100,34567,37777"
    r = run(["nmap", "-p", puertos_info, "-T4", ip], timeout=30)
    abiertos = []
    for linea in r.splitlines():
        if "/tcp" in linea and "open" in linea:
            abiertos.append(linea.split("/")[0].strip())
    return {
        "ip": ip, "mac": mac, "fabricante": fab,
        "tipo": tipo_por_puertos(abiertos), "puertos": abiertos
    }

# ============ UTILIDADES ============
def log(msg, level="info"):
    getattr(logging, level)(str(msg))

def clear():
    os.system("clear")

def pausa():
    try:
        input_raw(f"\n{DIM}Presioná ENTER para volver al menú...{RESET}")
    except (KeyboardInterrupt, EOFError):
        pass

def banner(titulo=""):
    clear()
    print(f"{C}{'='*55}{RESET}")
    print(f"{BOLD}{W}   ARSENAL DE AUDITORÍA  {DIM}v{VERSION}{RESET}")
    print(f"{C}{'='*55}{RESET}")
    if titulo:
        print(f"{M}  >> {titulo}{RESET}")
        print(f"{C}{'-'*55}{RESET}")

def menu_opciones(opciones):
    ancho = shutil.get_terminal_size((45, 20)).columns
    max_nombre = max((len(n) for _, n, _ in opciones if n), default=0)
    lado_a_lado = ancho >= 65 and (max_nombre + 22) < ancho
    for num, nombre, desc in opciones:
        if lado_a_lado and desc:
            print(f"  {C}[{num}]{RESET} {nombre:<{max_nombre}} {DIM}-> {desc}{RESET}")
        elif lado_a_lado:
            print(f"  {C}[{num}]{RESET} {nombre}")
        else:
            print(f"  {C}[{num}]{RESET} {nombre}")
            if desc:
                print(f"      {DIM}-> {desc}{RESET}")

def check_tool(name):
    return shutil.which(name) is not None

def es_volver(op):
    return op.strip().lower() in PALABRAS_ESCAPE

def detectar_red_actual():
    if check_tool("termux-wifi-connectioninfo"):
        try:
            out = run(["termux-wifi-connectioninfo"], timeout=10)
            data = json.loads(out)
            ip = data.get("ip", "")
            if ip and ip != "0.0.0.0":
                partes = ip.split(".")
                if len(partes) == 4:
                    return {"router": ".".join(partes[:3]) + ".1",
                            "red": ".".join(partes[:3]) + ".0/24",
                            "base": ".".join(partes[:3]), "ip_local": ip}
        except Exception:
            pass
    try:
        ruta = run(["ip", "route"], timeout=10)
        for linea in ruta.splitlines():
            if "default via" in linea:
                ip_router = linea.split()[2]
                partes = ip_router.split(".")
                if len(partes) == 4:
                    return {"router": ip_router,
                            "red": ".".join(partes[:3]) + ".0/24",
                            "base": ".".join(partes[:3])}
    except Exception:
        pass
    return None

def pedir_ip():
    net = detectar_red_actual()
    if net:
        print(f"{DIM}Red detectada: {net['red']}  (router: {net['router']}){RESET}")
        print(f"{DIM}ENTER = red actual | 'router' = gateway | o escribí otra{RESET}")
        print(f"{DIM}Escape: 0, atras, volver, b, q | Ctrl+X = salir{RESET}")
    while True:
        s = input(f"{C}IP / rango: {RESET}").strip()
        if not s and net:
            return net["red"]
        if s.lower() in ("local", "wifi", "mi red"):
            if net: return net["red"]
            print(f"{R}[!] No pude detectar la red local.{RESET}"); continue
        if s.lower() in ("router", "gw", "gateway"):
            if net: return net["router"]
            print(f"{R}[!] No pude detectar el router.{RESET}"); continue
        try:
            if "/" in s:
                ipaddress.ip_network(s, strict=False)
            else:
                ipaddress.ip_address(s)
            return s
        except ValueError:
            print(f"{R}[!] Formato inválido.{RESET}")
            print(f"{DIM}  IP: 192.168.0.50 | Rango: 192.168.0.0/24 | ENTER | router{RESET}")

def pedir_puertos():
    print(f"{DIM}Presets: comunes | web | camaras | todos | o puertos a mano{RESET}")
    s = input(f"{C}Puertos (ENTER = comunes): {RESET}").strip().lower()
    if s == "" or s == "comunes":
        return "21,22,23,25,53,80,110,139,143,443,445,993,995,3306,3389,5432,8080"
    if s == "web":
        return "80,443,8000,8080,8081,8443,8888"
    if s == "camaras":
        return "80,443,554,8000,8080,8554,34567,37777"
    if s == "todos":
        return "1-65535"
    return s

def guardar(nombre, contenido):
    nombre = nombre.replace("/", "_").replace("\\", "_").replace(":", "_")
    p = OUTS / nombre
    p.write_text(contenido, encoding="utf-8")
    log(f"Guardado: {p}")
    return p

def run(cmd, guardar_como=None, timeout=300, cwd=None):
    log(f"CMD: {' '.join(cmd)}")
    if not check_tool(cmd[0]):
        msg = f"[!] '{cmd[0]}' no está instalado. Instalalo con: pkg install {cmd[0]}"
        log(msg, "warning")
        return msg
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        salida = res.stdout + res.stderr
        if guardar_como:
            guardar(guardar_como, salida)
        return salida if salida.strip() else "[i] Sin salida."
    except subprocess.TimeoutExpired:
        log(f"Timeout: {cmd}", "error"); return "[!] Timeout alcanzado."
    except Exception as e:
        log(f"Error: {e}", "error"); return f"[!] Error: {e}"

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
    r = input_raw(f"{C}¿Tenés autorización? (s/n, Ctrl+X para salir): {RESET}").strip().lower()
    if r != "s":
        print(f"{R}Cerrando. Usá esto solo con permiso.{RESET}")
        log("Usuario rechazó autorización. Saliendo.", "warning")
        sys.exit(0)
    scope = input_raw(f"{C}Describí brevemente el scope: {RESET}").strip()
    log(f"Scope declarado: {scope}")
    (CONF / f"scope_{SESSION}.txt").write_text(
        f"Sesión: {SESSION}\nScope: {scope}\nAutorizado: sí\n", encoding="utf-8")

# ============ SUBMENÚ: ESCANEO ============
def menu_escaneo():
    opciones = [
        ("1", "Ping a un host", "Ver si responde"),
        ("2", "Nmap rápido", "Top 100 puertos"),
        ("3", "Nmap con presets", "comunes/web/camaras/todos"),
        ("4", "Nmap -sV", "Detectar versiones"),
        ("5", "Descubrir e identificar", "Hosts + fabricante + tipo"),
        ("6", "Análisis ARP", "IP a MAC"),
        ("7", "Escaneo completo (-p-)", "65535 puertos (lento)"),
        ("0", "Volver (o 'atras','b','q')", ""),
    ]
    while True:
        banner("ESCANEO DE RED")
        menu_opciones(opciones)
        print(f"{DIM}Ctrl+X para salir del script{RESET}")
        op = input(f"\n{C}Opción: {RESET}").strip()
        if es_volver(op): return
        elif op == "1":
            ip = pedir_ip()
            print(run(["ping", "-c", "4", ip], f"ping_{ip}_{SESSION}.txt"))
        elif op == "2":
            ip = pedir_ip()
            print(run(["nmap", "-F", ip], f"nmap_fast_{ip}_{SESSION}.txt"))
        elif op == "3":
            ip = pedir_ip(); puertos = pedir_puertos()
            print(run(["nmap", "-sV", "-p", puertos, ip], f"nmap_custom_{ip}_{SESSION}.txt", timeout=900))
        elif op == "4":
            ip = pedir_ip()
            print(run(["nmap", "-sV", ip], f"nmap_sv_{ip}_{SESSION}.txt", timeout=900))
        elif op == "5":
            escanear_e_identificar()
        elif op == "6":
            print(run(["arp", "-a"], f"arp_{SESSION}.txt"))
        elif op == "7":
            ip = pedir_ip()
            if pedir_confirmacion("Escaneo de TODOS los puertos (tarda mucho). ¿Continuar?"):
                print(run(["nmap", "-p-", ip], f"nmap_full_{ip}_{SESSION}.txt", timeout=1800))
        else:
            print(f"{R}Opción inválida.{RESET}"); continue
        pausa()

def escanear_e_identificar():
    net = detectar_red_actual()
    red = net["red"] if net else input(f"{C}Rango (ej 192.168.0.0/24): {RESET}").strip()
    print(f"\n{DIM}Red objetivo: {red}{RESET}")
    print(f"{DIM}[1/2] Descubriendo hosts activos...{RESET}")
    out = run(["nmap", "-sn", red], timeout=300)
    ips = []
    for linea in out.splitlines():
        if "Nmap scan report for" in linea:
            ip = linea.split("(")[-1].split(")")[0] if "(" in linea else linea.split()[-1]
            ips.append(ip)
    if not ips:
        print(f"{R}[!] No se encontraron hosts.{RESET}"); return
    print(f"{G}[+] {len(ips)} hosts encontrados.{RESET}\n")
    print(f"{DIM}[2/2] Identificando cada dispositivo...{RESET}\n")
    resultados = []
    for i, ip in enumerate(ips, 1):
        print(f"{DIM}[{i}/{len(ips)}] Analizando {ip}...{RESET}")
        resultados.append(identificar_dispositivo(ip))
    print(f"\n{C}{'='*55}{RESET}")
    print(f"{BOLD}{W}  DISPOSITIVOS EN LA RED {red}{RESET}")
    print(f"{C}{'='*55}{RESET}\n")
    for d in resultados:
        marca = f"{Y} [ROUTER]{RESET}" if net and d["ip"] == net["router"] else ""
        color = G if d["tipo"] != "Desconocido" else Y
        print(f"{BOLD}{d['ip']}{RESET}{marca}")
        print(f"  MAC:         {d['mac']}")
        print(f"  Fabricante:  {d['fabricante']}")
        print(f"  Tipo:        {color}{d['tipo']}{RESET}")
        if d["puertos"]:
            print(f"  Puertos:     {', '.join(d['puertos'])}")
        print()
    rep = [f"# Inventario de red - {datetime.now():%Y-%m-%d %H:%M}", "",
           f"Red: {red}", f"Hosts: {len(resultados)}", "",
           "| IP | MAC | Fabricante | Tipo | Puertos |",
           "|---|---|---|---|---|"]
    for d in resultados:
        rep.append(f"| {d['ip']} | {d['mac']} | {d['fabricante']} | {d['tipo']} | {', '.join(d['puertos'])} |")
    p = guardar(f"inventario_{SESSION}.md", "\n".join(rep))
    print(f"{G}[+] Inventario: {p}{RESET}")
    log(f"Inventario: {len(resultados)} hosts")

# ============ SUBMENÚ: WEB ============
def menu_web():
    opciones = [
        ("1", "Headers HTTP", "Servidor y respuesta"),
        ("2", "Certificado SSL/TLS", "Ver si expiró, emisor"),
        ("3", "Whois", "Dueño y registro"),
        ("4", "DNS", "Resolver dominio"),
        ("5", "Traceroute", "Camino hasta el host"),
        ("0", "Volver (o 'atras','b','q')", ""),
    ]
    while True:
        banner("ANÁLISIS WEB / SSL")
        menu_opciones(opciones)
        op = input(f"\n{C}Opción: {RESET}").strip()
        if es_volver(op): return
        elif op == "1":
            url = input(f"{C}URL: {RESET}").strip()
            print(run(["curl", "-s", "-I", url], f"headers_{SESSION}.txt"))
        elif op == "2":
            host = input(f"{C}Host: {RESET}").strip()
            print(run(["openssl", "s_client", "-connect", f"{host}:443", "-servername", host],
                      f"ssl_{host}_{SESSION}.txt", timeout=30))
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
        else:
            print(f"{R}Opción inválida.{RESET}"); continue
        pausa()

# ============ SUBMENÚ: CRIPTO ============
def menu_cripto():
    opciones = [
        ("1", "MD5 de archivo", "Hash rápido (obsoleto)"),
        ("2", "SHA256 de archivo", "Hash recomendado"),
        ("3", "Verificar hash", "Comparar con esperado"),
        ("4", "Hash de texto", "MD5 y SHA256 de texto"),
        ("0", "Volver (o 'atras','b','q')", ""),
    ]
    while True:
        banner("CRIPTOGRAFÍA / INTEGRIDAD")
        menu_opciones(opciones)
        op = input(f"\n{C}Opción: {RESET}").strip()
        if es_volver(op): return
        elif op == "1":
            f = input(f"{C}Ruta: {RESET}").strip()
            print(run(["md5sum", f], f"md5_{SESSION}.txt"))
        elif op == "2":
            f = input(f"{C}Ruta: {RESET}").strip()
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
        else:
            print(f"{R}Opción inválida.{RESET}"); continue
        pausa()

# ============ SUBMENÚ: RTSP ============
def menu_rtsp():
    banner("MONITOREO RTSP (cámaras IP)")
    print(f"{Y}[!] Solo cámaras propias o con autorización.{RESET}\n")
    ip = pedir_ip()
    print(f"\n{DIM}Verificando puerto 554...{RESET}\n")
    out = run(["nc", "-z", "-w", "2", ip, "554"], timeout=10)
    if "succeeded" in out.lower() or "open" in out.lower():
        print(f"{G}[+] Puerto 554 abierto.{RESET}")
    else:
        print(f"{Y}[i] Puerto 554 cerrado o filtrado.{RESET}")
    guardar(f"rtsp_{ip}_{SESSION}.txt", f"RTSP check {ip}\nPuerto 554 -> {out}\n")
    pausa()

# ============ SUBMENÚ: SOCKETS ============
def menu_sockets():
    opciones = [
        ("1", "Escuchar en puerto", "Recibir conexiones"),
        ("2", "Conectar a host", "Probar puerto abierto"),
        ("3", "Puertos en escucha", "Servicios locales"),
        ("0", "Volver (o 'atras','b','q')", ""),
    ]
    while True:
        banner("SOCKETS / NETCAT")
        menu_opciones(opciones)
        op = input(f"\n{C}Opción: {RESET}").strip()
        if es_volver(op): return
        elif op == "1":
            p = input(f"{C}Puerto: {RESET}").strip()
            if pedir_confirmacion("¿Tenés autorización?"):
                print(run(["nc", "-lvp", p], f"nc_listen_{p}_{SESSION}.txt"))
        elif op == "2":
            ip = pedir_ip(); p = input(f"{C}Puerto: {RESET}").strip()
            print(run(["nc", "-zv", ip, p], f"nc_{ip}_{p}_{SESSION}.txt", timeout=10))
        elif op == "3":
            if check_tool("ss"):
                print(run(["ss", "-tuln"], f"sockets_{SESSION}.txt"))
            else:
                print(run(["netstat", "-tuln"], f"sockets_{SESSION}.txt"))
        else:
            print(f"{R}Opción inválida.{RESET}"); continue
        pausa()

# ============ SUBMENÚ: WIFI ============
def menu_wifi():
    banner("AUDITORÍA WI-FI")
    print(f"{Y}[!] En Termux sin root solo info de interfaces.{RESET}\n")
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

# ============ SUBMENÚ: WORDLISTS ============
def menu_wordlists():
    opciones = [
        ("1", "Listar wordlists", "Ver diccionarios"),
        ("2", "Crear wordlist", "Generar combinaciones"),
        ("0", "Volver (o 'atras','b','q')", ""),
    ]
    while True:
        banner("GESTIÓN DE WORDLISTS")
        menu_opciones(opciones)
        op = input(f"\n{C}Opción: {RESET}").strip()
        wl_dir = BASE / "wordlists"; wl_dir.mkdir(exist_ok=True)
        if es_volver(op): return
        elif op == "1":
            archivos = list(wl_dir.iterdir())
            if not archivos: print(f"{DIM}No hay wordlists.{RESET}")
            for f in archivos: print(f"  - {f.name}")
        elif op == "2":
            print(f"{Y}[!] Uso solo en labs autorizados.{RESET}")
            base = input(f"{C}Palabra base: {RESET}").strip()
            anio = input(f"{C}Año: {RESET}").strip()
            salida = []
            for s in ["", "123", "1234", "!", "@", "2024", "2025"]:
                salida.append(f"{base}{s}"); salida.append(f"{base.capitalize()}{s}")
            if anio.isdigit():
                for s in range(int(anio)-2, int(anio)+3):
                    salida.append(f"{base}{s}")
            p = wl_dir / f"wl_{base}_{SESSION}.txt"
            p.write_text("\n".join(salida), encoding="utf-8")
            print(f"{G}[+] Guardada ({len(salida)} entradas){RESET}")
        else:
            print(f"{R}Opción inválida.{RESET}"); continue
        pausa()

# ============ SUBMENÚ: IA ============
def menu_ia():
    banner("CHAT IA")
    key_file = CONF / "ia_api_key.txt"
    if not key_file.exists():
        print(f"{Y}No hay API key.{RESET}")
        print(f"{DIM}Groq free: console.groq.com{RESET}")
        key = input(f"{C}API key: {RESET}").strip()
        if not key: pausa(); return
        key_file.write_text(key, encoding="utf-8")
        os.chmod(key_file, 0o600)
    key = key_file.read_text(encoding="utf-8").strip()
    modelo = "openai/gpt-oss-20b"
    print(f"{DIM}Modelo: {modelo} | 'salir' o 'volver' para regresar | Ctrl+X sale{RESET}\n")
    historial = [{
        "role": "system",
        "content": ("Sos un asistente de ciberseguridad para un laboratorio autorizado. "
                    "Respondés en español, breve y técnico. "
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
        payload = {"model": modelo, "messages": historial}
        cmd = ["curl", "-s", "https://api.groq.com/openai/v1/chat/completions",
               "-H", f"Authorization: Bearer {key}",
               "-H", "Content-Type: application/json",
               "-d", json.dumps(payload)]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if not res.stdout.strip():
                print(f"{R}[!] Sin respuesta.{RESET}"); historial.pop(); continue
            data = json.loads(res.stdout)
            if "error" in data:
                print(f"{R}[!] Error: {data['error'].get('message','?')}{RESET}")
                historial.pop(); continue
            if "choices" not in data:
                print(f"{R}[!] Respuesta inesperada.{RESET}"); historial.pop(); continue
            respuesta = data["choices"][0]["message"]["content"]
            historial.append({"role": "assistant", "content": respuesta})
            print(f"\n{G}IA>{RESET} {respuesta}\n")
        except subprocess.TimeoutExpired:
            print(f"{R}[!] Timeout.{RESET}"); historial.pop()
        except Exception as e:
            print(f"{R}[!] Error: {e}{RESET}"); historial.pop()

# ============ SUBMENÚ: GITHUB ============
def menu_github():
    TOKEN_FILE = CONF / "github_token.txt"
    URL_FILE   = CONF / "github_url.txt"
    opciones = [
        ("1", "Configurar repo", "URL + token"),
        ("2", "Inicializar repo", "Primera vez"),
        ("3", "Ver estado", "git status"),
        ("4", "Subir cambios", "commit + push"),
        ("5", "Bajar cambios", "pull + actualizar"),
        ("6", "Historial de commits", "Últimos 20"),
        ("7", "Clonar repo", "Bajar de GitHub"),
        ("0", "Volver (o 'atras','b','q')", ""),
    ]
    while True:
        banner("SINCRONIZACIÓN CON GITHUB")
        menu_opciones(opciones)
        op = input(f"\n{C}Opción: {RESET}").strip()
        if es_volver(op): return
        elif op == "1":
            print(f"{DIM}Ej URL: https://github.com/tuuser/arsenal.git{RESET}")
            url = input(f"{C}URL: {RESET}").strip()
            print(f"{DIM}Token: github.com/settings/tokens -> scope 'repo'{RESET}")
            token = input(f"{C}Token (ENTER = mantener): {RESET}").strip()
            if url: URL_FILE.write_text(url, encoding="utf-8")
            if token:
                TOKEN_FILE.write_text(token, encoding="utf-8")
                os.chmod(TOKEN_FILE, 0o600)
            print(f"{G}[+] Guardado.{RESET}")
        elif op == "2":
            if not URL_FILE.exists():
                print(f"{R}[!] Configurá el repo primero.{RESET}"); pausa(); continue
            src = Path(__file__).resolve()
            shutil.copy(src, REPO / "arsenal.py")
            if not (REPO / ".git").exists():
                run(["git", "init"], cwd=str(REPO))
                run(["git", "branch", "-M", "main"], cwd=str(REPO))
            print(f"{G}[+] Repo inicializado.{RESET}")
        elif op == "3":
            print(run(["git", "status"], cwd=str(REPO)))
        elif op == "4":
            if not TOKEN_FILE.exists() or not URL_FILE.exists():
                print(f"{R}[!] Configurá el repo primero.{RESET}"); pausa(); continue
            if not (REPO / ".git").exists():
                print(f"{R}[!] Inicializá el repo primero.{RESET}"); pausa(); continue
            src = Path(__file__).resolve()
            shutil.copy(src, REPO / "arsenal.py")
            msg = input(f"{C}Mensaje: {RESET}").strip() or f"update {datetime.now():%Y-%m-%d %H:%M}"
            url = URL_FILE.read_text().strip()
            token = TOKEN_FILE.read_text().strip()
            auth_url = url.replace("https://", f"https://{token}@", 1) if url.startswith("https://") and token else url
            run(["git", "add", "."], cwd=str(REPO))
            run(["git", "commit", "-m", msg], cwd=str(REPO))
            remotos = run(["git", "remote"], cwd=str(REPO))
            if "origin" in remotos:
                run(["git", "remote", "remove", "origin"], cwd=str(REPO))
            run(["git", "remote", "add", "origin", auth_url], cwd=str(REPO))
            print(run(["git", "push", "-u", "origin", "main"], timeout=180, cwd=str(REPO)))
        elif op == "5":
            if not (REPO / ".git").exists():
                print(f"{R}[!] No hay repo local.{RESET}"); pausa(); continue
            out = run(["git", "pull", "origin", "main"], timeout=180, cwd=str(REPO))
            print(out)
            if "Already up to date" not in out and "Ya está actualizado" not in out:
                if (REPO / "arsenal.py").exists():
                    shutil.copy(REPO / "arsenal.py", Path.home() / "arsenal.py")
                    print(f"{G}[+] arsenal.py actualizado.{RESET}")
        elif op == "6":
            print(run(["git", "log", "--oneline", "-20"], cwd=str(REPO)))
        elif op == "7":
            if not URL_FILE.exists():
                print(f"{R}[!] Configurá la URL primero.{RESET}"); pausa(); continue
            url = URL_FILE.read_text().strip()
            if (REPO / ".git").exists():
                print(f"{Y}[!] Ya hay un repo.{RESET}")
            else:
                print(run(["git", "clone", url, "repo"], timeout=300, cwd=str(BASE)))
        else:
            print(f"{R}Opción inválida.{RESET}"); continue
        pausa()

# ============ SUBMENÚ: MAPEO DE CÁMARAS ============
def menu_camaras():
    banner("MAPEO DE CÁMARAS IP")
    print(f"{Y}[!] Solo en tu red local, con autorización.{RESET}\n")
    net = detectar_red_actual()
    if not net:
        print(f"{R}[!] No pude detectar la red.{RESET}"); pausa(); return
    red = net["red"]
    print(f"{G}[+] Red detectada: {red}{RESET}\n")
    if not pedir_confirmacion(f"¿Escanear {red}?"): return
    out = run(["nmap", "-sn", red], timeout=300)
    ips = []
    for linea in out.splitlines():
        if "Nmap scan report for" in linea:
            ip = linea.split("(")[-1].split(")")[0] if "(" in linea else linea.split()[-1]
            ips.append(ip)
    if not ips:
        print(f"{R}[!] No se encontraron hosts.{RESET}"); pausa(); return
    puertos_cam = "80,443,554,8000,8080,8554,34567,37777,8081"
    camaras = []
    for ip in ips:
        r = run(["nmap", "-p", puertos_cam, ip], timeout=60)
        abiertos = [l.split("/")[0].strip() for l in r.splitlines() if "/tcp" in l and "open" in l]
        if not abiertos: continue
        if any(p in abiertos for p in ["554", "8554", "37777", "34567"]):
            camaras.append((ip, abiertos, "CÁMARA"))
        elif any(p in abiertos for p in ["80", "443", "8000", "8080", "8081"]):
            camaras.append((ip, abiertos, "candidato"))
    rep = [f"# Mapeo cámaras - {datetime.now():%Y-%m-%d %H:%M}", "", f"Red: {red}", "",
           "| IP | MAC | Fabricante | Puertos | Tipo |", "|---|---|---|---|---|"]
    for ip, puertos, tipo in camaras:
        mac = obtener_mac(ip); fab = fabricante(mac)
        color = G if tipo == "CÁMARA" else Y
        print(f"{color}[{tipo}]{RESET} {ip}")
        print(f"  MAC: {mac}  |  Fabricante: {fab}")
        print(f"  Puertos: {', '.join(puertos)}\n")
        rep.append(f"| {ip} | {mac} | {fab} | {', '.join(puertos)} | {tipo} |")
    p = guardar(f"mapeo_camaras_{SESSION}.md", "\n".join(rep))
    print(f"{G}[+] Reporte: {p}{RESET}")
    pausa()

# ============ REPORTES / LOGS ============
def generar_reporte():
    banner("REPORTE DE SESIÓN")
    if not LOG_FILE.exists():
        print(f"{R}No hay logs.{RESET}"); pausa(); return
    contenido = LOG_FILE.read_text(encoding="utf-8")
    lineas = [l for l in contenido.splitlines() if "CMD:" in l or "Aviso" in l or "Scope" in l]
    salidas = list(OUTS.glob(f"*{SESSION}*.txt"))
    reporte = ["# Reporte de Auditoría", "",
               f"- **Sesión:** {SESSION}",
               f"- **Autor:** {AUTOR}",
               f"- **Herramienta:** Arsenal v{VERSION}",
               f"- **Fecha:** {datetime.now():%Y-%m-%d %H:%M}", "",
               "## Comandos ejecutados", ""]
    for l in lineas: reporte.append(f"- `{l}`")
    reporte += ["", "## Archivos de salida", ""]
    for s in salidas: reporte.append(f"- `{s.name}` ({s.stat().st_size} bytes)")
    p = OUTS / f"reporte_{SESSION}.md"
    p.write_text("\n".join(reporte), encoding="utf-8")
    print(f"{G}[+] Reporte: {p}{RESET}")
    pausa()

def ver_logs():
    banner("HISTORIAL DE LOGS")
    archivos = sorted(LOGS.glob("auditoria_*.log"), reverse=True)[:10]
    if not archivos:
        print(f"{DIM}No hay logs.{RESET}"); pausa(); return
    for i, f in enumerate(archivos, 1):
        print(f"  {C}[{i}]{RESET} {f.name}  {DIM}({f.stat().st_size} bytes){RESET}")
    op = input(f"\n{C}Ver cuál (número) o ENTER: {RESET}").strip()
    if op.isdigit() and 1 <= int(op) <= len(archivos):
        print(archivos[int(op)-1].read_text(encoding="utf-8"))
    pausa()

# ============ MENÚ PRINCIPAL ============
def main():
    aviso_autorizacion()
    net = detectar_red_actual()
    opciones = [
        ("1",  "Escaneo de Red",      "Puertos, hosts, inventario"),
        ("2",  "Análisis Web / SSL",  "Headers, SSL, whois, DNS"),
        ("3",  "Criptografía",        "Hashes e integridad"),
        ("4",  "Monitoreo RTSP",      "Cámaras IP (autorizado)"),
        ("5",  "Sockets / Netcat",    "Escucha y captura local"),
        ("6",  "Auditoría Wi-Fi",     "Interfaces inalámbricas"),
        ("7",  "Wordlists",           "Gestión de diccionarios"),
        ("8",  "Chat IA",             "Asistente de seguridad"),
        ("9",  "GitHub Sync",         "Subir/bajar a VS Code"),
        ("10", "Generar Reporte",     "Exportar sesión a .md"),
        ("11", "Ver Historial",       "Últimas sesiones"),
        ("12", "Mapeo de Cámaras",    "Detectar cámaras en tu red"),
        ("0",  "Salir",               ""),
    ]
    while True:
        banner()
        if net:
            print(f"{DIM}Red actual: {net['red']}  |  Router: {net['router']}{RESET}")
            print(f"{C}{'-'*55}{RESET}")
        menu_opciones(opciones)
        print(f"{DIM}Ctrl+X sale del script en cualquier momento{RESET}")
        print(f"{C}{'-'*55}{RESET}")
        try:
            op = _input_menu(f"{C}Seleccioná opción [0-12]: {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        log(f"Menú principal: opción {op}")
        try:
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
            elif op == "12": menu_camaras()
            elif op == "0":
                print(f"\n{G}Sesión guardada en {LOG_FILE}{RESET}")
                break
            else:
                print(f"{R}Opción inválida.{RESET}"); pausa()
        except KeyboardInterrupt:
            print(f"\n{Y}Operación cancelada.{RESET}"); continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Y}Interrumpido.{RESET}")
        print(f"{DIM}Logs: {LOG_FILE}{RESET}")
        sys.exit(0)

#!/usr/bin/env python3
"""
WiFi Device Scanner — Tkinter GUI
Build: pyinstaller --onefile --windowed scan_wifi_tkinter.py
Must be run with sudo for ARP/ping scanning.
"""

import socket, subprocess, ipaddress, requests, os, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk, font

try:
    from scapy.all import ARP, Ether, srp, conf
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

# ── Scanning core (same logic as CLI version) ─────────────────────────────────

def get_local_ip_and_subnet():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip, ip.rsplit('.', 1)[0] + ".0/24"

def get_vendor(mac):
    try:
        r = requests.get(f"https://api.macvendors.com/{mac}", timeout=3)
        if r.status_code == 200:
            return r.text.strip()
    except:
        pass
    return "Unknown"

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return ""

def ping_host(ip):
    result = subprocess.run(["ping", "-c", "1", "-W", "1", str(ip)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return str(ip) if result.returncode == 0 else None

def ping_sweep(subnet, log):
    log("Ping sweep…")
    network = ipaddress.ip_network(subnet, strict=False)
    alive = set()
    with ThreadPoolExecutor(max_workers=100) as ex:
        for r in as_completed({ex.submit(ping_host, ip): ip for ip in network.hosts()}):
            if r.result():
                alive.add(r.result())
    log(f"  Ping: {len(alive)} host(s) alive")
    return alive

def arp_scan(subnet, log):
    log("ARP scan…")
    if not SCAPY_AVAILABLE:
        log("  Scapy not available")
        return {}
    conf.verb = 0
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)
    answered, _ = srp(pkt, timeout=3, verbose=False, retry=2)
    res = {r.psrc: r.hwsrc for _, r in answered}
    log(f"  ARP: {len(res)} host(s)")
    return res

def read_arp_cache(log):
    log("Reading ARP cache…")
    mac_map = {}
    try:
        out = subprocess.check_output(["ip", "neigh"], text=True)
        for line in out.splitlines():
            p = line.split()
            if "lladdr" in p and "FAILED" not in line and "INCOMPLETE" not in line:
                mac_map[p[0]] = p[p.index("lladdr") + 1]
    except Exception as e:
        log(f"  ARP cache error: {e}")
    log(f"  Cache: {len(mac_map)} entries")
    return mac_map

def is_randomized_mac(mac):
    try:
        return bool(int(mac.split(":")[0], 16) & 0x02)
    except:
        return False

def guess_device_type(mac, hostname, vendor):
    if is_randomized_mac(mac):
        return "📱 Phone/Tablet (randomized MAC)"
    h = (hostname + vendor).lower()
    if any(x in h for x in ["iphone", "apple", "ipad"]): return "🍎 Apple"
    if any(x in h for x in ["android", "samsung", "xiaomi", "huawei", "oppo"]): return "📱 Android"
    if any(x in h for x in ["router", "gateway", "dlink", "tp-link", "asus", "netgear"]): return "📡 Router"
    if any(x in h for x in ["windows", "intel", "realtek"]): return "💻 PC/Laptop"
    if any(x in h for x in ["ubuntu", "linux", "debian", "raspi"]): return "🐧 Linux"
    if any(x in h for x in ["tv", "cast", "roku", "echo", "alexa", "nest"]): return "📺 Smart TV/IoT"
    if vendor and vendor != "Unknown": return f"🔌 {vendor}"
    return "❓ Unknown"

def full_scan(log):
    my_ip, subnet = get_local_ip_and_subnet()
    log(f"Scanning {subnet}…\n")
    ping_sweep(subnet, log)
    arp_direct = arp_scan(subnet, log)
    arp_cache  = read_arp_cache(log)
    all_ips    = set(arp_direct) | set(arp_cache)
    devices = []
    for ip in sorted(all_ips, key=lambda x: list(map(int, x.split('.')))):
        mac      = (arp_direct.get(ip) or arp_cache.get(ip) or "??:??:??:??:??:??").replace("-",":").upper()
        hostname = get_hostname(ip)
        vendor   = get_vendor(mac) if not is_randomized_mac(mac) else "N/A (randomized)"
        dtype    = guess_device_type(mac, hostname, vendor)
        devices.append({"ip": ip, "mac": mac, "hostname": hostname or "—",
                         "vendor": vendor, "type": dtype, "me": ip == my_ip})
    log(f"\nDone — {len(devices)} device(s) found.")
    return devices

# ── GUI ───────────────────────────────────────────────────────────────────────

BG       = "#0f1117"
BG2      = "#1a1d27"
ACCENT   = "#7c6af7"
ACCENT2  = "#5eead4"
TEXT     = "#e2e8f0"
SUBTEXT  = "#64748b"
ROW_ODD  = "#161923"
ROW_EVEN = "#1a1d27"
GREEN    = "#4ade80"
YELLOW   = "#fbbf24"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WiFi Device Scanner")
        self.geometry("1000x620")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._build_ui()
        self.after(100, self._start_scan)

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG, pady=14)
        hdr.pack(fill="x", padx=20)
        tk.Label(hdr, text="📡  WiFi Device Scanner", font=("Segoe UI", 18, "bold"),
                 fg=ACCENT, bg=BG).pack(side="left")
        self.status_lbl = tk.Label(hdr, text="", font=("Segoe UI", 10),
                                   fg=SUBTEXT, bg=BG)
        self.status_lbl.pack(side="left", padx=16)
        self.btn = tk.Button(hdr, text="⟳  Refresh", font=("Segoe UI", 11, "bold"),
                             bg=ACCENT, fg="white", relief="flat", padx=18, pady=6,
                             activebackground="#6357d4", cursor="hand2",
                             command=self._start_scan)
        self.btn.pack(side="right")

        # Log strip
        self.log_var = tk.StringVar(value="Starting…")
        tk.Label(self, textvariable=self.log_var, font=("Consolas", 9),
                 fg=SUBTEXT, bg=BG, anchor="w").pack(fill="x", padx=22)

        # Table
        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True, padx=16, pady=(6, 16))

        cols = ("ip", "mac", "hostname", "type", "me")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview",
                        background=ROW_EVEN, foreground=TEXT,
                        fieldbackground=ROW_EVEN, rowheight=32,
                        font=("Consolas", 10), borderwidth=0)
        style.configure("Treeview.Heading",
                        background=BG2, foreground=ACCENT,
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", ACCENT)])

        self.tree.heading("ip",       text="IP Address")
        self.tree.heading("mac",      text="MAC Address")
        self.tree.heading("hostname", text="Hostname")
        self.tree.heading("type",     text="Device Type")
        self.tree.heading("me",       text="")
        self.tree.column("ip",       width=150, anchor="w")
        self.tree.column("mac",      width=185, anchor="w")
        self.tree.column("hostname", width=190, anchor="w")
        self.tree.column("type",     width=340, anchor="w")
        self.tree.column("me",       width=80,  anchor="center")

        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.tag_configure("odd",  background=ROW_ODD)
        self.tree.tag_configure("even", background=ROW_EVEN)
        self.tree.tag_configure("me",   background="#1e2a1e", foreground=GREEN)

    def _log(self, msg):
        self.log_var.set(msg)
        self.update_idletasks()

    def _start_scan(self):
        if os.geteuid() != 0:
            self._log("⚠  Not running as root — results may be incomplete.")
        self.btn.config(state="disabled", text="Scanning…")
        self.status_lbl.config(text="")
        for row in self.tree.get_children():
            self.tree.delete(row)
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _do_scan(self):
        try:
            devices = full_scan(self._log)
            self.after(0, self._populate, devices)
        except Exception as e:
            self.after(0, self._log, f"Error: {e}")
            self.after(0, lambda: self.btn.config(state="normal", text="⟳  Refresh"))

    def _populate(self, devices):
        for i, d in enumerate(devices):
            tag  = "me" if d["me"] else ("odd" if i % 2 == 0 else "even")
            mark = "★ You" if d["me"] else ""
            self.tree.insert("", "end",
                             values=(d["ip"], d["mac"], d["hostname"], d["type"], mark),
                             tags=(tag,))
        self.status_lbl.config(text=f"{len(devices)} device(s)")
        self.btn.config(state="normal", text="⟳  Refresh")

if __name__ == "__main__":
    App().mainloop()

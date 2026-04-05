#!/usr/bin/env python3
"""
WiFi Device Scanner — Pygame GUI
Build: pyinstaller --onefile scan_wifi_pygame.py
Must be run with sudo for ARP/ping scanning.
"""

import socket, subprocess, ipaddress, requests, os, sys, threading, math, time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from scapy.all import ARP, Ether, srp, conf
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

import pygame

# ── Scanning core ──────────────────────────────────────────────────────────────

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
    r = subprocess.run(["ping", "-c", "1", "-W", "1", str(ip)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return str(ip) if r.returncode == 0 else None

def ping_sweep(subnet):
    net = ipaddress.ip_network(subnet, strict=False)
    alive = set()
    with ThreadPoolExecutor(max_workers=100) as ex:
        for f in as_completed({ex.submit(ping_host, ip): ip for ip in net.hosts()}):
            if f.result(): alive.add(f.result())
    return alive

def arp_scan(subnet):
    if not SCAPY_AVAILABLE: return {}
    conf.verb = 0
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)
    answered, _ = srp(pkt, timeout=3, verbose=False, retry=2)
    return {r.psrc: r.hwsrc for _, r in answered}

def read_arp_cache():
    mac_map = {}
    try:
        out = subprocess.check_output(["ip", "neigh"], text=True)
        for line in out.splitlines():
            p = line.split()
            if "lladdr" in p and "FAILED" not in line and "INCOMPLETE" not in line:
                mac_map[p[0]] = p[p.index("lladdr") + 1]
    except:
        pass
    return mac_map

def is_randomized_mac(mac):
    try:
        return bool(int(mac.split(":")[0], 16) & 0x02)
    except:
        return False

def guess_device_type(mac, hostname, vendor):
    if is_randomized_mac(mac): return "Phone/Tablet (randomized MAC)"
    h = (hostname + vendor).lower()
    if any(x in h for x in ["iphone","apple","ipad"]): return "Apple Device"
    if any(x in h for x in ["android","samsung","xiaomi","huawei","oppo"]): return "Android Device"
    if any(x in h for x in ["router","gateway","dlink","tp-link","asus","netgear"]): return "Router/Gateway"
    if any(x in h for x in ["windows","intel","realtek"]): return "PC / Laptop"
    if any(x in h for x in ["ubuntu","linux","debian","raspi"]): return "Linux Device"
    if any(x in h for x in ["tv","cast","roku","echo","alexa","nest"]): return "Smart TV / IoT"
    if vendor and vendor != "Unknown": return vendor[:30]
    return "Unknown"

def device_icon(dtype):
    t = dtype.lower()
    if "phone" in t or "android" in t: return "📱"
    if "apple" in t: return "🍎"
    if "router" in t: return "📡"
    if "linux" in t: return "🐧"
    if "pc" in t or "laptop" in t: return "💻"
    if "tv" in t or "iot" in t: return "📺"
    return "🔌"

def full_scan(status_cb):
    my_ip, subnet = get_local_ip_and_subnet()
    status_cb(f"Scanning {subnet}…")
    status_cb("Step 1/3 — Ping sweep…")
    ping_sweep(subnet)
    status_cb("Step 2/3 — ARP scan…")
    arp_direct = arp_scan(subnet)
    status_cb("Step 3/3 — Reading ARP cache…")
    arp_cache = read_arp_cache()
    all_ips = set(arp_direct) | set(arp_cache)
    status_cb("Enriching results…")
    devices = []
    for ip in sorted(all_ips, key=lambda x: list(map(int, x.split('.')))):
        mac      = (arp_direct.get(ip) or arp_cache.get(ip) or "??:??:??:??:??:??").replace("-",":").upper()
        hostname = get_hostname(ip)
        vendor   = get_vendor(mac) if not is_randomized_mac(mac) else "N/A"
        dtype    = guess_device_type(mac, hostname, vendor)
        devices.append({"ip": ip, "mac": mac, "hostname": hostname or "—",
                         "vendor": vendor, "type": dtype,
                         "icon": device_icon(dtype), "me": ip == my_ip})
    status_cb(f"Done — {len(devices)} device(s) found.")
    return devices

# ── Colours & helpers ──────────────────────────────────────────────────────────

C = {
    "bg":       (13,  16,  23),
    "bg2":      (22,  26,  39),
    "bg3":      (28,  33,  50),
    "accent":   (124,106, 247),
    "accent2":  (94, 234, 212),
    "text":     (226, 232, 240),
    "sub":      (100, 116, 139),
    "green":    ( 74, 222, 128),
    "yellow":   (251, 191,  36),
    "row_odd":  ( 18,  22,  33),
    "row_even": ( 22,  26,  39),
    "hover":    ( 30,  36,  55),
    "btn":      (124, 106, 247),
    "btn_hov":  ( 99,  87, 212),
}

def draw_rect_rounded(surf, color, rect, r=10):
    pygame.draw.rect(surf, color, rect, border_radius=r)

def truncate(text, font, max_w):
    if font.size(text)[0] <= max_w:
        return text
    while text and font.size(text + "…")[0] > max_w:
        text = text[:-1]
    return text + "…"

# ── App ────────────────────────────────────────────────────────────────────────

class WifiScanner:
    W, H = 1060, 640

    COLS = [
        ("  Device", 200),
        ("IP Address", 155),
        ("MAC Address", 190),
        ("Hostname", 195),
        ("Type", 260),
    ]

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("WiFi Device Scanner")
        self.screen = pygame.display.set_mode((self.W, self.H), pygame.RESIZABLE)
        self.clock  = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_hdr   = pygame.font.SysFont("Segoe UI", 12, bold=True)
        self.font_row   = pygame.font.SysFont("Consolas", 12)
        self.font_sub   = pygame.font.SysFont("Segoe UI", 11)
        self.font_btn   = pygame.font.SysFont("Segoe UI", 13, bold=True)

        self.devices    = []
        self.status     = "Initialising…"
        self.scanning   = False
        self.scroll     = 0
        self.hovered    = -1
        self.spin_angle = 0.0

        self._start_scan()

    # ── Scan thread ────────────────────────────────────────────────────────────

    def _start_scan(self):
        if self.scanning:
            return
        self.scanning = True
        self.devices  = []
        self.scroll   = 0
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _do_scan(self):
        try:
            result = full_scan(lambda s: setattr(self, "status", s))
            self.devices = result
        except Exception as e:
            self.status = f"Error: {e}"
        self.scanning = False

    # ── Drawing ────────────────────────────────────────────────────────────────

    def _btn_rect(self):
        return pygame.Rect(self.W - 160, 16, 140, 38)

    def _draw_header(self):
        # Title
        t = self.font_title.render("📡  WiFi Device Scanner", True, C["accent"])
        self.screen.blit(t, (20, 20))

        # Status
        s = self.font_sub.render(self.status, True, C["sub"])
        self.screen.blit(s, (20, 52))

        # Refresh button
        br = self._btn_rect()
        col = C["btn_hov"] if br.collidepoint(pygame.mouse.get_pos()) else C["btn"]
        draw_rect_rounded(self.screen, col, br, 8)
        if self.scanning:
            # spinning arc
            cx, cy = br.centerx - 30, br.centery
            pygame.draw.arc(self.screen, (255,255,255),
                            (cx-9, cy-9, 18, 18),
                            math.radians(self.spin_angle),
                            math.radians(self.spin_angle + 270), 2)
            self.spin_angle = (self.spin_angle + 6) % 360
        bt = self.font_btn.render("⟳  Refresh", True, (255, 255, 255))
        self.screen.blit(bt, bt.get_rect(center=br.center))

    def _col_x(self):
        xs, x = [], 0
        for _, w in self.COLS:
            xs.append(x)
            x += w
        return xs

    def _draw_table_header(self, top):
        pygame.draw.rect(self.screen, C["bg3"], (0, top, self.W, 32))
        xs = self._col_x()
        for i, ((label, _), x) in enumerate(zip(self.COLS, xs)):
            t = self.font_hdr.render(label, True, C["accent"])
            self.screen.blit(t, (x + 14, top + 9))
        pygame.draw.line(self.screen, C["accent"], (0, top + 32), (self.W, top + 32), 1)

    def _draw_rows(self, top, row_h=38):
        clip = pygame.Rect(0, top, self.W, self.H - top)
        self.screen.set_clip(clip)
        xs = self._col_x()
        mx, my = pygame.mouse.get_pos()
        self.hovered = -1

        for i, d in enumerate(self.devices):
            y = top + i * row_h - self.scroll
            if y + row_h < top or y > self.H:
                continue
            rect = pygame.Rect(0, y, self.W, row_h)
            if rect.collidepoint(mx, my):
                bg = C["hover"]
                self.hovered = i
            elif d["me"]:
                bg = (18, 38, 22)
            elif i % 2 == 0:
                bg = C["row_odd"]
            else:
                bg = C["row_even"]
            pygame.draw.rect(self.screen, bg, rect)

            # Columns
            cells = [
                d["icon"] + "  " + d["type"][:22],
                d["ip"],
                d["mac"],
                d["hostname"],
                d["type"],
            ]
            for col_i, (text, (_, col_w)) in enumerate(zip(cells, self.COLS)):
                col = C["green"] if d["me"] else C["text"]
                txt = truncate(text, self.font_row, col_w - 16)
                s = self.font_row.render(txt, True, col)
                self.screen.blit(s, (xs[col_i] + 14, y + 12))

            # "You" badge
            if d["me"]:
                badge = self.font_sub.render("★ You", True, C["green"])
                self.screen.blit(badge, (self.W - 70, y + 12))

        self.screen.set_clip(None)

    def _draw_scrollbar(self, top, row_h=38):
        total_h = len(self.devices) * row_h
        view_h  = self.H - top
        if total_h <= view_h:
            return
        ratio    = view_h / total_h
        bar_h    = max(30, int(view_h * ratio))
        bar_y    = top + int((self.scroll / total_h) * view_h)
        pygame.draw.rect(self.screen, C["bg3"],   (self.W - 8, top, 8, view_h))
        pygame.draw.rect(self.screen, C["accent"], (self.W - 7, bar_y, 6, bar_h), border_radius=3)

    def draw(self):
        self.screen.fill(C["bg"])
        self._draw_header()
        table_top = 80
        self._draw_table_header(table_top)
        self._draw_rows(table_top + 33)
        self._draw_scrollbar(table_top + 33)

        # footer
        footer = self.font_sub.render(
            f"{len(self.devices)} device(s) found   |   scroll with mouse wheel",
            True, C["sub"])
        self.screen.blit(footer, (20, self.H - 22))

        pygame.display.flip()

    # ── Event loop ─────────────────────────────────────────────────────────────

    def _max_scroll(self, row_h=38):
        table_top = 80 + 33
        total_h   = len(self.devices) * row_h
        view_h    = self.H - table_top
        return max(0, total_h - view_h)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.VIDEORESIZE:
                    self.W, self.H = event.w, event.h
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self._btn_rect().collidepoint(event.pos):
                        self._start_scan()
                    if event.button == 4:  # scroll up
                        self.scroll = max(0, self.scroll - 40)
                    if event.button == 5:  # scroll down
                        self.scroll = min(self._max_scroll(), self.scroll + 40)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self._start_scan()
                    if event.key == pygame.K_UP:
                        self.scroll = max(0, self.scroll - 40)
                    if event.key == pygame.K_DOWN:
                        self.scroll = min(self._max_scroll(), self.scroll + 40)

            self.draw()
            self.clock.tick(30)

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("⚠  Run with sudo for best results.")
    WifiScanner().run()

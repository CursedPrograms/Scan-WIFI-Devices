[![Twitter: @NorowaretaGemu](https://img.shields.io/badge/X-@NorowaretaGemu-blue.svg?style=flat)](https://x.com/NorowaretaGemu)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  
  <br>
<div align="center">
  <a href="https://ko-fi.com/cursedentertainment">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="ko-fi" style="width: 20%;"/>
  </a>
</div>
  <br>

<div align="center">
  <img alt="Python" src="https://img.shields.io/badge/python%20-%23323330.svg?&style=for-the-badge&logo=python&logoColor=white"/>
</div>
<div align="center">
    <img alt="Git" src="https://img.shields.io/badge/git%20-%23323330.svg?&style=for-the-badge&logo=git&logoColor=white"/>
  <img alt="PowerShell" src="https://img.shields.io/badge/PowerShell-%23323330.svg?&style=for-the-badge&logo=powershell&logoColor=white"/>
  <img alt="Shell" src="https://img.shields.io/badge/Shell-%23323330.svg?&style=for-the-badge&logo=gnu-bash&logoColor=white"/>
  <img alt="Batch" src="https://img.shields.io/badge/Batch-%23323330.svg?&style=for-the-badge&logo=windows&logoColor=white"/>
  </div>
  <br>

# Scan-WIFI-Devices

Find every device on your Wi-Fi: IP, MAC, hostname, maker and a best guess at what it is
(phone, router, PC, Linux box, smart TV). Combines a ping sweep, an ARP scan and the kernel's ARP
cache, so sleeping phones show up too. Terminal, Tkinter and Pygame versions.

**Website:** https://cursedprograms.github.io/Scan-WIFI-Devices/

[Farica☆Kimora](https://github.com/Farica-Kimora) © Cursed Entertainment

![A scan in the terminal](screenshot.png)

### The Tkinter window

| Scanning | Done |
| --- | --- |
| ![The Tkinter window while it scans](images/tkinter-scanning.png) | ![The Tkinter window after a scan](images/tkinter-window.png) |

A real scan of a small home network: the router and this PC (MAC addresses and hostname masked).

## What you need
- **Linux** (it uses `ping -c`, `ip neigh` and raw ARP packets; on Windows it says so and stops).
- **Python 3.9+** and root for the ARP scan.

## How to run
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt          # requests, scapy, pygame
sudo -E ./venv/bin/python scan_wifi.py           # terminal table
sudo -E ./venv/bin/python scan_wifi_tkinter.py   # window with a sortable list and Refresh
sudo -E ./venv/bin/python scan_wifi_pygame.py    # animated Pygame window
```
A scan takes about 15 seconds on a /24 network.

## How it works
1. **Ping sweep** of the whole subnet, 100 at a time - wakes devices up and fills the ARP cache.
2. **ARP scan** with scapy (when it's installed and you're root).
3. **ARP cache** from `ip neigh`.
4. Each device gets its hostname (reverse DNS), its maker from the MAC (api.macvendors.com) and a
   type guess. Phones and tablets that **randomize their MAC** (the "locally administered" bit)
   are flagged as such, since no maker can be looked up for them.

Only scan networks you own or are allowed to scan.

## Tests
`python -m pytest` checks the MAC and device-type helpers (run by the GitHub workflow on every push).

<div align="center">
<a href="https://cursedprograms.github.io/Scan-WIFI-Devices/" target="_blank">
    <img src="https://raw.githubusercontent.com/CursedPrograms/Scan-WIFI-Devices/main/images/site-qr.png"
        alt="QR code to the Scan-WIFI-Devices website" style="width:200px;">
</a>
</div>

## License
MIT, see [LICENSE](LICENSE).

---

<br>
<div align="center">
© Cursed Entertainment 2026
</div>
<br>
<div align="center">
<a href="https://cursed-entertainment.itch.io/" target="_blank">
    <img src="https://raw.githubusercontent.com/CursedPrograms/cursedentertainment/main/images/logos/logo-wide-grey.png"
        alt="CursedEntertainment Logo" style="width:250px;">
</a>
</div>

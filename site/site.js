// Scan-WIFI-Devices - a radar sweep that finds a few "devices".

"use strict";

const canvas = document.getElementById("radar");
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (canvas) {
  const ctx = canvas.getContext("2d");
  const size = canvas.width, c = size / 2, r = size / 2 - 6;
  const devices = [
    { a: 0.6, d: 0.45, label: "router" }, { a: 2.1, d: 0.7, label: "phone" },
    { a: 3.4, d: 0.35, label: "pc" }, { a: 4.6, d: 0.8, label: "phone" }, { a: 5.5, d: 0.55, label: "tv" },
  ].map((dev) => ({ ...dev, glow: 0 }));
  let angle = 0;

  const draw = () => {
    ctx.clearRect(0, 0, size, size);
    ctx.strokeStyle = "rgba(46, 242, 195, 0.25)";
    ctx.lineWidth = 1;
    for (const f of [1, 0.66, 0.33]) {
      ctx.beginPath();
      ctx.arc(c, c, r * f, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.beginPath();
    ctx.moveTo(c - r, c); ctx.lineTo(c + r, c); ctx.moveTo(c, c - r); ctx.lineTo(c, c + r);
    ctx.stroke();

    // the sweep: a fading wedge behind the beam
    const sweep = ctx.createConicGradient ? ctx.createConicGradient(angle - 0.9, c, c) : null;
    if (sweep) {
      sweep.addColorStop(0, "rgba(46, 242, 195, 0)");
      sweep.addColorStop(0.14, "rgba(46, 242, 195, 0.35)");
      sweep.addColorStop(0.145, "rgba(46, 242, 195, 0)");
      ctx.fillStyle = sweep;
      ctx.beginPath();
      ctx.arc(c, c, r, 0, Math.PI * 2);
      ctx.fill();
    }

    for (const dev of devices) {
      const diff = (angle - dev.a + Math.PI * 4) % (Math.PI * 2);
      if (diff < 0.08) dev.glow = 1;
      dev.glow *= 0.985;
      if (dev.glow < 0.05) continue;
      const x = c + Math.cos(dev.a) * r * dev.d, y = c + Math.sin(dev.a) * r * dev.d;
      ctx.fillStyle = `rgba(46, 242, 195, ${dev.glow})`;
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.font = "11px JetBrains Mono, monospace";
      ctx.fillText(dev.label, x + 7, y + 4);
    }
    angle = (angle + 0.03) % (Math.PI * 2);
    if (!reduced) requestAnimationFrame(draw);
  };

  if (reduced) devices.forEach((d) => (d.glow = 1));
  draw();
}
